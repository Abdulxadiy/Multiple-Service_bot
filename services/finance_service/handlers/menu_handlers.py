from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func, delete

from core.database.session import async_session_maker
from core.database.models import User, Wallet, Transaction, FinanceCategory
from services.finance_service.states import FinanceState
from services.finance_service.keyboards import (
    get_finance_main_keyboard,
    get_cancel_keyboard,
    get_wallets_manage_keyboard,
    get_wallet_detail_keyboard,
    get_categories_manage_menu_keyboard,
    get_category_list_manage_keyboard,
    get_category_detail_keyboard,
    get_choose_cat_type_keyboard
)
from services.finance_service.utils import (
    format_money,
    get_period_boundaries,
    parse_money_input,
    get_user_finance_categories,
    sanitize_category_name
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
        "💡 <b>Tezkor kiritish usullari:</b>\n"
        "• ✍️ <b>Matn orqali:</b> <code>35000 tushlik</code> yoki <code>+2000000 oylik</code>\n"
        "• 🎙 <b>Ovoz orqali:</b> Ovozli xabar yuboring (masalan: <i>«Tushlikka 35 ming ketdi»</i>)!\n\n"
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

# ==================== KATEGORIYALARNI BOSHQARISH ====================

@menu_router.callback_query(F.data == "fin:categories")
async def handle_categories_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()

    text = (
        "🏷 <b>Kategoriyalarni boshqarish:</b>\n\n"
        "Bu bo'limda siz o'zingizning xarajat va daromad kategoriyalaringizni sozlashingiz, "
        "nomini tahrirlashingiz, o'chirishingiz yoki yangilarini qo'shishingiz mumkin.\n\n"
        "Kerakli bo'limni tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=get_categories_manage_menu_keyboard(), parse_mode="HTML")

@menu_router.callback_query(F.data.startswith("fin_cat_list:"))
async def handle_category_list_by_type(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    cat_type = callback.data.split(":")[1]
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        categories = await get_user_finance_categories(session, user_id, cat_type)

    type_title = "🔴 Chiqim (Xarajat)" if cat_type == "expense" else "🟢 Kirim (Daromad)"
    text = (
        f"🏷 <b>{type_title} kategoriyalari:</b>\n\n"
        "Tahrirlash yoki o'chirish uchun kerakli kategoriyani bosing:"
    )
    await callback.message.edit_text(text, reply_markup=get_category_list_manage_keyboard(categories, cat_type), parse_mode="HTML")

@menu_router.callback_query(F.data.startswith("fin_cat_view:"))
async def handle_category_detail_view(callback: CallbackQuery):
    cat_id = int(callback.data.split(":")[1])
    await callback.answer()

    async with async_session_maker() as session:
        cat = await session.get(FinanceCategory, cat_id)
        if not cat or cat.user_id != callback.from_user.id:
            await callback.answer("Kategoriya topilmadi.", show_alert=True)
            return

        type_str = "🟢 Kirim" if cat.type == "income" else "🔴 Chiqim"
        text = (
            f"🏷 <b>Kategoriya ma'lumotlari:</b>\n\n"
            f"📌 <b>Nomi:</b> {cat.name}\n"
            f"📊 <b>Turi:</b> {type_str}\n\n"
            "Kerakli amalni tanlang:"
        )
        await callback.message.edit_text(text, reply_markup=get_category_detail_keyboard(cat.id, cat.type), parse_mode="HTML")

@menu_router.callback_query(F.data.startswith("fin_cat_rename:"))
async def handle_category_rename_prompt(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(":")[1])
    await callback.answer()

    async with async_session_maker() as session:
        cat = await session.get(FinanceCategory, cat_id)
        if not cat or cat.user_id != callback.from_user.id:
            await callback.answer("Kategoriya topilmadi.", show_alert=True)
            return
        cat_name = cat.name
        cat_type = cat.type

    await state.set_state(FinanceState.waiting_for_category_rename)
    await state.update_data(rename_cat_id=cat_id, rename_cat_type=cat_type)

    text = (
        f"✏️ <b>Kategoriya nomini o'zgartirish:</b>\n\n"
        f"Joriy nom: <b>{cat_name}</b>\n\n"
        "Yangi nomni kiriting (masalan: <i>Restoran va kafelar</i>):"
    )
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard("fin:categories"), parse_mode="HTML")

@menu_router.message(FinanceState.waiting_for_category_rename, F.text)
async def process_category_rename(message: Message, state: FSMContext):
    data = await state.get_data()
    cat_id = data.get("rename_cat_id")
    cat_type = data.get("rename_cat_type", "expense")
    new_name = sanitize_category_name(message.text)

    async with async_session_maker() as session:
        cat = await session.get(FinanceCategory, cat_id)
        if cat and cat.user_id == message.from_user.id:
            cat.name = new_name
            await session.commit()
            categories = await get_user_finance_categories(session, message.from_user.id, cat_type)
        else:
            categories = []

    await state.clear()
    await message.answer(
        f"✅ Kategoriya nomi <b>«{new_name}»</b> ga o'zgartirildi!",
        reply_markup=get_category_list_manage_keyboard(categories, cat_type),
        parse_mode="HTML"
    )

@menu_router.callback_query(F.data.startswith("fin_cat_del:"))
async def handle_category_delete(callback: CallbackQuery):
    cat_id = int(callback.data.split(":")[1])

    async with async_session_maker() as session:
        cat = await session.get(FinanceCategory, cat_id)
        if not cat or cat.user_id != callback.from_user.id:
            await callback.answer("Kategoriya topilmadi.", show_alert=True)
            return

        cat_type = cat.type
        cat_name = cat.name
        await session.delete(cat)
        await session.commit()

        categories = await get_user_finance_categories(session, callback.from_user.id, cat_type)

    await callback.answer(f"🗑 «{cat_name}» o'chirildi!", show_alert=False)
    type_title = "🔴 Chiqim (Xarajat)" if cat_type == "expense" else "🟢 Kirim (Daromad)"
    text = (
        f"🏷 <b>{type_title} kategoriyalari:</b>\n\n"
        "Tahrirlash yoki o'chirish uchun kerakli kategoriyani bosing:"
    )
    await callback.message.edit_text(text, reply_markup=get_category_list_manage_keyboard(categories, cat_type), parse_mode="HTML")

@menu_router.callback_query(F.data == "fin_cat_add_prompt")
async def handle_category_add_prompt(callback: CallbackQuery):
    await callback.answer()
    text = (
        "➕ <b>Yangi kategoriya qo'shish:</b>\n\n"
        "Kategoriya qaysi tur uchun bo'lishini tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=get_choose_cat_type_keyboard(), parse_mode="HTML")

@menu_router.callback_query(F.data.startswith("fin_cat_add:"))
async def handle_category_add_by_type(callback: CallbackQuery, state: FSMContext):
    cat_type = callback.data.split(":")[1]
    await callback.answer()
    await state.set_state(FinanceState.waiting_for_new_cat_manual_name)
    await state.update_data(manual_cat_type=cat_type)

    type_title = "Kirim" if cat_type == "income" else "Chiqim"
    text = (
        f"➕ <b>Yangi {type_title} kategoriyasi nomini kiriting:</b>\n\n"
        "Masalan: <i>Kutubxona</i> yoki <i>Kredit to'lovi</i>:"
    )
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard("fin:categories"), parse_mode="HTML")

@menu_router.message(FinanceState.waiting_for_new_cat_manual_name, F.text)
async def process_new_cat_manual_name(message: Message, state: FSMContext):
    data = await state.get_data()
    cat_type = data.get("manual_cat_type", "expense")
    cat_name = sanitize_category_name(message.text)
    user_id = message.from_user.id

    async with async_session_maker() as session:
        new_cat = FinanceCategory(user_id=user_id, type=cat_type, name=cat_name)
        session.add(new_cat)
        await session.commit()
        categories = await get_user_finance_categories(session, user_id, cat_type)

    await state.clear()
    type_title = "Kirim" if cat_type == "income" else "Chiqim"
    await message.answer(
        f"✅ Yangi {type_title} kategoriyasi qo'shildi: <b>{cat_name}</b>",
        reply_markup=get_category_list_manage_keyboard(categories, cat_type),
        parse_mode="HTML"
    )

