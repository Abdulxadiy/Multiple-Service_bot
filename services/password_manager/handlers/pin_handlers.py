from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from core.database.session import async_session_maker
from core.database.models import User, Account
from utils.crypto import (
    hash_secret,
    verify_secret,
    generate_recovery_code,
    decrypt_password
)
from services.password_manager.states import (
    PINSetupStates,
    PINChangeStates,
    PINRecoveryStates,
    PINVerifyStates
)
from services.password_manager.keyboards import (
    get_pin_recovery_options_keyboard
)

pin_router = Router(name="pin_router")

# --- PIN O'RNATISH (SETUP) ---

@pin_router.callback_query(F.data == "settings:set_pin")
async def start_set_pin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(PINSetupStates.waiting_for_new_pin)
    text = (
        "🛡 <b>Yangi PIN-kod o'rnatish</b>\n\n"
        "Iltimos, kamida 4 ta belgidan iborat PIN-kod kiriting:\n"
        "<i>(Faqat raqamlar yoki harflar bo'lishi mumkin)</i>"
    )
    await callback.message.answer(text, parse_mode="HTML")

@pin_router.message(PINSetupStates.waiting_for_new_pin)
async def process_new_pin(message: Message, state: FSMContext):
    pin = message.text.strip() if message.text else ""
    if len(pin) < 4:
        await message.answer("⚠️ PIN-kod kamida 4 ta belgidan iborat bo'lishi kerak. Qaytadan kiriting:")
        return

    # Foydalanuvchi yozgan PIN xabarini darhol o'chirish (xavfsizlik uchun)
    try:
        await message.delete()
    except Exception:
        pass

    await state.update_data(new_pin=pin)
    await state.set_state(PINSetupStates.waiting_for_confirm_pin)
    await message.answer("🔁 Tasdiqlash uchun PIN-kodni qayta kiriting:")

@pin_router.message(PINSetupStates.waiting_for_confirm_pin)
async def process_confirm_pin(message: Message, state: FSMContext):
    confirm_pin = message.text.strip() if message.text else ""
    data = await state.get_data()
    original_pin = data.get("new_pin")

    try:
        await message.delete()
    except Exception:
        pass

    if confirm_pin != original_pin:
        await message.answer("❌ PIN-kodlar mos kelmadi! Boshidan urinib ko'ring.\nKamida 4 ta belgidan iborat yangi PIN kiriting:")
        await state.set_state(PINSetupStates.waiting_for_new_pin)
        return

    # Tiklash kodi generatsiya qilamiz
    raw_recovery_code = generate_recovery_code()
    pin_hash = hash_secret(confirm_pin)
    recovery_hash = hash_secret(raw_recovery_code)

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.pin_hash = pin_hash
            user.recovery_code_hash = recovery_hash
            await session.commit()

    await state.clear()
    success_text = (
        "✅ <b>PIN-kod muvaffaqiyatli o'rnatildi!</b>\n\n"
        f"🔑 <b>Sizning shaxsiy Tiklash Kodingiz:</b>\n"
        f"<code>{raw_recovery_code}</code>\n\n"
        "⚠️ <b>Juda muhim:</b> Ushbu kodni xavfsiz joyga saqlab qo'ying! Agar PIN-kodingizni esdan chiqarsangiz, "
        "faqat shu kod yoki oldin saqlagan login/parolingiz yordamida tiklay olasiz."
    )
    await message.answer(success_text, parse_mode="HTML")

# --- PIN O'ZGARTIRISH (CHANGE PIN) ---

@pin_router.callback_query(F.data == "settings:change_pin")
async def start_change_pin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(PINChangeStates.waiting_for_old_pin)
    await callback.message.answer("🔒 Amaldagi eski PIN-kodingizni kiriting:")

@pin_router.message(PINChangeStates.waiting_for_old_pin)
async def process_old_pin(message: Message, state: FSMContext):
    pin = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user or not verify_secret(pin, user.pin_hash or ""):
            await message.answer("❌ Eski PIN-kod noto'g'ri kiritildi! Bekor qilindi.")
            await state.clear()
            return

    await state.set_state(PINChangeStates.waiting_for_new_pin)
    await message.answer("🆕 Endi yangi PIN-kodni kiriting (kamida 4 ta belgi):")

@pin_router.message(PINChangeStates.waiting_for_new_pin)
async def process_change_new_pin(message: Message, state: FSMContext):
    pin = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass

    if len(pin) < 4:
        await message.answer("⚠️ PIN kamida 4 ta belgidan iborat bo'lishi kerak. Qaytadan kiriting:")
        return

    await state.update_data(new_pin=pin)
    await state.set_state(PINChangeStates.waiting_for_confirm_new_pin)
    await message.answer("🔁 Yangi PIN-kodni tasdiqlash uchun qayta kiriting:")

@pin_router.message(PINChangeStates.waiting_for_confirm_new_pin)
async def process_change_confirm_pin(message: Message, state: FSMContext):
    confirm_pin = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    original_pin = data.get("new_pin")
    if confirm_pin != original_pin:
        await message.answer("❌ Mos kelmadi! PIN o'zgartirish bekor qilindi.")
        await state.clear()
        return

    new_hash = hash_secret(confirm_pin)
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.pin_hash = new_hash
            await session.commit()

    await state.clear()
    await message.answer("✅ PIN-kodingiz muvaffaqiyatli o'zgartirildi!")

# --- YANGI TIKLASH KODI OLISH ---

@pin_router.callback_query(F.data == "settings:new_recovery_code")
async def generate_new_recovery_code_handler(callback: CallbackQuery):
    await callback.answer()
    raw_recovery_code = generate_recovery_code()
    recovery_hash = hash_secret(raw_recovery_code)

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.recovery_code_hash = recovery_hash
            await session.commit()

    text = (
        "🔑 <b>Yangi Tiklash Kodi yaratildi:</b>\n\n"
        f"<code>{raw_recovery_code}</code>\n\n"
        "<i>(Ushbu kodni xavfsiz joyga saqlab oling, eski kod bekor qilindi)</i>"
    )
    await callback.message.answer(text, parse_mode="HTML")

# --- PIN TIKLASH (RECOVERY) TANLOVI ---

@pin_router.callback_query(F.data.startswith("pm:rec:start"))
async def start_recovery(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    text = (
        "❓ <b>PIN-kodni tiklash</b>\n\n"
        "PIN-kodni unutgan bo'lsangiz, uni quyidagi 2 ta usuldan biri orqali tiklashingiz mumkin:\n\n"
        "1. <b>Tiklash kodi orqali:</b> PIN o'rnatganda berilgan maxfiy kodni kiritish.\n"
        "2. <b>Saqlangan login/parol orqali:</b> Seyfingizdagi ixtiyoriy bitta akkauntingiz ma'lumotini to'g'ri kiritish."
    )
    await callback.message.edit_text(text, reply_markup=get_pin_recovery_options_keyboard(), parse_mode="HTML")

# 1-usul: Tiklash kodi orqali
@pin_router.callback_query(F.data == "pm:rec:by_code")
async def recovery_by_code_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(PINRecoveryStates.waiting_for_recovery_code)
    await callback.message.answer("🔑 Iltimos, maxfiy <b>Tiklash kodingizni</b> kiriting (masalan, <code>ABCD-1234</code>):", parse_mode="HTML")

@pin_router.message(PINRecoveryStates.waiting_for_recovery_code)
async def process_recovery_by_code(message: Message, state: FSMContext):
    code = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

    if not user or not verify_secret(code, user.recovery_code_hash or ""):
        await message.answer("❌ Kiritilgan Tiklash kodi noto'g'ri! Iltimos, qayta tekshirib kiriting:")
        return

    await state.set_state(PINRecoveryStates.waiting_for_new_pin)
    await message.answer("✅ Tiklash kodi tasdiqlandi!\n\nEndi yangi PIN-kodingizni kiriting (kamida 4 ta belgi):")

# 2-usul: Saqlangan login/parol orqali (Bilim asosida tiklash)
@pin_router.callback_query(F.data == "pm:rec:by_cred")
async def recovery_by_cred_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(PINRecoveryStates.waiting_for_sample_cred)
    text = (
        "💡 <b>Saqlangan ma'lumot orqali tasdiqlash</b>\n\n"
        "Seyfingizda saqlangan ixtiyoriy bitta akkauntingiz parolini (yoki agar login bo'lsa `login:parol` formatida) kiriting.\n\n"
        "<i>Misol:</i> <code>mening_parolim123</code> yoki <code>user@gmail.com:parol123</code>"
    )
    await callback.message.answer(text, parse_mode="HTML")

@pin_router.message(PINRecoveryStates.waiting_for_sample_cred)
async def process_recovery_by_cred(message: Message, state: FSMContext):
    text_input = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass

    # Foydalanuvchining barcha akkauntlarini tekshiramiz
    async with async_session_maker() as session:
        result = await session.execute(
            select(Account).where(Account.user_id == message.from_user.id)
        )
        accounts = result.scalars().all()

    matched = False
    for acc in accounts:
        try:
            real_pwd = decrypt_password(acc.encrypted_password)
            real_login = acc.login or ""

            # 1. Faqat parol mos kelishi
            if text_input == real_pwd:
                matched = True
                break
            # 2. "login:parol" formatida mos kelishi
            if ":" in text_input:
                in_login, in_pwd = text_input.split(":", 1)
                if in_login.strip() == real_login.strip() and in_pwd.strip() == real_pwd:
                    matched = True
                    break
        except Exception:
            continue

    if not matched:
        await message.answer(
            "❌ Kiritilgan ma'lumot bazangizdagi hech qaysi akkauntga to'g'ri kelmadi!\n"
            "Iltimos, qaytadan aniqroq urinib ko'ring yoki Tiklash kodi orqali urinib ko'ring:"
        )
        return

    await state.set_state(PINRecoveryStates.waiting_for_new_pin)
    await message.answer("✅ Haqiqiy egasi ekanligingiz tasdiqlandi!\n\nEndi yangi PIN-kod kiriting (kamida 4 ta belgi):")

# Yangi PIN o'rnatish bosqichi (tiklashdan so'ng)
@pin_router.message(PINRecoveryStates.waiting_for_new_pin)
async def process_recovery_new_pin(message: Message, state: FSMContext):
    pin = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass

    if len(pin) < 4:
        await message.answer("⚠️ PIN kamida 4 ta belgi bo'lishi kerak. Qaytadan kiriting:")
        return

    await state.update_data(new_pin=pin)
    await state.set_state(PINRecoveryStates.waiting_for_confirm_new_pin)
    await message.answer("🔁 Yangi PIN-kodni tasdiqlash uchun qayta kiriting:")

@pin_router.message(PINRecoveryStates.waiting_for_confirm_new_pin)
async def process_recovery_confirm_pin(message: Message, state: FSMContext):
    confirm_pin = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    original_pin = data.get("new_pin")
    if confirm_pin != original_pin:
        await message.answer("❌ PIN-kodlar mos kelmadi! Qaytadan kiriting:")
        await state.set_state(PINRecoveryStates.waiting_for_new_pin)
        return

    new_hash = hash_secret(confirm_pin)
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.pin_hash = new_hash
            await session.commit()

    await state.clear()
    await message.answer("🎉 <b>Tabriklaymiz! PIN-kodingiz muvaffaqiyatli tiklandi va yangilandi.</b>", parse_mode="HTML")
