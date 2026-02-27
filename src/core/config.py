from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "Sentinel API"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Postgres
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "sentinel_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    ALLOWED_ORIGINS: str = "*"

    @property
    def database_url(self) -> str:
        password = quote_plus(self.POSTGRES_PASSWORD) if self.POSTGRES_PASSWORD else ""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{password}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # backward-compatible uppercase attributes
    @property
    def DATABASE_URL(self) -> str:
        return self.database_url

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return self.database_url_sync


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
