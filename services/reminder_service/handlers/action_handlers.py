from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from core.database.session import async_session_maker
from core.database.models import Reminder, utc_now
from services.reminder_service.states import ReminderState
from services.reminder_service.keyboards import (
    get_notification_keyboard,
    get_snooze_keyboard,
    get_cancel_keyboard,
    get_reminder_main_keyboard
)
from services.reminder_service.utils import (
    get_now_tashkent,
    parse_time_input,
    format_uzbek_datetime,
    to_utc,
    to_tashkent,
    TASHKENT_TZ
)

action_router = Router(name="reminder_action_router")

@action_router.callback_query(F.data.startswith("rem:done:"))
async def handle_reminder_done(callback: CallbackQuery):
    reminder_id = int(callback.data.split(":")[2])
    
    async with async_session_maker() as session:
        reminder = await session.get(Reminder, reminder_id)
        if not reminder or reminder.user_id != callback.from_user.id:
            await callback.answer("⚠️ Eslatma topilmadi yoki allaqachon o'chirilgan.", show_alert=True)
            return

        reminder.status = "completed"
        reminder.completed_at = utc_now()
        await session.commit()
        reminder_text = reminder.text or "Ovozli / Rasm eslatmasi"

    await callback.answer("✅ Bajarildi deb belgilandi!")

    updated_text = (
        "✅ <b>Bajarildi deb belgilandi!</b>\n\n"
        f"📌 <i>«{reminder_text}»</i>\n\n"
        "ℹ️ <i>Ushbu eslatma 7 kundan so'ng avtomatik o'chiriladi.\n"
        "Istalgan vaqtda 'Bajarilganlar tarixi' bo'limidan qo'lda ham o'chirishingiz mumkin.</i>"
    )
    try:
        await callback.message.edit_text(updated_text, parse_mode="HTML")
    except Exception:
        # Agar rasm yoki ovozli xabar bo'lsa caption ni o'zgartirish
        try:
            await callback.message.edit_caption(caption=updated_text, parse_mode="HTML")
        except Exception:
            pass

@action_router.callback_query(F.data.startswith("rem:snooze_menu:"))
async def handle_snooze_menu(callback: CallbackQuery):
    reminder_id = int(callback.data.split(":")[2])
    await callback.answer()
    
    prompt_text = (
        "⏰ <b>Qachon qayta eslatilsin?</b>\n\n"
        "Quyidagi vaqtlardan birini tanlang:"
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=get_snooze_keyboard(reminder_id))
    except Exception:
        await callback.message.answer(prompt_text, reply_markup=get_snooze_keyboard(reminder_id), parse_mode="HTML")

@action_router.callback_query(F.data.startswith("rem:back_to_notify:"))
async def handle_back_to_notify(callback: CallbackQuery):
    reminder_id = int(callback.data.split(":")[2])
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=get_notification_keyboard(reminder_id))
    except Exception:
        pass

@action_router.callback_query(F.data.startswith("rem:snooze:"))
async def handle_snooze_preset(callback: CallbackQuery):
    parts = callback.data.split(":")
    reminder_id = int(parts[2])
    option = parts[3]

    now = get_now_tashkent()
    target_dt = None

    if option == "15m":
        target_dt = now + timedelta(minutes=15)
    elif option == "1h":
        target_dt = now + timedelta(hours=1)
    elif option == "3h":
        target_dt = now + timedelta(hours=3)
    elif option == "tomorrow_morning":
        tomorrow = (now + timedelta(days=1)).date()
        target_dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 9, 0, tzinfo=TASHKENT_TZ)
    elif option == "tomorrow_same":
        target_dt = now + timedelta(days=1)

    if not target_dt:
        await callback.answer("Noto'g'ri tanlov!", show_alert=True)
        return

    utc_dt = to_utc(target_dt)

    async with async_session_maker() as session:
        reminder = await session.get(Reminder, reminder_id)
        if not reminder or reminder.user_id != callback.from_user.id:
            await callback.answer("⚠️ Eslatma topilmadi.", show_alert=True)
            return

        reminder.remind_at = utc_dt
        reminder.status = "pending"
        reminder.notified_at = None
        await session.commit()
        reminder_text = reminder.text or "Ovozli / Rasm eslatmasi"

    await callback.answer("⏰ Eslatma keyinga qoldirildi!")

    updated_text = (
        "⏰ <b>Eslatma keyinga qoldirildi:</b>\n\n"
        f"📌 <i>«{reminder_text}»</i>\n\n"
        f"📅 <b>Yangi eslatish vaqti:</b> {format_uzbek_datetime(target_dt)}\n"
        "🔔 <i>Vaqti kelganda yana bildirishnoma yuboriladi.</i>"
    )
    try:
        await callback.message.edit_text(updated_text, parse_mode="HTML")
    except Exception:
        try:
            await callback.message.edit_caption(caption=updated_text, parse_mode="HTML")
        except Exception:
            await callback.message.answer(updated_text, parse_mode="HTML")

@action_router.callback_query(F.data.startswith("rem:snooze_custom:"))
async def handle_snooze_custom_prompt(callback: CallbackQuery, state: FSMContext):
    reminder_id = int(callback.data.split(":")[2])
    await callback.answer()
    await state.set_state(ReminderState.waiting_for_custom_snooze)
    await state.update_data(snooze_reminder_id=reminder_id)

    text = (
        "✍️ <b>Qachon qayta eslatilishini xohlaysiz?</b>\n\n"
        "Vaqtni kiriting (Masalan:\n"
        "• <code>45 daqiqa</code> yoki <code>2 soat</code>\n"
        "• <code>17:30</code>\n"
        "• <code>ertaga 11:00</code>)"
    )
    await callback.message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

@action_router.message(ReminderState.waiting_for_custom_snooze, F.text)
async def process_custom_snooze_text(message: Message, state: FSMContext):
    target_dt = parse_time_input(message.text)
    if not target_dt:
        text = (
            "⚠️ <b>Vaqt formatini tushunmadim.</b>\n\n"
            "Iltimos, qaytadan yozing (Masalan: <code>30 daqiqa</code>, <code>2 soat</code>, <code>18:00</code>):"
        )
        await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
        return

    data = await state.get_data()
    reminder_id = data.get("snooze_reminder_id")
    utc_dt = to_utc(target_dt)

    async with async_session_maker() as session:
        reminder = await session.get(Reminder, reminder_id)
        if not reminder or reminder.user_id != message.from_user.id:
            await state.clear()
            await message.answer("⚠️ Eslatma topilmadi.", reply_markup=get_reminder_main_keyboard())
            return

        reminder.remind_at = utc_dt
        reminder.status = "pending"
        reminder.notified_at = None
        await session.commit()
        reminder_text = reminder.text or "Ovozli / Rasm eslatmasi"

    await state.clear()
    confirm_text = (
        "⏰ <b>Eslatma keyinga qoldirildi:</b>\n\n"
        f"📌 <i>«{reminder_text}»</i>\n\n"
        f"📅 <b>Yangi vaqt:</b> {format_uzbek_datetime(target_dt)}\n"
        "🔔 <i>Belgilangan vaqtda bot sizga eslatadi.</i>"
    )
    await message.answer(confirm_text, reply_markup=get_reminder_main_keyboard(), parse_mode="HTML")
