from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.database.models import Category, Account

def get_categories_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    """Foydalanuvchining shaxsiy kategoriyalari ro'yxati"""
    keyboard = []
    # Kategoriyalar 2 tadan yoki 1 tadan qator qilib joylashtiriladi
    row = []
    for cat in categories:
        row.append(InlineKeyboardButton(text=f"📁 {cat.name}", callback_data=f"pm:cat:{cat.id}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="➕ Yangi Kategoriya", callback_data="pm:cat:add")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Xizmatlar ro'yxatiga", callback_data="nav:services")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_accounts_keyboard(category_id: int, accounts: list[Account]) -> InlineKeyboardMarkup:
    """Kategoriya ichidagi akkauntlar ro'yxati"""
    keyboard = []
    for acc in accounts:
        keyboard.append([
            InlineKeyboardButton(text=f"🔹 {acc.title}", callback_data=f"pm:acc:{acc.id}")
        ])

    keyboard.append([InlineKeyboardButton(text="➕ Yangi akkaunt qo'shish", callback_data=f"pm:acc:add:{category_id}")])
    keyboard.append([InlineKeyboardButton(text="🗑 Ushbu kategoriyani o'chirish", callback_data=f"pm:cat:del_confirm:{category_id}")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Kategoriyalar ro'yxatiga", callback_data="svc:passwords")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_account_detail_keyboard(account_id: int, category_id: int) -> InlineKeyboardMarkup:
    """Akkaunt tafsilotlari ko'ringandagi tugmalar"""
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"pm:acc:edit:{account_id}"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"pm:acc:del_confirm:{account_id}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Akkauntlar ro'yxatiga qaytish", callback_data=f"pm:cat:{category_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_password_input_keyboard() -> InlineKeyboardMarkup:
    """Parol kiritishda kuchli parol generatsiya qilish tugmasi"""
    keyboard = [
        [InlineKeyboardButton(text="🎲 Kuchli parol yaratish", callback_data="pm:gen_pwd")],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="svc:passwords")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_skip_keyboard(skip_callback: str) -> InlineKeyboardMarkup:
    """Ixtiyoriy maydonlar uchun o'tkazib yuborish tugmasi"""
    keyboard = [
        [InlineKeyboardButton(text="O'tkazib yuborish ⏭", callback_data=skip_callback)],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="svc:passwords")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_pin_prompt_keyboard(account_id: int) -> InlineKeyboardMarkup:
    """PIN kod so'ralganda chiqadigan tugmalar"""
    keyboard = [
        [InlineKeyboardButton(text="❓ PIN kodni unutdingizmi?", callback_data=f"pm:rec:start:{account_id}")],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="svc:passwords")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_pin_recovery_options_keyboard() -> InlineKeyboardMarkup:
    """PIN kodni tiklash yo'llari"""
    keyboard = [
        [InlineKeyboardButton(text="🔑 Tiklash kodi orqali", callback_data="pm:rec:by_code")],
        [InlineKeyboardButton(text="💡 Saqlangan login/parol orqali", callback_data="pm:rec:by_cred")],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="svc:passwords")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_delete_keyboard(confirm_callback: str, cancel_callback: str) -> InlineKeyboardMarkup:
    """O'chirishni tasdiqlash dialogi"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Ha, o'chirilsin", callback_data=confirm_callback),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=cancel_callback)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_edit_fields_keyboard(account_id: int) -> InlineKeyboardMarkup:
    """Akkauntning qaysi maydonini tahrirlash tanlovi"""
    keyboard = [
        [InlineKeyboardButton(text="🏷 Nomini o'zgartirish", callback_data=f"pm:edit_field:title:{account_id}")],
        [InlineKeyboardButton(text="👤 Loginni o'zgartirish", callback_data=f"pm:edit_field:login:{account_id}")],
        [InlineKeyboardButton(text="🔑 Parolni o'zgartirish", callback_data=f"pm:edit_field:password:{account_id}")],
        [InlineKeyboardButton(text="📝 Eslatmani o'zgartirish", callback_data=f"pm:edit_field:note:{account_id}")],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data=f"pm:acc:{account_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
