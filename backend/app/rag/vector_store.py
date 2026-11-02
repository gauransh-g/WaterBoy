"""
Vector Store with FAISS, ChromaDB, and NumPy backends.
Provides resilient cosine similarity search, persistence, metadata filtering, and hybrid retrieval.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from app.rag.chunker import DocumentChunk
from app.config import settings

logger = logging.getLogger("waterboy.vector_store")

# Attempt importing FAISS safely
_FAISS_AVAILABLE = False
try:
    import faiss
    _FAISS_AVAILABLE = True
except Exception as e:
    logger.warning(f"FAISS native library unavailable ({e}); utilizing high-performance NumPy cosine index.")


class FaissVectorStore:
    """
    Resilient Vector Store supporting dense embeddings, cosine similarity search,
    hybrid lexical re-ranking, and metadata filtering.
    """
    def __init__(self, embedding_dim: int = settings.EMBEDDING_DIM):
        self.dim = embedding_dim
        self.chunks: List[DocumentChunk] = []
        self.chunk_id_to_idx: Dict[str, int] = {}
        self.embeddings: Optional[np.ndarray] = None
        self.faiss_index = None

        if _FAISS_AVAILABLE:
            try:
                self.faiss_index = faiss.IndexFlatIP(self.dim)
            except Exception as e:
                logger.warning(f"Could not instantiate FAISS IndexFlatIP: {e}")
                self.faiss_index = None

    def add_chunks(self, chunks: List[DocumentChunk], embeddings: np.ndarray) -> None:
        """Add chunks and their normalized embeddings."""
        if len(chunks) == 0:
            return
        
        assert len(chunks) == embeddings.shape[0], "Chunks and embeddings count mismatch"
        start_idx = len(self.chunks)

        if self.embeddings is None:
            self.embeddings = embeddings.astype(np.float32)
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings.astype(np.float32)])

        if self.faiss_index is not None:
            try:
                self.faiss_index.add(embeddings.astype(np.float32))
            except Exception as e:
                logger.warning(f"FAISS add failed ({e}); falling back to NumPy matrix.")
                self.faiss_index = None

        for i, chunk in enumerate(chunks):
            self.chunks.append(chunk)
            self.chunk_id_to_idx[chunk.chunk_id] = start_idx + i

        logger.info(f"Added {len(chunks)} chunks to vector index. Total items: {len(self.chunks)}")

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filter_state: Optional[str] = None,
        filter_district: Optional[str] = None,
        filter_category: Optional[str] = None,
        query_text: Optional[str] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Search for top_k most similar chunks.
        Computes cosine similarity (dot product on L2-normalized embeddings)
        and applies hybrid lexical scoring and metadata filtering.
        """
        if len(self.chunks) == 0 or self.embeddings is None:
            return []

        q_vec = query_embedding.astype(np.float32)
        if q_vec.ndim == 1:
            q_vec = q_vec.reshape(1, -1)

        # Dense retrieval scores: dot product of normalized vectors
        scores = np.dot(self.embeddings, q_vec.T).flatten()

        query_tokens = set(query_text.lower().split()) if query_text else set()
        candidates: List[Tuple[DocumentChunk, float]] = []

        for idx, score in enumerate(scores):
            chunk = self.chunks[idx]
            meta = chunk.metadata

            # Metadata filtering
            if filter_state and meta.get("state"):
                if filter_state.lower() not in meta["state"].lower():
                    continue
            if filter_district and meta.get("district"):
                if filter_district.lower() not in meta["district"].lower():
                    continue
            if filter_category and meta.get("category"):
                if filter_category.lower() not in meta["category"].lower():
                    continue

            # Hybrid lexical boost
            final_score = float(score)
            if query_tokens:
                text_lower = chunk.text.lower()
                matches = sum(1 for token in query_tokens if len(token) > 2 and token in text_lower)
                lexical_overlap = matches / max(len(query_tokens), 1)
                final_score = 0.70 * float(score) + 0.30 * float(lexical_overlap)

                # Prioritize conceptual guidelines when conceptual terms are requested
                conceptual_terms = {"formula", "methodology", "calculate", "definition", "criteria", "scheme", "yojana", "structure", "limit", "standards"}
                if conceptual_terms.intersection(query_tokens) and meta.get("section") == "Official Guidelines and Methodology":
                    final_score += 0.20

            candidates.append((chunk, final_score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_k]

    def save(self, index_dir: Path | str) -> None:
        """Persist vector index and metadata to disk."""
        target_dir = Path(index_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        meta_file = target_dir / "metadata.json"
        emb_file = target_dir / "embeddings.npy"

        if self.embeddings is not None:
            np.save(str(emb_file), self.embeddings)

        chunks_data = [chunk.to_dict() for chunk in self.chunks]
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)

        if self.faiss_index is not None and _FAISS_AVAILABLE:
            try:
                faiss_file = target_dir / "faiss.index"
                faiss.write_index(self.faiss_index, str(faiss_file))
            except Exception as e:
                logger.warning(f"Could not write faiss.index: {e}")

        logger.info(f"Saved vector index ({len(self.chunks)} items) to {target_dir}")

    @classmethod
    def load(cls, index_dir: Path | str) -> "FaissVectorStore":
        """Load vector index and metadata from disk."""
        target_dir = Path(index_dir)
        meta_file = target_dir / "metadata.json"
        emb_file = target_dir / "embeddings.npy"
        faiss_file = target_dir / "faiss.index"

        if not meta_file.exists() or not emb_file.exists():
            raise FileNotFoundError(f"Vector index files not found in {target_dir}")

        embeddings = np.load(str(emb_file))
        store = cls(embedding_dim=embeddings.shape[1])
        store.embeddings = embeddings.astype(np.float32)

        with open(meta_file, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)

        for i, item in enumerate(chunks_data):
            chunk = DocumentChunk(
                chunk_id=item["chunk_id"],
                text=item["text"],
                metadata=item["metadata"]
            )
            store.chunks.append(chunk)
            store.chunk_id_to_idx[chunk.chunk_id] = i

        if faiss_file.exists() and _FAISS_AVAILABLE:
            try:
                store.faiss_index = faiss.read_index(str(faiss_file))
            except Exception as e:
                logger.warning(f"Could not load faiss.index ({e}), using NumPy cosine matrix.")

        logger.info(f"Loaded vector index ({len(store.chunks)} items) from {target_dir}")
        return store

    @property
    def total_count(self) -> int:
        return len(self.chunks)
