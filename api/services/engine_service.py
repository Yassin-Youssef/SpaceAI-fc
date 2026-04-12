"""
SpaceAI FC - Engine Service
==============================
Stateless wrapper functions that call engine modules and return
serialisable dicts + matplotlib figures for base64 encoding.

Each function is independent — no shared state between calls.
"""

import matplotlib
matplotlib.use('Agg')

from api.utils.image_encoder import fig_to_base64

# ── Engine imports ────────────────────────────────────────────────
from engine.analysis.pass_network import PassNetwork
from engine.analysis.space_control import SpaceControl
from engine.analysis.formation_detection import FormationDetector
from engine.analysis.role_classifier import RoleClassifier
from engine.analysis.press_resistance import PressResistance
from engine.analysis.pattern_detection import PatternDetector
from engine.intelligence.knowledge_graph import TacticalKnowledgeGraph
from engine.intelligence.tactical_reasoning import TacticalReasoner
from engine.intelligence.strategy_recommender import StrategyRecommender
from engine.intelligence.explanation_layer import ExplanationLayer


# ════════════════════════════════════════════════════════════════
# Pass Network
# ════════════════════════════════════════════════════════════════

def run_pass_network(
    players: list,
    passes: list,
    team_name: str = "Team A",
    team_color: str = "#e74c3c",
    min_passes: int = 2,
    sequence: list = None,
) -> dict:
    """
    Build pass network and return summary + base64 visualisations.

    Parameters:
        players: list of player dicts (name, number, x, y, position)
        passes: list of PassEvent dicts
        sequence: optional list of player numbers for sequence viz
    """
    pn = PassNetwork()
    pn.add_players(players)

    pass_tuples = [(p["passer"], p["receiver"], p.get("success", True)) for p in passes]
    pn.add_passes(pass_tuples)

    summary = pn.get_summary()
    # get_centrality() returns {int_jersey: {...}} — stringify keys for JSON/Pydantic
    centrality = {str(k): v for k, v in pn.get_centrality().items()}

    visuals = []

    # Network viz
    fig, _ = pn.draw(
        title=f"{team_name} — Pass Network",
        team_color=team_color,
        team_name=team_name,
        min_passes=min_passes,
    )
    visuals.append({"image_base64": fig_to_base64(fig), "title": "Pass Network"})

    # Sequence viz (if provided)
    if sequence and len(sequence) >= 2:
        fig2, _ = pn.draw_sequence(
            sequence,
            title=f"{team_name} — Pass Sequence",
            team_color=team_color,
            team_name=team_name,
        )
        visuals.append({"image_base64": fig_to_base64(fig2), "title": "Pass Sequence"})

    return {
        "total_passes": summary["total_passes"],
        "key_distributor": summary["key_distributor"],
        "most_involved": summary["most_involved"],
        "top_connections": summary["top_connections"],
        "weak_links": summary["weak_links"],
        "centrality": centrality,
        "visualizations": visuals,
    }


# ════════════════════════════════════════════════════════════════
# Space Control
# ════════════════════════════════════════════════════════════════

def run_space_control(
    team_a: list,
    team_b: list,
    ball_x: float = 60.0,
    ball_y: float = 40.0,
    team_a_name: str = "Team A",
    team_b_name: str = "Team B",
    team_a_color: str = "#e74c3c",
    team_b_color: str = "#3498db",
    mode: str = "both",
    sigma: float = 15.0,
) -> dict:
    sc = SpaceControl()
    sc.set_teams(team_a, team_b)
    sc.set_ball(ball_x, ball_y)

    visuals = []
    stats = {}

    if mode in ("voronoi", "both"):
        fig, _, vstats = sc.draw_voronoi(
            title=f"{team_a_name} vs {team_b_name} — Space Control (Voronoi)",
            team_a_name=team_a_name,
            team_b_name=team_b_name,
            team_a_color=team_a_color,
            team_b_color=team_b_color,
        )
        stats = vstats
        visuals.append({"image_base64": fig_to_base64(fig), "title": "Voronoi Space Control"})

    if mode in ("influence", "both"):
        fig, _, istats = sc.draw_influence(
            title=f"{team_a_name} vs {team_b_name} — Space Control (Influence)",
            team_a_name=team_a_name,
            team_b_name=team_b_name,
            team_a_color=team_a_color,
            team_b_color=team_b_color,
            sigma=sigma,
        )
        stats = istats  # use influence stats when both modes
        visuals.append({"image_base64": fig_to_base64(fig), "title": "Influence Space Control"})

    _, computed_stats = sc.compute_voronoi_control()
    midfield = sc.get_midfield_control(sc.compute_voronoi_control()[0])

    return {
        "team_a_control": computed_stats["team_a_control"],
        "team_b_control": computed_stats["team_b_control"],
        "zones": computed_stats["zones"],
        "midfield_control": midfield,
        "visualizations": visuals,
    }


# ════════════════════════════════════════════════════════════════
# Formation Detection
# ════════════════════════════════════════════════════════════════

def run_formation(
    team_a: list,
    team_b: list = None,
    team_a_name: str = "Team A",
    team_b_name: str = "Team B",
    team_a_color: str = "#e74c3c",
    team_b_color: str = "#3498db",
    method: str = "auto",
) -> dict:
    result = {}
    visuals = []

    if team_a:
        fd_a = FormationDetector()
        fd_a.set_team(team_a, team_a_name, team_a_color)
        res_a = fd_a.detect(method=method)
        fig, _ = fd_a.draw(res_a, title=f"{team_a_name} — Formation")
        visuals.append({"image_base64": fig_to_base64(fig), "title": f"{team_a_name} Formation"})
        result["team_a_formation"] = res_a["formation"]
        result["team_a_confidence"] = res_a["confidence"]
        result["team_a_method"] = res_a["method"]
        result["team_a_lines"] = [
            [{"name": p["name"], "number": p["number"]} for p in line]
            for line in res_a.get("lines", [])
        ]

    if team_b:
        fd_b = FormationDetector()
        fd_b.set_team(team_b, team_b_name, team_b_color)
        res_b = fd_b.detect(method=method)
        fig, _ = fd_b.draw(res_b, title=f"{team_b_name} — Formation")
        visuals.append({"image_base64": fig_to_base64(fig), "title": f"{team_b_name} Formation"})
        result["team_b_formation"] = res_b["formation"]
        result["team_b_confidence"] = res_b["confidence"]
        result["team_b_method"] = res_b["method"]
        result["team_b_lines"] = [
            [{"name": p["name"], "number": p["number"]} for p in line]
            for line in res_b.get("lines", [])
        ]

    result["visualizations"] = visuals
    return result


# ════════════════════════════════════════════════════════════════
# Role Classification
# ════════════════════════════════════════════════════════════════

def run_roles(
    team_a: list,
    team_b: list = None,
    team_a_name: str = "Team A",
    team_b_name: str = "Team B",
    team_a_color: str = "#e74c3c",
    team_b_color: str = "#3498db",
) -> dict:
    result = {"team_a_roles": [], "team_b_roles": [], "visualizations": []}
    visuals = []

    if team_a:
        rc_a = RoleClassifier()
        rc_a.set_team(team_a, team_a_name, team_a_color)
        roles_a = rc_a.classify_all()
        fig, _ = rc_a.draw(roles_a, title=f"{team_a_name} — Player Roles")
        visuals.append({"image_base64": fig_to_base64(fig), "title": f"{team_a_name} Roles"})
        result["team_a_roles"] = roles_a

    if team_b:
        rc_b = RoleClassifier()
        rc_b.set_team(team_b, team_b_name, team_b_color)
        roles_b = rc_b.classify_all()
        fig, _ = rc_b.draw(roles_b, title=f"{team_b_name} — Player Roles")
        visuals.append({"image_base64": fig_to_base64(fig), "title": f"{team_b_name} Roles"})
        result["team_b_roles"] = roles_b

    result["visualizations"] = visuals
    return result


# ════════════════════════════════════════════════════════════════
# Press Resistance
# ════════════════════════════════════════════════════════════════

def run_press_resistance(
    team_positions: list,
    opponent_positions: list,
    pass_events: list,
    team_name: str = "Team A",
    team_color: str = "#e74c3c",
    opponent_name: str = "Team B",
    pressure_radius: float = 10.0,
    pressure_threshold: int = 2,
) -> dict:
    pr = PressResistance(
        pressure_radius=pressure_radius,
        pressure_threshold=pressure_threshold,
    )
    pr.set_teams(
        team_positions, opponent_positions,
        team_name=team_name,
        team_color=team_color,
        opponent_name=opponent_name,
    )

    events = [
        {
            "passer": p.get("passer", 0),
            "receiver": p.get("receiver", 0),
            "success": p.get("success", True),
            "x": p.get("x", 0),
            "y": p.get("y", 0),
            "end_x": p.get("end_x", 0),
            "end_y": p.get("end_y", 0),
        }
        for p in pass_events
    ]
    pr.add_pass_events(events)

    analysis = pr.analyze()

    fig, _ = pr.draw(
        result=analysis,
        title=f"{team_name} — Press Resistance",
    )
    viz = {"image_base64": fig_to_base64(fig), "title": "Press Resistance Heatmap"}

    return {
        "press_resistance_score": analysis["press_resistance_score"],
        "total_passes": analysis["total_passes"],
        "passes_under_pressure": analysis["passes_under_pressure"],
        "pass_success_overall": analysis["pass_success_overall"],
        "pass_success_under_pressure": analysis["pass_success_under_pressure"],
        "escape_rate": analysis["escape_rate"],
        "vulnerable_zones": analysis["vulnerable_zones"],
        "visualizations": [viz],
    }


# ════════════════════════════════════════════════════════════════
# Pattern Detection
# ════════════════════════════════════════════════════════════════

def run_patterns(
    team_a: list,
    team_b: list,
    team_a_name: str = "Team A",
    team_b_name: str = "Team B",
    team_a_color: str = "#e74c3c",
    team_b_color: str = "#3498db",
    analyze_team: str = "a",
) -> dict:
    pd_inst = PatternDetector()
    pd_inst.set_teams(
        team_a, team_b,
        team_a_name=team_a_name,
        team_b_name=team_b_name,
        team_a_color=team_a_color,
        team_b_color=team_b_color,
    )

    result = {"team_a_patterns": [], "team_b_patterns": [], "visualizations": []}
    visuals = []

    def _normalise_patterns(raw: list) -> list:
        out = []
        for p in raw:
            if p is None:
                continue
            out.append({
                "name": p.get("pattern", p.get("name", "Unknown")),
                "detected": p.get("detected", p.get("confidence", 0) > 0.5),
                "confidence": round(float(p.get("confidence", 0.0)), 2),
                "description": p.get("description", ""),
                "involved_players": p.get("involved_players", []),
            })
        return out

    if analyze_team in ("a", "both"):
        raw_a = pd_inst.detect_all(team="a")
        result["team_a_patterns"] = _normalise_patterns(raw_a)

    if analyze_team in ("b", "both"):
        raw_b = pd_inst.detect_all(team="b")
        result["team_b_patterns"] = _normalise_patterns(raw_b)

    # Draw viz if the module has a draw method
    try:
        fig, _ = pd_inst.draw(title=f"Tactical Patterns — {team_a_name} vs {team_b_name}")
        visuals.append({"image_base64": fig_to_base64(fig), "title": "Tactical Patterns"})
    except Exception:
        pass

    result["visualizations"] = visuals
    return result


# ════════════════════════════════════════════════════════════════
# Tactical Intelligence (SWOT + Recommendations)
# ════════════════════════════════════════════════════════════════

def run_reasoning(
    analysis_data: dict,
    team_name: str = "Team A",
    opponent_name: str = "Team B",
) -> dict:
    kg = TacticalKnowledgeGraph()
    reasoner = TacticalReasoner(knowledge_graph=kg)
    reasoner.set_analysis(analysis_data, team_name=team_name, opponent_name=opponent_name)
    swot = reasoner.reason()
    return swot


def run_recommendations(
    swot_results: dict,
    analysis_data: dict,
    team_name: str = "Team A",
    opponent_name: str = "Team B",
) -> list:
    kg = TacticalKnowledgeGraph()
    rec = StrategyRecommender(knowledge_graph=kg)
    rec.set_reasoning(swot_results, analysis_data, team_name=team_name, opponent_name=opponent_name)
    return rec.recommend()


def run_knowledge_graph_query(
    formation: str = None,
    situation: str = None,
) -> dict:
    kg = TacticalKnowledgeGraph()
    result = {"counter_strategies": [], "weaknesses": [], "strengths": []}

    if formation:
        try:
            raw = kg.get_formation_weaknesses(formation)
            # Returns [{'situation': str, 'description': str}, ...] — extract description strings
            result["weaknesses"] = [
                f"{w['situation']}: {w['description']}" if isinstance(w, dict) else str(w)
                for w in raw
            ]
        except Exception:
            pass
        try:
            raw = kg.get_formation_strengths(formation)
            result["strengths"] = [
                f"{s['situation']}: {s['description']}" if isinstance(s, dict) else str(s)
                for s in raw
            ]
        except Exception:
            pass

    if situation:
        try:
            # Method is get_counter_strategies, not get_counters
            raw = kg.get_counter_strategies(situation)
            result["counter_strategies"] = [
                f"{c['strategy']}: {c['description']}" if isinstance(c, dict) else str(c)
                for c in raw
            ]
        except Exception:
            pass

    return result


# ════════════════════════════════════════════════════════════════
# Explanation
# ════════════════════════════════════════════════════════════════

def run_explanation(
    mode: str = "template",
    match_info: dict = None,
    report_data: dict = None,
    swot_results: dict = None,
    recommendations: list = None,
    team_name: str = "Team A",
    opponent_name: str = "Team B",
) -> str:
    exp = ExplanationLayer(mode=mode)
    exp.set_data(
        match_info=match_info or {},
        report_data=report_data or {},
        swot_results=swot_results or {},
        recommendations=recommendations or [],
        team_name=team_name,
        opponent_name=opponent_name,
    )
    return exp.generate()


# ════════════════════════════════════════════════════════════════
# Full Pipeline
# ════════════════════════════════════════════════════════════════

def run_full_pipeline(
    team_a: list,
    team_b: list,
    passes: list,
    ball_x: float = 60.0,
    ball_y: float = 40.0,
    team_a_name: str = "Team A",
    team_b_name: str = "Team B",
    team_a_color: str = "#e74c3c",
    team_b_color: str = "#3498db",
    match_info: dict = None,
) -> dict:
    """Run the full Sense → Understand → Reason → Act → Explain pipeline."""
    results = {}

    # Phase 1
    pn_result = run_pass_network(team_a, passes, team_a_name, team_a_color)
    sc_result = run_space_control(
        team_a, team_b, ball_x, ball_y,
        team_a_name, team_b_name, team_a_color, team_b_color, mode="both"
    )

    # Phase 2
    fm_result = run_formation(team_a, team_b, team_a_name, team_b_name, team_a_color, team_b_color)
    ro_result = run_roles(team_a, team_b, team_a_name, team_b_name, team_a_color, team_b_color)
    pr_result = run_press_resistance(team_a, team_b, passes, team_a_name, team_a_color, team_b_name)
    pt_result = run_patterns(
        team_a, team_b, team_a_name, team_b_name, team_a_color, team_b_color, analyze_team="both"
    )

    # Phase 3
    analysis_data = {
        "formation_a": {"formation": fm_result.get("team_a_formation", "Unknown"),
                        "confidence": fm_result.get("team_a_confidence", 0)},
        "formation_b": {"formation": fm_result.get("team_b_formation", "Unknown"),
                        "confidence": fm_result.get("team_b_confidence", 0)},
        "space_control": {
            "team_a_control": sc_result["team_a_control"],
            "team_b_control": sc_result["team_b_control"],
            "zones": sc_result["zones"],
            "midfield": sc_result["midfield_control"],
        },
        "pass_summary": {
            "total_passes": pn_result["total_passes"],
            "key_distributor": pn_result["key_distributor"],
        },
        "press_resistance": {
            "press_resistance_score": pr_result["press_resistance_score"],
        },
        "patterns_a": pt_result["team_a_patterns"],
        "patterns_b": pt_result["team_b_patterns"],
        "roles_a": ro_result["team_a_roles"],
        "roles_b": ro_result["team_b_roles"],
    }

    swot = run_reasoning(analysis_data, team_a_name, team_b_name)
    recs = run_recommendations(swot, analysis_data, team_a_name, team_b_name)
    explanation = run_explanation(
        mode="template",
        match_info=match_info,
        swot_results=swot,
        recommendations=recs,
        team_name=team_a_name,
        opponent_name=team_b_name,
    )

    # Collect all visualisations
    all_visuals = (
        pn_result["visualizations"]
        + sc_result["visualizations"]
        + fm_result["visualizations"]
        + ro_result["visualizations"]
        + pr_result["visualizations"]
        + pt_result["visualizations"]
    )

    return {
        "pass_network": pn_result,
        "space_control": sc_result,
        "formation": fm_result,
        "roles": ro_result,
        "press_resistance": pr_result,
        "patterns": pt_result,
        "swot": swot,
        "recommendations": recs,
        "explanation": explanation,
        "visualizations": all_visuals,
    }
