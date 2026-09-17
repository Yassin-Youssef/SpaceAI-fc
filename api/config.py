"""
SpaceAI FC - API Configuration
================================
Central settings, env vars, and constants.

Secrets are read from environment variables only. A `.env` file at the
project root is loaded (without overriding variables that are already set)
so local development does not require exporting keys by hand.
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


# ── .env loader (dependency-free) ────────────────────────────────
def _load_dotenv(path: Path) -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ if unset."""
    if not path.exists():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        pass


_load_dotenv(BASE_DIR / ".env")


# ── API ──────────────────────────────────────────────────────────
API_VERSION = "4.1"
API_TITLE = "SpaceAI FC"
API_DESCRIPTION = (
    "Agentic tactical intelligence system for football. "
    "Wraps all 4 engine phases as HTTP endpoints."
)

# ── CORS ─────────────────────────────────────────────────────────
_default_origins = [
    "http://localhost:3000",
    "http://localhost:8501",
    "http://localhost:5173",
    "http://localhost:4173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8501",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:4173",
]
_extra_origins = [
    o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
]
CORS_ORIGINS = _default_origins + _extra_origins

# ── File limits ──────────────────────────────────────────────────
MAX_VIDEO_SIZE_MB = 500
MAX_DATASET_SIZE_MB = 50
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024
MAX_DATASET_SIZE_BYTES = MAX_DATASET_SIZE_MB * 1024 * 1024

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}
ALLOWED_DATASET_EXTENSIONS = {".csv", ".json"}

# ── Rate limiting ────────────────────────────────────────────────
RATE_LIMIT = os.environ.get("RATE_LIMIT", "60/minute")

# ── LLM ─────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

# ── Coordinate validation ────────────────────────────────────────
PITCH_X_MIN, PITCH_X_MAX = 0.0, 120.0
PITCH_Y_MIN, PITCH_Y_MAX = 0.0, 80.0
