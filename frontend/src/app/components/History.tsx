import { motion } from "motion/react";
import { Clock, Search, Filter, BarChart3, Map, Share2, Trash2, Loader2 } from "lucide-react";
import { useState } from "react";
import { deleteAnalysis, isSupabaseConfigured } from "../../lib/supabase";
import type { SavedAnalysis } from "../../lib/types";

// Feature → icon mapping
const featureIconMap: Record<string, any> = {
  "Full Match Analysis": BarChart3,
  "Space Control": Map,
  "Pass Network": Share2,
  default: BarChart3,
};

interface HistoryProps {
  userId?: string;
  savedAnalyses?: SavedAnalysis[];
  onLoadAnalysis?: (analysis: SavedAnalysis) => void;
  onDeleted?: () => void;
}

export function History({
  userId,
  savedAnalyses = [],
  onLoadAnalysis,
  onDeleted,
}: HistoryProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"date" | "feature">("date");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const supabaseOk = isSupabaseConfigured();

  const filteredHistory = savedAnalyses
    .filter(
      (item) =>
        item.match_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.feature.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === "date")
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      return a.feature.localeCompare(b.feature);
    });

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setDeletingId(id);
    await deleteAnalysis(id);
    setDeletingId(null);
    onDeleted?.();
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
    } catch {
      return iso.slice(0, 10);
    }
  };

  const formatTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto p-8 space-y-6">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Your Analyses</h1>
              <p className="text-white/60">Review and manage your tactical analysis history</p>
            </div>
            <div className="flex items-center gap-2 text-white/50">
              <Clock className="w-5 h-5" />
              <span className="text-sm">{savedAnalyses.length} total analyses</span>
            </div>
          </div>
        </motion.div>

        {/* Supabase not configured warning */}
        {!supabaseOk && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="px-4 py-3 rounded-xl bg-yellow-500/10 border border-yellow-500/20 text-sm text-yellow-400/80"
          >
            💡 Supabase is not configured — add{" "}
            <code className="text-yellow-300">VITE_SUPABASE_URL</code> and{" "}
            <code className="text-yellow-300">VITE_SUPABASE_ANON_KEY</code> to your{" "}
            <code>.env</code> to enable history.
          </motion.div>
        )}

        {/* Search and Filter */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="flex items-center gap-4"
        >
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search analyses..."
              className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 py-3 text-white placeholder-white/40 focus:outline-none focus:border-cyan-500/50 focus:bg-white/10 transition-all"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-white/40" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-500/50 cursor-pointer"
            >
              <option value="date">Sort by Date</option>
              <option value="feature">Sort by Feature</option>
            </select>
          </div>
        </motion.div>

        {/* History Grid */}
        {filteredHistory.length > 0 ? (
          <div className="grid grid-cols-3 gap-6">
            {filteredHistory.map((item, index) => {
              const Icon = featureIconMap[item.feature] ?? featureIconMap.default;
              const isDeleting = deletingId === item.id;

              return (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + index * 0.05 }}
                  className="group cursor-pointer"
                  onClick={() => onLoadAnalysis?.(item)}
                >
                  <div
                    className="rounded-xl backdrop-blur-xl border border-white/10 overflow-hidden transition-all duration-300 hover:border-cyan-500/40 hover:shadow-[0_0_30px_rgba(0,217,255,0.15)]"
                    style={{
                      background:
                        "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)",
                    }}
                  >
                    {/* Thumbnail */}
                    <div className="relative h-40 bg-gradient-to-br from-cyan-900/30 to-blue-900/30 flex items-center justify-center overflow-hidden">
                      <div
                        className="absolute inset-0 opacity-20"
                        style={{
                          backgroundImage: `radial-gradient(circle at 50% 50%, #00d9ff 1px, transparent 1px)`,
                          backgroundSize: "20px 20px",
                        }}
                      />
                      <Icon className="w-16 h-16 text-cyan-400/40 relative z-10" />
                      <div className="absolute top-3 right-3">
                        <button
                          onClick={(e) => handleDelete(e, item.id)}
                          disabled={isDeleting}
                          className="p-2 rounded-lg bg-black/50 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500/20 disabled:cursor-not-allowed"
                        >
                          {isDeleting ? (
                            <Loader2 className="w-4 h-4 text-white/70 animate-spin" />
                          ) : (
                            <Trash2 className="w-4 h-4 text-white/70 hover:text-red-400" />
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Content */}
                    <div className="p-4">
                      <h3 className="font-bold text-white mb-1 group-hover:text-cyan-400 transition-colors">
                        {item.match_name}
                      </h3>
                      <p className="text-sm text-white/60 mb-3">{item.feature}</p>
                      <div className="flex items-center justify-between text-xs text-white/40">
                        <span>{formatDate(item.created_at)}</span>
                        <span>{formatTime(item.created_at)}</span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        ) : (
          /* Empty State */
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="py-20 text-center"
          >
            <div
              className="max-w-md mx-auto rounded-2xl p-12 backdrop-blur-xl border border-white/10"
              style={{
                background: "linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%)",
              }}
            >
              <Clock className="w-20 h-20 text-white/20 mx-auto mb-6" />
              <h2 className="text-xl font-bold text-white mb-2">
                {searchQuery ? "No matching analyses" : "No analyses yet"}
              </h2>
              <p className="text-white/50">
                {searchQuery ? "Try a different search term." : "Start by running your first analysis!"}
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
