"""
Pydantic schemas for API requests, responses, RAG results, and evaluation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class Citation(BaseModel):
    chunk_id: str
    source_doc: str
    title: str
    section: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    year: Optional[str] = None
    relevance_score: float
    excerpt: str


class ChatRequest(BaseModel):
    query: str = Field(..., description="Natural language groundwater inquiry")
    top_k: int = Field(default=4, ge=1, le=10, description="Number of context chunks to retrieve")
    filter_state: Optional[str] = Field(default=None, description="Optional state filter")
    filter_district: Optional[str] = Field(default=None, description="Optional district filter")
    filter_category: Optional[str] = Field(default=None, description="Optional category filter (e.g., Over-exploited, Safe)")


class ChatResponse(BaseModel):
    query: str
    answer: str
    citations: List[Citation]
    confidence_score: float
    has_sufficient_evidence: bool
    query_intent: str
    execution_time_ms: float
    model_used: str
    state_context: Optional[str] = None
    district_context: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filter_state: Optional[str] = None
    filter_category: Optional[str] = None


class SearchResult(BaseModel):
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    score: float


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResult]


class AssessmentUnitData(BaseModel):
    state: str
    district: str
    location_name: str
    category: str
    stage_of_extraction: float
    total_recharge_ham: float
    total_extraction_ham: float
    availability_for_future_use_ham: float
    rainfall_mm: Optional[float] = None
    geology: Optional[str] = None
    water_table_trend: Optional[str] = None


class StateSummary(BaseModel):
    state: str
    total_units: int
    safe_units: int
    semi_critical_units: int
    critical_units: int
    over_exploited_units: int
    saline_units: int
    avg_stage_of_extraction: float
    total_annual_recharge_ham: float
    total_annual_extraction_ham: float


class GroundwaterOverview(BaseModel):
    assessment_year: str
    total_states_covered: int
    total_assessment_units: int
    national_stage_of_extraction_avg: float
    category_breakdown: Dict[str, int]
    top_overexploited_states: List[Dict[str, Any]]
    dataset_source: str


class TestCaseResult(BaseModel):
    question: str
    expected_topics: List[str]
    retrieved_chunk_ids: List[str]
    retrieval_hit: bool
    faithfulness_score: float
    has_citations: bool
    refusal_correctness: bool
    latency_ms: float
    status: str


class BenchmarkSummary(BaseModel):
    total_tests: int
    passed_tests: int
    retrieval_precision_at_k: float
    retrieval_recall_at_k: float
    faithfulness_score_avg: float
    citation_rate: float
    unsupported_query_refusal_accuracy: float
    avg_latency_ms: float
    test_results: List[TestCaseResult]

