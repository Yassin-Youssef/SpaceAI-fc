/**
 * The twelve SpaceAI FC features, grouped by the area of the product they
 * belong to. The area decides the accent colour (see styles/theme.css).
 */
import {
  ScanSearch, Share2, Map, Columns4, Gauge, Waypoints, ListOrdered, MessageSquare, FileText,
  UserSearch, ArrowLeftRight, MonitorPlay, type LucideIcon,
} from "lucide-react";
import type { CSSProperties } from "react";

export type Section = "analysis" | "intelligence" | "advanced" | "core";

export interface Feature {
  id: string;
  icon: LucideIcon;
  name: string;
  /** One line, plain language: what you get back. */
  description: string;
  section: Exclude<Section, "core">;
}

export const SECTION_LABEL: Record<Feature["section"], string> = {
  analysis: "Analysis",
  intelligence: "Intelligence",
  advanced: "Advanced",
};

export const FEATURES: Feature[] = [
  { id: "full-match", icon: ScanSearch, name: "Full Match Analysis", description: "Every engine phase in one run: passes, space, shape, SWOT, recommendations and a written report.", section: "analysis" },
  { id: "pass-network", icon: Share2, name: "Pass Network", description: "Who passes to whom, who the team runs through, and which players are cut off.", section: "analysis" },
  { id: "space-control", icon: Map, name: "Space Control", description: "Voronoi and influence maps of which side owns each third of the pitch.", section: "analysis" },
  { id: "formation", icon: Columns4, name: "Formation Detection", description: "The average shape of both teams, read from player depth, with a confidence score.", section: "analysis" },
  { id: "press-resistance", icon: Gauge, name: "Press Resistance", description: "A 0–100 score for playing through pressure, plus the zones where passes break down.", section: "analysis" },
  { id: "patterns", icon: Waypoints, name: "Tactical Patterns", description: "Overlaps, compact blocks, wide overloads, high lines and low blocks, with the players involved.", section: "analysis" },
  { id: "strategy", icon: ListOrdered, name: "Strategy Recommendations", description: "High, medium and low priority changes, each with its reasoning and expected effect.", section: "intelligence" },
  { id: "ask-ai", icon: MessageSquare, name: "Ask SpaceAI", description: "Ask a tactical question; answers draw on your last analysis and the knowledge graph.", section: "intelligence" },
  { id: "explanation", icon: FileText, name: "Tactical Explanation", description: "A match report in plain language: what is happening, why it matters, what to change.", section: "intelligence" },
  { id: "player-assessment", icon: UserSearch, name: "Player Assessment", description: "An attribute radar, the role a player suits best, and a scouting report.", section: "advanced" },
  { id: "compare", icon: ArrowLeftRight, name: "Compare", description: "Simulate two tactical match-ups several times each and see which setup comes out ahead.", section: "advanced" },
  { id: "simulation", icon: MonitorPlay, name: "Simulation", description: "A 5v5 or 7v7 multi-agent match between two tactics, with a frame-by-frame replay.", section: "advanced" },
];

export const FEATURE_BY_ID: Record<string, Feature> = Object.fromEntries(FEATURES.map((f) => [f.id, f]));

/** Accent area for any view id, including the non-feature pages. */
export function sectionOf(view: string): Section {
  return FEATURE_BY_ID[view]?.section ?? "core";
}

const AREA_COLOUR: Record<Section, { name: string; on: string }> = {
  analysis: { name: "green", on: "#0d0d0d" },
  core: { name: "green", on: "#0d0d0d" },
  intelligence: { name: "blue", on: "#ffffff" },
  advanced: { name: "yellow", on: "#0d0d0d" },
};

/** Inline style that points the --section colours at an area's accent. */
export const sectionVar = (s: Section): CSSProperties => {
  const c = AREA_COLOUR[s];
  return { "--section": `var(--${c.name})`, "--section-fill": `var(--${c.name}-fill)`, "--section-on": c.on } as CSSProperties;
};
