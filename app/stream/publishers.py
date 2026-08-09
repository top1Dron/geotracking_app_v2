from app.schemas.location import AlertEvent, LocationEvent, LocationIn
from app.settings import config
from app.stream.router import stream_router


class StreamPublisher:
    """Publisher for ingest, location, and alert stream messages."""

    async def publish_ingest(self, location: LocationIn) -> None:
        """Publish a location payload to the ingest channel."""
        await stream_router.broker.publish(
            location.model_dump(mode="json"),
            channel=config.INGEST_CHANNEL,
        )

    async def publish_ingest_batch(self, locations: list[LocationIn]) -> None:
        """Publish a batch of location payloads to the ingest channel."""
        await stream_router.broker.publish(
            {"locations": [location.model_dump(mode="json") for location in locations]},
            channel=config.INGEST_CHANNEL,
        )

    async def publish_location(self, event: LocationEvent) -> None:
        """Publish a normalized location event to the fanout channel."""
        await stream_router.broker.publish(
            event.model_dump(mode="json"),
            channel=config.LOCATIONS_CHANNEL,
        )

    async def publish_alert(self, event: AlertEvent) -> None:
        """Publish a geozone alert event to the fanout channel."""
        await stream_router.broker.publish(
            event.model_dump(mode="json"),
            channel=config.ALERTS_CHANNEL,
        )


stream_publisher = StreamPublisher()
