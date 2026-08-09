from asyncio import Semaphore
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio

from loguru import logger

from app.dataclasses import ProcessLocationResult
from app.db import SessionLocal
from app.repositories.spatial import SpatialQueryRepository
from app.schemas.location import LocationEvent, LocationIn
from app.services.alert_service import AlertService
from app.settings import config
from app.stream.publishers import stream_publisher


class LocationProcessingService:
    """Service for processing locations from ingest flow."""
    
    def __init__(self) -> None:
        """Initialize processing limits and age-threshold settings."""
        self._ingest_semaphore = Semaphore(config.INGEST_CONCURRENCY)
        self._location_max_age_seconds = config.LOCATION_MAX_AGE_SECONDS
        self._session_factory = SessionLocal
    
    # region process ingest message
    async def process_ingest_message(self, message: dict) -> None:
        """Process ingest message from the ingest flow."""
        locations = self._extract_locations(message)
        batch_results = await asyncio.gather(
            *[self._process_location(location) for location in locations]
        )
        processed = 0
        skipped_stale = 0
        published_alerts = 0
        for result in batch_results:
            if result.location_event is None:
                skipped_stale += 1
                continue
            processed += 1
            await stream_publisher.publish_location(result.location_event)
            for alert_event in result.alert_events:
                await stream_publisher.publish_alert(alert_event)
            published_alerts += len(result.alert_events)

        logger.info(
            "Processing ingest message result: processed={} skipped_stale={} alerts={}",
            processed,
            skipped_stale,
            published_alerts,
        )
    # endregion process ingest message
    
    # region helpers
    async def _process_location(self, location: LocationIn) -> ProcessLocationResult:
        """Process location."""
        now = datetime.now(ZoneInfo("Europe/Kyiv"))
        if self._is_stale(location, now):
            # if location info is too old, skip it
            return ProcessLocationResult(location_event=None, alert_events=[])
        
        async with self._ingest_semaphore:
            async with self._session_factory() as session:
                alert_service = AlertService(SpatialQueryRepository(session=session))
                hits = await alert_service.match_location(location)

        location_event = LocationEvent(**location.model_dump())
        alert_events = [AlertService.build_alert(hit) for hit in hits]
        return ProcessLocationResult(location_event=location_event, alert_events=alert_events)
    
    def _is_stale(self, location: LocationIn, now: datetime):
        """Return True when location timestamp is older than allowed max age."""
        timestamp = location.timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=ZoneInfo("Europe/Kyiv"))
        age_seconds = (now - timestamp).total_seconds()
        return age_seconds > self._location_max_age_seconds
    
    def _extract_locations(self, message: dict) -> list[LocationIn]:
        """Normalize ingest payloads into LocationIn models."""
        if "locations" in message:
            return [
                LocationIn.model_validate(location_data)
                for location_data in message["locations"]
            ]
        return [LocationIn.model_validate(message)]
    # endregion helpers