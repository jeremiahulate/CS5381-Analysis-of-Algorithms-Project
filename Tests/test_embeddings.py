import sys
from pathlib import Path

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"           # quiet TF logs
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1" # hide HF symlink warning (Windows)

from src.embeddings.sbert import SBERTEmbedder

embedder = SBERTEmbedder()

chunks = [
    "FAISS is a library for efficient similarity search.",
    "Streamlit is used to build simple web apps in Python.",
    "A vector database stores embeddings for retrieval.",
]

q = "What is FAISS used for?"

chunk_vecs = embedder.embed_texts(chunks)
q_vec = embedder.embed_query(q)

print("Chunks shape:", chunk_vecs.shape)
print("Query shape:", q_vec.shape)
print("Dim:", chunk_vecs.shape[1])