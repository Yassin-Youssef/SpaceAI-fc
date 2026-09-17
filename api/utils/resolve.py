"""
SpaceAI FC - Input Resolver
=============================
Single integration point between the three input methods
(manual / video / dataset) and the analysis engine.

Every analysis router calls `resolve_input(req)` and receives plain
`(team_a, team_b, passes)` lists regardless of where the data came from.
"""

from pathlib import Path
from fastapi import HTTPException

from api.utils.file_handler import parse_dataset
from api.services import video_service


def resolve_input(req):
    """
    Resolve request data into engine-ready lists.

    Priority:
        1. dataset  — `dataset_file` path (populated by /api/dataset/upload)
        2. video    — `video_file` path or `youtube_url` (Phase 4 CV, with fallback)
        3. manual   — `team_a` / `team_b` / `passes` supplied directly

    If the declared input_type has no matching payload but manual coordinates
    are present (e.g. the frontend already uploaded the video and injected the
    tracked positions), the manual data is used.

    Returns:
        tuple: (team_a: list, team_b: list, passes: list)
    """
    input_type = getattr(req, "input_type", "manual") or "manual"
    dataset_file = getattr(req, "dataset_file", None)
    video_file = getattr(req, "video_file", None)
    youtube_url = getattr(req, "youtube_url", None)

    # 1. Dataset file already saved on disk
    if input_type == "dataset" and dataset_file:
        path = Path(dataset_file)
        if not path.exists():
            raise HTTPException(status_code=400, detail="Dataset file not found on server.")
        data = parse_dataset(path)
        if not data.get("team_a") and not data.get("team_b"):
            raise HTTPException(
                status_code=400,
                detail="Dataset parsed but contained no players. "
                       "Expected CSV columns team,name,number,x,y,position or JSON with team_a/team_b.",
            )
        return data.get("team_a", []), data.get("team_b", []), data.get("passes", [])

    # 2. Video / YouTube — Phase 4 computer vision
    if input_type == "video" and (video_file or youtube_url):
        try:
            if youtube_url:
                tracking = video_service.process_youtube_url(youtube_url)
            else:
                tracking = video_service.process_video_file(video_file)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Video analysis failed: {exc}")

        team_a = tracking.get("team_a", [])
        team_b = tracking.get("team_b", [])
        if not team_a and not team_b:
            raise HTTPException(status_code=400, detail="No players detected in video.")
        return team_a, team_b, []

    # 3. Manual coordinates (also used after client-side video/dataset upload)
    team_a = [_dump(p) for p in getattr(req, "team_a", None) or []]
    team_b = [_dump(p) for p in getattr(req, "team_b", None) or []]
    passes = [_dump(p) for p in getattr(req, "passes", None) or []]

    return team_a, team_b, passes


def _dump(item):
    """Accept both Pydantic models and plain dicts."""
    if hasattr(item, "model_dump"):
        return item.model_dump()
    return dict(item)
