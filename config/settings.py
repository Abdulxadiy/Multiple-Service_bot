import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.fernet import Fernet

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/bot.db"
    ENCRYPTION_KEY: str = ""
    AUTO_DELETE_MINUTES: int = 20

    model_config = SettingsConfigDict(
        env_file=f"{BASE_DIR}/.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_encryption_key(self) -> bytes:
        if self.ENCRYPTION_KEY:
            return self.ENCRYPTION_KEY.encode()
        # If no encryption key is in .env, generate a default one or read fallback
        key_file = BASE_DIR / ".secret_key"
        if key_file.exists():
            return key_file.read_bytes().strip()
        new_key = Fernet.generate_key()
        key_file.write_bytes(new_key)
        return new_key

settings = Settings()
