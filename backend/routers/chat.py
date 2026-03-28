import json
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.mistral_client import gemini_chat, gemini_chat_stream
from services import supermemory_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

CHAT_SYSTEM = (
    "You are Mindd, an AI assistant with browser automation capabilities. "
    "You answer questions conversationally, clearly, and concisely. "
    "If the user asks you to do something on a webpage, tell them to use "
    "the task command bar instead. For everything else, answer directly. "
    "You have access to memories from past tasks and conversations — use them "
    "to give informed, contextual answers when relevant."
)

CHAT_SYSTEM_AWARE = (
    "You are Mindd, the Queen orchestrator of a browser automation swarm. "
    "You can see what agents are doing in real-time. When asked 'what's happening?', "
    "describe live agent activity. Summarize findings when agents complete. "
    "Be conversational, concise, specific. Speak as the coordinator who knows everything."
)

conversation_history: list[dict] = []


class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


def _build_agent_context() -> str:
    """Build a context string describing live agent status and completed results."""
    parts = []

    try:
        from mind.worker import agent_logs
        from services.browser_manager import browser_manager

        active_agents = browser_manager.agents
        if active_agents:
            lines = []
            for agent_id in active_agents:
                logs = agent_logs.get(agent_id, [])
                recent = logs[-3:] if logs else []
                log_summary = ", ".join(
                    f"{l.get('action', '')}: {l.get('message', '')[:60]}"
                    for l in recent
                ) if recent else "starting..."
                url = recent[-1].get("url", "") if recent else ""
                step = recent[-1].get("step", 0) if recent else 0
                lines.append(
                    f"- {agent_id} (running, step {step}): {log_summary}"
                    + (f" | URL: {url}" if url else "")
                )
            if lines:
                parts.append("\n\nLIVE AGENT STATUS:\n" + "\n".join(lines))
    except Exception as e:
        logger.debug("Agent context build skipped: %s", e)

    try:
        from mind.memory import get_active_memory
        memory = get_active_memory()
        if memory and memory.completed_subtasks:
            result_lines = []
            for r in memory.completed_subtasks[-5:]:
                result_lines.append(f"- Agent {r.subtask_id}: {r.result[:200]}")
            if result_lines:
                parts.append(
                    "\n\nCOMPLETED RESULTS FROM MEMORY:\n" + "\n".join(result_lines)
                )
    except Exception as e:
        logger.debug("Memory context build skipped: %s", e)

    return "".join(parts)


async def _get_memory_block(query: str) -> str:
    """Search supermemory for relevant context."""
    try:
        memories = await supermemory_service.search_memory(query, limit=3)
        if memories:
            snippets = []
            for m in memories:
                text = m.get("summary") or m.get("content") or ""
                if text:
                    snippets.append(text[:300])
            if snippets:
                return "\n\nRelevant memories from past tasks/conversations:\n" + "\n---\n".join(snippets)
    except Exception as e:
        logger.debug("Supermemory search skipped in chat: %s", e)
    return ""


@router.post("/", response_model=ChatResponse)
async def chat(msg: ChatMessage):
    conversation_history.append({"role": "user", "content": msg.message})

    memory_block = await _get_memory_block(msg.message)
    agent_context = _build_agent_context()

    system_msg = CHAT_SYSTEM_AWARE if agent_context else CHAT_SYSTEM
    system_msg += agent_context + memory_block

    messages = [{"role": "system", "content": system_msg}] + conversation_history[-20:]

    try:
        reply = await gemini_chat(messages, temperature=0.5, max_output_tokens=1024)
        if not reply:
            reply = "I couldn't generate a response."
        conversation_history.append({"role": "assistant", "content": reply})

        try:
            await supermemory_service.save_chat_exchange(msg.message, reply)
        except Exception:
            pass

        return ChatResponse(reply=reply)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(reply=f"Error: {str(e)}")


@router.post("/stream")
async def chat_stream(msg: ChatMessage):
    """SSE streaming chat endpoint with live agent context."""
    conversation_history.append({"role": "user", "content": msg.message})

    memory_block = await _get_memory_block(msg.message)
    agent_context = _build_agent_context()

    system_msg = CHAT_SYSTEM_AWARE if agent_context else CHAT_SYSTEM
    system_msg += agent_context + memory_block

    messages = [{"role": "system", "content": system_msg}] + conversation_history[-20:]

    async def generate():
        full_reply = ""
        try:
            async for chunk in gemini_chat_stream(messages, temperature=0.5, max_output_tokens=1024):
                full_reply += chunk
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            error_msg = f"Error: {str(e)}"
            full_reply = error_msg
            yield f"data: {json.dumps({'text': error_msg})}\n\n"

        yield "data: [DONE]\n\n"
        conversation_history.append({"role": "assistant", "content": full_reply})

        try:
            await supermemory_service.save_chat_exchange(msg.message, full_reply)
        except Exception:
            pass

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.delete("/history")
async def clear_history():
    conversation_history.clear()
    return {"status": "cleared"}
