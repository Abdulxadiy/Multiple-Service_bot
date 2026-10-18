from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_currency_main_keyboard() -> InlineKeyboardMarkup:
    """Valyuta xizmati bosh menyusi"""
    keyboard = [
        [
            InlineKeyboardButton(text="🔄 Kurslarni yangilash", callback_data="cur:refresh"),
            InlineKeyboardButton(text="🧮 Hisoblash (Kalkulyator)", callback_data="cur:calc")
        ],
        [
            InlineKeyboardButton(text="💵 100 $ ➡️ So'm", callback_data="cur_preset:100:USD"),
            InlineKeyboardButton(text="💵 500 $ ➡️ So'm", callback_data="cur_preset:500:USD")
        ],
        [
            InlineKeyboardButton(text="💶 100 € ➡️ So'm", callback_data="cur_preset:100:EUR"),
            InlineKeyboardButton(text="🇷🇺 5 000 ₽ ➡️ So'm", callback_data="cur_preset:5000:RUB")
        ],
        [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="nav:home")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_calculator_keyboard() -> InlineKeyboardMarkup:
    """Kalkulyator menyusi"""
    keyboard = [
        [
            InlineKeyboardButton(text="🇺🇸 USD ➡️ UZS", callback_data="cur_mode:USD_UZS"),
            InlineKeyboardButton(text="🇺🇿 UZS ➡️ USD", callback_data="cur_mode:UZS_USD")
        ],
        [
            InlineKeyboardButton(text="🇪🇺 EUR ➡️ UZS", callback_data="cur_mode:EUR_UZS"),
            InlineKeyboardButton(text="🇷🇺 RUB ➡️ UZS", callback_data="cur_mode:RUB_UZS")
        ],
        [InlineKeyboardButton(text="🔙 Valyuta menyusiga", callback_data="svc:currency")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Bekor qilish"""
    keyboard = [
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="svc:currency")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
