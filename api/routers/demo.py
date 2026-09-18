"""
SpaceAI FC - Demo Matches Router
  GET /api/demo/matches          → list of bundled fixtures
  GET /api/demo/matches/{id}     → full fixture (players, passes, match info)
  GET /api/demo/players          → player stat lines for Player Assessment
  GET /api/demo/video            → bundled sample clip metadata
  POST /api/demo/video/analyze   → run the sample clip through the CV pipeline

Fixtures live in data/demo_matches/*.json and are built by
scripts/build_demo_matches.py from StatsBomb open data (plus two
reconstructed line-ups).  They are read once and cached in memory.
"""

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.config import BASE_DIR
from api.models.responses import VideoResponse, VideoTrackingData
from api.services import video_service

router = APIRouter(prefix="/api/demo", tags=["Demo"])

DEMO_DIR = BASE_DIR / "data" / "demo_matches"


@lru_cache(maxsize=1)
def _index() -> list:
    path = DEMO_DIR / "index.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


@lru_cache(maxsize=32)
def _match(match_id: str) -> dict | None:
    safe = "".join(c for c in match_id if c.isalnum() or c in "-_")
    path = DEMO_DIR / f"{safe}.json"
    if safe != match_id or not path.exists() or safe == "index":
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


@lru_cache(maxsize=1)
def _players() -> list:
    path = DEMO_DIR / "players.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


@router.get("/players")
async def list_demo_players():
    """Real player stat lines (from the demo fixtures) for Player Assessment."""
    return {"total": len(_players()), "players": _players()}


# ── Sample video clip ─────────────────────────────────────────────

VIDEO_PATH = BASE_DIR / "data" / "demo_video" / "corner_kick.mp4"
VIDEO_META = {
    "title": "FC Utrecht corner kick",
    "subtitle": "FC Utrecht v SC Heerenveen, play-off, 17 May 2013",
    "author": "Pel Laurens",
    "license": "CC BY 3.0",
    "source_url": "https://commons.wikimedia.org/wiki/File:FC_Utrecht_takes_a_Corner.ogv",
    "duration_s": 14,
    "resolution": "576x576",
    "note": (
        "Detection and tracking work well here (10-15 players a frame). Team "
        "assignment is approximate: this is a zoomed corner, so the white shirts "
        "dominate and the smaller group includes the referee."
    ),
}

_video_cache = None


@router.get("/video")
async def demo_video_info():
    """Metadata for the bundled sample clip."""
    return {"available": VIDEO_PATH.exists(), **VIDEO_META}


@router.post("/video/analyze", response_model=VideoResponse)
async def demo_video_analyze():
    """Run the bundled sample clip through the real CV pipeline (cached)."""
    global _video_cache
    if not VIDEO_PATH.exists():
        raise HTTPException(status_code=404, detail="Sample clip is not bundled with this install.")
    if _video_cache is None:
        tracking = video_service.process_video_file(str(VIDEO_PATH))
        _video_cache = VideoResponse(
            success=True,
            tracking_data=VideoTrackingData(
                team_a=tracking["team_a"], team_b=tracking["team_b"],
                frames_processed=tracking["frames_processed"], method=tracking["method"],
            ),
            message=f"{VIDEO_META['title']} ({VIDEO_META['license']}, {VIDEO_META['author']}). "
                    + (tracking.get("message") or ""),
        )
    return _video_cache


@router.get("/matches")
async def list_demo_matches():
    """Summaries of every bundled demo fixture, in display order."""
    return {"total": len(_index()), "matches": _index()}


@router.get("/matches/{match_id}")
async def get_demo_match(match_id: str):
    """Full fixture data ready to feed any analysis endpoint."""
    match = _match(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Unknown demo match '{match_id}'.")
    return match
