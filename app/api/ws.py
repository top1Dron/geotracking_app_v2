from fastapi import APIRouter, WebSocket

from app.dependencies import WebSocketServiceDependency


ws_router = APIRouter(tags=["websocket"])


@ws_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    websocket_service: WebSocketServiceDependency,
) -> None:
    """Accept websocket sessions and register by user id."""
    await websocket_service.handle_connection(websocket)
