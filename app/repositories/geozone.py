from uuid import UUID
from geoalchemy2 import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.geozone import Geozone
from app.schemas.geozone import GeozoneCreate, GeozoneUpdate


class GeozoneRepository:
    """Repository for executing DB queries with Geozone model."""
    
    def __init__(self, session: AsyncSession) -> None:
        """Initializing repository with async db session."""
        self.session = session
    
    # region get user's geozones
    async def get_user_geozones(self, user_id: str) -> list[Geozone]:
        """Get user's geozones."""
        stmt = (
            select(Geozone)
            .where(
                Geozone.user_id == user_id
            )
            .order_by(Geozone.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    # endregion get user's geozones
    
    # region get user's geozone
    async def get_user_geozone(self, user_id: str, geozone_id: UUID) -> Geozone | None:
        """Get user's geozones."""
        stmt = (
            select(Geozone)
            .where(
                Geozone.id == geozone_id,
                Geozone.user_id == user_id
            )
            .order_by(Geozone.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    # endregion get user's geozone
    
    # region create geozone for user
    async def create_for_user(self, user_id: str, payload: GeozoneCreate) -> Geozone:
        """Create user's geozone in DB."""
        geozone = Geozone(
            user_id=user_id,
            name=payload.name,
            latitude=payload.latitude,
            longitude=payload.longitude,
            radius_meters=payload.radius_meters,
            center=WKTElement(f"POINT({payload.longitude} {payload.latitude})", srid=4326)
        )
        self.session.add(geozone)
        await self.session.commit()
        await self.session.refresh(geozone)
        return geozone
    # endregion create geozone for user
    
    # region update for user
    async def update_for_user(
        self,
        user_id: str,
        geozone_id: UUID,
        payload: GeozoneUpdate
    ) -> Geozone | None:
        """Update user's geozone."""
        geozone = await self.get_user_geozone(user_id, geozone_id)
        if not geozone:
            return None
        
        # for attr in ("name", "latitude", "longitude", "radius_meters"):
        #     if (value_attr := getattr(payload, attr, None)) is not None:
        #         setattr(geozone, attr, value_attr)
        
        # get only set data
        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(geozone, field, value)
        
        if "latitude" in update_data or "longitude" in update_data:
            geozone.center = WKTElement(
                f"POINT({geozone.longitude} {geozone.latitude})",
                srid=4326,
            )
        
        await self.session.commit()
        await self.session.refresh(geozone)
        return geozone
        
    # endregion update for user
    
    # region delete for user
    async def delete_for_user(self, user_id: str, geozone_id: UUID) -> bool:
        geozone = await self.get_user_geozone(user_id, geozone_id)
        if not geozone:
            return False
        await self.session.delete(geozone)
        await self.session.commit()
        return True
    # endregion delete for user
