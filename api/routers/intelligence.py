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
    KnowledgeGraphResponse, IntelligenceResponse, SWOTItem, RecommendationItem
)
from api.services import engine_service
from api.utils.file_handler import parse_dataset
from api.utils.resolve import resolve_input
from pathlib import Path

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

        # Build analysis_data from available data
        analysis_data = _build_analysis_data(req, team_a, team_b, passes)

        swot = engine_service.run_reasoning(
            analysis_data=analysis_data,
            team_name=req.team_a_name,
            opponent_name=req.team_b_name,
        )

        swot_items = _flatten_swot(swot)

        return IntelligenceResponse(
            success=True,
            swot=swot_items,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Recommendations ───────────────────────────────────────────────

@router.post("/api/recommendations", response_model=IntelligenceResponse)
async def recommendations(req: RecommendationsRequest):
    try:
        swot = req.swot_results or {}
        analysis_data = req.analysis_data or {}

        if not swot:
            # Auto-derive SWOT if not provided
            swot = engine_service.run_reasoning(
                analysis_data=analysis_data,
                team_name=req.team_name,
                opponent_name=req.opponent_name,
            )

        recs = engine_service.run_recommendations(
            swot_results=swot,
            analysis_data=analysis_data,
            team_name=req.team_name,
            opponent_name=req.opponent_name,
        )

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
            recommendations=rec_items,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Helpers ───────────────────────────────────────────────────────


def _build_analysis_data(req: ReasoningRequest, team_a, team_b, passes) -> dict:
    """
    Build the analysis_data dict expected by TacticalReasoner.
    Run individual modules if team data is present, otherwise return empty stubs.
    """
    ad = {
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

    if team_a:
        try:
            fm = engine_service.run_formation(team_a, team_b or None,
                                              req.team_a_name, req.team_b_name,
                                              req.team_a_color, req.team_b_color)
            ad["formation_a"] = {"formation": fm.get("team_a_formation", "Unknown"),
                                  "confidence": fm.get("team_a_confidence", 0)}
            if team_b:
                ad["formation_b"] = {"formation": fm.get("team_b_formation", "Unknown"),
                                      "confidence": fm.get("team_b_confidence", 0)}
        except Exception:
            pass

    if team_a and team_b:
        try:
            sc = engine_service.run_space_control(team_a, team_b,
                                                   req.ball_x, req.ball_y,
                                                   req.team_a_name, req.team_b_name)
            ad["space_control"] = {
                "team_a_control": sc["team_a_control"],
                "team_b_control": sc["team_b_control"],
                "zones": sc["zones"],
                "midfield": sc["midfield_control"],
            }
        except Exception:
            pass

    if team_a and passes:
        try:
            pn = engine_service.run_pass_network(team_a, passes,
                                                  req.team_a_name, req.team_a_color)
            ad["pass_summary"] = {
                "total_passes": pn["total_passes"],
                "key_distributor": pn["key_distributor"],
            }
        except Exception:
            pass

    return ad


def _flatten_swot(swot: dict) -> list:
    """Convert SWOT dict {strengths:[], weaknesses:[], ...} to list of SWOTItem."""
    items = []
    for category in ("strengths", "weaknesses", "opportunities", "threats"):
        for entry in swot.get(category, []):
            if isinstance(entry, dict):
                items.append(SWOTItem(
                    category=category,
                    description=entry.get("description", str(entry)),
                    confidence=entry.get("confidence", 0.7),
                    source=entry.get("action", entry.get("source", "")),
                ))
            else:
                items.append(SWOTItem(
                    category=category,
                    description=str(entry),
                    confidence=0.7,
                ))
    return items
