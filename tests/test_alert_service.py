from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from app.repositories.spatial import GeozoneHit
from app.schemas.location import LocationIn
from app.services.alert_service import AlertService


class DummySpatialRepository:
    """Stub repository that returns predefined geozone hits."""

    def __init__(self, hits: list[GeozoneHit]) -> None:
        """Store hit list for deterministic service tests."""
        self._hits = hits

    async def find_hits_for_location(self, location: LocationIn) -> list[GeozoneHit]:
        """Return predefined hits regardless of input."""
        return self._hits


@pytest.mark.asyncio
async def test_match_location_returns_hits() -> None:
    """Service should return hits from its spatial repository."""
    location = LocationIn(
        device_id="device-1",
        latitude=50.45,
        longitude=30.52,
        timestamp=datetime.now(ZoneInfo("Europe/Kyiv")),
    )
    hit = GeozoneHit(
        user_id="user-1",
        geozone_id="zone-1",
        geozone_name="Home",
        location=location,
    )
    service = AlertService(DummySpatialRepository([hit]))

    result = await service.match_location(location)

    assert result == [hit]


def test_build_alert_maps_hit_to_payload() -> None:
    """build_alert should map spatial hits to alert event schema."""
    location = LocationIn(
        device_id="device-1",
        latitude=50.45,
        longitude=30.52,
        timestamp=datetime.now(ZoneInfo("Europe/Kyiv")),
    )
    hit = GeozoneHit(
        user_id="user-1",
        geozone_id="zone-1",
        geozone_name="Home",
        location=location,
    )

    event = AlertService.build_alert(hit)

    assert event.user_id == "user-1"
    assert event.geozone_id == "zone-1"
    assert event.device_id == "device-1"
