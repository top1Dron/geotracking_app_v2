# Real-Time Geo-Tracking and Alerting Service

FastAPI + FastStream + PostGIS application for real-time device location ingest, user-scoped geozone CRUD, and live location/alert delivery to browser clients over WebSocket.

## 1) Build and run the project

### Prerequisites

- Docker Desktop (or Docker Engine) with Compose
- Free local ports: `8000` (API/UI), `5433` (Postgres), `6432` (PgBouncer), `5678` (debugpy)

### Start the full stack

Important: create your local environment file before first run.

```bash
cp .env.example .env
```

```bash
docker compose up --build
```

This starts:

- `api` (FastAPI + FastStream handlers)
- `db` (PostgreSQL + PostGIS, exposed as `localhost:5433`)
- `pgbouncer` (connection pooling, exposed as `localhost:6432`)
- `redis` (stream transport)

PgBouncer auth (`userlist`) is generated at container start from `DB_USER` / `DB_PASSWORD` in `.env` (not committed to git).

The API container runs Alembic migrations automatically at startup.

### Open the app

- UI: [http://localhost:8000](http://localhost:8000)
- API base: [http://localhost:8000/api/v1](http://localhost:8000/api/v1)

### Stop services

```bash
docker compose down
```

Full cleanup (including DB volume):

```bash
docker compose down -v
```

## 2) Run the load generator

In a second terminal (while stack is running):

```bash
uv run python generator.py \
  --url http://localhost:8000/api/v1/locations \
  --devices 10000 \
  --interval 2 \
  --batch-size 500
```

Generator options:

- `--devices` number of simulated devices (default `10000`)
- `--interval` delay between ticks in seconds (default `2.0`)
- `--batch-size` HTTP batch size per POST (default `500`)
- `--one-by-one` send each device location as a separate HTTP request (ignores `--batch-size`)
- `--ticks` finite run control:
  - `0` (default) = infinite stream
  - `>0` = stop after N ticks, for example:

```bash
uv run python generator.py --url http://localhost:8000/api/v1/locations --devices 10000 --batch-size 500 --ticks 20
```

One-by-one mode (10_000 sequential API calls per tick, useful to compare vs batched ingest):

```bash
uv run python generator.py \
  --url http://localhost:8000/api/v1/locations \
  --devices 10000 \
  --one-by-one \
  --ticks 1
```

## 3) Architecture choices

### Spatial queries (PostGIS)

- Geozones are stored with geographic center coordinates and radius in meters.
- On ingest processing, zone matching is executed in the database using `ST_DWithin(...)`.
- Why this choice:
  - spatial filtering is pushed to PostGIS instead of Python loops
  - query remains compact and index-friendly for larger zone sets
  - distance checks are done with DB-native geospatial functions

### WebSocket state management

- WebSocket lifecycle is handled by `ConnectionManager` (`app/websocket/manager.py`).
- The manager stores `user_id -> set[WebSocket]`, so one user can have multiple active sessions/tabs.
- Broadcast strategy:
  - location events -> broadcast to all connected clients
  - alert events -> broadcast only to the target user sessions
- Failed sockets are cleaned up automatically to keep in-memory state healthy.

### High-throughput device data path

- `/api/v1/locations` endpoint is intentionally thin: validate payload and publish to ingest channel.
- FastStream subscribers process messages outside HTTP request lifecycle.
- Processing flow:
  1. ingest message from Redis channel
  2. run spatial match in repository
  3. publish normalized location/alert events to fanout channels
  4. deliver to active WebSocket clients
- Throughput controls:
  - Redis decouples producers from consumers
  - PgBouncer protects Postgres from connection spikes
  - async SQLAlchemy sessions + bounded pool settings are used in app config
  - ingest publishes one Redis batch message per HTTP batch
  - stale locations are dropped by `LOCATION_MAX_AGE_SECONDS` to avoid long tail drain
  - WebSocket location fanout is throttled by `WS_LOCATION_MIN_INTERVAL_MS`
  - generator sends batched requests to avoid one-request-per-device overhead

### Load-control settings

- `INGEST_CONCURRENCY`: max concurrent location workers in ingest handler
- `LOCATION_MAX_AGE_SECONDS`: drop stale points older than this age before DB/WS
- `WS_LOCATION_MIN_INTERVAL_MS`: minimum interval between location broadcasts per `device_id`

## Useful commands

Run tests:

```bash
uv run pytest
```

Run tests excluding integration-marked ones:

```bash
uv run pytest -m "not integration"
```
