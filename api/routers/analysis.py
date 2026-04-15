"""
SpaceAI FC - Full Analysis Router
  POST /api/analyze
  POST /api/tactical-analysis
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pathlib import Path

from api.models.requests import AnalysisRequest, TacticalAnalysisRequest
from api.models.responses import (
    FullAnalysisResponse, FormationResponse, SpaceControlResponse,
    PassNetworkResponse, PressResistanceResponse, PatternsResponse,
    RolesResponse, IntelligenceResponse, ExplanationResponse,
    SWOTItem, RecommendationItem, VisualizationData, PlayerRoleItem, PatternItem,
)
from api.services import engine_service
from api.utils.file_handler import parse_dataset, save_dataset_upload, cleanup
from api.utils.resolve import resolve_input

router = APIRouter(tags=["Analysis"])


@router.post("/api/analyze", response_model=FullAnalysisResponse)
async def full_analysis(req: AnalysisRequest):
    """
    Run the full Sense → Understand → Reason → Act → Explain pipeline.
    Returns all phase results plus all visualisations as base64 images.
    """
    dataset_path = None
    try:
        # If video/YouTube was provided, extract positions first
        if getattr(req, "youtube_url", None) or getattr(req, "video_file", None):
            from engine.perception.video_analyzer import VideoAnalyzer
            va = VideoAnalyzer()
            
            if getattr(req, "youtube_url", None):
                # Process YouTube URL
                tracking_data = va.run_synthetic_demo(n_frames=50)  # Use synthetic for now until real video processing works
            else:
                # Process uploaded video file
                tracking_data = va.run_synthetic_demo(n_frames=50)
            
            # Convert last frame's positions to team_a and team_b format
            last_frame = tracking_data['frames'][-1]
            team_a = [{'name': f'Player {p["id"]}', 'number': p['id'], 'x': p['x'], 'y': p['y'], 'position': 'CM'} for p in last_frame['team_a']]
            team_b = [{'name': f'Player {p["id"]}', 'number': p['id'], 'x': p['x'], 'y': p['y'], 'position': 'CM'} for p in last_frame['team_b']]
            
            # Use extracted data instead of manual input
            req.team_a = team_a
            req.team_b = team_b

        team_a, team_b, passes = resolve_input(req)

        if not team_a or not team_b:
            raise HTTPException(
                status_code=400,
                detail="Both team_a and team_b are required for full analysis.",
            )

        match_info = req.match_info.model_dump() if req.match_info else {}

        result = engine_service.run_full_pipeline(
            team_a=team_a,
            team_b=team_b,
            passes=passes,
            ball_x=req.ball_x,
            ball_y=req.ball_y,
            team_a_name=req.team_a_name,
            team_b_name=req.team_b_name,
            team_a_color=req.team_a_color,
            team_b_color=req.team_b_color,
            match_info=match_info or None,
        )

        return _build_full_response(result, req, match_info)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        cleanup(dataset_path)


@router.post("/api/tactical-analysis", response_model=FullAnalysisResponse)
async def tactical_analysis(req: TacticalAnalysisRequest):
    """
    Analyse team structure, space control, and passing for a match segment.
    Runs Phase 1 + Phase 2 only (no SWOT / recommendations).
    """
    dataset_path = None
    try:
        # If video/YouTube was provided, extract positions first
        if getattr(req, "youtube_url", None) or getattr(req, "video_file", None):
            from engine.perception.video_analyzer import VideoAnalyzer
            va = VideoAnalyzer()
            
            if getattr(req, "youtube_url", None):
                # Process YouTube URL
                tracking_data = va.run_synthetic_demo(n_frames=50)  # Use synthetic for now until real video processing works
            else:
                # Process uploaded video file
                tracking_data = va.run_synthetic_demo(n_frames=50)
            
            # Convert last frame's positions to team_a and team_b format
            last_frame = tracking_data['frames'][-1]
            team_a = [{'name': f'Player {p["id"]}', 'number': p['id'], 'x': p['x'], 'y': p['y'], 'position': 'CM'} for p in last_frame['team_a']]
            team_b = [{'name': f'Player {p["id"]}', 'number': p['id'], 'x': p['x'], 'y': p['y'], 'position': 'CM'} for p in last_frame['team_b']]
            
            # Use extracted data instead of manual input
            req.team_a = team_a
            req.team_b = team_b

        team_a, team_b, passes = resolve_input(req)

        if not team_a:
            raise HTTPException(status_code=400, detail="team_a is required.")

        match_info = req.match_info.model_dump() if req.match_info else {}

        # Phase 1
        pn = engine_service.run_pass_network(
            team_a, passes, req.team_a_name, req.team_a_color
        ) if passes else None

        sc = engine_service.run_space_control(
            team_a, team_b or [],
            req.ball_x, req.ball_y,
            req.team_a_name, req.team_b_name,
            req.team_a_color, req.team_b_color,
        ) if team_b else None

        # Phase 2
        fm = engine_service.run_formation(
            team_a, team_b or None,
            req.team_a_name, req.team_b_name,
            req.team_a_color, req.team_b_color,
        )

        ro = engine_service.run_roles(
            team_a, team_b or None,
            req.team_a_name, req.team_b_name,
            req.team_a_color, req.team_b_color,
        )

        all_visuals = (
            (pn["visualizations"] if pn else [])
            + (sc["visualizations"] if sc else [])
            + fm["visualizations"]
            + ro["visualizations"]
        )

        return FullAnalysisResponse(
            success=True,
            match_info=match_info,
            formation=FormationResponse(
                success=True,
                team_a_formation=fm.get("team_a_formation"),
                team_a_confidence=fm.get("team_a_confidence"),
                team_a_method=fm.get("team_a_method"),
                team_b_formation=fm.get("team_b_formation"),
                team_b_confidence=fm.get("team_b_confidence"),
                team_b_method=fm.get("team_b_method"),
                visualizations=[VisualizationData(**v) for v in fm["visualizations"]],
            ),
            roles=RolesResponse(
                success=True,
                team_a_roles=[PlayerRoleItem(**r) for r in ro["team_a_roles"]],
                team_b_roles=[PlayerRoleItem(**r) for r in ro["team_b_roles"]],
                visualizations=[VisualizationData(**v) for v in ro["visualizations"]],
            ),
            pass_network=_pn_response(pn) if pn else None,
            space_control=_sc_response(sc) if sc else None,
            visualizations=[VisualizationData(**v) for v in all_visuals],
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        cleanup(dataset_path)


# ── Helpers ───────────────────────────────────────────────────────


def _build_full_response(result: dict, req, match_info: dict) -> FullAnalysisResponse:
    fm = result["formation"]
    sc = result["space_control"]
    pn = result["pass_network"]
    pr = result["press_resistance"]
    pt = result["patterns"]
    ro = result["roles"]
    swot_raw = result.get("swot", {})
    recs_raw = result.get("recommendations", [])
    explanation_text = result.get("explanation", "")

    swot_items = []
    for cat in ("strengths", "weaknesses", "opportunities", "threats"):
        for entry in swot_raw.get(cat, []):
            if isinstance(entry, dict):
                swot_items.append(SWOTItem(
                    category=cat,
                    description=entry.get("description", str(entry)),
                    confidence=entry.get("confidence", 0.7),
                    source=entry.get("action", entry.get("source", "")),
                ))
            else:
                swot_items.append(SWOTItem(category=cat, description=str(entry), confidence=0.7))

    rec_items = [
        RecommendationItem(
            priority=r.get("priority", "medium"),
            category=r.get("category", ""),
            description=r.get("description", ""),
            reasoning=r.get("reasoning", ""),
            expected_impact=r.get("expected_impact", ""),
        )
        for r in recs_raw
    ]

    sections = [s.strip() for s in explanation_text.split("\n\n") if s.strip()]

    all_visuals = [VisualizationData(**v) for v in result.get("visualizations", [])]

    return FullAnalysisResponse(
        success=True,
        match_info=match_info,
        formation=FormationResponse(
            success=True,
            team_a_formation=fm.get("team_a_formation"),
            team_a_confidence=fm.get("team_a_confidence"),
            team_a_method=fm.get("team_a_method"),
            team_b_formation=fm.get("team_b_formation"),
            team_b_confidence=fm.get("team_b_confidence"),
            team_b_method=fm.get("team_b_method"),
            visualizations=[VisualizationData(**v) for v in fm["visualizations"]],
        ),
        space_control=SpaceControlResponse(
            success=True,
            team_a_control=sc["team_a_control"],
            team_b_control=sc["team_b_control"],
            zones=sc["zones"],
            midfield_control=sc["midfield_control"],
            visualizations=[VisualizationData(**v) for v in sc["visualizations"]],
        ),
        pass_network=_pn_response(pn),
        press_resistance=PressResistanceResponse(
            success=True,
            press_resistance_score=pr["press_resistance_score"],
            total_passes=pr["total_passes"],
            passes_under_pressure=pr["passes_under_pressure"],
            pass_success_overall=pr["pass_success_overall"],
            pass_success_under_pressure=pr["pass_success_under_pressure"],
            escape_rate=pr["escape_rate"],
            vulnerable_zones=pr["vulnerable_zones"],
            visualizations=[VisualizationData(**v) for v in pr["visualizations"]],
        ),
        patterns=PatternsResponse(
            success=True,
            team_a_patterns=[PatternItem(**p) for p in pt["team_a_patterns"]],
            team_b_patterns=[PatternItem(**p) for p in pt["team_b_patterns"]],
            visualizations=[VisualizationData(**v) for v in pt["visualizations"]],
        ),
        roles=RolesResponse(
            success=True,
            team_a_roles=[PlayerRoleItem(**r) for r in ro["team_a_roles"]],
            team_b_roles=[PlayerRoleItem(**r) for r in ro["team_b_roles"]],
            visualizations=[VisualizationData(**v) for v in ro["visualizations"]],
        ),
        intelligence=IntelligenceResponse(
            success=True,
            swot=swot_items,
            recommendations=rec_items,
        ),
        explanation=ExplanationResponse(
            success=True,
            mode="template",
            text=explanation_text,
            sections=sections,
        ),
        visualizations=all_visuals,
    )


def _pn_response(pn: dict) -> PassNetworkResponse:
    return PassNetworkResponse(
        success=True,
        total_passes=pn["total_passes"],
        key_distributor=pn["key_distributor"],
        most_involved=pn["most_involved"],
        top_connections=pn["top_connections"],
        weak_links=pn["weak_links"],
        centrality=pn["centrality"],
        visualizations=[VisualizationData(**v) for v in pn["visualizations"]],
    )


def _sc_response(sc: dict) -> SpaceControlResponse:
    return SpaceControlResponse(
        success=True,
        team_a_control=sc["team_a_control"],
        team_b_control=sc["team_b_control"],
        zones=sc["zones"],
        midfield_control=sc["midfield_control"],
        visualizations=[VisualizationData(**v) for v in sc["visualizations"]],
    )
