from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from geoalchemy2 import WKTElement

from app.db import SessionLocal
from app.models.geozone import Geozone
from app.repositories.spatial import SpatialQueryRepository
from app.schemas.location import LocationIn


@pytest.mark.asyncio
async def test_spatial_query_maps_rows_to_hits() -> None:
    """Spatial repository should map query rows into GeozoneHit objects."""
    repository = SpatialQueryRepository(session=AsyncMock())
    first_zone_id = "11111111-1111-1111-1111-111111111111"
    second_zone_id = "22222222-2222-2222-2222-222222222222"
    repository._query_repo = AsyncMock()
    repository._query_repo.get_many.return_value = [
        ("user-a", first_zone_id, "Zone A"),
        ("user-b", second_zone_id, "Zone B"),
    ]
    location = LocationIn(
        device_id="device-test",
        latitude=50.451,
        longitude=30.521,
        timestamp=datetime.now(timezone.utc),
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
    repository._query_repo.get_many.assert_awaited_once()


@pytest.mark.asyncio
async def test_spatial_query_returns_empty_when_no_hits() -> None:
    """Spatial repository should return an empty list when no rows found."""
    repository = SpatialQueryRepository(session=AsyncMock())
    repository._query_repo = AsyncMock()
    repository._query_repo.get_many.return_value = []
    location = LocationIn(
        device_id="device-empty",
        latitude=46.48,
        longitude=30.73,
        timestamp=datetime.now(timezone.utc),
    )

    hits = await repository.find_hits_for_location(location)

    assert hits == []
    repository._query_repo.get_many.assert_awaited_once()


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
            radius_meters=2000,
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
                timestamp=datetime.now(timezone.utc),
            )
        )

        assert any(hit.geozone_id == str(geozone.id) for hit in hits)
