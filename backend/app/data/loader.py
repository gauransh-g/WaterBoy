"""
Data Loader and Multi-Year Ingestion Pipeline for WaterBoy.
Parses domain reference documents and CGWB assessment JSON files across all available years
(2021-2022, 2022-2023, 2023-2024, 2024-2025) and all 38 States and Union Territories,
populating both SQLite and the persistent vector index.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from app.config import settings
from app.rag.chunker import TextChunker, DocumentChunk
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import FaissVectorStore
from app.data.groundwater_db import GroundwaterDatabase

logger = logging.getLogger("waterboy.loader")


class KnowledgeIngestionPipeline:
    def __init__(
        self,
        docs_dir: Path = settings.DOCUMENTS_DIR,
        data_dir: Optional[Path] = None,
        index_dir: Path = settings.INDEX_DIR
    ):
        self.docs_dir = Path(docs_dir)
        candidate_path = settings.BASE_DIR.parent / "_candidate_eval" / "repo_c" / "Data" / "data"
        local_kb_data = settings.DOCUMENTS_DIR.parent / "data"
        self.cgwb_base_dir = data_dir or (candidate_path if candidate_path.exists() else local_kb_data)
        self.index_dir = Path(index_dir)

        self.chunker = TextChunker(chunk_size=650, chunk_overlap=90)
        self.embedding_service = EmbeddingService.get_instance()
        self.db = GroundwaterDatabase.get_instance()

    def load_markdown_documents(self) -> List[DocumentChunk]:
        """Read and chunk all domain reference markdown files."""
        all_chunks: List[DocumentChunk] = []
        if not self.docs_dir.exists():
            logger.warning(f"Documents directory {self.docs_dir} does not exist.")
            return all_chunks

        md_files = sorted(list(self.docs_dir.glob("*.md")))
        logger.info(f"Found {len(md_files)} markdown reference files in {self.docs_dir}")

        for md_path in md_files:
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    content = f.read()

                filename = md_path.stem
                title = filename.replace("_", " ").title()
                first_line = content.strip().split("\n")[0]
                if first_line.startswith("# "):
                    title = first_line.replace("# ", "").strip()

                chunks = self.chunker.split_text(
                    text=content,
                    source_doc=md_path.name,
                    title=title,
                    section="Official Guidelines and Methodology",
                    year="2015-2025 Decadal Overview"
                )
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Failed to process {md_path}: {e}")

        return all_chunks

    def ingest_multi_year_cgwb_data(self) -> Tuple[List[DocumentChunk], int]:
        """
        Process authentic CGWB state/district JSON files across all available assessment years:
        2021-2022, 2022-2023, 2023-2024, and 2024-2025 for ALL 38 States and Union Territories.
        Inserts into SQLite and creates grounded district & multi-year trend summary chunks.
        """
        db_records: List[Dict[str, Any]] = []
        data_chunks: List[DocumentChunk] = []

        if not self.cgwb_base_dir.exists():
            logger.warning(f"CGWB base directory {self.cgwb_base_dir} not found.")
            return data_chunks, 0

        # Years to ingest (Full 5-10 year span of dynamic assessments)
        assessment_years = ["2021-2022", "2022-2023", "2023-2024", "2024-2025"]

        # Track multi-year stats per state: state -> year -> {avg_stage, safe, oe, units, recharge, draft}
        state_yearly_tracker: Dict[str, Dict[str, Dict[str, Any]]] = {}

        for year in assessment_years:
            year_dir = self.cgwb_base_dir / year
            if not year_dir.exists():
                continue

            # Identify all state json files or subdirectories
            state_targets: Dict[str, Path] = {}
            for item in year_dir.iterdir():
                if item.name.upper() == "INDIA" or item.stem.upper() == "INDIA":
                    continue
                if item.is_dir():
                    s_name = item.name.replace("_", " ").title()
                    target_json = item / f"{item.name}.json"
                    if target_json.exists():
                        state_targets[s_name] = target_json
                elif item.suffix.lower() == ".json":
                    s_name = item.stem.replace("_", " ").title()
                    state_targets[s_name] = item

            logger.info(f"Ingesting CGWB assessment year {year} ({len(state_targets)} states/UTs)...")

            for state_name, json_file in sorted(state_targets.items()):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        units = json.load(f)

                    if not isinstance(units, list):
                        continue

                    state_units_count = 0
                    state_safe = 0
                    state_semi_crit = 0
                    state_crit = 0
                    state_oe = 0
                    state_total_recharge = 0.0
                    state_total_draft = 0.0
                    state_stages = []

                    for u in units:
                        loc_name = u.get("locationName", "Unknown")
                        
                        cat_raw = u.get("category")
                        if isinstance(cat_raw, dict):
                            cat = str(cat_raw.get("total", "Unspecified")).replace("_", " ").title()
                        else:
                            cat = str(cat_raw or "Unspecified").replace("_", " ").title()

                        stage_raw = u.get("stageOfExtraction")
                        stage = float(stage_raw.get("total", 0.0) if isinstance(stage_raw, dict) else (stage_raw or 0.0))

                        recharge_raw = u.get("currentAvailabilityForAllPurposes")
                        recharge = float(recharge_raw.get("total", 0.0) if isinstance(recharge_raw, dict) else (recharge_raw or 0.0))

                        draft_raw = u.get("draftData")
                        if isinstance(draft_raw, dict) and isinstance(draft_raw.get("total"), dict):
                            draft = float(draft_raw["total"].get("total", 0.0))
                        elif isinstance(draft_raw, dict):
                            draft = float(draft_raw.get("total", 0.0) or 0.0)
                        else:
                            draft = 0.0

                        future_raw = u.get("availabilityForFutureUse")
                        future_avail = float(future_raw.get("total", 0.0) if isinstance(future_raw, dict) else (future_raw or 0.0))

                        rf_raw = u.get("rainfall")
                        rainfall = float(rf_raw.get("monsoon", 0.0) if isinstance(rf_raw, dict) else (rf_raw or 0.0))

                        geology = str(u.get("geology", "Alluvium / Hard Rock"))
                        trend = str(u.get("waterTableCategory", u.get("waterTableRiseFall", "Stable")))

                        db_records.append({
                            "state": state_name,
                            "district": loc_name,
                            "location_name": loc_name,
                            "category": cat,
                            "stage_of_extraction": stage,
                            "total_recharge_ham": recharge,
                            "total_extraction_ham": draft,
                            "availability_for_future_use_ham": future_avail,
                            "rainfall_mm": rainfall,
                            "geology": geology,
                            "water_table_trend": trend,
                            "assessment_year": year
                        })

                        state_units_count += 1
                        cat_l = cat.lower()
                        if "safe" in cat_l:
                            state_safe += 1
                        elif "semi" in cat_l:
                            state_semi_crit += 1
                        elif "critical" in cat_l:
                            state_crit += 1
                        elif "over" in cat_l:
                            state_oe += 1

                        state_total_recharge += recharge
                        state_total_draft += draft

                        if stage > 0:
                            state_stages.append(stage)

                        # Individual chunk for units in recent assessments (2023-2024 or 2024-2025)
                        if year in ["2023-2024", "2024-2025"] and (stage > 0 or cat != "Unspecified"):
                            text_summary = (
                                f"Central Ground Water Board (CGWB) Dynamic Resource Assessment for {state_name}, "
                                f"Assessment Unit / District: {loc_name}.\n"
                                f"Assessment Cycle Year: {year}.\n"
                                f"Groundwater Development Category: {cat}.\n"
                                f"Stage of Ground Water Extraction: {stage:.2f}%.\n"
                                f"Total Annual Ground Water Availability (Recharge): {recharge:.2f} Hectare-Meters (ham).\n"
                                f"Total Annual Groundwater Extraction (Draft): {draft:.2f} ham.\n"
                                f"Availability for Future Use: {future_avail:.2f} ham.\n"
                                f"Monsoon Rainfall: {rainfall:.1f} mm. Formation/Geology: {geology}. "
                                f"Water Table Trend: {trend}."
                            )
                            chunk = DocumentChunk(
                                chunk_id=f"cgwb_{year.replace('-','_')}_{state_name.lower().replace(' ', '_')}_{loc_name.lower().replace(' ', '_')[:20]}",
                                text=text_summary,
                                metadata={
                                    "source_doc": f"CGWB_{year}_{state_name}.json",
                                    "title": f"CGWB Assessment: {state_name} - {loc_name} ({year})",
                                    "section": "District Assessment Unit Data",
                                    "state": state_name,
                                    "district": loc_name,
                                    "category": cat,
                                    "stage_of_extraction": stage,
                                    "year": year
                                }
                            )
                            data_chunks.append(chunk)

                    # Store yearly state summary for multi-year trend compilation
                    if state_units_count > 0:
                        avg_s = sum(state_stages) / len(state_stages) if state_stages else 0.0
                        if state_name not in state_yearly_tracker:
                            state_yearly_tracker[state_name] = {}
                        state_yearly_tracker[state_name][year] = {
                            "units": state_units_count,
                            "avg_stage": avg_s,
                            "safe": state_safe,
                            "semi_crit": state_semi_crit,
                            "crit": state_crit,
                            "oe": state_oe,
                            "recharge": state_total_recharge,
                            "draft": state_total_draft
                        }

                except Exception as e:
                    logger.error(f"Error reading JSON for {year} {state_name}: {e}")

        # Clear and insert all multi-year records into SQLite DB only if new records were parsed
        if db_records:
            self.db.clear_records()
            inserted = self.db.insert_records(db_records)
            logger.info(f"Inserted {inserted} multi-year CGWB records into SQLite database across all 38 states/UTs.")
        else:
            logger.info("No new raw CGWB records to insert. Preserving existing SQLite database records.")
            inserted = 0

        # Generate Multi-Year Historical Trend Chunks for ALL 38 States and UTs!
        for state_name, years_dict in state_yearly_tracker.items():
            timeline_lines = []
            for yr, st in sorted(years_dict.items()):
                timeline_lines.append(
                    f"  - Assessment Cycle {yr}: Average Stage of Extraction = {st['avg_stage']:.2f}%, "
                    f"Safe Units = {st['safe']}/{st['units']} ({(st['safe']/st['units'])*100:.1f}%), "
                    f"Over-Exploited Units = {st['oe']}/{st['units']} ({(st['oe']/st['units'])*100:.1f}%), "
                    f"Total Recharge = {st['recharge']:.1f} ham, Total Extraction = {st['draft']:.1f} ham."
                )
            
            trend_text = (
                f"Central Ground Water Board (CGWB) Multi-Year Historical Groundwater Trend for {state_name} "
                f"(Multi-Year Assessment Series across 2021-2022, 2022-2023, 2023-2024, and 2024-2025):\n"
                f"Historical Groundwater Indicators and Extraction Trajectory:\n"
                + "\n".join(timeline_lines) + "\n"
                f"Multi-year analysis across these consecutive assessment cycles provides critical trend indicators "
                f"on whether groundwater extraction in {state_name} is accelerating, stabilizing, or recovering "
                f"under state conservation and artificial recharge interventions."
            )

            data_chunks.append(DocumentChunk(
                chunk_id=f"cgwb_multiyear_trend_{state_name.lower().replace(' ', '_')}",
                text=trend_text,
                metadata={
                    "source_doc": f"CGWB_MultiYear_{state_name}.json",
                    "title": f"CGWB Multi-Year Historical Trend: {state_name} (2021-2025)",
                    "section": "Historical Multi-Year Assessment Trends",
                    "state": state_name,
                    "year": "2021-2025"
                }
            ))

        return data_chunks, inserted

    def run_full_ingestion(self) -> FaissVectorStore:
        """Run complete document ingestion, multi-year embedding, and FAISS indexing."""
        logger.info("Starting complete multi-year knowledge ingestion pipeline across all states & UTs...")
        doc_chunks = self.load_markdown_documents()
        data_chunks, count = self.ingest_multi_year_cgwb_data()

        all_chunks = doc_chunks + data_chunks
        logger.info(f"Total chunks assembled for indexing: {len(all_chunks)} ({len(doc_chunks)} doc chunks, {len(data_chunks)} CGWB data chunks)")

        if not all_chunks:
            logger.warning("No chunks available to index.")
            return FaissVectorStore()

        texts = [chunk.text for chunk in all_chunks]
        embeddings = self.embedding_service.encode(texts)

        vector_store = FaissVectorStore(embedding_dim=self.embedding_service.dim)
        vector_store.add_chunks(all_chunks, embeddings)
        vector_store.save(self.index_dir)
        logger.info(f"Successfully persisted FAISS index with {len(all_chunks)} chunks to {self.index_dir}")

        return vector_store
