from pydantic_settings import BaseSettings, SettingsConfigDict
from os import getenv


ENV_FILE = getenv("ENV_FILE",".env")

class Settings(BaseSettings):
    # App
    APP_NAME: str
    APP_VERSION: str
    ENV: str
    DEBUG: bool

    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # LLM
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str

    # Logging
    LOG_LEVEL: str

    # CORS
    ALLOWED_ORIGINS: list[str] = []

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        extra="ignore",
    )


settings = Settings()
