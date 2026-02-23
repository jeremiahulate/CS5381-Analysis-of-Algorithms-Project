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

    # We know all-MiniLM-L6-v2 is 384 dims, but we can infer after embedding:
    q = "What is FAISS used for?"
    q_vec = embedder.embed_query(q)
    dim = q_vec.shape[0]

    store = FaissStore(
        dim=dim,
        index_path=Path("data/indexes/index.faiss"),
        meta_path=Path("data/indexes/meta.jsonl"),
    )
    store.load()

    results = store.search(q_vec, top_k=3)

    print("Question:", q)
    for r in results:
        print("\n---")
        print("Score:", r["score"])
        print("Source:", r.get("source"))
        print("Chunk:", r.get("chunk_id"))
        print("Text:", r.get("text"))


if __name__ == "__main__":
    main()