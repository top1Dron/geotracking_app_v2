from fastapi import APIRouter, status

from app.dependencies import UserId, GeozoneServiceDependency
from app.schemas.geozone import GeozoneCreate, GeozoneRead
from app.settings import config


geozone_router = APIRouter(
    prefix=f"{config.API_VERSION}/geozones",
    tags=["geozones"],
)


@geozone_router.get(
    "",
    status_code=status.HTTP_200_OK,
)
async def get_users_geozones(
    user_id: UserId,
    geozone_service: GeozoneServiceDependency,
):
    return []


@geozone_router.post(
    "",
    response_model=GeozoneRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_geozone(
    payload: GeozoneCreate,
    user_id: UserId,
    geozone_service: GeozoneServiceDependency,
):
    geozone = await geozone_service.create_for_user(user_id, payload)
    return GeozoneRead.model_validate(geozone)
    
    