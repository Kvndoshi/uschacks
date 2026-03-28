import asyncio
import json
import logging
from fastapi import WebSocket
from models.events import WSEvent, ping
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._heartbeat_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, event: WSEvent):
        message = event.model_dump_json()
        dead = []
        for conn in self.active_connections:
            try:
                await conn.send_text(message)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, event: WSEvent):
        try:
            await websocket.send_text(event.model_dump_json())
        except Exception:
            self.disconnect(websocket)

    async def start_heartbeat(self, interval: int = 10):
        async def _beat():
            while True:
                await asyncio.sleep(interval)
                await self.broadcast(ping(datetime.utcnow().isoformat()))
        self._heartbeat_task = asyncio.create_task(_beat())

    async def stop_heartbeat(self):
        if self._heartbeat_task:
            self._heartbeat_task.cancel()


manager = ConnectionManager()
