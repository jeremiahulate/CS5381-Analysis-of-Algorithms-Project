from __future__ import annotations

from dataclasses import dataclass
from typing import List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

@dataclass
class RetrievedExample:
    text: str
    score: float
    index: int

class FaissRetriever:
    def __init__(
        self,
        documents: List[str],
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.documents = documents
        self.model = SentenceTransformer(model_name)

        embeddings = self.model.encode(documents, convert_to_numpy=True)
        embeddings = embeddings.astype("float32")

        faiss.normalize_L2(embeddings)
        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(embeddings)

    def retrieve(self, query_text: str, top_k: int = 3) -> List[RetrievedExample]:
        query = self.model.encode([query_text], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(query)

        scores, indices = self.index.search(query, top_k)

        results: List[RetrievedExample] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append(
                RetrievedExample(
                    text=self.documents[idx],
                    score=float(score),
                    index=int(idx),
                )
            )
        return results