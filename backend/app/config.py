from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

# WebAuthn user handle
WEBAUTHN_USER_HANDLE_BYTES = 64


class Settings(BaseSettings):
    # --- Environment ---
    ENV: Literal["dev", "prod", "test"] = "dev"

    # --- App ---
    APP_NAME: str = "FastAPI App"
    APP_DESCRIPTION: str = "API"
    APP_VERSION: str = "0.1.0"

    DEBUG: bool = False
    PORT: int = 8000

    # --- Security ---
    SECRET_KEY: str

    # --- Database (structured) ---
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    RP_ID: str = "localhost"
    RP_NAME: str = "Encrypted P2P Chat"
    RP_ORIGIN: str = "http://localhost:8000"

    WEBAUTHN_CHALLENGE_TTL_SECONDS: int = 600
    WEBAUTHN_CHALLENGE_BYTES: int = 32
    WEBAUTHN_USER_HANDLE_BYTES: int = 64

    USERNAME_MIN_LENGTH: int
    USERNAME_MAX_LENGTH: int
    DEVICE_NAME_MAX_LENGTH: int

    SESSION_TTL_SECONDS: int
    SESSION_COOKIE_NAME: str
    SESSION_TOKEN_BYTES: int

    REDIS_URL: str = "redis://localhost:6379"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
    )

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:"
            f"{self.DB_PASSWORD}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()