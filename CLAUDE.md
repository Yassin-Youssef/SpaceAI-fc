# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install Python dependencies** (use a venv; on this Windows machine `python` is not on PATH, use `py -3`):
```bash
py -3 -m venv .venv            # or: python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS / Linux
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
.venv/Scripts/python -m uvicorn api.main:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
# Feature list: http://localhost:8000/api/features
```
Note: with `--reload` on Windows, killing the reloader parent can leave the worker
process alive and still serving old code on port 8000. If changes don't show up, kill
every `python.exe` whose command line contains `uvicorn` before restarting.

**Start the React frontend** (`frontend/` — primary production UI):
```bash
cd frontend
npm install        # or: pnpm install
npm run dev        # http://localhost:5173
npm run typecheck  # tsc --noEmit (run before committing)
npm run build      # production bundle in frontend/dist
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
python test_api.py --endpoint formation # single endpoint (also: dataset, export, ...)
```
On Windows set `PYTHONIOENCODING=utf-8` first, otherwise the ✓/✗ glyphs crash the console.

**LLM keys**: the API also reads a `.env` file at the project root (`OPENROUTER_API_KEY`,
`ANTHROPIC_API_KEY`, optional `OPENROUTER_MODEL`, `RATE_LIMIT`, `CORS_ORIGINS`). Never commit it.

**Install Phase 4 optional dependencies** (video analysis and RL coach):
```bash
pip install ultralytics opencv-python yt-dlp   # video analysis
pip install gymnasium stable-baselines3         # RL coach
```

## Frontend Environment Variables

Create `frontend/.env.local` with:
```
VITE_API_URL=http://localhost:8000/api          # defaults to this if omitted
VITE_SUPABASE_URL=https://xxx.supabase.co       # required for auth + saved analyses
VITE_SUPABASE_ANON_KEY=eyJ...                   # required for auth + saved analyses
VITE_OPENROUTER_API_KEY=sk-or-...               # optional: enables direct browser LLM calls
```

If `VITE_SUPABASE_URL`/`VITE_SUPABASE_ANON_KEY` are absent the app still runs in **guest mode** (the login screen offers "Continue as guest"); auth and history saving are disabled.

**Supabase table required for history saving** (run in Supabase SQL editor):
```sql
create table public.analyses (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references auth.users(id) on delete cascade,
  match_name  text not null,
  feature     text not null,
  input_data  jsonb default '{}',
  results     jsonb default '{}',
  created_at  timestamptz default now()
);
alter table public.analyses enable row level security;
create policy "Users manage own analyses"
  on public.analyses for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
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
- **`simulation.py`** — Rule-based 5v5/7v7 multi-agent pitch simulation; exports animated GIFs. Valid tactics: `high_press`, `low_block`, `wide_play`, `narrow_play`, `counter_attack`, `possession`.

### API Layer (`api/`)

FastAPI backend with 14 routers covering every engine phase.

- **`api/main.py`** — App entry point, CORS, rate limiting (slowapi, `10/minute`), all routers registered.
- **`api/config.py`** — All settings and env vars (`OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, file size limits, CORS origins). Pitch coordinates are `x: 0–120`, `y: 0–80`. CORS whitelists localhost:3000, 5173, 8501 only — update for production deployment.
- **`api/models/requests.py`** — Pydantic request models. `BaseAnalysisRequest` is the shared base; every analysis endpoint accepts `input_type: "manual" | "video" | "dataset"`. Player coordinates validated against pitch bounds.
- **`api/models/responses.py`** — Pydantic response models.
- **`api/services/engine_service.py`** — Stateless wrappers for each engine module; returns dicts + base64 image strings.
- **`api/services/llm_service.py`** — LLM calls: OpenRouter first → Anthropic → knowledge-graph template fallback.
- **`api/services/video_service.py`** — Video upload processing and YouTube download; falls back to synthetic El Clásico data when Phase 4 dependencies are absent.
- **`api/utils/resolve.py`** — `resolve_input()` bridges all three input types: parses CSV/JSON datasets, runs the Phase 4 CV pipeline for video inputs (via `video_service`, with synthetic fallback), or passes through manual player coordinates. Called at the top of every analysis router.
- **`api/utils/image_encoder.py`** — `fig_to_base64(fig)` converts matplotlib figures to base64 PNG.
- **`api/utils/file_handler.py`** — Upload validation, temp file save/cleanup, CSV/JSON parsing (`DatasetParseError` for malformed files).
- **`api/routers/`** — One file per feature: `analysis`, `pass_network`, `space_control`, `formation`, `roles`, `press_resistance`, `patterns`, `intelligence`, `explanation`, `video`, `simulation`, `ask`, `export`, `player_assessment`, `dataset`.
  - `POST /api/dataset/upload` parses a CSV/JSON file and returns normalised `team_a`/`team_b`/`passes`; `GET /api/dataset/template/{csv|json}` serves sample files. The frontend uploads video/dataset first, then sends the resolved players as `input_type: "manual"`.
  - `POST /api/recommendations` and `POST /api/explanation` accept the full `BaseAnalysisRequest` (positions + passes) and run the Phase 1/2 modules themselves; `intelligence.build_analysis_data()` is the shared helper.
  - `POST /api/simulation/run` returns down-sampled `frames` (player + ball positions) so the UI can replay the match.
  - `POST /api/export/docx|pdf` rebuilds a `MatchReport` from the supplied players and embeds the visualisations found in `analysis_data`.
  - `GET /api/demo/players` serves `data/demo_matches/players.json`: ten real stat lines (nine counted from StatsBomb events, Lamine Yamal 2025 reconstructed) with bio, position and `minutes` for per-90 normalisation. Player Assessment's data mode normalises counts per 90 and restricts the role model to roles the given `position` can play. Simulation and Compare "Try Demo" menus use fixture-themed presets from `lib/demo.ts` (`SIM_PRESETS`, `COMPARE_PRESETS`); Ask SpaceAI shows fixture-aware suggested questions when a context exists. The shared split-button menu is `common/PresetPicker.tsx` (portalled to `body` so headers never clip it).
  - `GET /api/demo/matches` and `GET /api/demo/matches/{id}` serve the bundled fixtures in `data/demo_matches/` (built by `scripts/build_demo_matches.py` from StatsBomb open data plus two reconstructed line-ups). Each fixture carries `players_a/b` (starters' median event positions), real `passes`, `match_info`, the nominal line-up `team_a.formation`, and a `source.kind` of `statsbomb` or `reconstructed`. The frontend's "Try Demo" split button (`common/DemoPicker.tsx`) lists them; the built-in El Clásico sample in `lib/demo.ts` is the offline fallback. Rebuilding needs internet (`.venv/Scripts/python scripts/build_demo_matches.py`).

### Formation detection note
`FormationDetector.detect(method="auto")` scores clustering candidates (k = 2–4, KMeans + agglomerative) and the gap method by tactical plausibility (3–4 lines, no line larger than 5, common shapes) rather than raw silhouette, because real average positions otherwise collapse into two bands like "7-3". Detected shapes for real fixtures are *average* shapes and legitimately differ from the named line-up (e.g. Argentina 2022 reads 2-4-4 with the full-backs in midfield); the UI shows both.

### React Frontend (`frontend/`)

Primary production UI — React 18 + TypeScript + Vite + Tailwind CSS v4 + shadcn/Radix UI + MUI. Authentication via Supabase.

- **`frontend/src/main.tsx`** — Entry point, mounts `App.tsx`.
- **`frontend/src/app/App.tsx`** — State-machine router: a single `currentView` string (useState) drives which page component renders, wrapped in a motion `AnimatePresence` for page transitions. React Router is installed but navigation is handled via state, not URL routing. Position-based features (`full-match`, `pass-network`, `space-control`, `formation`, `press-resistance`, `patterns`, `strategy`, `explanation`) share the `FeaturePageInput` → `FeaturePageResults` flow; the others have their own pages.
- **`frontend/src/app/components/`** — Page-level components: `Home` (also exports the `FEATURES` catalogue), `About`, `Auth` (guest mode + Supabase + Google OAuth), `AskSpaceAI`, `Compare`, `FeaturePageInput/Results`, `History`, `PlayerAssessment`, `AppSidebar`, `Settings`, `Simulation`.
- **`frontend/src/app/components/common/`** — Shared building blocks: `Primitives.tsx` (Page, PageHeader, GlassCard, Button, StatTile, Collapsible, EmptyState, ResultsSkeleton), `AnimatedNumber`, `PitchPreview` (SVG pitch), `Markdown` (safe renderer for LLM text).
- **`frontend/src/app/components/results/Sections.tsx`** — Feature-specific result renderers (formation cards, zone bars, pass stats, press gauge, pattern cards, SWOT, recommendations, report text).
- **`frontend/src/app/components/ui/`** — shadcn/ui primitives (accordion, dialog, button, etc.).
- **`frontend/src/lib/api.ts`** — All backend calls. `analyzeFeature(featureId, formData)` resolves the input (manual / uploads video / uploads dataset) via `resolveFormInput()` and maps feature IDs to endpoints (`FEATURE_ENDPOINTS`). Pass text (`4->8->1`) is parsed with coordinates filled in from player positions.
- **`frontend/src/lib/demo.ts`** — El Clásico demo data used by every "Try Demo" button.
- **`frontend/src/lib/motion.ts`** — Shared animation presets. The project uses the `motion` package (`motion/react`), which is framer-motion under its current name.
- **`frontend/src/lib/llm.ts`** — Optional direct browser→OpenRouter calls (requires `VITE_OPENROUTER_API_KEY`). Returns `null` when unconfigured; callers fall back to the backend `/api/ask` endpoint.
- **`frontend/src/lib/supabase.ts`** — Auth (signUp/signIn/signOut) and analyses CRUD. Degrades gracefully when env vars are absent.
- **`frontend/src/lib/types.ts`** — Shared TypeScript types.

### Streamlit Frontend (`app/`)

MVP/fallback UI calling the same FastAPI backend.

- **`app/streamlit_app.py`** — Entry point; sets page config, injects CSS, routes to view modules.
- **`app/demo_data.py`** — El Clásico pre-built data used by every view's "Load Demo Data" button.
- **`app/views/`** — One file per feature (mirrors API routers).
- **`app/components/`** — `theme.py` (all CSS), `sidebar.py`, `input_forms.py`, `results_display.py`.
- **`app/utils/api_client.py`** — `requests`-based calls to every API endpoint; `base64_to_image()` for PIL rendering.

### Key Design Patterns

- Engine modules are stateless — each takes data as input and returns results; they don't import each other.
- `main.py` is the orchestrator, threading results from one module into the next.
- All matplotlib figures use `matplotlib.use('Agg')` — no display server required.
- LLM fallback chain: OpenRouter → Anthropic → template strings. No LLM key required to run.
- `resolve_input()` in `api/utils/resolve.py` is the single integration point between input types (manual/video/dataset) and the analysis engine — every router calls it to normalise inputs before passing to engine services.

### Reporting (`engine/analysis/match_report.py`)

Integrator producing a 4-panel matplotlib dashboard, formatted text report, and Word document export via `python-docx`. All artifacts go to `outputs/`.

### Tests

`tests/` contains only `__init__.py` — no unit tests yet.
`test_api.py` at the project root tests all API endpoints (including dataset upload and export) against a running server.
Frontend: `npm run typecheck` must pass; there is no unit-test suite. For end-to-end checks, drive the dev server with Playwright against the installed Chrome (`chromium.launch({ channel: "chrome" })`).
