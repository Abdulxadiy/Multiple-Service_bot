from datetime import timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, delete

from core.database.session import async_session_maker
from core.database.models import Reminder, utc_now
from services.reminder_service.keyboards import (
    get_active_reminders_keyboard,
    get_reminder_detail_keyboard,
    get_history_keyboard,
    get_reminder_main_keyboard
)
from services.reminder_service.utils import (
    format_uzbek_datetime,
    to_tashkent
)

list_router = Router(name="reminder_list_router")

@list_router.callback_query(F.data == "rem:active")
async def handle_list_active(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        query = (
            select(Reminder)
            .where(Reminder.user_id == user_id, Reminder.status.in_(["pending", "notified"]))
            .order_by(Reminder.remind_at.asc())
        )
        result = await session.execute(query)
        reminders = result.scalars().all()

    if not reminders:
        text = (
            "📌 <b>Faol eslatmalar:</b>\n\n"
            "Sizda hozircha kutilayotgan faol eslatmalar yo'q.\n"
            "Yangi eslatma yaratish uchun quyidagi tugmani bosing:"
        )
        await callback.message.edit_text(text, reply_markup=get_active_reminders_keyboard([]), parse_mode="HTML")
        return

    text = f"📌 <b>Faol eslatmalaringiz (jami {len(reminders)} ta):</b>\n\n"
    for idx, r in enumerate(reminders[:10], start=1):
        content = (r.text or "Ovozli / Rasm eslatma")[:45]
        time_str = format_uzbek_datetime(r.remind_at)
        text += f"<b>{idx}.</b> ⏰ {time_str}\n    «{content}»\n\n"

    text += "<i>Batafsil ko'rish yoki boshqarish uchun pastdagi tugmalardan tanlang:</i>"
    await callback.message.edit_text(text, reply_markup=get_active_reminders_keyboard(reminders), parse_mode="HTML")

@list_router.callback_query(F.data.startswith("rem:view:"))
async def handle_view_reminder(callback: CallbackQuery):
    reminder_id = int(callback.data.split(":")[2])
    await callback.answer()

    async with async_session_maker() as session:
        reminder = await session.get(Reminder, reminder_id)
        if not reminder or reminder.user_id != callback.from_user.id:
            await callback.answer("⚠️ Eslatma topilmadi.", show_alert=True)
            return

        repeat_labels = {
            "none": "🚫 Bir martalik",
            "daily": "🔄 Har kuni",
            "weekly": "📆 Har hafta",
            "monthly": "🗓 Har oy"
        }
        repeat_name = repeat_labels.get(reminder.repeat_type, "Bir martalik")
        status_labels = {
            "pending": "⏳ Kutilmoqda",
            "notified": "🔔 Bildirishnoma yuborilgan",
            "completed": "✅ Bajarilgan"
        }
        status_name = status_labels.get(reminder.status, reminder.status)

        time_str = format_uzbek_datetime(reminder.remind_at)
        text = (
            "📌 <b>Eslatma tafsilotlari:</b>\n\n"
            f"📝 <b>Matn:</b> {reminder.text or 'Ovozli / Rasm'}\n"
            f"⏰ <b>Vaqti:</b> {time_str}\n"
            f"🔄 <b>Takrorlanish:</b> {repeat_name}\n"
            f"📊 <b>Holati:</b> {status_name}\n"
        )
        is_completed = (reminder.status == "completed")
        await callback.message.edit_text(
            text,
            reply_markup=get_reminder_detail_keyboard(reminder.id, is_completed),
            parse_mode="HTML"
        )

@list_router.callback_query(F.data.startswith("rem:delete:"))
async def handle_delete_reminder(callback: CallbackQuery):
    reminder_id = int(callback.data.split(":")[2])

    async with async_session_maker() as session:
        reminder = await session.get(Reminder, reminder_id)
        if reminder and reminder.user_id == callback.from_user.id:
            await session.delete(reminder)
            await session.commit()

    await callback.answer("🗑 Eslatma o'chirildi!", show_alert=False)
    # Faol eslatmalarga qaytish
    await handle_list_active(callback)

@list_router.callback_query(F.data == "rem:history")
async def handle_list_history(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        query = (
            select(Reminder)
            .where(Reminder.user_id == user_id, Reminder.status == "completed")
            .order_by(Reminder.completed_at.desc())
        )
        result = await session.execute(query)
        completed = result.scalars().all()

    if not completed:
        text = (
            "✅ <b>Bajarilganlar tarixi:</b>\n\n"
            "Sizda hali bajarilgan eslatmalar mavjud emas.\n"
            "Eslatma kelganda 'Bajarildi' tugmasini bossangiz, shu yerda 7 kun davomida saqlanadi."
        )
        await callback.message.edit_text(text, reply_markup=get_history_keyboard(has_items=False), parse_mode="HTML")
        return

    now = utc_now()
    text = (
        f"✅ <b>Bajarilgan eslatmalar (jami {len(completed)} ta):</b>\n\n"
        "<i>Eslatma: Bajarilgan eslatmalar 7 kundan so'ng avtomatik o'chiriladi.</i>\n\n"
    )

    for idx, r in enumerate(completed[:10], start=1):
        content = (r.text or "Ovozli / Rasm eslatma")[:40]
        comp_time = format_uzbek_datetime(r.completed_at) if r.completed_at else "Yaqinda"
        # Qolgan kunlar
        days_left = 7
        if r.completed_at:
            elapsed = (now - r.completed_at).days
            days_left = max(1, 7 - elapsed)
        text += f"<b>{idx}.</b> ✅ «{content}»\n    Bajarildi: {comp_time} <i>({days_left} kun qoldi)</i>\n\n"

    await callback.message.edit_text(text, reply_markup=get_history_keyboard(has_items=True), parse_mode="HTML")

@list_router.callback_query(F.data == "rem:clear_history")
async def handle_clear_history(callback: CallbackQuery):
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        await session.execute(
            delete(Reminder).where(Reminder.user_id == user_id, Reminder.status == "completed")
        )
        await session.commit()

    await callback.answer("🗑 Bajarilgan barcha eslatmalar tozalandi!", show_alert=True)
    await handle_list_history(callback)
