from fastapi import APIRouter, status

from app.dependencies import LocationIngestServiceDependency
from app.schemas.location import LocationIn
from app.settings import config


locations_router = APIRouter(
    prefix=f"{config.API_VERSION}/locations",
    tags=["locations"],
)


@locations_router.post("", status_code=status.HTTP_202_ACCEPTED)
async def ingest_locations(
    payload: LocationIn | list[LocationIn],
    location_ingest_service: LocationIngestServiceDependency,
):
    """Publish location payloads to the ingest redis flow."""
    return await location_ingest_service.ingest(payload)
