from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy import select
from core.database.session import async_session_maker
from core.database.models import User

class UserTrackingMiddleware(BaseMiddleware):
    """Har bir murojaat qilgan foydalanuvchini bazada avtomatik ro'yxatga olish"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        event_user: TgUser | None = data.get("event_from_user")
        if event_user and not event_user.is_bot:
            async with async_session_maker() as session:
                query = select(User).where(User.telegram_id == event_user.id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()

                if not user:
                    user = User(
                        telegram_id=event_user.id,
                        username=event_user.username
                    )
                    session.add(user)
                    await session.commit()
                elif user.username != event_user.username:
                    user.username = event_user.username
                    await session.commit()

        return await handler(event, data)
