"""
FastAPI Router for Groundwater RAG Chat and Search.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, SearchRequest, SearchResponse
from app.rag.pipeline import RagPipeline

router = APIRouter()

# Global pipeline instance injected on startup
_pipeline: RagPipeline | None = None

def set_pipeline(pipeline: RagPipeline):
    global _pipeline
    _pipeline = pipeline

def get_pipeline() -> RagPipeline:
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="RAG Pipeline not yet initialized")
    return _pipeline


@router.post("/chat", response_model=ChatResponse, summary="Ask WaterBoy groundwater questions")
async def chat_endpoint(
    request: ChatRequest,
    pipeline: RagPipeline = Depends(get_pipeline)
) -> ChatResponse:
    """
    Submit a natural language groundwater question.
    Returns evidence-backed answer with verifiable citations and confidence metrics.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return pipeline.answer_query(request)


@router.post("/search", response_model=SearchResponse, summary="Direct semantic chunk retrieval")
async def search_endpoint(
    request: SearchRequest,
    pipeline: RagPipeline = Depends(get_pipeline)
) -> SearchResponse:
    """Retrieve top matching document chunks with hybrid semantic and lexical scoring."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return pipeline.search_chunks(request)

