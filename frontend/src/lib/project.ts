/** Facts about SpaceAI FC shown on the Overview and How it works pages. */
import { Eye, Layers, Brain, Play, MessageSquareText, type LucideIcon } from "lucide-react";
import type { Section } from "./features";

export const GITHUB_URL = "https://github.com/Yassin-Youssef/SpaceAI-fc";

export interface PipelineStep {
  icon: LucideIcon;
  name: string;
  text: string;
  /** Product area the step feeds; decides its colour. */
  section: Section;
}

export const PIPELINE: PipelineStep[] = [
  { icon: Eye, name: "Sense", text: "Take in player positions and passes: typed in, tracked from video, or uploaded as a dataset.", section: "analysis" },
  { icon: Layers, name: "Understand", text: "Detect formations and roles, score press resistance, map space, spot patterns.", section: "analysis" },
  { icon: Brain, name: "Reason", text: "Query a tactical knowledge graph with SWOT rules to judge what is working and what is not.", section: "intelligence" },
  { icon: Play, name: "Act", text: "Rank changes by priority, then test tactics in simulation before committing to them.", section: "advanced" },
  { icon: MessageSquareText, name: "Explain", text: "Write it up for the coaching staff, from templates or a language model.", section: "intelligence" },
];

export interface EnginePhase {
  name: string;
  text: string;
  modules: string[];
}

export const PHASES: EnginePhase[] = [
  {
    name: "Perception",
    text: "A directed pass graph with degree, betweenness and eigenvector centrality, and two spatial models (Voronoi cells and Gaussian influence) that give zone-by-zone control.",
    modules: ["pass_network", "space_control", "pitch"],
  },
  {
    name: "Understanding",
    text: "Clustering on player depth reads each team's shape; a rule-based classifier assigns sub-roles such as false nine or inverted winger; press resistance and pattern detection measure how the shape behaves.",
    modules: ["formation_detection", "role_classifier", "press_resistance", "pattern_detection"],
  },
  {
    name: "Intelligence",
    text: "A knowledge graph of 30+ nodes links formations, situations and counter-strategies. Fifteen SWOT rules query it, a recommender ranks the actions, and an explanation layer writes the briefing.",
    modules: ["knowledge_graph", "tactical_reasoning", "strategy_recommender", "explanation_layer"],
  },
  {
    name: "Advanced AI",
    text: "Optional: YOLOv8 with a homography turns footage into pitch coordinates, a PPO agent learns nine tactical decisions in a Gymnasium environment, and a multi-agent simulation plays out 5v5 and 7v7 scenarios.",
    modules: ["video_analyzer", "rl_coach", "simulation"],
  },
];

export const STACK: Array<{ group: string; items: string[] }> = [
  { group: "Engine", items: ["Python", "NumPy", "SciPy", "NetworkX", "scikit-learn", "mplsoccer"] },
  { group: "API", items: ["FastAPI", "Pydantic v2", "Uvicorn", "slowapi", "python-docx"] },
  { group: "Interface", items: ["React 18", "TypeScript", "Vite", "Tailwind CSS v4", "Radix UI", "Motion", "Recharts"] },
  { group: "Data and models", items: ["StatsBomb open data", "Supabase", "OpenRouter / Anthropic", "YOLOv8", "OpenCV", "Stable-Baselines3"] },
];
