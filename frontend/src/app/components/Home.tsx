import { motion } from "motion/react";
import {
  BarChart3, Share2, Map, Shield, Zap, Grid3x3, Lightbulb, User, MessageSquare, GitCompare, Gamepad2,
  FileText, ArrowRight, Clock, Info, Sparkles, type LucideIcon,
} from "lucide-react";
import type { UserProfile, SavedAnalysis } from "../../lib/types";
import { Page, StaggerGrid, StaggerItem, Button, EmptyState } from "./common/Primitives";
import { cardHover } from "../../lib/motion";

interface Feature {
  id: string;
  icon: LucideIcon;
  name: string;
  description: string;
  group: "Analysis" | "Intelligence" | "Advanced";
}

export const FEATURES: Feature[] = [
  { id: "full-match", icon: BarChart3, name: "Full Match Analysis", description: "Every engine phase in one run: pitch, passes, space, formations, SWOT, recommendations and a written report.", group: "Analysis" },
  { id: "pass-network", icon: Share2, name: "Pass Network", description: "Directed pass graph with centrality metrics, key distributor and weak links.", group: "Analysis" },
  { id: "space-control", icon: Map, name: "Space Control", description: "Voronoi and influence maps showing who owns each zone of the pitch.", group: "Analysis" },
  { id: "formation", icon: Shield, name: "Formation Detection", description: "Clustering on player depth to read the shape of both teams, with confidence.", group: "Analysis" },
  { id: "press-resistance", icon: Zap, name: "Press Resistance", description: "How well a side plays through pressure, scored 0–100 with vulnerable zones.", group: "Analysis" },
  { id: "patterns", icon: Grid3x3, name: "Tactical Patterns", description: "Overlaps, compact blocks, wide overloads, high lines and low blocks.", group: "Analysis" },
  { id: "strategy", icon: Lightbulb, name: "Strategy Recommendations", description: "Prioritised adjustments reasoned from SWOT and the knowledge graph.", group: "Intelligence" },
  { id: "ask-ai", icon: MessageSquare, name: "Ask SpaceAI", description: "Conversational tactical Q&A grounded in your latest analysis.", group: "Intelligence" },
  { id: "explanation", icon: FileText, name: "Tactical Explanation", description: "A natural-language match report from the template engine or an LLM.", group: "Intelligence" },
  { id: "player-assessment", icon: User, name: "Player Assessment", description: "Attribute radar, best role and scouting report from video, stats or ratings.", group: "Advanced" },
  { id: "compare", icon: GitCompare, name: "Compare", description: "Run two tactical match-ups side by side and see which setup wins.", group: "Advanced" },
  { id: "simulation", icon: Gamepad2, name: "Simulation", description: "Multi-agent 5v5 / 7v7 simulation with an animated replay.", group: "Advanced" },
];

interface HomeProps {
  user?: UserProfile | null;
  recentAnalyses?: SavedAnalysis[];
  onFeatureClick: (featureId: string) => void;
  onNavigate: (view: string) => void;
}

export function Home({ user, recentAnalyses = [], onFeatureClick, onNavigate }: HomeProps) {
  const hero = FEATURES[0];
  const HeroIcon = hero.icon;
  const groups: Feature["group"][] = ["Analysis", "Intelligence", "Advanced"];
  const firstName = user?.full_name?.split(" ")[0] ?? "Manager";

  return (
    <Page>
      <div className="space-y-8">
        {/* Welcome */}
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="eyebrow mb-2">Tactical intelligence · Sense → Understand → Reason → Act → Explain</div>
            <h1 className="text-3xl font-bold text-white sm:text-4xl">
              Welcome back, <span className="text-brand">{firstName}</span>
            </h1>
            <p className="mt-1 text-text-secondary">Pick a feature, load the El Clásico demo, and let the engine read the game.</p>
          </div>
          <Button variant="secondary" icon={Info} onClick={() => onNavigate("about")}>How it works</Button>
        </motion.div>

        {/* Hero */}
        <motion.button
          type="button"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.08 }}
          whileHover={{ y: -3 }}
          onClick={() => onFeatureClick(hero.id)}
          className="glass-brand group relative block w-full overflow-hidden p-6 text-left sm:p-8"
        >
          <div className="pitch-grid-bg pointer-events-none absolute inset-0 opacity-70" />
          <motion.div
            aria-hidden
            className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-brand/20 blur-3xl"
            animate={{ scale: [1, 1.15, 1], opacity: [0.5, 0.8, 0.5] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          />
          <div className="relative flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-5">
              <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-[0_0_40px_rgba(0,217,255,0.45)] transition-transform group-hover:scale-105 sm:h-20 sm:w-20">
                <HeroIcon className="h-8 w-8 text-white sm:h-10 sm:w-10" />
              </div>
              <div>
                <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-brand"><Sparkles className="h-3.5 w-3.5" /> Start here</div>
                <h2 className="text-2xl font-bold text-white sm:text-3xl">{hero.name}</h2>
                <p className="mt-1 max-w-xl text-sm text-text-secondary sm:text-base">{hero.description}</p>
              </div>
            </div>
            <ArrowRight className="hidden h-8 w-8 shrink-0 text-brand transition-transform group-hover:translate-x-2 sm:block" />
          </div>
        </motion.button>

        {/* Feature groups */}
        {groups.map((group, gi) => (
          <section key={group}>
            <div className="mb-3 flex items-center gap-3">
              <h2 className="text-lg font-bold text-white">{group}</h2>
              <span className="h-px flex-1 bg-white/10" />
            </div>
            <StaggerGrid className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" stagger={0.05}>
              {FEATURES.filter((f) => f.group === group && f.id !== hero.id).map((feature) => {
                const Icon = feature.icon;
                return (
                  <StaggerItem key={feature.id}>
                    <motion.button
                      type="button"
                      {...cardHover}
                      onClick={() => onFeatureClick(feature.id)}
                      className="glass group relative h-full w-full p-5 text-left transition-colors hover:border-brand/40"
                    >
                      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-gradient-to-br from-white/10 to-white/5 text-brand transition-all group-hover:from-brand/25 group-hover:to-brand/10">
                        <Icon className="h-5 w-5" />
                      </div>
                      <h3 className="mb-1 text-base font-bold text-white transition-colors group-hover:text-brand">{feature.name}</h3>
                      <p className="text-sm leading-relaxed text-text-secondary">{feature.description}</p>
                      <ArrowRight className="absolute right-4 top-5 h-4 w-4 text-text-muted opacity-0 transition-all group-hover:translate-x-1 group-hover:text-brand group-hover:opacity-100" />
                    </motion.button>
                  </StaggerItem>
                );
              })}
            </StaggerGrid>
            {gi < groups.length - 1 && <div className="h-2" />}
          </section>
        ))}

        {/* Recent analyses */}
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">Recent analyses</h2>
            {recentAnalyses.length > 0 && <button type="button" onClick={() => onNavigate("history")} className="text-sm font-semibold text-brand hover:underline">View all</button>}
          </div>
          {recentAnalyses.length > 0 ? (
            <StaggerGrid className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {recentAnalyses.slice(0, 3).map((a) => (
                <StaggerItem key={a.id}>
                  <button type="button" onClick={() => onNavigate("history")} className="glass group w-full p-4 text-left transition-colors hover:border-brand/40">
                    <div className="mb-2 flex items-start justify-between">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand/15 text-brand"><Clock className="h-4 w-4" /></div>
                      <span className="text-xs text-text-muted">{formatDate(a.created_at)}</span>
                    </div>
                    <h3 className="truncate font-bold text-white transition-colors group-hover:text-brand">{a.match_name}</h3>
                    <p className="text-xs text-text-secondary">{a.feature}</p>
                  </button>
                </StaggerItem>
              ))}
            </StaggerGrid>
          ) : (
            <EmptyState
              compact
              icon={Clock}
              title="No analyses saved yet"
              description={user?.isGuest ? "Sign in with a Supabase-backed account to keep a history of your analyses." : "Run any feature and press “Save to history” to see it here."}
            />
          )}
        </section>
      </div>
    </Page>
  );
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, { day: "2-digit", month: "short" });
  } catch {
    return iso.slice(0, 10);
  }
}
