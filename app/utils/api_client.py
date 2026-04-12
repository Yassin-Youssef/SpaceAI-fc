"""
SpaceAI FC - API Client
========================
Functions to call the FastAPI backend.
All calls are synchronous (requests library).
"""

import base64
from io import BytesIO

import requests
from PIL import Image

API_BASE = "http://127.0.0.1:8000/api"
TIMEOUT = 120  # seconds


# ── Image helpers ─────────────────────────────────────────────────

def base64_to_image(b64_string: str) -> Image.Image:
    """Convert a base64 PNG string to a PIL Image for st.image()."""
    img_bytes = base64.b64decode(b64_string)
    return Image.open(BytesIO(img_bytes))


def _post(endpoint: str, data: dict) -> dict:
    """POST JSON to the API. Returns parsed response or an error dict."""
    try:
        resp = requests.post(f"{API_BASE}/{endpoint}", json=data, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": (
            "Cannot connect to the SpaceAI FC engine. "
            "Please start the API server:\n\n"
            "    uvicorn api.main:app --reload --port 8000"
        )}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out. The analysis is taking too long."}
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return {"success": False, "error": f"API error: {detail}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── API calls ─────────────────────────────────────────────────────

def analyze_full_match(data: dict) -> dict:
    return _post("analyze", data)


def analyze_tactical(data: dict) -> dict:
    return _post("tactical-analysis", data)


def analyze_pass_network(data: dict) -> dict:
    return _post("pass-network", data)


def analyze_space_control(data: dict) -> dict:
    return _post("space-control", data)


def analyze_formation(data: dict) -> dict:
    return _post("formation", data)


def analyze_roles(data: dict) -> dict:
    return _post("roles", data)


def analyze_press_resistance(data: dict) -> dict:
    return _post("press-resistance", data)


def analyze_patterns(data: dict) -> dict:
    return _post("patterns", data)


def query_knowledge_graph(data: dict) -> dict:
    return _post("knowledge-graph", data)


def run_reasoning(data: dict) -> dict:
    return _post("reasoning", data)


def get_recommendations(data: dict) -> dict:
    return _post("recommendations", data)


def get_explanation(data: dict) -> dict:
    return _post("explanation", data)


def ask_spaceai(data: dict) -> dict:
    return _post("ask", data)


def upload_video(file_bytes: bytes, filename: str) -> dict:
    """Upload a video file using multipart form data."""
    try:
        resp = requests.post(
            f"{API_BASE}/video/upload",
            files={"file": (filename, file_bytes)},
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Cannot connect to the API."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def process_youtube(url: str, demo_mode: bool = False) -> dict:
    return _post("video/youtube", {"url": url, "demo_mode": demo_mode})


def run_simulation(data: dict) -> dict:
    return _post("simulation/run", data)


def export_docx(data: dict) -> bytes | None:
    """Download a Word document export. Returns raw bytes or None on error."""
    try:
        resp = requests.post(f"{API_BASE}/export/docx", json=data, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None


def health_check() -> dict:
    """Check if the API is reachable."""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        return resp.json()
    except Exception:
        return {"status": "offline"}


# ── Request builders ──────────────────────────────────────────────

def build_base_request(
    team_a: list,
    team_b: list,
    passes: list,
    team_a_name: str = "Team A",
    team_b_name: str = "Team B",
    team_a_color: str = "#a50044",
    team_b_color: str = "#ffffff",
    ball_x: float = 60.0,
    ball_y: float = 40.0,
    match_info: dict = None,
    input_type: str = "manual",
) -> dict:
    """Build the standard analysis request body."""
    body = {
        "input_type": input_type,
        "team_a": team_a,
        "team_b": team_b,
        "passes": passes,
        "team_a_name": team_a_name,
        "team_b_name": team_b_name,
        "team_a_color": team_a_color,
        "team_b_color": team_b_color,
        "ball_x": ball_x,
        "ball_y": ball_y,
    }
    if match_info:
        body["match_info"] = match_info
    return body
