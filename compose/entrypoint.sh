#!/usr/bin/env bash
set -euo pipefail

wait_for_port() {
  local host="$1"
  local port="$2"
  local name="$3"
  python - <<PY
import socket
import time

host = "${host}"
port = int("${port}")
name = "${name}"
deadline = time.time() + 90
while time.time() < deadline:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        try:
            sock.connect((host, port))
            print(f"{name} is reachable at {host}:{port}")
            raise SystemExit(0)
        except OSError:
            time.sleep(1)
print(f"Timed out waiting for {name} at {host}:{port}")
raise SystemExit(1)
PY
}

wait_for_port "pgbouncer" "5432" "PgBouncer"
wait_for_port "redis" "6379" "Redis"

uv run alembic upgrade head

if [[ "${DEBUGPY_ENABLED:-false}" == "true" ]]; then
  exec uv run python -m debugpy \
    --listen "0.0.0.0:${DEBUGPY_PORT:-5678}" \
    -m uvicorn app.main:app \
    --host "${APP_HOST:-0.0.0.0}" \
    --port "${APP_PORT:-8000}" \
    --log-level "${LOG_LEVEL:-info}"
fi

exec uv run uvicorn app.main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8000}" --log-level "${LOG_LEVEL:-info}"
