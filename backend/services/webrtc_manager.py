"""
WebRTC manager for browser screencast streaming.

Provides BrowserVideoTrack (feeds CDP JPEG frames into a WebRTC video track)
and WebRTCSession (signaling and one RTCPeerConnection per viewer).
"""
import asyncio
import logging
from typing import Optional

import cv2
import numpy as np
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamError
from av import VideoFrame

logger = logging.getLogger(__name__)

# Reduce av frame logging
logging.getLogger("av").setLevel(logging.WARNING)


class BrowserVideoTrack(MediaStreamTrack):
    """
    Video track that receives CDP screencast JPEG frames and yields VideoFrames
    for WebRTC. Frames are pushed from the CDP handler and consumed by recv().
    """

    kind = "video"

    def __init__(self) -> None:
        super().__init__()
        self._queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=2)
        self._closed = False

    def push_frame(self, jpeg_bytes: bytes) -> None:
        """Called by the CDP screencast handler. Drops frame if queue full."""
        if self._closed:
            return
        try:
            self._queue.put_nowait(jpeg_bytes)
        except asyncio.QueueFull:
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(jpeg_bytes)
            except (asyncio.QueueEmpty, asyncio.QueueFull):
                pass

    async def recv(self) -> VideoFrame:
        if self._closed:
            raise MediaStreamError("Track closed")
        jpeg_bytes = await self._queue.get()
        try:
            nparr = np.frombuffer(jpeg_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                img = np.zeros((480, 640, 3), dtype=np.uint8)
            frame = VideoFrame.from_ndarray(img, format="bgr24")
            frame.pts, frame.time_base = await self.next_timestamp()
            return frame
        except Exception as e:
            logger.debug("BrowserVideoTrack decode error: %s", e)
            frame = VideoFrame.from_ndarray(
                np.zeros((480, 640, 3), dtype=np.uint8), format="bgr24"
            )
            frame.pts, frame.time_base = await self.next_timestamp()
            return frame

    def stop(self) -> None:
        self._closed = True
        super().stop()


class WebRTCSession:
    """
    Manages one RTCPeerConnection for a single viewer. Handles offer/answer
    and ICE candidate exchange. The video track is fed by the CDP screencast loop.
    """

    def __init__(self, video_track: BrowserVideoTrack, on_ice_candidate=None) -> None:
        self._pc = RTCPeerConnection()
        self._track = video_track
        self._on_ice_candidate = on_ice_candidate

    async def handle_offer(self, sdp: str, type_: str) -> tuple[str, str]:
        """Set remote description (offer), create answer, return (sdp, type)."""
        offer = RTCSessionDescription(sdp=sdp, type=type_)
        self._pc.addTrack(self._track)
        if self._on_ice_candidate:
            self._pc.on("icecandidate", self._on_ice_candidate)
        await self._pc.setRemoteDescription(offer)
        answer = await self._pc.createAnswer()
        await self._pc.setLocalDescription(answer)
        assert self._pc.localDescription
        return self._pc.localDescription.sdp, self._pc.localDescription.type

    async def add_ice_candidate(self, candidate: dict) -> None:
        """Add a remote ICE candidate from client. candidate has 'candidate', 'sdpMid', 'sdpMLineIndex'."""
        raw = candidate.get("candidate", "").strip()
        if not raw:
            return
        if raw.startswith("candidate:"):
            raw = raw[10:].strip()
        try:
            from aiortc.sdp import candidate_from_sdp

            ice = candidate_from_sdp(raw)
            ice.sdpMid = candidate.get("sdpMid")
            ice.sdpMLineIndex = candidate.get("sdpMLineIndex")
            await self._pc.addIceCandidate(ice)
        except Exception as e:
            logger.debug("addIceCandidate failed: %s", e)

    async def close(self) -> None:
        """Close peer connection and stop track."""
        self._track.stop()
        await self._pc.close()
