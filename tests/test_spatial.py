from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from geoalchemy2 import WKTElement

from app.db import SessionLocal
from app.models.geozone import Geozone
from app.repositories.spatial import SpatialQueryRepository
from app.schemas.location import LocationIn


@pytest.mark.asyncio
async def test_spatial_query_maps_rows_to_hits() -> None:
    """Spatial repository should map query rows into GeozoneHit objects."""
    first_zone_id = UUID("11111111-1111-1111-1111-111111111111")
    second_zone_id = UUID("22222222-2222-2222-2222-222222222222")
    session = AsyncMock()
    result = MagicMock()
    result.tuples.return_value.all.return_value = [
        (first_zone_id, "user-a", "Zone A"),
        (second_zone_id, "user-b", "Zone B"),
    ]
    session.execute.return_value = result
    repository = SpatialQueryRepository(session=session)
    location = LocationIn(
        device_id="device-test",
        latitude=50.451,
        longitude=30.521,
        timestamp=datetime.now(ZoneInfo("Europe/Kyiv")),
    )

    hits = await repository.find_hits_for_location(location)

    assert len(hits) == 2
    assert hits[0].user_id == "user-a"
    assert hits[0].geozone_id == first_zone_id
    assert hits[0].geozone_name == "Zone A"
    assert hits[0].location == location
    assert hits[1].user_id == "user-b"
    assert hits[1].geozone_id == second_zone_id
    assert hits[1].geozone_name == "Zone B"
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_spatial_query_returns_empty_when_no_hits() -> None:
    """Spatial repository should return an empty list when no rows found."""
    session = AsyncMock()
    result = MagicMock()
    result.tuples.return_value.all.return_value = []
    session.execute.return_value = result
    repository = SpatialQueryRepository(session=session)
    location = LocationIn(
        device_id="device-empty",
        latitude=46.48,
        longitude=30.73,
        timestamp=datetime.now(ZoneInfo("Europe/Kyiv")),
    )

    hits = await repository.find_hits_for_location(location)

    assert hits == []
    session.execute.assert_awaited_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_spatial_query_finds_inside_radius() -> None:
    """Spatial repository should detect a point located inside geozone radius."""
    async with SessionLocal() as session:
        geozone = Geozone(
            user_id="integration-user",
            name="Integration Zone",
            latitude=50.45,
            longitude=30.52,
            radius_meters=Decimal(2000),
            center=WKTElement("POINT(30.52 50.45)", srid=4326),
        )
        try:
            session.add(geozone)
            await session.commit()
        except Exception as exc:  # pragma: no cover - environment dependent
            await session.rollback()
            pytest.skip(f"Integration DB is not available: {exc}")

        repository = SpatialQueryRepository(session=session)
        hits = await repository.find_hits_for_location(
            LocationIn(
                device_id="device-test",
                latitude=50.451,
                longitude=30.521,
                timestamp=datetime.now(ZoneInfo("Europe/Kyiv")),
            )
        )

        assert any(hit.geozone_id == geozone.id for hit in hits)
