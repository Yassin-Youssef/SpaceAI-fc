"""
SpaceAI FC - Demo Matches Router
  GET /api/demo/matches          → list of bundled fixtures
  GET /api/demo/matches/{id}     → full fixture (players, passes, match info)
  GET /api/demo/players          → player stat lines for Player Assessment

Fixtures live in data/demo_matches/*.json and are built by
scripts/build_demo_matches.py from StatsBomb open data (plus two
reconstructed line-ups).  They are read once and cached in memory.
"""

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.config import BASE_DIR

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
