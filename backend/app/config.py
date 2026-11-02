"""
Configuration settings for Waterboy Groundwater Intelligence Platform.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field

# Ensure TensorFlow does not conflict with HuggingFace/Protobuf
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    BASE_DIR: Path = BASE_DIR
    PROJECT_NAME: str = "WaterBoy Groundwater Intelligence Platform"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Embedding and Vector Store
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    INDEX_DIR: Path = BASE_DIR / "data_store" / "vector_index"
    DOCUMENTS_DIR: Path = BASE_DIR / "knowledge_base" / "documents"
    CGWB_DATA_DIR: Path = BASE_DIR / "knowledge_base" / "data"
    
    # RAG parameters
    DEFAULT_TOP_K: int = 4
    SIMILARITY_THRESHOLD: float = 0.35  # Minimum cosine similarity for relevance
    MAX_CONTEXT_TOKENS: int = 2000
    
    # Server & CORS
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]
    
    # Optional LLM API Key (if provided)
    GEMINI_API_KEY: str | None = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))

settings = Settings()
