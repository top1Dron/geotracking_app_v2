from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.schemas.location import LocationIn
from app.services.location_processing_service import LocationProcessingService


@pytest.mark.asyncio
async def test_process_location_skips_stale_payload_without_db(monkeypatch) -> None:
    """Stale payload should be skipped before DB session is opened."""
    service = LocationProcessingService()
    monkeypatch.setattr(service, "_location_max_age_seconds", 1)

    opened_session = False

    class SessionLocalSpy:
        """Session-local spy that marks any DB access attempt."""

        async def __aenter__(self):
            nonlocal opened_session
            opened_session = True
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr(service, "_session_factory", SessionLocalSpy)
    stale_location = LocationIn(
        device_id="device-stale",
        latitude=50.45,
        longitude=30.52,
        timestamp=datetime.now(ZoneInfo("Europe/Kyiv")) - timedelta(seconds=5),
    )

    result = await service._process_location(stale_location)

    assert result.location_event is None
    assert result.alert_events == []
    assert opened_session is False
