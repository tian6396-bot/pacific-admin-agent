"""WebSocket：聊天会话房间 / 工单房间 / 坐席队列刷新。"""

from __future__ import annotations

from typing import Optional

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.core.security import decode_access_token
from src.db.session import get_session_factory
from src.services.auth_service import AuthService
from src.services.ws_hub import chat_ws_hub

router = APIRouter(tags=["chat-ws"])


@router.websocket("/chat/ws")
async def chat_ws(
    websocket: WebSocket,
    token: str = Query(...),
    session_id: Optional[str] = Query(default=None),
    room: Optional[str] = Query(default=None),
):
    """
    room 优先；否则用 session_id 作为房间。
    工单房间传 room=ticket:{id}；队列刷新 room=agent:queue。
    """
    try:
        payload = decode_access_token(token)
        user_id = str(payload.get("sub") or "")
        if not user_id:
            await websocket.close(code=4401)
            return
    except jwt.PyJWTError:
        await websocket.close(code=4401)
        return

    room_id = room or session_id
    if not room_id:
        await websocket.close(code=4400)
        return

    factory = get_session_factory()
    async with factory() as db:
        user = await AuthService(db).get_user(user_id)
        if user is None or not user.is_active:
            await websocket.close(code=4401)
            return

        if room_id.startswith("ticket:"):
            from src.repositories.ticket import TicketRepository

            ticket_id = room_id.split(":", 1)[1]
            ticket = await TicketRepository(db).get(ticket_id)
            if ticket is None:
                await websocket.close(code=4404)
                return
            if user.role == "employee" and ticket.employee_id != user.id:
                await websocket.close(code=4403)
                return
        elif room_id == "agent:queue":
            if user.role not in ("agent", "admin"):
                await websocket.close(code=4403)
                return
        elif not room_id.startswith("ticket:") and room is None:
            from src.repositories.chat import ChatRepository

            session = await ChatRepository(db).get_session(room_id, user.id)
            if session is None and user.role == "employee":
                await websocket.close(code=4404)
                return

    await chat_ws_hub.connect(room_id, websocket)
    try:
        await websocket.send_json(
            {"type": "status", "status": "connected", "room": room_id}
        )
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await chat_ws_hub.disconnect(room_id, websocket)
    except Exception:  # noqa: BLE001
        await chat_ws_hub.disconnect(room_id, websocket)
