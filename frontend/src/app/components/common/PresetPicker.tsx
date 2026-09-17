import { motion, AnimatePresence } from "motion/react";
import { Sparkles, ChevronDown, Play, Download, Check, Database, PenLine, Wand2 } from "lucide-react";
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { cn } from "../ui/utils";
import { springSoft } from "../../../lib/motion";

export interface PresetItem {
  id: string;
  title: string;
  subtitle: string;
  /** "statsbomb" | "reconstructed" | "preset" — controls the badge */
  kind?: string;
  meta?: string;
}

interface PresetPickerProps {
  items: PresetItem[];
  storageKey: string;
  label?: string;
  onRun: (item: PresetItem) => void;
  onLoad?: (item: PresetItem) => void;
  disabled?: boolean;
  busyId?: string | null;
  footer?: ReactNode;
}

function badge(kind?: string) {
  if (kind === "statsbomb") return { cls: "border-success/40 bg-success/10 text-success", icon: Database, text: "StatsBomb data" };
  if (kind === "reconstructed") return { cls: "border-warning/40 bg-warning/10 text-warning", icon: PenLine, text: "Reconstructed" };
  return { cls: "border-brand/40 bg-brand/10 text-brand", icon: Wand2, text: "Preset" };
}

/**
 * Generic "Try Demo" split button with a portalled menu.
 * Main click runs the last-used preset; the chevron lists all of them.
 */
export function PresetPicker({ items, storageKey, label = "Try Demo", onRun, onLoad, disabled, busyId, footer }: PresetPickerProps) {
  const [open, setOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(() => {
    try { return localStorage.getItem(storageKey); } catch { return null; }
  });
  const [pos, setPos] = useState<{ top: number; right: number } | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

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

  const selected = items.find((i) => i.id === selectedId) ?? items[0];
  if (!selected) return null;

  const choose = (item: PresetItem, run: boolean) => {
    setSelectedId(item.id);
    try { localStorage.setItem(storageKey, item.id); } catch { /* ignore */ }
    setOpen(false);
    if (run) onRun(item); else onLoad?.(item);
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
          title={selected.subtitle}
          className="inline-flex items-center gap-2 bg-gradient-to-r from-amber-400 to-orange-500 px-4 py-2.5 text-sm font-semibold text-[#1a1200] transition-shadow hover:shadow-[0_0_28px_rgba(255,193,7,0.4)] disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Sparkles className="h-4 w-4" />
          <span className="max-w-[220px] truncate">{label} · {selected.title}</span>
        </motion.button>
        <button
          type="button"
          disabled={disabled}
          onClick={() => setOpen((o) => !o)}
          aria-haspopup="menu"
          aria-expanded={open}
          aria-label={`Choose a ${label.toLowerCase()} preset`}
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
                <ul className="max-h-[60vh] overflow-y-auto p-1.5">
                  {items.map((item) => {
                    const b = badge(item.kind);
                    const active = item.id === selected.id;
                    const busy = busyId === item.id;
                    return (
                      <li key={item.id} className={cn("rounded-lg transition-colors hover:bg-white/5", active && "bg-brand/10")}>
                        <div className="flex items-center gap-2 px-2.5 py-2">
                          <button type="button" role="menuitem" onClick={() => choose(item, true)} disabled={disabled} className="min-w-0 flex-1 text-left">
                            <div className="flex items-center gap-2">
                              <span className="truncate text-sm font-semibold text-white">{item.title}</span>
                              {active && <Check className="h-3.5 w-3.5 shrink-0 text-brand" />}
                            </div>
                            <div className="truncate text-[11px] text-text-muted">{item.subtitle}</div>
                            <div className="mt-1 flex items-center gap-1.5">
                              <span className={cn("chip text-[10px]", b.cls)}><b.icon className="h-3 w-3" />{b.text}</span>
                              {item.meta && <span className="truncate text-[10px] text-text-muted">{item.meta}</span>}
                            </div>
                          </button>
                          <div className="flex shrink-0 flex-col gap-1">
                            <button type="button" onClick={() => choose(item, true)} disabled={disabled} title="Load and run" className="flex h-7 w-7 items-center justify-center rounded-md bg-brand/20 text-brand hover:bg-brand/30">
                              {busy ? <span className="h-3 w-3 animate-spin rounded-full border-2 border-brand/30 border-t-brand" /> : <Play className="h-3.5 w-3.5" />}
                            </button>
                            {onLoad && (
                              <button type="button" onClick={() => choose(item, false)} disabled={disabled} title="Load into the form only" className="flex h-7 w-7 items-center justify-center rounded-md bg-white/5 text-text-secondary hover:bg-white/10 hover:text-white">
                                <Download className="h-3.5 w-3.5" />
                              </button>
                            )}
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>
                {footer && <div className="border-t border-white/10 px-4 py-2 text-[11px] text-text-muted">{footer}</div>}
              </motion.div>
            )}
          </AnimatePresence>
        </div>,
        document.body
      )}
    </div>
  );
}
