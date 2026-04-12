"""
SpaceAI FC - File Handler
===========================
Validate, save, and clean up uploaded files.
"""

import os
import uuid
import json
import csv
from pathlib import Path
from fastapi import HTTPException, UploadFile

from api.config import (
    TEMP_DIR,
    MAX_VIDEO_SIZE_BYTES,
    MAX_DATASET_SIZE_BYTES,
    ALLOWED_VIDEO_EXTENSIONS,
    ALLOWED_DATASET_EXTENSIONS,
)


def _unique_path(ext: str) -> Path:
    return TEMP_DIR / f"{uuid.uuid4().hex}{ext}"


async def save_video_upload(file: UploadFile) -> Path:
    """
    Validate and save a video upload to the temp directory.

    Returns the saved path.
    Raises HTTPException on validation failure.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid video format '{ext}'. Allowed: {sorted(ALLOWED_VIDEO_EXTENSIONS)}",
        )

    dest = _unique_path(ext)
    contents = await file.read()

    if len(contents) > MAX_VIDEO_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Video file exceeds {MAX_VIDEO_SIZE_BYTES // (1024*1024)} MB limit.",
        )

    dest.write_bytes(contents)
    return dest


async def save_dataset_upload(file: UploadFile) -> Path:
    """
    Validate and save a dataset upload (CSV or JSON) to temp.

    Returns the saved path.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_DATASET_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dataset format '{ext}'. Allowed: {sorted(ALLOWED_DATASET_EXTENSIONS)}",
        )

    dest = _unique_path(ext)
    contents = await file.read()

    if len(contents) > MAX_DATASET_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Dataset exceeds {MAX_DATASET_SIZE_BYTES // (1024*1024)} MB limit.",
        )

    dest.write_bytes(contents)
    return dest


def cleanup(path) -> None:
    """Delete a temp file, silently ignoring missing files."""
    try:
        if path and Path(path).exists():
            Path(path).unlink()
    except OSError:
        pass


def parse_dataset(path: Path) -> dict:
    """
    Parse a CSV or JSON dataset file into a dict with keys:
        'team_a', 'team_b', 'passes', 'match_info'

    Supports StatsBomb-lite format and the custom SpaceAI FC format.
    Returns empty structures on any parse error.
    """
    ext = path.suffix.lower()
    try:
        if ext == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            return _normalise_dataset(data)
        elif ext == ".csv":
            rows = []
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
            return _normalise_csv(rows)
    except Exception:
        pass
    return {"team_a": [], "team_b": [], "passes": [], "match_info": {}}


def _normalise_dataset(data: dict) -> dict:
    """Normalise a JSON dataset to the internal format."""
    result = {
        "team_a": data.get("team_a", data.get("home_team_players", [])),
        "team_b": data.get("team_b", data.get("away_team_players", [])),
        "passes": data.get("passes", data.get("pass_events", [])),
        "match_info": data.get("match_info", {}),
    }
    return result


def _normalise_csv(rows: list) -> dict:
    """
    Attempt to parse a flat CSV with columns:
    team, name, number, x, y, position
    """
    team_a, team_b = [], []
    for row in rows:
        player = {
            "name": row.get("name", "Player"),
            "number": int(row.get("number", 0)),
            "x": float(row.get("x", 60)),
            "y": float(row.get("y", 40)),
            "position": row.get("position", "CM"),
        }
        team = row.get("team", "a").lower()
        if team in ("a", "home", "1"):
            team_a.append(player)
        else:
            team_b.append(player)
    return {"team_a": team_a, "team_b": team_b, "passes": [], "match_info": {}}
