from decimal import Decimal

from pydantic import BaseModel, Field


class GeozoneCreate(BaseModel):
    """Schema for creating Geozone."""
    
    name: str = Field(min_length=1, max_length=255)
    latitude: float = Field(ge=-90, le=-90)
    longitude: float = Field(ge=-180, le=-180)
    radius_meters: Decimal = Field(
        ...,
        ge=Decimal("1.00"),
        le=Decimal("50000.00"),
        decimal_places=2,
        description="Geozone radius in meters [1 до 50000]",
    )
