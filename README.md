# CS5381 Evolutionary Algorithm Agent (AlgoChat)

This project implements a simplified evolutionary agent inspired by **AlphaEvolve**, designed to iteratively improve code or algorithmic solutions using fitness-based evaluation and mutation strategies.

The system integrates:
- Evolutionary algorithms
- Local LLM-guided mutation (llama.cpp server)
- FAISS + SBERT (vector database)
- A Streamlit-based UI

---

## 🚀 Prototype Features

### Evolution Engine
- Generates candidate programs across generations
- Supports multiple mutation modes:
  - `none` → baseline (no change)
  - `random` → rule-based mutation
  - `llm` → LLM-guided mutation (local)
- Top-k selection strategy
- Tracks best candidate across generations

Core implementation:
- `src/evolve/engine.py`

---

## 🧠 LLM Mutation (Local - llama.cpp Server)

The system uses a **locally hosted LLM via llama.cpp (`llama-server`)**:

- Runs entirely on the user's machine (no API required)
- Uses HTTP requests instead of subprocess calls
- Avoids repeated model loading → improves performance
- Ensures privacy and offline capability

### Why llama-server?
- Faster than `llama-cli` (no reload per generation)
- Required for iterative evolutionary loops
- Supports scalable mutation generation

### Mutation Constraints (IMPORTANT)

To ensure valid outputs, the system enforces:

- Must return exactly one function:
  
  def pacman_agent(state):

- No helper functions allowed
- Must return valid actions only:
  - "run_away"
  - "eat_food"
  - "wait"

### Validation Layer

The system includes strict validation:

- Syntax validation (`ast.parse`)
- Function structure validation
- Domain-specific validation (allowed actions)
- Rejects invalid or malformed LLM outputs

File:
- `src/evolve/generator.py`

---

## ⚙️ Fitness & Evaluation

### Fitness Function:
Fitness = w1 * score + w2 * survival_time - w3 * steps

- Score → maximize
- Survival time → maximize
- Steps → minimize

Evaluation uses a **deterministic stub environment**.

Files:
- `src/evolve/fitness.py`
- `src/evolve/evaluator.py`

---

## 🖥️ Streamlit UI

The UI allows users to:

- Input **initial code (required)**
- Input **algorithm description (optional)**
- Adjust fitness weights
- Choose mutation mode
- Set number of generations

### Displays:
- Best fitness score
- Best solution
- Raw metrics (score, survival time, steps)
- Fitness progression graph
- CSV export of results

---

## 🧠 Vector Database (FAISS + SBERT)

- Sentence embeddings via SBERT
- FAISS index for similarity search
- Designed for future retrieval-augmented mutation

Files:
- `src/embeddings/sbert.py`
- `src/vectordb/faiss_store.py`

---

## 📂 Project Structure

src/
├── evolve/
│   ├── engine.py
│   ├── evaluator.py
│   ├── fitness.py
│   ├── generator.py
│
├── embeddings/
│   └── sbert.py
│
├── vectordb/
│   └── faiss_store.py

Scripts/
├── build_faiss_index.py
├── query_faiss_index.py
└── run_prototype_check.py

UI/
└── UI.py

Data/
└── indexes/

Tests/
└── test_*.py

---

## ▶️ How to Run

### 1. Clone Repo
git clone https://github.com/jeremiahulate/CS5381-Analysis-of-Algorithms-Project.git

### 2. Setup Environment
python -m venv .venv  
.\.venv\Scripts\Activate.ps1

### 3. Install Dependencies
pip install -r requirements-prototype.txt  
pip install -e .

---

## 🔥 Run Local LLM (IMPORTANT)

Start the llama server:

.\Models\llama\llama-server.exe ^
  -m .\Models\llama\models\tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf ^
  --host 127.0.0.1 ^
  --port 8080

You should see:
server is listening on http://127.0.0.1:8080

---

## ▶️ Run UI

streamlit run UI/UI.py

---

## 🧪 Experiment Modes

- No Evolution (`none`)
- Random Mutation (`random`)
- LLM Mutation (`llm`)

These allow comparison of:
- Baseline performance
- Random improvements
- LLM-guided improvements

---

## ⚠️ Current Limitations

- Stub evaluator (not real Pacman environment)
- Small local model (TinyLlama) → limited reasoning ability
- LLM occasionally produces invalid outputs (handled via validation)
- FAISS not yet integrated into mutation loop

---

## 🚧 Future Work

- Integrate real environment for evaluation
- FAISS-guided mutation (RAG)
- Improve mutation diversity
- Multi-run comparison visualization
- Performance optimization

---

## 📚 References

- AlphaEvolve (Google Research)
- Evolutionary Algorithms
- Sentence Transformers (SBERT)
- FAISS (Facebook AI Similarity Search)
