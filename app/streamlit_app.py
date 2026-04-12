"""
SpaceAI FC - Streamlit Frontend
=================================
Main entry point.

Run with:
    streamlit run app/streamlit_app.py --server.port 8501

Make sure the FastAPI backend is also running:
    uvicorn api.main:app --reload --port 8000
"""

import sys
import os

# Ensure the project root (SpaceAI FC/) is on sys.path so that
# `from app.*` and `from engine.*` imports work regardless of where
# Streamlit was launched from.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

# Must be the FIRST Streamlit call
st.set_page_config(
    page_title="SpaceAI FC",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "SpaceAI FC v4.0 — Agentic Tactical Intelligence System",
    },
)

# Inject theme CSS
from app.components.theme import inject_css
inject_css()

# Sidebar navigation
from app.components.sidebar import render_sidebar
page = render_sidebar()

# Route to the selected page
if page == "full_analysis":
    from app.views.full_analysis import render
elif page == "pass_network":
    from app.views.pass_network import render
elif page == "space_control":
    from app.views.space_control import render
elif page == "formation":
    from app.views.formation import render
elif page == "press_resistance":
    from app.views.press_resistance import render
elif page == "patterns":
    from app.views.patterns import render
elif page == "recommendations":
    from app.views.recommendations import render
elif page == "player_assessment":
    from app.views.player_assessment import render
elif page == "ask_spaceai":
    from app.views.ask_spaceai import render
elif page == "compare":
    from app.views.compare import render
elif page == "simulation":
    from app.views.simulation import render
elif page == "explanation":
    from app.views.explanation import render
else:
    def render():
        st.error(f"Unknown page: {page}")

render()
