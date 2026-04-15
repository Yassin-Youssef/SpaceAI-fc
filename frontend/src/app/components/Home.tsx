import { motion } from "motion/react";
import {
  BarChart3,
  Share2,
  Map,
  Shield,
  Zap,
  Grid3x3,
  Lightbulb,
  User,
  MessageSquare,
  GitCompare,
  Gamepad2,
  FileText,
  ArrowRight,
} from "lucide-react";
import type { UserProfile, SavedAnalysis } from "../../lib/types";



interface Feature {
  id: string;
  icon: any;
  name: string;
  description: string;
  emoji: string;
}

const features: Feature[] = [
  {
    id: "full-match",
    icon: BarChart3,
    emoji: "🏟️",
    name: "Full Match Analysis",
    description: "Complete tactical breakdown",
  },
  {
    id: "pass-network",
    icon: Share2,
    emoji: "🔗",
    name: "Pass Network",
    description: "Passing structure & key distributors",
  },
  {
    id: "space-control",
    icon: Map,
    emoji: "🗺️",
    name: "Space Control",
    description: "Territorial dominance mapping",
  },
  {
    id: "formation",
    icon: Shield,
    emoji: "📐",
    name: "Formation Detection",
    description: "Identify team shape & structure",
  },
  {
    id: "press-resistance",
    icon: Zap,
    emoji: "💪",
    name: "Press Resistance",
    description: "Measure pressing survival",
  },
  {
    id: "patterns",
    icon: Grid3x3,
    emoji: "🔍",
    name: "Tactical Patterns",
    description: "Detect overlaps, blocks, overloads",
  },
  {
    id: "strategy",
    icon: Lightbulb,
    emoji: "🎯",
    name: "Strategy Recommendations",
    description: "AI-powered tactical suggestions",
  },
  {
    id: "player-assessment",
    icon: User,
    emoji: "👤",
    name: "Player Assessment",
    description: "Scouting reports & radar charts",
  },
  {
    id: "ask-ai",
    icon: MessageSquare,
    emoji: "💬",
    name: "Ask SpaceAI",
    description: "Tactical Q&A with AI",
  },
  {
    id: "compare",
    icon: GitCompare,
    emoji: "⚖️",
    name: "Compare",
    description: "Side-by-side tactical comparison",
  },
  {
    id: "simulation",
    icon: Gamepad2,
    emoji: "🎮",
    name: "Simulation",
    description: "What-if tactical testing",
  },
  {
    id: "explanation",
    icon: FileText,
    emoji: "📝",
    name: "Tactical Explanation",
    description: "Full match analysis report",
  },
];

const recentAnalysesPlaceholder = [
  { id: "1", match_name: "Barcelona vs Real Madrid", feature: "Full Match Analysis", created_at: "2026-04-12T14:30:00Z" },
  { id: "2", match_name: "Man City vs Arsenal", feature: "Space Control", created_at: "2026-04-10T09:15:00Z" },
  { id: "3", match_name: "Bayern vs Dortmund", feature: "Pass Network", created_at: "2026-04-08T16:45:00Z" },
];

interface HomeProps {
  userName?: string;
  user?: UserProfile | null;
  recentAnalyses?: SavedAnalysis[];
  onFeatureClick?: (featureId: string) => void;
}

export function Home({ userName, user, recentAnalyses = recentAnalysesPlaceholder as any, onFeatureClick }: HomeProps) {
  const heroFeature = features[0];
  const gridFeatures = features.slice(1);

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto p-8 space-y-8">
        {/* Welcome Message */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <h1 className="text-4xl font-bold text-white mb-2">
            Welcome back, <span className="text-cyan-400">{user?.full_name?.split(" ")[0] ?? userName ?? "Manager"}</span>
          </h1>
          <p className="text-white/60">Ready to unlock tactical intelligence</p>
        </motion.div>

        {/* Hero Feature Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          onClick={() => onFeatureClick?.(heroFeature.id)}
          className="relative group cursor-pointer"
        >
          <div
            className="relative rounded-2xl p-8 backdrop-blur-xl border border-cyan-500/30 overflow-hidden transition-all duration-300 hover:border-cyan-500/50 hover:shadow-[0_0_40px_rgba(0,217,255,0.2)]"
            style={{
              background: `
                linear-gradient(135deg, rgba(0, 217, 255, 0.12) 0%, rgba(0, 217, 255, 0.05) 100%),
                url('data:image/svg+xml,<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100" fill="none"/><path d="M0,50 L100,50 M50,0 L50,100" stroke="rgba(0,217,255,0.1)" stroke-width="1"/></svg>')
              `,
              backgroundSize: "100% 100%, 50px 50px",
            }}
          >
            <div className="relative z-10 flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_40px_rgba(0,217,255,0.4)] group-hover:scale-110 transition-transform">
                  <span className="text-4xl">{heroFeature.emoji}</span>
                </div>
                <div>
                  <h2 className="text-3xl font-bold text-white mb-2">{heroFeature.name}</h2>
                  <p className="text-lg text-white/60">{heroFeature.description}</p>
                </div>
              </div>
              <ArrowRight className="w-8 h-8 text-cyan-400 group-hover:translate-x-2 transition-transform" />
            </div>

            {/* Glow effect on hover */}
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/0 via-cyan-500/5 to-cyan-500/0 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </motion.div>

        {/* Feature Grid */}
        <div className="grid grid-cols-3 gap-4">
          {gridFeatures.map((feature, index) => {
            const Icon = feature.icon;

            return (
              <motion.div
                key={feature.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 + index * 0.05 }}
                onClick={() => onFeatureClick?.(feature.id)}
                className="group cursor-pointer"
              >
                <div
                  className="relative rounded-xl p-6 backdrop-blur-xl border border-white/10 h-full transition-all duration-300 hover:border-cyan-500/40 hover:bg-white/5"
                  style={{
                    background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)",
                  }}
                >
                  {/* Icon */}
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-white/10 to-white/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                    <span className="text-2xl">{feature.emoji}</span>
                  </div>

                  {/* Content */}
                  <h3 className="text-base font-bold text-white mb-2 group-hover:text-cyan-400 transition-colors">
                    {feature.name}
                  </h3>
                  <p className="text-sm text-white/50 leading-relaxed">{feature.description}</p>

                  {/* Hover glow */}
                  <div className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
                    style={{
                      boxShadow: "inset 0 0 30px rgba(0, 217, 255, 0.1)",
                    }}
                  />
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Recent Analyses */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.8 }}
          className="pt-4"
        >
          <h2 className="text-xl font-bold text-white mb-4">Recent Analyses</h2>
          <div className="grid grid-cols-3 gap-4">
          {recentAnalyses.map((analysis: any, index: number) => (
              <motion.div
                key={analysis.id ?? index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.9 + index * 0.1 }}
                className="rounded-lg p-4 backdrop-blur-xl border border-white/10 hover:border-cyan-500/30 cursor-pointer transition-all group"
                style={{
                  background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)",
                }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-600/20 flex items-center justify-center">
                    <BarChart3 className="w-5 h-5 text-cyan-400" />
                  </div>
                  <span className="text-xs text-white/40">
                    {analysis.date ?? analysis.created_at?.slice(0, 10)}
                  </span>
                </div>
                <h3 className="font-bold text-white mb-1 group-hover:text-cyan-400 transition-colors">
                  {analysis.match ?? analysis.match_name}
                </h3>
                <p className="text-xs text-white/50">{analysis.feature}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
