import sys
from pathlib import Path

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from pathlib import Path

from src.embeddings.sbert import SBERTEmbedder
from src.vectordb.faiss_store import FaissStore


def main() -> None:
    embedder = SBERTEmbedder()
    chunks = [
        "FAISS is a library for efficient similarity search.",
        "Streamlit is used to build simple web apps in Python.",
        "A vector database stores embeddings for retrieval.",
    ]

    # Create metadata aligned with each chunk
    metas = [
        {"source": "demo", "chunk_id": 0, "text": chunks[0]},
        {"source": "demo", "chunk_id": 1, "text": chunks[1]},
        {"source": "demo", "chunk_id": 2, "text": chunks[2]},
    ]

    vectors = embedder.embed_texts(chunks)  # shape (n, dim), float32, normalized

    dim = vectors.shape[1]
    store = FaissStore(
        dim=dim,
        index_path=Path("data/indexes/index.faiss"),
        meta_path=Path("data/indexes/meta.jsonl"),
    )

    store.add(vectors, metas)
    store.save()

    print("Saved FAISS index to:", store.index_path)
    print("Saved metadata to:", store.meta_path)


if __name__ == "__main__":
    main()