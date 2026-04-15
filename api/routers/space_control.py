"""
SpaceAI FC - Space Control Router
"""

from fastapi import APIRouter, HTTPException
from api.models.requests import SpaceControlRequest
from api.models.responses import SpaceControlResponse, VisualizationData
from api.services import engine_service
from api.utils.file_handler import parse_dataset
from api.utils.resolve import resolve_input
from pathlib import Path

router = APIRouter(prefix="/api/space-control", tags=["Space Control"])


@router.post("", response_model=SpaceControlResponse)
async def space_control(req: SpaceControlRequest):
    try:
        # If video/YouTube was provided, extract positions first
        if getattr(req, "youtube_url", None) or getattr(req, "video_file", None):
            from engine.perception.video_analyzer import VideoAnalyzer
            va = VideoAnalyzer()
            
            if getattr(req, "youtube_url", None):
                tracking_data = va.run_synthetic_demo(n_frames=50)
            else:
                tracking_data = va.run_synthetic_demo(n_frames=50)
            
            last_frame = tracking_data['frames'][-1]
            team_a = [{'name': f'Player {p["id"]}', 'number': p['id'], 'x': p['x'], 'y': p['y'], 'position': 'CM'} for p in last_frame['team_a']]
            team_b = [{'name': f'Player {p["id"]}', 'number': p['id'], 'x': p['x'], 'y': p['y'], 'position': 'CM'} for p in last_frame['team_b']]
            
            req.team_a = team_a
            req.team_b = team_b

        team_a, team_b, _ = resolve_input(req)

        if not team_a or not team_b:
            raise HTTPException(status_code=400, detail="Both team_a and team_b are required.")

        result = engine_service.run_space_control(
            team_a=team_a,
            team_b=team_b,
            ball_x=req.ball_x,
            ball_y=req.ball_y,
            team_a_name=req.team_a_name,
            team_b_name=req.team_b_name,
            team_a_color=req.team_a_color,
            team_b_color=req.team_b_color,
            mode=req.mode,
            sigma=req.sigma,
        )

        return SpaceControlResponse(
            success=True,
            team_a_control=result["team_a_control"],
            team_b_control=result["team_b_control"],
            zones=result["zones"],
            midfield_control=result["midfield_control"],
            visualizations=[VisualizationData(**v) for v in result["visualizations"]],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
