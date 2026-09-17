import { motion, AnimatePresence } from "motion/react";
import { Send, Sparkles, MessageSquare, Trash2, Link2, Link2Off, User as UserIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { askSpaceAI, isLLMConfigured } from "../../lib/llm";
import { askBackend } from "../../lib/api";
import type { HealthResponse } from "../../lib/types";
import { Markdown } from "./common/Markdown";
import { Button } from "./common/Primitives";
import { cn } from "./ui/utils";
import { pressable } from "../../lib/motion";

interface Message {
  id: string;
  text: string;
  sender: "user" | "ai";
  mode?: string;
  timestamp: number;
}

const WELCOME: Message = {
  id: "welcome",
  text: "Hello! I'm **SpaceAI**, your tactical analyst. Ask me about formations, pressing structures, build-up patterns or how to beat a specific setup.",
  sender: "ai",
  timestamp: Date.now(),
};

const EXAMPLES = [
  "How do I beat a low block with a 4-3-3?",
  "What are the weaknesses of a 4-2-3-1?",
  "Which formations thrive under a high press?",
  "Explain half-space overloads",
  "When should full-backs invert?",
];

interface AskSpaceAIProps {
  health: HealthResponse | null;
  context: Record<string, unknown> | null;
}

export function AskSpaceAI({ health, context }: AskSpaceAIProps) {
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const raw = sessionStorage.getItem("spaceai.chat");
      const parsed = raw ? (JSON.parse(raw) as Message[]) : null;
      return parsed?.length ? parsed : [WELCOME];
    } catch {
      return [WELCOME];
    }
  });
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [useContext, setUseContext] = useState(true);
  const endRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const browserLLM = isLLMConfigured();
  const backendLLM = Boolean(health?.llm_available);

  // Questions grounded in the last analysis the user ran
  const contextQuestions: string[] = (() => {
    if (!context) return [];
    const c = context as Record<string, unknown>;
    const teamA = (c.team_a_name as string) || "our team";
    const teamB = (c.team_b_name as string) || "the opponent";
    const f = (c.formation as Record<string, unknown> | undefined) ?? {};
    const fa = (f.team_a_formation as string) || (c.formation_a as string) || "";
    const fb = (f.team_b_formation as string) || (c.formation_b as string) || "";
    const press = ((c.press_resistance as Record<string, unknown> | undefined)?.press_resistance_score as number | undefined);
    const qs: string[] = [];
    if (fa) qs.push(`Why does ${teamA}'s average shape read as ${fa}?`);
    if (fa && fb) qs.push(`How should ${teamB} in a ${fb} counter ${teamA}'s ${fa}?`);
    if (typeof press === "number") qs.push(`${teamA} scored ${Math.round(press)}/100 for press resistance — what does that mean for their build-up?`);
    if (c.match) qs.push(`Summarise the tactical story of ${c.match}.`);
    return qs.slice(0, 4);
  })();

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    try { sessionStorage.setItem("spaceai.chat", JSON.stringify(messages.slice(-40))); } catch { /* ignore */ }
  }, [messages]);

  const autoGrow = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  const send = async (text: string) => {
    const question = text.trim();
    if (!question || isTyping) return;
    setMessages((m) => [...m, { id: crypto.randomUUID(), text: question, sender: "user", timestamp: Date.now() }]);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setIsTyping(true);

    const ctx = useContext && context ? context : undefined;
    try {
      let answer: string | null = null;
      let mode = "openrouter (browser)";
      if (browserLLM) answer = await askSpaceAI(question, ctx);
      if (!answer) {
        const res = await askBackend(question, ctx);
        answer = res.answer;
        mode = res.mode;
      }
      setMessages((m) => [...m, { id: crypto.randomUUID(), text: answer ?? "I couldn't generate a response. Please try again.", sender: "ai", mode, timestamp: Date.now() }]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Connection error.";
      toast.error("SpaceAI is unavailable", { description: message });
      setMessages((m) => [...m, { id: crypto.randomUUID(), text: `⚠ ${message}`, sender: "ai", mode: "error", timestamp: Date.now() }]);
    } finally {
      setIsTyping(false);
    }
  };

  const clear = () => {
    setMessages([WELCOME]);
    toast.success("Conversation cleared");
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="relative border-b border-white/10 px-4 py-4 sm:px-6">
        <div className="absolute inset-0 bg-gradient-to-b from-surface-2/70 to-transparent" />
        <div className="relative mx-auto flex max-w-4xl items-center gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 shadow-[0_0_30px_rgba(123,97,255,0.45)]">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-bold text-white sm:text-2xl">Ask SpaceAI</h1>
            <p className="truncate text-sm text-text-secondary">Your tactical analyst · {browserLLM ? "OpenRouter (browser)" : backendLLM ? `${health?.llm_provider} via backend` : "knowledge-graph mode"}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setUseContext((v) => !v)}
              disabled={!context}
              title={context ? (useContext ? "Answers reference your last analysis" : "Ignoring your last analysis") : "Run an analysis to give SpaceAI context"}
              className={cn("chip transition-colors", !context ? "border-white/10 bg-white/5 text-text-muted" : useContext ? "border-brand/40 bg-brand/15 text-brand" : "border-white/10 bg-white/5 text-text-secondary")}
            >
              {useContext && context ? <Link2 className="h-3.5 w-3.5" /> : <Link2Off className="h-3.5 w-3.5" />}
              <span className="hidden sm:inline">{context ? "Last analysis" : "No context"}</span>
            </button>
            <Button variant="ghost" size="sm" icon={Trash2} onClick={clear} aria-label="Clear conversation" />
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
        <div className="mx-auto max-w-4xl space-y-5">
          <AnimatePresence initial={false}>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                layout
                initial={{ opacity: 0, y: 16, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.25 }}
                className={cn("flex", message.sender === "user" ? "justify-end" : "justify-start")}
              >
                <div className={cn("flex max-w-[88%] gap-3 sm:max-w-[80%]", message.sender === "user" && "flex-row-reverse")}>
                  <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-full", message.sender === "ai" ? "bg-gradient-to-br from-violet-500 to-fuchsia-500 shadow-[0_0_16px_rgba(123,97,255,0.35)]" : "bg-brand/20 text-brand")}>
                    {message.sender === "ai" ? <Sparkles className="h-4 w-4 text-white" /> : <UserIcon className="h-4 w-4" />}
                  </div>
                  <div className={cn("rounded-2xl px-4 py-3", message.sender === "user" ? "border border-brand/40 bg-gradient-to-br from-cyan-500/20 to-blue-600/20" : "border border-white/10 bg-white/5")}>
                    <Markdown text={message.text} className="text-[15px] text-white/90" />
                    <div className="mt-1.5 flex items-center gap-2 text-[11px] text-text-muted">
                      {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      {message.mode && message.mode !== "error" && <span className="rounded-full bg-white/5 px-1.5 py-0.5">{message.mode.replace("_", " ")}</span>}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {isTyping && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex justify-start">
              <div className="flex gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500"><Sparkles className="h-4 w-4 text-white" /></div>
                <div className="flex items-center gap-1.5 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                  {[0, 0.2, 0.4].map((d) => (
                    <motion.span key={d} className="h-2 w-2 rounded-full bg-brand" animate={{ opacity: [0.3, 1, 0.3], y: [0, -3, 0] }} transition={{ duration: 1, repeat: Infinity, delay: d }} />
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {contextQuestions.length > 0 && !isTyping && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="pt-2">
              <div className="mb-2 flex items-center gap-2 text-sm text-text-muted"><Link2 className="h-4 w-4 text-brand" /> About your last analysis{context && (context as Record<string, unknown>).match ? ` · ${(context as Record<string, unknown>).match as string}` : ""}</div>
              <div className="flex flex-wrap gap-2">
                {contextQuestions.map((q, i) => (
                  <motion.button key={q} {...pressable} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.25 + i * 0.05 }} onClick={() => { setUseContext(true); void send(q); }} className="rounded-full border border-brand/30 bg-brand/10 px-4 py-2 text-sm text-brand transition-colors hover:bg-brand/20">
                    {q}
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}

          {messages.length <= 1 && !isTyping && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="pt-2">
              <div className="mb-2 flex items-center gap-2 text-sm text-text-muted"><MessageSquare className="h-4 w-4" /> Try one of these</div>
              <div className="flex flex-wrap gap-2">
                {EXAMPLES.map((q, i) => (
                  <motion.button key={q} {...pressable} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.35 + i * 0.06 }} onClick={() => send(q)} className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-text-secondary transition-colors hover:border-brand/40 hover:text-brand">
                    {q}
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}
          <div ref={endRef} />
        </div>
      </div>

      {/* Composer */}
      <div className="border-t border-white/10 p-4 sm:p-5">
        <div className="mx-auto max-w-4xl">
          <div className="flex items-end gap-3">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => { setInput(e.target.value); autoGrow(); }}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void send(input); } }}
              placeholder="Ask about tactics, formations, strategies… (Enter to send, Shift+Enter for a new line)"
              rows={1}
              className="field flex-1 resize-none rounded-xl px-4 py-3 text-[15px]"
            />
            <motion.button
              {...pressable}
              onClick={() => send(input)}
              disabled={!input.trim() || isTyping}
              aria-label="Send"
              className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 text-white shadow-[0_0_20px_rgba(0,217,255,0.4)] disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Send className="h-5 w-5" />
            </motion.button>
          </div>
          <p className={cn("mt-3 rounded-lg border px-3 py-2 text-xs", browserLLM || backendLLM ? "border-success/20 bg-success/10 text-success/90" : "border-warning/20 bg-warning/10 text-warning/90")}>
            {browserLLM
              ? "OpenRouter connected in the browser — full AI answers enabled."
              : backendLLM
              ? `Backend LLM (${health?.llm_provider}) connected — full AI answers enabled.`
              : "Knowledge-graph mode: ask about formations and situations. Add OPENROUTER_API_KEY or ANTHROPIC_API_KEY to the backend for open-ended answers."}
          </p>
        </div>
      </div>
    </div>
  );
}
