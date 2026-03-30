"""WebSocket connection manager for real-time chat.

Maintains a per-user list of active WebSocket connections.
Designed to be a singleton instantiated once at import time.
"""

import json
import logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Single-server WebSocket hub.

    For multi-server deployments this would be backed by Redis pub/sub;
    the public interface (connect / disconnect / send_to_user) stays identical
    so the swap is non-breaking (Open/Closed principle).
    """

    def __init__(self) -> None:
        # user_id → list of open sockets (a user may have several browser tabs)
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, []).append(websocket)
        logger.info("WS connected: user=%s sockets=%d", user_id, len(self._connections[user_id]))

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        sockets = self._connections.get(user_id, [])
        if websocket in sockets:
            sockets.remove(websocket)
        if not sockets:
            self._connections.pop(user_id, None)

    def is_online(self, user_id: str) -> bool:
        return bool(self._connections.get(user_id))

    async def send_to_user(self, user_id: str, payload: dict[str, Any]) -> None:
        sockets = self._connections.get(user_id, [])
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)


# Application-wide singleton
ws_manager = ConnectionManager()
