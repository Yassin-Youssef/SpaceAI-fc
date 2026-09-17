import { motion, AnimatePresence } from "motion/react";
import { Sparkles, ChevronDown, Play, Download, Database, PenLine, Check } from "lucide-react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { listDemoMatches } from "../../../lib/api";
import type { DemoMatchSummary } from "../../../lib/types";
import { cn } from "../ui/utils";
import { springSoft } from "../../../lib/motion";

const LAST_KEY = "spaceai.demoMatch";

export function readLastDemoId(): string | null {
  try { return localStorage.getItem(LAST_KEY); } catch { return null; }
}

export function rememberDemoId(id: string): void {
  try { localStorage.setItem(LAST_KEY, id); } catch { /* ignore */ }
}

/** Fallback entry when the backend can't be reached. */
export const BUILTIN_DEMO: DemoMatchSummary = {
  id: "builtin",
  title: "FC Barcelona 2-1 Real Madrid",
  subtitle: "Built-in sample line-ups (no backend needed)",
  date: "2026-04-07",
  competition: "Sample fixture",
  team_a: "FC Barcelona",
  team_b: "Real Madrid",
  score: { a: 2, b: 1 },
  source_kind: "sample",
  players: 22,
  passes: 30,
};

interface DemoPickerProps {
  /** Run the analysis immediately with this fixture. */
  onRun: (match: DemoMatchSummary) => void;
  /** Only fill the form with this fixture. */
  onLoad: (match: DemoMatchSummary) => void;
  disabled?: boolean;
  busyId?: string | null;
}

/**
 * "Try Demo" split button: the main action runs the last-used fixture,
 * the chevron opens a menu of every bundled real match.
 */
export function DemoPicker({ onRun, onLoad, disabled, busyId }: DemoPickerProps) {
  const [matches, setMatches] = useState<DemoMatchSummary[]>([]);
  const [open, setOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(readLastDemoId());
  const [pos, setPos] = useState<{ top: number; right: number } | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // The menu is portalled to <body> so it is never clipped by, or painted
  // beneath, the header's stacking context.
  useLayoutEffect(() => {
    if (!open || !ref.current) return;
    const place = () => {
      const r = ref.current!.getBoundingClientRect();
      setPos({ top: r.bottom + 8, right: Math.max(8, window.innerWidth - r.right) });
    };
    place();
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => { window.removeEventListener("resize", place); window.removeEventListener("scroll", place, true); };
  }, [open]);

  useEffect(() => {
    let cancelled = false;
    listDemoMatches()
      .then((list) => { if (!cancelled) setMatches(list.length ? list : [BUILTIN_DEMO]); })
      .catch(() => { if (!cancelled) setMatches([BUILTIN_DEMO]); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      const t = e.target as Node;
      if (ref.current?.contains(t) || menuRef.current?.contains(t)) return;
      setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onDown); document.removeEventListener("keydown", onKey); };
  }, [open]);

  const selected = matches.find((m) => m.id === selectedId) ?? matches[0] ?? BUILTIN_DEMO;

  const choose = (m: DemoMatchSummary, run: boolean) => {
    setSelectedId(m.id);
    rememberDemoId(m.id);
    setOpen(false);
    (run ? onRun : onLoad)(m);
  };

  return (
    <div ref={ref} className="relative">
      <div className="flex overflow-hidden rounded-lg shadow-[0_0_0_1px_rgba(255,193,7,0.35)]">
        <motion.button
          type="button"
          whileHover={disabled ? undefined : { scale: 1.02 }}
          whileTap={disabled ? undefined : { scale: 0.97 }}
          transition={springSoft}
          disabled={disabled}
          onClick={() => choose(selected, true)}
          className="inline-flex items-center gap-2 bg-gradient-to-r from-amber-400 to-orange-500 px-4 py-2.5 text-sm font-semibold text-[#1a1200] transition-shadow hover:shadow-[0_0_28px_rgba(255,193,7,0.4)] disabled:cursor-not-allowed disabled:opacity-60"
          title={selected.subtitle}
        >
          <Sparkles className="h-4 w-4" />
          <span className="max-w-[200px] truncate">Try Demo · {selected.title}</span>
        </motion.button>
        <button
          type="button"
          disabled={disabled}
          onClick={() => setOpen((o) => !o)}
          aria-haspopup="menu"
          aria-expanded={open}
          aria-label="Choose a demo match"
          className="inline-flex items-center border-l border-black/20 bg-orange-500 px-2 text-[#1a1200] transition-colors hover:bg-orange-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <motion.span animate={{ rotate: open ? 180 : 0 }} transition={springSoft}><ChevronDown className="h-4 w-4" /></motion.span>
        </button>
      </div>

      {createPortal(
      <div ref={menuRef}>
      <AnimatePresence>
        {open && pos && (
          <motion.div
            role="menu"
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.16 }}
            style={{ position: "fixed", top: pos.top, right: pos.right, zIndex: 70 }}
            className="w-[min(92vw,420px)] overflow-hidden rounded-xl border border-white/10 bg-surface-2 shadow-2xl"
          >
            <div className="border-b border-white/10 px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-text-muted">Demo fixtures</div>
            <ul className="max-h-[60vh] overflow-y-auto p-1.5">
              {matches.map((m) => {
                const real = m.source_kind === "statsbomb";
                const active = m.id === selected.id;
                const busy = busyId === m.id;
                return (
                  <li key={m.id} className={cn("group rounded-lg transition-colors hover:bg-white/5", active && "bg-brand/10")}>
                    <div className="flex items-center gap-2 px-2.5 py-2">
                      <button type="button" role="menuitem" onClick={() => choose(m, true)} disabled={disabled} className="min-w-0 flex-1 text-left">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-sm font-semibold text-white">{m.title}</span>
                          {active && <Check className="h-3.5 w-3.5 shrink-0 text-brand" />}
                        </div>
                        <div className="truncate text-[11px] text-text-muted">{m.subtitle}</div>
                        <div className="mt-1 flex items-center gap-1.5">
                          <span className={cn("chip text-[10px]", real ? "border-success/40 bg-success/10 text-success" : m.source_kind === "sample" ? "border-white/10 bg-white/5 text-text-secondary" : "border-warning/40 bg-warning/10 text-warning")}>
                            {real ? <Database className="h-3 w-3" /> : <PenLine className="h-3 w-3" />}
                            {real ? "StatsBomb data" : m.source_kind === "sample" ? "Sample" : "Reconstructed line-ups"}
                          </span>
                          <span className="text-[10px] text-text-muted">{m.passes} passes{m.formation_a ? ` · ${m.formation_a} v ${m.formation_b}` : ""}</span>
                        </div>
                      </button>
                      <div className="flex shrink-0 flex-col gap-1">
                        <button type="button" onClick={() => choose(m, true)} disabled={disabled} title="Load and analyse" className="flex h-7 w-7 items-center justify-center rounded-md bg-brand/20 text-brand hover:bg-brand/30">
                          {busy ? <span className="h-3 w-3 animate-spin rounded-full border-2 border-brand/30 border-t-brand" /> : <Play className="h-3.5 w-3.5" />}
                        </button>
                        <button type="button" onClick={() => choose(m, false)} disabled={disabled} title="Load into the form only" className="flex h-7 w-7 items-center justify-center rounded-md bg-white/5 text-text-secondary hover:bg-white/10 hover:text-white">
                          <Download className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
            <div className="border-t border-white/10 px-4 py-2 text-[11px] text-text-muted">
              Real fixtures use StatsBomb open data (starters' median positions, real passes). Play = analyse now, ↓ = fill the form.
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      </div>,
      document.body)}
    </div>
  );
}
