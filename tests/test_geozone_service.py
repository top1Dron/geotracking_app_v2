from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.schemas.geozone import GeozoneCreate
from app.services.geozone_service import GeozoneService


@pytest.mark.asyncio
async def test_service_scopes_create_by_user() -> None:
    """Service should pass user id and payload to repository create."""
    repository = AsyncMock()
    service = GeozoneService(repository)
    payload = GeozoneCreate(
        name="Office",
        latitude=50.45,
        longitude=30.52,
        radius_meters=500,
    )

    await service.create("user-1", payload)

    repository.create_for_user.assert_awaited_once_with("user-1", payload)


@pytest.mark.asyncio
async def test_service_scopes_get_by_user() -> None:
    """Service should query geozones by user and id."""
    repository = AsyncMock()
    service = GeozoneService(repository)
    geozone_id = uuid4()

    await service.get("user-2", geozone_id)

    repository.get_for_user.assert_awaited_once_with("user-2", geozone_id)
