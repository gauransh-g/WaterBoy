"""
WaterBoy Groundwater Intelligence Platform - FastAPI Main Application.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.rag.vector_store import FaissVectorStore
from app.rag.embeddings import EmbeddingService
from app.rag.pipeline import RagPipeline
from app.data.loader import KnowledgeIngestionPipeline
from app.data.groundwater_db import GroundwaterDatabase
from app.api.routes_chat import router as chat_router, set_pipeline
from app.api.routes_data import router as data_router
from app.api.routes_eval import router as eval_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("waterboy")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event for initializing vector store, knowledge base, and pipeline."""
    import app.api.routes_chat as rc
    if rc._pipeline is not None:
        logger.info("Pipeline already configured (e.g. test fixture). Skipping full initialization.")
        yield
        return

    logger.info("Initializing WaterBoy Groundwater Intelligence Platform...")

    # Ensure embedding model is ready
    embedding_service = EmbeddingService.get_instance()
    
    # Check if vector index exists or if ingestion is required
    index_file = settings.INDEX_DIR / "metadata.json"
    if not index_file.exists():
        logger.info(f"Vector index not found at {settings.INDEX_DIR}. Initiating initial ingestion...")
        ingestion = KnowledgeIngestionPipeline()
        vector_store = ingestion.run_full_ingestion()
    else:
        logger.info(f"Loading existing vector index from {settings.INDEX_DIR}...")
        vector_store = FaissVectorStore.load(settings.INDEX_DIR)
        # Ensure database is connected
        GroundwaterDatabase.get_instance()

    # Construct and register RAG Pipeline
    pipeline = RagPipeline(
        vector_store=vector_store,
        embedding_service=embedding_service
    )
    set_pipeline(pipeline)
    logger.info("WaterBoy RAG Pipeline successfully initialized and ready for requests.")

    yield

    logger.info("Shutting down WaterBoy backend.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Evidence-backed AI intelligence, RAG search, and analytics for India's groundwater resources.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat_router, prefix=settings.API_PREFIX, tags=["Conversational RAG"])
app.include_router(data_router, prefix=settings.API_PREFIX, tags=["Groundwater Analytics"])
app.include_router(eval_router, prefix=settings.API_PREFIX, tags=["Evaluation Benchmark"])


@app.get("/api/health", tags=["System"])
async def health_check():
    """Verify backend health, knowledge base readiness, and index count."""
    try:
        from app.api.routes_chat import get_pipeline
        pipeline = get_pipeline()
        total_chunks = pipeline.vector_store.total_count
        db = GroundwaterDatabase.get_instance()
        overview = db.get_national_overview()
        
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "total_indexed_chunks": total_chunks,
            "total_assessment_units": overview.total_assessment_units,
            "states_covered": overview.total_states_covered
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "degraded", "error": str(e)}
        )


@app.get("/", tags=["System"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_prefix": settings.API_PREFIX
    }
