from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import faiss
import numpy as np


@dataclass
class FaissStore:
    """
    A simple persistent FAISS store.

    - Uses IndexFlatIP (inner product).
    - Assumes vectors are L2-normalized so inner product ~= cosine similarity.
    - Persists:
        - FAISS index -> index.faiss
        - metadata (aligned with vectors) -> meta.jsonl
    """
    dim: int
    index_path: Path
    meta_path: Path

    def __post_init__(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)

        self.index: faiss.Index = faiss.IndexFlatIP(self.dim)
        self.metadata: List[Dict[str, Any]] = []

    @staticmethod
    def _as_float32_2d(x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float32)
        if x.ndim == 1:
            x = x.reshape(1, -1)
        return x

    def add(self, vectors: np.ndarray, metas: List[Dict[str, Any]]) -> None:
        vectors = self._as_float32_2d(vectors)

        if vectors.shape[1] != self.dim:
            raise ValueError(f"Vector dim mismatch: got {vectors.shape[1]}, expected {self.dim}")

        if len(metas) != vectors.shape[0]:
            raise ValueError("Metadata count must match number of vectors")

        self.index.add(vectors)
        self.metadata.extend(metas)

    def search(self, query_vec: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        query_vec = self._as_float32_2d(query_vec)

        scores, ids = self.index.search(query_vec, top_k)  # shapes: (1, k), (1, k)
        results: List[Dict[str, Any]] = []

        for score, idx in zip(scores[0].tolist(), ids[0].tolist()):
            if idx == -1:
                continue
            meta = dict(self.metadata[idx])
            meta["score"] = float(score)
            meta["id"] = int(idx)
            results.append(meta)

        return results

    def save(self) -> None:
        faiss.write_index(self.index, str(self.index_path))

        with self.meta_path.open("w", encoding="utf-8") as f:
            for item in self.metadata:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def load(self) -> None:
        if not self.index_path.exists():
            raise FileNotFoundError(f"Missing FAISS index file: {self.index_path}")
        if not self.meta_path.exists():
            raise FileNotFoundError(f"Missing metadata file: {self.meta_path}")

        self.index = faiss.read_index(str(self.index_path))
        self.metadata = []

        with self.meta_path.open("r", encoding="utf-8") as f:
            for line in f:
                self.metadata.append(json.loads(line))