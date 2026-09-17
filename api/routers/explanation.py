"""
SpaceAI FC - Explanation Router
  POST /api/explanation

Generates a natural-language tactical report.  When team positions are
provided the report is grounded in a fresh run of the analysis engine.
LLM mode uses the configured provider (OpenRouter → Anthropic) and falls
back to the deterministic template engine when no key is available.
"""

from fastapi import APIRouter, HTTPException

from api.models.requests import ExplanationRequest
from api.models.responses import ExplanationResponse, VisualizationData
from api.services import engine_service
from api.services.llm_service import ask_llm, has_llm
from api.utils.resolve import resolve_input
from api.routers.intelligence import build_analysis_data

router = APIRouter(tags=["Explanation"])


@router.post("/api/explanation", response_model=ExplanationResponse)
async def explanation(req: ExplanationRequest):
    try:
        team_name = req.team_name or req.team_a_name
        opponent_name = req.opponent_name or req.team_b_name

        team_a, team_b, passes = resolve_input(req)

        match_info = dict(req.report_match_info or {})
        if req.match_info:
            match_info = {**req.match_info.model_dump(), **match_info}
        match_info.setdefault("home_team", team_name)
        match_info.setdefault("away_team", opponent_name)

        report_data = req.report_data or {}
        swot = req.swot_results or {}
        recs = req.recommendations or []
        visuals = []
        summary = {}

        # Ground the report in real analysis when positions are provided
        if team_a:
            analysis_data, visuals = build_analysis_data(req, team_a, team_b, passes)
            raw = analysis_data.pop("_raw", {})

            report_data = _report_data_from_analysis(
                analysis_data, raw, team_name, opponent_name
            )
            swot = engine_service.run_reasoning(analysis_data, team_name, opponent_name)
            recs = engine_service.run_recommendations(swot, analysis_data, team_name, opponent_name)

            summary = {
                "formation_a": analysis_data["formation_a"]["formation"],
                "formation_b": analysis_data["formation_b"]["formation"],
                "team_a_control": analysis_data["space_control"]["team_a_control"],
                "team_b_control": analysis_data["space_control"]["team_b_control"],
                "total_passes": analysis_data["pass_summary"]["total_passes"],
                "press_resistance_score": analysis_data["press_resistance"]["press_resistance_score"],
                "high_priority_recs": sum(1 for r in recs if r.get("priority") == "high"),
                "situations": list(dict.fromkeys(swot.get("situations", []))),
            }

        mode_used = "template"
        text = ""

        if req.mode == "llm" and has_llm():
            text = await _generate_llm_report(
                match_info, report_data, swot, recs, team_name, opponent_name
            )
            if text:
                mode_used = "llm"

        if not text:
            text = engine_service.run_explanation(
                mode="template",
                match_info=match_info,
                report_data=report_data,
                swot_results=swot,
                recommendations=recs,
                team_name=team_name,
                opponent_name=opponent_name,
            )

        sections = [s.strip() for s in text.split("\n\n") if s.strip()]

        return ExplanationResponse(
            success=True,
            mode=mode_used,
            text=text,
            sections=sections,
            summary=summary,
            visualizations=[VisualizationData(**v) for v in visuals],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Helpers ───────────────────────────────────────────────────────

def _report_data_from_analysis(ad: dict, raw: dict, team_name: str, opponent_name: str) -> dict:
    """Shape engine output into the report_data structure the template engine reads."""
    sc = ad.get("space_control", {})
    pr = ad.get("press_resistance", {})
    ps = ad.get("pass_summary", {})
    return {
        "team_a": {"name": team_name, "formation": ad["formation_a"]["formation"]},
        "team_b": {"name": opponent_name, "formation": ad["formation_b"]["formation"]},
        "pass_analysis": {
            "total_passes": ps.get("total_passes", 0),
            "key_distributor": ps.get("key_distributor", {}),
        },
        "space_analysis": {
            "overall": {
                "team_a_control": sc.get("team_a_control", 50),
                "team_b_control": sc.get("team_b_control", 50),
            },
            "zones": sc.get("zones", {}),
        },
        "press_resistance": {
            "press_resistance_score": pr.get("press_resistance_score", 50),
            "pass_success_under_pressure": pr.get("pass_success_under_pressure", 0),
            "escape_rate": pr.get("escape_rate", 0),
        } if raw.get("press_resistance") else {},
    }


async def _generate_llm_report(match_info, report_data, swot, recs, team_name, opponent_name) -> str:
    """Ask the configured LLM for a briefing grounded in the analysis summary."""
    from engine.intelligence.explanation_layer import ExplanationLayer

    layer = ExplanationLayer(mode="template")
    layer.set_data(
        match_info=match_info,
        report_data=report_data,
        swot_results=swot,
        recommendations=recs,
        team_name=team_name,
        opponent_name=opponent_name,
    )
    data_summary = layer._build_data_summary()

    prompt = (
        "You are writing a post-match tactical briefing for a professional coaching staff. "
        "Using ONLY the analysis below, write 4 short paragraphs: match overview, tactical "
        "situation, strengths and vulnerabilities, and specific recommendations. "
        "Reference the real formations, players and numbers. Do not invent statistics.\n\n"
        f"{data_summary}"
    )
    try:
        answer, mode = await ask_llm(prompt, context=None)
        if mode == "knowledge_graph":
            return ""
        return answer.strip()
    except Exception:
        return ""
