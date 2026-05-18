from functools import lru_cache
from typing import Literal

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TrueID API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    environment: Literal["development", "staging", "production"] = "+"
    allowed_origins: str = "*"
    data_backend: Literal["auto", "memory", "supabase"] = "auto"
    default_country: str = "Nigeria"
    spam_threshold: int = 55
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_secret_key: str | None = None
    database_url: str | None = None
    supabase_db_url: str | None = None
    auto_migrate: bool = True

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        if value in {"development", "staging", "production"}:
            return value
        return "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TRUEID_",
        extra="ignore",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def has_supabase_credentials(self) -> bool:
        return bool(self.supabase_url and self.supabase_admin_key)

    @property
    def supabase_admin_key(self) -> str | None:
        candidate = self.supabase_secret_key or self.supabase_service_role_key
        if not candidate:
            return None
        if candidate.startswith("sb_publishable_"):
            return None
        return candidate

    @property
    def resolved_backend(self) -> Literal["memory", "supabase"]:
        if self.data_backend == "memory":
            return "memory"
        if self.data_backend == "supabase" and self.has_supabase_credentials:
            return "supabase"
        return "supabase" if self.has_supabase_credentials else "memory"

    @property
    def migration_database_url(self) -> str | None:
        return self.database_url or self.supabase_db_url


@lru_cache
def get_settings() -> Settings:
    return Settings(
        supabase_url=_read_passthrough_env("SUPABASE_URL"),
        supabase_service_role_key=_read_passthrough_env("SUPABASE_SERVICE_ROLE_KEY"),
        supabase_secret_key=_read_passthrough_env("SUPABASE_SECRET_KEY"),
        database_url=_read_passthrough_env("DATABASE_URL"),
        supabase_db_url=_read_passthrough_env("SUPABASE_DB_URL"),
    )


def _read_passthrough_env(key: str) -> str | None:
    import os

    return os.getenv(key)
