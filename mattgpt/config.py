from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    google_client_secret_path: Path = Path("credentials/client_secret.json")
    google_token_path: Path = Path("credentials/token.json")
    db_path: Path = Path("mattgpt.db")


settings = Settings()
