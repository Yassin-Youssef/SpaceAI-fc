"""
SpaceAI FC - Intelligence Router
  POST /api/knowledge-graph
  POST /api/reasoning
  POST /api/recommendations
"""

from fastapi import APIRouter, HTTPException
from api.models.requests import (
    KnowledgeGraphRequest, ReasoningRequest, RecommendationsRequest
)
from api.models.responses import (
    KnowledgeGraphResponse, IntelligenceResponse, SWOTItem, RecommendationItem,
    VisualizationData,
)
from api.services import engine_service
from api.utils.resolve import resolve_input

router = APIRouter(tags=["Intelligence"])


# ── Knowledge Graph Query ─────────────────────────────────────────

@router.post("/api/knowledge-graph", response_model=KnowledgeGraphResponse)
async def knowledge_graph(req: KnowledgeGraphRequest):
    try:
        result = engine_service.run_knowledge_graph_query(
            formation=req.formation,
            situation=req.situation,
        )
        return KnowledgeGraphResponse(
            success=True,
            formation=req.formation,
            situation=req.situation,
            counter_strategies=result["counter_strategies"],
            weaknesses=result["weaknesses"],
            strengths=result["strengths"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── SWOT Reasoning ────────────────────────────────────────────────

@router.post("/api/reasoning", response_model=IntelligenceResponse)
async def reasoning(req: ReasoningRequest):
    try:
        team_a, team_b, passes = resolve_input(req)
        analysis_data, visuals = build_analysis_data(req, team_a, team_b, passes)

        swot = engine_service.run_reasoning(
            analysis_data=analysis_data,
            team_name=req.team_a_name,
            opponent_name=req.team_b_name,
        )

        return IntelligenceResponse(
            success=True,
            swot=flatten_swot(swot),
            situations=list(dict.fromkeys(swot.get("situations", []))),
            formation_a=analysis_data["formation_a"]["formation"],
            formation_b=analysis_data["formation_b"]["formation"],
            visualizations=[VisualizationData(**v) for v in visuals],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Recommendations ───────────────────────────────────────────────

@router.post("/api/recommendations", response_model=IntelligenceResponse)
async def recommendations(req: RecommendationsRequest):
    """
    Prioritised tactical recommendations.

    Works from raw positions (runs formation / space / pass / press analysis
    first), from a pre-computed SWOT, or from just a formation + situation
    (knowledge-graph only).
    """
    try:
        team_name = req.team_name or req.team_a_name
        opponent_name = req.opponent_name or req.team_b_name

        team_a, team_b, passes = resolve_input(req)
        visuals = []

        analysis_data = req.analysis_data or {}
        if team_a:
            analysis_data, visuals = build_analysis_data(req, team_a, team_b, passes)
        elif not analysis_data:
            analysis_data = _empty_analysis_data()

        # Manual overrides (used when no positional data is supplied)
        if req.formation:
            analysis_data["formation_a"] = {"formation": req.formation, "confidence": 1.0}

        swot = req.swot_results or engine_service.run_reasoning(
            analysis_data=analysis_data,
            team_name=team_name,
            opponent_name=opponent_name,
        )

        # A user-declared situation feeds the knowledge graph
        kg_insights = []
        if req.situation:
            swot.setdefault("situations", [])
            if req.situation not in swot["situations"]:
                swot["situations"].append(req.situation)
            kg = engine_service.run_knowledge_graph_query(
                formation=analysis_data.get("formation_a", {}).get("formation"),
                situation=req.situation,
            )
            kg_insights = [f"Counter: {c}" for c in kg["counter_strategies"]]
            kg_insights += [f"Formation weakness — {w}" for w in kg["weaknesses"]]
            kg_insights += [f"Formation strength — {s}" for s in kg["strengths"]]
        elif analysis_data.get("formation_a", {}).get("formation") not in (None, "Unknown"):
            kg = engine_service.run_knowledge_graph_query(
                formation=analysis_data["formation_a"]["formation"]
            )
            kg_insights = [f"Formation weakness — {w}" for w in kg["weaknesses"]]
            kg_insights += [f"Formation strength — {s}" for s in kg["strengths"]]

        recs = engine_service.run_recommendations(
            swot_results=swot,
            analysis_data=analysis_data,
            team_name=team_name,
            opponent_name=opponent_name,
        )

        # Knowledge-graph suggested strategies become low-priority recs when
        # the rule engine produced nothing for them
        existing = {r.get("description", "").lower() for r in recs}
        for strat in swot.get("suggested_strategies", []):
            if not isinstance(strat, dict):
                continue
            desc = strat.get("description", "")
            if desc and desc.lower() not in existing:
                recs.append({
                    "priority": "low",
                    "category": "Knowledge Graph",
                    "description": desc,
                    "reasoning": f"Counter-strategy '{strat.get('strategy', '').replace('_', ' ')}' "
                                 f"for the detected tactical situation.",
                    "expected_impact": "Situational edge if executed consistently.",
                })

        rec_items = [
            RecommendationItem(
                priority=r.get("priority", "medium"),
                category=r.get("category", ""),
                description=r.get("description", ""),
                reasoning=r.get("reasoning", ""),
                expected_impact=r.get("expected_impact", ""),
            )
            for r in recs
        ]

        return IntelligenceResponse(
            success=True,
            swot=flatten_swot(swot),
            recommendations=rec_items,
            knowledge_graph_insights=kg_insights,
            situations=list(dict.fromkeys(swot.get("situations", []))),
            formation_a=analysis_data.get("formation_a", {}).get("formation"),
            formation_b=analysis_data.get("formation_b", {}).get("formation"),
            visualizations=[VisualizationData(**v) for v in visuals],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Helpers (shared with the explanation router) ──────────────────

def _empty_analysis_data() -> dict:
    return {
        "formation_a": {"formation": "Unknown", "confidence": 0},
        "formation_b": {"formation": "Unknown", "confidence": 0},
        "space_control": {"team_a_control": 50, "team_b_control": 50,
                          "zones": {}, "midfield": {}},
        "pass_summary": {"total_passes": 0, "key_distributor": {}},
        "press_resistance": {"press_resistance_score": 50},
        "patterns_a": [],
        "patterns_b": [],
        "roles_a": [],
        "roles_b": [],
    }


def build_analysis_data(req, team_a, team_b, passes) -> tuple:
    """
    Build the analysis_data dict expected by TacticalReasoner by running the
    Phase 1 + 2 modules that the supplied data allows.

    Returns (analysis_data, visualizations).
    """
    ad = _empty_analysis_data()
    visuals = []
    raw = {}

    if team_a:
        try:
            fm = engine_service.run_formation(team_a, team_b or None,
                                              req.team_a_name, req.team_b_name,
                                              req.team_a_color, req.team_b_color)
            raw["formation"] = fm
            ad["formation_a"] = {"formation": fm.get("team_a_formation", "Unknown"),
                                 "confidence": fm.get("team_a_confidence", 0)}
            if team_b:
                ad["formation_b"] = {"formation": fm.get("team_b_formation", "Unknown"),
                                     "confidence": fm.get("team_b_confidence", 0)}
            visuals += fm.get("visualizations", [])
        except Exception:
            pass

        try:
            ro = engine_service.run_roles(team_a, team_b or None,
                                          req.team_a_name, req.team_b_name,
                                          req.team_a_color, req.team_b_color)
            ad["roles_a"] = ro["team_a_roles"]
            ad["roles_b"] = ro["team_b_roles"]
        except Exception:
            pass

    if team_a and team_b:
        try:
            sc = engine_service.run_space_control(team_a, team_b,
                                                  req.ball_x, req.ball_y,
                                                  req.team_a_name, req.team_b_name,
                                                  req.team_a_color, req.team_b_color,
                                                  mode="voronoi")
            raw["space_control"] = sc
            ad["space_control"] = {
                "team_a_control": sc["team_a_control"],
                "team_b_control": sc["team_b_control"],
                "zones": sc["zones"],
                "midfield": sc["midfield_control"],
            }
            visuals += sc.get("visualizations", [])
        except Exception:
            pass

        try:
            pt = engine_service.run_patterns(team_a, team_b,
                                             req.team_a_name, req.team_b_name,
                                             req.team_a_color, req.team_b_color,
                                             analyze_team="both")
            ad["patterns_a"] = pt["team_a_patterns"]
            ad["patterns_b"] = pt["team_b_patterns"]
        except Exception:
            pass

        if passes:
            try:
                pr = engine_service.run_press_resistance(
                    team_a, team_b, passes,
                    req.team_a_name, req.team_a_color, req.team_b_name,
                )
                raw["press_resistance"] = pr
                ad["press_resistance"] = {
                    "press_resistance_score": pr["press_resistance_score"],
                    "pass_success_under_pressure": pr["pass_success_under_pressure"],
                    "escape_rate": pr["escape_rate"],
                }
            except Exception:
                pass

    if team_a and passes:
        try:
            pn = engine_service.run_pass_network(team_a, passes,
                                                 req.team_a_name, req.team_a_color)
            raw["pass_network"] = pn
            ad["pass_summary"] = {
                "total_passes": pn["total_passes"],
                "key_distributor": pn["key_distributor"],
                "weak_links": pn["weak_links"],
            }
            visuals += pn.get("visualizations", [])
        except Exception:
            pass

    ad["_raw"] = raw
    return ad, visuals


def flatten_swot(swot: dict) -> list:
    """Convert SWOT dict {strengths:[], weaknesses:[], ...} to list of SWOTItem."""
    items = []
    for category in ("strengths", "weaknesses", "opportunities", "threats"):
        for entry in swot.get(category, []):
            if isinstance(entry, dict):
                items.append(SWOTItem(
                    category=category,
                    description=entry.get("description", str(entry)),
                    confidence=float(entry.get("confidence", 0.7)),
                    source=entry.get("action", entry.get("source", "")),
                ))
            else:
                items.append(SWOTItem(
                    category=category,
                    description=str(entry),
                    confidence=0.7,
                ))
    return items
