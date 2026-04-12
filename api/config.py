"""
SpaceAI FC - API Configuration
================================
Central settings, env vars, and constants.
"""

import os
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Ensure temp dir exists
TEMP_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# ── API ──────────────────────────────────────────────────────────
API_VERSION = "4.0"
API_TITLE = "SpaceAI FC"
API_DESCRIPTION = (
    "Agentic tactical intelligence system for football. "
    "Wraps all 4 engine phases as HTTP endpoints."
)

# ── CORS ─────────────────────────────────────────────────────────
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8501",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8501",
]

# ── File limits ──────────────────────────────────────────────────
MAX_VIDEO_SIZE_MB = 500
MAX_DATASET_SIZE_MB = 50
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024
MAX_DATASET_SIZE_BYTES = MAX_DATASET_SIZE_MB * 1024 * 1024

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
ALLOWED_DATASET_EXTENSIONS = {".csv", ".json"}

# ── Rate limiting ────────────────────────────────────────────────
RATE_LIMIT = "10/minute"

# ── LLM ─────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "anthropic/claude-haiku-4-20250514"

# ── Coordinate validation ────────────────────────────────────────
PITCH_X_MIN, PITCH_X_MAX = 0.0, 120.0
PITCH_Y_MIN, PITCH_Y_MAX = 0.0, 80.0
