"""
SpaceAI FC - Reusable Input Form Components
=============================================
Shared form widgets used across feature pages.
"""

import streamlit as st
from app.demo_data import POSITIONS, BARCA_PLAYERS, MADRID_PLAYERS, DEMO_PASSES, DEMO_MATCH_INFO


# ── Player table ──────────────────────────────────────────────────

def player_table(label: str, key_prefix: str, default_players: list = None, n: int = 11) -> list:
    """
    Render a compact player entry table (n rows).
    Returns list of player dicts.
    """
    st.markdown(f"**{label}**")

    defaults = default_players or [
        {"name": f"Player {i+1}", "number": i+1, "x": 60.0, "y": 40.0, "position": "CM"}
        for i in range(n)
    ]

    players = []
    header = st.columns([3, 1, 1.5, 1.5, 2])
    header[0].markdown("<small>**Name**</small>", unsafe_allow_html=True)
    header[1].markdown("<small>**#**</small>", unsafe_allow_html=True)
    header[2].markdown("<small>**X (0-120)**</small>", unsafe_allow_html=True)
    header[3].markdown("<small>**Y (0-80)**</small>", unsafe_allow_html=True)
    header[4].markdown("<small>**Position**</small>", unsafe_allow_html=True)

    for i in range(n):
        d = defaults[i] if i < len(defaults) else defaults[0]
        cols = st.columns([3, 1, 1.5, 1.5, 2])
        name = cols[0].text_input("", value=d["name"],    key=f"{key_prefix}_name_{i}",  label_visibility="collapsed")
        num  = cols[1].number_input("", value=int(d["number"]), min_value=1, max_value=99,
                                    key=f"{key_prefix}_num_{i}", label_visibility="collapsed")
        x    = cols[2].number_input("", value=float(d["x"]), min_value=0.0, max_value=120.0, step=0.5,
                                    key=f"{key_prefix}_x_{i}", label_visibility="collapsed")
        y    = cols[3].number_input("", value=float(d["y"]), min_value=0.0, max_value=80.0, step=0.5,
                                    key=f"{key_prefix}_y_{i}", label_visibility="collapsed")
        pos_idx = POSITIONS.index(d["position"]) if d["position"] in POSITIONS else 0
        pos  = cols[4].selectbox("", POSITIONS, index=pos_idx,
                                 key=f"{key_prefix}_pos_{i}", label_visibility="collapsed")
        players.append({"name": name, "number": int(num), "x": float(x), "y": float(y), "position": pos})

    return players


# ── Pass event text area ──────────────────────────────────────────

def pass_events_input(key: str, default_text: str = "", simple: bool = False) -> list:
    """
    Text area for pass events.
    simple=True  → format: "from_number,to_number" per line
    simple=False → format: "from,to,success(1/0),x,y" per line
    Returns list of pass dicts.
    """
    if simple:
        help_text = "Format: `passer_number,receiver_number` — one pass per line"
        placeholder = "8,6\n6,9\n9,19"
    else:
        help_text = "Format: `passer,receiver,success(1/0),x,y` — one pass per line"
        placeholder = "8,6,1,45,48\n6,9,1,60,40\n9,19,0,80,40"

    text = st.text_area(
        "Pass events",
        value=default_text,
        height=160,
        help=help_text,
        placeholder=placeholder,
        key=key,
    )
    return _parse_passes(text, simple=simple)


def _parse_passes(text: str, simple: bool = False) -> list:
    passes = []
    for line in text.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        try:
            if simple and len(parts) >= 2:
                passes.append({
                    "passer": int(parts[0]), "receiver": int(parts[1]),
                    "success": True, "x": 0.0, "y": 0.0, "end_x": 0.0, "end_y": 0.0,
                })
            elif not simple and len(parts) >= 5:
                passes.append({
                    "passer": int(parts[0]), "receiver": int(parts[1]),
                    "success": bool(int(parts[2])),
                    "x": float(parts[3]), "y": float(parts[4]),
                    "end_x": float(parts[5]) if len(parts) > 5 else 0.0,
                    "end_y": float(parts[6]) if len(parts) > 6 else 0.0,
                })
        except (ValueError, IndexError):
            pass
    return passes


# ── Match info form ───────────────────────────────────────────────

def match_info_form(key_prefix: str, defaults: dict = None) -> dict:
    d = defaults or DEMO_MATCH_INFO
    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    home = c1.text_input("Home team", value=d.get("home_team", "Team A"), key=f"{key_prefix}_home")
    away = c2.text_input("Away team", value=d.get("away_team", "Team B"), key=f"{key_prefix}_away")
    sh   = c3.number_input("Score (H)", value=d.get("score_home", 0), min_value=0, max_value=20, key=f"{key_prefix}_sh")
    sa   = c4.number_input("Score (A)", value=d.get("score_away", 0), min_value=0, max_value=20, key=f"{key_prefix}_sa")
    c5, c6, c7 = st.columns([1, 2, 2])
    minute = c5.number_input("Minute", value=d.get("minute", 0), min_value=0, max_value=120, key=f"{key_prefix}_min")
    comp   = c6.text_input("Competition", value=d.get("competition", ""), key=f"{key_prefix}_comp")
    date   = c7.text_input("Date (YYYY-MM-DD)", value=d.get("date", ""), key=f"{key_prefix}_date")
    return {
        "home_team": home, "away_team": away,
        "score_home": int(sh), "score_away": int(sa),
        "minute": int(minute), "competition": comp, "date": date,
    }


# ── Team color and name ───────────────────────────────────────────

def team_meta(key_prefix: str, default_name: str = "Team A", default_color: str = "#a50044") -> tuple:
    c1, c2 = st.columns([3, 1])
    name  = c1.text_input("Team name", value=default_name, key=f"{key_prefix}_tname")
    color = c2.color_picker("Color", value=default_color, key=f"{key_prefix}_tcolor")
    return name, color


# ── Video / YouTube input tab ─────────────────────────────────────

def video_input_tab(key_prefix: str) -> dict:
    """
    Render video upload + YouTube URL options.
    Returns dict with keys: source ("file"|"youtube"|None), file_bytes, filename, url.
    """
    v_col, y_col = st.columns(2)

    with v_col:
        st.markdown("**Upload video file**")
        uploaded = st.file_uploader(
            "Drop video here",
            type=["mp4", "avi", "mov", "mkv"],
            key=f"{key_prefix}_video_file",
            label_visibility="collapsed",
        )

    with y_col:
        st.markdown("**— or — YouTube URL**")
        yt_url = st.text_input(
            "YouTube URL",
            placeholder="https://youtube.com/watch?v=...",
            key=f"{key_prefix}_yt_url",
            label_visibility="collapsed",
        )
        demo_yt = st.checkbox("Use demo data (no download)", value=True,
                              key=f"{key_prefix}_yt_demo")

    if uploaded:
        return {"source": "file", "file_bytes": uploaded.read(),
                "filename": uploaded.name, "url": None}
    if yt_url:
        return {"source": "youtube", "file_bytes": None,
                "filename": None, "url": yt_url, "demo_mode": demo_yt}
    return {"source": None}


# ── Dataset upload tab ────────────────────────────────────────────

def dataset_input_tab(key_prefix: str) -> dict:
    """
    Render dataset file uploader (CSV/JSON).
    Returns dict with file_bytes or None.
    """
    st.markdown("**Upload dataset file** (CSV or JSON)")
    st.caption(
        "Expected columns (CSV): `team, name, number, x, y, position`  \n"
        "Or JSON with keys: `team_a`, `team_b`, `passes`, `match_info`"
    )
    uploaded = st.file_uploader(
        "Upload dataset",
        type=["csv", "json"],
        key=f"{key_prefix}_dataset",
        label_visibility="collapsed",
    )
    if uploaded:
        content = uploaded.read()
        st.success(f"Loaded **{uploaded.name}** ({len(content):,} bytes)")
        return {"file_bytes": content, "filename": uploaded.name}
    return {"file_bytes": None}


# ── Demo data button ──────────────────────────────────────────────

def demo_button(key: str, label: str = "⚡ Load El Clásico Demo Data") -> bool:
    """Render a styled demo data button. Returns True if clicked."""
    st.markdown('<div class="demo-btn">', unsafe_allow_html=True)
    clicked = st.button(label, key=key)
    st.markdown("</div>", unsafe_allow_html=True)
    return clicked


# ── Analyze button ────────────────────────────────────────────────

def analyze_button(key: str, label: str = "⚽ Analyze") -> bool:
    st.markdown('<div class="analyze-btn">', unsafe_allow_html=True)
    clicked = st.button(label, key=key)
    st.markdown("</div>", unsafe_allow_html=True)
    return clicked
