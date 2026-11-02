"""
FastAPI Router for Structured Multi-Year Groundwater Assessment Metrics and Trends.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from app.models.schemas import GroundwaterOverview, StateSummary, AssessmentUnitData
from app.data.groundwater_db import GroundwaterDatabase

router = APIRouter()

def get_db() -> GroundwaterDatabase:
    return GroundwaterDatabase.get_instance()


@router.get("/groundwater/summary", response_model=GroundwaterOverview, summary="National groundwater overview")
async def get_overview(
    year: Optional[str] = Query(default=None, description="Optional year filter e.g. 2023-2024 or 'all'")
) -> GroundwaterOverview:
    """Retrieve national aggregate overview of dynamic groundwater resource assessment."""
    db = get_db()
    return db.get_national_overview(year=year)


@router.get("/groundwater/states", response_model=List[StateSummary], summary="State-wise groundwater statistics")
async def get_state_summaries(
    year: Optional[str] = Query(default=None, description="Optional year filter e.g. 2023-2024 or 'all'")
) -> List[StateSummary]:
    """Retrieve summarized statistics (Safe, Semi-Critical, Over-Exploited units) by state."""
    db = get_db()
    return db.get_state_summaries(year=year)


@router.get("/groundwater/trends", summary="Multi-year historical trends across 2021-2025")
async def get_groundwater_trends(
    state: Optional[str] = Query(default=None, description="Optional state name e.g. Delhi, Punjab")
) -> List[Dict[str, Any]]:
    """Retrieve multi-year progression of extraction rates, recharge, and category distributions."""
    db = get_db()
    return db.get_yearly_trends(state=state)


@router.get("/groundwater/district/{state}/{district}", response_model=List[AssessmentUnitData], summary="District assessment units across years")
async def get_district_data(
    state: str,
    district: str,
    year: Optional[str] = Query(default=None, description="Optional year filter")
) -> List[AssessmentUnitData]:
    """Retrieve assessment units and dynamic metrics for a specific district."""
    db = get_db()
    units = db.get_district_details(state, district, year=year)
    if not units:
        raise HTTPException(status_code=404, detail=f"No assessment records found for {district}, {state}")
    return units
