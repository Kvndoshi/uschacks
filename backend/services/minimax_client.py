import asyncio
import logging
from typing import Optional
from openai import AsyncOpenAI

from config import (
    MINIMAX_API_KEY,
    MINIMAX_BASE_URL,
    MINIMAX_MODEL,
)

logger = logging.getLogger(__name__)

_minimax_client: AsyncOpenAI | None = None

def get_client() -> AsyncOpenAI:
    """Return the MiniMax client using OpenAI SDK."""
    global _minimax_client
    if _minimax_client is None:
        _minimax_client = AsyncOpenAI(
            api_key=MINIMAX_API_KEY,
            base_url=MINIMAX_BASE_URL,
        )
    return _minimax_client

async def _call_minimax(model: str, messages: list[dict], temperature: float, max_tokens: int, retries: int = 3) -> str:
    """Call MiniMax with retry on transient errors."""
    client = get_client()
    last_err = None
    for attempt in range(retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            last_err = e
            err_str = str(e)
            if "503" in err_str or "429" in err_str or "timeout" in err_str.lower():
                wait = 2 ** attempt + 1
                logger.warning("MiniMax transient error (attempt %d/%d), retrying in %ds: %s",
                                 attempt + 1, retries, wait, err_str[:120])
                await asyncio.sleep(wait)
            else:
                raise
    raise last_err  # type: ignore[misc]

async def minimax_chat(
    messages: list[dict],
    model: str = MINIMAX_MODEL,  # Default model for Person C's task logic
    temperature: float = 0.5,
    max_tokens: int = 1024,
) -> str:
    """Chat using MiniMax platform.

    Accepts a list of dicts with 'role' and 'content' keys (OpenAI-style).
    """
    return await _call_minimax(model, messages, temperature, max_tokens)

async def minimax_chat_stream(
    messages: list[dict],
    model: str = MINIMAX_MODEL,
    temperature: float = 0.5,
    max_tokens: int = 1024,
):
    """Streaming chat using MiniMax platform. Yields text chunks as they arrive."""
    client = get_client()

    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
