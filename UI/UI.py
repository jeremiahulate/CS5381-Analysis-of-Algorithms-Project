import sys
from datetime import datetime
import time
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evolve.engine import run_evolution
from src.evolve.evaluator import DeterministicStubPacmanEvaluator
from src.evolve.fitness import FitnessWeights
from src.evolve.generator import LLMSettings

st.set_page_config(page_title="gradient color", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 0.75rem; }

    .stApp {
        background: radial-gradient(circle at 20% 10%, #1d4ed8 0%, rgba(29, 78, 216, 0) 35%),
                    radial-gradient(circle at 80% 20%, #7c3aed 0%, rgba(124, 58, 237, 0) 40%),
                    linear-gradient(135deg, #0b1020 0%, #0f172a 45%, #020617 100%);
        color: #ffffff;
    }

    section[data-testid="stMain"] > div {
        background: rgba(2, 6, 23, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 1.25rem 1.25rem;
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
    }

    .top-center {
        text-align: center;
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def run_backend_evolution(
    initial_code: str,
    language: str,
    generations: int,
    w1: float,
    w2: float,
    w3: float,
    mutation_mode: str,
    problem_description: str,
    api_provider: str,
    population_size: int,
    selection_k: int,
):
    evaluator = DeterministicStubPacmanEvaluator()

    weights = FitnessWeights(
        w_score=w1,
        w_survival=w2,
        w_steps=w3,
    )

    provider_map = {
        "Heuristic": "heuristic",
        "Llama (local)": "llama",
    }

    llm_settings = LLMSettings(
        provider=provider_map.get(api_provider, "heuristic"),
    )
    print(
        f"[UI DEBUG] api_provider={api_provider}, "
        f"mapped_provider={llm_settings.provider}, "
    )
    result = run_evolution(
        initial_code=initial_code,
        evaluator=evaluator,
        weights=weights,
        generations=generations,
        population_size=int(population_size),
        selection_k=int(selection_k),
        mutation_mode=mutation_mode,
        language=language,
        seed=42,
        problem_description=problem_description,
        llm_settings=llm_settings,
    )

    return result


def history_to_dataframe(history):
    rows = []
    for item in history:
        rows.append(
            {
                "generation": item.generation,
                "best_generation_fitness": item.best_generation_fitness,
                "best_so_far_fitness": item.best_so_far_fitness,
                "best_score": item.best_score,
                "best_survival_time": item.best_survival_time,
                "best_steps": item.best_steps,
                "mutation_mode": item.mutation_mode,
                "provider": item.provider,
            }
        )
    return pd.DataFrame(rows)



def save_history_csv(history_df: pd.DataFrame, student_name: str) -> str:
    output_dir = ROOT / "Data" / "evolution_runs"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = output_dir / f"{student_name}.csv"
    history_df.to_csv(file_path, index=False)
    return str(file_path)


# Session defaults
if "api_provider" not in st.session_state:
    st.session_state["api_provider"] = "Heuristic (Offline)"
if "problem_description" not in st.session_state:
    st.session_state["problem_description"] = ""
if "initial_code" not in st.session_state:
    st.session_state["initial_code"] = ""
if "code_language" not in st.session_state:
    st.session_state["code_language"] = "python"
if "history" not in st.session_state:
    st.session_state["history"] = []
if "last_csv_path" not in st.session_state:
    st.session_state["last_csv_path"] = ""
if "runtime_timeseconds" not in st.session_state:
    st.session_state["runtime_timeseconds"] = 0.0

# Evolution state
if "evolution_running" not in st.session_state:
    st.session_state["evolution_running"] = False
if "stop_requested" not in st.session_state:
    st.session_state["stop_requested"] = False
if "gen_done" not in st.session_state:
    st.session_state["gen_done"] = 0

# Fitness/Best tracking
if "best_fitness" not in st.session_state:
    st.session_state["best_fitness"] = float("-inf")
if "best_solution" not in st.session_state:
    st.session_state["best_solution"] = ""
if "best_metrics" not in st.session_state:
    st.session_state["best_metrics"] = {"score": 0.0, "survival_time": 0.0, "steps": 0.0}


with st.sidebar:
    st.subheader("API Setup (optional)")

    st.session_state["api_provider"] = st.selectbox(
        "Provider",
        ["Heuristic (Offline)", "Llama (local)"],
        index=["Heuristic (Offline)",  "Llama (local)"].index(st.session_state["api_provider"])
        if st.session_state["api_provider"] in ["Heuristic (Offline)", "Llama (local)"]
        else 0,
        disabled=st.session_state["evolution_running"],
    )

    if st.session_state["api_provider"] == "Llama (local)":
        st.caption("Make sure llama-server is running locally at http://127.0.0.1:8080")
    else:
        st.caption("Heuristic mode runs fully offline without the local LLM server.")


st.markdown('<h1 class="top-center">Welcome to AlgoChat</h1>', unsafe_allow_html=True)
st.markdown('<p class="top-center">CS5381 Algorithm Assistant</p>', unsafe_allow_html=True)
st.markdown("### Enter your name with underscores(for saving results)")
st.caption("This will be used to save your CSV file")
student_name = st.text_input(
    "Student Name",
    placeholder="e.g. Jeremiah_Ulate"
)


st.markdown("## Algorithm / Problem Description (optional)")
st.session_state["problem_description"] = st.text_area(
    "Paste your algorithm description / pseudocode / code goal here:",
    height=220,
    placeholder="Example: Evolve candidate programs; fitness = w1*score + w2*survival - w3*steps; selection = top-k; mutation = ...",
    value=st.session_state["problem_description"],
)

desc_ok = bool(st.session_state["problem_description"].strip())

st.markdown("## Initial Code (required)")
st.session_state["code_language"] = st.selectbox(
    "Language",
    ["python", "java", "cpp", "javascript", "text"],
    index=["python", "java", "cpp", "javascript", "text"].index(st.session_state["code_language"])
    if st.session_state["code_language"] in ["python", "java", "cpp", "javascript", "text"]
    else 0,
)

st.session_state["initial_code"] = st.text_area(
    "Paste the initial code you want to test/evolve:",
    height=260,
    placeholder="Paste your starting code here...",
    value=st.session_state["initial_code"],
)

code_ok = bool(st.session_state["initial_code"].strip())

st.markdown("## Mutation Mode")
mutation_mode = st.selectbox(
    "Choose mutation mode",
    ["none", "random", "llm"],
    help="none = baseline, random = safe mutation, llm = placeholder until real LLM is integrated",
    disabled=st.session_state["evolution_running"],
)

st.markdown("## Evolution Settings")

population_size = st.number_input(
    "Population size",
    min_value=1,
    max_value=20,
    value=4,
    step=1,
    disabled=st.session_state["evolution_running"],
)

selection_k = st.number_input(
    "Top-K Selection",
    min_value=1,
    max_value=int(population_size),
    value=min(2, int(population_size)),
    step=1,
    disabled=st.session_state["evolution_running"],
)

st.markdown("## Fitness Weights (must sum to 1)")
w_col1, w_col2, w_col3 = st.columns(3)
with w_col1:
    w1 = st.slider("w₁ × score", 0.0, 1.0, 0.50, 0.05, disabled=st.session_state["evolution_running"])
with w_col2:
    w2 = st.slider("w₂ × survival time", 0.0, 1.0, 0.30, 0.05, disabled=st.session_state["evolution_running"])
with w_col3:
    w3 = st.slider("w₃ × steps (cost)", 0.0, 1.0, 0.20, 0.05, disabled=st.session_state["evolution_running"])

w_sum = w1 + w2 + w3
if abs(w_sum - 1.0) > 1e-6:
    st.warning(f"Your weights sum to {w_sum:.2f}. Adjust sliders so ∑w = 1.00.")

col1, col2 = st.columns(2)
with col1:
    start_btn = st.button(
        "Start evolution / testing",
        type="primary",
        disabled=(not code_ok) or st.session_state["evolution_running"] or (abs(w_sum - 1.0) > 1e-6),
    )
with col2:
    if st.button("Clear Initial Code", disabled=st.session_state["evolution_running"]):
        st.session_state["initial_code"] = ""


with st.expander("Algorithm / Problem Description", expanded=False):
    st.write(st.session_state["problem_description"] or "(empty)")

with st.expander("Initial Code preview", expanded=False):
    st.code(st.session_state["initial_code"] or "(empty)", language=st.session_state["code_language"])

if not code_ok:
    st.info("Enter Initial Code to start evolution.")
elif not desc_ok:
    st.info("No algorithm description provided. Running with code only.")

st.markdown("## Evolution Status")

target_generations = st.number_input(
    "Number of generations to run (iterations)",
    min_value=1,
    max_value=2000,
    value=50,
    step=1,
    disabled=st.session_state["evolution_running"],
)

dash_status = st.empty()
dash_metrics = st.empty()
dash_progress = st.progress(0)

def render_dashboard():
    status = "RUNNING" if st.session_state["evolution_running"] else "IDLE"
    if status == "RUNNING":
        dash_status.warning(f"Status: **{status}**")
    else:
        dash_status.info(f"Status: **{status}**")

    a, b, c, d, e = dash_metrics.columns(5)
    a.metric("Generations performed", f"{st.session_state['gen_done']}")
    b.metric("Best fitness", f"{st.session_state['best_fitness']:.3f}" if st.session_state["best_fitness"] != float("-inf") else "—")
    c.metric("Target generations", f"{int(target_generations)}")
    d.metric("Best score (raw)", f"{st.session_state['best_metrics']['score']:.0f}")
    e.metric("Runtime (seconds)", f"{st.session_state['runtime_timeseconds']:.2f}")

render_dashboard()

stop_col1, stop_col2 = st.columns(2)
with stop_col1:
    stop_btn = st.button("Stop evolution", disabled=not st.session_state["evolution_running"])
with stop_col2:
    reset_stats_btn = st.button("Reset stats", disabled=st.session_state["evolution_running"])

if stop_btn:
    st.session_state["stop_requested"] = True

if reset_stats_btn:
    st.session_state["gen_done"] = 0
    st.session_state["best_fitness"] = float("-inf")
    st.session_state["best_solution"] = ""
    st.session_state["best_metrics"] = {"score": 0.0, "survival_time": 0.0, "steps": 0.0}
    st.session_state["history"] = []
    st.session_state["last_csv_path"] = ""
    st.session_state["runtime_timeseconds"] = 0.0
    dash_progress.progress(0)
    render_dashboard()

if start_btn:
    st.session_state["evolution_running"] = True
    st.session_state["stop_requested"] = False
    st.session_state["gen_done"] = 0
    st.session_state["best_fitness"] = float("-inf")
    st.session_state["best_solution"] = st.session_state["initial_code"]
    st.session_state["best_metrics"] = {"score": 0.0, "survival_time": 0.0, "steps": 0.0}
    st.session_state["history"] = []
    st.session_state["last_csv_path"] = ""
    run_start = time.perf_counter()
    dash_progress.progress(0)
    render_dashboard()

    result = run_backend_evolution(
        initial_code=st.session_state["initial_code"],
        language=st.session_state["code_language"],
        generations=int(target_generations),
        w1=w1,
        w2=w2,
        w3=w3,
        mutation_mode=mutation_mode,
        population_size=int(population_size),
        selection_k=int(selection_k),
        problem_description=(
    st.session_state["problem_description"].strip()
    or "Improve the given code conservatively."
),
        api_provider=st.session_state["api_provider"],
    )

    for item in result.history:
        if st.session_state["stop_requested"]:
            break

        st.session_state["gen_done"] = item.generation
        st.session_state["best_fitness"] = item.best_so_far_fitness
        st.session_state["best_solution"] = item.best_code
        st.session_state["best_metrics"] = {
            "score": item.best_score,
            "survival_time": item.best_survival_time,
            "steps": item.best_steps,
        }

        dash_progress.progress(item.generation / int(target_generations))
        render_dashboard()

    st.session_state["evolution_running"] = False
    st.session_state["stop_requested"] = False
    st.session_state["history"] = result.history
    st.session_state["runtime_timeseconds"] = time.perf_counter() - run_start
    history_df = history_to_dataframe(result.history)
    if not history_df.empty:
        st.session_state["last_csv_path"] = save_history_csv(history_df,student_name)

    render_dashboard()

    if st.session_state["gen_done"] >= int(target_generations):
        st.success("Evolution finished.")
    else:
        st.warning("Evolution stopped early.")

st.markdown("## Fitness Across Generations")

history_df = history_to_dataframe(st.session_state["history"])
if not history_df.empty:
    st.line_chart(
        history_df.set_index("generation")[["best_generation_fitness", "best_so_far_fitness"]]
    )

    csv_bytes = history_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download evolution history CSV",
        data=csv_bytes,
        file_name=f"{student_name}_data.csv",
        mime="text/csv",
    )

    if st.session_state["last_csv_path"]:
        st.caption(f"Saved run CSV: {st.session_state['last_csv_path']}")

st.markdown("## Evolution Details")
if st.session_state["history"]:
    for item in st.session_state["history"][-10:]:
        with st.expander(f"Generation {item.generation}"):
            st.write(f"**Mutation Mode:** {item.mutation_mode}")
            st.write(f"**Provider:** {item.provider}")
            st.write(f"**Operation Summary:**")
            st.write(item.operation_summary or "No summary available.")
            st.write("**Best Code at this Generation:**")
            st.code(item.best_code, language=st.session_state["code_language"])

if st.session_state["best_solution"].strip():
    bm = st.session_state["best_metrics"] 
    st.write(
        f"**Best Fitness:** `{st.session_state['best_fitness']:.3f}`  \n"
        f"**Runtime:** '{st.session_state['runtime_timeseconds']:.2f}' seconds' \n"
        f"**Raw Metrics:** score=`{bm['score']:.0f}`, survival_time=`{bm['survival_time']:.2f}`, steps=`{bm['steps']:.0f}`"
    )
    st.code(st.session_state["best_solution"], language=st.session_state["code_language"])
else:
    st.info("Run the evolution to generate and display the best solution.")