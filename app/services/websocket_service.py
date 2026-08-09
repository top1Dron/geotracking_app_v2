from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from app.websocket.connection_manager import connection_manager


class WebSocketService:
    """Service for websocket session lifecycle handling."""

    @staticmethod
    def resolve_user_id(websocket: WebSocket) -> str | None:
        """Resolve user id from query string or request headers."""
        return websocket.query_params.get("user_id") or websocket.headers.get("x-user-id")

    async def handle_connection(self, websocket: WebSocket) -> None:
        """Handle websocket connect, receive loop, and disconnect flow."""
        user_id = self.resolve_user_id(websocket)
        if not user_id:
            logger.info("websocket service rejected connection without user_id")
            await websocket.close(code=4401)
            return

        logger.info("websocket service connecting user_id={}", user_id)
        await connection_manager.connect(user_id=user_id, websocket=websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("websocket service disconnected user_id={}", user_id)
            await connection_manager.disconnect(user_id=user_id, websocket=websocket)
