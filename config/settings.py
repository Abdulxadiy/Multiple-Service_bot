import os
import logging
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.fernet import Fernet

logger = logging.getLogger("config")
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/bot.db"
    ENCRYPTION_KEY: str = ""
    AUTO_DELETE_MINUTES: int = 20
    ENVIRONMENT: str = "production"

    # Database Pool sozlamalari (PostgreSQL uchun)
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 300  # AWS RDS idle uzilishlarini oldini olish uchun (soniyalarda)

    # Xavfsizlik va Anti-spam sozlamalari
    RATE_LIMIT_DELAY: float = 0.5  # Xabarlar oralig'i (soniya)
    MAX_PIN_ATTEMPTS: int = 5       # Ketma-ket xato urinishlar limiti
    PIN_LOCKOUT_MINUTES: int = 10   # Bloklanish vaqti (daqiqa)

    model_config = SettingsConfigDict(
        env_file=f"{BASE_DIR}/.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str:
        if not v:
            return f"sqlite+aiosqlite:///{BASE_DIR}/bot.db"
        # Agar postgres:// yoki postgresql:// ko'rinishida berilsa, uni asyncpg ga o'giramiz
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        if v.startswith("sqlite://") and not v.startswith("sqlite+aiosqlite://"):
            return v.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return v

    def get_encryption_key(self) -> bytes:
        if self.ENCRYPTION_KEY:
            return self.ENCRYPTION_KEY.strip().encode()

        # Agar .env da kalit bo'lmasa, .secret_key faylidan tekshiramiz
        key_file = BASE_DIR / ".secret_key"
        if key_file.exists():
            key = key_file.read_bytes().strip()
            if key:
                return key

        # Agar umuman kalit bo'lmasa, yangi yaratiladi (faqat birinchi lokal ishga tushish uchun)
        new_key = Fernet.generate_key()
        key_file.write_bytes(new_key)
        logger.warning(
            "⚠️ Yangi ENCRYPTION_KEY generatsiya qilindi va .secret_key fayliga saqlandi. "
            "Productionda ushbu kalitni .env fayliga ENCRYPTION_KEY qilib ko'chirish shart!"
        )
        return new_key

settings = Settings()

