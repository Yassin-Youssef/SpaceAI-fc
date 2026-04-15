import { motion } from "motion/react";
import { AlertTriangle, Zap, CheckCircle2 } from "lucide-react";

interface Weakness {
  id: number;
  area: string;
  severity: "high" | "medium" | "low";
  description: string;
}

interface Recommendation {
  id: number;
  action: string;
  impact: string;
  confidence: number;
}

const mockWeaknesses: Weakness[] = [
  {
    id: 1,
    area: "Left Wing Defense",
    severity: "high",
    description: "Opposition RW exploiting space behind LB with 73% success rate",
  },
  {
    id: 2,
    area: "Central Midfield",
    severity: "medium",
    description: "Low press resistance in middle third, 12 turnovers in 30min",
  },
  {
    id: 3,
    area: "High Line",
    severity: "medium",
    description: "Defensive line averaging 48m, vulnerable to through balls",
  },
];

const mockRecommendations: Recommendation[] = [
  {
    id: 1,
    action: "Shift to 4-2-3-1",
    impact: "Add defensive midfielder to shield back four",
    confidence: 87,
  },
  {
    id: 2,
    action: "Push LB deeper",
    impact: "Reduce space exploitation on left flank",
    confidence: 92,
  },
  {
    id: 3,
    action: "Lower defensive line 5m",
    impact: "Compress space, reduce through-ball risk",
    confidence: 78,
  },
];

export function AIReasoningPanel() {
  return (
    <div className="relative h-full w-96 flex flex-col gap-4 p-6 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-[0_0_20px_rgba(123,97,255,0.4)]">
          <Zap className="w-4 h-4 text-white" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-white">Tactical Intelligence</h2>
          <p className="text-xs text-white/50">Real-time AI Analysis</p>
        </div>
      </div>

      {/* Identified Weaknesses */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wide">Identified Weaknesses</h3>
        </div>

        <div className="space-y-2">
          {mockWeaknesses.map((weakness, index) => (
            <motion.div
              key={weakness.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="relative group"
            >
              {/* Broadcast-style card */}
              <div
                className="relative rounded-lg p-3 backdrop-blur-xl border cursor-pointer transition-all hover:scale-[1.02]"
                style={{
                  background: "linear-gradient(135deg, rgba(255, 71, 87, 0.08) 0%, rgba(255, 71, 87, 0.03) 100%)",
                  borderColor:
                    weakness.severity === "high"
                      ? "rgba(255, 71, 87, 0.4)"
                      : weakness.severity === "medium"
                      ? "rgba(255, 193, 61, 0.4)"
                      : "rgba(255, 255, 255, 0.2)",
                  boxShadow:
                    weakness.severity === "high"
                      ? "0 0 20px rgba(255, 71, 87, 0.2)"
                      : weakness.severity === "medium"
                      ? "0 0 20px rgba(255, 193, 61, 0.2)"
                      : "none",
                }}
              >
                {/* Severity badge */}
                <div className="flex items-start justify-between mb-1.5">
                  <span className="text-xs font-bold text-white uppercase tracking-wider">{weakness.area}</span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      weakness.severity === "high"
                        ? "bg-red-500/20 text-red-400"
                        : weakness.severity === "medium"
                        ? "bg-yellow-500/20 text-yellow-400"
                        : "bg-blue-500/20 text-blue-400"
                    }`}
                  >
                    {weakness.severity.toUpperCase()}
                  </span>
                </div>
                <p className="text-xs text-white/70 leading-relaxed">{weakness.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Strategy Recommendations */}
      <div className="space-y-3 mt-4">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-green-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wide">Strategy Recommendations</h3>
        </div>

        <div className="space-y-2">
          {mockRecommendations.map((rec, index) => (
            <motion.div
              key={rec.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + index * 0.1 }}
              className="relative group"
            >
              {/* Broadcast-style card */}
              <div
                className="relative rounded-lg p-3 backdrop-blur-xl border border-cyan-500/30 cursor-pointer transition-all hover:scale-[1.02] hover:border-cyan-500/50"
                style={{
                  background: "linear-gradient(135deg, rgba(0, 217, 255, 0.08) 0%, rgba(0, 217, 255, 0.03) 100%)",
                  boxShadow: "0 0 20px rgba(0, 217, 255, 0.1)",
                }}
              >
                <div className="flex items-start justify-between mb-1.5">
                  <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">{rec.action}</span>
                  <div className="flex items-center gap-1">
                    <div className="w-12 h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-cyan-500 to-green-400"
                        initial={{ width: 0 }}
                        animate={{ width: `${rec.confidence}%` }}
                        transition={{ delay: 0.5 + index * 0.1, duration: 0.8 }}
                      />
                    </div>
                    <span className="text-[10px] font-bold text-green-400">{rec.confidence}%</span>
                  </div>
                </div>
                <p className="text-xs text-white/70 leading-relaxed">{rec.impact}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* AI Status */}
      <div className="mt-auto pt-4 border-t border-white/10">
        <div className="flex items-center gap-2 text-xs text-white/50">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_10px_rgba(0,217,255,0.6)]" />
          <span>AI reasoning engine active • Updated 2s ago</span>
        </div>
      </div>
    </div>
  );
}
