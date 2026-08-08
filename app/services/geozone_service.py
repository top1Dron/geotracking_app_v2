from loguru import logger

from app.repositories.geozone import GeozoneRepository
from app.schemas.geozone import GeozoneCreate


class GeozoneService:
    """Service class for making operations with geozones."""

    def __init__(self, repository: GeozoneRepository) -> None:
        """Initialize service with a geozone repository."""
        self._repository = repository
    
    async def create_for_user(self, user_id: str, payload: GeozoneCreate):
        """Create a geozone for the given user."""
        logger.info("Creating geozone for user {}", user_id)
        return await self._repository.create_for_user(user_id, payload)