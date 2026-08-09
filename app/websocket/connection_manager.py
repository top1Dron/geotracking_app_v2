import asyncio
import time
from collections import defaultdict
from collections.abc import Iterable

from fastapi import WebSocket

from app.settings import config


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts."""

    def __init__(self) -> None:
        """Initialize connection storage and synchronization lock."""
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._last_location_sent_at: dict[str, float] = {}
        self._location_min_interval_ms = max(0, config.WS_LOCATION_MIN_INTERVAL_MS)
        self._lock = asyncio.Lock()

    # region connect - disconnect
    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """Accept and register a websocket connection for a user."""
        await websocket.accept()
        async with self._lock:
            self._connections[user_id].add(websocket)

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """Remove a websocket from the user's active connection set."""
        async with self._lock:
            sockets = self._connections.get(user_id)
            if not sockets:
                return
            sockets.discard(websocket)
            if not sockets:
                self._connections.pop(user_id, None)
    # endregion connect - disconnect

    # region broadcast to all
    async def broadcast_to_all(self, payload: dict) -> None:
        """Broadcast a JSON payload to all connected users."""
        if self._should_throttle_location(payload):
            return
        sockets = await self._all_sockets()
        await self._broadcast(sockets, payload)
    # endregion broadcast to all

    # region broadcast to user
    async def broadcast_to_user(self, user_id: str, payload: dict) -> None:
        """Broadcast a JSON payload to all sessions of one user."""
        async with self._lock:
            sockets = tuple(self._connections.get(user_id, set()))
        await self._broadcast(sockets, payload)
    # endregion broadcast to user

    # region helper methods
    async def _all_sockets(self) -> tuple[WebSocket, ...]:
        """Return a snapshot of all active websocket connections."""
        async with self._lock:
            return tuple(socket for sockets in self._connections.values() for socket in sockets)

    async def _broadcast(self, sockets: Iterable[WebSocket], payload: dict) -> None:
        """Send payload to provided sockets and cleanup failed connections."""
        tasks = [socket.send_json(payload) for socket in sockets]
        if not tasks:
            return
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for socket, result in zip(sockets, results):
            if isinstance(result, Exception):
                await self._cleanup_socket(socket)

    async def _cleanup_socket(self, websocket: WebSocket) -> None:
        """Remove a broken websocket from all user connection sets."""
        async with self._lock:
            for user_id, sockets in tuple(self._connections.items()):
                if websocket in sockets:
                    sockets.discard(websocket)
                    if not sockets:
                        self._connections.pop(user_id, None)

    def _should_throttle_location(self, payload: dict) -> bool:
        """Return True when location message is sent too frequently per device."""
        if payload.get("type") != "location":
            return False
        device_id = payload.get("device_id")
        if not isinstance(device_id, str) or self._location_min_interval_ms == 0:
            return False

        now_ms = time.monotonic() * 1000
        last_sent_ms = self._last_location_sent_at.get(device_id)
        if last_sent_ms is not None and now_ms - last_sent_ms < self._location_min_interval_ms:
            return True
        self._last_location_sent_at[device_id] = now_ms
        return False
    # endregion helper methods


connection_manager = ConnectionManager()
