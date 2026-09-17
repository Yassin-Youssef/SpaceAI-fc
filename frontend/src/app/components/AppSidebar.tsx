import { motion, AnimatePresence } from "motion/react";
import {
  LayoutDashboard, BarChart3, Share2, Map, Shield, Zap, Grid3x3, Lightbulb, User, MessageSquare, FileText,
  GitCompare, Gamepad2, Clock, Settings, LogOut, ChevronLeft, ChevronRight, Info, X, type LucideIcon,
} from "lucide-react";
import { useEffect, useState } from "react";
import type { UserProfile, HealthResponse } from "../../lib/types";
import { cn } from "./ui/utils";
import { springSoft, staggerContainer, staggerItem } from "../../lib/motion";

interface NavItem { id: string; icon: LucideIcon; label: string }
interface NavSection { title: string; items: NavItem[] }

const navSections: NavSection[] = [
  {
    title: "Analysis",
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
    title: "Intelligence",
    items: [
      { id: "strategy", icon: Lightbulb, label: "Strategy Recommendations" },
      { id: "ask-ai", icon: MessageSquare, label: "Ask SpaceAI" },
      { id: "explanation", icon: FileText, label: "Tactical Explanation" },
    ],
  },
  {
    title: "Advanced",
    items: [
      { id: "player-assessment", icon: User, label: "Player Assessment" },
      { id: "compare", icon: GitCompare, label: "Compare" },
      { id: "simulation", icon: Gamepad2, label: "Simulation" },
    ],
  },
];

const footerItems: NavItem[] = [
  { id: "history", icon: Clock, label: "History" },
  { id: "about", icon: Info, label: "About" },
  { id: "settings", icon: Settings, label: "Settings" },
];

interface AppSidebarProps {
  activeItem: string;
  onNavigate: (id: string) => void;
  user?: UserProfile | null;
  health?: HealthResponse | null;
  healthError?: boolean;
  /** Mobile: whether the drawer is open */
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function AppSidebar({ activeItem, onNavigate, user, health, healthError, mobileOpen, onMobileClose }: AppSidebarProps) {
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try { return localStorage.getItem("spaceai.sidebar") === "collapsed"; } catch { return false; }
  });
  useEffect(() => {
    try { localStorage.setItem("spaceai.sidebar", collapsed ? "collapsed" : "open"); } catch { /* ignore */ }
  }, [collapsed]);

  const go = (id: string) => { onNavigate(id); onMobileClose(); };

  const content = (
    <div className="relative z-10 flex h-full flex-col overflow-hidden">
      {/* Logo */}
      <div className="flex items-center gap-3 border-b border-white/10 px-4 py-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-[0_0_30px_rgba(0,217,255,0.4)]">
          <svg viewBox="0 0 64 64" className="h-6 w-6" aria-hidden><circle cx="32" cy="32" r="22" fill="none" stroke="#fff" strokeWidth="4" /><path d="M32 14l8 6-3 10H27l-3-10z" fill="#fff" /><circle cx="32" cy="32" r="4" fill="#fff" /></svg>
        </div>
        {!collapsed && (
          <motion.div initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} className="min-w-0">
            <div className="truncate font-bold tracking-tight text-white">Space<span className="text-brand">AI</span> FC</div>
            <div className="truncate text-[11px] text-text-muted">Tactical intelligence</div>
          </motion.div>
        )}
        <button type="button" onClick={onMobileClose} className="ml-auto rounded-lg p-2 text-text-muted hover:bg-white/5 hover:text-white lg:hidden" aria-label="Close menu">
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Nav */}
      <motion.nav variants={staggerContainer(0.03, 0.05)} initial="hidden" animate="show" className="flex-1 space-y-3.5 overflow-y-auto px-3 py-3">
        <motion.div variants={staggerItem}>
          <NavButton item={{ id: "home", icon: LayoutDashboard, label: "Dashboard" }} active={activeItem === "home"} collapsed={collapsed} onClick={() => go("home")} />
        </motion.div>

        {navSections.map((section) => (
          <div key={section.title}>
            {!collapsed && <div className="eyebrow mb-1.5 px-3">{section.title}</div>}
            {collapsed && <div className="mx-3 mb-2 h-px bg-white/10" />}
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <motion.div key={item.id} variants={staggerItem}>
                  <NavButton item={item} active={activeItem === item.id} collapsed={collapsed} onClick={() => go(item.id)} />
                </motion.div>
              ))}
            </div>
          </div>
        ))}

        <div>
          <div className="mx-3 mb-2 h-px bg-white/10" />
          <div className="space-y-0.5">
            {footerItems.map((item) => (
              <motion.div key={item.id} variants={staggerItem}>
                <NavButton item={item} active={activeItem === item.id} collapsed={collapsed} onClick={() => go(item.id)} />
              </motion.div>
            ))}
          </div>
        </div>
      </motion.nav>

      {/* Status + user */}
      <div className="border-t border-white/10 px-3 py-2.5">
        <div className={cn("mb-1.5 flex items-center gap-2 rounded-lg px-2 py-1 text-[11px]", collapsed && "justify-center")} title={healthError ? "Backend unreachable" : health ? `Backend v${health.version} · ${health.llm_provider}` : "Checking backend…"}>
          <span className={cn("h-2 w-2 shrink-0 rounded-full", healthError ? "bg-danger" : health ? "bg-success shadow-[0_0_8px_rgba(47,229,143,0.8)]" : "animate-pulse bg-warning")} />
          {!collapsed && <span className="truncate text-text-muted">{healthError ? "Backend offline" : health ? `Engine online · ${health.llm_available ? "LLM" : "Knowledge graph"}` : "Connecting…"}</span>}
        </div>
        <div className={cn("flex items-center gap-3", collapsed && "justify-center")}>
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-pink-500 text-xs font-bold text-white">
            {initials(user)}
          </div>
          {!collapsed && (
            <>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium text-white">{user?.full_name ?? user?.email ?? "Guest"}</div>
                <div className="truncate text-[11px] text-text-muted">{user?.isGuest ? "Guest session" : user?.email ?? "Not signed in"}</div>
              </div>
              <button type="button" onClick={() => go("logout")} className="rounded-lg p-2 text-text-muted transition-colors hover:bg-white/5 hover:text-white" aria-label={user?.isGuest ? "Exit guest session" : "Sign out"} title={user?.isGuest ? "Exit guest session" : "Sign out"}>
                <LogOut className="h-4 w-4" />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <motion.aside
        className="relative hidden h-full shrink-0 flex-col lg:flex"
        animate={{ width: collapsed ? 84 : 272 }}
        transition={springSoft}
      >
        <div className="absolute inset-0 border-r border-brand/20 bg-sidebar backdrop-blur-2xl" style={{ boxShadow: "inset 0 0 40px rgba(0, 217, 255, 0.04)" }} />
        {content}
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          className="absolute -right-3 top-[72px] z-20 flex h-6 w-6 items-center justify-center rounded-full bg-brand text-[#0a0e27] shadow-[0_0_16px_rgba(0,217,255,0.5)] transition-transform hover:scale-110"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
        </button>
      </motion.aside>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div key="backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onMobileClose} className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden" />
            <motion.aside
              key="drawer"
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              transition={springSoft}
              className="fixed inset-y-0 left-0 z-50 flex w-[280px] max-w-[85vw] flex-col bg-surface-1 shadow-2xl lg:hidden"
            >
              {content}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

function NavButton({ item, active, collapsed, onClick }: { item: NavItem; active: boolean; collapsed: boolean; onClick: () => void }) {
  const Icon = item.icon;
  return (
    <button
      type="button"
      onClick={onClick}
      title={collapsed ? item.label : undefined}
      className={cn(
        "group relative flex w-full items-center gap-3 rounded-lg px-3 py-[7px] text-sm font-medium transition-colors",
        active ? "bg-brand/15 text-brand" : "text-text-secondary hover:bg-white/5 hover:text-white",
        collapsed && "justify-center px-0"
      )}
    >
      {active && (
        <motion.span layoutId="nav-indicator" transition={springSoft} className="absolute bottom-1.5 left-0 top-1.5 w-1 rounded-r-full bg-brand shadow-[0_0_10px_rgba(0,217,255,0.7)]" />
      )}
      <Icon className={cn("h-[18px] w-[18px] shrink-0 transition-transform group-hover:scale-110", active && "drop-shadow-[0_0_6px_rgba(0,217,255,0.6)]")} />
      {!collapsed && <span className="truncate">{item.label}</span>}
    </button>
  );
}

function initials(user?: UserProfile | null): string {
  if (!user) return "?";
  if (user.isGuest) return "G";
  const src = user.full_name || user.email || "?";
  return src.split(/[\s@.]+/).filter(Boolean).slice(0, 2).map((s) => s[0]?.toUpperCase() ?? "").join("") || "?";
}
