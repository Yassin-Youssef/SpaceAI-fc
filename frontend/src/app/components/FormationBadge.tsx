import { motion } from "motion/react";
import { Users } from "lucide-react";

interface FormationBadgeProps {
  formation: string;
  style?: string;
}

export function FormationBadge({ formation = "4-3-3", style = "Attacking" }: FormationBadgeProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="absolute top-4 left-4 z-10"
    >
      <div
        className="flex items-center gap-3 px-4 py-3 rounded-xl backdrop-blur-xl border border-cyan-500/30"
        style={{
          background: "linear-gradient(135deg, rgba(0, 217, 255, 0.12) 0%, rgba(0, 217, 255, 0.05) 100%)",
          boxShadow: "0 0 30px rgba(0, 217, 255, 0.2)",
        }}
      >
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_20px_rgba(0,217,255,0.4)]">
          <Users className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="text-xs text-white/50 uppercase tracking-wider font-medium">Formation Detected</div>
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-white tracking-tight">{formation}</span>
            <span className="text-xs text-cyan-400 font-medium px-2 py-0.5 rounded bg-cyan-500/20 border border-cyan-500/30">
              {style}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
