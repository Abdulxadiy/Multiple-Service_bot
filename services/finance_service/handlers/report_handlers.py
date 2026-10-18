from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, func, desc

from core.database.session import async_session_maker
from core.database.models import Transaction
from services.finance_service.keyboards import (
    get_reports_menu_keyboard,
    get_finance_main_keyboard
)
from services.finance_service.utils import (
    format_money,
    get_period_boundaries
)
from services.reminder_service.utils import format_uzbek_datetime

report_router = Router(name="finance_report_router")

@report_router.callback_query(F.data == "fin:reports")
async def handle_reports_menu(callback: CallbackQuery):
    await callback.answer()
    text = (
        "📊 <b>Moliya Hisobotlari va Tahlil:</b>\n\n"
        "Qaysi davr bo'yicha hisobotni ko'rmoqchisiz?"
    )
    await callback.message.edit_text(text, reply_markup=get_reports_menu_keyboard(), parse_mode="HTML")

@report_router.callback_query(F.data.startswith("fin_rep:"))
async def handle_period_report(callback: CallbackQuery):
    period = callback.data.split(":")[1]
    await callback.answer()

    period_names = {
        "today": "📅 Bugungi hisobot",
        "week": "📆 Haftalik hisobot (Dushanbadan buyon)",
        "month": "🗓 Oylik hisobot (Shu oy boshi)"
    }
    period_title = period_names.get(period, "Hisobot")
    start_dt, end_dt = get_period_boundaries(period)
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        # Kirim summasi
        inc_res = await session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(
                Transaction.user_id == user_id,
                Transaction.type == "income",
                Transaction.created_at >= start_dt,
                Transaction.created_at <= end_dt
            )
        )
        total_income = inc_res.scalar() or 0

        # Chiqim summasi
        exp_res = await session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(
                Transaction.user_id == user_id,
                Transaction.type == "expense",
                Transaction.created_at >= start_dt,
                Transaction.created_at <= end_dt
            )
        )
        total_expense = exp_res.scalar() or 0

        # Kategoriyalar bo'yicha chiqimlar tahlili
        cat_res = await session.execute(
            select(Transaction.category, func.sum(Transaction.amount).label("cat_total"))
            .where(
                Transaction.user_id == user_id,
                Transaction.type == "expense",
                Transaction.created_at >= start_dt,
                Transaction.created_at <= end_dt
            )
            .group_by(Transaction.category)
            .order_by(desc("cat_total"))
        )
        categories = cat_res.all()

    net = total_income - total_expense
    net_sign = "+" if net >= 0 else "-"

    text = (
        f"<b>{period_title}</b>\n\n"
        f"🟢 <b>Jami Kirim:</b> +{format_money(total_income)}\n"
        f"🔴 <b>Jami Chiqim:</b> -{format_money(total_expense)}\n"
        f"💰 <b>Qoldiq / Farq:</b> <code>{net_sign}{format_money(abs(net))}</code>\n\n"
    )

    if categories and total_expense > 0:
        text += "📈 <b>Chiqimlar tarkibi (Kategoriyalar):</b>\n"
        for idx, (cat_name, cat_amount) in enumerate(categories, start=1):
            percent = int((cat_amount / total_expense) * 100)
            text += f"<b>{idx}.</b> {cat_name}: <b>{percent}%</b> (<i>{format_money(cat_amount)}</i>)\n"
    elif total_expense == 0 and total_income == 0:
        text += "<i>Ushbu davrda hali hech qanday amal bajarilmagan.</i>\n"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Hisobotlar menyusi", callback_data="fin:reports")],
        [InlineKeyboardButton(text="🏠 Moliya bosh menyusi", callback_data="svc:finance")]
    ])
    await callback.message.edit_text(text, reply_markup=back_kb, parse_mode="HTML")

@report_router.callback_query(F.data == "fin:history")
async def handle_transaction_history(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        res = await session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(10)
        )
        transactions = res.scalars().all()

    if not transactions:
        text = (
            "📜 <b>Oxirgi amallar tarixi:</b>\n\n"
            "Sizda hali birorta ham kiritilgan kirim yoki chiqim mavjud emas."
        )
    else:
        text = "📜 <b>Oxirgi 10 ta amal:</b>\n\n"
        for t in transactions:
            icon = "🟢" if t.type == "income" else "🔴"
            sign = "+" if t.type == "income" else "-"
            date_str = format_uzbek_datetime(t.created_at)
            note_str = f" - <i>{t.note}</i>" if t.note else ""
            text += f"{icon} <b>{sign}{format_money(t.amount)}</b> | {t.category}{note_str}\n   🗓 {date_str}\n\n"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Moliya bosh menyusi", callback_data="svc:finance")]
    ])
    await callback.message.edit_text(text, reply_markup=back_kb, parse_mode="HTML")
