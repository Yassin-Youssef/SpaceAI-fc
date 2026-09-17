import { motion, AnimatePresence } from "motion/react";
import { Clock, Search, Trash2, Loader2, ArrowUpDown, Play, UserRound } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { deleteAnalysis, isSupabaseConfigured } from "../../lib/supabase";
import type { SavedAnalysis, UserProfile } from "../../lib/types";
import { FEATURES } from "./Home";
import { Page, PageHeader, EmptyState, Button, StaggerGrid, StaggerItem } from "./common/Primitives";
import { cardHover } from "../../lib/motion";

interface HistoryProps {
  user: UserProfile;
  savedAnalyses: SavedAnalysis[];
  onLoadAnalysis: (analysis: SavedAnalysis) => void;
  onDeleted: () => void;
  onNavigate: (view: string) => void;
}

export function History({ user, savedAnalyses, onLoadAnalysis, onDeleted, onNavigate }: HistoryProps) {
  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState<"date" | "feature">("date");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const supabaseOk = isSupabaseConfigured();

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    return savedAnalyses
      .filter((a) => a.match_name.toLowerCase().includes(q) || a.feature.toLowerCase().includes(q))
      .sort((a, b) => (sortBy === "date" ? new Date(b.created_at).getTime() - new Date(a.created_at).getTime() : a.feature.localeCompare(b.feature)));
  }, [savedAnalyses, query, sortBy]);

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    const { error } = await deleteAnalysis(id);
    setDeletingId(null);
    setConfirmId(null);
    if (error) toast.error("Could not delete", { description: error });
    else { toast.success("Analysis deleted"); onDeleted(); }
  };

  return (
    <Page>
      <div className="space-y-5">
        <PageHeader
          icon={Clock}
          eyebrow="Library"
          title="Your analyses"
          description={`${savedAnalyses.length} saved ${savedAnalyses.length === 1 ? "analysis" : "analyses"}`}
        />

        {user.isGuest || !supabaseOk ? (
          <EmptyState
            icon={UserRound}
            title={supabaseOk ? "History needs an account" : "History is not configured"}
            description={supabaseOk ? "Sign in to save analyses and revisit them later." : "Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to frontend/.env.local to enable saved analyses."}
            action={<Button variant="secondary" onClick={() => onNavigate(supabaseOk ? "logout" : "settings")}>{supabaseOk ? "Sign in" : "Open settings"}</Button>}
          />
        ) : (
          <>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="flex flex-col gap-3 sm:flex-row">
              <label className="relative flex-1">
                <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by match or feature…" className="field rounded-xl py-3 pl-10" />
              </label>
              <label className="relative">
                <ArrowUpDown className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                <select value={sortBy} onChange={(e) => setSortBy(e.target.value as typeof sortBy)} className="field cursor-pointer rounded-xl py-3 pl-10 pr-8 sm:w-48">
                  <option value="date">Newest first</option>
                  <option value="feature">By feature</option>
                </select>
              </label>
            </motion.div>

            {filtered.length > 0 ? (
              <StaggerGrid className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                <AnimatePresence>
                  {filtered.map((item) => {
                    const Icon = FEATURES.find((f) => f.name === item.feature)?.icon ?? Clock;
                    const isDeleting = deletingId === item.id;
                    return (
                      <StaggerItem key={item.id}>
                        <motion.div {...cardHover} layout className="glass group relative overflow-hidden">
                          <button type="button" onClick={() => onLoadAnalysis(item)} className="block w-full text-left">
                            <div className="relative flex h-32 items-center justify-center bg-gradient-to-br from-brand/15 to-violet/10">
                              <div className="pitch-grid-bg absolute inset-0 opacity-70" />
                              <Icon className="relative h-12 w-12 text-brand/60 transition-transform group-hover:scale-110" />
                              <span className="absolute bottom-3 right-3 inline-flex items-center gap-1 rounded-full bg-black/40 px-2.5 py-1 text-[11px] font-semibold text-white opacity-0 backdrop-blur transition-opacity group-hover:opacity-100"><Play className="h-3 w-3" /> Open</span>
                            </div>
                            <div className="p-4">
                              <h3 className="truncate font-bold text-white transition-colors group-hover:text-brand">{item.match_name}</h3>
                              <p className="text-sm text-text-secondary">{item.feature}</p>
                              <div className="mt-2 flex items-center justify-between text-xs text-text-muted">
                                <span>{formatDate(item.created_at)}</span><span>{formatTime(item.created_at)}</span>
                              </div>
                            </div>
                          </button>
                          <div className="absolute right-3 top-3">
                            {confirmId === item.id ? (
                              <div className="flex items-center gap-1 rounded-lg bg-black/70 p-1 backdrop-blur">
                                <button type="button" onClick={() => handleDelete(item.id)} disabled={isDeleting} className="rounded-md bg-danger px-2 py-1 text-xs font-semibold text-white">{isDeleting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Delete"}</button>
                                <button type="button" onClick={() => setConfirmId(null)} className="rounded-md px-2 py-1 text-xs text-white/80 hover:bg-white/10">Cancel</button>
                              </div>
                            ) : (
                              <button type="button" onClick={() => setConfirmId(item.id)} aria-label="Delete analysis" className="rounded-lg bg-black/50 p-2 text-white/70 opacity-0 backdrop-blur transition-all hover:bg-danger/30 hover:text-danger group-hover:opacity-100">
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </motion.div>
                      </StaggerItem>
                    );
                  })}
                </AnimatePresence>
              </StaggerGrid>
            ) : (
              <EmptyState
                icon={Clock}
                title={query ? "No matching analyses" : "Nothing saved yet"}
                description={query ? "Try a different search term." : "Run any feature and press “Save to history” on the results page."}
                action={!query ? <Button onClick={() => onNavigate("full-match")}>Run an analysis</Button> : undefined}
              />
            )}
          </>
        )}
      </div>
    </Page>
  );
}

function formatDate(iso: string) {
  try { return new Date(iso).toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" }); } catch { return iso.slice(0, 10); }
}
function formatTime(iso: string) {
  try { return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); } catch { return ""; }
}
