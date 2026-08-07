"""进程内 WebSocket 连接管理：按 session 推送事件。"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from pycore.core import get_logger

logger = get_logger()


class ChatWSHub:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._rooms[session_id].add(ws)
        logger.info("WS connected", session_id=session_id)

    async def disconnect(self, session_id: str, ws: WebSocket) -> None:
        async with self._lock:
            room = self._rooms.get(session_id)
            if not room:
                return
            room.discard(ws)
            if not room:
                self._rooms.pop(session_id, None)
        logger.info("WS disconnected", session_id=session_id)

    async def broadcast(self, session_id: str, event: dict[str, Any]) -> None:
        payload = json.dumps(event, ensure_ascii=False, default=str)
        async with self._lock:
            peers = list(self._rooms.get(session_id, set()))
        dead: list[WebSocket] = []
        for ws in peers:
            try:
                await ws.send_text(payload)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        for ws in dead:
            await self.disconnect(session_id, ws)


chat_ws_hub = ChatWSHub()
