# ⚽ SpaceAI FC

**Agentic Tactical Intelligence System for Football**

An AI-powered football analysis engine that understands player positioning, analyzes space control and passing dynamics, detects tactical patterns, and generates strategic insights. Built with a robotics-inspired pipeline: **Sense → Understand → Reason → Act → Explain**.

---

## 🎯 What It Does

SpaceAI FC takes match data (player positions, pass events) and produces:

- **Pitch visualization** with player positions and team separation
- **Pass network analysis** identifying key distributors and strongest connections
- **Pass sequence visualization** showing step-by-step build-up plays
- **Space control maps** using Voronoi and Gaussian influence models
- **Automated match reports** with tactical insights and recommendations

---

## 📸 Sample Output

### Pitch Model
![Pitch](outputs/01_pitch.png)

### Pass Network
![Pass Network](outputs/02_pass_network.png)

### Build-Up Sequence
![Sequence](outputs/03_pass_sequence.png)

### Space Control (Voronoi)
![Voronoi](outputs/04_space_voronoi.png)

### Space Control (Influence Model)
![Influence](outputs/05_space_influence.png)

### Full Match Dashboard
![Dashboard](outputs/06_match_dashboard.png)

---

## 🏗️ System Architecture
```
Input (positions, passes, stats)
        ↓
   Perception
   (player positions, coordinate mapping)
        ↓
   Tactical Analysis
   (space control, pass networks)
        ↓
   Match Report
   (insights, recommendations, visualizations)
        ↓
   Output
   (dashboards, reports, images)
```

---

## 📁 Project Structure
```
spaceai-fc/
├── engine/
│   ├── analysis/
│   │   ├── pass_network.py      # Pass graph analysis & visualization
│   │   ├── space_control.py     # Voronoi & influence space control
│   │   └── match_report.py      # Combined report & dashboard generator
│   ├── intelligence/            # Phase 3: tactical reasoning (coming soon)
│   ├── perception/              # Phase 2: formation detection (coming soon)
│   └── visualization/
│       └── pitch.py             # Football pitch model & player plotting
├── outputs/                     # Generated images and reports
├── notebooks/                   # Experiments
├── tests/                       # Unit tests
├── main.py                      # Full demo - runs entire pipeline
├── requirements.txt             # Python dependencies
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/spaceai-fc.git
cd spaceai-fc
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
.\venv\Scripts\Activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the demo
```bash
python main.py
```

This runs the full El Clásico analysis and saves all outputs to the `outputs/` folder.

---

## 🔧 Engine Modules

### Pitch Model (`engine/visualization/pitch.py`)
- 2D football pitch rendering using mplsoccer
- Player position plotting with team colors
- Ball position marker
- Configurable pitch dimensions and styles

### Pass Network (`engine/analysis/pass_network.py`)
- Directed graph of passes between players (NetworkX)
- Centrality metrics: degree, betweenness, eigenvector
- Key distributor identification
- Top connection detection
- Weak link analysis
- Two visualization modes:
  - **Network view**: overall passing structure with curved arrows
  - **Sequence view**: step-by-step build-up play with numbered passes

### Space Control (`engine/analysis/space_control.py`)
- **Voronoi model**: nearest-player territorial zones
- **Influence model**: Gaussian decay spatial dominance
- Overall control percentages
- Zone breakdown (defensive / middle / attacking third)
- Midfield control analysis

### Match Report (`engine/analysis/match_report.py`)
- Combines all analysis modules
- Simple formation detection from player positions
- Automated insight generation
- Tactical recommendations
- 4-panel visual dashboard
- Formatted text report

---

## 🗺️ Roadmap

### Phase 1 — Foundation ✅ (Current)
- [x] Pitch model & player plotting
- [x] Pass network analysis
- [x] Space control (Voronoi + Influence)
- [x] Match report generator
- [x] Visual dashboard

### Phase 2 — Detection (Next)
- [ ] Formation detection with clustering algorithms
- [ ] Player role classification
- [ ] Press resistance analysis
- [ ] Tactical pattern detection

### Phase 3 — Tactical Intelligence
- [ ] Football knowledge graph
- [ ] Rule-based tactical reasoning
- [ ] Strategy recommendation system
- [ ] LLM explanation layer

### Phase 4 — Advanced AI
- [ ] Video-based player tracking
- [ ] Reinforcement learning coach
- [ ] Multi-agent simulation

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| NumPy | Numerical computing |
| Pandas | Data processing |
| NetworkX | Graph-based pass analysis |
| SciPy | Voronoi tessellation, spatial analysis |
| matplotlib | Visualization engine |
| mplsoccer | Football-specific pitch rendering |

---

## 💡 Inspired By

The system follows a robotics-inspired agentic pipeline:

**Sense → Understand → Reason → Act → Explain**

Designed to function like an intelligent football analyst that observes matches, understands structure, reasons about tactics, recommends strategies, and explains decisions.

---

## 📄 License

MIT License

---

*Built by [Yassin Youssef]*
