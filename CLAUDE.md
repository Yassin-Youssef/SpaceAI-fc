# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**Run the full end-to-end demo** (generates all outputs in `outputs/`):
```bash
python main.py
```

**Run tests:**
```bash
pytest tests/
pytest tests/test_filename.py -v
```

**Set up LLM-powered explanations** (optional — falls back to templates without it):
```bash
export ANTHROPIC_API_KEY=your_key_here
export OPENROUTER_API_KEY=your_key_here   # preferred; falls back to Anthropic
```

**Start the API server** (required first for both frontends):
```bash
uvicorn api.main:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
```

**Start the React frontend** (`frontend/` — primary production UI):
```bash
cd frontend
npm install     # or: pnpm install
npm run dev     # http://localhost:5173
```

**Start the Streamlit frontend** (`app/` — MVP/fallback UI):
```bash
streamlit run app/streamlit_app.py --server.port 8501
# http://localhost:8501
```

**Test all API endpoints** (server must be running):
```bash
python test_api.py
python test_api.py --skip-slow          # skip the full pipeline test
python test_api.py --endpoint formation # single endpoint
```

**Install Phase 4 optional dependencies** (video analysis and RL coach):
```bash
pip install ultralytics opencv-python yt-dlp   # video analysis
pip install gymnasium stable-baselines3         # RL coach
```

## Architecture

SpaceAI FC is a tactical intelligence system modeled on a robotics cognitive pipeline: **Sense → Understand → Reason → Act → Explain**.

### Data Flow

`main.py` defines a match fixture (player positions + pass events as dicts) and runs a 15-step pipeline, passing intermediate results between modules. There is no persistent database — data lives in Python dicts/dataframes in memory during a run.

The API layer exposes all engine phases as HTTP endpoints. Both frontends call the API; they share no code.

### Phase 1 — Perception (`engine/analysis/`)

- **`pass_network.py`** — Builds a directed NetworkX graph of passes; computes degree/betweenness/eigenvector centrality.
- **`space_control.py`** — Dual spatial analysis: Voronoi tessellation and Gaussian influence decay. Returns zone-by-zone control percentages.
- **`pitch.py`** (`engine/visualization/`) — mplsoccer pitch rendering used by all modules.

### Phase 2 — Understanding (`engine/analysis/`)

- **`formation_detection.py`** — K-Means/Agglomerative clustering on player x-coordinates; outputs formation strings like `"4-3-3"`.
- **`role_classifier.py`** — Rule-based classifier for tactical sub-roles (false nine, inverted winger, box-to-box, etc.); returns role + confidence per player.
- **`press_resistance.py`** — Scores 0–100 press resistance; flags vulnerable zones.
- **`pattern_detection.py`** — Detects overlapping runs, compact blocks, wide overloads, high/low lines.

### Phase 3 — Intelligence (`engine/intelligence/`)

- **`knowledge_graph.py`** — 30+ node NetworkX graph encoding formations, tactical situations, strategies, and their relationships. Core domain knowledge store.
- **`tactical_reasoning.py`** — SWOT engine (15+ rules) querying the knowledge graph from Phase 1/2 outputs.
- **`strategy_recommender.py`** — Converts SWOT output into prioritized recommendations (High/Medium/Low) across five categories.
- **`explanation_layer.py`** — Natural language reports. Template-based by default; uses Claude API if `ANTHROPIC_API_KEY` is set.

### Phase 4 — Advanced AI (`engine/perception/` + `engine/intelligence/`)

All three modules are optional — `main.py` skips them gracefully if their dependencies are missing.

- **`video_analyzer.py`** — Extracts player positions from video via YOLOv8 + homography. Falls back to synthetic demo data if dependencies are absent.
- **`rl_coach.py`** — Custom Gymnasium environment with PPO agent (Stable-Baselines3) learning 9 tactical decisions.
- **`simulation.py`** — Rule-based 5v5/7v7 multi-agent pitch simulation; exports animated GIFs.

### API Layer (`api/`)

FastAPI backend with 14 routers covering every engine phase.

- **`api/main.py`** — App entry point, CORS, rate limiting (slowapi, `10/minute`), all routers registered.
- **`api/config.py`** — All settings and env vars (`OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, file size limits, CORS origins). Pitch coordinates are `x: 0–120`, `y: 0–80`.
- **`api/models/`** — Pydantic request/response models. Every analysis endpoint accepts `input_type: "manual" | "video" | "dataset"`.
- **`api/services/engine_service.py`** — Stateless wrappers for each engine module; returns dicts + base64 image strings.
- **`api/services/llm_service.py`** — LLM calls: OpenRouter first → Anthropic → knowledge-graph template fallback.
- **`api/routers/`** — One file per feature: `analysis`, `pass_network`, `space_control`, `formation`, `roles`, `press_resistance`, `patterns`, `intelligence`, `explanation`, `video`, `simulation`, `ask`, `export`, `player_assessment`.
- **`api/utils/image_encoder.py`** — `fig_to_base64(fig)` converts matplotlib figures to base64 PNG.
- **`api/utils/file_handler.py`** — Upload validation, temp file save/cleanup, CSV/JSON parsing.

### React Frontend (`frontend/`)

Primary production UI — React 18 + TypeScript + Vite + Tailwind CSS v4 + shadcn/Radix UI. Authentication via Supabase.

- **`frontend/src/main.tsx`** — Entry point, mounts `App.tsx`.
- **`frontend/src/app/App.tsx`** — Router and layout shell using react-router v7.
- **`frontend/src/app/components/`** — Page-level components: `Home`, `Auth`, `AskSpaceAI`, `ChatInterface`, `Compare`, `Explanation`, `FeaturePageInput/Results`, `Formation`, `History`, `MatchStats`, `PlayerAssessment`, `Sidebar/AppSidebar`, `Simulation`, `Strategy`, `TacticalPitch`.
- **`frontend/src/imports/`** — shadcn/ui primitives and shared UI utilities.

### Streamlit Frontend (`app/`)

MVP/fallback UI calling the same FastAPI backend.

- **`app/streamlit_app.py`** — Entry point; sets page config, injects CSS, routes to view modules.
- **`app/demo_data.py`** — El Clásico pre-built data used by every view's "Load Demo Data" button.
- **`app/views/`** — One file per feature (mirrors API routers): `formation.py`, `pass_network.py`, `space_control.py`, `patterns.py`, `press_resistance.py`, `roles.py`, `player_assessment.py`, `recommendations.py`, `explanation.py`, `simulation.py`, `compare.py`, `full_analysis.py`, `ask_spaceai.py`.
- **`app/components/`** — `theme.py` (all CSS), `sidebar.py`, `input_forms.py`, `results_display.py`.
- **`app/utils/api_client.py`** — `requests`-based calls to every API endpoint; `base64_to_image()` for PIL rendering.

### Key Design Patterns

- Engine modules are stateless — each takes data as input and returns results; they don't import each other.
- `main.py` is the orchestrator, threading results from one module into the next.
- All matplotlib figures use `matplotlib.use('Agg')` — no display server required.
- LLM fallback chain: OpenRouter → Anthropic → template strings. No LLM key required to run.

### Reporting (`engine/analysis/match_report.py`)

Integrator producing a 4-panel matplotlib dashboard, formatted text report, and Word document export via `python-docx`. All artifacts go to `outputs/`.

### Tests

`tests/` contains only `__init__.py` — no unit tests yet.
`test_api.py` at the project root tests all API endpoints against a running server.
