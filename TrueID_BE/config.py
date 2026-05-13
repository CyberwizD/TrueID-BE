from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TrueID API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    environment: Literal["development", "staging", "production"] = "development"
    allowed_origins: str = "http://localhost:8081,http://localhost:19006,http://localhost:3000"
    data_backend: Literal["auto", "memory", "supabase"] = "auto"
    default_country: str = "Nigeria"
    spam_threshold: int = 55
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None

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
        return bool(self.supabase_url and self.supabase_service_role_key)

    @property
    def resolved_backend(self) -> Literal["memory", "supabase"]:
        if self.data_backend == "memory":
            return "memory"
        if self.data_backend == "supabase":
            return "supabase"
        return "supabase" if self.has_supabase_credentials else "memory"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        supabase_url=_read_passthrough_env("SUPABASE_URL"),
        supabase_service_role_key=_read_passthrough_env("SUPABASE_SERVICE_ROLE_KEY"),
    )


def _read_passthrough_env(key: str) -> str | None:
    import os

    return os.getenv(key)
