from fastapi import FastAPI

from app.api.geozones import geozone_router


app = FastAPI(
    title="Real-Time Location Service",
    version="0.2.0"
)
app.include_router(geozone_router)
app.frontend("/", directory="frontend", fallback="index.html")


@app.get("/health")
async def health_check():
    return {"status": "ok"}