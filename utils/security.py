import time
import logging
from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import settings
from utils.crypto import hash_secret, is_legacy_hash
from core.database.models import User

logger = logging.getLogger("security")

class PINAttemptTracker:
    """
    PIN-kodni terishda brute-force (taxmin qilish) hujumlaridan himoyalovchi tizim.
    Ketma-ket xato urinishlar soni oshganda foydalanuvchini vaqtincha bloklaydi.
    """

    def __init__(
        self,
        max_attempts: int = settings.MAX_PIN_ATTEMPTS,
        lockout_seconds: int = settings.PIN_LOCKOUT_MINUTES * 60
    ):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        # user_id -> {"attempts": int, "locked_until": float}
        self._store: dict[int, dict] = {}

    def is_locked(self, user_id: int) -> Tuple[bool, int]:
        """
        Foydalanuvchi blok holatidami yoki yo'qligini tekshirish.
        Qaytaradi: (bloklanganmi: bool, qolgan_soniyalar: int)
        """
        data = self._store.get(user_id)
        if not data:
            return False, 0

        locked_until = data.get("locked_until", 0.0)
        now = time.time()

        if now < locked_until:
            remaining = int(locked_until - now)
            return True, remaining

        # Blok muddati tugagan bo'lsa, xatoliklar hisoblagichini tozalash
        if locked_until > 0 and now >= locked_until:
            self._store.pop(user_id, None)

        return False, 0

    def record_failure(self, user_id: int) -> Tuple[int, bool, int]:
        """
        Xato PIN kiritilishini qayd etish.
        Qaytaradi: (xatolar_soni, endi_bloklandimi, qolgan_urinishlar)
        """
        now = time.time()
        data = self._store.setdefault(user_id, {"attempts": 0, "locked_until": 0.0})

        data["attempts"] += 1
        attempts = data["attempts"]

        if attempts >= self.max_attempts:
            data["locked_until"] = now + self.lockout_seconds
            logger.warning(
                f"Foydalanuvchi {user_id} ketma-ket {attempts} marta xato PIN kiritdi va {self.lockout_seconds} soniyaga bloklandi."
            )
            return attempts, True, 0

        remaining_attempts = self.max_attempts - attempts
        return attempts, False, remaining_attempts

    def record_success(self, user_id: int) -> None:
        """To'g'ri PIN kiritilganda urinishlar tarixini tozalash"""
        self._store.pop(user_id, None)

# Global tracker instansiyasi
pin_tracker = PINAttemptTracker()

async def upgrade_pin_hash_if_needed(session: AsyncSession, user: User, plain_pin: str) -> None:
    """
    Agar foydalanuvchining PIN xeshi eski SHA-256 formatida bo'lsa,
    uni zamonaviy xavfsiz PBKDF2 formatiga avtomatik yangilash (seamless migration).
    """
    if user.pin_hash and is_legacy_hash(user.pin_hash):
        try:
            user.pin_hash = hash_secret(plain_pin)
            await session.commit()
            logger.info(f"Foydalanuvchi {user.telegram_id} ning PIN xeshi xavfsiz PBKDF2 formatiga muvaffaqiyatli yangilandi.")
        except Exception as e:
            logger.error(f"Foydalanuvchi PIN xeshini yangilashda xatolik: {e}")
