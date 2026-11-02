"""
Grounded Answer Generator with Citation Attribution, Adaptive Domain Detection,
and Refusal Handling.
"""

import os
import re
import logging
from typing import List, Tuple, Optional, Set
from app.rag.chunker import DocumentChunk
from app.models.schemas import Citation
from app.config import settings

logger = logging.getLogger("waterboy.generator")

# Comprehensive vocabulary of domain concepts, hydrogeology, policies, and Indian geography
GROUNDWATER_DOMAIN_TERMS: Set[str] = {
    # Core hydrogeology & water terms
    "water", "groundwater", "aquifer", "recharge", "draft", "extraction", "discharge",
    "well", "wells", "borewell", "borewells", "tubewell", "tubewells", "dugwell", "dugwells",
    "cgwb", "gec", "ingres", "atal", "bhujal", "jal", "jeevan", "rainwater", "harvesting",
    "monsoon", "salinity", "saline", "arsenic", "fluoride", "nitrate", "iron", "pumping",
    "pump", "irrigation", "depth", "level", "levels", "table", "water table", "piezometer",
    "dwlr", "telemetry", "naquim", "pmksy", "contamination", "potable", "drinking", "fluorosis",
    "drought", "alluvium", "alluvial", "basalt", "hard rock", "crystalline", "granite", "gneiss",
    "limestone", "karst", "soil", "farmer", "agriculture", "catchment", "river", "basin",
    "ganga", "yamuna", "indus", "godavari", "krishna", "cauvery", "brahmaputra", "narmada",
    "tapi", "bcm", "ham", "mcm", "hectare", "specific yield", "transmissivity", "porosity",
    "safe", "semi-critical", "critical", "over-exploited", "overexploited", "stage of extraction",
    "soe", "availability", "replenishment", "percolation", "check dam", "trench", "dyke",
    "spring", "springs", "dhara", "naula", "amrit sarovar", "mission", "policy", "cgwa",
    "guidelines", "noc", "abstraction", "sustainable", "depletion", "falling", "rising",

    # All Indian States & UTs (lowercase)
    "andaman", "nicobar", "andhra", "arunachal", "pradesh", "assam", "bihar", "chandigarh",
    "chhattisgarh", "dadra", "nagar", "haveli", "daman", "diu", "delhi", "goa", "gujarat",
    "haryana", "himachal", "jammu", "kashmir", "jharkhand", "karnataka", "kerala", "ladakh",
    "lakshadweep", "madhya", "maharashtra", "manipur", "meghalaya", "mizoram", "nagaland",
    "odisha", "puducherry", "punjab", "rajasthan", "sikkim", "tamil", "nadu", "tamilnadu",
    "telangana", "tripura", "uttar", "uttarakhand", "bengal", "india", "national"
}


class GroundedGenerator:
    def __init__(self, gemini_api_key: Optional[str] = settings.GEMINI_API_KEY):
        self.gemini_api_key = gemini_api_key
        self.gemini_model = None

        if self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("Initialized Gemini LLM generation pipeline.")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini LLM ({e}), using local synthesis.")

    def is_in_domain(self, query: str) -> bool:
        """
        Check if query pertains to groundwater, hydrology, water policy, or Indian geography.
        """
        tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", query.lower()))
        return bool(tokens.intersection(GROUNDWATER_DOMAIN_TERMS))

    def generate(
        self,
        query: str,
        retrieved_chunks: List[Tuple[DocumentChunk, float]],
        min_threshold: float = settings.SIMILARITY_THRESHOLD
    ) -> Tuple[str, List[Citation], float, bool, str]:
        """
        Synthesize answer from retrieved chunks with verifiable citations.
        Applies adaptive thresholds:
        - In-domain inquiries are never falsely blocked by rigid cutoffs.
        - Out-of-domain queries (e.g. stock prices, sports) are safely refused.
        """
        in_domain = self.is_in_domain(query)
        top_score = retrieved_chunks[0][1] if retrieved_chunks else 0.0

        # Safe refusal ONLY if the query is clearly out of domain AND score is low
        if not in_domain and top_score < 0.28:
            refusal_answer = (
                "The current WaterBoy groundwater intelligence knowledge base does not contain "
                "sufficient documented evidence to reliably answer this question. "
                "Please query specific Indian states, districts, Central Ground Water Board (CGWB) "
                "assessment metrics, or groundwater conservation schemes (e.g., Atal Bhujal Yojana, "
                "Jal Jeevan Mission, dynamic resource estimation)."
            )
            return (refusal_answer, [], 0.0, False, "rule-based-guard")

        # For in-domain questions, accept chunks adaptively
        effective_threshold = 0.15 if in_domain else min_threshold
        relevant_chunks = [
            (chunk, score) for chunk, score in retrieved_chunks if score >= effective_threshold
        ]

        # If somehow none met effective threshold but in-domain chunks exist, take the top available
        if not relevant_chunks and retrieved_chunks and in_domain:
            relevant_chunks = retrieved_chunks[:3]

        if not relevant_chunks:
            refusal_answer = (
                "The current WaterBoy groundwater intelligence knowledge base does not contain "
                "sufficient documented evidence to reliably answer this question. "
                "Please query specific Indian states, districts, Central Ground Water Board (CGWB) "
                "assessment metrics, or groundwater conservation schemes."
            )
            return (refusal_answer, [], 0.0, False, "rule-based-guard")

        # Build Citations
        citations: List[Citation] = []
        for i, (chunk, score) in enumerate(relevant_chunks, start=1):
            meta = chunk.metadata
            sentences = re.split(r"(?<=[.!?])\s+", chunk.text.strip())
            excerpt = sentences[0] if sentences else chunk.text[:180]
            if len(excerpt) > 200:
                excerpt = excerpt[:197] + "..."

            citations.append(
                Citation(
                    chunk_id=chunk.chunk_id,
                    source_doc=meta.get("source_doc", "CGWB Report"),
                    title=meta.get("title", "Groundwater Resource Assessment"),
                    section=meta.get("section", "General"),
                    state=meta.get("state"),
                    district=meta.get("district"),
                    year=meta.get("year", "2021-2025"),
                    relevance_score=round(score, 3),
                    excerpt=excerpt
                )
            )

        # Confidence calculation based on top score and mean
        mean_score = sum(s for _, s in relevant_chunks) / len(relevant_chunks)
        confidence = round(min(1.0, max(0.40, (top_score * 0.7 + mean_score * 0.3))), 2)

        # Attempt Gemini generation if configured
        if self.gemini_model:
            try:
                answer = self._generate_with_gemini(query, relevant_chunks)
                return (answer, citations, confidence, True, "gemini-1.5-flash")
            except Exception as e:
                logger.warning(f"Gemini API call failed ({e}); falling back to local factual synthesis.")

        # Local factual synthesis engine
        answer = self._generate_local_synthesis(query, relevant_chunks, citations)
        return (answer, citations, confidence, True, "local-grounded-synthesizer")

    def _generate_with_gemini(
        self,
        query: str,
        chunks_with_scores: List[Tuple[DocumentChunk, float]]
    ) -> str:
        """Synthesize with Gemini using strict grounding prompt."""
        context_blocks = []
        for i, (chunk, _) in enumerate(chunks_with_scores, start=1):
            meta = chunk.metadata
            loc = f"State: {meta.get('state', 'National')}"
            if meta.get("district"):
                loc += f", District: {meta.get('district')}"
            context_blocks.append(
                f"[{i}] (Source: {meta.get('title', 'Report')}, {loc})\n{chunk.text}"
            )
        context_str = "\n\n".join(context_blocks)

        prompt = f"""You are WaterBoy, an authoritative Groundwater Intelligence assistant.
Answer the following groundwater inquiry strictly based on the provided evidence contexts below.
Rules:
1. Cite evidence using bracketed numbers like [1], [2] immediately following stated facts.
2. If the context does not contain enough evidence, explicitly state what is missing.
3. Be professional, quantitative, and concise. Highlight key metrics (annual recharge, extraction %, category, rainfall) when available.

Context:
{context_str}

User Question: {query}

Answer:"""
        response = self.gemini_model.generate_content(prompt)
        return response.text.strip()

    def _generate_local_synthesis(
        self,
        query: str,
        chunks_with_scores: List[Tuple[DocumentChunk, float]],
        citations: List[Citation]
    ) -> str:
        """
        Extractive & grounded factual synthesis engine.
        Synthesizes the key findings from retrieved chunks and embeds citations [1], [2].
        """
        query_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", query.lower()))
        synthesis_paragraphs = []

        # Find most relevant sentences across chunks
        for i, (chunk, score) in enumerate(chunks_with_scores, start=1):
            text = chunk.text.strip()
            
            # Check if chunk contains a mathematical formula or bullet list
            if "$$" in text or "Stage of Ground Water Extraction (%)" in text:
                for p in text.split("\n\n"):
                    if any(term in p.lower() for term in query_words if len(term) > 3):
                        synthesis_paragraphs.append(p.strip() + f" [{i}]")
                        break
                continue

            # Check if chunk is a multi-year trajectory chunk
            if "Multi-Year Assessment Series" in text or "Historical Groundwater Indicators" in text:
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                trajectory_summary = "\n".join(lines[:6]) + f" [{i}]"
                synthesis_paragraphs.append(trajectory_summary)
                continue

            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 15]
            
            # Score sentences based on term overlap with query
            scored_sentences = []
            for s in sentences:
                s_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", s.lower()))
                overlap = len(query_words.intersection(s_words))
                scored_sentences.append((s, overlap))

            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [s for s, ov in scored_sentences[:3] if ov > 0]
            
            if not top_sentences and sentences:
                top_sentences = [sentences[0]]

            if top_sentences:
                paragraph = " ".join(top_sentences) + f" [{i}]"
                synthesis_paragraphs.append(paragraph)

        # Assemble cohesive answer
        if synthesis_paragraphs:
            main_body = "\n\n".join(synthesis_paragraphs)
        else:
            main_body = chunks_with_scores[0][0].text[:400] + " [1]"

        # Add a summary header if multiple sources
        primary_title = citations[0].title
        header = f"**Groundwater Assessment Summary ({primary_title})**:"
        
        return f"{header}\n\n{main_body}"
