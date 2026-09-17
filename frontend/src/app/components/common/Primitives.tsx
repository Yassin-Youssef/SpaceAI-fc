/**
 * Small shared building blocks: cards, headers, buttons, stat tiles,
 * empty states, collapsible sections, badges.
 */
import { motion, AnimatePresence, useReducedMotion } from "motion/react";
import { ChevronDown, Loader2, type LucideIcon } from "lucide-react";
import { useState, type ReactNode, type ButtonHTMLAttributes } from "react";
import { cn } from "../ui/utils";
import { pressable, staggerContainer, staggerItem, springSoft } from "../../../lib/motion";
import { AnimatedNumber } from "./AnimatedNumber";

// ── Layout ──────────────────────────────────────────────────────

export function Page({ children, width = "max-w-7xl" }: { children: ReactNode; width?: string }) {
  return (
    <div className="h-full overflow-y-auto">
      <div className={cn("mx-auto w-full px-4 py-5 sm:px-6 sm:py-7 lg:px-8", width)}>{children}</div>
    </div>
  );
}

interface PageHeaderProps {
  icon: LucideIcon;
  title: string;
  description: string;
  eyebrow?: string;
  actions?: ReactNode;
  tone?: "brand" | "violet";
}

export function PageHeader({ icon: Icon, title, description, eyebrow, actions, tone = "brand" }: PageHeaderProps) {
  const gradient = tone === "violet" ? "from-violet-500 to-fuchsia-500" : "from-cyan-500 to-blue-600";
  const glow = tone === "violet" ? "shadow-[0_0_30px_rgba(123,97,255,0.4)]" : "shadow-[0_0_30px_rgba(0,217,255,0.4)]";
  return (
    <motion.header
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="glass-brand relative p-5 sm:p-6"
    >
      <div className="pitch-grid-bg pointer-events-none absolute inset-0 rounded-xl opacity-60" />
      <div className="relative flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className={cn("flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br sm:h-14 sm:w-14", gradient, glow)}>
            <Icon className="h-6 w-6 text-white sm:h-7 sm:w-7" />
          </div>
          <div className="min-w-0">
            {eyebrow && <div className="eyebrow mb-1">{eyebrow}</div>}
            <h1 className="text-xl font-bold text-white sm:text-2xl">{title}</h1>
            <p className="text-sm text-text-secondary sm:text-base">{description}</p>
          </div>
        </div>
        {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
      </div>
    </motion.header>
  );
}

export function SectionTitle({ children, hint, right }: { children: ReactNode; hint?: string; right?: ReactNode }) {
  return (
    <div className="mb-3 flex items-end justify-between gap-3">
      <div>
        <h3 className="text-base font-bold text-white sm:text-lg">{children}</h3>
        {hint && <p className="text-xs text-text-muted">{hint}</p>}
      </div>
      {right}
    </div>
  );
}

// ── Cards ───────────────────────────────────────────────────────

export function GlassCard({ children, className, brand = false }: { children: ReactNode; className?: string; brand?: boolean }) {
  return <div className={cn(brand ? "glass-brand" : "glass", "p-4 sm:p-5", className)}>{children}</div>;
}

/** Container whose direct children animate in with a stagger. */
export function StaggerGrid({ children, className, stagger = 0.06 }: { children: ReactNode; className?: string; stagger?: number }) {
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
    <div className="glass overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-white/[0.04] sm:px-5"
      >
        {Icon && (
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand/15 text-brand">
            <Icon className="h-4 w-4" />
          </span>
        )}
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-bold text-white sm:text-base">{title}</span>
          {subtitle && <span className="block truncate text-xs text-text-muted">{subtitle}</span>}
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
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <div className="border-t border-white/10 px-4 py-4 sm:px-5">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Buttons ─────────────────────────────────────────────────────

type Variant = "primary" | "secondary" | "ghost" | "success" | "danger" | "demo";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  icon?: LucideIcon;
  block?: boolean;
}

const variantClasses: Record<Variant, string> = {
  primary: "bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:shadow-[0_0_28px_rgba(0,217,255,0.4)]",
  success: "bg-gradient-to-r from-emerald-500 to-green-600 text-white hover:shadow-[0_0_28px_rgba(47,229,143,0.35)]",
  secondary: "border border-white/10 bg-white/5 text-white hover:bg-white/10",
  ghost: "text-text-secondary hover:bg-white/5 hover:text-white",
  danger: "border border-danger/40 bg-danger/10 text-danger hover:bg-danger/20",
  demo: "bg-gradient-to-r from-amber-400 to-orange-500 text-[#1a1200] hover:shadow-[0_0_28px_rgba(255,193,7,0.4)]",
};

const sizeClasses = {
  sm: "px-3 py-1.5 text-xs gap-1.5 rounded-lg",
  md: "px-4 py-2.5 text-sm gap-2 rounded-lg",
  lg: "px-6 py-3.5 text-base gap-2.5 rounded-xl",
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
        "inline-flex items-center justify-center font-semibold transition-shadow disabled:cursor-not-allowed disabled:opacity-60",
        variantClasses[variant],
        sizeClasses[size],
        block && "w-full",
        className
      )}
      disabled={isDisabled}
      {...(rest as object)}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : Icon ? <Icon className="h-4 w-4" /> : null}
      {children}
    </motion.button>
  );
}

// ── Stat tile ───────────────────────────────────────────────────

interface StatTileProps {
  label: string;
  value: number | string;
  suffix?: string;
  decimals?: number;
  tone?: "brand" | "teamA" | "teamB" | "success" | "warning" | "neutral";
  hint?: string;
  className?: string;
}

const toneColor: Record<NonNullable<StatTileProps["tone"]>, string> = {
  brand: "text-brand",
  teamA: "text-team-a",
  teamB: "text-team-b",
  success: "text-success",
  warning: "text-warning",
  neutral: "text-white",
};

export function StatTile({ label, value, suffix = "", decimals = 0, tone = "brand", hint, className }: StatTileProps) {
  return (
    <div className={cn("glass p-4 text-center", className)}>
      <div className="mb-1 text-xs font-medium uppercase tracking-wider text-text-muted">{label}</div>
      <div className={cn("text-2xl font-black sm:text-3xl", toneColor[tone])}>
        {typeof value === "number" ? <AnimatedNumber value={value} decimals={decimals} suffix={suffix} /> : value}
      </div>
      {hint && <div className="mt-1 text-[11px] text-text-muted">{hint}</div>}
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
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn("glass flex flex-col items-center text-center", compact ? "p-6" : "p-10 sm:p-14")}
    >
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand/10 text-brand">
        <Icon className="h-7 w-7" />
      </div>
      <h3 className="mb-1 text-lg font-bold text-white">{title}</h3>
      <p className="max-w-md text-sm text-text-secondary">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </motion.div>
  );
}

// ── Badges ──────────────────────────────────────────────────────

export function PriorityBadge({ priority }: { priority: string }) {
  const p = priority.toLowerCase();
  const cls =
    p === "high"
      ? "border-danger/40 bg-danger/15 text-danger"
      : p === "medium"
      ? "border-warning/40 bg-warning/15 text-warning"
      : "border-brand/40 bg-brand/15 text-brand";
  return <span className={cn("chip uppercase", cls)}>{p}</span>;
}

export function ConfidenceBar({ value, color = "var(--brand)" }: { value: number; color?: string }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="h-full rounded-full"
          style={{ background: color }}
        />
      </div>
      <span className="w-9 text-right text-xs tabular-nums text-text-muted">{pct}%</span>
    </div>
  );
}

// ── Skeletons ───────────────────────────────────────────────────

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-lg bg-white/[0.07]", className)} />;
}

export function ResultsSkeleton({ message = "Running the tactical engine…" }: { message?: string }) {
  return (
    <div className="space-y-6" aria-busy="true" aria-live="polite">
      <div className="flex items-center gap-3">
        <Skeleton className="h-9 w-9 rounded-lg" />
        <Skeleton className="h-6 w-56" />
      </div>
      <div className="glass flex items-center gap-3 p-4">
        <Loader2 className="h-4 w-4 animate-spin text-brand" />
        <span className="text-sm text-text-secondary">{message}</span>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="aspect-[3/2]" />
        <Skeleton className="aspect-[3/2]" />
      </div>
      <div className="space-y-3">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-11/12" />
        <Skeleton className="h-4 w-4/5" />
      </div>
    </div>
  );
}
