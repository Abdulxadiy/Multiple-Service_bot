import asyncio
import logging
from datetime import datetime, timedelta, timezone
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from sqlalchemy import select, delete

from core.database.session import async_session_maker
from core.database.models import Reminder, utc_now
from services.reminder_service.keyboards import get_notification_keyboard
from services.reminder_service.utils import format_uzbek_datetime

logger = logging.getLogger("reminder_worker")

async def reminder_worker(bot: Bot, check_interval: int = 15) -> None:
    """
    Fondagi asinxron xizmat:
    1. Vaqti kelgan eslatmalarni topib, foydalanuvchiga bildirishnoma yuboradi.
    2. '✅ Bajarildi' deb belgilangan va 7 kun o'tgan eslatmalarni bazadan avtomatik o'chiradi.
    """
    logger.info("Eslatmalar xizmati (Reminder Worker) ishga tushdi.")
    
    last_cleanup_time = datetime.min.replace(tzinfo=timezone.utc)

    while True:
        try:
            now = utc_now()

            # 1. Bildirishnoma yuborilishi kerak bo'lgan faol eslatmalar
            async with async_session_maker() as session:
                query = (
                    select(Reminder)
                    .where(
                        Reminder.status == "pending",
                        Reminder.remind_at <= now
                    )
                )
                result = await session.execute(query)
                due_reminders = result.scalars().all()

                for r in due_reminders:
                    try:
                        content_text = r.text or "Siz rejalashtirgan eslatma vaqti bo'ldi!"
                        notification_msg = (
                            "🔔 <b>DIQQAT, ESLATMA!</b>\n\n"
                            f"📌 <b>Mazmuni:</b>\n{content_text}\n\n"
                            f"⏰ <b>Rejalashtirilgan vaqt:</b> {format_uzbek_datetime(r.remind_at)}"
                        )

                        kb = get_notification_keyboard(r.id)

                        if r.media_type == "voice" and r.media_file_id:
                            await bot.send_voice(
                                chat_id=r.user_id,
                                voice=r.media_file_id,
                                caption=notification_msg,
                                reply_markup=kb,
                                parse_mode="HTML"
                            )
                        elif r.media_type == "photo" and r.media_file_id:
                            await bot.send_photo(
                                chat_id=r.user_id,
                                photo=r.media_file_id,
                                caption=notification_msg,
                                reply_markup=kb,
                                parse_mode="HTML"
                            )
                        else:
                            await bot.send_message(
                                chat_id=r.user_id,
                                text=notification_msg,
                                reply_markup=kb,
                                parse_mode="HTML"
                            )

                        # Holatni yangilash
                        if r.repeat_type == "none":
                            r.status = "notified"
                            r.notified_at = now
                        elif r.repeat_type == "daily":
                            r.remind_at = r.remind_at + timedelta(days=1)
                            r.status = "pending"
                            r.notified_at = now
                        elif r.repeat_type == "weekly":
                            r.remind_at = r.remind_at + timedelta(weeks=1)
                            r.status = "pending"
                            r.notified_at = now
                        elif r.repeat_type == "monthly":
                            r.remind_at = r.remind_at + timedelta(days=30)
                            r.status = "pending"
                            r.notified_at = now

                    except TelegramForbiddenError:
                        logger.warning(f"Foydalanuvchi {r.user_id} botni bloklagan. Eslatma bajarildi deb belgilandi.")
                        r.status = "completed"
                        r.completed_at = now
                    except TelegramBadRequest as e:
                        logger.error(f"Xabar yuborishda xatolik (user: {r.user_id}): {e}")
                    except Exception as e:
                        logger.error(f"Eslatma yuborishda kutilmagan xatolik: {e}")

                await session.commit()

            # 2. 7 kun o'tgan bajarilgan eslatmalarni tozalash (har 10 daqiqada bir marta)
            if (now - last_cleanup_time).total_seconds() > 600:
                seven_days_ago = now - timedelta(days=7)
                async with async_session_maker() as session:
                    cleanup_query = (
                        delete(Reminder)
                        .where(
                            Reminder.status == "completed",
                            Reminder.completed_at <= seven_days_ago
                        )
                    )
                    clean_res = await session.execute(cleanup_query)
                    await session.commit()
                    if clean_res.rowcount > 0:
                        logger.info(f"7 kundan oshgan {clean_res.rowcount} ta bajarilgan eslatma tozalandi.")
                last_cleanup_time = now

        except asyncio.CancelledError:
            logger.info("Reminder Worker to'xtatildi.")
            break
        except Exception as e:
            logger.error(f"Reminder Worker xatoligi: {e}")

        await asyncio.sleep(check_interval)
