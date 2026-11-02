"""
Integration tests for FastAPI endpoints using TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.rag.chunker import DocumentChunk
from app.rag.vector_store import FaissVectorStore
from app.rag.pipeline import RagPipeline
from app.api.routes_chat import set_pipeline
import numpy as np


class MockEmbeddingService:
    dim = 384
    def encode(self, texts, normalize=True):
        if isinstance(texts, str):
            texts = [texts]
        vec = np.ones((len(texts), 384), dtype=np.float32)
        return vec / np.linalg.norm(vec, axis=1, keepdims=True)


@pytest.fixture(scope="module")
def client():
    # Setup test pipeline with in-memory store
    store = FaissVectorStore(embedding_dim=384)
    chunk = DocumentChunk(
        chunk_id="test_chunk_cgwb",
        text="The Central Ground Water Board assesses groundwater under GEC-2015 methodology.",
        metadata={
            "source_doc": "01_cgwb_methodology.md",
            "title": "CGWB Methodology",
            "state": "National"
        }
    )
    # Normalized embedding
    emb = np.ones((1, 384), dtype=np.float32)
    emb = emb / np.linalg.norm(emb)
    store.add_chunks([chunk], emb)

    pipeline = RagPipeline(vector_store=store, embedding_service=MockEmbeddingService())
    set_pipeline(pipeline)

    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "total_indexed_chunks" in data


def test_chat_endpoint_valid(client):
    payload = {"query": "How does CGWB assess groundwater?", "top_k": 3}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert "confidence_score" in data
    assert "execution_time_ms" in data


def test_chat_endpoint_empty_query(client):
    payload = {"query": "   "}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 400


def test_groundwater_summary_endpoint(client):
    response = client.get("/api/groundwater/summary")
    assert response.status_code == 200
    data = response.json()
    assert "assessment_year" in data
    assert "total_states_covered" in data
