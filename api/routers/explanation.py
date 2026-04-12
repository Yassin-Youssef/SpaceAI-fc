"""
SpaceAI FC - Explanation Router
  POST /api/explanation
"""

from fastapi import APIRouter, HTTPException
from api.models.requests import ExplanationRequest
from api.models.responses import ExplanationResponse
from api.services import engine_service

router = APIRouter(tags=["Explanation"])


@router.post("/api/explanation", response_model=ExplanationResponse)
async def explanation(req: ExplanationRequest):
    try:
        text = engine_service.run_explanation(
            mode=req.mode,
            match_info=req.match_info,
            report_data=req.report_data,
            swot_results=req.swot_results,
            recommendations=req.recommendations,
            team_name=req.team_name,
            opponent_name=req.opponent_name,
        )

        # Split into sections at double newlines
        sections = [s.strip() for s in text.split("\n\n") if s.strip()]

        return ExplanationResponse(
            success=True,
            mode=req.mode,
            text=text,
            sections=sections,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
