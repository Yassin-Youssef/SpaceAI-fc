"""
SpaceAI FC - FastAPI Application
==================================
Entry point.  Start with:
    uvicorn api.main:app --reload --port 8000
"""

import matplotlib
matplotlib.use('Agg')

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.config import (
    API_TITLE, API_DESCRIPTION, API_VERSION,
    CORS_ORIGINS, RATE_LIMIT,
    OPENROUTER_API_KEY, ANTHROPIC_API_KEY,
)

# ── Routers ──────────────────────────────────────────────────────
from api.routers import (
    analysis, pass_network, space_control, formation, roles,
    press_resistance, patterns, intelligence, explanation,
    video, simulation, ask, export,
)

# ── Rate limiter ─────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT])

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include routers ───────────────────────────────────────────────
app.include_router(analysis.router)
app.include_router(pass_network.router)
app.include_router(space_control.router)
app.include_router(formation.router)
app.include_router(roles.router)
app.include_router(press_resistance.router)
app.include_router(patterns.router)
app.include_router(intelligence.router)
app.include_router(explanation.router)
app.include_router(video.router)
app.include_router(simulation.router)
app.include_router(ask.router)
app.include_router(export.router)

# ── Utility endpoints ─────────────────────────────────────────────

@app.get("/api/health", tags=["Utility"])
async def health():
    from engine.intelligence.simulation import TACTICAL_PRESETS
    return {
        "status": "ok",
        "version": API_VERSION,
        "engine_phases": 4,
        "llm_available": bool(OPENROUTER_API_KEY or ANTHROPIC_API_KEY),
        "available_tactics": sorted(TACTICAL_PRESETS.keys()),
    }


@app.get("/api/features", tags=["Utility"])
async def features():
    feature_list = [
        {"endpoint": "POST /api/analyze",           "description": "Full pipeline — all 4 phases",                   "input_types": ["manual", "video", "dataset"]},
        {"endpoint": "POST /api/tactical-analysis", "description": "Phase 1+2 — formation, space, passes",           "input_types": ["manual", "video", "dataset"]},
        {"endpoint": "POST /api/pass-network",      "description": "Pass graph, centrality, key distributor",        "input_types": ["manual", "dataset"]},
        {"endpoint": "POST /api/space-control",     "description": "Voronoi + influence territorial dominance",      "input_types": ["manual", "dataset"]},
        {"endpoint": "POST /api/formation",         "description": "Formation detection (clustering / gap)",         "input_types": ["manual", "dataset"]},
        {"endpoint": "POST /api/roles",             "description": "Tactical sub-role classification",               "input_types": ["manual", "dataset"]},
        {"endpoint": "POST /api/press-resistance",  "description": "Press resistance score and vulnerable zones",    "input_types": ["manual", "dataset"]},
        {"endpoint": "POST /api/patterns",          "description": "Overlaps, blocks, overloads, high/low line",     "input_types": ["manual", "dataset"]},
        {"endpoint": "POST /api/knowledge-graph",   "description": "Query tactical knowledge graph",                 "input_types": ["manual"]},
        {"endpoint": "POST /api/reasoning",         "description": "SWOT tactical reasoning",                        "input_types": ["manual", "dataset"]},
        {"endpoint": "POST /api/recommendations",   "description": "Prioritised tactical recommendations",           "input_types": ["manual"]},
        {"endpoint": "POST /api/explanation",       "description": "Natural language tactical report",               "input_types": ["manual"]},
        {"endpoint": "POST /api/video/upload",      "description": "Upload and analyse video file",                  "input_types": ["video"]},
        {"endpoint": "POST /api/video/youtube",     "description": "Download and analyse YouTube clip",              "input_types": ["video"]},
        {"endpoint": "POST /api/video/track-player","description": "Track individual player from video data",        "input_types": ["video"]},
        {"endpoint": "POST /api/simulation/run",    "description": "Run 5v5/7v7 tactical simulation",               "input_types": ["manual"]},
        {"endpoint": "POST /api/simulation/compare","description": "Compare two tactical matchups",                  "input_types": ["manual"]},
        {"endpoint": "POST /api/rl/predict",        "description": "RL coach tactical recommendation",              "input_types": ["manual"]},
        {"endpoint": "POST /api/rl/train",          "description": "Train RL PPO agent (admin)",                    "input_types": ["manual"]},
        {"endpoint": "POST /api/ask",               "description": "Natural language Q&A about tactics",            "input_types": ["manual"]},
        {"endpoint": "POST /api/export/docx",       "description": "Export report as Word document",                "input_types": ["manual"]},
        {"endpoint": "POST /api/export/pdf",        "description": "Export report as PDF",                          "input_types": ["manual"]},
    ]
    return {"total": len(feature_list), "features": feature_list}


# ── Global error handler ──────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred.", "type": type(exc).__name__},
    )
