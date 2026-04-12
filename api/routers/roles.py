"""
SpaceAI FC - Player Roles Router
"""

from fastapi import APIRouter, HTTPException
from api.models.requests import RolesRequest
from api.models.responses import RolesResponse, PlayerRoleItem, VisualizationData
from api.services import engine_service
from api.utils.file_handler import parse_dataset
from pathlib import Path

router = APIRouter(prefix="/api/roles", tags=["Player Roles"])


@router.post("", response_model=RolesResponse)
async def roles(req: RolesRequest):
    try:
        team_a, team_b = _resolve_input(req)

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


def _resolve_input(req: RolesRequest):
    if req.input_type == "dataset" and req.dataset_file:
        data = parse_dataset(Path(req.dataset_file))
        return data.get("team_a", []), data.get("team_b", [])
    team_a = [p.model_dump() for p in req.team_a] if req.team_a else []
    team_b = [p.model_dump() for p in req.team_b] if req.team_b else []
    return team_a, team_b
