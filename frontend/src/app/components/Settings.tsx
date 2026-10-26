import { motion } from "motion/react";
import { Settings2, RefreshCw, CheckCircle2, XCircle, Minus, ExternalLink, Trash2 } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { toast } from "sonner";
import { API_BASE, API_ORIGIN, healthCheck } from "../../lib/api";
import { isSupabaseConfigured } from "../../lib/supabase";
import { isLLMConfigured } from "../../lib/llm";
import type { HealthResponse, UserProfile } from "../../lib/types";
import { Page, PageHeader, Button } from "./common/Primitives";
import { cn } from "./ui/utils";
import { springSoft } from "../../lib/motion";

interface SettingsProps {
  user?: UserProfile | null;
  health: HealthResponse | null;
  healthError: boolean;
  onRefreshHealth: () => Promise<void>;
  reduceMotion: boolean;
  onReduceMotion: (v: boolean) => void;
}

export function Settings({ user, health, healthError, onRefreshHealth, reduceMotion, onReduceMotion }: SettingsProps) {
  const [checking, setChecking] = useState(false);
  const [latency, setLatency] = useState<number | null>(null);

  const ping = async () => {
    setChecking(true);
    const t0 = performance.now();
    try {
      await healthCheck();
      setLatency(Math.round(performance.now() - t0));
      await onRefreshHealth();
      toast.success("Engine reachable");
    } catch (err) {
      setLatency(null);
      await onRefreshHealth();
      toast.error("Engine unreachable", { description: err instanceof Error ? err.message : undefined });
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => { if (!health && !healthError) void ping(); /* eslint-disable-line react-hooks/exhaustive-deps */ }, []);

  const caps = health?.capabilities ?? {};
  const capRows: Array<{ key: string; label: string; hint: string }> = [
    { key: "cv_pipeline", label: "Video analysis (YOLOv8, OpenCV)", hint: "pip install ultralytics opencv-python" },
    { key: "yt_dlp", label: "YouTube download (yt-dlp)", hint: "pip install yt-dlp" },
    { key: "rl_coach", label: "RL coach (Gymnasium, Stable-Baselines3)", hint: "pip install gymnasium stable-baselines3" },
    { key: "docx_export", label: "Word export (python-docx)", hint: "pip install python-docx" },
  ];

  const clearLocal = () => {
    try {
      ["spaceai.sidebar", "spaceai.reduceMotion", "spaceai.demoMatch", "spaceai.simPreset", "spaceai.comparePreset", "spaceai.demoPlayer"].forEach((k) => localStorage.removeItem(k));
      sessionStorage.removeItem("spaceai.chat");
      toast.success("Local preferences cleared");
    } catch { /* ignore */ }
  };

  return (
    <Page width="max-w-4xl">
      <PageHeader title="Settings" description="Engine connection, optional modules, language models and your preferences." />

      <Group title="Engine" action={<Button size="sm" variant="secondary" icon={RefreshCw} loading={checking} onClick={ping}>Check now</Button>}>
        <Row label="Status" value={<Status ok={!healthError && Boolean(health)} pending={!health && !healthError} okText="Online" badText="Offline" />} />
        <Row label="Address" value={<code className="break-all text-sm text-text-secondary">{API_BASE}</code>} />
        <Row label="Version" value={health?.version ? `v${health.version}` : "–"} />
        <Row label="Round trip" value={latency !== null ? `${latency} ms` : "–"} />
        <Row label="API docs" value={<a className="inline-flex items-center gap-1 text-section underline-offset-4 hover:underline" href={`${API_ORIGIN}/docs`} target="_blank" rel="noreferrer">Swagger UI <ExternalLink className="h-3 w-3" /></a>} />
        {healthError && (
          <p className="mt-3 rounded-md border border-danger/50 bg-danger/10 p-3 text-sm text-danger">
            Start the API from the project root with <code className="text-text-primary">uvicorn api.main:app --reload --port 8000</code>.
          </p>
        )}
      </Group>

      <Group title="Language models">
        <Row label="Backend" value={<Status ok={Boolean(health?.llm_available)} okText={health?.llm_provider ?? "Configured"} badText="Not set: knowledge-graph answers" neutral />} />
        <Row label="In the browser" value={<Status ok={isLLMConfigured()} okText="OpenRouter key set" badText="Not set" neutral />} />
        <p className="mt-3 text-sm text-text-muted">
          Set <code className="text-text-secondary">OPENROUTER_API_KEY</code> or <code className="text-text-secondary">ANTHROPIC_API_KEY</code> in the backend environment or a root <code className="text-text-secondary">.env</code> file for written answers and reports. Every feature works without a key.
        </p>
      </Group>

      <Group title="Optional engine modules">
        {capRows.map((c) => (
          <Row
            key={c.key}
            label={<span>{c.label}{!caps[c.key] && <code className="mt-0.5 block text-xs text-text-muted">{c.hint}</code>}</span>}
            value={<Status ok={Boolean(caps[c.key])} pending={!health} okText="Installed" badText="Using fallback" neutral />}
          />
        ))}
      </Group>

      <Group title="Account and preferences">
        <Row label="Accounts (Supabase)" value={<Status ok={isSupabaseConfigured()} okText="Configured" badText="Not configured: guest mode" neutral />} />
        <Row label="Signed in as" value={user?.isGuest ? "Guest" : user?.email ?? "–"} />
        <div className="flex items-center justify-between gap-4 py-3">
          <div>
            <div className="text-text-primary">Reduce motion</div>
            <div className="text-sm text-text-muted">Turns off page transitions, staggered entrances and counting numbers.</div>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={reduceMotion}
            aria-label="Reduce motion"
            onClick={() => onReduceMotion(!reduceMotion)}
            className={cn("relative h-6 w-11 shrink-0 rounded-full border transition-colors duration-150", reduceMotion ? "border-section bg-section-fill" : "border-line-strong bg-surface-3")}
          >
            <motion.span layout transition={springSoft} className={cn("absolute top-0.5 h-[18px] w-[18px] rounded-full", reduceMotion ? "left-[22px] bg-section-on" : "left-0.5 bg-text-secondary")} />
          </button>
        </div>
        <div className="pt-2">
          <Button size="sm" variant="ghost" icon={Trash2} onClick={clearLocal}>Clear local preferences</Button>
        </div>
      </Group>
    </Page>
  );
}

function Group({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return (
    <section className="border-b border-line py-8 last:border-b-0">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-2xl text-text-primary">{title}</h2>
        {action}
      </div>
      <div className="divide-y divide-line">{children}</div>
    </section>
  );
}

function Row({ label, value }: { label: ReactNode; value: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-3 text-sm">
      <span className="min-w-0 text-text-secondary">{label}</span>
      <span className="shrink-0 text-right text-text-primary">{value}</span>
    </div>
  );
}

function Status({ ok, pending, okText, badText, neutral = false }: { ok: boolean; pending?: boolean; okText: string; badText: string; neutral?: boolean }) {
  if (pending) return <span className="chip border-line-strong text-text-muted"><Minus className="h-3 w-3" /> Checking</span>;
  if (ok) return <span className="chip border-success/50 text-success"><CheckCircle2 className="h-3 w-3" /> {okText}</span>;
  return <span className={cn("chip", neutral ? "border-line-strong text-text-secondary" : "border-danger/50 text-danger")}><XCircle className="h-3 w-3" /> {badText}</span>;
}
