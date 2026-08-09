from uuid import UUID
from loguru import logger

from app.errors import GeozoneNotFoundError
from app.repositories.geozone import GeozoneRepository
from app.schemas.geozone import GeozoneCreate, GeozoneUpdate


class GeozoneService:
    """Service class for making operations with geozones."""

    def __init__(self, repository: GeozoneRepository) -> None:
        """Initialize service with a geozone repository."""
        self._repository = repository
    
    async def get_user_geozones(self, user_id: str):
        """Get user's geozones."""
        logger.info("Getting geozones for user with id {}", user_id)
        return await self._repository.get_user_geozones(user_id)
    
    async def get_user_geozone(self, user_id: str, geozone_id: UUID):
        """Get user's geozone or raise GeozoneNotFoundError."""
        logger.info("Getting specific user's geozone user_id={} geozone_id={}",
                    user_id, geozone_id)
        geozone = await self._repository.get_user_geozone(user_id, geozone_id)
        if geozone is None:
            logger.warning("Geozone with id {} for user {} not found", geozone_id, user_id)
            raise GeozoneNotFoundError(f"Geozone {geozone_id} not found")
        return geozone
    
    async def create_for_user(self, user_id: str, payload: GeozoneCreate):
        """Create a geozone for the given user."""
        logger.info("Creating geozone for user {}", user_id)
        return await self._repository.create_for_user(user_id, payload)
    
    async def update_for_user(self, user_id: str, geozone_id: UUID, payload: GeozoneUpdate):
        """Update the user's geozone."""
        logger.info("Updating geozone {} for user {}", geozone_id, user_id)
        geozone = await self._repository.update_for_user(user_id, geozone_id, payload)
        if geozone is None:
            logger.warning("Geozone with id {} for user {} not found", geozone_id, user_id)
            raise GeozoneNotFoundError(f"Geozone {geozone_id} not found")
        return geozone
    
    async def delete_for_user(self, user_id: str, geozone_id: UUID,):
        """Drop the user's geozone."""
        logger.info("Drop geozone {} for user {}", geozone_id, user_id)
        is_deleted = await self._repository.delete_for_user(user_id, geozone_id)
        if not is_deleted:
            logger.warning("Geozone with id {} for user {} not found", geozone_id, user_id)
            raise GeozoneNotFoundError(f"Geozone {geozone_id} not found")
