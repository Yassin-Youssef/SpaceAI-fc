import { motion, AnimatePresence } from "motion/react";
import { Send, Sparkles } from "lucide-react";
import { useState } from "react";

interface Message {
  id: number;
  text: string;
  sender: "user" | "ai";
  timestamp: Date;
}

const mockResponses = [
  "Based on current positioning, I recommend dropping your defensive line 5 meters to compress space and reduce through-ball vulnerability.",
  "The opposition's right winger has a 73% success rate exploiting space behind your left-back. Consider instructing your LB to hold a deeper position.",
  "Your midfield press is being bypassed. Shifting to a 4-2-3-1 with a double pivot would provide better defensive coverage in transition.",
  "I've identified a pattern: the opponent completes 68% of switches to their left flank. Consider shifting your right-sided midfielder narrower.",
];

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hello! I'm SpaceAI, your tactical intelligence assistant. Ask me anything about the match.",
      sender: "ai",
      timestamp: new Date(Date.now() - 60000),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      text: input,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: messages.length + 2,
        text: mockResponses[Math.floor(Math.random() * mockResponses.length)],
        sender: "ai",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="fixed bottom-6 right-6 w-96 h-[32rem] flex flex-col rounded-2xl overflow-hidden"
      style={{
        background: "linear-gradient(135deg, rgba(18, 24, 53, 0.95) 0%, rgba(10, 14, 39, 0.95) 100%)",
        backdropFilter: "blur(20px)",
        border: "1px solid rgba(0, 217, 255, 0.3)",
        boxShadow: "0 0 60px rgba(0, 217, 255, 0.2), 0 20px 40px rgba(0, 0, 0, 0.5)",
      }}
    >
      {/* Header */}
      <div className="relative p-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center shadow-[0_0_20px_rgba(0,217,255,0.4)]">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-green-400 border-2 border-[#121835] shadow-[0_0_10px_rgba(0,255,136,0.6)]" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Ask SpaceAI</h3>
            <p className="text-xs text-white/50">Tactical Intelligence Assistant</p>
          </div>
        </div>

        {/* Glow effect */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: "linear-gradient(180deg, rgba(0, 217, 255, 0.1) 0%, transparent 100%)",
          }}
        />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.sender === "user"
                    ? "bg-cyan-500/20 border border-cyan-500/40 text-white"
                    : "bg-white/5 border border-white/10 text-white/90"
                }`}
              >
                <p className="text-sm leading-relaxed">{message.text}</p>
                <span className="text-[10px] text-white/40 mt-1 block">
                  {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing indicator */}
        {isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-start"
          >
            <div className="bg-white/5 border border-white/10 rounded-lg p-3">
              <div className="flex gap-1">
                <motion.div
                  className="w-2 h-2 rounded-full bg-cyan-400"
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1, repeat: Infinity, delay: 0 }}
                />
                <motion.div
                  className="w-2 h-2 rounded-full bg-cyan-400"
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
                />
                <motion.div
                  className="w-2 h-2 rounded-full bg-cyan-400"
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
                />
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-white/10">
        <div className="relative flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask about tactics, formations, weaknesses..."
            className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-white/40 focus:outline-none focus:border-cyan-500/50 focus:bg-white/10 transition-all"
          />
          <motion.button
            onClick={handleSend}
            disabled={!input.trim()}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-[0_0_20px_rgba(0,217,255,0.4)] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <Send className="w-4 h-4 text-white" />
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}
