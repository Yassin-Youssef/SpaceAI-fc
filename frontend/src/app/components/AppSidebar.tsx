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
  FileText,
  GitCompare,
  Gamepad2,
  Clock,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";
import type { UserProfile } from "../../lib/types";

interface NavItem {
  id: string;
  icon: any;
  label: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navSections: NavSection[] = [
  {
    title: "ANALYSIS",
    items: [
      { id: "full-match", icon: BarChart3, label: "Full Match Analysis" },
      { id: "pass-network", icon: Share2, label: "Pass Network" },
      { id: "space-control", icon: Map, label: "Space Control" },
      { id: "formation", icon: Shield, label: "Formation Detection" },
      { id: "press-resistance", icon: Zap, label: "Press Resistance" },
      { id: "patterns", icon: Grid3x3, label: "Tactical Patterns" },
    ],
  },
  {
    title: "INTELLIGENCE",
    items: [
      { id: "strategy", icon: Lightbulb, label: "Strategy Recommendations" },
      { id: "ask-ai", icon: MessageSquare, label: "Ask SpaceAI" },
      { id: "explanation", icon: FileText, label: "Tactical Explanation" },
    ],
  },
  {
    title: "ADVANCED",
    items: [
      { id: "player-assessment", icon: User, label: "Player Assessment" },
      { id: "compare", icon: GitCompare, label: "Compare" },
      { id: "simulation", icon: Gamepad2, label: "Simulation" },
    ],
  },
];

interface AppSidebarProps {
  activeItem?: string;
  onNavigate?: (id: string) => void;
  collapsed?: boolean;
  user?: UserProfile | null;
}

export function AppSidebar({ activeItem = "home", onNavigate, collapsed: controlledCollapsed, user }: AppSidebarProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const collapsed = controlledCollapsed ?? internalCollapsed;

  return (
    <motion.div
      className="relative h-full flex flex-col"
      animate={{ width: collapsed ? 80 : 280 }}
      transition={{ duration: 0.3 }}
    >
      {/* Glassmorphism Background */}
      <div
        className="absolute inset-0 backdrop-blur-2xl"
        style={{
          background: "linear-gradient(135deg, rgba(18, 24, 53, 0.95) 0%, rgba(10, 14, 39, 0.95) 100%)",
          boxShadow: "inset 0 0 40px rgba(0, 217, 255, 0.05), 0 0 60px rgba(0, 0, 0, 0.3)",
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

      {/* Content */}
      <div className="relative z-10 flex-1 flex flex-col overflow-hidden">
        {/* Logo Section */}
        <div className="px-6 py-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_30px_rgba(0,217,255,0.4)] shrink-0">
              <div className="text-white font-bold text-xl">S</div>
            </div>
            {!collapsed && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="font-bold text-white tracking-tight">
                  Space<span className="text-cyan-400">AI</span> FC
                </div>
              </motion.div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {/* Home */}
          <div>
            <button
              onClick={() => onNavigate?.("home")}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all group relative ${
                activeItem === "home"
                  ? "bg-cyan-500/20 text-cyan-400"
                  : "text-white/70 hover:text-white hover:bg-white/5"
              }`}
            >
              {activeItem === "home" && (
                <motion.div
                  layoutId="activeIndicator"
                  className="absolute left-0 top-0 bottom-0 w-1 bg-cyan-400 rounded-r-full shadow-[0_0_10px_rgba(0,217,255,0.6)]"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
              <BarChart3 className="w-5 h-5 shrink-0" />
              {!collapsed && <span className="text-sm font-medium">Dashboard</span>}
            </button>
          </div>

          {/* Feature Sections */}
          {navSections.map((section) => (
            <div key={section.title}>
              {!collapsed && (
                <div className="px-3 mb-2">
                  <div className="text-[10px] uppercase tracking-wider text-white/40 font-bold">{section.title}</div>
                </div>
              )}
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeItem === item.id;

                  return (
                    <button
                      key={item.id}
                      onClick={() => onNavigate?.(item.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all group relative ${
                        isActive
                          ? "bg-cyan-500/20 text-cyan-400"
                          : "text-white/70 hover:text-white hover:bg-white/5"
                      }`}
                    >
                      {isActive && (
                        <motion.div
                          layoutId="activeIndicator"
                          className="absolute left-0 top-0 bottom-0 w-1 bg-cyan-400 rounded-r-full shadow-[0_0_10px_rgba(0,217,255,0.6)]"
                          transition={{ type: "spring", stiffness: 300, damping: 30 }}
                        />
                      )}
                      <Icon className="w-5 h-5 shrink-0" />
                      {!collapsed && <span className="text-sm font-medium truncate">{item.label}</span>}

                      {/* Tooltip for collapsed state */}
                      {collapsed && (
                        <div className="absolute left-full ml-4 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                          <div className="bg-black/90 backdrop-blur-sm px-3 py-2 rounded-lg text-sm font-medium text-white border border-cyan-500/30">
                            {item.label}
                          </div>
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Divider */}
          <div className="border-t border-white/10 my-4" />

          {/* History & Settings */}
          <div className="space-y-1">
            <button
              onClick={() => onNavigate?.("history")}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all group relative ${
                activeItem === "history"
                  ? "bg-cyan-500/20 text-cyan-400"
                  : "text-white/70 hover:text-white hover:bg-white/5"
              }`}
            >
              {activeItem === "history" && (
                <motion.div
                  layoutId="activeIndicator"
                  className="absolute left-0 top-0 bottom-0 w-1 bg-cyan-400 rounded-r-full shadow-[0_0_10px_rgba(0,217,255,0.6)]"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
              <Clock className="w-5 h-5 shrink-0" />
              {!collapsed && <span className="text-sm font-medium">History</span>}
            </button>

            <button
              onClick={() => onNavigate?.("settings")}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all group relative ${
                activeItem === "settings"
                  ? "bg-cyan-500/20 text-cyan-400"
                  : "text-white/70 hover:text-white hover:bg-white/5"
              }`}
            >
              {activeItem === "settings" && (
                <motion.div
                  layoutId="activeIndicator"
                  className="absolute left-0 top-0 bottom-0 w-1 bg-cyan-400 rounded-r-full shadow-[0_0_10px_rgba(0,217,255,0.6)]"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
              <Settings className="w-5 h-5 shrink-0" />
              {!collapsed && <span className="text-sm font-medium">Settings</span>}
            </button>
          </div>
        </nav>

        {/* User Section */}
        <div className="border-t border-white/10 p-4">
          {!collapsed ? (
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shrink-0">
                <span className="text-sm font-bold text-white">
                  {user?.full_name ? user.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase() : "?"}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-white truncate">{user?.full_name ?? user?.email ?? "Guest"}</div>
                <div className="text-xs text-white/50">{user?.email ? "Manager" : "Not signed in"}</div>
              </div>
              <button className="p-2 hover:bg-white/5 rounded-lg transition-colors" onClick={() => onNavigate?.("logout")}>
                <LogOut className="w-4 h-4 text-white/50" />
              </button>
            </div>
          ) : (
            <div className="flex justify-center">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <span className="text-sm font-bold text-white">
                  {user?.full_name ? user.full_name[0].toUpperCase() : "?"}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={() => setInternalCollapsed(!collapsed)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-cyan-500 flex items-center justify-center shadow-[0_0_20px_rgba(0,217,255,0.4)] hover:scale-110 transition-transform z-20"
      >
        {collapsed ? <ChevronRight className="w-3 h-3 text-white" /> : <ChevronLeft className="w-3 h-3 text-white" />}
      </button>
    </motion.div>
  );
}
