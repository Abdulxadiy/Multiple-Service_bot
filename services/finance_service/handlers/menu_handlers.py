from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func, delete

from core.database.session import async_session_maker
from core.database.models import User, Wallet, Transaction
from services.finance_service.states import FinanceState
from services.finance_service.keyboards import (
    get_finance_main_keyboard,
    get_cancel_keyboard,
    get_wallets_manage_keyboard,
    get_wallet_detail_keyboard
)
from services.finance_service.utils import (
    format_money,
    get_period_boundaries,
    parse_money_input
)

menu_router = Router(name="finance_menu_router")

async def ensure_default_wallets(session, user_id: int, username: str | None) -> list[Wallet]:
    """Foydalanuvchi birinchi marta kirganda standart hamyonlarni (Karta, Naqd pul) yaratish"""
    user = await session.get(User, user_id)
    if not user:
        user = User(telegram_id=user_id, username=username)
        session.add(user)
        await session.flush()

    res = await session.execute(
        select(Wallet).where(Wallet.user_id == user_id).order_by(Wallet.id.asc())
    )
    wallets = res.scalars().all()
    if not wallets:
        card = Wallet(user_id=user_id, name="💳 Karta", balance=0, is_default=True)
        cash = Wallet(user_id=user_id, name="💵 Naqd pul", balance=0, is_default=False)
        session.add_all([card, cash])
        await session.commit()
        wallets = [card, cash]
    return wallets

@menu_router.callback_query(F.data == "svc:finance")
async def handle_finance_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        wallets = await ensure_default_wallets(session, user_id, callback.from_user.username)
        total_balance = sum(w.balance for w in wallets)

        # Shu oylik kirim va chiqim
        start_month, end_month = get_period_boundaries("month")
        inc_res = await session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(
                Transaction.user_id == user_id,
                Transaction.type == "income",
                Transaction.created_at >= start_month,
                Transaction.created_at <= end_month
            )
        )
        total_income = inc_res.scalar() or 0

        exp_res = await session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(
                Transaction.user_id == user_id,
                Transaction.type == "expense",
                Transaction.created_at >= start_month,
                Transaction.created_at <= end_month
            )
        )
        total_expense = exp_res.scalar() or 0

    wallets_text = " | ".join(f"{w.name}: <b>{format_money(w.balance)}</b>" for w in wallets)

    text = (
        "💰 <b>Mening Hamyonim (Shaxsiy Moliya)</b>\n\n"
        f"💵 <b>Umumiy Balans:</b> <code>{format_money(total_balance)}</code>\n"
        f"📂 {wallets_text}\n\n"
        "📊 <b>Shu oylik hisob-kitob:</b>\n"
        f"🟢 Kirim: <b>+{format_money(total_income)}</b>\n"
        f"🔴 Chiqim: <b>-{format_money(total_expense)}</b>\n"
        f"📈 Sof farq: <b>{format_money(total_income - total_expense)}</b>\n\n"
        "💡 <i>Tezkor xarajat yoki daromad kiritish uchun botga shunchaki yozing:</i>\n"
        "• <code>35000 tushlik</code>\n"
        "• <code>+2000000 oylik</code>\n"
        "• <code>50k taxi</code>\n\n"
        "Quyidagi menyulardan birini tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=get_finance_main_keyboard(), parse_mode="HTML")

@menu_router.callback_query(F.data == "fin:cancel")
async def handle_finance_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Bekor qilindi")
    await handle_finance_home(callback, state)

@menu_router.callback_query(F.data == "fin:wallets")
async def handle_wallets_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        wallets = await ensure_default_wallets(session, user_id, callback.from_user.username)
        total_balance = sum(w.balance for w in wallets)

    text = (
        "💳 <b>Sizning Hamyonlaringiz:</b>\n\n"
        f"💵 <b>Jami mablag':</b> <code>{format_money(total_balance)}</code>\n\n"
        "Balansni yangilash yoki o'chirish uchun kerakli hamyonni tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=get_wallets_manage_keyboard(wallets), parse_mode="HTML")

@menu_router.callback_query(F.data.startswith("fin_w_edit:"))
async def handle_wallet_detail(callback: CallbackQuery):
    wallet_id = int(callback.data.split(":")[1])
    await callback.answer()

    async with async_session_maker() as session:
        wallet = await session.get(Wallet, wallet_id)
        if not wallet or wallet.user_id != callback.from_user.id:
            await callback.answer("Hamyon topilmadi.", show_alert=True)
            return

        text = (
            f"💳 <b>Hamyon tafsilotlari:</b>\n\n"
            f"📌 <b>Nomi:</b> {wallet.name}\n"
            f"💰 <b>Joriy balans:</b> <code>{format_money(wallet.balance)}</code>\n\n"
            "Kerakli amalni tanlang:"
        )
        await callback.message.edit_text(text, reply_markup=get_wallet_detail_keyboard(wallet.id), parse_mode="HTML")

@menu_router.callback_query(F.data.startswith("fin_w_setbal:"))
async def handle_set_balance_prompt(callback: CallbackQuery, state: FSMContext):
    wallet_id = int(callback.data.split(":")[1])
    await callback.answer()
    await state.set_state(FinanceState.waiting_for_set_balance)
    await state.update_data(target_wallet_id=wallet_id)

    text = (
        "💰 <b>Hamyondagi yangi summani kiriting:</b>\n\n"
        "Masalan: <code>500000</code> yoki <code>1.5 mln</code> yoki <code>0</code>:"
    )
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

@menu_router.message(FinanceState.waiting_for_set_balance, F.text)
async def process_set_balance(message: Message, state: FSMContext):
    amount, _, _ = parse_money_input(message.text)
    if amount is None or amount < 0:
        await message.answer(
            "⚠️ Noto'g'ri summa kiritildi. Qaytadan yozing (masalan: <code>350000</code>):",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    wallet_id = data.get("target_wallet_id")

    async with async_session_maker() as session:
        wallet = await session.get(Wallet, wallet_id)
        if wallet and wallet.user_id == message.from_user.id:
            wallet.balance = amount
            await session.commit()
            wallet_name = wallet.name

    await state.clear()
    await message.answer(
        f"✅ <b>{wallet_name}</b> balansi yangilandi: <code>{format_money(amount)}</code>",
        parse_mode="HTML"
    )

@menu_router.callback_query(F.data.startswith("fin_w_del:"))
async def handle_wallet_delete(callback: CallbackQuery, state: FSMContext):
    wallet_id = int(callback.data.split(":")[1])

    async with async_session_maker() as session:
        wallets_count = await session.scalar(
            select(func.count(Wallet.id)).where(Wallet.user_id == callback.from_user.id)
        )
        if wallets_count <= 1:
            await callback.answer("⚠️ Yagona qolgan hamyonni o'chirib bo'lmaydi!", show_alert=True)
            return

        wallet = await session.get(Wallet, wallet_id)
        if wallet and wallet.user_id == callback.from_user.id:
            await session.delete(wallet)
            await session.commit()

    await callback.answer("🗑 Hamyon o'chirildi!", show_alert=False)
    await handle_wallets_list(callback, state)

@menu_router.callback_query(F.data == "fin_w:new")
async def handle_wallet_new_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(FinanceState.waiting_for_wallet_name)
    text = (
        "➕ <b>Yangi hamyon nomini kiriting:</b>\n\n"
        "Masalan: <code>Jamg'arma</code> yoki <code>TBC Bank</code> yoki <code>Dollardagi hisob</code>:"
    )
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

@menu_router.message(FinanceState.waiting_for_wallet_name, F.text)
async def process_wallet_new_name(message: Message, state: FSMContext):
    name = message.text.strip()[:40]
    user_id = message.from_user.id

    async with async_session_maker() as session:
        wallet = Wallet(user_id=user_id, name=f"💳 {name}", balance=0)
        session.add(wallet)
        await session.commit()

    await state.clear()
    await message.answer(
        f"✅ <b>Yangi hamyon qo'shildi:</b> {wallet.name}\n"
        "Balansini sozlash uchun Hamyonlar bo'limidan foydalaning.",
        parse_mode="HTML"
    )
