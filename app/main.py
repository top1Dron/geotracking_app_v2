from fastapi import FastAPI


app = FastAPI(title="Real-Time Location Service", version="0.1.0")
app.frontend("/", directory="frontend", fallback="index.html")


@app.get("/health")
async def health_check():
    return {"status": "ok"}