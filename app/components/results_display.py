"""
SpaceAI FC - Reusable Results Display Components
==================================================
Shared widgets for showing analysis output across feature pages.
"""

import streamlit as st
from app.utils.api_client import base64_to_image
from app.components.theme import section_title


# ── Error / API offline ───────────────────────────────────────────

def show_error(result: dict):
    """Show a friendly error message from an API response."""
    msg = result.get("error", "Unknown error occurred.")
    if "Cannot connect" in msg:
        st.error("🔴 **Cannot connect to SpaceAI FC Engine**")
        st.info(
            "Make sure the API server is running:\n\n"
            "```\nuvicorn api.main:app --reload --port 8000\n```"
        )
    else:
        st.error(f"❌ **Analysis failed:** {msg}")


def check_result(result: dict) -> bool:
    """Return True if result is OK; show error and return False otherwise."""
    if not result.get("success", False):
        show_error(result)
        return False
    return True


# ── Visualisations ────────────────────────────────────────────────

def show_visualizations(visualizations: list, cols: int = 1):
    """
    Display a list of visualisation dicts (image_base64 + title).
    If cols > 1, lays them out side by side.
    """
    if not visualizations:
        return

    section_title("📊 Visualisations")
    if cols == 1 or len(visualizations) == 1:
        for viz in visualizations:
            try:
                img = base64_to_image(viz["image_base64"])
                st.image(img, caption=viz.get("title", ""), use_container_width=True)
            except Exception:
                st.warning(f"Could not render: {viz.get('title', 'image')}")
    else:
        groups = [visualizations[i:i+cols] for i in range(0, len(visualizations), cols)]
        for group in groups:
            c = st.columns(len(group))
            for idx, viz in enumerate(group):
                try:
                    img = base64_to_image(viz["image_base64"])
                    c[idx].image(img, caption=viz.get("title", ""), use_container_width=True)
                except Exception:
                    c[idx].warning(f"Could not render: {viz.get('title', 'image')}")


# ── Metric rows ───────────────────────────────────────────────────

def metric_row(metrics: list):
    """
    metrics: list of (label, value, delta=None) tuples.
    Renders them in equal-width columns.
    """
    if not metrics:
        return
    cols = st.columns(len(metrics))
    for i, m in enumerate(metrics):
        label, value = m[0], m[1]
        delta = m[2] if len(m) > 2 else None
        cols[i].metric(label, value, delta)


# ── Insights list ─────────────────────────────────────────────────

def show_insights(items: list, title: str = "💡 Key Insights"):
    """Show a list of insight strings as styled cards."""
    if not items:
        return
    section_title(title)
    for item in items:
        text = item if isinstance(item, str) else str(item)
        st.markdown(f'<div class="insight-card">• {text}</div>', unsafe_allow_html=True)


# ── Recommendations list ──────────────────────────────────────────

def show_recommendations(recs: list):
    """Show prioritized recommendations with color coding."""
    if not recs:
        return
    section_title("🎯 Recommendations")

    priority_order = {"high": 0, "medium": 1, "low": 2}
    sorted_recs = sorted(recs, key=lambda r: priority_order.get(r.get("priority", "low"), 2))

    for rec in sorted_recs:
        priority = rec.get("priority", "low").lower()
        label_map = {"high": "🔴 HIGH", "medium": "🟡 MEDIUM", "low": "🟢 LOW"}
        css_class = f"priority-{priority}"
        cat = rec.get("category", "")
        desc = rec.get("description", "")
        reason = rec.get("reasoning", "")
        impact = rec.get("expected_impact", "")

        with st.expander(f"{label_map.get(priority, priority.upper())} — {cat}: {desc[:80]}"):
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            if reason:
                st.markdown(f"**Why:** {reason}")
            if impact:
                st.markdown(f"**Expected impact:** {impact}")
            st.markdown("</div>", unsafe_allow_html=True)


# ── SWOT display ──────────────────────────────────────────────────

def show_swot(swot_items: list):
    """Display SWOT analysis as a 2x2 grid of cards."""
    if not swot_items:
        return
    section_title("⚡ SWOT Analysis")

    categories = {
        "strengths":    ("💪 Strengths",    "swot-strength"),
        "weaknesses":   ("⚠️ Weaknesses",   "swot-weakness"),
        "opportunities":("🌟 Opportunities","swot-opportunity"),
        "threats":      ("🛡️ Threats",      "swot-threat"),
    }

    # Group items by category
    grouped = {k: [] for k in categories}
    for item in swot_items:
        cat = item.get("category", "").lower()
        if cat in grouped:
            grouped[cat].append(item)

    c1, c2 = st.columns(2)
    for idx, (cat_key, (cat_label, css_class)) in enumerate(categories.items()):
        col = c1 if idx % 2 == 0 else c2
        items = grouped[cat_key]
        with col:
            st.markdown(f"**{cat_label}**")
            if items:
                for item in items:
                    desc = item.get("description", str(item))
                    conf = item.get("confidence", 0)
                    st.markdown(
                        f'<div class="swot-item {css_class}">'
                        f'• {desc} <small style="opacity:0.6">({conf:.0%})</small>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown('<div class="swot-item" style="opacity:0.5">None detected</div>',
                            unsafe_allow_html=True)


# ── Pattern list ──────────────────────────────────────────────────

def show_patterns(patterns: list, team_name: str = "Team"):
    """Show detected/not-detected patterns with confidence."""
    if patterns is None:
        return
    section_title(f"🔍 {team_name} — Tactical Patterns")

    detected = [p for p in patterns if p.get("detected", False)]
    not_detected = [p for p in patterns if not p.get("detected", False)]

    for p in detected:
        name = p.get("name", "Pattern")
        conf = p.get("confidence", 0)
        desc = p.get("description", "")
        players = p.get("involved_players", [])
        with st.container():
            st.markdown(
                f'<div class="pattern-detected">'
                f'✅ <strong>{name}</strong> '
                f'<span style="color:#2E7D32;font-weight:600">{conf:.0%} confidence</span><br>'
                f'<small>{desc}</small>'
                + (f'<br><small style="color:#666">Players: {", ".join(str(x) for x in players)}</small>' if players else '')
                + '</div>',
                unsafe_allow_html=True,
            )

    with st.expander(f"Not detected ({len(not_detected)} patterns)", expanded=False):
        for p in not_detected:
            st.markdown(
                f'<div class="pattern-not-detected">'
                f'○ {p.get("name","Pattern")}'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── Download buttons ──────────────────────────────────────────────

def download_image_button(viz: dict, key: str):
    """Render a download button for a single visualisation."""
    if not viz or not viz.get("image_base64"):
        return
    import base64
    img_bytes = base64.b64decode(viz["image_base64"])
    filename = viz.get("title", "visualization").replace(" ", "_").lower() + ".png"
    st.download_button(
        label="⬇️ Download PNG",
        data=img_bytes,
        file_name=filename,
        mime="image/png",
        key=key,
    )


def download_docx_button(docx_bytes: bytes, filename: str = "report.docx", key: str = "dl_docx"):
    """Render a download button for a Word document."""
    if not docx_bytes:
        return
    st.download_button(
        label="📄 Download Word Report",
        data=docx_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key=key,
    )


# ── Formation display ─────────────────────────────────────────────

def show_formation_result(result: dict, team_a_name: str, team_b_name: str):
    """Display formation detection results for both teams."""
    section_title("📐 Formation Detection")

    metrics = []
    if result.get("team_a_formation"):
        conf_a = result.get("team_a_confidence", 0)
        metrics.append((f"{team_a_name} Formation", result["team_a_formation"],
                         f"{conf_a:.0%} confidence"))
    if result.get("team_b_formation"):
        conf_b = result.get("team_b_confidence", 0)
        metrics.append((f"{team_b_name} Formation", result["team_b_formation"],
                         f"{conf_b:.0%} confidence"))

    if metrics:
        metric_row(metrics)


# ── Explanation text ──────────────────────────────────────────────

def show_explanation(text: str):
    """Display the tactical explanation text in sections."""
    if not text:
        return
    section_title("📝 Tactical Explanation")
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    for para in paragraphs:
        if para.startswith("##") or para.startswith("**"):
            st.markdown(para)
        else:
            st.markdown(
                f'<div class="result-card" style="line-height:1.7">{para}</div>',
                unsafe_allow_html=True,
            )
