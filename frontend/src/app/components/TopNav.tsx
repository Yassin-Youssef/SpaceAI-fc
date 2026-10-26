import { motion, AnimatePresence } from "motion/react";
import { Menu, X, LogOut, Settings2 } from "lucide-react";
import { useEffect } from "react";
import type { UserProfile, HealthResponse } from "../../lib/types";
import { FEATURES, SECTION_LABEL, sectionOf, sectionVar, type Feature } from "../../lib/features";
import { cn } from "./ui/utils";
import { springSoft, EASE_OUT } from "../../lib/motion";

const AREAS: Feature["section"][] = ["analysis", "intelligence", "advanced"];
const firstOf = (area: Feature["section"]) => FEATURES.find((f) => f.section === area)!.id;

interface TopNavProps {
  activeItem: string;
  onNavigate: (id: string) => void;
  user?: UserProfile | null;
  health?: HealthResponse | null;
  healthError?: boolean;
  mobileOpen: boolean;
  onMobileOpen: () => void;
  onMobileClose: () => void;
}

/**
 * Black top bar (wordmark, areas, status, account) plus, inside an area,
 * a strip of that area's features. Replaces the old sidebar.
 */
export function TopNav({ activeItem, onNavigate, user, health, healthError, mobileOpen, onMobileOpen, onMobileClose }: TopNavProps) {
  const area = sectionOf(activeItem);
  const go = (id: string) => { onNavigate(id); onMobileClose(); };

  // Lock page scroll and close on Escape while the phone menu is open.
  useEffect(() => {
    if (!mobileOpen) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onMobileClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [mobileOpen, onMobileClose]);

  const status = healthError ? "Engine offline" : health ? (health.llm_available ? "Engine online, LLM connected" : "Engine online") : "Connecting";

  return (
    <>
      <header className="band shrink-0">
        <div className="flex h-14 items-center gap-6 px-4 sm:px-6 lg:px-10">
          <button type="button" onClick={() => go("home")} className="font-display shrink-0 text-xl leading-none text-white" aria-label="SpaceAI FC, overview">
            SPACEAI <span className="text-green-fill">FC</span>
          </button>

          <nav aria-label="Main" className="hidden h-full items-stretch gap-1 lg:flex">
            <TopLink label="Overview" active={activeItem === "home"} onClick={() => go("home")} />
            {AREAS.map((a) => (
              <TopLink key={a} label={SECTION_LABEL[a]} area={a} active={area === a} onClick={() => go(firstOf(a))} />
            ))}
            <TopLink label="History" active={activeItem === "history"} onClick={() => go("history")} />
            <TopLink label="How it works" active={activeItem === "about"} onClick={() => go("about")} />
          </nav>

          <div className="ml-auto flex items-center gap-1">
            <span className="mr-2 hidden items-center gap-2 text-sm text-text-muted xl:flex" title={health ? `Backend v${health.version}, ${health.llm_provider}` : undefined}>
              <span className={cn("h-2 w-2 rounded-full", healthError ? "bg-danger" : health ? "bg-green-fill" : "bg-yellow-fill")} />
              {status}
            </span>
            <button type="button" onClick={() => go("settings")} aria-label="Settings" title="Settings" className={cn("press hidden rounded-md p-2 hover:bg-surface-2 lg:block", activeItem === "settings" ? "text-white" : "text-text-muted hover:text-white")}>
              <Settings2 className="h-[18px] w-[18px]" />
            </button>
            <span className="hidden h-8 w-8 items-center justify-center rounded-full bg-surface-3 text-xs font-bold text-white lg:flex" title={user?.isGuest ? "Guest session" : user?.email ?? ""}>
              {initials(user)}
            </span>
            <button type="button" onClick={() => go("logout")} aria-label={user?.isGuest ? "Exit guest session" : "Sign out"} title={user?.isGuest ? "Exit guest session" : "Sign out"} className="press hidden rounded-md p-2 text-text-muted hover:bg-surface-2 hover:text-white lg:block">
              <LogOut className="h-[18px] w-[18px]" />
            </button>
            <button type="button" onClick={onMobileOpen} aria-label="Open menu" className="press rounded-md p-2 text-white hover:bg-surface-2 lg:hidden">
              <Menu className="h-5 w-5" />
            </button>
          </div>
        </div>
      </header>

      {area !== "core" && (
        <div className="shrink-0 border-b border-line bg-surface-1" style={sectionVar(area)}>
          <nav aria-label={`${SECTION_LABEL[area]} features`} className="flex items-stretch gap-1 overflow-x-auto px-4 sm:px-6 lg:px-10">
            {FEATURES.filter((f) => f.section === area).map((f) => {
              const active = activeItem === f.id;
              return (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => go(f.id)}
                  aria-current={active ? "page" : undefined}
                  className={cn("relative flex h-11 shrink-0 items-center gap-2 px-3 text-sm font-semibold transition-colors duration-150", active ? "text-text-primary" : "text-text-muted hover:text-text-primary")}
                >
                  <f.icon className="h-4 w-4" strokeWidth={2} />
                  {f.name}
                  {active && <motion.span layoutId="feature-tab" transition={springSoft} className="absolute inset-x-0 bottom-0 h-[3px] bg-section-fill" />}
                </button>
              );
            })}
          </nav>
        </div>
      )}

      {/* Phone menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            key="menu"
            role="dialog"
            aria-modal="true"
            aria-label="Menu"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0, transition: { duration: 0.22, ease: EASE_OUT } }}
            exit={{ opacity: 0, transition: { duration: 0.15 } }}
            className="band fixed inset-0 z-50 flex flex-col overflow-y-auto lg:hidden"
          >
            <div className="flex h-14 shrink-0 items-center justify-between px-4">
              <span className="font-display text-xl text-white">SPACEAI <span className="text-green-fill">FC</span></span>
              <button type="button" onClick={onMobileClose} aria-label="Close menu" className="press rounded-md p-2 text-white hover:bg-surface-2"><X className="h-5 w-5" /></button>
            </div>
            <nav aria-label="Main" className="flex-1 space-y-6 px-4 pb-8 pt-2">
              <MenuItem label="Overview" active={activeItem === "home"} onClick={() => go("home")} />
              {AREAS.map((a) => (
                <div key={a} style={sectionVar(a)}>
                  <span className="tag mb-2">{SECTION_LABEL[a]}</span>
                  {FEATURES.filter((f) => f.section === a).map((f) => (
                    <MenuItem key={f.id} label={f.name} active={activeItem === f.id} onClick={() => go(f.id)} />
                  ))}
                </div>
              ))}
              <div className="border-t border-line pt-4">
                <MenuItem label="History" active={activeItem === "history"} onClick={() => go("history")} />
                <MenuItem label="How it works" active={activeItem === "about"} onClick={() => go("about")} />
                <MenuItem label="Settings" active={activeItem === "settings"} onClick={() => go("settings")} />
                <MenuItem label={user?.isGuest ? "Exit guest session" : "Sign out"} active={false} onClick={() => go("logout")} />
              </div>
              <p className="flex items-center gap-2 text-sm text-text-muted">
                <span className={cn("h-2 w-2 rounded-full", healthError ? "bg-danger" : health ? "bg-green-fill" : "bg-yellow-fill")} />{status}
              </p>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

function TopLink({ label, active, onClick, area }: { label: string; active: boolean; onClick: () => void; area?: Feature["section"] }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      style={area ? sectionVar(area) : undefined}
      className={cn("relative flex items-center px-3 text-sm font-bold uppercase tracking-[0.02em] transition-colors duration-150 [font-stretch:112%]", active ? "text-white" : "text-text-muted hover:text-white")}
    >
      {label}
      {active && <motion.span layoutId="top-link" transition={springSoft} className="absolute inset-x-3 bottom-0 h-[3px] bg-section-fill" />}
    </button>
  );
}

function MenuItem({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} aria-current={active ? "page" : undefined} className={cn("font-display block w-full py-1.5 text-left text-2xl", active ? "text-section-fill" : "text-white")}>
      {label}
    </button>
  );
}

function initials(user?: UserProfile | null): string {
  if (!user) return "?";
  if (user.isGuest) return "G";
  const src = user.full_name || user.email || "?";
  return src.split(/[\s@.]+/).filter(Boolean).slice(0, 2).map((s) => s[0]?.toUpperCase() ?? "").join("") || "?";
}
