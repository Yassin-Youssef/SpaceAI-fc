"""
SpaceAI FC - Press Resistance Router
"""

from fastapi import APIRouter, HTTPException
from api.models.requests import PressResistanceRequest
from api.models.responses import PressResistanceResponse, VisualizationData
from api.services import engine_service
from api.utils.file_handler import parse_dataset
from api.utils.resolve import resolve_input
from pathlib import Path

router = APIRouter(prefix="/api/press-resistance", tags=["Press Resistance"])


@router.post("", response_model=PressResistanceResponse)
async def press_resistance(req: PressResistanceRequest):
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

        team_a, team_b, passes = resolve_input(req)

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
