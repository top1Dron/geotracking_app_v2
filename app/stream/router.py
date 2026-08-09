from faststream.redis.fastapi import RedisRouter

from app.settings import config

stream_router = RedisRouter(url=config.REDIS_URL)