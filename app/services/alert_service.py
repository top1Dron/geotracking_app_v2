from app.dataclasses import GeozoneHit
from app.repositories.spatial import SpatialQueryRepository
from app.schemas.location import AlertEvent, LocationIn


class AlertService:
    """Service for alerting users about matching locations."""
    
    def __init__(self, spatial_repository: SpatialQueryRepository) -> None:
        self._spatial_repository = spatial_repository
    
    async def match_location(self, location: LocationIn) -> list[GeozoneHit]:
        """Find geozones that contain the provided location."""
        return await self._spatial_repository.find_hits_for_location(location)
    
    @staticmethod
    def build_alert(hit: GeozoneHit) -> AlertEvent:
        """Build an alert event payload from a spatial hit."""
        return AlertEvent(
            user_id=hit.user_id,
            device_id=hit.location.device_id,
            geozone_id=str(hit.geozone_id),
            geozone_name=hit.geozone_name,
            latitude=hit.location.latitude,
            longitude=hit.location.longitude,
            timestamp=hit.location.timestamp,
        )
