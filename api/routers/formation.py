"""
SpaceAI FC - Formation Detection Router
"""

from fastapi import APIRouter, HTTPException
from api.models.requests import FormationRequest
from api.models.responses import FormationResponse, VisualizationData
from api.services import engine_service
from api.utils.resolve import resolve_input

router = APIRouter(prefix="/api/formation", tags=["Formation"])


@router.post("", response_model=FormationResponse)
async def formation(req: FormationRequest):
    try:
        team_a, team_b, _ = resolve_input(req)

        if not team_a:
            raise HTTPException(status_code=400, detail="team_a is required.")

        result = engine_service.run_formation(
            team_a=team_a,
            team_b=team_b or None,
            team_a_name=req.team_a_name,
            team_b_name=req.team_b_name,
            team_a_color=req.team_a_color,
            team_b_color=req.team_b_color,
            method=req.method,
        )

        return FormationResponse(
            success=True,
            team_a_formation=result.get("team_a_formation"),
            team_a_confidence=result.get("team_a_confidence"),
            team_a_method=result.get("team_a_method"),
            team_b_formation=result.get("team_b_formation"),
            team_b_confidence=result.get("team_b_confidence"),
            team_b_method=result.get("team_b_method"),
            visualizations=[VisualizationData(**v) for v in result["visualizations"]],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
