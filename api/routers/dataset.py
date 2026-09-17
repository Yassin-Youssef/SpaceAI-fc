"""
SpaceAI FC - Dataset Router
  POST /api/dataset/upload
  GET  /api/dataset/template/{fmt}

Uploads are parsed immediately and the normalised players / passes are
returned to the client, which then submits them as manual coordinates to
any analysis endpoint.  Nothing is kept on the server.
"""

import csv
import io
import json

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse, JSONResponse

from api.models.responses import DatasetResponse
from api.utils.file_handler import (
    save_dataset_upload, parse_dataset, cleanup, DatasetParseError,
)

router = APIRouter(prefix="/api/dataset", tags=["Dataset"])


# El Clásico sample used for downloadable templates
_TEMPLATE_TEAM_A = [
    ("ter Stegen", 1, 5, 40, "GK"), ("Koundé", 23, 30, 70, "RB"), ("Araújo", 4, 25, 52, "CB"),
    ("Cubarsí", 2, 25, 28, "CB"), ("Baldé", 3, 30, 10, "LB"), ("Pedri", 8, 45, 48, "CM"),
    ("De Jong", 21, 45, 32, "CM"), ("Lamine", 19, 65, 68, "RW"), ("Gavi", 6, 60, 40, "CAM"),
    ("Raphinha", 11, 65, 12, "LW"), ("Lewandowski", 9, 80, 40, "ST"),
]
_TEMPLATE_TEAM_B = [
    ("Courtois", 1, 115, 40, "GK"), ("Carvajal", 2, 90, 70, "RB"), ("Rüdiger", 22, 93, 52, "CB"),
    ("Militão", 3, 93, 28, "CB"), ("Mendy", 23, 90, 10, "LB"), ("Tchouaméni", 14, 78, 40, "CDM"),
    ("Valverde", 15, 70, 55, "CM"), ("Bellingham", 5, 70, 25, "CM"), ("Rodrygo", 11, 55, 65, "RW"),
    ("Mbappé", 7, 50, 40, "ST"), ("Vinícius", 20, 55, 15, "LW"),
]
_TEMPLATE_PASSES = [
    (1, 4, 1, 5, 40, 25, 52), (4, 8, 1, 25, 52, 45, 48), (8, 6, 1, 45, 48, 60, 40),
    (6, 9, 1, 60, 40, 80, 40), (23, 19, 1, 30, 70, 65, 68), (19, 9, 0, 65, 68, 80, 40),
    (21, 8, 1, 45, 32, 45, 48), (8, 11, 1, 45, 48, 65, 12), (11, 9, 1, 65, 12, 80, 40),
    (9, 6, 1, 80, 40, 60, 40),
]


@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload a CSV or JSON dataset (max 50 MB) and receive normalised
    team_a / team_b / passes ready for any analysis endpoint.
    """
    saved_path = None
    try:
        saved_path = await save_dataset_upload(file)
        data = parse_dataset(saved_path)
        n_a, n_b, n_p = len(data["team_a"]), len(data["team_b"]), len(data["passes"])
        return DatasetResponse(
            success=True,
            team_a=data["team_a"],
            team_b=data["team_b"],
            passes=data["passes"],
            match_info=data.get("match_info", {}),
            format=data.get("format", ""),
            message=f"Parsed {n_a} + {n_b} players and {n_p} passes from {file.filename}.",
        )
    except DatasetParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Dataset upload failed: {exc}")
    finally:
        cleanup(saved_path)


@router.get("/template/{fmt}")
async def dataset_template(fmt: str):
    """Download a sample dataset in CSV or JSON format."""
    fmt = fmt.lower()
    if fmt == "json":
        payload = {
            "match_info": {
                "home_team": "FC Barcelona", "away_team": "Real Madrid",
                "score_home": 2, "score_away": 1, "minute": 65,
                "competition": "La Liga",
            },
            "team_a": [dict(name=n, number=num, x=x, y=y, position=p) for n, num, x, y, p in _TEMPLATE_TEAM_A],
            "team_b": [dict(name=n, number=num, x=x, y=y, position=p) for n, num, x, y, p in _TEMPLATE_TEAM_B],
            "passes": [
                dict(passer=a, receiver=b, success=bool(s), x=x, y=y, end_x=ex, end_y=ey)
                for a, b, s, x, y, ex, ey in _TEMPLATE_PASSES
            ],
        }
        return JSONResponse(
            content=payload,
            headers={"Content-Disposition": 'attachment; filename="spaceai_dataset_template.json"'},
        )

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["type", "team", "name", "number", "x", "y", "position", "passer", "receiver", "success", "end_x", "end_y"])
        for n, num, x, y, p in _TEMPLATE_TEAM_A:
            writer.writerow(["player", "a", n, num, x, y, p, "", "", "", "", ""])
        for n, num, x, y, p in _TEMPLATE_TEAM_B:
            writer.writerow(["player", "b", n, num, x, y, p, "", "", "", "", ""])
        for a, b, s, x, y, ex, ey in _TEMPLATE_PASSES:
            writer.writerow(["pass", "a", "", "", x, y, "", a, b, s, ex, ey])
        return PlainTextResponse(
            buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="spaceai_dataset_template.csv"'},
        )

    raise HTTPException(status_code=404, detail="Template format must be 'csv' or 'json'.")
