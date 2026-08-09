import pytest

from app.websocket.manager import ConnectionManager


class FakeWebSocket:
    """Simple websocket stub for connection manager tests."""

    def __init__(self) -> None:
        """Initialize message store and accepted-state flag."""
        self.accepted = False
        self.messages: list[dict] = []

    async def accept(self) -> None:
        """Mark websocket as accepted."""
        self.accepted = True

    async def send_json(self, payload: dict) -> None:
        """Capture outbound payloads."""
        self.messages.append(payload)


@pytest.mark.asyncio
async def test_broadcast_to_all_sessions_for_same_user() -> None:
    """Broadcast should reach every active websocket session."""
    manager = ConnectionManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    await manager.connect("user-1", ws1)
    await manager.connect("user-1", ws2)
    await manager.broadcast_to_user("user-1", {"type": "alert"})

    assert ws1.messages == [{"type": "alert"}]
    assert ws2.messages == [{"type": "alert"}]


@pytest.mark.asyncio
async def test_disconnect_removes_socket() -> None:
    """Disconnect should remove socket from active user set."""
    manager = ConnectionManager()
    ws1 = FakeWebSocket()

    await manager.connect("user-1", ws1)
    await manager.disconnect("user-1", ws1)
    await manager.broadcast_to_user("user-1", {"type": "alert"})

    assert ws1.messages == []


@pytest.mark.asyncio
async def test_location_broadcast_throttles_per_device(monkeypatch) -> None:
    """Location fanout should skip overly frequent updates per device."""
    monkeypatch.setattr("app.websocket.manager.config.WS_LOCATION_MIN_INTERVAL_MS", 200)
    monotonic_values = iter([1.0, 1.1, 1.4])

    def fake_monotonic() -> float:
        """Return deterministic monotonic values for throttle checks."""
        return next(monotonic_values, 1.4)

    monkeypatch.setattr("app.websocket.manager.time.monotonic", fake_monotonic)

    manager = ConnectionManager()
    ws = FakeWebSocket()
    payload = {
        "type": "location",
        "device_id": "device-1",
        "latitude": 50.45,
        "longitude": 30.52,
    }

    await manager.connect("user-1", ws)
    await manager.broadcast_to_all(payload)
    await manager.broadcast_to_all(payload)
    await manager.broadcast_to_all(payload)

    assert ws.messages == [payload, payload]
