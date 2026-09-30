import hashlib
import secrets
import string
from cryptography.fernet import Fernet
from config.settings import settings

# Salt for hashing PIN and Recovery codes
SALT = "MultipleServiceBot_SecureSalt_2026"

def hash_secret(plain_text: str) -> str:
    """Xavfsiz SHA-256 xesh yaratish (tuz - salt bilan)"""
    salted = f"{plain_text.strip()}:{SALT}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()

def verify_secret(plain_text: str, hashed_value: str) -> bool:
    """Kiritilgan matn xeshga mos kelishini tekshirish"""
    if not hashed_value:
        return False
    return hash_secret(plain_text) == hashed_value

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
