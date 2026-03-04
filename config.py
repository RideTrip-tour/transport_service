from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "transport-service"
    DEBUG: bool = False

    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "mydb"
    db_user: str = "user"
    db_pass: str = "password123"
    db_driver: str = "postgresql+asyncpg"

    location_service_base_url: str = "http://location-service:8000"
    location_service_timeout_ms: int = 1000
    location_service_retries: int = 2

    schedule_provider_base_url: str = "http://schedule-provider:8000"
    schedule_provider_timeout_ms: int = 1500
    schedule_provider_retries: int = 2

    default_currency: str = "USD"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    redis_segments_ttl_seconds: int = 3600

    max_request_body_bytes: int = 262_144
    routing_max_paths_to_explore: int = 5_000
    batch_max_size: int = 500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def DATABASE_URL(self) -> str:
        """Build SQLAlchemy DSN for PostgreSQL connection."""
        return (
            f"{self.db_driver}://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def REDIS_URL(self) -> str:
        """Build Redis DSN from configured host/port/password/db."""
        auth_part = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
