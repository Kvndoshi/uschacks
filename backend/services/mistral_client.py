import asyncio
import json
import logging
from typing import Optional
from google import genai
from google.genai import types
from config import (
    GEMINI_API_KEY,
    QUEEN_MODEL,
    CHAT_MODEL,
)

logger = logging.getLogger(__name__)

_queen_client: genai.Client | None = None

QUEEN_SYSTEM_PROMPT = """You are the Queen — the orchestrator of a multi-agent browser automation system called Hivemind.

You receive a user's request and translate it into precise, actionable tasks for browser-use agents. Each agent controls one Chrome tab and can: navigate, click, scroll, extract, search_page, find_elements, input, send_keys, wait, go_back, screenshot, read_file, write_file, and done.

YOUR CORE RESPONSIBILITY: Understand the user's TRUE INTENT, then write clear, specific task descriptions.

INTENT INTERPRETATION:
- The user speaks casually. You must interpret their intent and produce professional, detailed instructions.
- "write a draft saying I met you at an event" means: compose a warm, professional email referencing meeting the recipient at a recent event.
- "search for flights" means: go to a flight search engine, enter the route and dates, search, and extract results.
- Always expand vague instructions into concrete browser actions with specific URLs and UI element names.

AGENT COUNT RULES:
- 1 agent for any task involving a single website or a sequential flow
- 2+ agents ONLY when the task explicitly requires parallel work on DIFFERENT websites
- Examples:
  - "Draft an email to John" → 1 agent
  - "Compare prices on Amazon AND eBay" → 2 agents (different sites, parallel)
  - "Find flights on Google Flights" → 1 agent

WRITING TASK DESCRIPTIONS (browser-use optimized):
Each agent's description must follow this format: [Specific verb] + [what] + [where] + [constraints] + [expected output]

Rules:
1. Reference browser-use actions by name: navigate, click, input, send_keys, extract, search_page, find_elements, scroll, done.
2. For simple tasks, keep descriptions concise — the agent plans well on its own for open-ended goals.
3. For specific tasks, provide step-by-step instructions with exact UI element names and selectors.
4. Include the target URL in the description so the agent auto-navigates.
5. Specify expected output format: "Extract the title, price, and rating as a structured list."
6. For filters/sorting: tell the agent to apply filters BEFORE scrolling through results.
7. End with a clear completion condition: "Once you have collected 5 results, use the done action with the results."

CONTENT GENERATION: When the user asks to write/draft/compose something, YOU write the actual content in the agent's instructions. The agent types what you tell it.
   Bad: "Type a message about meeting at an event"
   Good: "In the compose body, input the following message:\n\nHi [Name],\n\nIt was great meeting you at the event!..."

EMAIL SAFETY: For email/message tasks, ALWAYS end with: "After typing the message, STOP. Do NOT click Send — the user will review and send manually."

CRITICAL SAFETY RULES:
- NEVER navigate to or interact with localhost or 127.0.0.1 URLs
- Each agent gets exactly 1 tab. Do NOT instruct an agent to open new tabs
- NEVER instruct an agent to click Send/Submit on emails, messages, forms, or payments
- The description MUST be a single string, NOT an array

MULTI-AGENT COORDINATION:
- Each agent works independently on ONE tab. They cannot see each other's work.
- Write task descriptions that are self-contained — include all URLs, search terms, and expected output format.
- Each subtask must specify the EXACT website/URL to operate on.
- Include explicit boundaries: "Only work on [site]. Do NOT navigate elsewhere."
- For comparison tasks, each agent gets ONE site and a structured output format so results can be merged.

TAB ALLOCATION:
- If open_tabs are provided and one matches the task domain, assign that tab via tab_hint
- Otherwise the system will allocate a blank tab

Return ONLY a JSON array (no other text):
[{"description": "task description as a single string", "url": "https://... or null", "tab_hint": "existing tab URL to reuse or null"}]"""


def _get_queen_client() -> genai.Client:
    """Return the Queen orchestrator client (native Google GenAI SDK)."""
    global _queen_client
    if _queen_client is None:
        _queen_client = genai.Client(api_key=GEMINI_API_KEY)
    return _queen_client


QUEEN_FALLBACK_MODEL = "gemini-2.5-flash"


async def _call_gemini(client, model: str, user_message: str, config, retries: int = 3) -> str:
    """Call a Gemini model with retry on transient errors."""
    last_err = None
    for attempt in range(retries):
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=user_message,
                config=config,
            )
            return response.text or ""
        except Exception as e:
            last_err = e
            err_str = str(e)
            if "503" in err_str or "429" in err_str or "UNAVAILABLE" in err_str or "overloaded" in err_str.lower():
                wait = 2 ** attempt + 1
                logger.warning("Gemini %s transient error (attempt %d/%d), retrying in %ds: %s",
                               model, attempt + 1, retries, wait, err_str[:120])
                await asyncio.sleep(wait)
            else:
                raise
    raise last_err  # type: ignore[misc]


async def queen_chat(
    user_message: str,
    system_prompt: str = "",
    temperature: float = 0.2,
    max_output_tokens: int = 2048,
) -> str:
    """Send a prompt to the Queen LLM (Gemini) with automatic fallback.

    Tries QUEEN_MODEL first (with retries), then falls back to
    gemini-2.5-flash if the primary model is overloaded."""
    client = _get_queen_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    if system_prompt:
        config.system_instruction = system_prompt

    try:
        return await _call_gemini(client, QUEEN_MODEL, user_message, config, retries=3)
    except Exception as primary_err:
        err_str = str(primary_err)
        if "503" in err_str or "429" in err_str or "UNAVAILABLE" in err_str:
            logger.warning("Primary model %s exhausted retries, falling back to %s", QUEEN_MODEL, QUEEN_FALLBACK_MODEL)
            return await _call_gemini(client, QUEEN_FALLBACK_MODEL, user_message, config, retries=2)
        raise


async def queen_decompose(task: str, context: str = "", open_tabs: Optional[list[str]] = None) -> list[dict]:
    prompt = f"Task: {task}"
    if context:
        prompt += f"\nContext: {context}"
    if open_tabs:
        prompt += f"\nCurrently open tabs (prefer using these when relevant): {', '.join(open_tabs)}"

    content = await queen_chat(
        user_message=prompt,
        system_prompt=QUEEN_SYSTEM_PROMPT,
        temperature=0.2,
        max_output_tokens=2048,
    )
    logger.info(f"Queen decomposition raw: {content[:300]}")

    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        subtasks = json.loads(content.strip())
        if isinstance(subtasks, list):
            return subtasks
        raise ValueError("Not a list")
    except Exception as e:
        logger.error(f"Failed to parse Queen response: {e} — falling back to single task")
        return [{"description": task, "url": None, "depends_on": [], "priority": 1}]


async def gemini_chat(
    messages: list[dict],
    temperature: float = 0.5,
    max_output_tokens: int = 1024,
) -> str:
    """Chat using Gemini 2.0 Flash (for conversational responses).

    Accepts a list of dicts with 'role' and 'content' keys (OpenAI-style),
    including an optional system message as the first entry.
    """
    client = _get_queen_client()

    # Extract system prompt from messages
    system = next((m["content"] for m in messages if m["role"] == "system"), "")

    # Build conversation content as a list of Content objects
    contents = []
    for m in messages:
        if m["role"] == "system":
            continue
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    if system:
        config.system_instruction = system

    return await _call_gemini(client, CHAT_MODEL, contents, config, retries=2)


async def gemini_chat_stream(
    messages: list[dict],
    temperature: float = 0.5,
    max_output_tokens: int = 1024,
):
    """Streaming chat using Gemini Flash. Yields text chunks as they arrive.

    Accepts a list of dicts with 'role' and 'content' keys (OpenAI-style).
    """
    client = _get_queen_client()

    system = next((m["content"] for m in messages if m["role"] == "system"), "")

    contents = []
    for m in messages:
        if m["role"] == "system":
            continue
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    if system:
        config.system_instruction = system

    stream = await client.aio.models.generate_content_stream(
        model=CHAT_MODEL, contents=contents, config=config,
    )
    async for chunk in stream:
        if chunk.text:
            yield chunk.text
