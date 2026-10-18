from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.finance_service.utils import (
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
    format_money
)

def get_finance_main_keyboard() -> InlineKeyboardMarkup:
    """Moliya xizmati bosh menyusi"""
    keyboard = [
        [
            InlineKeyboardButton(text="🟢 Kirim qo'shish", callback_data="fin:add_income"),
            InlineKeyboardButton(text="🔴 Chiqim qo'shish", callback_data="fin:add_expense")
        ],
        [
            InlineKeyboardButton(text="📊 Hisobotlar", callback_data="fin:reports"),
            InlineKeyboardButton(text="💳 Hamyonlar", callback_data="fin:wallets")
        ],
        [
            InlineKeyboardButton(text="📜 Oxirgi amallar tarixi", callback_data="fin:history")
        ],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="nav:home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Bekor qilish tugmasi"""
    keyboard = [
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="fin:cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_skip_note_keyboard() -> InlineKeyboardMarkup:
    """Izoh qoldirish yoki o'tkazib yuborish"""
    keyboard = [
        [InlineKeyboardButton(text="➡️ Izohsiz saqlash", callback_data="fin_note:skip")],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="fin:cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_categories_keyboard(transaction_type: str = "expense") -> InlineKeyboardMarkup:
    """Kategoriyalarni tanlash tugmalari"""
    categories = INCOME_CATEGORIES if transaction_type == "income" else EXPENSE_CATEGORIES
    keyboard = []
    
    row = []
    for cat in categories:
        row.append(InlineKeyboardButton(text=cat, callback_data=f"fin_cat:{cat}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="fin:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_wallets_keyboard(wallets: list, prefix: str = "fin_sel_w") -> InlineKeyboardMarkup:
    """Hamyonni tanlash tugmalari"""
    keyboard = []
    for w in wallets:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{w.name} ({format_money(w.balance)})",
                callback_data=f"{prefix}:{w.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="fin:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_reports_menu_keyboard() -> InlineKeyboardMarkup:
    """Hisobotlar menyusi tugmalari"""
    keyboard = [
        [InlineKeyboardButton(text="📅 Bugungi hisobot", callback_data="fin_rep:today")],
        [InlineKeyboardButton(text="📆 Haftalik hisobot", callback_data="fin_rep:week")],
        [InlineKeyboardButton(text="🗓 Oylik hisobot (Shu oy)", callback_data="fin_rep:month")],
        [InlineKeyboardButton(text="🔙 Moliya menyusi", callback_data="svc:finance")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_wallets_manage_keyboard(wallets: list) -> InlineKeyboardMarkup:
    """Hamyonlarni boshqarish menyusi"""
    keyboard = []
    for w in wallets:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{w.name}: {format_money(w.balance)}",
                callback_data=f"fin_w_edit:{w.id}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton(text="➕ Yangi hamyon qo'shish", callback_data="fin_w:new")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Moliya menyusi", callback_data="svc:finance")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_wallet_detail_keyboard(wallet_id: int) -> InlineKeyboardMarkup:
    """Bitta hamyonni tahrirlash yoki balansini o'zgartirish"""
    keyboard = [
        [InlineKeyboardButton(text="💰 Balansni yangilash", callback_data=f"fin_w_setbal:{wallet_id}")],
        [InlineKeyboardButton(text="🗑 Hamyonni o'chirish", callback_data=f"fin_w_del:{wallet_id}")],
        [InlineKeyboardButton(text="🔙 Hamyonlar ro'yxatiga", callback_data="fin:wallets")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_voice_finance_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Ovozli moliya xabari tahlil qilinganda tasdiqlash tugmalari"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Ha, hamyonga saqlansin", callback_data="fin_v_save")],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="fin:cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
