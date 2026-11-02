"""
Embeddings generator wrapping SentenceTransformer with L2 normalization.
"""

import os
import logging
from typing import List
import numpy as np

os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from sentence_transformers import SentenceTransformer
from app.config import settings

logger = logging.getLogger("waterboy.embeddings")


class EmbeddingService:
    _instance = None

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding model ready. Dimensionality: {self.dim}")

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = EmbeddingService()
        return cls._instance

    def encode(self, texts: List[str] | str, normalize: bool = True) -> np.ndarray:
        """
        Encode a string or list of strings into float32 numpy embeddings.
        Normalized embeddings allow inner product to compute exact cosine similarity.
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self.model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=normalize
        )
        return embeddings.astype(np.float32)

