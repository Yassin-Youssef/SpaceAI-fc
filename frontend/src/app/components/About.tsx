import { motion } from "motion/react";
import {
  Eye, Brain, Lightbulb, Play, MessageSquareText, Github, ExternalLink, Cpu, Layers, Database,
  Video, Gamepad2, Sparkles, ArrowRight, Info,
} from "lucide-react";
import { Page, PageHeader, StaggerGrid, StaggerItem, GlassCard, Button } from "./common/Primitives";
import { cardHover } from "../../lib/motion";

const GITHUB_URL = "https://github.com/Yassin-Youssef/SpaceAI-fc";

const PIPELINE = [
  { icon: Eye, name: "Sense", text: "Ingest player positions and passes from manual entry, tracked video, or a dataset." },
  { icon: Layers, name: "Understand", text: "Detect formations, classify roles, score press resistance and spot tactical patterns." },
  { icon: Brain, name: "Reason", text: "A knowledge graph and SWOT rule engine judge strengths, weaknesses, threats and opportunities." },
  { icon: Play, name: "Act", text: "Prioritised strategy recommendations, simulations and an RL coach propose what to change." },
  { icon: MessageSquareText, name: "Explain", text: "A written report — template or LLM — tells the coaching staff why, in plain language." },
];

const PHASES = [
  {
    icon: Eye, phase: "Phase 1", name: "Perception", color: "#00d9ff",
    text: "Builds a directed pass graph (degree, betweenness, eigenvector centrality) and dual spatial models: Voronoi tessellation and Gaussian influence decay, giving zone-by-zone control.",
    modules: ["pass_network", "space_control", "pitch"],
  },
  {
    icon: Layers, phase: "Phase 2", name: "Understanding", color: "#2fe58f",
    text: "K-Means / agglomerative clustering on player depth reads the formation; a rule-based classifier assigns sub-roles such as false nine or inverted winger; press resistance and pattern detection quantify how the shape behaves.",
    modules: ["formation_detection", "role_classifier", "press_resistance", "pattern_detection"],
  },
  {
    icon: Brain, phase: "Phase 3", name: "Intelligence", color: "#7b61ff",
    text: "A 30+ node tactical knowledge graph links formations, situations and counter-strategies. Fifteen SWOT rules query it, a recommender ranks actions by priority, and an explanation layer writes the briefing.",
    modules: ["knowledge_graph", "tactical_reasoning", "strategy_recommender", "explanation_layer"],
  },
  {
    icon: Cpu, phase: "Phase 4", name: "Advanced AI", color: "#ffcf4d",
    text: "Optional modules: YOLOv8 + homography extract positions from footage, a PPO agent learns nine tactical decisions in a Gymnasium environment, and a multi-agent simulation plays out 5v5 / 7v7 scenarios.",
    modules: ["video_analyzer", "rl_coach", "simulation"],
  },
];

const STACK: Array<{ group: string; icon: typeof Cpu; items: string[] }> = [
  { group: "Engine", icon: Cpu, items: ["Python 3", "NumPy · SciPy", "NetworkX", "scikit-learn", "matplotlib · mplsoccer"] },
  { group: "API", icon: Database, items: ["FastAPI", "Pydantic v2", "Uvicorn", "slowapi rate limiting", "python-docx export"] },
  { group: "Frontend", icon: Sparkles, items: ["React 18 + TypeScript", "Vite", "Tailwind CSS v4", "shadcn/ui · Radix", "Motion (framer-motion)", "Recharts"] },
  { group: "Data & AI", icon: Video, items: ["Supabase auth + history", "OpenRouter / Anthropic LLMs", "YOLOv8 · OpenCV", "Gymnasium · Stable-Baselines3"] },
];

export function About({ onFeatureClick }: { onFeatureClick: (id: string) => void }) {
  return (
    <Page width="max-w-6xl">
      <div className="space-y-8">
        <PageHeader
          icon={Info}
          eyebrow="About"
          title="SpaceAI FC"
          description="An agentic tactical intelligence system for football, modelled on a robotics cognitive pipeline."
          actions={
            <a href={GITHUB_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-white/10">
              <Github className="h-4 w-4" /> GitHub <ExternalLink className="h-3.5 w-3.5 text-text-muted" />
            </a>
          }
        />

        {/* What it is */}
        <motion.section initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="glass p-6 sm:p-8">
          <h2 className="mb-3 text-xl font-bold text-white">What it does</h2>
          <p className="max-w-3xl leading-relaxed text-text-secondary">
            SpaceAI FC watches a match situation, understands its tactical structure, reasons about strengths and
            weaknesses, recommends what to change, and explains its thinking in the language a coaching staff uses.
            Give it eleven positions and a handful of passes and it returns pass networks, territorial maps, detected
            formations, role classifications, a press-resistance score, tactical patterns, a SWOT analysis, prioritised
            recommendations and a written report. It also simulates what-if scenarios and scouts individual players.
          </p>
          <div className="mt-5 flex flex-wrap gap-2">
            {["12 features", "3 input methods", "4 engine phases", "30+ node knowledge graph", "15+ SWOT rules", "No API key required"].map((t) => (
              <span key={t} className="chip border-brand/30 bg-brand/10 text-brand">{t}</span>
            ))}
          </div>
        </motion.section>

        {/* Pipeline */}
        <section>
          <h2 className="mb-1 text-xl font-bold text-white">The pipeline</h2>
          <p className="mb-4 text-sm text-text-secondary">Every feature is a slice of the same five-step loop.</p>
          <StaggerGrid className="grid gap-3 md:grid-cols-5" stagger={0.09}>
            {PIPELINE.map((step, i) => (
              <StaggerItem key={step.name} className="relative">
                <motion.div {...cardHover} className="glass h-full p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand/15 text-brand"><step.icon className="h-4 w-4" /></span>
                    <span className="text-xs font-bold text-text-muted">0{i + 1}</span>
                  </div>
                  <div className="text-base font-bold text-white">{step.name}</div>
                  <p className="mt-1 text-xs leading-relaxed text-text-secondary">{step.text}</p>
                </motion.div>
                {i < PIPELINE.length - 1 && (
                  <ArrowRight className="absolute -right-3 top-1/2 hidden h-4 w-4 -translate-y-1/2 text-brand/60 md:block" />
                )}
              </StaggerItem>
            ))}
          </StaggerGrid>
        </section>

        {/* Engine phases */}
        <section>
          <h2 className="mb-1 text-xl font-bold text-white">Four engine phases</h2>
          <p className="mb-4 text-sm text-text-secondary">Stateless Python modules; the orchestrator threads results from one into the next.</p>
          <StaggerGrid className="grid gap-4 md:grid-cols-2" stagger={0.08}>
            {PHASES.map((p) => (
              <StaggerItem key={p.name}>
                <motion.div {...cardHover} className="glass relative h-full overflow-hidden p-5">
                  <div className="absolute inset-y-0 left-0 w-1" style={{ background: p.color }} />
                  <div className="mb-2 flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-lg" style={{ background: `${p.color}22`, color: p.color }}><p.icon className="h-5 w-5" /></span>
                    <div>
                      <div className="text-[11px] font-bold uppercase tracking-widest" style={{ color: p.color }}>{p.phase}</div>
                      <div className="text-lg font-bold text-white">{p.name}</div>
                    </div>
                  </div>
                  <p className="text-sm leading-relaxed text-text-secondary">{p.text}</p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {p.modules.map((m) => <code key={m} className="rounded bg-white/5 px-2 py-0.5 text-[11px] text-text-secondary">{m}.py</code>)}
                  </div>
                </motion.div>
              </StaggerItem>
            ))}
          </StaggerGrid>
        </section>

        {/* Tech stack */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-white">Tech stack</h2>
          <StaggerGrid className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" stagger={0.07}>
            {STACK.map((s) => (
              <StaggerItem key={s.group}>
                <GlassCard className="h-full">
                  <div className="mb-3 flex items-center gap-2 text-sm font-bold text-white"><s.icon className="h-4 w-4 text-brand" />{s.group}</div>
                  <ul className="space-y-1.5">
                    {s.items.map((it) => <li key={it} className="flex items-center gap-2 text-sm text-text-secondary"><span className="h-1.5 w-1.5 rounded-full bg-brand/70" />{it}</li>)}
                  </ul>
                </GlassCard>
              </StaggerItem>
            ))}
          </StaggerGrid>
        </section>

        {/* Data credits */}
        <motion.section initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="glass p-6">
          <h2 className="mb-2 text-xl font-bold text-white">Demo match data</h2>
          <p className="max-w-3xl text-sm leading-relaxed text-text-secondary">
            The bundled demo fixtures (2022 World Cup final, 2005 and 2011 Champions League finals, the 2017 Clásico)
            are built from <a href="https://github.com/statsbomb/open-data" target="_blank" rel="noreferrer" className="text-brand hover:underline">StatsBomb open data</a>:
            each starter's position is their median event location and the passes are the real events. Data © StatsBomb,
            used under their non-commercial open-data licence with attribution. Two fixtures without public event data
            (Barcelona 4-3 Real Madrid 2025, Liverpool 7-0 Manchester United 2023) use real line-ups and scores with
            synthesised passes and are labelled "reconstructed" in the app.
          </p>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-text-secondary">
            Player Assessment draws on the same fixtures: ten real stat lines (Messi, Mbappé, Xavi, Gerrard, Kaká and
            others) counted from those events, normalised per 90 minutes. Distance covered and sprints are estimates,
            because event data carries no tracking. Simulation and Compare offer presets themed after each fixture's
            tactical identity; those are stylised what-ifs, not replays of the real matches.
          </p>
        </motion.section>

        {/* Author + CTA */}
        <motion.section initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-brand relative overflow-hidden p-6 sm:p-8">
          <div className="pitch-grid-bg pointer-events-none absolute inset-0 opacity-60" />
          <div className="relative flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 via-blue-600 to-violet-600 text-lg font-black text-white shadow-[0_0_30px_rgba(0,217,255,0.4)]">YY</div>
              <div>
                <div className="eyebrow mb-1">Built by</div>
                <div className="text-xl font-bold text-white">Yassin Youssef</div>
                <p className="text-sm text-text-secondary">Designed and engineered end-to-end: engine, API and interface.</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <a href={GITHUB_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-white/10">
                <Github className="h-4 w-4" /> View source
              </a>
              <Button icon={Gamepad2} onClick={() => onFeatureClick("full-match")}>Run the demo</Button>
            </div>
          </div>
        </motion.section>
      </div>
    </Page>
  );
}
