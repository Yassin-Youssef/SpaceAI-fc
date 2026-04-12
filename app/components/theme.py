"""
SpaceAI FC - Theme & CSS
==========================
Football-themed styling that overrides Streamlit defaults.
"""

FOOTBALL_CSS = """
<style>
/* ── Google Font ──────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif; }

/* ── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1B5E20 0%, #2E7D32 50%, #1B5E20 100%);
    border-right: 2px solid #FFD700;
}
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 4px; }
[data-testid="stSidebar"] .stRadio label {
    background: rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 10px 14px !important;
    margin-bottom: 2px;
    transition: background 0.2s;
    cursor: pointer;
    font-size: 0.95rem;
    font-weight: 500;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,215,0,0.2) !important;
}
[data-testid="stSidebar"] input[type="radio"]:checked + div {
    background: rgba(255,215,0,0.25) !important;
    border-left: 3px solid #FFD700;
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2); }
[data-testid="stSidebar"] .stMarkdown p { font-size: 0.8rem; opacity: 0.75; }

/* ── Main content area ───────────────────────────────────── */
.main .block-container {
    background-color: #F1F8E9;
    padding: 1.5rem 2rem 3rem 2rem;
    max-width: 1400px;
}
.stApp { background-color: #F1F8E9; }

/* ── Page header ─────────────────────────────────────────── */
.page-header {
    background: linear-gradient(135deg, #1B5E20, #2E7D32);
    color: white;
    padding: 20px 28px;
    border-radius: 12px;
    margin-bottom: 24px;
    border-left: 5px solid #FFD700;
    box-shadow: 0 4px 15px rgba(27,94,32,0.3);
}
.page-header h1 { color: white !important; margin: 0; font-size: 1.8rem; font-weight: 800; }
.page-header p { color: rgba(255,255,255,0.85) !important; margin: 6px 0 0 0; font-size: 0.95rem; }

/* ── Metric cards ────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1B5E20, #2E7D32);
    padding: 16px 20px;
    border-radius: 12px;
    border: 1px solid rgba(255,215,0,0.3);
    box-shadow: 0 4px 12px rgba(27,94,32,0.2);
}
[data-testid="stMetricLabel"] { color: rgba(255,255,255,0.8) !important; font-size: 0.8rem !important; }
[data-testid="stMetricValue"] { color: #FFD700 !important; font-size: 1.8rem !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"] { color: rgba(255,255,255,0.7) !important; }

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #2E7D32, #1B5E20) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.3px;
    box-shadow: 0 3px 10px rgba(27,94,32,0.3) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #388E3C, #2E7D32) !important;
    box-shadow: 0 5px 18px rgba(27,94,32,0.45) !important;
    transform: translateY(-1px);
}
.stButton > button:active { transform: translateY(0); }

/* ── Analyze button (big) ────────────────────────────────── */
.analyze-btn .stButton > button {
    background: linear-gradient(135deg, #FFD700, #FFC107) !important;
    color: #1B5E20 !important;
    font-size: 1.1rem !important;
    padding: 14px 40px !important;
    font-weight: 700 !important;
    width: 100%;
}
.analyze-btn .stButton > button:hover {
    background: linear-gradient(135deg, #FFCA28, #FFB300) !important;
    box-shadow: 0 5px 20px rgba(255,215,0,0.4) !important;
}

/* ── Demo data button ────────────────────────────────────── */
.demo-btn .stButton > button {
    background: rgba(27,94,32,0.12) !important;
    color: #1B5E20 !important;
    border: 2px solid #2E7D32 !important;
    box-shadow: none !important;
}
.demo-btn .stButton > button:hover {
    background: rgba(27,94,32,0.2) !important;
}

/* ── Tabs ─────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background-color: #E8F5E9;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #2E7D32 !important;
    font-weight: 500;
    padding: 8px 20px;
}
.stTabs [aria-selected="true"] {
    background-color: #2E7D32 !important;
    color: white !important;
}

/* ── Cards / containers ──────────────────────────────────── */
.result-card {
    background: white;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    border: 1px solid #C8E6C9;
    box-shadow: 0 2px 8px rgba(27,94,32,0.08);
}
.insight-card {
    background: #E8F5E9;
    border-left: 4px solid #2E7D32;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 6px 0;
}
.warning-card {
    background: #FFF8E1;
    border-left: 4px solid #FFD700;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 6px 0;
}
.danger-card {
    background: #FFEBEE;
    border-left: 4px solid #C62828;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 6px 0;
}
.section-title {
    color: #1B5E20;
    font-size: 1.1rem;
    font-weight: 700;
    margin: 20px 0 10px 0;
    padding-bottom: 6px;
    border-bottom: 2px solid #C8E6C9;
}
.priority-high {
    background: linear-gradient(90deg, #FFEBEE, white);
    border-left: 4px solid #C62828;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 8px 0;
}
.priority-medium {
    background: linear-gradient(90deg, #FFF8E1, white);
    border-left: 4px solid #F57F17;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 8px 0;
}
.priority-low {
    background: linear-gradient(90deg, #E8F5E9, white);
    border-left: 4px solid #2E7D32;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 8px 0;
}
.pattern-detected {
    background: #E8F5E9;
    border: 1px solid #A5D6A7;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 4px 0;
}
.pattern-not-detected {
    background: #FAFAFA;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 4px 0;
    opacity: 0.7;
}
.swot-strength { border-left: 4px solid #2E7D32; background: #E8F5E9; }
.swot-weakness { border-left: 4px solid #C62828; background: #FFEBEE; }
.swot-opportunity { border-left: 4px solid #1565C0; background: #E3F2FD; }
.swot-threat { border-left: 4px solid #E65100; background: #FBE9E7; }
.swot-item {
    border-radius: 0 8px 8px 0;
    padding: 10px 16px;
    margin: 6px 0;
    font-size: 0.9rem;
}

/* ── Inputs ──────────────────────────────────────────────── */
.stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox > div {
    border-color: #A5D6A7 !important;
    border-radius: 6px !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: #2E7D32 !important;
    box-shadow: 0 0 0 2px rgba(46,125,50,0.15) !important;
}

/* ── Expander ────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background-color: #E8F5E9 !important;
    border-radius: 8px !important;
    color: #1B5E20 !important;
    font-weight: 600 !important;
}

/* ── Spinner ─────────────────────────────────────────────── */
.stSpinner > div { border-top-color: #2E7D32 !important; }

/* ── Error / success ─────────────────────────────────────── */
.stAlert { border-radius: 10px !important; }

/* ── Headings ────────────────────────────────────────────── */
h1, h2, h3 { color: #1B5E20 !important; }
h4, h5, h6 { color: #2E7D32 !important; }

/* ── DataFrame ───────────────────────────────────────────── */
.stDataFrame { border-radius: 8px; overflow: hidden; }

/* ── Divider ─────────────────────────────────────────────── */
hr { border-color: #C8E6C9 !important; }

/* ── Logo area ───────────────────────────────────────────── */
.logo-container {
    text-align: center;
    padding: 16px 0 8px 0;
    margin-bottom: 8px;
}
.logo-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: white;
    letter-spacing: 1px;
}
.logo-subtitle {
    font-size: 0.7rem;
    color: rgba(255,255,255,0.7);
    letter-spacing: 2px;
    text-transform: uppercase;
}
</style>
"""


def inject_css():
    """Call this once at app startup to inject the theme CSS."""
    import streamlit as st
    st.markdown(FOOTBALL_CSS, unsafe_allow_html=True)


def page_header(icon: str, title: str, description: str):
    """Render a styled page header."""
    import streamlit as st
    st.markdown(
        f"""
        <div class="page-header">
            <h1>{icon} {title}</h1>
            <p>{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(text: str):
    """Render a section divider title."""
    import streamlit as st
    st.markdown(f'<p class="section-title">{text}</p>', unsafe_allow_html=True)


def result_card(content_html: str):
    """Wrap content in a white result card."""
    import streamlit as st
    st.markdown(f'<div class="result-card">{content_html}</div>', unsafe_allow_html=True)


def insight_item(text: str, kind: str = "insight"):
    """Render a single insight bullet."""
    import streamlit as st
    css_class = {"insight": "insight-card", "warning": "warning-card",
                 "danger": "danger-card"}.get(kind, "insight-card")
    st.markdown(f'<div class="{css_class}">{text}</div>', unsafe_allow_html=True)
