import time
import random
import streamlit as st

st.set_page_config(page_title="gradient color", layout="wide")

st.markdown(
    """
    <style>
    /* Reduce top padding so content sits closer to the top */
    .block-container { padding-top: 0.75rem; }

    /* Full app background */
    .stApp {
        background: radial-gradient(circle at 20% 10%, #1d4ed8 0%, rgba(29, 78, 216, 0) 35%),
                    radial-gradient(circle at 80% 20%, #7c3aed 0%, rgba(124, 58, 237, 0) 40%),
                    linear-gradient(135deg, #0b1020 0%, #0f172a 45%, #020617 100%);
        color: #ffffff;
    }

    /* Main content container styling for readability */
    section[data-testid="stMain"] > div {
        background: rgba(2, 6, 23, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 1.25rem 1.25rem;
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
    }

    /* Center the specific header + subtitle (and force white) */
    .top-center {
        text-align: center;
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Evolution demo (replace later)
# ----------------------------
def evolve_stub(num_generations: int, initial_code: str):
    """
    Replace with your real evolution loop.
    Yields (generation_number, best_score_so_far, best_solution_so_far).
    """
    best = 0.0
    best_solution = initial_code
    for g in range(1, num_generations + 1):
        time.sleep(0.05)  # simulate work

        # simulate score improving sometimes
        candidate_score = random.random() * (g / num_generations)
        if candidate_score >= best:
            best = candidate_score
            best_solution = initial_code + f"\n# improved at generation {g} (stub)\n"

        yield g, best, best_solution


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
if "best_score" not in st.session_state:
    st.session_state["best_score"] = 0.0
if "best_solution" not in st.session_state:
    st.session_state["best_solution"] = ""  # <- store final/best program/code here

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
    placeholder="Example: Evolve candidate programs; fitness = passed unit tests; selection = tournament; mutation = ...",
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

col1, col2 = st.columns(2)
with col1:
    start_btn = st.button(
        "Start evolution / testing",
        type="primary",
        disabled=not code_ok or st.session_state["evolution_running"],
    )
with col2:
    if st.button("Clear Initial Code"):
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
    "Number of generations to run",
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

    a, b, c = dash_metrics.columns(3)
    a.metric("Generations performed", f"{st.session_state['gen_done']}")
    b.metric("Best score", f"{st.session_state['best_score']:.6f}")
    c.metric("Target generations", f"{int(target_generations)}")

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
    st.session_state["best_score"] = 0.0
    st.session_state["best_solution"] = ""
    dash_progress.progress(0)
    render_dashboard()

if start_btn:
    st.session_state["evolution_running"] = True
    st.session_state["stop_requested"] = False
    st.session_state["gen_done"] = 0
    st.session_state["best_score"] = 0.0
    st.session_state["best_solution"] = st.session_state["initial_code"]  # start from initial
    dash_progress.progress(0)
    render_dashboard()

    for g, best, best_solution in evolve_stub(int(target_generations), st.session_state["initial_code"]):
        if st.session_state["stop_requested"]:
            break

        st.session_state["gen_done"] = g
        st.session_state["best_score"] = best
        st.session_state["best_solution"] = best_solution
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
    st.write(f"**Best Score:** `{st.session_state['best_score']:.6f}`")
    st.code(st.session_state["best_solution"], language=st.session_state["code_language"])
else:
    st.info("Run the evolution to generate and display the best solution.")