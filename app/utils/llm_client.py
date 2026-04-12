"""
SpaceAI FC - OpenRouter LLM Client
=====================================
Synchronous client for OpenRouter API using Claude Sonnet.
Falls back gracefully when OPENROUTER_API_KEY is not set.
"""

import os
import requests


def call_openrouter(
    system_prompt: str,
    user_message: str,
    model: str = "anthropic/claude-sonnet-4-20250514",
) -> str | None:
    """
    Send a chat completion request to OpenRouter.

    Returns the assistant response text, or None if:
      - No API key is set
      - The request fails
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return None

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 2000,
            },
            timeout=60.0,
        )

        if response.status_code != 200:
            return None

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception:
        return None


def is_llm_available() -> bool:
    """Return True when an OpenRouter API key is configured."""
    return os.environ.get("OPENROUTER_API_KEY") is not None
