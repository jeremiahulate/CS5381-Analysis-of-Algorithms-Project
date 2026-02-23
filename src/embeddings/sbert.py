from __future__ import annotations

from dataclasses import dataclass
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

@dataclass
class SBERTEmbedder:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    def __post_init__(self) -> None:
        self.model = SentenceTransformer(self.model_name)

    def embed_texts(self, texts: List[str]) -> np.ndarray:

        vectors = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return np.asarray(vectors, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:

        v = self.model.encode(
            [query],
            show_progress_bar=False,
            normalize_embeddings=True,
        )[0]
        return np.asarray(v, dtype=np.float32)