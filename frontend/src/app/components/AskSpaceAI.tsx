import { motion, AnimatePresence } from "motion/react";
import { ArrowUp, Trash2, Link2, Link2Off, AlertTriangle, CornerDownRight } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { askSpaceAI, isLLMConfigured } from "../../lib/llm";
import { askBackend } from "../../lib/api";
import type { HealthResponse } from "../../lib/types";
import { Markdown } from "./common/Markdown";
import { Skeleton } from "./common/Primitives";
import { cn } from "./ui/utils";
import { EASE_OUT, pressable } from "../../lib/motion";

interface Message {
  id: string;
  text: string;
  sender: "user" | "ai";
  mode?: string;
  timestamp: number;
}

const WELCOME: Message = {
  id: "welcome",
  text: "Ask about formations, pressing, build-up play or how to beat a particular setup. If you have run an analysis, answers can refer to it.",
  sender: "ai",
  timestamp: Date.now(),
};

const EXAMPLES = [
  "How do I beat a low block with a 4-3-3?",
  "What are the weaknesses of a 4-2-3-1?",
  "Which formations cope best with a high press?",
  "Explain half-space overloads",
  "When should full-backs invert?",
];

const MODE_LABEL: Record<string, string> = {
  openrouter: "OpenRouter",
  "openrouter (browser)": "OpenRouter, in the browser",
  anthropic: "Anthropic",
  knowledge_graph: "Knowledge graph",
};

interface AskSpaceAIProps {
  health: HealthResponse | null;
  context: Record<string, unknown> | null;
}

const enter = { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.25, ease: EASE_OUT } };

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
  const source = browserLLM ? "OpenRouter, in the browser" : backendLLM ? `${health?.llm_provider ?? "Language model"} via the backend` : "Knowledge graph (no API key set)";

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
    if (typeof press === "number") qs.push(`${teamA} scored ${Math.round(press)}/100 for press resistance. What does that mean for their build-up?`);
    if (c.match) qs.push(`Summarise the tactical story of ${c.match}.`);
    return qs.slice(0, 4);
  })();

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
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
      setMessages((m) => [...m, { id: crypto.randomUUID(), text: answer ?? "No answer came back. Try asking again.", sender: "ai", mode, timestamp: Date.now() }]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Could not reach the engine.";
      toast.error("SpaceAI could not answer", { description: message });
      setMessages((m) => [...m, { id: crypto.randomUUID(), text: message, sender: "ai", mode: "error", timestamp: Date.now() }]);
    } finally {
      setIsTyping(false);
    }
  };

  const clear = () => {
    setMessages([WELCOME]);
    toast.success("Conversation cleared");
  };

  const fresh = messages.length <= 1;

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="shrink-0 border-b border-line px-4 py-4 sm:px-6">
        <div className="mx-auto flex max-w-3xl items-center gap-3">
          <div className="min-w-0 flex-1">
            <h1 className="text-2xl text-text-primary sm:text-3xl">Ask SpaceAI</h1>
            <p className="truncate text-sm text-text-muted">Answers from: {source}</p>
          </div>
          <button
            type="button"
            onClick={() => setUseContext((v) => !v)}
            disabled={!context}
            aria-pressed={Boolean(context) && useContext}
            title={context ? (useContext ? "Answers refer to your last analysis" : "Answers ignore your last analysis") : "Run an analysis to give SpaceAI something to refer to"}
            className={cn(
              "press inline-flex h-8 items-center gap-1.5 rounded-md border px-2.5 text-sm",
              !context ? "border-line text-text-muted" : useContext ? "border-section/60 text-section" : "border-line-strong text-text-secondary hover:text-text-primary"
            )}
          >
            {useContext && context ? <Link2 className="h-3.5 w-3.5" /> : <Link2Off className="h-3.5 w-3.5" />}
            <span className="hidden sm:inline">{context ? (useContext ? "Using last analysis" : "Not using last analysis") : "No analysis yet"}</span>
          </button>
          <button type="button" onClick={clear} className="press rounded-md p-2 text-text-muted hover:bg-surface-2 hover:text-text-primary" aria-label="Clear conversation" title="Clear conversation">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-4 py-6 sm:px-6">
        <div className="mx-auto max-w-3xl space-y-6">
          <AnimatePresence initial={false}>
            {messages.map((message) =>
              message.sender === "user" ? (
                <motion.div key={message.id} {...enter} className="flex justify-end">
                  <div className="max-w-[85%] rounded-md border border-line-strong bg-surface-2 px-4 py-2.5 text-text-primary">
                    <Markdown text={message.text} className="text-base [&_p]:my-0" />
                  </div>
                </motion.div>
              ) : (
                <motion.div key={message.id} {...enter} className="max-w-[92%]">
                  <div className="mb-1 flex items-center gap-2 text-xs text-text-muted">
                    <span className={cn("font-medium", message.mode === "error" ? "text-danger" : "text-section")}>SpaceAI</span>
                    {message.mode && message.mode !== "error" && <span>{MODE_LABEL[message.mode] ?? message.mode.replace(/_/g, " ")}</span>}
                    <span>{new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                  </div>
                  {message.mode === "error" ? (
                    <p className="flex items-start gap-2 text-base text-danger"><AlertTriangle className="mt-1 h-4 w-4 shrink-0" />{message.text}</p>
                  ) : (
                    <Markdown text={message.text} className="font-serif text-lg text-text-primary [&>p:first-child]:mt-0 [&_h3]:font-sans" />
                  )}
                </motion.div>
              )
            )}
          </AnimatePresence>

          {isTyping && (
            <motion.div {...enter} className="max-w-md space-y-2" aria-live="polite" aria-label="SpaceAI is answering">
              <div className="text-xs font-medium text-section">SpaceAI</div>
              <Skeleton className="h-3.5 w-full" />
              <Skeleton className="h-3.5 w-4/5" />
              <Skeleton className="h-3.5 w-3/5" />
            </motion.div>
          )}

          {!isTyping && (contextQuestions.length > 0 || fresh) && (
            <motion.div {...enter} className="space-y-5 pt-2">
              {contextQuestions.length > 0 && (
                <SuggestionList
                  title={`About your last analysis${context && (context as Record<string, unknown>).match ? `: ${(context as Record<string, unknown>).match as string}` : ""}`}
                  items={contextQuestions}
                  onPick={(q) => { setUseContext(true); void send(q); }}
                />
              )}
              {fresh && <SuggestionList title="Or try one of these" items={EXAMPLES} onPick={(q) => void send(q)} />}
            </motion.div>
          )}
          <div ref={endRef} />
        </div>
      </div>

      {/* Composer */}
      <div className="shrink-0 border-t border-line bg-surface-1 px-4 py-4 sm:px-6">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-end gap-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => { setInput(e.target.value); autoGrow(); }}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void send(input); } }}
              placeholder="Ask a tactical question"
              aria-label="Your question"
              rows={1}
              className="field flex-1 resize-none py-2.5 text-base"
            />
            <motion.button
              {...pressable}
              onClick={() => send(input)}
              disabled={!input.trim() || isTyping}
              aria-label="Send"
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-section-fill text-section-on transition-[filter] hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ArrowUp className="h-5 w-5" />
            </motion.button>
          </div>
          <p className="mt-2 text-xs text-text-muted">Enter to send, Shift+Enter for a new line.{!browserLLM && !backendLLM && " Add OPENROUTER_API_KEY or ANTHROPIC_API_KEY to the backend for open-ended answers."}</p>
        </div>
      </div>
    </div>
  );
}

function SuggestionList({ title, items, onPick }: { title: string; items: string[]; onPick: (q: string) => void }) {
  return (
    <div>
      <div className="mb-2 text-sm text-text-muted">{title}</div>
      <ul className="divide-y divide-line overflow-hidden rounded-md border border-line">
        {items.map((q) => (
          <li key={q}>
            <button type="button" onClick={() => onPick(q)} className="group flex w-full items-center gap-3 bg-surface-1 px-4 py-2.5 text-left text-sm text-text-secondary transition-colors duration-150 hover:bg-surface-2 hover:text-text-primary">
              <CornerDownRight className="h-3.5 w-3.5 shrink-0 text-text-muted group-hover:text-section" />
              {q}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
