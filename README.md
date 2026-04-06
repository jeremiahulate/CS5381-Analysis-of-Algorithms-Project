# CS5381 Evolutionary Algorithm Agent (AlgoChat)

This project implements a simplified evolutionary agent inspired by **AlphaEvolve**, designed to iteratively improve code or algorithmic solutions using fitness-based evaluation and mutation strategies.

The system integrates:
- Evolutionary algorithms
- LLM-guided mutation (with fallback)
- FAISS + SBERT (vector database)
- A Streamlit-based UI

---

## Current Prototype Features

### Evolution Engine
- Generates candidate programs across generations
- Supports multiple mutation modes:
  - `none` → baseline (no change)
  - `random` → rule-based mutation
  - `llm` → LLM-guided mutation (or fallback)
- Top-k selection strategy
- Tracks best candidate across generations

Core implementation in: 
- src/evolve/engine.py

---

### LLM Mutation ( with Fallback)

The system supports **LLM-guided mutation** with a safe fallback:

- Uses API-based mutation when available
- Falls back to a heuristic mutator if no API key is provided

#### Example:

```python```
LLMSettings(provider="heuristic")

- Heuristic mutator ensures the system works offline
- API mutation uses OpenAI-compatible endpoints when configured

See: src/evolve/generator.py
This includes:
- HeursticLLMMutator (offline fallback)
- OpenAiCompatibleMutator (API-based)
- Automatic fallback if API fails

---

### Fitness & Evolution

## Fitness function:
- Fitness = w1 * score + w2 * survival_time - w3 * steps
  - Score -> maximize
  - Survival time -> maximize
  - Steps (cost) -> minimize
- Evaluation uses a deterministic stub evaluator

See:
- src/evolve/fitness.py
- src/evolve/evaluator.py

---

### Streamlit UI

The UI allows users to:

- Input algorithm description or psuedocode
- Provide inital code
- adjust fitness weights
- Choose mutation mode
- Set number of generations

Displays:

- Best fitness
- Best solution
- Raw metrics (score, survival time, steps)
- Fitness progression graph

---

### Vector Database (FAISS + SBERT)

The database includes:

- Sentence embeddings via SBERT
- FAISS index for similarity search
- Supports future retrieval-augmented mutation

See:

- src/embeddings/sbert.py
- src/vectordb/faiss_store.py

---

### Project Structure

```text
src/
├── evolve/
│   ├── engine.py        # Evolution loop
│   ├── evaluator.py     # Candidate evaluation
│   ├── fitness.py       # Fitness computation
│   ├── generator.py     # Mutation (LLM + heuristic)
│
├── embeddings/
│   └── sbert.py         # Embedding model
│
├── vectordb/
│   └── faiss_store.py   # FAISS interface

UI/
└── streamlit_app.py     # Frontend UI

Data/
└── indexes/             # FAISS index storage

Tests/
└── test_*.py            # Unit tests
```
---

### How to Run

1. Clone Repository:

- git clone https://github.com/jeremiahulate/CS5381-Analysis-of-Algorithms-Project.git
- cd CS5381-Analysis-of-Algorithms-Project

3. Create virtual environment:

- python -m venv .venv
- .\.venv\Scripts\Activate.ps1

4. Install Dependencies:

- pip install -r requirements-prototype.txt
- pip install -e .
The dependencies include:

- Streamlit
- FAISS
- SBERT
- Optional OpenAI support

5. Run the UI:

- streamlit run UI/streamlit_app.py

## Running Prototype Scripts

You can test the evolution system directly with:
- python Scripts/run_prototype_check.py

This will run:

- LLM mutation mode
- Fitness evaluation
- Evolution loop

Example usage includes:

- LLM mutation with fallback
- Mutation summaries per generation

---

### Experiment Modes

This system supports:

- No evolution
- Random Mutation
- LLM-guided Mutation (heuristic or API)

These modes allow comparison of:

- Baseline performance
- Random Improvements
- Guided Improvements

---

### Current Limitations

- Pacman environment is simulated (stub evaluator)
- LLM mutation may use heuristic fallback if API not configured
- FAISS retrieval is implemented but not fully integrated into mutation loop

---

### Future Work

- Integrate real Pacman environment for evaluation
- Fully integrate FAISS retrieval into mutation generation
- Improve LLM mutation strategies
- Add multi-run experiment comparison (none vs random vs llm)
- Optimize search performance with caching

---

### References

AlphaEvolve (Google Research)
Evolutionary Algorithms
Sentence Transformers (SBERT)
FAISS (Facebook AI Similarity Search)
