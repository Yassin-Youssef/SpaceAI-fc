import { motion } from "motion/react";
import { Settings as SettingsIcon, Server, Cpu, Database, Sparkles, RefreshCw, CheckCircle2, XCircle, MinusCircle, ExternalLink, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { API_BASE, API_ORIGIN, healthCheck } from "../../lib/api";
import { isSupabaseConfigured } from "../../lib/supabase";
import { isLLMConfigured } from "../../lib/llm";
import type { HealthResponse, UserProfile } from "../../lib/types";
import { Page, PageHeader, GlassCard, Button, StaggerGrid, StaggerItem } from "./common/Primitives";
import { cn } from "./ui/utils";

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
      toast.success("Backend reachable");
    } catch (err) {
      setLatency(null);
      await onRefreshHealth();
      toast.error("Backend unreachable", { description: err instanceof Error ? err.message : undefined });
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => { if (!health && !healthError) void ping(); /* eslint-disable-line react-hooks/exhaustive-deps */ }, []);

  const caps = health?.capabilities ?? {};
  const capRows: Array<{ key: string; label: string; hint: string }> = [
    { key: "cv_pipeline", label: "Video analysis (YOLOv8 + OpenCV)", hint: "pip install ultralytics opencv-python" },
    { key: "yt_dlp", label: "YouTube download (yt-dlp)", hint: "pip install yt-dlp" },
    { key: "rl_coach", label: "RL coach (Gymnasium + SB3)", hint: "pip install gymnasium stable-baselines3" },
    { key: "docx_export", label: "Word export (python-docx)", hint: "pip install python-docx" },
  ];

  const clearLocal = () => {
    try {
      localStorage.removeItem("spaceai.sidebar");
      localStorage.removeItem("spaceai.reduceMotion");
      localStorage.removeItem("spaceai.chat");
      toast.success("Local preferences cleared");
    } catch { /* ignore */ }
  };

  return (
    <Page width="max-w-5xl">
      <div className="space-y-5">
        <PageHeader icon={SettingsIcon} eyebrow="Configuration" title="Settings" description="Connection status, capabilities and personal preferences." />

        <StaggerGrid className="grid gap-4 md:grid-cols-2">
          <StaggerItem>
            <GlassCard className="h-full">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm font-bold text-white"><Server className="h-4 w-4 text-brand" /> Backend</div>
                <Button size="sm" variant="secondary" icon={RefreshCw} loading={checking} onClick={ping}>Check</Button>
              </div>
              <Row label="Status" value={<Status ok={!healthError && Boolean(health)} pending={!health && !healthError} okText="Online" badText="Offline" />} />
              <Row label="URL" value={<code className="text-xs text-text-secondary">{API_BASE}</code>} />
              <Row label="Version" value={health?.version ? `v${health.version}` : "–"} />
              <Row label="Latency" value={latency !== null ? `${latency} ms` : "–"} />
              <Row label="Docs" value={<a className="inline-flex items-center gap-1 text-brand hover:underline" href={`${API_ORIGIN}/docs`} target="_blank" rel="noreferrer">Swagger UI <ExternalLink className="h-3 w-3" /></a>} />
              {healthError && (
                <p className="mt-3 rounded-lg border border-danger/30 bg-danger/10 p-3 text-xs text-danger">
                  Start the API with <code className="text-white">uvicorn api.main:app --reload --port 8000</code> from the project root.
                </p>
              )}
            </GlassCard>
          </StaggerItem>

          <StaggerItem>
            <GlassCard className="h-full">
              <div className="mb-3 flex items-center gap-2 text-sm font-bold text-white"><Sparkles className="h-4 w-4 text-violet" /> AI providers</div>
              <Row label="Backend LLM" value={<Status ok={Boolean(health?.llm_available)} okText={health?.llm_provider ?? "configured"} badText="Knowledge graph fallback" neutral />} />
              <Row label="Browser LLM" value={<Status ok={isLLMConfigured()} okText="OpenRouter key set" badText="Not configured" neutral />} />
              <p className="mt-3 text-xs text-text-muted">
                Set <code className="text-white">OPENROUTER_API_KEY</code> or <code className="text-white">ANTHROPIC_API_KEY</code> in the backend environment (or a root <code className="text-white">.env</code>) for AI answers and narrative reports. Everything works without a key using the tactical knowledge graph.
              </p>
            </GlassCard>
          </StaggerItem>

          <StaggerItem>
            <GlassCard className="h-full">
              <div className="mb-3 flex items-center gap-2 text-sm font-bold text-white"><Cpu className="h-4 w-4 text-success" /> Optional engine modules</div>
              <div className="space-y-2">
                {capRows.map((c) => (
                  <div key={c.key} className="flex items-center justify-between gap-3 rounded-lg bg-white/[0.04] px-3 py-2">
                    <div className="min-w-0">
                      <div className="truncate text-sm text-white">{c.label}</div>
                      {!caps[c.key] && <div className="truncate text-[11px] text-text-muted"><code>{c.hint}</code></div>}
                    </div>
                    <Status ok={Boolean(caps[c.key])} pending={!health} okText="Ready" badText="Fallback" neutral />
                  </div>
                ))}
              </div>
            </GlassCard>
          </StaggerItem>

          <StaggerItem>
            <GlassCard className="h-full">
              <div className="mb-3 flex items-center gap-2 text-sm font-bold text-white"><Database className="h-4 w-4 text-warning" /> Account & preferences</div>
              <Row label="Supabase" value={<Status ok={isSupabaseConfigured()} okText="Configured" badText="Not configured (guest mode)" neutral />} />
              <Row label="Signed in as" value={user?.isGuest ? "Guest" : user?.email ?? "–"} />
              <label className="mt-3 flex cursor-pointer items-center justify-between gap-3 rounded-lg bg-white/[0.04] px-3 py-2.5">
                <div>
                  <div className="text-sm text-white">Reduce motion</div>
                  <div className="text-[11px] text-text-muted">Disable page transitions and staggered animations</div>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={reduceMotion}
                  onClick={() => onReduceMotion(!reduceMotion)}
                  className={cn("relative h-6 w-11 shrink-0 rounded-full transition-colors", reduceMotion ? "bg-brand" : "bg-white/15")}
                >
                  <motion.span layout transition={{ type: "spring", stiffness: 500, damping: 30 }} className={cn("absolute top-0.5 h-5 w-5 rounded-full bg-white shadow", reduceMotion ? "left-[22px]" : "left-0.5")} />
                </button>
              </label>
              <div className="mt-3 flex justify-end">
                <Button size="sm" variant="ghost" icon={Trash2} onClick={clearLocal}>Clear local preferences</Button>
              </div>
            </GlassCard>
          </StaggerItem>
        </StaggerGrid>
      </div>
    </Page>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-white/5 py-2 text-sm last:border-0">
      <span className="text-text-muted">{label}</span>
      <span className="text-right text-white">{value}</span>
    </div>
  );
}

function Status({ ok, pending, okText, badText, neutral = false }: { ok: boolean; pending?: boolean; okText: string; badText: string; neutral?: boolean }) {
  if (pending) return <span className="chip border-white/10 bg-white/5 text-text-muted"><MinusCircle className="h-3.5 w-3.5" /> Checking</span>;
  if (ok) return <span className="chip border-success/40 bg-success/10 text-success"><CheckCircle2 className="h-3.5 w-3.5" /> {okText}</span>;
  return <span className={cn("chip", neutral ? "border-white/10 bg-white/5 text-text-secondary" : "border-danger/40 bg-danger/10 text-danger")}><XCircle className="h-3.5 w-3.5" /> {badText}</span>;
}
