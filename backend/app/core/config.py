"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Code Archaeologist"
    debug: bool = False
    api_prefix: str = ""

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/code_archaeologist"

    supabase_url: str = ""
    supabase_jwt_secret: str = ""
    supabase_anon_key: str = ""

    github_token: str | None = None
    groq_api_key: str | None = None

    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    temp_workspace_dir: str | None = None

    embedding_dimensions: int = 1536
    auto_create_tables: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
