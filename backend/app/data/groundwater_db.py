"""
Structured Groundwater Database for Central Ground Water Board (CGWB) Multi-Year Datasets.
Provides aggregated analytics, multi-year historical trends, state overviews, and district metrics.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

from app.models.schemas import AssessmentUnitData, StateSummary, GroundwaterOverview
from app.config import settings

logger = logging.getLogger("waterboy.database")


class GroundwaterDatabase:
    _instance = None

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (settings.BASE_DIR / "data_store" / "groundwater.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_tables()

    @classmethod
    def get_instance(cls) -> "GroundwaterDatabase":
        if cls._instance is None:
            cls._instance = GroundwaterDatabase()
        return cls._instance

    def _init_tables(self) -> None:
        """Create structured table for CGWB multi-year assessment units."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS assessment_units (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state TEXT NOT NULL,
                    district TEXT NOT NULL,
                    location_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    stage_of_extraction REAL,
                    total_recharge_ham REAL,
                    total_extraction_ham REAL,
                    availability_for_future_use_ham REAL,
                    rainfall_mm REAL,
                    geology TEXT,
                    water_table_trend TEXT,
                    assessment_year TEXT NOT NULL
                )
            """)
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_state ON assessment_units(state)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_district ON assessment_units(district)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON assessment_units(category)")
            self.conn.execute("CREATE INDEX IF NOT EXISTS idx_year ON assessment_units(assessment_year)")

    def clear_records(self) -> None:
        """Clear table before a fresh full multi-year ingestion."""
        with self.conn:
            self.conn.execute("DELETE FROM assessment_units")

    def insert_records(self, records: List[Dict[str, Any]]) -> int:
        """Bulk insert assessment unit records."""
        if not records:
            return 0
        
        insert_sql = """
            INSERT INTO assessment_units (
                state, district, location_name, category, stage_of_extraction,
                total_recharge_ham, total_extraction_ham, availability_for_future_use_ham,
                rainfall_mm, geology, water_table_trend, assessment_year
            ) VALUES (
                :state, :district, :location_name, :category, :stage_of_extraction,
                :total_recharge_ham, :total_extraction_ham, :availability_for_future_use_ham,
                :rainfall_mm, :geology, :water_table_trend, :assessment_year
            )
        """
        with self.conn:
            self.conn.executemany(insert_sql, records)
        return len(records)

    def get_national_overview(self, year: Optional[str] = None) -> GroundwaterOverview:
        """Aggregate national groundwater overview metrics for a given year or all years."""
        query = "SELECT * FROM assessment_units"
        params = []
        if year and year != "all":
            query += " WHERE assessment_year = ?"
            params.append(year)

        df = pd.read_sql_query(query, self.conn, params=params)
        if df.empty:
            return GroundwaterOverview(
                assessment_year=year or "Multi-Year (2021-2025)",
                total_states_covered=0,
                total_assessment_units=0,
                national_stage_of_extraction_avg=0.0,
                category_breakdown={},
                top_overexploited_states=[],
                dataset_source="Central Ground Water Board (CGWB) Dynamic Assessment Series"
            )

        cat_counts = df["category"].value_counts().to_dict()
        avg_stage = float(df[df["stage_of_extraction"] > 0]["stage_of_extraction"].mean()) if not df.empty else 0.0

        oe_df = df[df["category"].str.contains("Over", case=False, na=False)]
        top_oe = (
            oe_df.groupby("state")["id"]
            .count()
            .reset_index(name="over_exploited_units")
            .sort_values(by="over_exploited_units", ascending=False)
            .head(5)
            .to_dict(orient="records")
        )

        return GroundwaterOverview(
            assessment_year=year or "Multi-Year (2021-2025)",
            total_states_covered=int(df["state"].nunique()),
            total_assessment_units=int(len(df)),
            national_stage_of_extraction_avg=round(avg_stage, 2),
            category_breakdown={str(k): int(v) for k, v in cat_counts.items()},
            top_overexploited_states=top_oe,
            dataset_source="Central Ground Water Board (CGWB) Dynamic Assessment Series"
        )

    def get_state_summaries(self, year: Optional[str] = None) -> List[StateSummary]:
        """Compute summarized statistics by state, optionally filtered by year."""
        query = "SELECT * FROM assessment_units"
        params = []
        if year and year != "all":
            query += " WHERE assessment_year = ?"
            params.append(year)

        df = pd.read_sql_query(query, self.conn, params=params)
        if df.empty:
            return []

        summaries = []
        for state, grp in df.groupby("state"):
            safe = int((grp["category"].str.contains("Safe", case=False, na=False)).sum())
            semi = int((grp["category"].str.contains("Semi", case=False, na=False)).sum())
            crit = int((grp["category"].str.match(r"^Critical$", case=False, na=False)).sum())
            oe = int((grp["category"].str.contains("Over", case=False, na=False)).sum())
            saline = int((grp["category"].str.contains("Saline", case=False, na=False)).sum())

            valid_stages = grp[grp["stage_of_extraction"] > 0]["stage_of_extraction"]
            avg_st = float(valid_stages.mean()) if not valid_stages.empty else 0.0

            summaries.append(
                StateSummary(
                    state=str(state),
                    total_units=int(len(grp)),
                    safe_units=safe,
                    semi_critical_units=semi,
                    critical_units=crit,
                    over_exploited_units=oe,
                    saline_units=saline,
                    avg_stage_of_extraction=round(avg_st, 2),
                    total_annual_recharge_ham=round(float(grp["total_recharge_ham"].sum()), 2),
                    total_annual_extraction_ham=round(float(grp["total_extraction_ham"].sum()), 2)
                )
            )

        # Sort states and UTs in strict alphabetical order
        summaries.sort(key=lambda s: s.state.upper())
        return summaries

    def get_yearly_trends(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Aggregate multi-year historical trend statistics across years.
        Returns yearly progression of average extraction %, total recharge, and extraction.
        """
        query = "SELECT * FROM assessment_units"
        params = []
        if state and state.lower() != "all states":
            query += " WHERE LOWER(state) = LOWER(?)"
            params.append(state)

        df = pd.read_sql_query(query, self.conn, params=params)
        if df.empty:
            return []

        trends = []
        for year, grp in df.groupby("assessment_year"):
            valid_stages = grp[grp["stage_of_extraction"] > 0]["stage_of_extraction"]
            avg_st = float(valid_stages.mean()) if not valid_stages.empty else 0.0
            safe = int((grp["category"].str.contains("Safe", case=False, na=False)).sum())
            oe = int((grp["category"].str.contains("Over", case=False, na=False)).sum())

            trends.append({
                "year": str(year),
                "total_units": int(len(grp)),
                "avg_stage_of_extraction": round(avg_st, 2),
                "total_recharge_ham": round(float(grp["total_recharge_ham"].sum()), 2),
                "total_extraction_ham": round(float(grp["total_extraction_ham"].sum()), 2),
                "safe_units": safe,
                "over_exploited_units": oe
            })

        # Order chronologically
        trends.sort(key=lambda x: x["year"])
        return trends

    def get_district_details(
        self, state: str, district: str, year: Optional[str] = None
    ) -> List[AssessmentUnitData]:
        """Fetch all assessment units for a specific district across years or for a specific year."""
        query = """
            SELECT state, district, location_name, category, stage_of_extraction,
                   total_recharge_ham, total_extraction_ham, availability_for_future_use_ham,
                   rainfall_mm, geology, water_table_trend, assessment_year
            FROM assessment_units
            WHERE LOWER(state) = LOWER(?) AND LOWER(district) = LOWER(?)
        """
        params = [state, district]
        if year and year != "all":
            query += " AND assessment_year = ?"
            params.append(year)

        cursor = self.conn.cursor()
        rows = cursor.execute(query, params).fetchall()
        
        return [
            AssessmentUnitData(
                state=r[0],
                district=r[1],
                location_name=f"{r[2]} ({r[11]})",
                category=r[3],
                stage_of_extraction=r[4] or 0.0,
                total_recharge_ham=r[5] or 0.0,
                total_extraction_ham=r[6] or 0.0,
                availability_for_future_use_ham=r[7] or 0.0,
                rainfall_mm=r[8],
                geology=r[9],
                water_table_trend=r[10]
            )
            for r in rows
        ]
