import base64
import logging
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL_ID

logger = logging.getLogger(__name__)

try:
    from elevenlabs import AsyncElevenLabs
    _ELEVENLABS_AVAILABLE = True
except ImportError:
    _ELEVENLABS_AVAILABLE = False
    logger.warning("elevenlabs package not installed — TTS disabled. Run: pip install elevenlabs")

_client = None


def get_client():
    global _client
    if not _ELEVENLABS_AVAILABLE:
        return None
    if _client is None:
        from elevenlabs import AsyncElevenLabs
        _client = AsyncElevenLabs(api_key=ELEVENLABS_API_KEY)
    return _client


async def announce(text: str) -> str:
    """Generate TTS audio and return base64-encoded MP3 string."""
    if not _ELEVENLABS_AVAILABLE or not ELEVENLABS_API_KEY:
        return ""

    try:
        client = get_client()
        if client is None:
            return ""

        audio_iter = client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            text=text,
            model_id=ELEVENLABS_MODEL_ID,
        )

        chunks = []
        try:
            async for chunk in audio_iter:
                chunks.append(chunk)
        except TypeError:
            for chunk in audio_iter:
                chunks.append(chunk)

        audio_bytes = b"".join(chunks)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        logger.info(f"Generated TTS: '{text[:50]}' ({len(audio_bytes)} bytes)")
        return audio_b64
    except Exception as e:
        logger.error(f"ElevenLabs TTS failed: {e}")
        return ""


async def transcribe(audio_bytes: bytes) -> str:
    """Transcribe audio bytes using ElevenLabs Scribe v2. Returns text.

    Note: This is used as a fallback when Gemini transcription is unavailable.
    Primary transcription is handled by routers.voice._gemini_transcribe().
    """
    if not _ELEVENLABS_AVAILABLE or not ELEVENLABS_API_KEY:
        return ""

    try:
        client = get_client()
        if client is None:
            return ""

        result = await client.speech_to_text.convert(
            file=audio_bytes,
            model_id="scribe_v1",
        )
        text = getattr(result, "text", "") or ""
        logger.info("STT transcribed: '%s'", text[:80])
        return text.strip()
    except Exception as e:
        logger.error("ElevenLabs STT failed: %s", e)
        return ""
