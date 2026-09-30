import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import settings
from core.database.session import init_db, engine
from core.middlewares.user_middleware import UserTrackingMiddleware
from core.handlers.base import base_router
from services.password_manager.router import password_manager_router
from core.tasks.cleaner import auto_delete_worker

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

async def main():
    logger.info("Bot tizimi initsializatsiya qilinmoqda...")

    # 1. Bazani ishga tushirish (jadvallarni yaratish)
    logger.info("Ma'lumotlar bazasi jadvallari tekshirilmoqda...")
    await init_db()
    logger.info("Baza muvaffaqiyatli tayyorlandi.")

    # Bot tokeni tekshiruvi
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.warning(
            "\n" + "=" * 65 + "\n"
            "⚠️  DIQQAT! BOT_TOKEN SOZLANMAGAN!\n\n"
            "1. .env faylini oching.\n"
            "2. Telegram'da @BotFather ga o'tib botingizning tokenini oling.\n"
            "3. BOT_TOKEN=qatoriga tokenni yozing va faylni saqlang.\n"
            "4. Qaytadan 'python main.py' buyrug'ini ishga tushiring.\n"
            + "=" * 65
        )
        return

    # 2. Bot va Dispatcher obyektlari
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # 3. Middleware larni ro'yxatga olish
    dp.message.middleware(UserTrackingMiddleware())
    dp.callback_query.middleware(UserTrackingMiddleware())

    # 4. Modulli routerlarni ulash
    dp.include_router(base_router)
    dp.include_router(password_manager_router)

    # 5. 20 daqiqalik avto-o'chirish fondagi xizmatini ishga tushirish
    cleaner_task = asyncio.create_task(auto_delete_worker(bot))

    logger.info("Multiple-Service Bot tayyor va polling rejimida ishga tushmoqda...")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        cleaner_task.cancel()
        await bot.session.close()
        await engine.dispose()
        logger.info("Bot to'xtatildi.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
