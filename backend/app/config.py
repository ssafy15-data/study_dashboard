from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    github_token: str = ""
    github_owner: str = "ssafy15-data"
    github_repo: str = "python_codingtest"
    study_members: str = (
        "dong99u,JiseokLee0106,minjun069,hyo-4,"
        "holmane333,kjin5341-blip,us4c0d3,watermell0n"
    )
    refresh_interval_minutes: int = Field(default=15, ge=1)
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def members(self) -> list[str]:
        return [member.strip() for member in self.study_members.split(",") if member.strip()]

    @property
    def allowed_origins(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

