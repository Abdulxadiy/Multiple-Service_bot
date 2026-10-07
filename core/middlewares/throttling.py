import time
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from config.settings import settings

logger = logging.getLogger("throttling")

class ThrottlingMiddleware(BaseMiddleware):
    """
    Spam va flood hujumlaridan himoyalovchi tezlik cheklovi (Rate Limiting).
    Foydalanuvchilar botga belgilangan vaqtdan tez so'rov yuborishini cheklaydi.
    """

    def __init__(self, rate_limit: float = settings.RATE_LIMIT_DELAY):
        self.rate_limit = rate_limit
        self.user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id: int | None = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id:
            now = time.monotonic()
            last_time = self.user_timestamps.get(user_id, 0.0)

            # Agar so'rovlar orasidagi vaqt cheklovdan kam bo'lsa
            if now - last_time < self.rate_limit:
                if isinstance(event, CallbackQuery):
                    try:
                        await event.answer("⚠️ Iltimos, biroz kuting!", show_alert=False)
                    except Exception:
                        pass
                return None  # Xabarni qayta ishlamaymiz (drop)

            self.user_timestamps[user_id] = now

            # Xotirani tozalab turish (har 1000 ta foydalanuvchidan keyin eski yozuvlarni tozalash)
            if len(self.user_timestamps) > 1000:
                cutoff = now - 60
                self.user_timestamps = {
                    uid: ts for uid, ts in self.user_timestamps.items() if ts > cutoff
                }

        return await handler(event, data)
