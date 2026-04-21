from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

@dataclass
class KnowledgeChunk:
    text: str
    source: str

def chunk_text(text: str, chunk_size: int = 200, overlap: int = 40) -> List[str]:
    text = text.strip()
    if not text:
        return []

    chunks: List[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def load_knowledge_documents(
    folder: str = "Data/knowledge",
    include_files: List[str] | None = None,
) -> List[KnowledgeChunk]:
    base = Path(folder)
    documents: List[KnowledgeChunk] = []

    if include_files is None:
        paths = sorted(base.glob("*.txt"))
    else:
        paths = [base / name for name in include_files]

    for path in paths:
        if not path.exists():
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_text(text, chunk_size=200, overlap=40)

        for chunk in chunks:
            documents.append(
                KnowledgeChunk(
                    text=chunk,
                    source=path.name,
                )
            )

    if not documents:
        raise ValueError(f"No knowledge documents found in: {base}")

    return documents