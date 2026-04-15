import { motion, AnimatePresence } from "motion/react";
import { Send, Sparkles, Paperclip } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { askSpaceAI, isLLMConfigured } from "../../lib/llm";
import { askBackend } from "../../lib/api";

interface Message {
  id: number;
  text: string;
  sender: "user" | "ai";
  timestamp: Date;
}

const exampleQuestions = [
  "How to beat a low block?",
  "Weaknesses of 4-3-3?",
  "Best setup vs high press?",
  "Half-space overloads explained",
  "When to use inverted fullbacks?",
];


export function AskSpaceAI() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hello! I'm **SpaceAI**, your tactical analyst. Ask me anything about football tactics, formations, or strategies.",
      sender: "ai",
      timestamp: new Date(Date.now() - 60000),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showAttachToggle, setShowAttachToggle] = useState(false);
  const llmAvailable = isLLMConfigured();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    const userMessage: Message = {
      id: messages.length + 1,
      text: input,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const question = input;
    setInput("");
    setIsTyping(true);

    try {
      // 1. Try OpenRouter LLM
      let answer = await askSpaceAI(question);

      // 2. Fall back to backend /api/ask
      if (!answer) {
        const res = await askBackend(question);
        answer = res.answer;
      }

      const aiMessage: Message = {
        id: messages.length + 2,
        text: answer ?? "I couldn't generate a response. Please try again.",
        sender: "ai",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch {
      const aiMessage: Message = {
        id: messages.length + 2,
        text: "⚠ Connection error. Make sure the backend is running at **http://localhost:8000**.",
        sender: "ai",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleExampleClick = (question: string) => {
    setInput(question);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="relative px-8 py-6 border-b border-white/10">
        <div
          className="absolute inset-0"
          style={{
            background: "linear-gradient(180deg, rgba(18, 24, 53, 0.6) 0%, rgba(18, 24, 53, 0.3) 100%)",
          }}
        />
        <div className="relative flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-[0_0_30px_rgba(147,51,234,0.4)]">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">💬 Ask SpaceAI</h1>
            <p className="text-white/60">Your AI tactical analyst</p>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <AnimatePresence initial={false}>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
                className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                <div className={`flex gap-3 max-w-[80%] ${message.sender === "user" ? "flex-row-reverse" : "flex-row"}`}>
                  {/* Avatar */}
                  {message.sender === "ai" && (
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shrink-0 shadow-[0_0_20px_rgba(147,51,234,0.3)]">
                      <Sparkles className="w-5 h-5 text-white" />
                    </div>
                  )}

                  {/* Message Bubble */}
                  <div
                    className={`rounded-2xl p-4 ${
                      message.sender === "user"
                        ? "bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/40"
                        : "bg-white/5 border border-white/10"
                    }`}
                  >
                    <div
                      className="text-white/90 leading-relaxed whitespace-pre-wrap"
                      dangerouslySetInnerHTML={{
                        __html: message.text
                          .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-bold">$1</strong>')
                          .replace(/•/g, '<span class="text-cyan-400">•</span>')
                          .replace(/\n/g, '<br/>'),
                      }}
                    />
                    <div className="text-xs text-white/30 mt-2">
                      {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Typing Indicator */}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shrink-0">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                  <div className="flex gap-1.5">
                    <motion.div
                      className="w-2.5 h-2.5 rounded-full bg-cyan-400"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1, repeat: Infinity, delay: 0 }}
                    />
                    <motion.div
                      className="w-2.5 h-2.5 rounded-full bg-cyan-400"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
                    />
                    <motion.div
                      className="w-2.5 h-2.5 rounded-full bg-cyan-400"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
                    />
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Example Questions */}
          {messages.length === 1 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="pt-4"
            >
              <div className="text-sm text-white/50 mb-3">Try these examples:</div>
              <div className="flex flex-wrap gap-2">
                {exampleQuestions.map((question, index) => (
                  <motion.button
                    key={index}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.6 + index * 0.1 }}
                    onClick={() => handleExampleClick(question)}
                    className="px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm text-white/70 hover:bg-white/10 hover:border-cyan-500/30 hover:text-cyan-400 transition-all"
                  >
                    {question}
                  </motion.button>
                ))}
              </div>
            </motion.div>
          )}
          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Bar */}
      <div className="border-t border-white/10 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="relative flex items-end gap-3">
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask about tactics, formations, strategies..."
                rows={1}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 pr-12 text-white placeholder-white/40 focus:outline-none focus:border-cyan-500/50 focus:bg-white/10 transition-all resize-none"
              />
              <button
                onClick={() => setShowAttachToggle(!showAttachToggle)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                <Paperclip className="w-4 h-4 text-white/40 hover:text-cyan-400 transition-colors" />
              </button>
            </div>
            <motion.button
              onClick={handleSend}
              disabled={!input.trim() || isTyping}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_20px_rgba(0,217,255,0.4)] disabled:opacity-50 disabled:cursor-not-allowed transition-all shrink-0"
            >
              <Send className="w-5 h-5 text-white" />
            </motion.button>
          </div>

          {/* Optional API Key Banner */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`mt-4 px-4 py-2 rounded-lg text-sm ${
              llmAvailable
                ? "bg-green-500/10 border border-green-500/20 text-green-400/80"
                : "bg-yellow-500/10 border border-yellow-500/20 text-yellow-400/80"
            }`}
          >
            {llmAvailable
              ? "✅ OpenRouter AI connected — full responses enabled"
              : "💡 Using backend AI — add VITE_OPENROUTER_API_KEY for enhanced responses"}
          </motion.div>
        </div>
      </div>
    </div>
  );
}
