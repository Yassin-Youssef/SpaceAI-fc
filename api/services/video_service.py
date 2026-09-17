"""
SpaceAI FC - Video Service
============================
Bridges Phase 4 (computer vision) to the Phase 1-3 analysis engine.

Pipeline:  video file / YouTube URL  →  VideoAnalyzer (YOLOv8 + tracking)
           →  per-frame pitch coordinates  →  robust team snapshot
           →  player dicts the engine understands (name, number, x, y, position)

When the optional CV dependencies (ultralytics, opencv-python, yt-dlp) are
missing, or when processing fails, the service falls back to the engine's
synthetic tracking generator so every downstream feature keeps working.
The `method` field always tells the caller which path was used.
"""

from pathlib import Path

import numpy as np

try:
    from engine.perception.video_analyzer import (
        VideoAnalyzer, HAS_CV2, HAS_YOLO, HAS_YTDLP,
    )
    HAS_VIDEO = True
except ImportError:  # pragma: no cover - engine always ships the module
    VideoAnalyzer = None
    HAS_CV2 = HAS_YOLO = HAS_YTDLP = False
    HAS_VIDEO = False


CV_AVAILABLE = bool(HAS_VIDEO and HAS_CV2 and HAS_YOLO)
YOUTUBE_AVAILABLE = bool(HAS_VIDEO and HAS_YTDLP)


def capabilities() -> dict:
    """Report which parts of the video pipeline are usable on this machine."""
    return {
        "opencv": bool(HAS_CV2),
        "yolo": bool(HAS_YOLO),
        "yt_dlp": bool(HAS_YTDLP),
        "cv_pipeline": CV_AVAILABLE,
    }


# ── Public API ────────────────────────────────────────────────────

def process_video_file(video_path: str, max_frames: int = 60) -> dict:
    """
    Process a local video file and extract a team snapshot.

    Returns a dict with 'team_a', 'team_b', 'frames', 'frames_processed',
    'method' and 'message'.
    """
    if not CV_AVAILABLE:
        return _synthetic_tracking(
            "synthetic",
            "Computer-vision dependencies (ultralytics, opencv-python) are not "
            "installed, so synthetic tracking data was used. "
            "Run `pip install ultralytics opencv-python` to enable real detection.",
        )

    analyzer = VideoAnalyzer()
    try:
        analyzer.load_video(str(video_path))
        tracking = analyzer.analyze_video(sample_rate=5, max_frames=max_frames)
        return _tracking_to_snapshot(tracking, method="yolo")
    except Exception as exc:
        return _synthetic_tracking(
            "synthetic",
            f"Video processing failed ({exc}); synthetic tracking data was used instead.",
        )
    finally:
        analyzer.cleanup()


def process_youtube_url(url: str, demo_mode: bool = False, max_frames: int = 60) -> dict:
    """
    Download and process a YouTube clip, or return synthetic data in demo mode.
    """
    import re
    if not re.match(r"^https?://(www\.|m\.)?(youtube\.com|youtu\.be)/", (url or "").strip()):
        raise ValueError("Invalid YouTube URL. Only youtube.com and youtu.be links are accepted.")

    if demo_mode:
        return _synthetic_tracking("synthetic", "Demo mode: synthetic tracking data.")

    if not YOUTUBE_AVAILABLE or not CV_AVAILABLE:
        missing = []
        if not YOUTUBE_AVAILABLE:
            missing.append("yt-dlp")
        if not CV_AVAILABLE:
            missing.append("ultralytics/opencv-python")
        return _synthetic_tracking(
            "synthetic",
            f"YouTube processing needs {', '.join(missing)} which is not installed; "
            "synthetic tracking data was used instead.",
        )

    analyzer = VideoAnalyzer()
    try:
        analyzer.download_youtube(url)
        tracking = analyzer.analyze_video(sample_rate=5, max_frames=max_frames)
        return _tracking_to_snapshot(tracking, method="yolo")
    except ValueError as exc:
        # Invalid URL — surface this to the caller rather than silently faking data
        raise
    except Exception as exc:
        return _synthetic_tracking(
            "synthetic",
            f"YouTube processing failed ({exc}); synthetic tracking data was used instead.",
        )
    finally:
        analyzer.cleanup()


def track_player(video_data: dict, player_id: int) -> dict:
    """
    Extract individual player trajectory from tracking data.

    Accepts frames in either the analyzer format ({team_a: [...], team_b: [...]})
    or a flat {players: [...]} format.
    Returns trajectory list, total distance, avg speed and a heat-map image.
    """
    all_positions = []
    for frame in video_data.get("frames", []):
        candidates = list(frame.get("players", []))
        candidates += frame.get("team_a", []) + frame.get("team_b", [])
        for player in candidates:
            if player.get("id") == player_id:
                all_positions.append({
                    "x": float(player["x"]),
                    "y": float(player["y"]),
                    "frame": frame.get("frame_idx", frame.get("frame", 0)),
                })

    if not all_positions:
        return {
            "player_id": player_id,
            "trajectory": [],
            "total_distance": 0.0,
            "avg_speed": 0.0,
            "heatmap_base64": None,
        }

    coords = np.array([[p["x"], p["y"]] for p in all_positions])
    diffs = np.diff(coords, axis=0)
    distances = np.linalg.norm(diffs, axis=1) if len(coords) > 1 else np.array([])
    total_distance = float(np.sum(distances)) if distances.size else 0.0
    avg_speed = float(np.mean(distances)) if distances.size else 0.0

    heatmap_b64 = None
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from api.utils.image_encoder import fig_to_base64

        fig, ax = plt.subplots(figsize=(10, 7))
        fig.patch.set_facecolor("#0a0e27")
        ax.set_facecolor("#0a0e27")
        ax.set_xlim(0, 120)
        ax.set_ylim(0, 80)
        xs = [p["x"] for p in all_positions]
        ys = [p["y"] for p in all_positions]
        ax.scatter(xs, ys, c="#00d9ff", alpha=0.35, s=18)
        ax.plot(xs, ys, color="#00d9ff", alpha=0.6, linewidth=0.9)
        ax.set_title(f"Player {player_id} — Trajectory", color="white")
        ax.tick_params(colors="#8892b0")
        for spine in ax.spines.values():
            spine.set_color("#1a2147")
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

_LEFT_LABELS = ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CAM", "LW", "ST", "RW"]


def _label_positions(players: list, attacking_right: bool) -> list:
    """
    Assign plausible position labels to anonymous tracked players so the
    role classifier and pattern detector have something to reason about.
    Players are ranked by depth (distance from own goal) and then by width.
    """
    if not players:
        return players

    ranked = sorted(players, key=lambda p: p["x"] if attacking_right else -p["x"])
    n = len(ranked)

    # Split into lines by depth: GK, defenders, midfielders, attackers
    if n >= 11:
        line_sizes = [1, 4, 3, n - 8]
    elif n >= 7:
        line_sizes = [1, 3, 2, n - 6]
    elif n >= 4:
        line_sizes = [1, 2, 1, n - 4]
    else:
        line_sizes = [1, n - 1, 0, 0]

    line_labels = [
        ["GK"],
        ["LB", "CB", "CB", "RB", "CB"],
        ["CM", "CDM", "CM", "CAM"],
        ["LW", "ST", "RW", "ST", "CF"],
    ]

    idx = 0
    labelled = []
    for size, labels in zip(line_sizes, line_labels):
        line = ranked[idx: idx + size]
        idx += size
        # Sort each line by width so left/right labels make sense
        line_sorted = sorted(line, key=lambda p: p["y"])
        for i, p in enumerate(line_sorted):
            p = dict(p)
            p["position"] = labels[min(i, len(labels) - 1)] if size > 1 else labels[0]
            labelled.append(p)
    return labelled


def _tracking_to_snapshot(tracking: dict, method: str = "yolo") -> dict:
    """
    Reduce multi-frame tracking output to one robust snapshot per team.

    For each track id we take the median position across all frames — this is
    far less noisy than a single frame and represents the player's average
    station in the observed period.
    """
    frames = tracking.get("frames", []) or []
    if not frames:
        return _synthetic_tracking("synthetic", "No frames were produced by the tracker.")

    def _median_positions(key: str) -> list:
        buckets: dict = {}
        for f in frames:
            for p in f.get(key, []):
                buckets.setdefault(p["id"], []).append((float(p["x"]), float(p["y"])))
        out = []
        for pid, pts in buckets.items():
            arr = np.array(pts)
            out.append({
                "name": f"Player {pid}",
                "number": int(pid),
                "x": float(np.clip(np.median(arr[:, 0]), 0, 120)),
                "y": float(np.clip(np.median(arr[:, 1]), 0, 80)),
                "position": "CM",
                "frames_seen": len(pts),
            })
        # Keep the 11 most consistently tracked players per team
        out.sort(key=lambda p: -p["frames_seen"])
        return out[:11]

    team_a = _median_positions("team_a")
    team_b = _median_positions("team_b")

    # Decide attacking direction from average x
    avg_a = np.mean([p["x"] for p in team_a]) if team_a else 30
    avg_b = np.mean([p["x"] for p in team_b]) if team_b else 90
    a_attacks_right = avg_a <= avg_b

    team_a = _label_positions(team_a, attacking_right=a_attacks_right)
    team_b = _label_positions(team_b, attacking_right=not a_attacks_right)

    for p in team_a + team_b:
        p.pop("frames_seen", None)

    compact_frames = [
        {
            "frame_idx": f.get("frame_idx", i),
            "team_a": [{"id": p["id"], "x": round(float(p["x"]), 2), "y": round(float(p["y"]), 2)} for p in f.get("team_a", [])],
            "team_b": [{"id": p["id"], "x": round(float(p["x"]), 2), "y": round(float(p["y"]), 2)} for p in f.get("team_b", [])],
        }
        for i, f in enumerate(frames[:120])
    ]

    return {
        "team_a": team_a,
        "team_b": team_b,
        "frames": compact_frames,
        "frames_processed": len(frames),
        "method": method,
        "message": (
            f"Tracked {len(team_a)} + {len(team_b)} players across {len(frames)} frames "
            f"using {'YOLOv8 detection' if method == 'yolo' else 'synthetic tracking'}."
        ),
    }


def _synthetic_tracking(method: str, message: str) -> dict:
    """Generate synthetic tracking data using the engine's own generator."""
    if HAS_VIDEO and VideoAnalyzer is not None:
        try:
            analyzer = VideoAnalyzer()
            tracking = analyzer.run_synthetic_demo(n_frames=60)
            snapshot = _tracking_to_snapshot(tracking, method=method)
            snapshot["message"] = message
            return snapshot
        except Exception:
            pass

    # Last-resort static snapshot (engine generator unavailable)
    team_a = [
        {"name": "Player 1",  "number": 1,  "x": 5,  "y": 40, "position": "GK"},
        {"name": "Player 2",  "number": 2,  "x": 28, "y": 68, "position": "RB"},
        {"name": "Player 3",  "number": 3,  "x": 25, "y": 50, "position": "CB"},
        {"name": "Player 4",  "number": 4,  "x": 25, "y": 30, "position": "CB"},
        {"name": "Player 5",  "number": 5,  "x": 28, "y": 12, "position": "LB"},
        {"name": "Player 6",  "number": 6,  "x": 45, "y": 48, "position": "CM"},
        {"name": "Player 7",  "number": 7,  "x": 45, "y": 32, "position": "CM"},
        {"name": "Player 8",  "number": 8,  "x": 60, "y": 40, "position": "CAM"},
        {"name": "Player 9",  "number": 9,  "x": 66, "y": 66, "position": "RW"},
        {"name": "Player 10", "number": 10, "x": 66, "y": 14, "position": "LW"},
        {"name": "Player 11", "number": 11, "x": 80, "y": 40, "position": "ST"},
    ]
    team_b = [
        {"name": "Player 12", "number": 12, "x": 115, "y": 40, "position": "GK"},
        {"name": "Player 13", "number": 13, "x": 92,  "y": 68, "position": "RB"},
        {"name": "Player 14", "number": 14, "x": 94,  "y": 50, "position": "CB"},
        {"name": "Player 15", "number": 15, "x": 94,  "y": 30, "position": "CB"},
        {"name": "Player 16", "number": 16, "x": 92,  "y": 12, "position": "LB"},
        {"name": "Player 17", "number": 17, "x": 76,  "y": 40, "position": "CDM"},
        {"name": "Player 18", "number": 18, "x": 70,  "y": 56, "position": "CM"},
        {"name": "Player 19", "number": 19, "x": 70,  "y": 24, "position": "CM"},
        {"name": "Player 20", "number": 20, "x": 56,  "y": 66, "position": "RW"},
        {"name": "Player 21", "number": 21, "x": 50,  "y": 40, "position": "ST"},
        {"name": "Player 22", "number": 22, "x": 56,  "y": 14, "position": "LW"},
    ]
    return {
        "team_a": team_a,
        "team_b": team_b,
        "frames": [],
        "frames_processed": 0,
        "method": method,
        "message": message,
    }
