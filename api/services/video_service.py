"""
SpaceAI FC - Video Service
============================
Handles video upload processing and YouTube download.
Falls back to synthetic demo data if Phase 4 dependencies are absent.
"""

from pathlib import Path

# Phase 4 optional imports
HAS_VIDEO = False
try:
    from engine.perception.video_analyzer import VideoAnalyzer
    HAS_VIDEO = True
except ImportError:
    pass


def process_video_file(video_path: str) -> dict:
    """
    Process a local video file and extract player tracking data.

    Returns a dict with 'team_a', 'team_b', 'frames_processed', 'method'.
    Falls back to synthetic data if VideoAnalyzer is unavailable.
    """
    if not HAS_VIDEO:
        return _synthetic_tracking("synthetic_no_deps")

    try:
        va = VideoAnalyzer()
        tracking = va.analyze(str(video_path))
        return _normalise_tracking(tracking, method="yolo")
    except Exception as exc:
        return _synthetic_tracking(f"synthetic_error: {exc}")


def process_youtube_url(url: str, demo_mode: bool = False) -> dict:
    """
    Download and process a YouTube clip, or return synthetic data in demo mode.
    """
    if demo_mode or not HAS_VIDEO:
        return _synthetic_tracking("synthetic_demo")

    try:
        va = VideoAnalyzer()
        tracking = va.analyze_youtube(url)
        return _normalise_tracking(tracking, method="yolo")
    except Exception as exc:
        return _synthetic_tracking(f"synthetic_error: {exc}")


def track_player(video_data: dict, player_id: int) -> dict:
    """
    Extract individual player trajectory from tracking data.

    Returns trajectory list, total distance, avg speed.
    """
    all_positions = []
    for frame in video_data.get("frames", []):
        for player in frame.get("players", []):
            if player.get("id") == player_id:
                all_positions.append({"x": player["x"], "y": player["y"],
                                      "frame": frame.get("frame_idx", 0)})

    if not all_positions:
        return {
            "player_id": player_id,
            "trajectory": [],
            "total_distance": 0.0,
            "avg_speed": 0.0,
            "heatmap_base64": None,
        }

    import numpy as np
    coords = np.array([[p["x"], p["y"]] for p in all_positions])
    diffs = np.diff(coords, axis=0)
    distances = np.linalg.norm(diffs, axis=1)
    total_distance = float(np.sum(distances))
    avg_speed = float(np.mean(distances)) if len(distances) > 0 else 0.0

    # Simple heatmap via matplotlib
    heatmap_b64 = None
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from api.utils.image_encoder import fig_to_base64

        fig, ax = plt.subplots(figsize=(10, 7))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#1a1a2e")
        ax.set_xlim(0, 120)
        ax.set_ylim(0, 80)

        xs = [p["x"] for p in all_positions]
        ys = [p["y"] for p in all_positions]

        ax.scatter(xs, ys, c="#e74c3c", alpha=0.3, s=15)
        ax.plot(xs, ys, color="#e74c3c", alpha=0.5, linewidth=0.8)
        ax.set_title(f"Player {player_id} — Trajectory", color="white")

        heatmap_b64 = fig_to_base64(fig)
    except Exception:
        pass

    return {
        "player_id": player_id,
        "trajectory": all_positions,
        "total_distance": round(total_distance, 2),
        "avg_speed": round(avg_speed, 4),
        "heatmap_base64": heatmap_b64,
    }


# ── Internal helpers ──────────────────────────────────────────────

def _normalise_tracking(tracking: dict, method: str = "yolo") -> dict:
    """Normalise VideoAnalyzer output to our internal format."""
    team_a = tracking.get("team_a", [])
    team_b = tracking.get("team_b", [])
    frames = tracking.get("frames_processed", 0)

    return {
        "team_a": team_a,
        "team_b": team_b,
        "frames": tracking.get("frames", []),
        "frames_processed": frames,
        "method": method,
    }


def _synthetic_tracking(method: str) -> dict:
    """Generate synthetic El Clásico tracking data for demo/fallback."""
    team_a = [
        {"name": "ter Stegen",  "number": 1,  "x": 5,   "y": 40, "position": "GK"},
        {"name": "Koundé",      "number": 23, "x": 30,  "y": 70, "position": "RB"},
        {"name": "Araújo",      "number": 4,  "x": 25,  "y": 52, "position": "CB"},
        {"name": "Cubarsí",     "number": 2,  "x": 25,  "y": 28, "position": "CB"},
        {"name": "Baldé",       "number": 3,  "x": 30,  "y": 10, "position": "LB"},
        {"name": "Pedri",       "number": 8,  "x": 45,  "y": 48, "position": "CM"},
        {"name": "De Jong",     "number": 21, "x": 45,  "y": 32, "position": "CM"},
        {"name": "Lamine",      "number": 19, "x": 65,  "y": 68, "position": "RW"},
        {"name": "Gavi",        "number": 6,  "x": 60,  "y": 40, "position": "CAM"},
        {"name": "Raphinha",    "number": 11, "x": 65,  "y": 12, "position": "LW"},
        {"name": "Lewandowski", "number": 9,  "x": 80,  "y": 40, "position": "ST"},
    ]
    team_b = [
        {"name": "Courtois",   "number": 1,  "x": 115, "y": 40, "position": "GK"},
        {"name": "Carvajal",   "number": 2,  "x": 90,  "y": 70, "position": "RB"},
        {"name": "Rüdiger",    "number": 22, "x": 93,  "y": 52, "position": "CB"},
        {"name": "Militão",    "number": 3,  "x": 93,  "y": 28, "position": "CB"},
        {"name": "Mendy",      "number": 23, "x": 90,  "y": 10, "position": "LB"},
        {"name": "Tchouaméni", "number": 14, "x": 78,  "y": 40, "position": "CDM"},
        {"name": "Valverde",   "number": 15, "x": 70,  "y": 55, "position": "CM"},
        {"name": "Bellingham", "number": 5,  "x": 70,  "y": 25, "position": "CM"},
        {"name": "Rodrygo",    "number": 11, "x": 55,  "y": 65, "position": "RW"},
        {"name": "Mbappé",     "number": 7,  "x": 50,  "y": 40, "position": "ST"},
        {"name": "Vinícius",   "number": 20, "x": 55,  "y": 15, "position": "LW"},
    ]
    return {
        "team_a": team_a,
        "team_b": team_b,
        "frames": [],
        "frames_processed": 0,
        "method": method,
    }
