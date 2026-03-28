# Browser tab streaming: options for fast processing

This project uses **CDP (Chrome DevTools Protocol) screencast over WebSocket**: backend forwards `Page.screencastFrame` as base64 JPEGs; frontend shows them in an `<img>`. Tuned for fast first-frame (960×600, quality 40).

## Other approaches (for reference)

| Approach | Latency | Pros | Cons |
|----------|---------|------|------|
| **Direct WebSocket frames (current)** | First frame as soon as CDP sends | Simple, no handshake, works everywhere | Higher bandwidth (full JPEG per frame) |
| **WebRTC (aiortc)** | Slower first frame (offer/answer/ICE + encode) | VP8/H.264, lower bandwidth once connected | Complex, “waiting for video stream” delay |
| **JSMpeg (MPEG1 over WebSocket)** | ~50 ms on LAN | Low latency, small decoder, no WebRTC | Backend must encode to MPEG-TS (e.g. ffmpeg); extra pipeline |
| **WebTransport + WebCodecs** | ~200 ms | Modern, low latency | No Safari/iOS; more implementation work |
| **Hyperbeam / Anchor Browser** | Service-dependent | Managed “browser in browser”, APIs | Third-party, not self-hosted CDP |
| **noVNC (VNC over WebSocket)** | 1–2 s typical | Embed full desktop/browser via VNC | Need VNC server + websockify; heavier |

## Tuning CDP screencast (current stack)

In `backend/routers/screencast.py`, `CDP_SCREENCAST_PARAMS`:

- **Lower quality** (e.g. 30–40): faster encode, smaller frames.
- **Smaller maxWidth/maxHeight**: less data, quicker first paint.
- **everyNthFrame: 2** or **3**: skip frames to reduce load if 60 FPS is not needed.

For even faster first-frame at the cost of resolution, try e.g. `maxWidth: 640`, `maxHeight: 400`, `quality: 30`.
