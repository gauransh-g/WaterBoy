"""
Unit tests for FAISS vector store and hybrid retrieval.
"""

import tempfile
import numpy as np
from app.rag.chunker import DocumentChunk
from app.rag.vector_store import FaissVectorStore


def test_vector_store_add_and_search():
    dim = 4
    store = FaissVectorStore(embedding_dim=dim)
    
    # 2 mock chunks
    chunk1 = DocumentChunk("c1", "Groundwater recharge in Maharashtra", {"state": "Maharashtra"})
    chunk2 = DocumentChunk("c2", "Arsenic pollution in Bihar alluvium", {"state": "Bihar"})
    
    # Normalized mock embeddings
    emb1 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    emb2 = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    embeddings = np.stack([emb1, emb2])
    
    store.add_chunks([chunk1, chunk2], embeddings)
    assert store.total_count == 2
    
    # Query matching chunk 1
    query_emb = np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)
    results = store.search(query_emb, top_k=1)
    
    assert len(results) == 1
    assert results[0][0].chunk_id == "c1"
    assert results[0][1] >= 0.7  # Score close to 1.0


def test_vector_store_save_and_load():
    dim = 4
    store = FaissVectorStore(embedding_dim=dim)
    chunk = DocumentChunk("c_test", "CGWB estimation methodology", {"section": "Methodology"})
    emb = np.array([[0.5, 0.5, 0.5, 0.5]], dtype=np.float32)
    emb = emb / np.linalg.norm(emb)
    
    store.add_chunks([chunk], emb)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        store.save(tmp_dir)
        loaded_store = FaissVectorStore.load(tmp_dir)
        
        assert loaded_store.total_count == 1
        assert loaded_store.chunks[0].chunk_id == "c_test"
        assert loaded_store.chunks[0].metadata["section"] == "Methodology"
