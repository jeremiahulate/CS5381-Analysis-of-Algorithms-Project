import time
import random
import streamlit as st

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

# ----------------------------
# Fitness definition
# Fitness = w1*score + w2*survival_time - w3*cost(steps), s.t. w1+w2+w3=1
# ----------------------------
def compute_fitness(score: float, survival_time: float, steps: float, w1: float, w2: float, w3: float) -> float:
    return (w1 * score) + (w2 * survival_time) - (w3 * steps)


# ----------------------------
# Evaluation stub (replace later with real Pacman evaluation)
# Returns metrics used by the fitness function: score, survival_time, steps
# ----------------------------
def evaluate_candidate_stub(generation: int, num_generations: int):
    """
    Replace with your real Pacman evaluation.
    This stub simulates:
      - score tends to improve over generations
      - survival time tends to improve
      - steps may decrease (cost)
    """
    progress = generation / max(1, num_generations)

    score = random.randint(0, 500) + int(2000 * progress * random.random())
    survival_time = random.uniform(5, 20) + (60 * progress * random.random())
    steps = random.randint(150, 600) - int(80 * progress * random.random())  # cost decreases a bit

    # steps shouldn't go below something reasonable
    steps = max(20, steps)

    return {"score": float(score), "survival_time": float(survival_time), "steps": float(steps)}


# ----------------------------
# Evolution loop (fitness-based)
# Yields (generation, best_fitness, best_solution, best_metrics)
# ----------------------------
def evolve_stub(num_generations: int, initial_code: str, w1: float, w2: float, w3: float):
    best_fitness = float("-inf")
    best_solution = initial_code
    best_metrics = {"score": 0.0, "survival_time": 0.0, "steps": 0.0}

    for g in range(1, num_generations + 1):
        time.sleep(0.05)  # simulate work

        metrics = evaluate_candidate_stub(g, num_generations)
        fitness = compute_fitness(metrics["score"], metrics["survival_time"], metrics["steps"], w1, w2, w3)

        if fitness >= best_fitness:
            best_fitness = fitness
            best_metrics = metrics
            best_solution = initial_code + f"\n# improved at generation {g} (stub)\n"

        yield g, best_fitness, best_solution, best_metrics


# Session defaults
if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""
if "api_provider" not in st.session_state:
    st.session_state["api_provider"] = "Custom"
if "problem_description" not in st.session_state:
    st.session_state["problem_description"] = ""
if "initial_code" not in st.session_state:
    st.session_state["initial_code"] = ""
if "code_language" not in st.session_state:
    st.session_state["code_language"] = "python"

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
        ["Custom", "Provider A", "Provider B"],
        help="Choose where this key will be used (optional).",
        index=["Custom", "Provider A", "Provider B"].index(st.session_state["api_provider"])
        if st.session_state["api_provider"] in ["Custom", "Provider A", "Provider B"]
        else 0,
    )

    api_key_input = st.text_input(
        "API key (optional)",
        type="password",
        placeholder="paste-your-api-key-here",
        help="Leave blank to use the app without an API key.",
        value=st.session_state["api_key"],
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save key", type="primary"):
            st.session_state["api_key"] = api_key_input.strip()

    with col2:
        if st.button("Clear key"):
            st.session_state["api_key"] = ""


# Header
st.markdown('<h1 class="top-center">Welcome to AlgoChat</h1>', unsafe_allow_html=True)
st.markdown('<p class="top-center">CS5381 Algorithm Assistant</p>', unsafe_allow_html=True)

# --- API key is OPTIONAL now (no st.stop) ---
key_in_use = bool(st.session_state["api_key"])
if key_in_use:
    st.success("API key saved for this session.")
else:
    st.info("No API key provided (optional). You can still use the app.")


# Algorithm / Problem Description
st.markdown("## Algorithm / Problem Description")
st.session_state["problem_description"] = st.text_area(
    "Paste your algorithm description / pseudocode / code goal here:",
    height=220,
    placeholder="Example: Evolve candidate programs; fitness = w1*score + w2*survival - w3*steps; selection = top-k; mutation = ...",
    value=st.session_state["problem_description"],
)

desc_ok = bool(st.session_state["problem_description"].strip())
if not desc_ok:
    st.info("Enter your Algorithm / Problem Description to continue.")
    st.stop()


# Initial Code input
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


# Fitness weights (NEW)
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


with st.expander("Initial Code preview", expanded=False):
    st.code(st.session_state["initial_code"] or "(empty)", language=st.session_state["code_language"])

with st.expander("Preview", expanded=False):
    st.write(st.session_state["problem_description"] or "(empty)")


# ----------------------------
# Live Evolution Dashboard
# ----------------------------
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

    a, b, c, d = dash_metrics.columns(4)
    a.metric("Generations performed", f"{st.session_state['gen_done']}")
    b.metric("Best fitness", f"{st.session_state['best_fitness']:.3f}" if st.session_state["best_fitness"] != float("-inf") else "—")
    c.metric("Target generations", f"{int(target_generations)}")
    d.metric("Best score (raw)", f"{st.session_state['best_metrics']['score']:.0f}")

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
    dash_progress.progress(0)
    render_dashboard()

if start_btn:
    st.session_state["evolution_running"] = True
    st.session_state["stop_requested"] = False
    st.session_state["gen_done"] = 0
    st.session_state["best_fitness"] = float("-inf")
    st.session_state["best_solution"] = st.session_state["initial_code"]
    st.session_state["best_metrics"] = {"score": 0.0, "survival_time": 0.0, "steps": 0.0}
    dash_progress.progress(0)
    render_dashboard()

    for g, best_fit, best_solution, best_metrics in evolve_stub(
        int(target_generations),
        st.session_state["initial_code"],
        w1, w2, w3,
    ):
        if st.session_state["stop_requested"]:
            break

        st.session_state["gen_done"] = g
        st.session_state["best_fitness"] = best_fit
        st.session_state["best_solution"] = best_solution
        st.session_state["best_metrics"] = best_metrics

        dash_progress.progress(g / int(target_generations))
        render_dashboard()

    st.session_state["evolution_running"] = False
    st.session_state["stop_requested"] = False
    render_dashboard()

    if st.session_state["gen_done"] >= int(target_generations):
        st.success("Evolution finished.")
    else:
        st.warning("Evolution stopped early.")


# ----------------------------
# Show Best Solution (FINAL)
# ----------------------------
st.markdown("## Best Solution")

if st.session_state["best_solution"].strip():
    bm = st.session_state["best_metrics"]
    st.write(
        f"**Best Fitness:** `{st.session_state['best_fitness']:.3f}`  \n"
        f"**Raw Metrics:** score=`{bm['score']:.0f}`, survival_time=`{bm['survival_time']:.2f}`, steps=`{bm['steps']:.0f}`"
    )
    st.code(st.session_state["best_solution"], language=st.session_state["code_language"])
else:
    st.info("Run the evolution to generate and display the best solution.")