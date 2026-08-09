from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from app.dependencies import UserId, GeozoneServiceDependency
from app.errors import GeozoneNotFoundError
from app.schemas.geozone import GeozoneCreate, GeozoneRead, GeozoneUpdate
from app.settings import config


geozone_router = APIRouter(
    prefix=f"{config.API_VERSION}/geozones",
    tags=["geozones"],
)


@geozone_router.get(
    "",
    response_model=list[GeozoneRead],
    status_code=status.HTTP_200_OK,
)
async def get_user_geozones(
    user_id: UserId,
    geozone_service: GeozoneServiceDependency,
):
    """Get all user's geozones."""
    geozone_list = await geozone_service.get_user_geozones(user_id)
    return [GeozoneRead.model_validate(geozone) for geozone in geozone_list]

@geozone_router.get(
    "/{geozone_id}", response_model=GeozoneRead
)
async def get_user_geozone(
    geozone_id: UUID,
    user_id: UserId,
    geozone_service: GeozoneServiceDependency,
):
    """Get specified user's geozone by id."""
    try:
        geozone = await geozone_service.get_user_geozone(user_id, geozone_id)
        return GeozoneRead.model_validate(geozone)
    except GeozoneNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


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
    """Create geozone for the given user."""
    geozone = await geozone_service.create_for_user(user_id, payload)
    return GeozoneRead.model_validate(geozone)


@geozone_router.patch(
    "/{geozone_id}",
    response_model=GeozoneRead,
    status_code=status.HTTP_200_OK,
)
async def update_geozone(
    geozone_id: UUID,
    user_id: UserId,
    payload: GeozoneUpdate,
    geozone_service: GeozoneServiceDependency,
):
    """Update user's geozone using given payload."""
    try:
        geozone = await geozone_service.update_for_user(user_id, geozone_id, payload)
        return GeozoneRead.model_validate(geozone)
    except GeozoneNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@geozone_router.delete(
    "/{geozone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_geozone(
    geozone_id: UUID,
    user_id: UserId,
    geozone_service: GeozoneServiceDependency,
):
    """Drop user's geozone."""
    try:
        return await geozone_service.delete_for_user(user_id, geozone_id)
    except GeozoneNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
