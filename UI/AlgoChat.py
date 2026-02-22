import streamlit as st

st.set_page_config(page_title="Gradient Background", layout="wide")

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
        color: #e5e7eb;
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

    /* Center the specific header + subtitle */
    .top-center { text-align: center; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<h1 class="top-center">Welcome to AlgoChat</h1>', unsafe_allow_html=True)
st.markdown('<p class="top-center">CS5381 Algorithm Assistant</p>', unsafe_allow_html=True)