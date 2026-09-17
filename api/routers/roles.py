"""
SpaceAI FC - Player Roles Router
"""

from fastapi import APIRouter, HTTPException
from api.models.requests import RolesRequest
from api.models.responses import RolesResponse, PlayerRoleItem, VisualizationData
from api.services import engine_service
from api.utils.resolve import resolve_input

router = APIRouter(prefix="/api/roles", tags=["Player Roles"])


@router.post("", response_model=RolesResponse)
async def roles(req: RolesRequest):
    try:
        team_a, team_b, _ = resolve_input(req)

        if not team_a:
            raise HTTPException(status_code=400, detail="team_a is required.")

        result = engine_service.run_roles(
            team_a=team_a,
            team_b=team_b or None,
            team_a_name=req.team_a_name,
            team_b_name=req.team_b_name,
            team_a_color=req.team_a_color,
            team_b_color=req.team_b_color,
        )

        return RolesResponse(
            success=True,
            team_a_roles=[PlayerRoleItem(**r) for r in result["team_a_roles"]],
            team_b_roles=[PlayerRoleItem(**r) for r in result["team_b_roles"]],
            visualizations=[VisualizationData(**v) for v in result["visualizations"]],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
