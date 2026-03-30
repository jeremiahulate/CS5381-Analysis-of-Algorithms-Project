# Round 2 – Individual Run (Arefeh)

## Environment
- OS: Windows
- Python: 3.x
- UI: Streamlit
- Project install: editable install (`pip install -e .`)

## Adopted Libraries (main)
- streamlit
- (others are installed from pyproject.toml / requirements in the repo)

## How to Run (commands)
From the repo root:

```bash
python -m venv .venv
# activate venv (Windows CMD): .venv\Scripts\activate.bat
pip install -U pip
pip install -e .
streamlit run UI/AlgoChat.py

```

Flow of Execution (high-level)

User provides initial code + fitness weights.

System runs evolutionary loop for N generations.

Each generation: generate candidate(s) -> evaluate -> compute fitness -> keep best.

UI shows best fitness/score and raw metrics.

My parameter configuration

generations: 10

weights: w1=0.50, w2=0.30, w3=0.20

runtime: 1.50 seconds

best fitness: 884.688

raw metrics: score=1838, survival_time=44.29, steps=238

Issues experienced + solutions

PowerShell could not activate venv (scripts disabled).

Solution: use .venv\Scripts\python ... directly or change execution policy.

Streamlit missing: No module named streamlit

Solution: pip install streamlit