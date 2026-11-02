"""
FastAPI Router for Evaluation Benchmarks.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import BenchmarkSummary
from app.rag.pipeline import RagPipeline
from app.api.routes_chat import get_pipeline
from app.evaluation.benchmark import BenchmarkEvaluator

router = APIRouter()


@router.post("/evaluate", response_model=BenchmarkSummary, summary="Run automated groundwater benchmark")
async def run_evaluation(
    pipeline: RagPipeline = Depends(get_pipeline)
) -> BenchmarkSummary:
    """
    Executes the 10 gold-standard groundwater benchmark queries.
    Returns Precision@k, Recall@k, Faithfulness, Citation rate, Refusal accuracy, and Latency.
    """
    evaluator = BenchmarkEvaluator(pipeline)
    return evaluator.run_benchmark()

