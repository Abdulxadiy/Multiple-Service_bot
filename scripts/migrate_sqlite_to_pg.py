"""
SQLite dan PostgreSQL ga ma'lumotlarni xavfsiz ko'chirish (migratsiya) skripti.
Ushbu skript SQLite dagi 'bot.db' faylidan barcha foydalanuvchilar, kategoriyalar,
akkauntlar va avto-o'chirish navbatidagi xabarlarni PostgreSQL bazasiga to'liq ko'chirib beradi.

Foydalanish:
    python scripts/migrate_sqlite_to_pg.py --sqlite bot.db --pg-url postgresql://user:pass@host:5432/dbname
    yoki .env dagi DATABASE_URL dan avtomatik foydalanish:
    python scripts/migrate_sqlite_to_pg.py
"""

import sys
import os
import argparse
import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text, select

# Loyiha ildiz papkasini sys.path ga qo'shish
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import settings
from core.database.base import Base
from core.database.models import User, Category, Account, PendingDeletion

def parse_sqlite_datetime(val: str | None) -> datetime | None:
    """SQLite matnli sanasini datetime obyektiga xavfsiz aylantirish"""
    if not val:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
    try:
        # ISO formatni tekshirish
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(val, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
    return datetime.now(timezone.utc)

async def run_migration(sqlite_path: Path, pg_url: str):
    if not sqlite_path.exists():
        print(f"❌ Xatolik: SQLite bazasi topilmadi: {sqlite_path}")
        sys.exit(1)

    print(f"📦 1. SQLite baza o'qilmoqda: {sqlite_path}")
    con = sqlite3.connect(sqlite_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    users_rows = cur.execute("SELECT * FROM users").fetchall()
    categories_rows = cur.execute("SELECT * FROM categories").fetchall()
    accounts_rows = cur.execute("SELECT * FROM accounts").fetchall()
    try:
        pending_rows = cur.execute("SELECT * FROM pending_deletions").fetchall()
    except Exception:
        pending_rows = []
    con.close()

    print(f"   - Users topildi: {len(users_rows)} ta")
    print(f"   - Categories topildi: {len(categories_rows)} ta")
    print(f"   - Accounts topildi: {len(accounts_rows)} ta")
    print(f"   - Pending deletions topildi: {len(pending_rows)} ta")

    # PostgreSQL URL tekshiruvi va asyncpg formatiga keltirish
    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif pg_url.startswith("postgresql://") and not pg_url.startswith("postgresql+asyncpg://"):
        pg_url = pg_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"\n🔌 2. PostgreSQL ga ulanmoqda: {pg_url.split('@')[-1] if '@' in pg_url else pg_url}")
    pg_engine = create_async_engine(pg_url, echo=False)
    pg_session_maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)

    # 1-qadam: PostgreSQL jadvallarini yaratish (agar mavjud bo'lmasa)
    print("   - PostgreSQL jadvallari tekshirilmoqda / yaratilmoqda...")
    async with pg_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2-qadam: Ma'lumotlarni ko'chirish
    async with pg_session_maker() as session:
        async with session.begin():
            # a) Users
            migrated_users = 0
            for r in users_rows:
                exists = await session.execute(
                    select(User).where(User.telegram_id == r["telegram_id"])
                )
                if not exists.scalar_one_or_none():
                    u = User(
                        telegram_id=r["telegram_id"],
                        username=r["username"],
                        pin_hash=r["pin_hash"],
                        recovery_code_hash=r["recovery_code_hash"],
                        created_at=parse_sqlite_datetime(r["created_at"])
                    )
                    session.add(u)
                    migrated_users += 1

            # b) Categories
            migrated_cats = 0
            for r in categories_rows:
                exists = await session.execute(
                    select(Category).where(Category.id == r["id"])
                )
                if not exists.scalar_one_or_none():
                    c = Category(
                        id=r["id"],
                        user_id=r["user_id"],
                        name=r["name"],
                        created_at=parse_sqlite_datetime(r["created_at"])
                    )
                    session.add(c)
                    migrated_cats += 1

            # c) Accounts
            migrated_accs = 0
            for r in accounts_rows:
                exists = await session.execute(
                    select(Account).where(Account.id == r["id"])
                )
                if not exists.scalar_one_or_none():
                    a = Account(
                        id=r["id"],
                        category_id=r["category_id"],
                        user_id=r["user_id"],
                        title=r["title"],
                        login=r["login"],
                        encrypted_password=r["encrypted_password"],
                        note=r["note"],
                        created_at=parse_sqlite_datetime(r["created_at"]),
                        updated_at=parse_sqlite_datetime(r["updated_at"])
                    )
                    session.add(a)
                    migrated_accs += 1

            # d) Pending Deletions
            migrated_pending = 0
            for r in pending_rows:
                p = PendingDeletion(
                    id=r["id"],
                    chat_id=r["chat_id"],
                    message_id=r["message_id"],
                    delete_at=parse_sqlite_datetime(r["delete_at"])
                )
                session.add(p)
                migrated_pending += 1

        # 3-qadam: PostgreSQL autoincrement sequence larini eng katta id ga sinxronlash
        print("\n🔄 3. PostgreSQL sequence (ID sanagichlari) sinxronlashtirilmoqda...")
        async with session.begin():
            for tbl, seq in [
                ("categories", "categories_id_seq"),
                ("accounts", "accounts_id_seq"),
                ("pending_deletions", "pending_deletions_id_seq")
            ]:
                try:
                    res = await session.execute(text(f"SELECT COALESCE(MAX(id), 0) FROM {tbl}"))
                    max_id = res.scalar() or 0
                    if max_id > 0:
                        await session.execute(text(f"SELECT setval('{seq}', {max_id})"))
                        print(f"   - {seq} -> {max_id} ga o'rnatildi")
                except Exception as seq_err:
                    print(f"   ⚠️ Sequence {seq} ogohlantirish: {seq_err}")

    await pg_engine.dispose()

    print("\n" + "=" * 50)
    print("🎉 MIGRATSIYA MUVAFFAQIYATLI YAKUNLANDI!")
    print(f"   ✅ Users ko'chirildi: {migrated_users} ta")
    print(f"   ✅ Categories ko'chirildi: {migrated_cats} ta")
    print(f"   ✅ Accounts ko'chirildi: {migrated_accs} ta")
    print(f"   ✅ Pending deletions: {migrated_pending} ta")
    print("=" * 50)

def main():
    parser = argparse.ArgumentParser(description="SQLite bazasini PostgreSQL ga ko'chirish vositasi")
    parser.add_argument("--sqlite", default=str(BASE_DIR / "bot.db"), help="SQLite db fayli yo'li (standart: bot.db)")
    parser.add_argument("--pg-url", default=None, help="PostgreSQL ulanish URL manzili (standart: .env dagi DATABASE_URL)")

    args = parser.parse_args()
    sqlite_file = Path(args.sqlite)

    pg_url = args.pg_url or settings.DATABASE_URL
    if "sqlite" in pg_url:
        print("❌ Xatolik: PostgreSQL URL ko'rsatilmadi!")
        print("Iltimos, --pg-url parametri orqali yoki .env faylida PostgreSQL manzilini ko'rsating:")
        print("Masalan: python scripts/migrate_sqlite_to_pg.py --pg-url postgresql://postgres:parol@localhost:5432/botdb")
        sys.exit(1)

    asyncio.run(run_migration(sqlite_file, pg_url))

if __name__ == "__main__":
    main()
