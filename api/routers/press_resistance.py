"""
SpaceAI FC - Press Resistance Router
"""

from fastapi import APIRouter, HTTPException
from api.models.requests import PressResistanceRequest
from api.models.responses import PressResistanceResponse, VisualizationData
from api.services import engine_service
from api.utils.file_handler import parse_dataset
from pathlib import Path

router = APIRouter(prefix="/api/press-resistance", tags=["Press Resistance"])


@router.post("", response_model=PressResistanceResponse)
async def press_resistance(req: PressResistanceRequest):
    try:
        team_a, team_b, passes = _resolve_input(req)

        if not team_a:
            raise HTTPException(status_code=400, detail="team_a is required.")
        if not team_b:
            raise HTTPException(status_code=400, detail="team_b (opponent) is required.")

        result = engine_service.run_press_resistance(
            team_positions=team_a,
            opponent_positions=team_b,
            pass_events=passes,
            team_name=req.team_a_name,
            team_color=req.team_a_color,
            opponent_name=req.team_b_name,
            pressure_radius=req.pressure_radius,
            pressure_threshold=req.pressure_threshold,
        )

        return PressResistanceResponse(
            success=True,
            press_resistance_score=result["press_resistance_score"],
            total_passes=result["total_passes"],
            passes_under_pressure=result["passes_under_pressure"],
            pass_success_overall=result["pass_success_overall"],
            pass_success_under_pressure=result["pass_success_under_pressure"],
            escape_rate=result["escape_rate"],
            vulnerable_zones=result["vulnerable_zones"],
            visualizations=[VisualizationData(**v) for v in result["visualizations"]],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _resolve_input(req: PressResistanceRequest):
    if req.input_type == "dataset" and req.dataset_file:
        data = parse_dataset(Path(req.dataset_file))
        return data.get("team_a", []), data.get("team_b", []), data.get("passes", [])
    team_a = [p.model_dump() for p in req.team_a] if req.team_a else []
    team_b = [p.model_dump() for p in req.team_b] if req.team_b else []
    passes = [p.model_dump() for p in req.passes] if req.passes else []
    return team_a, team_b, passes
