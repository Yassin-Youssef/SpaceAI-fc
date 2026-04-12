# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies:**
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
```

**Run a single test file:**
```bash
pytest tests/test_filename.py -v
```

**Set up LLM-powered explanations** (optional — falls back to templates without it):
```bash
export ANTHROPIC_API_KEY=your_key_here
```

**Start the Streamlit frontend** (Step 2 — requires API running first):
```bash
streamlit run app/streamlit_app.py --server.port 8501
# Open: http://localhost:8501
```

**Start the API server** (Step 1 product layer):
```bash
uvicorn api.main:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
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

SpaceAI FC is a three-phase agentic tactical intelligence system modeled on a robotics cognitive pipeline: **Sense → Understand → Reason → Act → Explain**.

### Data Flow

`main.py` defines a match fixture (player positions + pass events as dicts) and runs a 15-step pipeline, passing intermediate results between modules. There is no persistent database — data lives in Python dicts/dataframes in memory during a run.

### Phase 1 — Perception (`engine/analysis/`)

- **`pass_network.py`** — Builds a directed NetworkX graph of passes; computes degree/betweenness/eigenvector centrality; outputs key distributors and network visualizations.
- **`space_control.py`** — Dual spatial analysis: Voronoi tessellation and Gaussian influence decay. Returns zone-by-zone control percentages for each team.
- **`pitch.py`** (`engine/visualization/`) — mplsoccer pitch rendering used by all modules for visualizing player positions, heatmaps, and networks.

### Phase 2 — Understanding (`engine/analysis/`)

- **`formation_detection.py`** — K-Means/Agglomerative clustering on player x-coordinates; outputs formation strings like `"4-3-3"`. Handles left/right team orientation.
- **`role_classifier.py`** — Rule-based classifier for tactical roles beyond position (false nine, inverted winger, box-to-box, overlapping fullback, etc.); returns role + confidence score per player.
- **`press_resistance.py`** — Scores 0–100 press resistance; measures pass success under pressure; flags vulnerable zones.
- **`pattern_detection.py`** — Detects overlapping runs, compact blocks, wide overloads, high/low lines; returns patterns with confidence scores.

### Phase 3 — Intelligence (`engine/intelligence/`)

- **`knowledge_graph.py`** — 30+ node NetworkX graph encoding formations, tactical situations (low block, high press, counter-attack), strategies, and their relationships. The core domain knowledge store.
- **`tactical_reasoning.py`** — SWOT engine (15+ rules) that ingests all Phase 1/2 outputs and queries the knowledge graph to produce structured strengths/weaknesses/opportunities/threats.
- **`strategy_recommender.py`** — Converts SWOT output into prioritized recommendations (High/Medium/Low) across five categories: formation changes, pressing adjustments, attacking strategies, defensive adjustments, player instructions.
- **`explanation_layer.py`** — Produces natural language reports. Uses template strings by default; switches to Claude API (Anthropic) if `ANTHROPIC_API_KEY` is set.

### Reporting (`engine/analysis/match_report.py`)

Integrator class that combines all module outputs into:
- A 4-panel matplotlib dashboard
- Formatted text report
- Word document export via `python-docx`

### Output

All generated artifacts (PNGs, Word docs) go to the `outputs/` directory. The `data/raw/` and `data/processed/` directories hold match input data.

### Key Design Patterns

- Modules are independent and stateless — each takes data as input and returns results. They don't import each other.
- `main.py` acts as the orchestrator, threading results from one module into the next.
- The `explanation_layer.py` degrades gracefully: full LLM report with API key, template-based report without.
- Phase 4 is implemented but all three modules are **optional** — `main.py` skips them gracefully if their dependencies are missing. The `api/` directory is currently empty.

### Phase 4 — Advanced AI (`engine/perception/` + `engine/intelligence/`)

- **`video_analyzer.py`** — Extracts player positions from video via YOLOv8 + homography to pitch coordinates. Falls back to synthetic demo data if `ultralytics`/`opencv-python`/`yt-dlp` are absent.
- **`rl_coach.py`** — Custom Gymnasium environment (`FootballTacticsEnv`) with a PPO agent (Stable-Baselines3) that learns 9 tactical decisions (press higher, drop deeper, etc.) from simulated match states.
- **`simulation.py`** — Rule-based 5v5/7v7 multi-agent pitch simulation; compares tactical presets and exports animated GIFs. Requires only matplotlib (already in core deps).

### API Layer (`api/`)

FastAPI backend wrapping all engine phases as HTTP endpoints.

- **`api/main.py`** — App entry point, CORS, rate limiting (slowapi), all routers registered.
- **`api/config.py`** — All settings and env vars (`OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, file size limits, CORS origins).
- **`api/models/`** — Pydantic request/response models. Every analysis endpoint accepts `input_type: "manual" | "video" | "dataset"`.
- **`api/services/engine_service.py`** — Stateless functions wrapping each engine module. Returns dicts + base64 image strings.
- **`api/services/llm_service.py`** — LLM calls: OpenRouter first, then Anthropic, then knowledge-graph template fallback.
- **`api/services/video_service.py`** — Video processing; synthetic demo data fallback if Phase 4 deps absent.
- **`api/routers/`** — One router file per feature group.
- **`api/utils/image_encoder.py`** — `fig_to_base64(fig)` converts matplotlib figures to base64 PNG for responses.
- **`api/utils/file_handler.py`** — Upload validation, temp file save/cleanup, CSV/JSON dataset parsing.
- **`temp/`** — Temporary upload storage, cleaned up after each request.

### Frontend Layer (`app/`)

Streamlit MVP — football-themed UI calling the FastAPI backend.

- **`app/streamlit_app.py`** — Entry point. Sets page config, injects CSS, renders sidebar, routes to page module.
- **`app/demo_data.py`** — El Clásico pre-built data (BARCA_PLAYERS, MADRID_PLAYERS, DEMO_PASSES, etc.) used by every page's "Load Demo Data" button.
- **`app/components/theme.py`** — `FOOTBALL_CSS` string + helpers (`inject_css`, `page_header`, `section_title`, `insight_item`). All custom CSS lives here.
- **`app/components/sidebar.py`** — Navigation radio + API status indicator.
- **`app/components/input_forms.py`** — Reusable widgets: `player_table`, `pass_events_input`, `match_info_form`, `team_meta`, `demo_button`, `analyze_button`, `video_input_tab`, `dataset_input_tab`.
- **`app/components/results_display.py`** — Reusable result renderers: `show_visualizations`, `metric_row`, `show_swot`, `show_recommendations`, `show_patterns`, `show_explanation`, `download_image_button`.
- **`app/utils/api_client.py`** — `requests`-based calls to every FastAPI endpoint; `base64_to_image()` converts API images to PIL for `st.image()`.
- **`app/pages/`** — One file per feature (7 pages in Batch 1). Each page manages its own `st.session_state` keys so results survive navigation.

All matplotlib figures are generated with `matplotlib.use('Agg')` (no display server needed).

### Tests

`tests/` currently contains only `__init__.py` — no test files exist yet.
`test_api.py` at the project root tests all API endpoints against a running server.
