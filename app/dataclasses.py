from dataclasses import dataclass
from uuid import UUID

from app.schemas.location import LocationIn


@dataclass(slots=True)
class GeozoneHit:
    """Dataclass for describing hit of intersecting device's point with user's geozone."""
    
    user_id: str
    geozone_id: UUID
    geozone_name: str
    location: LocationIn
