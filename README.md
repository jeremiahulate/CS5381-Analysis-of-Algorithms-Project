# CS5381 Evolutionary Algorithm Agent (AlgoChat)

This project implements a simplified evolutionary agent inspired by **AlphaEvolve**, designed to iteratively improve code or algorithmic solutions using fitness-based evaluation, mutation, and top-k selection.

The system focuses on the **Pacman use case** and combines:
- Evolutionary algorithms
- Local LLM-guided mutation with **llama.cpp**
- **RAG-guided mutations** using **FAISS + SBERT**
- Top-k selection across generations
- A Streamlit-based UI
- Automatic CSV export of run history

---

## Prototype Features

### Evolution Engine
- Generates candidate programs across generations
- Supports multiple mutation modes:
  - `none` → baseline (no change)
  - `random` → rule-based mutation
  - `llm` → **RAG-guided local mutation**
- Uses **top-k selection**
- Tracks the best candidate across generations
- Preserves valid candidates when LLM output is invalid or unchanged

Core implementation:
- `src/evolve/engine.py`

---

## Local + RAG LLM Mutation 

The system uses a **locally hosted LLM via llama.cpp (`llama-server`)** and integrates **retrieval-augmented generation (RAG)** into the mutation loop.

### Current LLM Setup
- Local inference through `llama-server`
- Model used:
  - `mistral-7b-instruct-v0.2.Q4_K_M.gguf`
- No external API required
- Runs fully on the user’s machine

### Why llama-server?
- Avoids reloading the model on every mutation
- Faster for iterative evolutionary loops than `llama-cli`
- Supports local and private experimentation

### RAG Integration
The `llm` mutation mode is not plain LLM-only mutation. It is:

- SBERT embedding of the current prompt/code context
- FAISS retrieval of relevant local knowledge documents
- Retrieved guidance injected into the mutation prompt
- Local LLM mutation using the retrieved context

This means the current `llm` mode is effectively:
- **RAG + LLM mutation**

Files:
- `src/retrieval/faiss_retriever.py`
- `src/retrieval/knowledge_loader.py`
- `src/evolve/generator.py`

---

## Mutation Design

### Supported Mutation Modes
- `none`
  - Reuses the parent candidate
  - Used as the baseline condition
- `random`
  - Applies structured random mutation
  - Can mutate simple or conditional Pacman logic
- `llm`
  - Uses **RAG-guided local LLM mutation**
  - Falls back to safe mutation behavior if the LLM output is invalid

### Validation Layer
To keep the system stable, generated code is validated before use:

- Python syntax validation (`ast.parse`)
- Required function validation (`pacman_agent(state)`)
- Allowed-action validation
- Fallback preservation when invalid or unchanged output is detected

This prevents crashes and keeps the evolutionary loop running even when the local model produces malformed outputs.

File:
- `src/evolve/generator.py`

---

## Fitness & Evaluation

### Fitness Function:
Fitness is computed as:

`fitness = w1 * score + w2 * survival_time - w3 * steps`

Where:
- `score` is maximized
- `survival_time` time is maximized
- `steps` is minimized as cost

### Evaluator
The prototype currently uses a **deterministic stub Pacman evaluator**. It does not run the full Pacman game environment, but it scores candidate strategies consistently based on:

- code structure
- branching logic
- ghost/default action behavior
- deterministic hash-based variation

This makes comparisons reproducible across runs.

Files:
- `src/evolve/fitness.py`
- `src/evolve/evaluator.py`

---

## Selection Strategy

The system uses **top-k selection**.

For each generation:
1. A population of candidates is generated
2. All candidates are evaluated
3. Candidates are ranked by fitness
4. The **top k** candidates are retained as parents for the next generation

This allows better diversity than single-best-only selection.

File:
- `src/evolve/engine.py`

---

## Streamlit UI

The Streamlit UI allows users to:

- Input **initial code**
- Input **algorithm / problem description**
- Choose mutation mode
- Set:
  - number of generations
  - population size
  - top-k selection size
  - fitness weights
- Run the system with one click

### UI Displays
- Best fitness score
- Best raw metrics
- Runtime
- Fitness progression across generations
- Best solution found
- Per-generation operation summaries
- Top-k retained candidates for each generation
- CSV export of evolution history

File:
- `UI/UI.py`

---

## Vector Database and Knowledge Retrieval

The project uses:

- **Sentence Transformers (SBERT)** for embeddings
- **FAISS** for vector similarity search
- Local text knowledge files for mutation guidance

Knowledge is loaded from:
- `Data/knowledge/`

Examples include:
- Pacman strategy guidance
- heuristic references

The retriever returns top-k relevant contexts, which are inserted into the LLM prompt during `llm` mutation mode.

Files:
- `src/embeddings/sbert.py`
- `src/vectordb/faiss_store.py`

---
## System Workflow

### High-Level Evolution Loop
1. User enters initial code and optional problem description in the UI
2. The evolution engine generates a population of candidates
3. Mutation is applied using one of:
   - none
   - random
   - RAG + LLM
4. Each candidate is evaluated with the fitness function
5. The top-k candidates are selected
6. The process repeats for the requested number of generations
7. Results are displayed in the UI and saved to CSV

### RAG + LLM Workflow
1. The current code and problem description are embedded
2. FAISS retrieves relevant local knowledge documents
3. Retrieved guidance is appended to the mutation prompt
4. `llama-server` produces an action/code mutation
5. The mutation is validated before evaluation

---

## Project Structure
```text
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
├── knowledge/
└── evolution_runs/

Tests/
└── test_*.py
```
---

## How to Run

### 1. Clone Repo
```text
git clone https://github.com/jeremiahulate/CS5381-Analysis-of-Algorithms-Project.git
```
### 2. Setup Environment
```text
python -m venv .venv  
.\.venv\Scripts\Activate.ps1
```
### 3. Install Dependencies
```text
pip install -r requirements-prototype.txt  
pip install -e .
```
---

## Local LLM Setup

This project uses a **local LLM served by llama.cpp**.  

### 1. Download llama.cpp (Prebuilt Binaries)

Download from:  
https://github.com/ggerganov/llama.cpp/releases

Extract the contents into:
Models/llama/


Expected structure:

```text
Models/
└── llama/
    ├── llama-server.exe
    ├── llama-cli.exe
    ├── ggml-cpu-haswell.dll
    └── ...
```

---

### 2. Download a GGUF Model

Model used in this prototype:
- mistral-7b-instruct-v0.2.Q4_K_M.gguf

Place it here:
Models/llama/models/

Final structure:
```text
Models/
└── llama/
    ├── llama-server.exe
    └── models/
        └── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```
---

### 3. Start the LLM Server

Open PowerShell in the project root and run:
```text
.\Models\llama\llama-server.exe -m .\Models\llama\models\tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
--host 127.0.0.1 `
--port 8080
```

If successful, you will see:
```text
server is listening on http://127.0.0.1:8080
```

Keep this terminal open while running the UI.

---

## Run UI
```text
streamlit run UI/UI.py
```
---

## Experiment Modes

The current UI supports:
- `none`
- `random`
- `llm`

Where:
- `none` is the baseline performance
- `random` is structured random improvements
- `llm` is Rag-guided local LLM mutation

These three modes are intended for direct comparison in experiments

---

## Output and Saved Results

After execution, the system automatically saves evolution history to CSV in:

```text
Data/evolution_runs
```

The UI also allows downloading the CSV directly.

Each run records:
- generation
- best generation fitness
- best so far fitness
- best raw metrics
- provider / mutation mode
- top-k retained candidate fitness value

---

## Current Limitations

- Uses a deterministic stub evaluator rather than full Pacman gameplay
- Local LLM output can still be conservative or malformed
- LLM mode may preserve the original candidate instead of always mutating
- Comparative plotting across multiple CSV runs is performed externally
- Performance depends on local machine resources and model size

---

## Future Work

- Integrate a real Pacman environment
- Improve LLM mutation quality
- Add multi-run comparison plotting directly into the UI
- Add diversity tracking and elitism
- Extend to other algorithms such as matrix multiplication
- Support richer conditional mutation beyond action-only refinement

---

## References

- AlphaEvolve (Google Research)
- Evolutionary Algorithms
- Sentence Transformers (SBERT)
- FAISS (Facebook AI Similarity Search)
- llama.cpp
