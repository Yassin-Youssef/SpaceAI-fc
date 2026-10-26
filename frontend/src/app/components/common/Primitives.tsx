/**
 * Small shared building blocks: page shell, headers, panels, buttons,
 * stat tiles, empty states, collapsible sections, badges, skeletons.
 */
import { motion, AnimatePresence, useReducedMotion } from "motion/react";
import { ArrowLeft, ChevronDown, type LucideIcon } from "lucide-react";
import { useState, type ReactNode, type ButtonHTMLAttributes, type RefObject } from "react";
import { cn } from "../ui/utils";
import { pressable, staggerContainer, staggerItem, springSoft, EASE_OUT, crossfade } from "../../../lib/motion";
import { AnimatedNumber } from "./AnimatedNumber";

// ── Layout ──────────────────────────────────────────────────────

export function Page({ children, width = "max-w-7xl", scrollRef }: { children: ReactNode; width?: string; scrollRef?: RefObject<HTMLDivElement> }) {
  return (
    <div ref={scrollRef} className="h-full overflow-y-auto overflow-x-hidden">
      <div className={cn("mx-auto w-full px-4 pb-16 pt-6 sm:px-6 sm:pt-8 lg:px-10", width)}>{children}</div>
    </div>
  );
}

interface PageHeaderProps {
  /** Area tag shown above the title, e.g. "Analysis". */
  area?: string;
  title: string;
  description: string;
  actions?: ReactNode;
}

/** Poster-style page title: area tag, huge headline, one line of context. */
export function PageHeader({ area, title, description, actions }: PageHeaderProps) {
  return (
    <header className="flex flex-col gap-5 border-b-2 border-text-primary pb-6 lg:flex-row lg:items-end lg:justify-between">
      <div className="min-w-0">
        {area && <span className="tag mb-3">{area}</span>}
        <h1 className="text-4xl text-text-primary sm:text-6xl">{title}</h1>
        <p className="mt-3 max-w-2xl text-base text-text-secondary">{description}</p>
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}

/** Compact header used on results views, with a back control. */
export function ResultsHeader({ title, context, onBack, right }: { title: ReactNode; context: string; onBack: () => void; right?: ReactNode }) {
  return (
    <header className="flex flex-col gap-3 border-b-2 border-text-primary pb-5 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onBack}
          className="press flex h-11 w-11 shrink-0 items-center justify-center rounded-md border-2 border-text-primary bg-surface-1 text-text-primary hover:bg-text-primary hover:text-surface-1"
          aria-label="Back to inputs"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="min-w-0">
          <span className="tag">{context}</span>
          <h1 className="mt-1.5 truncate text-2xl text-text-primary sm:text-4xl">{title}</h1>
        </div>
      </div>
      {right && <div className="flex shrink-0 flex-wrap items-center gap-2">{right}</div>}
    </header>
  );
}

/**
 * Full-bleed black broadcast band. Breaks out of the page column to the
 * viewport edges; its content stays aligned with the page column.
 */
export function Band({ children, className, inner = "max-w-7xl" }: { children: ReactNode; className?: string; inner?: string }) {
  return (
    <section className={cn("band relative left-1/2 w-screen -translate-x-1/2", className)}>
      <div className={cn("mx-auto w-full px-4 sm:px-6 lg:px-10", inner)}>{children}</div>
    </section>
  );
}

export function SectionTitle({ children, hint, right }: { children: ReactNode; hint?: string; right?: ReactNode }) {
  return (
    <div className="mb-4 flex items-end justify-between gap-3">
      <div>
        <h2 className="text-xl text-text-primary">{children}</h2>
        {hint && <p className="text-sm text-text-muted">{hint}</p>}
      </div>
      {right}
    </div>
  );
}

// ── Panels ──────────────────────────────────────────────────────

export function Panel({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("panel p-4 sm:p-5", className)}>{children}</div>;
}

/** Container whose direct children animate in with a stagger. */
export function StaggerGrid({ children, className, stagger = 0.05 }: { children: ReactNode; className?: string; stagger?: number }) {
  return (
    <motion.div variants={staggerContainer(stagger)} initial="hidden" animate="show" className={className}>
      {children}
    </motion.div>
  );
}

export function StaggerItem({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <motion.div variants={staggerItem} className={className}>
      {children}
    </motion.div>
  );
}

/** Swaps a skeleton for real content with a crossfade. */
export function LoadSwap({ loading, skeleton, children }: { loading: boolean; skeleton: ReactNode; children: ReactNode }) {
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div key={loading ? "skeleton" : "content"} variants={crossfade} initial="hidden" animate="show" exit="exit">
        {loading ? skeleton : children}
      </motion.div>
    </AnimatePresence>
  );
}

// ── Collapsible section ─────────────────────────────────────────

interface CollapsibleProps {
  title: string;
  subtitle?: string;
  icon?: LucideIcon;
  defaultOpen?: boolean;
  badge?: ReactNode;
  children: ReactNode;
}

export function Collapsible({ title, subtitle, icon: Icon, defaultOpen = true, badge, children }: CollapsibleProps) {
  const [open, setOpen] = useState(defaultOpen);
  const reduce = useReducedMotion();
  return (
    <section className="panel overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-surface-2 sm:px-5"
      >
        {Icon && <Icon className="h-5 w-5 shrink-0 text-section" strokeWidth={2} />}
        <span className="min-w-0 flex-1">
          <span className="block truncate font-display text-xl text-text-primary">{title}</span>
          {subtitle && <span className="block truncate text-sm text-text-muted">{subtitle}</span>}
        </span>
        {badge}
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={springSoft} className="text-text-muted">
          <ChevronDown className="h-4 w-4" />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="content"
            initial={reduce ? false : { height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={reduce ? undefined : { height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: EASE_OUT }}
            className="overflow-hidden"
          >
            <div className="border-t border-line px-4 py-5 sm:px-5">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}

// ── Buttons ─────────────────────────────────────────────────────

type Variant = "primary" | "secondary" | "ghost" | "danger" | "accent";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  icon?: LucideIcon;
  block?: boolean;
}

const variantClasses: Record<Variant, string> = {
  primary: "bg-text-primary text-surface-1 hover:bg-section-fill hover:text-section-on",
  secondary: "border-2 border-text-primary bg-transparent text-text-primary hover:bg-text-primary hover:text-surface-1",
  ghost: "text-text-secondary hover:bg-surface-2 hover:text-text-primary",
  danger: "bg-danger text-white hover:brightness-110",
  accent: "bg-section-fill text-section-on hover:bg-text-primary hover:text-surface-1",
};

const sizeClasses = {
  sm: "h-8 px-3 text-sm gap-1.5",
  md: "h-10 px-4 text-sm gap-2",
  lg: "h-12 px-6 text-base gap-2.5 uppercase tracking-[0.02em] [font-stretch:112%]",
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon: Icon,
  block = false,
  className,
  children,
  disabled,
  ...rest
}: ButtonProps) {
  const isDisabled = disabled || loading;
  return (
    <motion.button
      {...(isDisabled ? {} : pressable)}
      className={cn(
        "relative inline-flex items-center justify-center overflow-hidden rounded-md font-bold transition-[background-color,border-color,color,filter] duration-150 disabled:cursor-not-allowed",
        variantClasses[variant],
        sizeClasses[size],
        block && "w-full",
        disabled && !loading && "opacity-50",
        className
      )}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      {...(rest as object)}
    >
      {Icon && <Icon className="h-4 w-4 shrink-0" strokeWidth={2} />}
      {children}
      {loading && <span className="busy-bar" aria-hidden />}
    </motion.button>
  );
}

// ── Stat tile ───────────────────────────────────────────────────

interface StatTileProps {
  label: string;
  value: number | string;
  suffix?: string;
  decimals?: number;
  tone?: "section" | "teamA" | "teamB" | "success" | "warning" | "neutral";
  hint?: string;
  className?: string;
}

const toneColor: Record<NonNullable<StatTileProps["tone"]>, string> = {
  section: "text-section",
  teamA: "text-team-a",
  teamB: "text-team-b",
  success: "text-success",
  warning: "text-warning",
  neutral: "text-text-primary",
};

export function StatTile({ label, value, suffix = "", decimals = 0, tone = "section", hint, className }: StatTileProps) {
  return (
    <div className={cn("tile px-4 pb-4 pt-3", className)}>
      <div className="truncate text-sm font-semibold text-text-secondary">{label}</div>
      <div className={cn("font-num mt-1 text-6xl leading-none", toneColor[tone])}>
        {typeof value === "number" ? <AnimatedNumber value={value} decimals={decimals} suffix={suffix} /> : value}
      </div>
      {hint && <div className="mt-1.5 truncate text-xs text-text-muted">{hint}</div>}
    </div>
  );
}

// ── Empty state ─────────────────────────────────────────────────

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
  compact?: boolean;
}

export function EmptyState({ icon: Icon, title, description, action, compact = false }: EmptyStateProps) {
  return (
    <div className={cn("rounded-md border border-dashed border-line-strong", compact ? "p-6" : "p-8 sm:p-12")}>
      <div className="flex max-w-lg flex-col items-start gap-3">
        <Icon className="h-6 w-6 text-section" strokeWidth={1.75} />
        <div>
          <h3 className="text-xl text-text-primary">{title}</h3>
          <p className="mt-1 text-sm text-text-secondary">{description}</p>
        </div>
        {action && <div className="mt-2">{action}</div>}
      </div>
    </div>
  );
}

// ── Badges and bars ─────────────────────────────────────────────

export function PriorityBadge({ priority }: { priority: string }) {
  const p = priority.toLowerCase();
  const cls =
    p === "high"
      ? "bg-danger text-white"
      : p === "medium"
      ? "bg-yellow-fill text-text-primary"
      : "bg-surface-2 text-text-primary";
  return <span className={cn("tag", cls)}>{p} priority</span>;
}

/** Horizontal fill bar. Animates scaleX, never width. */
export function FillBar({ value, color = "var(--section-fill)", delay = 0, className }: { value: number; color?: string; delay?: number; className?: string }) {
  const pct = Math.max(0, Math.min(1, value));
  return (
    <div className={cn("h-2 overflow-hidden bg-surface-2", className)}>
      <motion.div
        initial={{ scaleX: 0 }}
        whileInView={{ scaleX: pct }}
        viewport={{ once: true }}
        transition={{ duration: 0.5, delay, ease: EASE_OUT }}
        className="h-full origin-left"
        style={{ background: color }}
      />
    </div>
  );
}

export function ConfidenceBar({ value, color = "var(--section-fill)" }: { value: number; color?: string }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div className="flex items-center gap-2">
      <FillBar value={value} color={color} className="flex-1" />
      <span className="tabular w-9 text-right text-xs text-text-muted">{pct}%</span>
    </div>
  );
}

// ── Skeletons ───────────────────────────────────────────────────

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton", className)} />;
}

export type SkeletonVariant = "overview" | "network" | "space" | "formation" | "press" | "patterns" | "strategy" | "report" | "player" | "simulation" | "compare";

const Tiles = ({ n }: { n: number }) => (
  <div className={cn("grid gap-3", n === 2 ? "sm:grid-cols-2" : n === 3 ? "sm:grid-cols-3" : "sm:grid-cols-2 lg:grid-cols-4")}>
    {Array.from({ length: n }).map((_, i) => (
      <div key={i} className="tile space-y-2.5 px-4 py-3.5">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-20" />
      </div>
    ))}
  </div>
);

const Viz = ({ n = 2 }: { n?: number }) => (
  <div className={cn("grid gap-4", n > 1 && "md:grid-cols-2")}>
    {Array.from({ length: n }).map((_, i) => <Skeleton key={i} className="aspect-[3/2] w-full" />)}
  </div>
);

const Lines = ({ n = 4 }: { n?: number }) => (
  <div className="space-y-2.5">
    {Array.from({ length: n }).map((_, i) => <Skeleton key={i} className="h-3.5" />)}
    <Skeleton className="h-3.5 w-3/5" />
  </div>
);

const Cards = ({ n = 3 }: { n?: number }) => (
  <div className="space-y-3">
    {Array.from({ length: n }).map((_, i) => (
      <div key={i} className="panel space-y-2.5 p-4">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-4 w-4/5" />
        <Skeleton className="h-3 w-3/5" />
      </div>
    ))}
  </div>
);

/** Placeholder that mirrors the layout of the results it stands in for. */
export function ResultsSkeleton({ message, variant = "overview" }: { message?: string; variant?: SkeletonVariant }) {
  const body = (() => {
    switch (variant) {
      case "network": return <><Tiles n={3} /><Viz /><Cards n={2} /></>;
      case "space": return <><Tiles n={3} /><div className="panel space-y-4 p-5">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-2.5" />)}</div><Viz /></>;
      case "formation": return <><div className="grid gap-4 sm:grid-cols-2">{[0, 1].map((i) => <div key={i} className="tile space-y-3 p-5"><Skeleton className="h-3 w-24" /><Skeleton className="h-12 w-32" /><Skeleton className="h-1.5" /></div>)}</div><Viz n={1} /></>;
      case "press": return <><div className="grid gap-4 lg:grid-cols-[260px_1fr]"><Skeleton className="h-56" /><div className="grid gap-3 sm:grid-cols-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-20" />)}</div></div><Viz n={1} /></>;
      case "patterns": return <><div className="grid gap-5 lg:grid-cols-2"><Cards n={3} /><Cards n={3} /></div><Viz n={1} /></>;
      case "strategy": return <><div className="flex gap-2"><Skeleton className="h-6 w-28" /><Skeleton className="h-6 w-28" /></div><Cards n={4} /></>;
      case "report": return <><Tiles n={4} /><div className="panel space-y-6 p-6"><Lines /><Lines /><Lines n={3} /></div></>;
      case "player": return <div className="grid gap-5 lg:grid-cols-[320px_1fr]"><Skeleton className="h-[420px]" /><Skeleton className="h-[420px]" /></div>;
      case "simulation": return <><Skeleton className="h-24" /><Skeleton className="aspect-[2/1] w-full" /><Tiles n={4} /></>;
      case "compare": return <><Skeleton className="h-20" /><div className="grid gap-5 lg:grid-cols-2"><Skeleton className="h-64" /><Skeleton className="h-64" /></div></>;
      default: return <><Tiles n={4} /><Viz /><Cards n={2} /></>;
    }
  })();
  return (
    <div className="space-y-5" aria-busy="true" aria-live="polite">
      {message && <p className="text-sm text-text-secondary">{message}</p>}
      {body}
    </div>
  );
}
