from datetime import datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field


class LocationIn(BaseModel):
    """Model for input current location from a device."""
    
    device_id: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("Europe/Kyiv"))
    )


class AlertEvent(BaseModel):
    """Schema for broadcasting geozone alert events."""

    type: Literal["alert"] = "alert"
    user_id: str
    device_id: str
    geozone_id: UUID
    geozone_name: str
    latitude: float
    longitude: float
    timestamp: datetime
