from geoalchemy2 import WKTElement
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.geozone import Geozone
from app.schemas.geozone import GeozoneCreate


class GeozoneRepository:
    """Repository for executing DB queries with Geozone model."""
    
    def __init__(self, session: AsyncSession) -> None:
        """Initializing repository with async db session."""
        self.session = session
    
    # region create geozone for user
    async def create_for_user(self, user_id: str, payload: GeozoneCreate) -> Geozone:
        """Create user's geozone in DB."""
        geozone = Geozone(
            user_id=user_id,
            name=payload.name,
            latitude=payload.latitude,
            longitude=payload.longitude,
            radius=payload.radius_meters,
            center=WKTElement(f"POINT({payload.longitude}{payload.latitude})", srid=4326)
        )
        await self.session.add(geozone)
        await self.session.commit()
        await self.session.refresh(geozone)
        return geozone
    # endregion create geozone for user
