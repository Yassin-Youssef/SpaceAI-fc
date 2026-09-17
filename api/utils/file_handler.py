"""
SpaceAI FC - File Handler
===========================
Validate, save, parse and clean up uploaded files.

Dataset formats
---------------
JSON (SpaceAI FC format):
    {
      "team_a": [{"name": "...", "number": 1, "x": 5, "y": 40, "position": "GK"}, ...],
      "team_b": [...],
      "passes": [{"passer": 1, "receiver": 4, "success": true, "x": 5, "y": 40, "end_x": 25, "end_y": 52}],
      "match_info": {"home_team": "...", "away_team": "...", ...}
    }
    Aliases accepted: home_team_players / away_team_players, pass_events,
    or a flat "players" array where each player has a "team" field.

CSV (flat):
    team,name,number,x,y,position
    a,ter Stegen,1,5,40,GK
    b,Courtois,1,115,40,GK
    Optional pass rows use a "type" column:
    type,team,name,number,x,y,position,passer,receiver,success,end_x,end_y
    pass,a,,,5,40,,1,4,1,25,52
"""

import csv
import json
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile

from api.config import (
    TEMP_DIR,
    MAX_VIDEO_SIZE_BYTES,
    MAX_DATASET_SIZE_BYTES,
    ALLOWED_VIDEO_EXTENSIONS,
    ALLOWED_DATASET_EXTENSIONS,
)


class DatasetParseError(ValueError):
    """Raised when a dataset file cannot be interpreted."""


def _unique_path(ext: str) -> Path:
    return TEMP_DIR / f"{uuid.uuid4().hex}{ext}"


async def save_video_upload(file: UploadFile) -> Path:
    """Validate and save a video upload to the temp directory."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid video format '{ext or 'none'}'. Allowed: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}",
        )

    dest = _unique_path(ext)
    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded video is empty.")
    if len(contents) > MAX_VIDEO_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Video file exceeds {MAX_VIDEO_SIZE_BYTES // (1024*1024)} MB limit.",
        )

    dest.write_bytes(contents)
    return dest


async def save_dataset_upload(file: UploadFile) -> Path:
    """Validate and save a dataset upload (CSV or JSON) to temp."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_DATASET_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dataset format '{ext or 'none'}'. Allowed: {', '.join(sorted(ALLOWED_DATASET_EXTENSIONS))}",
        )

    dest = _unique_path(ext)
    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded dataset is empty.")
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


# ── Dataset parsing ───────────────────────────────────────────────

def parse_dataset(path: Path) -> dict:
    """
    Parse a CSV or JSON dataset file into a dict with keys:
        'team_a', 'team_b', 'passes', 'match_info', 'format'

    Raises DatasetParseError with a helpful message on malformed input.
    """
    ext = path.suffix.lower()
    try:
        if ext == ".json":
            text = path.read_text(encoding="utf-8-sig")
            data = json.loads(text)
            result = _normalise_dataset(data)
            result["format"] = "json"
            return result
        if ext == ".csv":
            with open(path, newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
            result = _normalise_csv(rows)
            result["format"] = "csv"
            return result
    except DatasetParseError:
        raise
    except json.JSONDecodeError as exc:
        raise DatasetParseError(f"Invalid JSON: {exc.msg} (line {exc.lineno}).")
    except (ValueError, KeyError, TypeError) as exc:
        raise DatasetParseError(f"Could not parse dataset: {exc}")
    raise DatasetParseError(f"Unsupported dataset extension '{ext}'.")


def _to_float(value, default=0.0) -> float:
    if value is None or value == "":
        return float(default)
    return float(value)


def _to_int(value, default=0) -> int:
    if value is None or value == "":
        return int(default)
    return int(float(value))


def _to_bool(value, default=True) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "y", "t", "success")


def _normalise_player(raw: dict, index: int) -> dict:
    x = _to_float(raw.get("x"), 60)
    y = _to_float(raw.get("y"), 40)
    if not (0 <= x <= 120) or not (0 <= y <= 80):
        raise DatasetParseError(
            f"Player '{raw.get('name', index)}' has coordinates ({x}, {y}) outside the pitch "
            "(x 0-120, y 0-80)."
        )
    return {
        "name": str(raw.get("name") or f"Player {index}"),
        "number": _to_int(raw.get("number") or raw.get("jersey") or raw.get("shirt"), index),
        "x": x,
        "y": y,
        "position": str(raw.get("position") or raw.get("pos") or "CM").upper(),
    }


def _normalise_pass(raw: dict) -> dict:
    return {
        "passer": _to_int(raw.get("passer") or raw.get("from")),
        "receiver": _to_int(raw.get("receiver") or raw.get("to")),
        "success": _to_bool(raw.get("success")),
        "x": _to_float(raw.get("x"), 0),
        "y": _to_float(raw.get("y"), 0),
        "end_x": _to_float(raw.get("end_x"), 0),
        "end_y": _to_float(raw.get("end_y"), 0),
    }


def _team_key(value) -> str:
    v = str(value or "a").strip().lower()
    if v in ("a", "home", "1", "team_a", "team a", "left"):
        return "a"
    if v in ("b", "away", "2", "team_b", "team b", "right"):
        return "b"
    return v


def _normalise_dataset(data) -> dict:
    """Normalise a JSON dataset to the internal format."""
    if isinstance(data, list):
        # A bare list is treated as a flat player list with a "team" field
        data = {"players": data}
    if not isinstance(data, dict):
        raise DatasetParseError("JSON root must be an object with team_a / team_b keys.")

    team_a_raw = data.get("team_a") or data.get("home_team_players") or data.get("home") or []
    team_b_raw = data.get("team_b") or data.get("away_team_players") or data.get("away") or []

    if not team_a_raw and not team_b_raw and data.get("players"):
        for i, p in enumerate(data["players"]):
            (team_a_raw if _team_key(p.get("team")) == "a" else team_b_raw).append(p)

    team_a = [_normalise_player(p, i + 1) for i, p in enumerate(team_a_raw)]
    team_b = [_normalise_player(p, i + 1) for i, p in enumerate(team_b_raw)]
    passes = [_normalise_pass(p) for p in (data.get("passes") or data.get("pass_events") or [])]

    if not team_a and not team_b:
        raise DatasetParseError(
            "No players found. Expected 'team_a' and 'team_b' arrays "
            "(or a 'players' array with a 'team' field)."
        )

    return {
        "team_a": team_a,
        "team_b": team_b,
        "passes": passes,
        "match_info": data.get("match_info", {}) or {},
    }


def _normalise_csv(rows: list) -> dict:
    """Parse a flat CSV of players (and optional pass rows)."""
    if not rows:
        raise DatasetParseError("CSV file has no data rows.")

    headers = {h.strip().lower() for h in rows[0].keys() if h}
    if not {"x", "y"} <= headers:
        raise DatasetParseError(
            "CSV must include at least 'x' and 'y' columns "
            "(recommended: team,name,number,x,y,position)."
        )

    team_a, team_b, passes = [], [], []
    for i, raw in enumerate(rows, start=1):
        row = {(k or "").strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in raw.items()}
        row_type = (row.get("type") or "player").lower()
        if row_type == "pass":
            passes.append(_normalise_pass(row))
            continue
        if not any(row.get(k) for k in ("name", "number", "x", "y")):
            continue  # skip blank lines
        player = _normalise_player(row, i)
        if _team_key(row.get("team")) == "b":
            team_b.append(player)
        else:
            team_a.append(player)

    if not team_a and not team_b:
        raise DatasetParseError("CSV parsed but contained no player rows.")

    return {"team_a": team_a, "team_b": team_b, "passes": passes, "match_info": {}}
