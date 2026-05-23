"""Groq LLM client (OpenAI-compatible chat API)."""

import asyncio

from app.config import settings


def _chat_sync(system: str, user: str, max_tokens: int = 600) -> str:
    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    resp = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return (resp.choices[0].message.content or "").strip()


async def groq_chat(system: str, user: str, max_tokens: int = 600) -> str | None:
    if not settings.groq_api_key:
        return None
    try:
        return await asyncio.to_thread(_chat_sync, system, user, max_tokens)
    except Exception:
        return None


def groq_available() -> bool:
    return bool(settings.groq_api_key)
