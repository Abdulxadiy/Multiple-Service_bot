from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Asosiy menyu doimiy tugmalari"""
    keyboard = [
        [KeyboardButton(text="🎛 Xizmatlar")],
        [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="ℹ️ Yordam")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Quyidagi menyulardan birini tanlang..."
    )

def get_services_inline_keyboard() -> InlineKeyboardMarkup:
    """Xizmatlar ro'yxati inline tugmalari"""
    keyboard = [
        [InlineKeyboardButton(text="🔐 Login va Parollar", callback_data="svc:passwords")],
        [
            InlineKeyboardButton(text="📝 Eslatmalar (Yaqinda)", callback_data="svc:soon_notes"),
            InlineKeyboardButton(text="💱 Valyuta (Yaqinda)", callback_data="svc:soon_rates")
        ],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="nav:home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_settings_inline_keyboard(has_pin: bool = False) -> InlineKeyboardMarkup:
    """Sozlamalar bo'limi tugmalari"""
    keyboard = []
    if has_pin:
        keyboard.append([InlineKeyboardButton(text="🔄 PIN kodni o'zgartirish", callback_data="settings:change_pin")])
        keyboard.append([InlineKeyboardButton(text="🔑 Yangi Tiklash kodi olish", callback_data="settings:new_recovery_code")])
    else:
        keyboard.append([InlineKeyboardButton(text="🛡 PIN kod o'rnatish", callback_data="settings:set_pin")])

    keyboard.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="nav:home")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
