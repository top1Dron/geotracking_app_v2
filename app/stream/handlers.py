from app.schemas.location import AlertEvent, LocationEvent
from app.services.location_processing_service import LocationProcessingService
from app.settings import config
from app.stream.router import stream_router
from app.websocket.connection_manager import connection_manager


location_processing_service = LocationProcessingService()


@stream_router.subscriber(config.INGEST_CHANNEL)
async def process_ingest_message(message: dict) -> None:
    """Process incoming locations and publish location and alert events."""
    await location_processing_service.process_ingest_message(message)


@stream_router.subscriber(config.LOCATIONS_CHANNEL)
async def consume_location(message: dict) -> None:
    """Consume location events from Redis to Websocket."""
    event = LocationEvent.model_validate_json(message)
    await connection_manager.broadcast_to_all(event.model_dump(mode="json"))


@stream_router.subscriber(config.ALERTS_CHANNEL)
async def consume_alert(message: dict) -> None:
    """Consume alert events from Redis to Websocket."""
    event = AlertEvent.model_validate_json(message)
    await connection_manager.broadcast_to_user(
        user_id=event.user_id,
        payload=event.model_dump(mode="json"),
    )