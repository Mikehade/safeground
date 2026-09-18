"""Application configuration — Pydantic Settings from environment."""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    APP_NAME: str = "SafeGround"
    DEBUG: bool = True
    LOG_LEVEL: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # Postgres
    PG_USERNAME: str = Field(default="postgres", validation_alias="PG_USERNAME")
    PG_PASSWORD: str = Field(default="postgres", validation_alias="PG_PASSWORD")
    PG_HOSTNAME: str = Field(default="localhost", validation_alias="PG_HOSTNAME")
    PG_PORT: str = Field(default="5432", validation_alias="PG_PORT")
    PG_DB_NAME: str = Field(default="safeground", validation_alias="PG_DB_NAME")

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0", validation_alias="REDIS_URL"
    )

    # AWS Bedrock
    AWS_ACCESS_KEY: str = Field(default="", validation_alias="AWS_ACCESS_KEY")
    AWS_SECRET_KEY: str = Field(default="", validation_alias="AWS_SECRET_KEY")
    AWS_REGION_NAME: str = Field(
        default="us-east-1", validation_alias="AWS_REGION_NAME"
    )

    # Mapping
    ORS_API_KEY: Optional[str] = Field(
        default=None, validation_alias="ORS_API_KEY"
    )

    # Scraping / search (you wire these)
    SERP_API_KEY: Optional[str] = Field(
        default=None, validation_alias="SERP_API_KEY"
    )
    FIRECRAWL_API_KEY: Optional[str] = Field(
        default=None, validation_alias="FIRECRAWL_API_KEY"
    )

    # Agent
    SCOUT_USE_GRAPH: bool = Field(
        default=False, validation_alias="SCOUT_USE_GRAPH"
    )

    # Rate limiting
    RATE_LIMIT_PER_IP: int = Field(default=60, validation_alias="RATE_LIMIT_PER_IP")
    RATE_LIMIT_WINDOW: int = Field(default=60, validation_alias="RATE_LIMIT_WINDOW")

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            f"postgresql://{self.PG_USERNAME}:{self.PG_PASSWORD}"
            f"@{self.PG_HOSTNAME}:{self.PG_PORT}/{self.PG_DB_NAME}"
        )

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        populate_by_name=True,
        extra="allow",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
