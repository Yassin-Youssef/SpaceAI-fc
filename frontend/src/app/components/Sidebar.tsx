import { motion } from "motion/react";
import { BarChart3, Shield, Lightbulb, TrendingUp } from "lucide-react";

interface SidebarProps {
  activeSection?: string;
  onSectionChange?: (section: string) => void;
}

const navItems = [
  { id: "analysis", icon: BarChart3, label: "Match Analysis" },
  { id: "formation", icon: Shield, label: "Formation" },
  { id: "strategy", icon: Lightbulb, label: "Strategy Lab" },
  { id: "insights", icon: TrendingUp, label: "Insights" },
];

export function Sidebar({ activeSection = "analysis", onSectionChange }: SidebarProps) {
  return (
    <div className="relative h-full w-20 flex flex-col items-center py-6 gap-6">
      {/* Glassmorphism Background */}
      <div
        className="absolute inset-0 backdrop-blur-2xl rounded-r-2xl"
        style={{
          background: `
            linear-gradient(135deg,
              rgba(18, 24, 53, 0.8) 0%,
              rgba(18, 24, 53, 0.6) 100%
            )
          `,
          boxShadow: `
            inset 0 0 40px rgba(0, 217, 255, 0.05),
            0 0 60px rgba(0, 0, 0, 0.3)
          `,
          borderRight: "1px solid rgba(0, 217, 255, 0.2)",
        }}
      >
        {/* Star pattern watermark */}
        <div
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: `radial-gradient(circle at 25% 25%, #00d9ff 1px, transparent 1px),
                             radial-gradient(circle at 75% 75%, #00d9ff 1px, transparent 1px)`,
            backgroundSize: "30px 30px",
          }}
        />
      </div>

      {/* Logo */}
      <div className="relative z-10 w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_30px_rgba(0,217,255,0.4)]">
        <div className="text-white font-bold text-xl">S</div>
      </div>

      {/* Navigation */}
      <nav className="relative z-10 flex-1 flex flex-col gap-4">
        {navItems.map((item, index) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;

          return (
            <motion.button
              key={item.id}
              onClick={() => onSectionChange?.(item.id)}
              className={`relative w-14 h-14 rounded-xl flex items-center justify-center transition-all group ${
                isActive ? "bg-cyan-500/20" : "bg-white/5 hover:bg-white/10"
              }`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {/* Active indicator */}
              {isActive && (
                <motion.div
                  layoutId="activeIndicator"
                  className="absolute inset-0 border-2 border-cyan-500 rounded-xl"
                  style={{
                    boxShadow: "0 0 20px rgba(0, 217, 255, 0.4)",
                  }}
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}

              <Icon
                className={`w-5 h-5 transition-colors ${
                  isActive ? "text-cyan-400" : "text-white/60 group-hover:text-white/90"
                }`}
              />

              {/* Tooltip */}
              <div className="absolute left-full ml-4 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                <div className="bg-black/90 backdrop-blur-sm px-3 py-2 rounded-lg text-sm font-medium text-white border border-cyan-500/30">
                  {item.label}
                </div>
              </div>
            </motion.button>
          );
        })}
      </nav>

      {/* Status Indicator */}
      <div className="relative z-10 flex flex-col items-center gap-2">
        <div className="w-3 h-3 rounded-full bg-green-400 shadow-[0_0_10px_rgba(0,255,136,0.6)] animate-pulse" />
        <span className="text-[10px] text-white/40 font-medium">LIVE</span>
      </div>
    </div>
  );
}
