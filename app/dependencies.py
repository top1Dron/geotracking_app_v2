from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.repositories.geozone import GeozoneRepository
from app.services.geozone_service import GeozoneService


async def get_user_id(x_user_id: Annotated[str | None, Header()] = None) -> str:
    """Extract user id from request header x-user-id."""
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authenticated"
        )
    return x_user_id


DbSession = Annotated[AsyncSession, Depends(get_db_session)]
UserId = Annotated[str, Depends(get_user_id)]


def get_geozone_service(session: DbSession) -> GeozoneService:
    """Build geozone service dependency from current DB session."""
    return GeozoneService(GeozoneRepository(session=session))


GeozoneServiceDependency = Annotated[GeozoneService, Depends(get_geozone_service)]
