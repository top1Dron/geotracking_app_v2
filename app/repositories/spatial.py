from collections.abc import Sequence
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dataclasses import GeozoneHit
from app.models.geozone import Geozone
from app.schemas.location import LocationIn


class SpatialQueryRepository:
    """Repository for spatial query repositories."""
    
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    async def find_hits_for_location(self, location: LocationIn) -> list[GeozoneHit]:
        """Find hits of given location with users' geozones in DB."""
        # cast location to geography point
        point = cast(
            func.ST_SetSRID(
                func.ST_MakePoint(location.longitude, location.latitude),
                4326
            ),
            Geography
        )
        
        # get hits with geozones in DB
        stmt = (
            select(
                Geozone.id, Geozone.user_id, Geozone.name
            )
            .where(
                func.ST_DWithin(
                    Geozone.center,
                    point,
                    Geozone.radius_meters
                )
            )
        )
        result = await self.session.execute(stmt)
        rows: Sequence[tuple[UUID, str, str]] = result.tuples().all()
        return [
            GeozoneHit(
                user_id=user_id,
                geozone_id=geozone_id,
                geozone_name=geozone_name,
                location=location
            )
            for geozone_id, user_id, geozone_name
            in rows
        ]
        