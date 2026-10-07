import hashlib
import hmac
import secrets
import string
from cryptography.fernet import Fernet
from config.settings import settings

# Eski xeshlarni tekshirish uchun legacy tuz (orqaga moslik)
LEGACY_SALT = "MultipleServiceBot_SecureSalt_2026"
PBKDF2_ITERATIONS = 100_000

def hash_secret(plain_text: str) -> str:
    """
    Xavfsiz PBKDF2-HMAC-SHA256 xesh yaratish.
    Har bir xesh uchun 16 baytli tasodifiy individual tuz (salt) va 100 000 iteratsiya ishlatiladi.
    Format: pbkdf2:sha256:100000$<salt>$<hash>
    """
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        plain_text.strip().encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS
    )
    return f"pbkdf2:sha256:{PBKDF2_ITERATIONS}${salt}${key.hex()}"

def is_legacy_hash(hashed_value: str) -> bool:
    """Xesh eski oddiy SHA-256 formatidami yoki yo'qligini aniqlash"""
    return not hashed_value.startswith("pbkdf2:")

def verify_secret(plain_text: str, hashed_value: str) -> bool:
    """
    Kiritilgan matn xeshga mos kelishini tekshirish (Timing Attack himoyasi bilan).
    Ham yangi PBKDF2, ham eski legacy SHA-256 formatlarini qo'llab-quvvatlaydi.
    """
    if not hashed_value or not plain_text:
        return False

    # 1. Yangi PBKDF2 formati
    if hashed_value.startswith("pbkdf2:sha256:"):
        try:
            parts = hashed_value.split("$")
            if len(parts) != 3:
                return False
            meta, salt, expected_hash = parts
            _, _, iterations_str = meta.split(":")
            iterations = int(iterations_str)

            actual_key = hashlib.pbkdf2_hmac(
                "sha256",
                plain_text.strip().encode("utf-8"),
                salt.encode("utf-8"),
                iterations
            )
            # Doimiy vaqtli xavfsiz solishtirish
            return hmac.compare_digest(actual_key.hex(), expected_hash)
        except Exception:
            return False

    # 2. Orqaga moslik: Eski oddiy SHA-256 xeshi
    salted = f"{plain_text.strip()}:{LEGACY_SALT}".encode("utf-8")
    legacy_hash = hashlib.sha256(salted).hexdigest()
    return hmac.compare_digest(legacy_hash, hashed_value)


def generate_recovery_code() -> str:
    """8-10 xonali bir martalik tiklash kodi generatsiyasi"""
    chars = string.ascii_uppercase + string.digits
    part1 = "".join(secrets.choice(chars) for _ in range(4))
    part2 = "".join(secrets.choice(chars) for _ in range(4))
    return f"{part1}-{part2}"

def generate_strong_password(length: int = 16) -> str:
    """Murakkab va xavfsiz tasodifiy parol yaratish"""
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*"
    all_chars = lowercase + uppercase + digits + special

    # Har bir toifadan kamida bittadan belgi bo'lishini kafolatlaymiz
    pwd = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]
    pwd += [secrets.choice(all_chars) for _ in range(length - len(pwd))]
    secrets.SystemRandom().shuffle(pwd)
    return "".join(pwd)

def get_fernet_cipher() -> Fernet:
    """Fernet (AES-256) shifrlash vositasini olish"""
    key = settings.get_encryption_key()
    return Fernet(key)

def encrypt_password(plain_password: str) -> str:
    """Parolni AES-256 orqali bazaga shifrlab yozish"""
    cipher = get_fernet_cipher()
    encrypted_bytes = cipher.encrypt(plain_password.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_password(encrypted_token: str) -> str:
    """AES-256 bilan shifrlangan parolni qayta tiklab o'qish"""
    cipher = get_fernet_cipher()
    decrypted_bytes = cipher.decrypt(encrypted_token.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")
