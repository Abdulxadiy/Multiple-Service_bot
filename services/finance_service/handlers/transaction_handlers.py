from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from core.database.session import async_session_maker
from core.database.models import User, Wallet, Transaction
from services.finance_service.states import FinanceState
from services.finance_service.keyboards import (
    get_cancel_keyboard,
    get_skip_note_keyboard,
    get_categories_keyboard,
    get_wallets_keyboard,
    get_finance_main_keyboard
)
from services.finance_service.utils import (
    format_money,
    parse_money_input,
    detect_category
)
from services.finance_service.handlers.menu_handlers import ensure_default_wallets

transaction_router = Router(name="finance_transaction_router")

@transaction_router.callback_query(F.data.in_(["fin:add_income", "fin:add_expense"]))
async def handle_start_transaction(callback: CallbackQuery, state: FSMContext):
    t_type = "income" if callback.data == "fin:add_income" else "expense"
    await state.clear()
    await state.set_state(FinanceState.waiting_for_amount)
    await state.update_data(transaction_type=t_type)
    await callback.answer()

    label = "🟢 <b>Kirim (Daromad)</b>" if t_type == "income" else "🔴 <b>Chiqim (Xarajat)</b>"
    text = (
        f"{label} qo'shish:\n\n"
        "Summani kiriting (masalan: <code>35000</code> yoki <code>50k</code> yoki <code>1.5 mln</code>):"
    )
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

@transaction_router.message(FinanceState.waiting_for_amount, F.text)
async def process_amount(message: Message, state: FSMContext):
    amount, note, parsed_type = parse_money_input(message.text)
    if not amount or amount <= 0:
        await message.answer(
            "⚠️ Summa noto'g'ri kiritildi. Iltimos, raqamlar bilan yozing (masalan: <code>45000</code> yoki <code>50k</code>):",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    t_type = data.get("transaction_type", parsed_type)

    await state.update_data(amount=amount, preliminary_note=note)

    # Hamyonlarni olish
    async with async_session_maker() as session:
        wallets = await ensure_default_wallets(session, message.from_user.id, message.from_user.username)

    await state.set_state(FinanceState.waiting_for_wallet)
    text = (
        f"💵 <b>Summa:</b> {format_money(amount)}\n\n"
        "Qaysi hamyondan amalga oshirilmoqda?"
    )
    await message.answer(text, reply_markup=get_wallets_keyboard(wallets), parse_mode="HTML")

@transaction_router.callback_query(FinanceState.waiting_for_wallet, F.data.startswith("fin_sel_w:"))
async def process_wallet_selection(callback: CallbackQuery, state: FSMContext):
    wallet_id = int(callback.data.split(":")[1])
    await callback.answer()
    await state.update_data(wallet_id=wallet_id)

    data = await state.get_data()
    t_type = data.get("transaction_type", "expense")

    await state.set_state(FinanceState.waiting_for_category)
    text = "📂 <b>Kategoriyani tanlang:</b>"
    await callback.message.edit_text(text, reply_markup=get_categories_keyboard(t_type), parse_mode="HTML")

@transaction_router.callback_query(FinanceState.waiting_for_category, F.data.startswith("fin_cat:"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":", 1)[1]
    await callback.answer()
    await state.update_data(category=category)

    data = await state.get_data()
    # Agar oldindan izoh yozilgan bo'lsa (masalan: "35000 tushlik")
    if data.get("preliminary_note"):
        await save_transaction(callback.message, state, data.get("preliminary_note"), is_callback=True)
        return

    await state.set_state(FinanceState.waiting_for_note)
    text = (
        "✍️ <b>Izoh kiritasizmi?</b>\n\n"
        "Masalan: «Oila uchun bozorlik» yoki «Tushlik do'stlar bilan».\n"
        "Agar kerak bo'lmasa, pastdagi tugmani bosing:"
    )
    await callback.message.edit_text(text, reply_markup=get_skip_note_keyboard(), parse_mode="HTML")

@transaction_router.callback_query(FinanceState.waiting_for_note, F.data == "fin_note:skip")
async def process_skip_note(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await save_transaction(callback.message, state, note=None, is_callback=True)

@transaction_router.message(FinanceState.waiting_for_note, F.text)
async def process_note_text(message: Message, state: FSMContext):
    await save_transaction(message, state, note=message.text.strip(), is_callback=False)

async def save_transaction(message: Message, state: FSMContext, note: str | None, is_callback: bool = False):
    """Tranzaksiyani bazaga saqlash va hamyon balansini yangilash"""
    data = await state.get_data()
    await state.clear()

    user_id = message.chat.id
    amount = data["amount"]
    t_type = data["transaction_type"]
    wallet_id = data["wallet_id"]
    category = data["category"]

    async with async_session_maker() as session:
        wallet = await session.get(Wallet, wallet_id)
        if not wallet:
            # Agar topilmasa birinchi hamyonni olamiz
            res = await session.execute(select(Wallet).where(Wallet.user_id == user_id))
            wallet = res.scalars().first()

        # Balansni yangilash
        if t_type == "income":
            wallet.balance += amount
        else:
            wallet.balance -= amount

        tx = Transaction(
            user_id=user_id,
            wallet_id=wallet.id,
            type=t_type,
            amount=amount,
            category=category,
            note=note
        )
        session.add(tx)
        await session.commit()
        wallet_name = wallet.name
        new_balance = wallet.balance

    type_icon = "🟢 Kirim" if t_type == "income" else "🔴 Chiqim"
    sign = "+" if t_type == "income" else "-"
    note_line = f"\n📝 <b>Izoh:</b> {note}" if note else ""

    success_text = (
        f"✅ <b>{type_icon} muvaffaqiyatli saqlandi!</b>\n\n"
        f"💵 <b>Miqdor:</b> <code>{sign}{format_money(amount)}</code>\n"
        f"📂 <b>Kategoriya:</b> {category}\n"
        f"💳 <b>Hamyon:</b> {wallet_name} (Qoldiq: <code>{format_money(new_balance)}</code>)"
        f"{note_line}"
    )

    if is_callback:
        await message.edit_text(success_text, reply_markup=get_finance_main_keyboard(), parse_mode="HTML")
    else:
        await message.answer(success_text, reply_markup=get_finance_main_keyboard(), parse_mode="HTML")

# Tezkor kiritish (Smart Quick Input - har qanday menyuda yoki bo'sh holatda)
@transaction_router.message(F.text.regexp(r"^(\+)?\s*\d+(?:[\s.,]\d+)*\s*(k|ming|mln)?(?:\s+.+)?$", flags=2))
async def handle_quick_money_input(message: Message, state: FSMContext):
    # Agar boshqa biror FSM holatida bo'lsa (masalan eslatma yozayotgan bo'lsa), xalal bermaymiz
    current_state = await state.get_state()
    if current_state is not None:
        return

    amount, note, t_type = parse_money_input(message.text)
    if not amount or amount <= 0:
        return

    category = detect_category(note, t_type)

    async with async_session_maker() as session:
        wallets = await ensure_default_wallets(session, message.from_user.id, message.from_user.username)
        # Asosiy hamyon (default) yoki birinchisi
        wallet = next((w for w in wallets if w.is_default), wallets[0])

        if t_type == "income":
            wallet.balance += amount
        else:
            wallet.balance -= amount

        tx = Transaction(
            user_id=message.from_user.id,
            wallet_id=wallet.id,
            type=t_type,
            amount=amount,
            category=category,
            note=note
        )
        session.add(tx)
        await session.commit()
        new_balance = wallet.balance
        wallet_name = wallet.name

    type_icon = "🟢 Kirim" if t_type == "income" else "🔴 Chiqim"
    sign = "+" if t_type == "income" else "-"
    note_line = f"\n📝 <b>Izoh:</b> {note}" if note else ""

    text = (
        f"⚡️ <b>{type_icon} qayd etildi:</b>\n\n"
        f"💵 <b>Miqdor:</b> <code>{sign}{format_money(amount)}</code>\n"
        f"📂 <b>Kategoriya:</b> {category}\n"
        f"💳 <b>Hamyon:</b> {wallet_name} (Qoldiq: <code>{format_money(new_balance)}</code>)"
        f"{note_line}"
    )
    await message.answer(text, reply_markup=get_finance_main_keyboard(), parse_mode="HTML")

import os
import tempfile
from services.reminder_service.stt import transcribe_voice
from services.finance_service.utils import extract_financial_from_text
from services.finance_service.keyboards import get_voice_finance_confirmation_keyboard

@transaction_router.message(F.voice)
async def handle_voice_finance_input(message: Message, state: FSMContext):
    """Ovozli xabar orqali xarajat yoki daromadni kiritish"""
    current_state = await state.get_state()
    # Agar boshqa biror aniq jarayonda bo'lsa (masalan hamyon nomi kiritish), e'tiborsiz qoldirish
    if current_state in [FinanceState.waiting_for_wallet_name, FinanceState.waiting_for_set_balance]:
        return

    status_msg = await message.answer(
        "⏳ <i>Ovozingiz tinglanmoqda va tahlil qilinmoqda...</i>",
        parse_mode="HTML"
    )

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_ogg:
        temp_ogg_path = temp_ogg.name

    try:
        await message.bot.download(message.voice, destination=temp_ogg_path)
        transcribed_text = await transcribe_voice(temp_ogg_path)
    finally:
        if os.path.exists(temp_ogg_path):
            try:
                os.remove(temp_ogg_path)
            except OSError:
                pass

    if not transcribed_text:
        await status_msg.edit_text(
            "⚠️ <b>Ovozingizni aniqlab bo'lmadi.</b>\n\n"
            "Iltimos, shovqinsizroq joyda biroz balandroq va aniqroq gapirib ko'ring yoki matn sifatida yozing.",
            reply_markup=get_finance_main_keyboard(),
            parse_mode="HTML"
        )
        return

    amount, t_type, category, note = extract_financial_from_text(transcribed_text)

    async with async_session_maker() as session:
        wallets = await ensure_default_wallets(session, message.from_user.id, message.from_user.username)
        wallet = next((w for w in wallets if w.is_default), wallets[0])

    if not amount or amount <= 0:
        # Summa aniqlanmadi, lekin mavzu tushunildi
        await state.set_state(FinanceState.waiting_for_amount)
        await state.update_data(
            transaction_type=t_type,
            category=category,
            preliminary_note=transcribed_text,
            wallet_id=wallet.id
        )
        await status_msg.edit_text(
            f"🎙 <b>Ovozingiz:</b> «<i>{transcribed_text}</i>»\n"
            f"📂 <b>Kategoriya:</b> {category}\n\n"
            "⚠️ <i>Lekin qancha summa ekanligi aniqlanmadi.</i>\n\n"
            "Summani yozing (masalan: <code>35000</code> yoki <code>50k</code>):",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    # Summa muvaffaqiyatli aniqlandi -> Tasdiqlashni so'raymiz
    await state.update_data(
        amount=amount,
        transaction_type=t_type,
        category=category,
        wallet_id=wallet.id,
        voice_note=transcribed_text
    )

    type_icon = "🟢 Kirim" if t_type == "income" else "🔴 Chiqim"
    sign = "+" if t_type == "income" else "-"

    confirm_text = (
        "🎙 <b>Ovozli xabaringiz tushunildi:</b>\n\n"
        f"🗣 «<i>{transcribed_text}</i>»\n\n"
        f"💵 <b>Miqdor:</b> <code>{sign}{format_money(amount)}</code>\n"
        f"📊 <b>Turi:</b> {type_icon}\n"
        f"📂 <b>Kategoriya:</b> {category}\n"
        f"💳 <b>Hamyon:</b> {wallet.name}\n\n"
        "❓ <b>Hamyonga saqlansinmi?</b>"
    )
    await status_msg.edit_text(confirm_text, reply_markup=get_voice_finance_confirmation_keyboard(), parse_mode="HTML")

@transaction_router.callback_query(F.data == "fin_v_save")
async def handle_voice_finance_save(callback: CallbackQuery, state: FSMContext):
    """Ovozli kiritilgan moliyani tasdiqlash va saqlash"""
    data = await state.get_data()
    if not data or "amount" not in data:
        await callback.answer("Ma'lumot topilmadi.", show_alert=True)
        return

    await state.clear()
    await callback.answer("✅ Saqlandi!")

    user_id = callback.from_user.id
    amount = data["amount"]
    t_type = data["transaction_type"]
    wallet_id = data["wallet_id"]
    category = data["category"]
    note = data.get("voice_note")

    async with async_session_maker() as session:
        wallet = await session.get(Wallet, wallet_id)
        if not wallet:
            wallets = await ensure_default_wallets(session, user_id, callback.from_user.username)
            wallet = wallets[0]

        if t_type == "income":
            wallet.balance += amount
        else:
            wallet.balance -= amount

        tx = Transaction(
            user_id=user_id,
            wallet_id=wallet.id,
            type=t_type,
            amount=amount,
            category=category,
            note=note
        )
        session.add(tx)
        await session.commit()
        new_balance = wallet.balance
        wallet_name = wallet.name

    type_icon = "🟢 Kirim" if t_type == "income" else "🔴 Chiqim"
    sign = "+" if t_type == "income" else "-"

    success_text = (
        f"✅ <b>{type_icon} muvaffaqiyatli saqlandi!</b>\n\n"
        f"💵 <b>Miqdor:</b> <code>{sign}{format_money(amount)}</code>\n"
        f"📂 <b>Kategoriya:</b> {category}\n"
        f"💳 <b>Hamyon:</b> {wallet_name} (Qoldiq: <code>{format_money(new_balance)}</code>)\n"
        f"📝 <b>Ovoz:</b> «<i>{note}</i>»"
    )
    await callback.message.edit_text(success_text, reply_markup=get_finance_main_keyboard(), parse_mode="HTML")
