"""
Centralised app configuration, loaded from environment variables / .env.
"""

from urllib.parse import quote_plus
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore[reportMissingImports]
except ImportError:
    from pydantic import BaseSettings

    SettingsConfigDict = dict


class Settings(BaseSettings):

    if hasattr(BaseSettings, "model_config"):
        model_config = SettingsConfigDict(
            env_file=".env",
            extra="ignore"
        )
    else:
        class Config:
            env_file = ".env"
            extra = "ignore"

    # --- MySQL ---
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # --- Storage ---
    UPLOAD_DIR: str = "app/static/uploads"
    BLURRED_DIR: str = "app/static/blurred"

    # --- ML / detection defaults ---
    DEFAULT_HATE_THRESHOLD: float = 0.5
    DEFAULT_OCR_LANGS: str = "en"
    BLIP_MODEL_NAME: str = "Salesforce/blip-image-captioning-base"
    CLASSIFIER_MODEL_NAME: str = "facebook/roberta-hate-speech-dynabench-r4-target"

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:4200"
    
    # --- Authentication / JWT ---
    JWT_SECRET: str

    @property
    def database_url(self) -> str:
        password = quote_plus(self.DB_PASSWORD)

        return (
            f"mysql+pymysql://{self.DB_USER}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            o.strip()
            for o in self.CORS_ORIGINS.split(",")
            if o.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()