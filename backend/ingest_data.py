"""
Offline / Standalone Knowledge and CGWB Data Ingestion Script for WaterBoy.
Builds the persistent SQLite database and FAISS/NumPy vector index.
"""

import sys
import logging
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings
from app.data.loader import KnowledgeIngestionPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    print("=" * 60)
    print("WaterBoy: Ingesting Knowledge Base and Central Ground Water Board Datasets")
    print("=" * 60)
    
    pipeline = KnowledgeIngestionPipeline()
    store = pipeline.run_full_ingestion()
    
    print("=" * 60)
    print(f"SUCCESS: Successfully indexed {store.total_count} chunks into {settings.INDEX_DIR}")
    print("=" * 60)

