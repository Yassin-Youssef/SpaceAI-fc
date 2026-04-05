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
- Phase 4 is planned (video tracking, RL coach, multi-agent simulation) — `engine/perception/` and `api/` directories are stubs for this.
