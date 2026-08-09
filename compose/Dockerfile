FROM ghcr.io/astral-sh/uv:0.12.3-python3.14-trixie-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock* /app/
RUN uv sync --frozen --no-dev

COPY app /app/app
COPY frontend /app/frontend
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY compose/entrypoint.sh /app/compose/entrypoint.sh

RUN chmod +x /app/compose/entrypoint.sh \
    && useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["/app/compose/entrypoint.sh"]
