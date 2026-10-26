import { AnimatePresence, motion } from "motion/react";
import { History as HistoryIcon, Search, Trash2, ArrowUpDown, UserRound, ChevronRight } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { deleteAnalysis, isSupabaseConfigured } from "../../lib/supabase";
import type { SavedAnalysis, UserProfile } from "../../lib/types";
import { FEATURES, sectionVar } from "../../lib/features";
import { Page, PageHeader, EmptyState, Button } from "./common/Primitives";
import { EASE_OUT } from "../../lib/motion";

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
    if (error) toast.error("Could not delete the analysis", { description: error });
    else { toast.success("Analysis deleted"); onDeleted(); }
  };

  return (
    <Page width="max-w-5xl">
      <PageHeader
        title="History"
        description={user.isGuest || !supabaseOk ? "Saved analyses, once you are signed in." : `${savedAnalyses.length} saved ${savedAnalyses.length === 1 ? "analysis" : "analyses"}. Open one to see its results again.`}
      />

      <div className="mt-6">
        {user.isGuest || !supabaseOk ? (
          <EmptyState
            icon={UserRound}
            title={supabaseOk ? "History needs an account" : "History is not set up on this install"}
            description={supabaseOk ? "Sign in to save analyses and come back to them later." : "Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to frontend/.env.local to turn on saved analyses."}
            action={<Button variant="secondary" onClick={() => onNavigate(supabaseOk ? "logout" : "settings")}>{supabaseOk ? "Sign in" : "Open settings"}</Button>}
          />
        ) : (
          <>
            <div className="flex flex-col gap-3 sm:flex-row">
              <label className="relative flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by match or feature" aria-label="Search saved analyses" className="field h-10 pl-9" />
              </label>
              <label className="relative">
                <ArrowUpDown className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                <select value={sortBy} onChange={(e) => setSortBy(e.target.value as typeof sortBy)} aria-label="Sort" className="field h-10 cursor-pointer pl-9 pr-8 sm:w-48">
                  <option value="date">Newest first</option>
                  <option value="feature">By feature</option>
                </select>
              </label>
            </div>

            {filtered.length > 0 ? (
              <ul className="mt-5 divide-y divide-line overflow-hidden rounded-md border border-line">
                <AnimatePresence initial={false}>
                  {filtered.map((item) => {
                    const feature = FEATURES.find((f) => f.name === item.feature);
                    const Icon = feature?.icon ?? HistoryIcon;
                    const confirming = confirmId === item.id;
                    return (
                      <motion.li
                        key={item.id}
                        layout
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0, transition: { duration: 0.15, ease: EASE_OUT } }}
                        className="flex items-center gap-2 bg-surface-1 pr-3"
                        style={sectionVar(feature?.section ?? "core")}
                      >
                        <button type="button" onClick={() => onLoadAnalysis(item)} className="group flex min-w-0 flex-1 items-center gap-4 px-4 py-3.5 text-left transition-colors duration-150 hover:bg-surface-2">
                          <Icon className="h-5 w-5 shrink-0 text-section" strokeWidth={1.75} />
                          <span className="min-w-0 flex-1">
                            <span className="block truncate font-medium text-text-primary">{item.match_name}</span>
                            <span className="block truncate text-sm text-text-muted">{item.feature}</span>
                          </span>
                          <span className="hidden shrink-0 text-right text-sm text-text-muted sm:block">
                            {formatDate(item.created_at)}
                            <span className="block text-xs">{formatTime(item.created_at)}</span>
                          </span>
                          <ChevronRight className="h-4 w-4 shrink-0 text-text-muted transition-transform duration-150 group-hover:translate-x-0.5" />
                        </button>
                        {confirming ? (
                          <div className="flex shrink-0 items-center gap-1">
                            <Button size="sm" variant="danger" loading={deletingId === item.id} onClick={() => handleDelete(item.id)}>Delete</Button>
                            <Button size="sm" variant="ghost" onClick={() => setConfirmId(null)}>Keep</Button>
                          </div>
                        ) : (
                          <button type="button" onClick={() => setConfirmId(item.id)} aria-label={`Delete ${item.match_name}`} className="press shrink-0 rounded-md p-2 text-text-muted hover:bg-danger/15 hover:text-danger">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </motion.li>
                    );
                  })}
                </AnimatePresence>
              </ul>
            ) : (
              <div className="mt-5">
                <EmptyState
                  icon={HistoryIcon}
                  title={query ? "Nothing matches that search" : "Nothing saved yet"}
                  description={query ? "Try a team name or a feature such as Pass Network." : "Run any analysis and press Save to history on its results page."}
                  action={!query ? <Button onClick={() => onNavigate("full-match")}>Run an analysis</Button> : undefined}
                />
              </div>
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
