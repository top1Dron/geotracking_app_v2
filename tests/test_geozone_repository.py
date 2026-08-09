from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.repositories.geozone import GeozoneRepository
from app.schemas.geozone import GeozoneCreate, GeozoneUpdate


class FakeSession:
    """Minimal async-session stub for repository behavior tests."""

    def __init__(self) -> None:
        """Initialize fake session call tracking fields."""
        self.added = []
        self.deleted = []
        self.commits = 0
        self.refreshed = []

    def add(self, value) -> None:
        """Track synchronously added entities."""
        self.added.append(value)

    async def commit(self) -> None:
        """Track commit calls."""
        self.commits += 1

    async def refresh(self, value) -> None:
        """Track refresh calls."""
        self.refreshed.append(value)

    async def delete(self, value) -> None:
        """Track delete calls."""
        self.deleted.append(value)


@pytest.mark.asyncio
async def test_create_for_user_uses_sync_add_and_commits() -> None:
    """Repository create should use session.add and commit once."""
    session = FakeSession()
    repository = GeozoneRepository(session=session)  # type: ignore[arg-type]
    payload = GeozoneCreate(
        name="Zone A",
        latitude=50.45,
        longitude=30.52,
        radius_meters=1000,
    )

    created = await repository.create_for_user("user-1", payload)

    assert created.user_id == "user-1"
    assert len(session.added) == 1
    assert session.commits == 1
    assert session.refreshed == [created]


@pytest.mark.asyncio
async def test_update_for_user_changes_fields_and_commits(monkeypatch) -> None:
    """Repository update should mutate entity and commit changes."""
    session = FakeSession()
    repository = GeozoneRepository(session=session)  # type: ignore[arg-type]
    geozone = SimpleNamespace(
        id=uuid4(),
        user_id="user-1",
        name="Old",
        latitude=50.45,
        longitude=30.52,
        radius_meters=500,
        center=None,
        created_at=datetime.now(timezone.utc),
    )

    async def fake_get_for_user(user_id: str, geozone_id):
        return geozone

    monkeypatch.setattr(repository, "get_for_user", fake_get_for_user)
    payload = GeozoneUpdate(name="New", latitude=50.5, longitude=30.6, radius_meters=900)

    updated = await repository.update_for_user("user-1", geozone.id, payload)

    assert updated is geozone
    assert geozone.name == "New"
    assert geozone.latitude == 50.5
    assert geozone.longitude == 30.6
    assert geozone.radius_meters == 900
    assert geozone.center is not None
    assert session.commits == 1
    assert session.refreshed == [geozone]


@pytest.mark.asyncio
async def test_delete_for_user_returns_false_when_missing(monkeypatch) -> None:
    """Repository delete should return False for unknown geozone."""
    session = FakeSession()
    repository = GeozoneRepository(session=session)  # type: ignore[arg-type]

    async def fake_get_for_user(user_id: str, geozone_id):
        return None

    monkeypatch.setattr(repository, "get_for_user", fake_get_for_user)

    deleted = await repository.delete_for_user("user-1", uuid4())

    assert deleted is False
    assert session.deleted == []
    assert session.commits == 0


@pytest.mark.asyncio
async def test_delete_for_user_deletes_and_commits(monkeypatch) -> None:
    """Repository delete should remove entity and commit transaction."""
    session = FakeSession()
    repository = GeozoneRepository(session=session)  # type: ignore[arg-type]
    geozone = SimpleNamespace(id=uuid4(), user_id="user-1")

    async def fake_get_for_user(user_id: str, geozone_id):
        return geozone

    monkeypatch.setattr(repository, "get_for_user", fake_get_for_user)

    deleted = await repository.delete_for_user("user-1", geozone.id)

    assert deleted is True
    assert session.deleted == [geozone]
    assert session.commits == 1
