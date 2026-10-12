from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables (and `.env` locally)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "PantryPulse API"
    app_env: str = "local"
    git_sha: str = "dev"
    database_url: str = "postgresql+psycopg://pantry:pantry@localhost:5432/pantrypulse"
    log_level: str = "INFO"
    # Comma separated list; empty means same-origin only (the Nginx/Ingress setup).
    cors_origins: str = ""
    # /ready reports NOT READY until Alembic has stamped the schema.
    require_migrations: bool = True
    # Days ahead that count as "expiring soon" on the dashboard.
    expiry_warning_days: int = 7

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
