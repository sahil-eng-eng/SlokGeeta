from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Centralized application settings loaded from .env via Pydantic BaseSettings."""

    APP_NAME: str = "ShlokVault"
    APP_ENV: str = "development"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 2880   # 48 h = 2 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30        # 30 days

    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    SMTP_HOST: str = "smtp.resend.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_NAME: str = "ShlokVault"
    EMAILS_FROM_EMAIL: str = "noreply@shlokvault.com"

    REDIS_URL: str
    CELERY_BROKER_URL: str = ""

    FRONTEND_URL: str = "http://localhost:3003"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3003"]

    @property
    def SUPABASE_SERVICE_KEY(self) -> str:
        return self.SUPABASE_SERVICE_ROLE_KEY

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
