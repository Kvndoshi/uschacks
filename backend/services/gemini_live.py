"""
Real-time voice session with Gemini.

Tries Gemini Live API first (native audio model). If that fails,
falls back to chunked transcription using the regular Gemini multimodal
API (same approach that works for the mic button), then generates
a chat response with live agent context.
"""
import asyncio
import base64
import logging
import time
from typing import Optional

from google import genai
from google.genai import types
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

LIVE_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
FLASH_MODEL = "gemini-3-flash-preview"

LIVE_SYSTEM_INSTRUCTION = (
    "You are Mindd, the Queen orchestrator of a browser automation swarm called Hivemind. "
    "You speak conversationally and concisely. Users talk to you via voice while AI agents "
    "are working in their browser tabs. Keep responses short (1-3 sentences). "
    "If asked what's happening, describe live agent activity. "
    "If the user gives a task, say you'll route it to the swarm."
)

# Chunked mode settings
SILENCE_THRESHOLD_S = 1.8
MIN_BUFFER_BYTES = 5000
TICK_S = 0.3


def _build_agent_context() -> str:
    """Build a brief context string about active agents."""
    try:
        from mind.worker import agent_logs
        from services.browser_manager import browser_manager

        active = browser_manager.agents
        if not active:
            return ""
        lines = []
        for agent_id in active:
            logs = agent_logs.get(agent_id, [])
            last = logs[-1] if logs else {}
            step = last.get("step", 0)
            msg = last.get("message", "starting...")[:60]
            lines.append(f"{agent_id} (step {step}): {msg}")
        return "\nActive agents: " + "; ".join(lines)
    except Exception:
        return ""


class GeminiLiveSession:
    """Voice session with automatic fallback.

    Tries Gemini Live API → if that fails, uses chunked transcription.
    """

    def __init__(self):
        self._active = False
        self._mode: str = ""  # "live" or "chunked"
        self._client: Optional[genai.Client] = None
        # Live API state
        self._session = None
        self._session_cm = None  # async context manager for cleanup
        # Chunked mode state
        self._audio_buffer = bytearray()
        self._last_audio_time: float = 0
        self._response_queue: asyncio.Queue = asyncio.Queue()
        self._process_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """Connect — try Live API first, fall back to chunked mode."""
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not set")
            return False

        self._client = genai.Client(api_key=GEMINI_API_KEY)

        # Try Gemini Live API
        if await self._try_live_connect():
            self._mode = "live"
            self._active = True
            logger.info("Voice session started (Gemini Live API, model=%s)", LIVE_MODEL)
            return True

        # Fall back to chunked transcription
        logger.warning("Gemini Live API failed — falling back to chunked transcription mode")
        self._mode = "chunked"
        self._active = True
        self._process_task = asyncio.create_task(self._chunked_process_loop())
        logger.info("Voice session started (chunked transcription mode)")
        return True

    async def _try_live_connect(self) -> bool:
        """Attempt to connect to Gemini Live API."""
        try:
            agent_context = _build_agent_context()
            system_text = LIVE_SYSTEM_INSTRUCTION + agent_context

            config = {
                "response_modalities": ["AUDIO"],
                "system_instruction": system_text,
            }
            session_cm = self._client.aio.live.connect(
                model=LIVE_MODEL,
                config=config,
            )
            self._session_cm = session_cm
            self._session = await session_cm.__aenter__()
            if not self._session:
                raise RuntimeError("Live session is None after connect")
            return True
        except Exception as e:
            logger.error("Gemini Live connect failed: %s", e)
            self._session = None
            self._session_cm = None
            return False

    async def send_audio(self, audio_chunk: bytes, mime_type: str = "audio/webm") -> None:
        """Send audio chunk. Live API needs PCM; browser sends webm so we
        buffer for chunked mode if format conversion isn't possible."""
        if not self._active:
            return

        if self._mode == "live" and self._session:
            try:
                await self._session.send_realtime_input(
                    audio=types.Blob(data=audio_chunk, mime_type=mime_type)
                )
            except Exception as e:
                logger.error("Live send failed, switching to chunked: %s", e)
                await self._switch_to_chunked()
                self._audio_buffer.extend(audio_chunk)
                self._last_audio_time = time.monotonic()
        else:
            self._audio_buffer.extend(audio_chunk)
            self._last_audio_time = time.monotonic()

    async def send_text(self, text: str) -> None:
        """Send text input."""
        if not self._active or not text.strip():
            return

        if self._mode == "live" and self._session:
            try:
                await self._session.send_realtime_input(text=text)
            except Exception as e:
                logger.error("Live text send failed: %s", e)
        else:
            # Chunked mode: generate response directly
            await self._chunked_respond(text.strip())

    async def receive(self):
        """Yield response messages for the frontend."""
        if self._mode == "live":
            async for msg in self._live_receive():
                yield msg
            # If live ended (normally or via switch), fall through to chunked
            if self._mode == "chunked" and self._active:
                async for msg in self._chunked_receive():
                    yield msg
        else:
            async for msg in self._chunked_receive():
                yield msg

    # ── Live API receive ──────────────────────────────────────────

    async def _live_receive(self):
        """Receive from Gemini Live API session.

        After this generator ends (normally or via exception), receive()
        checks self._mode and falls through to chunked if needed.
        """
        if not self._session:
            logger.warning("No live session object — switching to chunked")
            await self._switch_to_chunked()
            yield {
                "type": "transcript",
                "data": {"text": "(Using chunked voice mode)", "final": True},
            }
            return

        try:
            accumulated_text = ""
            async for response in self._session.receive():
                server_content = getattr(response, 'server_content', None)
                if not server_content:
                    continue

                # User speech transcription
                input_tx = getattr(server_content, 'input_transcription', None)
                if input_tx and getattr(input_tx, 'text', None):
                    yield {
                        "type": "transcript",
                        "data": {"text": input_tx.text, "final": True, "role": "user"},
                    }

                # Model speech transcription
                output_tx = getattr(server_content, 'output_transcription', None)
                if output_tx and getattr(output_tx, 'text', None):
                    accumulated_text += output_tx.text
                    yield {
                        "type": "transcript",
                        "data": {"text": accumulated_text, "final": False, "role": "model"},
                    }

                # Model audio/text parts
                parts = getattr(server_content, 'model_turn', None)
                if parts and hasattr(parts, 'parts'):
                    for part in parts.parts:
                        if hasattr(part, 'text') and part.text:
                            accumulated_text += part.text
                            yield {
                                "type": "transcript",
                                "data": {"text": accumulated_text, "final": False, "role": "assistant"},
                            }
                        if hasattr(part, 'inline_data') and part.inline_data:
                            audio_b64 = base64.b64encode(part.inline_data.data).decode()
                            yield {
                                "type": "speaking",
                                "data": {
                                    "text": accumulated_text,
                                    "audio_b64": audio_b64,
                                    "mime_type": part.inline_data.mime_type or "audio/pcm",
                                },
                            }

                turn_complete = getattr(server_content, 'turn_complete', False)
                if turn_complete:
                    if accumulated_text:
                        yield {
                            "type": "transcript",
                            "data": {"text": accumulated_text, "final": True, "role": "assistant"},
                        }
                    yield {"type": "done", "data": {}}
                    accumulated_text = ""
        except Exception as e:
            logger.error("Gemini Live receive error: %s", e)

        # Whether normal exit or exception, switch to chunked so receive()
        # can fall through to _chunked_receive()
        if self._active and self._mode == "live":
            logger.info("Live stream ended — switching to chunked mode")
            await self._switch_to_chunked()
            yield {
                "type": "transcript",
                "data": {"text": "(Switched to chunked voice mode)", "final": True},
            }

    # ── Chunked transcription ─────────────────────────────────────

    async def _switch_to_chunked(self):
        """Switch from live mode to chunked mode mid-session."""
        self._mode = "chunked"
        await self._close_live_session()
        if not self._process_task or self._process_task.done():
            self._process_task = asyncio.create_task(self._chunked_process_loop())

    async def _close_live_session(self):
        """Clean up live session and its context manager."""
        if self._session_cm:
            try:
                await self._session_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._session_cm = None
        elif self._session:
            try:
                await self._session.close()
            except Exception:
                pass
        self._session = None

    async def _chunked_receive(self):
        """Yield messages from the chunked response queue."""
        while self._active:
            try:
                msg = await asyncio.wait_for(self._response_queue.get(), timeout=30)
                yield msg
            except asyncio.TimeoutError:
                continue
            except Exception:
                break

    async def _chunked_process_loop(self):
        """Background loop: detect silence → transcribe → respond."""
        while self._active:
            await asyncio.sleep(TICK_S)

            if not self._audio_buffer:
                continue
            if time.monotonic() - self._last_audio_time < SILENCE_THRESHOLD_S:
                continue
            if len(self._audio_buffer) < MIN_BUFFER_BYTES:
                self._audio_buffer.clear()
                continue

            audio_data = bytes(self._audio_buffer)
            self._audio_buffer.clear()

            await self._response_queue.put({"type": "processing", "data": {}})

            transcript = await self._transcribe(audio_data)
            if not transcript:
                await self._response_queue.put({"type": "done", "data": {}})
                continue

            await self._response_queue.put({
                "type": "transcript",
                "data": {"text": transcript, "final": True, "role": "user"},
            })

            await self._chunked_respond(transcript)

    async def _transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio using regular Gemini multimodal API."""
        if not self._client:
            return ""
        try:
            response = await self._client.aio.models.generate_content(
                model=FLASH_MODEL,
                contents=[
                    types.Part.from_text(
                        text="Transcribe this audio exactly. Return ONLY the spoken words, nothing else. "
                             "If the audio is silence or noise, return an empty string."
                    ),
                    types.Part.from_bytes(data=audio_data, mime_type="audio/pcm;rate=16000"),
                ],
                config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=512),
            )
            text = (response.text or "").strip()
            if text.lower() in ("", "...", "(silence)", "(noise)", "(inaudible)"):
                return ""
            logger.info("Transcribed: %s", text[:80])
            return text
        except Exception as e:
            logger.error("Transcription failed: %s", e)
            return ""

    async def _chunked_respond(self, user_text: str):
        """Generate a chat response and push to queue."""
        if not self._client:
            return
        try:
            agent_context = _build_agent_context()
            system = LIVE_SYSTEM_INSTRUCTION + agent_context

            response = await self._client.aio.models.generate_content(
                model=FLASH_MODEL,
                contents=[
                    types.Content(role="user", parts=[types.Part.from_text(text=user_text)]),
                ],
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=256,
                    system_instruction=system,
                ),
            )
            reply = (response.text or "").strip() or "I didn't catch that."
            logger.info("Voice reply: %s", reply[:80])

            # Try TTS
            audio_b64 = ""
            try:
                from services import elevenlabs_service
                audio_b64 = await elevenlabs_service.announce(reply) or ""
            except Exception:
                pass

            await self._response_queue.put({
                "type": "speaking",
                "data": {"text": reply, "audio_b64": audio_b64},
            })
        except Exception as e:
            logger.error("Voice response failed: %s", e)
            await self._response_queue.put({
                "type": "speaking",
                "data": {"text": f"Sorry, error: {e}", "audio_b64": ""},
            })

        await self._response_queue.put({"type": "done", "data": {}})

    # ── Lifecycle ─────────────────────────────────────────────────

    async def close(self):
        """Shut down the session."""
        self._active = False
        await self._close_live_session()
        if self._process_task and not self._process_task.done():
            self._process_task.cancel()
            try:
                await self._process_task
            except (asyncio.CancelledError, Exception):
                pass
        self._audio_buffer.clear()
        logger.info("Voice session closed")

    @property
    def is_active(self) -> bool:
        return self._active
