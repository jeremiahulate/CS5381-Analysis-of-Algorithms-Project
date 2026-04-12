import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import os
import warnings

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
warnings.filterwarnings("ignore")

import random

from src.retrieval.faiss_retriever import FaissRetriever
from src.evolve.engine import rag_guided_mutation

docs = [
    "If a ghost is nearby, prioritize survival and move away.",
    "When safe, prioritize food collection to improve score.",
    "Balance score, survival time, and movement efficiency.",
]

retriever = FaissRetriever(docs)

parent_code = '''def pacman_agent(state):
    return "move_randomly"
'''

query_text = "avoid ghosts and survive longer while still scoring"
results = retriever.retrieve(query_text, top_k=2)
retrieved_contexts = [r.text for r in results]

print("Retrieved:")
for item in retrieved_contexts:
    print("-", item)

new_code, summary = rag_guided_mutation(
    code=parent_code,
    rng=random.Random(42),
    retrieved_contexts=retrieved_contexts,
    language="python",
)

print("\nSummary:")
print(summary)

print("\nNew code:")
print(new_code)