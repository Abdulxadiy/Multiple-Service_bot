from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import settings
from core.database.base import Base

# Asinxron dvijok va sessiyalar fabrikasi
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db() -> None:
    """Jadvallarni yaratish va bazani initsializatsiya qilish"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Asinxron sessiyani olish uchun kontekst menejer"""
    async with async_session_maker() as session:
        yield session
