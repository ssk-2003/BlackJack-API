from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "BlackJack API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+psycopg://blackjack:blackjack_secret@localhost:5432/blackjack_db"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["http://localhost:8000", "http://localhost:3000"]

    # ── Game Rules ────────────────────────────────────────────────────────────
    DEFAULT_CHIPS: int = 1000
    MIN_BET: int = 10
    MAX_BET: int = 1000
    NUM_DECKS: int = 6
    RESHUFFLE_THRESHOLD: int = 52

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" | "text"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
