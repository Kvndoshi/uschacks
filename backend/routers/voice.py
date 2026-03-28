import asyncio
import json
import logging
from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect
from services import elevenlabs_service
from services.gemini_live import GeminiLiveSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe uploaded audio to text. Tries Gemini first, falls back to ElevenLabs."""
    audio_bytes = await file.read()
    if not audio_bytes:
        return {"ok": False, "text": "", "error": "Empty audio"}
    text = await _gemini_transcribe(audio_bytes)
    if not text:
        text = await elevenlabs_service.transcribe(audio_bytes)
    if text:
        return {"ok": True, "text": text}
    return {"ok": False, "text": "", "error": "Transcription failed"}


async def _gemini_transcribe(audio_bytes: bytes) -> str:
    """Transcribe audio using Gemini as primary transcription provider."""
    try:
        from google import genai
        from google.genai import types
        from config import GEMINI_API_KEY
        if not GEMINI_API_KEY:
            return ""
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = await client.aio.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                types.Part.from_text(
                    text="Transcribe this audio. Return only the transcription text, nothing else."
                ),
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/webm"),
            ],
            config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=512),
        )
        return (response.text or "").strip()
    except Exception as e:
        logger.debug("Gemini transcription failed: %s", e)
        return ""


@router.websocket("/ws/voice")
async def voice_ws(websocket: WebSocket):
    """Real-time voice session with automatic fallback."""
    await websocket.accept()
    session = GeminiLiveSession()

    connected = await session.connect()
    if not connected:
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"text": "Failed to initialize voice session. Check GEMINI_API_KEY."},
            })
        except Exception:
            pass
        await websocket.close()
        return

    try:
        await websocket.send_json({
            "type": "transcript",
            "data": {"text": "Voice session active. Start speaking.", "final": False},
        })
    except Exception:
        pass

    client_closed = asyncio.Event()

    async def receive_from_client():
        """Receive audio/text from frontend WebSocket."""
        try:
            while not client_closed.is_set():
                data = await websocket.receive()
                if "bytes" in data:
                    await session.send_audio(data["bytes"], mime_type="audio/pcm;rate=16000")
                elif "text" in data:
                    try:
                        msg = json.loads(data["text"])
                        if msg.get("type") == "text":
                            await session.send_text(msg.get("data", ""))
                    except json.JSONDecodeError:
                        pass
        except WebSocketDisconnect:
            client_closed.set()
        except Exception as e:
            logger.debug("Voice WS receive error: %s", e)
            client_closed.set()

    async def send_to_client():
        """Forward session responses to frontend WebSocket."""
        try:
            async for response in session.receive():
                if client_closed.is_set():
                    break
                try:
                    await websocket.send_json(response)
                except Exception:
                    break
        except Exception as e:
            logger.debug("Voice WS send error: %s", e)

    try:
        recv_task = asyncio.create_task(receive_from_client())
        send_task = asyncio.create_task(send_to_client())

        # Wait for the client to disconnect (recv_task will set client_closed)
        # Don't exit when send_task completes — it may just be a mode switch
        done, pending = await asyncio.wait(
            [recv_task, send_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # If only send finished (e.g. live→chunked switch), keep going
        # until the client disconnects
        if recv_task not in done and not client_closed.is_set():
            await recv_task

        for t in pending:
            t.cancel()
    finally:
        await session.close()
        try:
            await websocket.close()
        except Exception:
            pass
