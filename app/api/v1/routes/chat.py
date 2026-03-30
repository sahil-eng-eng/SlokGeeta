"""Chat routes — HTTP + WebSocket.

GET  /chat/conversations              — list recent conversations
GET  /chat/messages/{user_id}         — get message history (cursor-based)
POST /chat/messages/{user_id}/seen    — mark conversation as seen
WS   /chat/ws?token=<jwt>             — real-time channel
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, AsyncSessionLocal
from app.core.dependencies import get_current_user
from app.core.security import decode_token
from app.core.ws_manager import ws_manager
from app.models.user import User
from app.services.chat import ChatService
from app.core.responses import ApiResponse
from app.constants.messages import CHAT_MESSAGES
from app.schemas.chat import MessageBody, EditMessageBody
import json

router = APIRouter(prefix="/chat", tags=["chat"])


def _get_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)


@router.get("/conversations", response_model=None)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(_get_service),
):
    results = await service.list_conversations(current_user.id)
    return ApiResponse(
        status_code=200,
        data=[r.model_dump() for r in results],
        message=CHAT_MESSAGES["CONVERSATIONS_RETRIEVED"],
    )


@router.post("/messages/{partner_id}", response_model=None, status_code=201)
async def send_message(
    partner_id: str,
    body: MessageBody,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(_get_service),
):
    result = await service.send_message(current_user.id, partner_id, body.content)
    return ApiResponse(
        status_code=201,
        data=result.model_dump(mode="json"),
        message=CHAT_MESSAGES["MESSAGE_SENT"],
    )


@router.get("/messages/{partner_id}", response_model=None)
async def get_conversation(
    partner_id: str,
    limit: int = Query(default=50, le=100),
    before_id: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(_get_service),
):
    result = await service.get_conversation(current_user.id, partner_id, limit, before_id)
    return ApiResponse(status_code=200, data=result.model_dump(), message=CHAT_MESSAGES["MESSAGES_RETRIEVED"])


@router.post("/messages/{partner_id}/seen", status_code=204)
async def mark_seen(
    partner_id: str,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(_get_service),
):
    await service.mark_conversation_seen(current_user.id, partner_id)


@router.delete("/messages/{message_id}", response_model=None)
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(_get_service),
):
    result = await service.delete_message(message_id, current_user.id)
    return ApiResponse(status_code=200, data=result.model_dump(mode="json"), message=CHAT_MESSAGES["MESSAGE_DELETED"])


@router.patch("/messages/{message_id}", response_model=None)
async def edit_message(
    message_id: str,
    body: EditMessageBody,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(_get_service),
):
    result = await service.edit_message(message_id, current_user.id, body.content)
    return ApiResponse(status_code=200, data=result.model_dump(mode="json"), message=CHAT_MESSAGES["MESSAGE_EDITED"])


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint.
    Clients pass their JWT as ?token=<jwt> since WS cannot send Authorization headers.
    """
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            event_type = data.get("type")
            if event_type == "typing":
                receiver_id = data.get("receiver_id")
                if receiver_id:
                    await ws_manager.send_to_user(
                        receiver_id,
                        {"type": "typing", "sender_id": user_id},
                    )
            elif event_type in ("call_offer", "call_answer", "call_reject", "call_ice_candidate", "call_end"):
                # Relay call-signalling events to the target user.
                # The backend does not persist these — they are ephemeral signalling frames.
                target_id = data.get("target_id")
                if target_id:
                    await ws_manager.send_to_user(
                        target_id,
                        {**data, "caller_id": user_id},
                    )
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
        # Update last_seen_at in a fresh session (WS session may be closed)
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user_obj = result.scalar_one_or_none()
            if user_obj:
                user_obj.last_seen_at = datetime.now(timezone.utc)
                await session.commit()
