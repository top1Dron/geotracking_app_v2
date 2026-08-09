from fastapi import FastAPI

from app.api.geozones import geozone_router
from app.api.locations import locations_router
from app.api.ws import ws_router
from app.stream import handlers  # noqa: F401
from app.stream.router import stream_router


app = FastAPI(
    title="Real-Time Location Service",
    version="0.2.0"
)
app.include_router(geozone_router)
app.include_router(locations_router)
app.include_router(stream_router)
app.include_router(ws_router)
app.frontend("/", directory="frontend", fallback="index.html")


@app.get("/health")
async def health_check():
    return {"status": "ok"}