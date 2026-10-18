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
            InlineKeyboardButton(text="🏷 Kategoriyalar", callback_data="fin:categories"),
            InlineKeyboardButton(text="📜 Amallar tarixi", callback_data="fin:history")
        ],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="nav:home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_cancel_keyboard(callback_data: str = "fin:cancel") -> InlineKeyboardMarkup:
    """Bekor qilish tugmasi"""
    keyboard = [
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data=callback_data)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_skip_note_keyboard() -> InlineKeyboardMarkup:
    """Izoh qoldirish yoki o'tkazib yuborish"""
    keyboard = [
        [InlineKeyboardButton(text="➡️ Izohsiz saqlash", callback_data="fin_note:skip")],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="fin:cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_skip_category_name_keyboard() -> InlineKeyboardMarkup:
    """Boshqa bosilganda nom kiritmasdan o'tkazib yuborish"""
    keyboard = [
        [InlineKeyboardButton(text="⏩ Nomni o'tkazib yuborish", callback_data="fin_cat_other:skip")],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="fin:cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_categories_keyboard(categories: list, transaction_type: str = "expense") -> InlineKeyboardMarkup:
    """Kategoriyalarni tanlash tugmalari (foydalanuvchi kategoriyalari va Boshqa tugmasi)"""
    keyboard = []
    row = []
    for cat in categories:
        cat_name = cat.name if hasattr(cat, "name") else str(cat)
        cat_id = cat.id if hasattr(cat, "id") else None
        cb_data = f"fin_cat_id:{cat_id}" if cat_id is not None else f"fin_cat:{cat_name}"
        row.append(InlineKeyboardButton(text=cat_name, callback_data=cb_data))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Maxsus '🔄 Boshqa' tugmasi
    keyboard.append([InlineKeyboardButton(text="🔄 Boshqa", callback_data="fin_cat_other")])
    keyboard.append([InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="fin:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_categories_manage_menu_keyboard() -> InlineKeyboardMarkup:
    """Kategoriyalarni boshqarish asosiy menyusi"""
    keyboard = [
        [InlineKeyboardButton(text="🔴 Chiqim kategoriyalari", callback_data="fin_cat_list:expense")],
        [InlineKeyboardButton(text="🟢 Kirim kategoriyalari", callback_data="fin_cat_list:income")],
        [InlineKeyboardButton(text="➕ Yangi kategoriya qo'shish", callback_data="fin_cat_add_prompt")],
        [InlineKeyboardButton(text="🔙 Moliya menyusi", callback_data="svc:finance")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_category_list_manage_keyboard(categories: list, cat_type: str) -> InlineKeyboardMarkup:
    """Kategoriyalar ro'yxatini boshqarish tugmalari"""
    keyboard = []
    row = []
    for cat in categories:
        row.append(InlineKeyboardButton(text=cat.name, callback_data=f"fin_cat_view:{cat.id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(text="➕ Kategoriya qo'shish", callback_data=f"fin_cat_add:{cat_type}")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🔙 Kategoriyalar menyusi", callback_data="fin:categories")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_category_detail_keyboard(cat_id: int, cat_type: str) -> InlineKeyboardMarkup:
    """Kategoriya tafsiloti: nomini o'zgartirish yoki o'chirish"""
    keyboard = [
        [InlineKeyboardButton(text="✏️ Nomini o'zgartirish", callback_data=f"fin_cat_rename:{cat_id}")],
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"fin_cat_del:{cat_id}")],
        [InlineKeyboardButton(text="🔙 Ro'yxatga qaytish", callback_data=f"fin_cat_list:{cat_type}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_choose_cat_type_keyboard() -> InlineKeyboardMarkup:
    """Kategoriya qo'shishda turini tanlash"""
    keyboard = [
        [
            InlineKeyboardButton(text="🟢 Kirim uchun", callback_data="fin_cat_add:income"),
            InlineKeyboardButton(text="🔴 Chiqim uchun", callback_data="fin_cat_add:expense")
        ],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="fin:categories")]
    ]
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
