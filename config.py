from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"{self.db_driver}://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
