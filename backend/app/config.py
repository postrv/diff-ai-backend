# backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn


class Settings(BaseSettings):
    # Database settings
    database_url: PostgresDsn

    # Authentication settings
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AI service settings
    ai_api_key: str
    ai_model_name: str = "claude-3-5-sonnet-20241022"
    ai_max_tokens: int = 4096
    ai_enabled: bool = True

    # File storage settings
    upload_dir: str = "uploads"
    max_file_size_mb: int = 10
    allowed_extensions: list[str] = ["txt", "md", "doc", "docx", "pdf"]

    # Updated to use SettingsConfigDict instead of Config class
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()