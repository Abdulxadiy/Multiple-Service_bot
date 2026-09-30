from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from core.database.session import async_session_maker
from core.database.models import User
from core.keyboards.main_menu import (
    get_main_reply_keyboard,
    get_services_inline_keyboard,
    get_settings_inline_keyboard
)

base_router = Router(name="base_router")

@base_router.message(CommandStart())
async def handle_start(message: Message):
    user_name = message.from_user.first_name if message.from_user else "Foydalanuvchi"
    welcome_text = (
        f"👋 Assalomu alaykum, <b>{user_name}</b>!\n\n"
        f"<b>Multiple-Service Bot</b>ga xush kelibsiz.\n"
        f"Ushbu bot orqali siz turli xil foydali xizmatlardan bitta joyda foydalanishingiz mumkin.\n\n"
        f"Hozirda faol xizmat: 🔐 <b>Login va Parollar Menejeri</b> (shaxsiy seyf).\n\n"
        f"Boshlash uchun quyidagi menyulardan birini tanlang:"
    )
    await message.answer(
        welcome_text,
        reply_markup=get_main_reply_keyboard(),
        parse_mode="HTML"
    )

@base_router.message(F.text == "🎛 Xizmatlar")
async def handle_services_menu(message: Message):
    text = (
        "🎛 <b>Mavjud Xizmatlar Bo'limi:</b>\n\n"
        "Quyidagi xizmatlardan birini tanlang:"
    )
    await message.answer(text, reply_markup=get_services_inline_keyboard(), parse_mode="HTML")

@base_router.callback_query(F.data == "nav:home")
async def handle_nav_home(callback: CallbackQuery):
    await callback.answer()
    text = (
        "🏠 <b>Asosiy menyu</b>\n\n"
        "Kerakli bo'limni tanlash uchun pastdagi tugmalardan foydalaning:"
    )
    await callback.message.edit_text(text, parse_mode="HTML")

@base_router.callback_query(F.data == "nav:services")
async def handle_nav_services(callback: CallbackQuery):
    await callback.answer()
    text = (
        "🎛 <b>Mavjud Xizmatlar Bo'limi:</b>\n\n"
        "Quyidagi xizmatlardan birini tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=get_services_inline_keyboard(), parse_mode="HTML")

@base_router.message(F.text == "⚙️ Sozlamalar")
async def handle_settings_menu(message: Message):
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        has_pin = bool(user and user.pin_hash)

    status_pin = "✅ O'rnatilgan" if has_pin else "❌ O'rnatilmagan"
    text = (
        "⚙️ <b>Xavfsizlik va Sozlamalar Bo'limi:</b>\n\n"
        f"🛡 <b>PIN-kod holati:</b> {status_pin}\n\n"
        "Sozlamalarni o'zgartirish uchun quyidagi tugmalardan birini tanlang:"
    )
    await message.answer(text, reply_markup=get_settings_inline_keyboard(has_pin), parse_mode="HTML")

@base_router.callback_query(F.data.startswith("svc:soon_"))
async def handle_soon_services(callback: CallbackQuery):
    await callback.answer("⏳ Ushbu xizmat tez kunda taqdim etiladi!", show_alert=True)

@base_router.message(F.text == "ℹ️ Yordam")
@base_router.message(Command("help"))
async def handle_help_menu(message: Message):
    text = (
        "ℹ️ <b>Multiple-Service Bot haqida ma'lumot:</b>\n\n"
        "🔐 <b>Login va Parollar Seyfi:</b>\n"
        "• Barcha parollaringiz AES-256 xalqaro shifrlash standarti orqali himoyalanadi.\n"
        "• Har bir foydalanuvchining ma'lumotlari to'liq alohida saqlanadi.\n"
        "• PIN kod o'rnatilgach, parollaringizni faqat siz ko'ra olasiz.\n"
        "• Ko'rilgan maxfiy login va parollar 20 daqiqadan so'ng chatdan avtomatik yo'q qilinadi.\n"
        "• Bir marta bosishda nusxalash (`monospaced`) qulayligi mavjud.\n\n"
        "Savol yoki takliflar uchun adminga murojaat qilishingiz mumkin."
    )
    await message.answer(text, parse_mode="HTML")
