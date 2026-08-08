import uuid
from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geography, WKTElement
from sqlalchemy import DateTime, Float, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Geozone(Base):
    """Database model for user geozone."""
    
    __tablename__ = "geozones"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[String] = mapped_column(String(128), index=True)
    name: Mapped[String] = mapped_column(String(256))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    radius_meters: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    
    center: Mapped[WKTElement] = mapped_column(Geography(geometry_type="POINT", srid=4326, spatial_index=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )