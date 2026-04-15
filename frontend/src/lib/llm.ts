/**
 * SpaceAI FC — OpenRouter LLM Client
 * =====================================
 * Calls OpenRouter API directly from the browser.
 * Falls back to null when no API key is set — caller
 * should then use the backend /api/ask endpoint instead.
 *
 * Required env var (optional):
 *   VITE_OPENROUTER_API_KEY
 */

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

const SYSTEM_PROMPT = `You are SpaceAI FC, a professional football tactical intelligence system. 
You provide expert analysis of football tactics, formations, player roles, pressing patterns, and strategic recommendations.

Your responses are:
- Concise and structured (use bullet points and **bold** for key terms)
- Data-driven and specific (reference zones, percentages, tactical concepts)
- Professional (like a UEFA Pro Licence coach speaking to analysts)

Always ground your answers in modern football tactical theory. Reference real-world examples where relevant.`;

/**
 * Ask SpaceAI via OpenRouter.
 * Returns the response string, or null if no API key is configured.
 */
export async function askSpaceAI(
  question: string,
  matchContext?: Record<string, unknown>
): Promise<string | null> {
  const apiKey = import.meta.env.VITE_OPENROUTER_API_KEY as string | undefined;

  if (!apiKey) return null;

  const contextMessage = matchContext
    ? `\n\nMatch context:\n${JSON.stringify(matchContext, null, 2)}`
    : "";

  const messages = [
    { role: "system", content: SYSTEM_PROMPT },
    { role: "user", content: question + contextMessage },
  ];

  const res = await fetch(OPENROUTER_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      "HTTP-Referer": "https://spaceai-fc.app",
      "X-Title": "SpaceAI FC",
    },
    body: JSON.stringify({
      model: "anthropic/claude-sonnet-4-20250514",
      messages,
      max_tokens: 2000,
      temperature: 0.7,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    console.error("[SpaceAI LLM] OpenRouter error:", err);
    return null; // caller will fall back to backend
  }

  const data = await res.json();
  return data?.choices?.[0]?.message?.content ?? null;
}

/** Returns true if the OpenRouter API key is set */
export function isLLMConfigured(): boolean {
  const key = import.meta.env.VITE_OPENROUTER_API_KEY as string | undefined;
  return Boolean(key && key.length > 10);
}
