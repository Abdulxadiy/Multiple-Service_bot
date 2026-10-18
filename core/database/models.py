from datetime import datetime, timezone
from sqlalchemy import BigInteger, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database.base import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pin_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recovery_code_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Aloqalar
    categories: Mapped[list["Category"]] = relationship(
        "Category", back_populates="user", cascade="all, delete-orphan"
    )
    accounts: Mapped[list["Account"]] = relationship(
        "Account", back_populates="user", cascade="all, delete-orphan"
    )
    reminders: Mapped[list["Reminder"]] = relationship(
        "Reminder", back_populates="user", cascade="all, delete-orphan"
    )
    wallets: Mapped[list["Wallet"]] = relationship(
        "Wallet", back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    finance_categories: Mapped[list["FinanceCategory"]] = relationship(
        "FinanceCategory", back_populates="user", cascade="all, delete-orphan"
    )

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Aloqalar
    user: Mapped["User"] = relationship("User", back_populates="categories")
    accounts: Mapped[list["Account"]] = relationship(
        "Account", back_populates="category", cascade="all, delete-orphan"
    )

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    login: Mapped[str | None] = mapped_column(String(255), nullable=True)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Aloqalar
    category: Mapped["Category"] = relationship("Category", back_populates="accounts")
    user: Mapped["User"] = relationship("User", back_populates="accounts")

class PendingDeletion(Base):
    """20 daqiqadan keyin xavfsiz avto-o'chirilishi kerak bo'lgan xabarlar"""
    __tablename__ = "pending_deletions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    delete_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

class Reminder(Base):
    """Foydalanuvchilarning eslatmalari va bildirishnomalari"""
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True, nullable=False
    )
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_type: Mapped[str] = mapped_column(String(20), default="text")  # 'text', 'voice', 'photo'
    media_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    repeat_type: Mapped[str] = mapped_column(String(20), default="none")  # 'none', 'daily', 'weekly', 'monthly'
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # 'pending', 'notified', 'completed'
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Aloqalar
    user: Mapped["User"] = relationship("User", back_populates="reminders")

class Wallet(Base):
    """Foydalanuvchining hamyonlari (Karta, Naqd pul, Jamg'arma)"""
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # masalan: '💳 Karta', '💵 Naqd pul'
    balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)  # so'mda
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Aloqalar
    user: Mapped["User"] = relationship("User", back_populates="wallets")
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="wallet", cascade="all, delete-orphan"
    )

class Transaction(Base):
    """Kirim va chiqim amallari tarixi"""
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True, nullable=False
    )
    wallet_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("wallets.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'income' yoki 'expense'
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # musbat miqdor (so'mda)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # '🍔 Oziq-ovqat', '🚕 Transport', etc.
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    # Aloqalar
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    wallet: Mapped["Wallet | None"] = relationship("Wallet", back_populates="transactions")

class FinanceCategory(Base):
    """Foydalanuvchining shaxsiy moliya kategoriyalari (Kirim va Chiqim)"""
    __tablename__ = "finance_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'income' yoki 'expense'
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Aloqalar
    user: Mapped["User"] = relationship("User", back_populates="finance_categories")

