from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra="ignore",
    )
    
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    DATABASE_URL: str
    DATABASE_URL_DIRECT: str
    REDIS_URL: str
    
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 15
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_PRE_PING: bool = True
    DB_STATEMENT_CACHE_SIZE: int = 0
    
    INGEST_CHANNEL: str = "locations.ingest"
    LOCATIONS_CHANNEL: str = "locations"
    ALERTS_CHANNEL: str = "alerts"
    INGEST_CONCURRENCY: int = 100
    LOCATION_MAX_AGE_SECONDS: int = 10
    WS_LOCATION_MIN_INTERVAL_MS: int = 200
    
    API_VERSION: str = "/api/v1"


config = Config()
