from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.deps import get_geozone_service
from app.main import app
from app.services.errors import GeozoneNotFoundError


@dataclass
class GeozoneRecord:
    """Simple geozone entity for API dependency-override tests."""

    id: UUID
    user_id: str
    name: str
    latitude: float
    longitude: float
    radius_meters: float
    created_at: datetime | None = None
    updated_at: datetime | None = None


class InMemoryGeozoneService:
    """In-memory service stub to validate API CRUD and user isolation."""

    def __init__(self) -> None:
        """Initialize user-scoped geozone storage."""
        self._data: dict[str, dict[UUID, GeozoneRecord]] = {}

    async def list(self, user_id: str) -> list[GeozoneRecord]:
        """Return all geozones for provided user id."""
        return list(self._data.get(user_id, {}).values())

    async def create(self, user_id: str, payload) -> GeozoneRecord:
        """Create and store a geozone under a user scope."""
        record = GeozoneRecord(
            id=uuid4(),
            user_id=user_id,
            name=payload.name,
            latitude=payload.latitude,
            longitude=payload.longitude,
            radius_meters=payload.radius_meters,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._data.setdefault(user_id, {})[record.id] = record
        return record

    async def get_or_raise(self, user_id: str, geozone_id: UUID) -> GeozoneRecord:
        """Return geozone or raise user-scoped not found error."""
        record = self._data.get(user_id, {}).get(geozone_id)
        if not record:
            raise GeozoneNotFoundError(f"Geozone {geozone_id} not found")
        return record

    async def update_or_raise(self, user_id: str, geozone_id: UUID, payload) -> GeozoneRecord:
        """Update geozone or raise when missing for the user."""
        record = await self.get_or_raise(user_id, geozone_id)
        if payload.name is not None:
            record.name = payload.name
        if payload.latitude is not None:
            record.latitude = payload.latitude
        if payload.longitude is not None:
            record.longitude = payload.longitude
        if payload.radius_meters is not None:
            record.radius_meters = payload.radius_meters
        record.updated_at = datetime.now(timezone.utc)
        return record

    async def delete_or_raise(self, user_id: str, geozone_id: UUID) -> None:
        """Delete geozone or raise when user has no such item."""
        await self.get_or_raise(user_id, geozone_id)
        del self._data[user_id][geozone_id]


def test_geozones_api_crud_and_user_scope(client) -> None:
    """Geozones API should support full CRUD with user isolation."""
    service = InMemoryGeozoneService()
    app.dependency_overrides[get_geozone_service] = lambda: service
    try:
        create_response = client.post(
            "/api/v1/geozones",
            headers={"X-User-Id": "user-a"},
            json={
                "name": "My Zone",
                "latitude": 46.48,
                "longitude": 30.73,
                "radius_meters": 800,
            },
        )
        assert create_response.status_code == 201
        created = create_response.json()
        geozone_id = created["id"]

        list_response = client.get("/api/v1/geozones", headers={"X-User-Id": "user-a"})
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

        get_response = client.get(
            f"/api/v1/geozones/{geozone_id}",
            headers={"X-User-Id": "user-a"},
        )
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "My Zone"

        foreign_user_response = client.get(
            f"/api/v1/geozones/{geozone_id}",
            headers={"X-User-Id": "user-b"},
        )
        assert foreign_user_response.status_code == 404

        patch_response = client.patch(
            f"/api/v1/geozones/{geozone_id}",
            headers={"X-User-Id": "user-a"},
            json={"name": "Updated Zone", "radius_meters": 1200},
        )
        assert patch_response.status_code == 200
        assert patch_response.json()["name"] == "Updated Zone"
        assert patch_response.json()["radius_meters"] == 1200

        delete_response = client.delete(
            f"/api/v1/geozones/{geozone_id}",
            headers={"X-User-Id": "user-a"},
        )
        assert delete_response.status_code == 204

        final_list_response = client.get("/api/v1/geozones", headers={"X-User-Id": "user-a"})
        assert final_list_response.status_code == 200
        assert final_list_response.json() == []
    finally:
        app.dependency_overrides.clear()


def test_geozones_api_requires_user_header(client) -> None:
    """Geozones API should return 401 when X-User-Id is missing."""
    service = InMemoryGeozoneService()
    app.dependency_overrides[get_geozone_service] = lambda: service
    try:
        response = client.get("/api/v1/geozones")
        assert response.status_code == 401
        assert response.json()["detail"] == "Missing X-User-Id header"
    finally:
        app.dependency_overrides.clear()


def test_geozones_api_returns_404_for_foreign_user_update(client) -> None:
    """Geozones API should deny updates of geozones owned by another user."""
    service = InMemoryGeozoneService()
    app.dependency_overrides[get_geozone_service] = lambda: service
    try:
        create_response = client.post(
            "/api/v1/geozones",
            headers={"X-User-Id": "owner"},
            json={
                "name": "Private Zone",
                "latitude": 46.48,
                "longitude": 30.73,
                "radius_meters": 800,
            },
        )
        assert create_response.status_code == 201
        geozone_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/geozones/{geozone_id}",
            headers={"X-User-Id": "intruder"},
            json={"name": "Hacked"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Geozone not found"
    finally:
        app.dependency_overrides.clear()


def test_geozones_api_returns_404_for_foreign_user_delete(client) -> None:
    """Geozones API should deny deleting geozones owned by another user."""
    service = InMemoryGeozoneService()
    app.dependency_overrides[get_geozone_service] = lambda: service
    try:
        create_response = client.post(
            "/api/v1/geozones",
            headers={"X-User-Id": "owner"},
            json={
                "name": "Private Zone",
                "latitude": 46.48,
                "longitude": 30.73,
                "radius_meters": 800,
            },
        )
        assert create_response.status_code == 201
        geozone_id = create_response.json()["id"]

        response = client.delete(
            f"/api/v1/geozones/{geozone_id}",
            headers={"X-User-Id": "intruder"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Geozone not found"
    finally:
        app.dependency_overrides.clear()


def test_geozones_api_validates_payload_fields(client) -> None:
    """Geozones API should reject invalid coordinates and radius values."""
    service = InMemoryGeozoneService()
    app.dependency_overrides[get_geozone_service] = lambda: service
    try:
        response = client.post(
            "/api/v1/geozones",
            headers={"X-User-Id": "user-a"},
            json={
                "name": "Bad Zone",
                "latitude": 146.48,
                "longitude": 30.73,
                "radius_meters": -5,
            },
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
