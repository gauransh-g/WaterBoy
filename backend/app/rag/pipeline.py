"""
End-to-end RAG Orchestrator for WaterBoy with Adaptive Search & Decadal History.
"""

import time
import re
import logging
from typing import Optional, List, Tuple
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import FaissVectorStore
from app.rag.generator import GroundedGenerator
from app.models.schemas import ChatRequest, ChatResponse, SearchRequest, SearchResponse, SearchResult
from app.config import settings

logger = logging.getLogger("waterboy.pipeline")

# All 38 States and Union Territories of India
ALL_INDIAN_STATES_UTS = [
    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam",
    "Bihar", "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli", "Daman and Diu",
    "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir",
    "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha",
    "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Tamilnadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
]


class RagPipeline:
    def __init__(
        self,
        vector_store: FaissVectorStore,
        embedding_service: Optional[EmbeddingService] = None,
        generator: Optional[GroundedGenerator] = None
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service or EmbeddingService.get_instance()
        self.generator = generator or GroundedGenerator()

    def detect_intent(self, query: str) -> str:
        """Categorize user query intent."""
        q = query.lower()
        if any(w in q for w in ["what is", "define", "explain", "meaning", "concept"]):
            return "concept_explanation"
        if any(w in q for w in ["how much", "percentage", "statistics", "data", "stage of extraction", "recharge", "numbers"]):
            return "quantitative_inquiry"
        if any(w in q for w in ["scheme", "atal bhujal", "jal jeevan", "policy", "government", "subsidy", "mission"]):
            return "policy_scheme"
        if any(w in q for w in ["method", "technique", "conservation", "rainwater harvesting", "recharge well", "structure"]):
            return "conservation_technique"
        if any(w in q for w in ["trend", "history", "decline", "rising", "level", "decadal", "last 5", "last 10", "trajectory"]):
            return "historical_trend"
        return "general_groundwater_query"

    def extract_location_hints(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Identify state or district mentions across all 38 Indian states & UTs."""
        q_lower = query.lower()
        found_state = None
        for state in ALL_INDIAN_STATES_UTS:
            if state.lower() in q_lower:
                found_state = state
                break

        # Check for district mentions like "... district"
        district_match = re.search(r"(\w+)\s+district", q_lower)
        found_district = district_match.group(1).capitalize() if district_match else None

        return found_state, found_district

    def answer_query(self, request: ChatRequest) -> ChatResponse:
        """Process chat inquiry and return grounded response."""
        start_time = time.perf_counter()
        
        # Detect intent and extract locations if not explicitly supplied
        intent = self.detect_intent(request.query)
        inferred_state, inferred_district = self.extract_location_hints(request.query)
        
        filter_state = request.filter_state or inferred_state
        filter_district = request.filter_district or inferred_district

        # Embed query
        query_embedding = self.embedding_service.encode([request.query])

        # Retrieve candidate chunks with intelligent fallback
        retrieved = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            filter_state=filter_state,
            filter_district=filter_district,
            filter_category=request.filter_category,
            query_text=request.query
        )

        # Fallback: If filtered by state yielded fewer than 2 chunks, perform global search
        if len(retrieved) < 2 and filter_state:
            logger.info(f"Filtered search for {filter_state} yielded {len(retrieved)} chunks; falling back to global search.")
            retrieved_global = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=request.top_k,
                query_text=request.query
            )
            if len(retrieved_global) > len(retrieved):
                retrieved = retrieved_global

        # Generate answer with citations
        answer, citations, confidence, has_evidence, model_used = self.generator.generate(
            query=request.query,
            retrieved_chunks=retrieved,
            min_threshold=settings.SIMILARITY_THRESHOLD
        )

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return ChatResponse(
            query=request.query,
            answer=answer,
            citations=citations,
            confidence_score=confidence,
            has_sufficient_evidence=has_evidence,
            query_intent=intent,
            execution_time_ms=latency_ms,
            model_used=model_used,
            state_context=filter_state,
            district_context=filter_district
        )

    def search_chunks(self, request: SearchRequest) -> SearchResponse:
        """Direct chunk search with hybrid semantic scoring."""
        start_time = time.perf_counter()
        query_embedding = self.embedding_service.encode([request.query])

        results_with_scores = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            filter_state=request.filter_state,
            filter_district=request.filter_district,
            filter_category=request.filter_category,
            query_text=request.query
        )

        results = [
            SearchResult(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                metadata=chunk.metadata,
                score=round(score, 4)
            )
            for chunk, score in results_with_scores
        ]

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return SearchResponse(
            query=request.query,
            results=results,
            total_matches=len(results),
            latency_ms=latency_ms
        )
