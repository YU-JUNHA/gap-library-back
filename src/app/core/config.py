from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    app_name: str = "GAP Library API"
    api_prefix: str = "/api/v1"
    debug: bool = True
    file_storage_root: str = "storage/uploads"
    file_public_prefix: str = "/uploads"
    document_storage_root: str = "storage/documents"
    draft_cleanup_enabled: bool = True
    draft_cleanup_retention_days: int = 30
    draft_cleanup_batch_size: int = 100
    draft_cleanup_interval_hours: int = 24
    draft_cleanup_run_on_startup: bool = True

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/gap_library"

    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("debug", mode="before")
    @classmethod
    def coerce_debug(cls, value):
        if isinstance(value, str) and value.lower() in {"release", "prod", "production"}:
            return False
        return value


settings = Settings()
