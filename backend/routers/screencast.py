"""
CDP Screencast WebSocket bridge (direct frame streaming for fast first-frame).

Frontend connects to /ws/tabs/{tab_id}/screencast.
- CDP Page.startScreencast frames are forwarded as {"type":"frame","data":"<base64>"}.
- URL updates: {"type":"url","url":"..."}.
- Input: same WebSocket, {"action":"click", ...} etc.
Tuned for low latency: smaller size, lower quality, immediate ack.
"""
import asyncio
import json
import logging
import aiohttp
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.tab_manager import tab_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Tuned for fast first-frame and lower latency (smaller payload, lower quality)
CDP_SCREENCAST_PARAMS = {
    "format": "jpeg",
    "quality": 40,
    "maxWidth": 960,
    "maxHeight": 600,
    "everyNthFrame": 1,
}


@router.websocket("/ws/tabs/{tab_id}/screencast")
async def screencast_ws(websocket: WebSocket, tab_id: str):
    await websocket.accept()

    ws_url = tab_manager.get_cdp_ws_url(tab_id)
    if not ws_url:
        await websocket.send_json({"type": "error", "message": "Tab not found or CDP unavailable"})
        await websocket.close()
        return

    tab_manager.register_screencast(tab_id)
    msg_id_counter = [100]

    def next_id() -> int:
        msg_id_counter[0] += 1
        return msg_id_counter[0]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url, timeout=aiohttp.ClientTimeout(total=None), origin="http://localhost:9222") as cdp_ws:
                await cdp_ws.send_json({"id": 1, "method": "Page.enable", "params": {}})
                await cdp_ws.send_json({
                    "id": 2,
                    "method": "Page.startScreencast",
                    "params": CDP_SCREENCAST_PARAMS,
                })

                async def from_frontend():
                    """Read commands from frontend, dispatch to Chrome CDP."""
                    while True:
                        try:
                            raw = await websocket.receive_text()
                        except WebSocketDisconnect:
                            return
                        try:
                            msg = json.loads(raw)
                        except Exception:
                            continue

                        action = msg.get("action")
                        mid = next_id()
                        if action == "navigate":
                            await cdp_ws.send_json({
                                "id": mid,
                                "method": "Page.navigate",
                                "params": {"url": msg.get("url", "about:blank")},
                            })
                        elif action == "goBack":
                            await cdp_ws.send_json({"id": mid, "method": "Page.goBack", "params": {}})
                        elif action == "goForward":
                            await cdp_ws.send_json({"id": mid, "method": "Page.goForward", "params": {}})
                        elif action == "click":
                            x, y = float(msg.get("x", 0)), float(msg.get("y", 0))
                            await cdp_ws.send_json({"id": mid, "method": "Input.dispatchMouseEvent",
                                "params": {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1}})
                            await cdp_ws.send_json({"id": mid + 1, "method": "Input.dispatchMouseEvent",
                                "params": {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1}})
                        elif action == "mousemove":
                            x, y = float(msg.get("x", 0)), float(msg.get("y", 0))
                            await cdp_ws.send_json({"id": mid, "method": "Input.dispatchMouseEvent",
                                "params": {"type": "mouseMoved", "x": x, "y": y}})
                        elif action == "scroll":
                            x, y = float(msg.get("x", 0)), float(msg.get("y", 0))
                            dx, dy = float(msg.get("delta_x", 0)), float(msg.get("delta_y", 0))
                            await cdp_ws.send_json({"id": mid, "method": "Input.dispatchMouseEvent",
                                "params": {"type": "mouseWheel", "x": x, "y": y, "deltaX": dx, "deltaY": dy}})
                        elif action == "type":
                            for i, ch in enumerate(msg.get("text", "")):
                                await cdp_ws.send_json({"id": mid + i, "method": "Input.dispatchKeyEvent",
                                    "params": {"type": "char", "text": ch}})
                        elif action == "keydown":
                            key = msg.get("key", "")
                            params: dict = {"type": "keyDown", "key": key}
                            if key == "Enter":
                                params.update({"code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13})
                            elif key == "Backspace":
                                params.update({"code": "Backspace", "windowsVirtualKeyCode": 8, "nativeVirtualKeyCode": 8})
                            elif key == "Tab":
                                params.update({"code": "Tab", "windowsVirtualKeyCode": 9, "nativeVirtualKeyCode": 9})
                            elif key == "Escape":
                                params.update({"code": "Escape", "windowsVirtualKeyCode": 27, "nativeVirtualKeyCode": 27})
                            await cdp_ws.send_json({"id": mid, "method": "Input.dispatchKeyEvent", "params": params})
                            params_up = dict(params)
                            params_up["type"] = "keyUp"
                            await cdp_ws.send_json({"id": mid + 1, "method": "Input.dispatchKeyEvent", "params": params_up})

                async def from_cdp():
                    """Forward frames and URL changes to frontend (no WebRTC)."""
                    async for msg in cdp_ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                            except Exception:
                                continue
                            method = data.get("method", "")
                            if method == "Page.screencastFrame":
                                params = data.get("params", {})
                                frame_data = params.get("data", "")
                                session_id = params.get("sessionId", 0)
                                await cdp_ws.send_json({
                                    "id": next_id(),
                                    "method": "Page.screencastFrameAck",
                                    "params": {"sessionId": session_id},
                                })
                                if frame_data:
                                    try:
                                        await websocket.send_json({"type": "frame", "data": frame_data})
                                    except Exception:
                                        return
                            elif method in ("Page.frameNavigated", "Page.navigatedWithinDocument"):
                                params = data.get("params", {})
                                url = params.get("url") or params.get("frame", {}).get("url", "")
                                if url:
                                    try:
                                        await websocket.send_json({"type": "url", "url": url})
                                    except Exception:
                                        return
                        elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
                            return

                tasks = [
                    asyncio.create_task(from_frontend()),
                    asyncio.create_task(from_cdp()),
                ]
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for t in pending:
                    t.cancel()
                try:
                    await cdp_ws.send_json({"id": next_id(), "method": "Page.stopScreencast", "params": {}})
                except Exception:
                    pass
    except Exception as e:
        logger.debug("Screencast %s ended: %s", tab_id, e)
    finally:
        tab_manager.unregister_screencast(tab_id)
        try:
            await websocket.close()
        except Exception:
            pass
