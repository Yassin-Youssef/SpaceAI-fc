"""
SpaceAI FC - Pass Network Router
"""

from fastapi import APIRouter, HTTPException
from api.models.requests import PassNetworkRequest
from api.models.responses import PassNetworkResponse, VisualizationData
from api.services import engine_service
from api.utils.resolve import resolve_input

router = APIRouter(prefix="/api/pass-network", tags=["Pass Network"])


@router.post("", response_model=PassNetworkResponse)
async def pass_network(req: PassNetworkRequest):
    try:
        team_a, _, passes = resolve_input(req)

        if not team_a:
            raise HTTPException(status_code=400, detail="No player data provided.")

        result = engine_service.run_pass_network(
            players=team_a,
            passes=passes,
            team_name=req.team_a_name,
            team_color=req.team_a_color,
            min_passes=req.min_passes,
            sequence=req.sequence,
        )

        return PassNetworkResponse(
            success=True,
            total_passes=result["total_passes"],
            key_distributor=result["key_distributor"],
            most_involved=result["most_involved"],
            top_connections=result["top_connections"],
            weak_links=result["weak_links"],
            centrality=result["centrality"],
            visualizations=[VisualizationData(**v) for v in result["visualizations"]],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


