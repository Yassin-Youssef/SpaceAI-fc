import { motion, AnimatePresence } from "motion/react";
import { ChevronDown, Play, Check, Database, PenLine, SlidersHorizontal, Package, PencilLine } from "lucide-react";
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { cn } from "../ui/utils";
import { springSoft, EASE_OUT } from "../../../lib/motion";

export interface PresetItem {
  id: string;
  title: string;
  subtitle: string;
  /** "statsbomb" | "reconstructed" | "sample" | "preset" — controls the badge */
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
  heading?: string;
  footer?: ReactNode;
}

function badge(kind?: string) {
  if (kind === "statsbomb") return { cls: "border-success/40 text-success", icon: Database, text: "StatsBomb data" };
  if (kind === "reconstructed") return { cls: "border-warning/40 text-warning", icon: PenLine, text: "Reconstructed" };
  if (kind === "sample") return { cls: "border-line-strong text-text-secondary", icon: Package, text: "Built-in sample" };
  return { cls: "border-section/40 text-section", icon: SlidersHorizontal, text: "Preset" };
}

/**
 * "Try demo" split button with a portalled menu (portalled to <body> so a
 * header's stacking context never clips it). The main click runs the
 * last-used item; the chevron lists all of them.
 */
export function PresetPicker({ items, storageKey, label = "Try demo:", onRun, onLoad, disabled, busyId, heading, footer }: PresetPickerProps) {
  const [open, setOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(() => {
    try { return localStorage.getItem(storageKey); } catch { return null; }
  });
  const [pos, setPos] = useState<{ top: number; right: number; section: string } | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (!open || !ref.current) return;
    const place = () => {
      const r = ref.current!.getBoundingClientRect();
      // The menu lives in <body>, so carry the page's accent over with it.
      const section = getComputedStyle(ref.current!).getPropertyValue("--section").trim();
      setPos({ top: r.bottom + 6, right: Math.max(8, window.innerWidth - r.right), section });
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
    <div ref={ref} className="relative max-w-full">
      <div className="flex h-11 max-w-full overflow-hidden rounded-md bg-section-fill text-section-on">
        <motion.button
          type="button"
          whileTap={disabled ? undefined : { scale: 0.98 }}
          disabled={disabled}
          onClick={() => choose(selected, true)}
          title={selected.subtitle}
          className="relative inline-flex min-w-0 items-center gap-2 px-4 text-sm font-bold transition-colors duration-150 hover:bg-black/10 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Play className="h-3.5 w-3.5 shrink-0" />
          <span className="truncate sm:max-w-[260px]"><span className="uppercase [font-stretch:112%]">{label}</span> {selected.title}</span>
          {busyId === selected.id && <span className="busy-bar" aria-hidden />}
        </motion.button>
        <button
          type="button"
          disabled={disabled}
          onClick={() => setOpen((o) => !o)}
          aria-haspopup="menu"
          aria-expanded={open}
          aria-label="Choose a different demo"
          className="inline-flex items-center border-l border-black/15 px-3 transition-colors duration-150 hover:bg-black/10 disabled:cursor-not-allowed disabled:opacity-50"
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
                initial={{ opacity: 0, scale: 0.97, y: -4 }}
                animate={{ opacity: 1, scale: 1, y: 0, transition: { duration: 0.16, ease: EASE_OUT } }}
                exit={{ opacity: 0, scale: 0.98, transition: { duration: 0.12, ease: EASE_OUT } }}
                style={{ position: "fixed", top: pos.top, right: pos.right, zIndex: 70, transformOrigin: "top right", ...(pos.section ? { ["--section" as string]: pos.section } : {}) }}
                className="w-[min(calc(100vw-16px),420px)] overflow-hidden rounded-lg border border-line-strong bg-surface-2 shadow-[0_16px_40px_rgba(0,0,0,0.14)]"
              >
                {heading && <div className="border-b border-line px-4 py-2.5 text-sm font-medium text-text-secondary">{heading}</div>}
                <ul className="max-h-[60vh] overflow-y-auto p-1">
                  {items.map((item) => {
                    const b = badge(item.kind);
                    const active = item.id === selected.id;
                    const busy = busyId === item.id;
                    return (
                      <li key={item.id} className={cn("rounded-md transition-colors duration-150 hover:bg-surface-3", active && "bg-surface-3/60")}>
                        <div className="flex items-center gap-2 px-3 py-2.5">
                          <button type="button" role="menuitem" onClick={() => choose(item, true)} disabled={disabled} className="min-w-0 flex-1 text-left">
                            <div className="flex items-center gap-2">
                              <span className="truncate text-sm font-semibold text-text-primary">{item.title}</span>
                              {active && <Check className="h-3.5 w-3.5 shrink-0 text-section" />}
                            </div>
                            <div className="truncate text-xs text-text-muted">{item.subtitle}</div>
                            <div className="mt-1.5 flex min-w-0 items-center gap-2">
                              <span className={cn("chip shrink-0", b.cls)}><b.icon className="h-3 w-3" />{b.text}</span>
                              {item.meta && <span className="truncate text-xs text-text-muted">{item.meta}</span>}
                            </div>
                          </button>
                          <div className="flex shrink-0 flex-col gap-1">
                            <button type="button" onClick={() => choose(item, true)} disabled={disabled} title="Load and run" aria-label={`Run ${item.title}`} className="press relative flex h-7 w-7 items-center justify-center overflow-hidden rounded-md bg-section-fill/15 text-section hover:bg-section-fill/25">
                              <Play className="h-3.5 w-3.5" />
                              {busy && <span className="busy-bar" aria-hidden />}
                            </button>
                            {onLoad && (
                              <button type="button" onClick={() => choose(item, false)} disabled={disabled} title="Fill the form only" aria-label={`Fill the form with ${item.title}`} className="press flex h-7 w-7 items-center justify-center rounded-md text-text-secondary hover:bg-surface-1 hover:text-text-primary">
                                <PencilLine className="h-3.5 w-3.5" />
                              </button>
                            )}
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>
                {footer && <div className="border-t border-line px-4 py-2.5 text-xs text-text-muted">{footer}</div>}
              </motion.div>
            )}
          </AnimatePresence>
        </div>,
        document.body
      )}
    </div>
  );
}
