from app.schemas.location import LocationIn
from app.stream.publishers import stream_publisher


class LocationIngestService:
    """Service for ingest endpoint publishing flow."""

    async def ingest(self, payload: LocationIn | list[LocationIn]) -> dict[str, int]:
        """Publish one or many location payloads to the ingest channel."""
        if isinstance(payload, LocationIn):
            method = stream_publisher.publish_ingest
            locations_len = 1
        else:
            method = stream_publisher.publish_ingest_batch
            locations_len = (len(payload))
        await method(payload)
        return {"accepted": locations_len}
