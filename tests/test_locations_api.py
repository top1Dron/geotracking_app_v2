from datetime import datetime, timezone
from typing import Any

from app.deps import get_location_ingest_service
from app.main import app


class DummyLocationIngestService:
    """Stub ingest service that tracks accepted payload count."""

    def __init__(self) -> None:
        """Initialize captured payload storage."""
        self.received: list[Any] = []

    async def ingest(self, payload) -> dict[str, int]:
        """Capture payload and return accepted count response."""
        locations = payload if isinstance(payload, list) else [payload]
        self.received.extend(locations)
        return {"accepted": len(locations)}


def test_ingest_single_location_publishes_once(client) -> None:
    """Single location payload should trigger one publish call."""
    service = DummyLocationIngestService()
    app.dependency_overrides[get_location_ingest_service] = lambda: service

    response = client.post(
        "/api/v1/locations",
        json={
            "device_id": "device-1",
            "latitude": 50.45,
            "longitude": 30.52,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    assert response.status_code == 202
    assert response.json() == {"accepted": 1}
    assert len(service.received) == 1
    app.dependency_overrides.clear()


def test_ingest_batch_locations_publishes_for_each(client) -> None:
    """Batch payload should publish each location event separately."""
    service = DummyLocationIngestService()
    app.dependency_overrides[get_location_ingest_service] = lambda: service

    response = client.post(
        "/api/v1/locations",
        json=[
            {
                "device_id": "device-1",
                "latitude": 50.45,
                "longitude": 30.52,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "device_id": "device-2",
                "latitude": 50.46,
                "longitude": 30.53,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ],
    )

    assert response.status_code == 202
    assert response.json() == {"accepted": 2}
    assert len(service.received) == 2
    app.dependency_overrides.clear()
