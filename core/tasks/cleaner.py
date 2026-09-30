import asyncio
import logging
from datetime import datetime, timedelta, timezone
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, delete
from core.database.session import async_session_maker
from core.database.models import PendingDeletion

logger = logging.getLogger(__name__)

async def register_auto_delete_message(chat_id: int, message_id: int, minutes: int = 20) -> None:
    """Xabarni 20 daqiqadan so'ng avtomatik o'chirilishi uchun navbatga qo'yish"""
    delete_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    async with async_session_maker() as session:
        pending = PendingDeletion(
            chat_id=chat_id,
            message_id=message_id,
            delete_at=delete_at
        )
        session.add(pending)
        await session.commit()

async def auto_delete_worker(bot: Bot, check_interval: int = 15) -> None:
    """Fondagi asinxron vazifa: Muddati o'tgan maxfiy xabarlarni o'chirib boradi"""
    logger.info("Avto-o'chirish xizmati (Auto-Delete Cleaner) ishga tushdi.")
    while True:
        try:
            now = datetime.now(timezone.utc)
            async with async_session_maker() as session:
                query = select(PendingDeletion).where(PendingDeletion.delete_at <= now)
                result = await session.execute(query)
                expired_records = result.scalars().all()

                if expired_records:
                    for record in expired_records:
                        try:
                            await bot.delete_message(chat_id=record.chat_id, message_id=record.message_id)
                        except TelegramBadRequest as e:
                            # Agar foydalanuvchi xabarni o'zi o'chirib yuborgan bo'lsa
                            logger.debug(f"Xabar allaqachon o'chirilgan yoki topilmadi: {e}")
                        except Exception as e:
                            logger.error(f"Xabarni o'chirishda xatolik yuz berdi: {e}")

                        # Bazadan o'chirish
                        await session.delete(record)
                    await session.commit()
        except asyncio.CancelledError:
            logger.info("Avto-o'chirish xizmati to'xtatildi.")
            break
        except Exception as e:
            logger.error(f"Avto-o'chirish fondagi vazifasida xatolik: {e}")

        await asyncio.sleep(check_interval)
