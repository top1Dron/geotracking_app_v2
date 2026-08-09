from datetime import datetime
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest

import app.services.location_ingest_service as ingest_module
from app.schemas.location import LocationIn
from app.services.location_ingest_service import LocationIngestService


@pytest.mark.asyncio
async def test_ingest_single_location_publishes_one_batch(monkeypatch) -> None:
    """Ingest should publish single payload as one batch message."""
    publisher = AsyncMock()
    monkeypatch.setattr(ingest_module, "stream_publisher", publisher)
    payload = LocationIn(
        device_id="device-1",
        latitude=50.45,
        longitude=30.52,
        timestamp=datetime.now(ZoneInfo("Europe/Kyiv")),
    )

    result = await LocationIngestService().ingest(payload)

    assert result == {"accepted": 1}
    publisher.publish_ingest.assert_awaited_once_with(payload)
    publisher.publish_ingest_batch.assert_not_awaited()


@pytest.mark.asyncio
async def test_ingest_batch_locations_publishes_single_batch_call(monkeypatch) -> None:
    """Ingest should publish all payloads with one batch publish call."""
    publisher = AsyncMock()
    monkeypatch.setattr(ingest_module, "stream_publisher", publisher)
    payload = [
        LocationIn(
            device_id="device-1",
            latitude=50.45,
            longitude=30.52,
            timestamp=datetime.now(ZoneInfo("Europe/Kyiv")),
        ),
        LocationIn(
            device_id="device-2",
            latitude=50.46,
            longitude=30.53,
            timestamp=datetime.now(ZoneInfo("Europe/Kyiv")),
        ),
    ]

    result = await LocationIngestService().ingest(payload)

    assert result == {"accepted": 2}
    publisher.publish_ingest_batch.assert_awaited_once_with(payload)
