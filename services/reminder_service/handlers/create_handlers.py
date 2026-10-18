import os
import tempfile
from datetime import timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from core.database.session import async_session_maker
from core.database.models import Reminder, User
from services.reminder_service.states import ReminderState
from services.reminder_service.keyboards import (
    get_reminder_main_keyboard,
    get_cancel_keyboard,
    get_time_presets_keyboard,
    get_repeat_keyboard,
    get_voice_confirmation_keyboard
)
from services.reminder_service.utils import (
    get_now_tashkent,
    parse_time_input,
    format_uzbek_datetime,
    to_utc,
    TASHKENT_TZ
)
from services.reminder_service.stt import transcribe_voice

create_router = Router(name="reminder_create_router")

@create_router.callback_query(F.data == "svc:reminders")
async def handle_reminder_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    text = (
        "📝 <b>Eslatmalar va Bildirishnomalar Xizmati</b>\n\n"
        "Kerakli ishlaringiz, to'lovlar yoki uchrashuvlarni rejalashtiring.\n"
        "Belgilangan vaqtda bot sizga eslatma yuboradi.\n\n"
        "💡 <i>Uzun eslatmalarni ovozli xabar (audio) qilib yuborishingiz ham mumkin!</i>\n\n"
        "Quyidagi menyulardan birini tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=get_reminder_main_keyboard(), parse_mode="HTML")

@create_router.callback_query(F.data == "rem:cancel")
async def handle_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Bekor qilindi")
    text = (
        "📝 <b>Eslatmalar va Bildirishnomalar Xizmati</b>\n\n"
        "Quyidagi menyulardan birini tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=get_reminder_main_keyboard(), parse_mode="HTML")

@create_router.callback_query(F.data == "rem:new")
async def handle_new_reminder(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(ReminderState.waiting_for_content)
    text = (
        "✍️ <b>Eslatmani yozing yoki ovozli xabar yuboring:</b>\n\n"
        "🎙 <b>Ovoz bilan yozish:</b> Uzun eslatmalarni erinmasdan ovozli xabar orqali yuboring. "
        "Bot uni o'zbekcha aniq matnga o'girib, sizdan tasdiqlashni so'raydi."
    )
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

# 1. Matn qabul qilish
@create_router.message(ReminderState.waiting_for_content, F.text)
async def process_content_text(message: Message, state: FSMContext):
    await state.update_data(
        content_text=message.text,
        media_type="text",
        media_file_id=None
    )
    await state.set_state(ReminderState.waiting_for_time)
    text = (
        f"📌 <b>Eslatma matni qabul qilindi:</b>\n"
        f"<i>«{message.text[:120]}»</i>\n\n"
        f"⏰ <b>Qachon eslatilsin?</b>\n"
        f"Quyidagi tayyor variantlardan birini tanlang yoki o'zingiz yozing:"
    )
    await message.answer(text, reply_markup=get_time_presets_keyboard(), parse_mode="HTML")

# 2. Ovozli xabarni qabul qilish va matnga o'girish (STT)
@create_router.message(ReminderState.waiting_for_content, F.voice)
async def process_content_voice(message: Message, state: FSMContext):
    status_msg = await message.answer(
        "⏳ <i>Ovozingiz tinglanmoqda va o'zbekcha matnga o'girilmoqda...</i>",
        parse_mode="HTML"
    )

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_ogg:
        temp_ogg_path = temp_ogg.name

    try:
        # Ovozli faylni yuklab olish
        await message.bot.download(message.voice, destination=temp_ogg_path)

        # Ovozni matnga o'girish
        transcribed_text = await transcribe_voice(temp_ogg_path)
    finally:
        if os.path.exists(temp_ogg_path):
            try:
                os.remove(temp_ogg_path)
            except OSError:
                pass

    if not transcribed_text:
        fail_text = (
            "⚠️ <b>Ovozingizni aniqlab bo'lmadi.</b>\n\n"
            "Iltimos, shovqinsizroq joyda biroz balandroq va aniqroq gapirib ko'ring "
            "yoki matn ko'rinishida yozing:"
        )
        retry_kb = [
            [get_cancel_keyboard().inline_keyboard[0][0]]
        ]
        from aiogram.types import InlineKeyboardMarkup
        await status_msg.edit_text(fail_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=retry_kb), parse_mode="HTML")
        return

    # Muvaffaqiyatli o'girildi -> foydalanuvchidan tasdiqlashni so'raymiz
    await state.update_data(
        content_text=transcribed_text,
        media_type="text",
        media_file_id=None
    )
    await state.set_state(ReminderState.waiting_for_voice_confirm)

    confirm_text = (
        "🎙 <b>Ovozingiz matnga o'girildi:</b>\n\n"
        f"«<b>{transcribed_text}</b>»\n\n"
        "❓ <b>Matn to'g'rimi?</b>"
    )
    await status_msg.edit_text(confirm_text, reply_markup=get_voice_confirmation_keyboard(), parse_mode="HTML")

# 3. Ovozli matnni tasdiqlash handlerlari
@create_router.callback_query(ReminderState.waiting_for_voice_confirm, F.data == "voice_confirm:yes")
async def handle_voice_confirm_yes(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Matn tasdiqlandi!")
    await state.set_state(ReminderState.waiting_for_time)

    data = await state.get_data()
    text = (
        f"📌 <b>Eslatma matni:</b>\n"
        f"«<i>{data.get('content_text', '')}</i>»\n\n"
        f"⏰ <b>Qachon eslatilsin?</b>\n"
        f"Quyidagi tayyor variantlardan birini tanlang yoki o'zingiz yozing:"
    )
    await callback.message.edit_text(text, reply_markup=get_time_presets_keyboard(), parse_mode="HTML")

@create_router.callback_query(ReminderState.waiting_for_voice_confirm, F.data == "voice_confirm:edit")
async def handle_voice_confirm_edit(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(ReminderState.waiting_for_edit_content)
    text = (
        "✍️ <b>Matnni to'g'rilab yuboring:</b>\n\n"
        "O'zingiz xohlagan aniq matnni xabar qilib yozing:"
    )
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

@create_router.message(ReminderState.waiting_for_edit_content, F.text)
async def process_edited_content_text(message: Message, state: FSMContext):
    await state.update_data(
        content_text=message.text,
        media_type="text",
        media_file_id=None
    )
    await state.set_state(ReminderState.waiting_for_time)
    text = (
        f"📌 <b>Eslatma matni yangilandi:</b>\n"
        f"<i>«{message.text[:120]}»</i>\n\n"
        f"⏰ <b>Qachon eslatilsin?</b>\n"
        f"Quyidagi tayyor variantlardan birini tanlang yoki o'zingiz yozing:"
    )
    await message.answer(text, reply_markup=get_time_presets_keyboard(), parse_mode="HTML")

@create_router.callback_query(ReminderState.waiting_for_voice_confirm, F.data == "voice_confirm:retry")
async def handle_voice_confirm_retry(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(ReminderState.waiting_for_content)
    text = (
        "🎙 <b>Yangi ovozli xabarni yuboring:</b>\n\n"
        "Ovoz bilan aniq gapirib yuboring, bot uni qaytadan matnga o'giradi."
    )
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

# 4. Rasm qabul qilish
@create_router.message(ReminderState.waiting_for_content, F.photo)
async def process_content_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    await state.update_data(
        content_text=message.caption or "🖼 Rasm eslatmasi",
        media_type="photo",
        media_file_id=photo.file_id
    )
    await state.set_state(ReminderState.waiting_for_time)
    text = (
        "🖼 <b>Rasm qabul qilindi!</b>\n\n"
        "⏰ <b>Qachon eslatilsin?</b>\n"
        "Quyidagi tayyor variantlardan birini tanlang yoki o'zingiz yozing:"
    )
    await message.answer(text, reply_markup=get_time_presets_keyboard(), parse_mode="HTML")

# 5. Vaqt tanlash (Presetlar)
@create_router.callback_query(ReminderState.waiting_for_time, F.data.startswith("rem_time:"))
async def process_time_preset(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    now = get_now_tashkent()
    target_dt = None

    if action == "15m":
        target_dt = now + timedelta(minutes=15)
    elif action == "30m":
        target_dt = now + timedelta(minutes=30)
    elif action == "1h":
        target_dt = now + timedelta(hours=1)
    elif action == "3h":
        target_dt = now + timedelta(hours=3)
    elif action == "tomorrow_morning":
        tomorrow = (now + timedelta(days=1)).date()
        from datetime import datetime
        target_dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 9, 0, tzinfo=TASHKENT_TZ)
    elif action == "tomorrow_same":
        target_dt = now + timedelta(days=1)
    elif action == "custom":
        await callback.answer()
        text = (
            "✍️ <b>Vaqtni kiriting:</b>\n\n"
            "Misollar:\n"
            "• <code>14:30</code> (bugun yoki ertaga)\n"
            "• <code>ertaga 09:00</code>\n"
            "• <code>45 daqiqa</code> yoki <code>2 soat</code>\n"
            "• <code>25.10 18:00</code> (sana va soat)"
        )
        await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
        return

    if target_dt:
        await callback.answer()
        await state.update_data(remind_at_iso=target_dt.isoformat())
        await state.set_state(ReminderState.waiting_for_repeat)
        text = (
            f"📅 <b>Belgilangan vaqt:</b> {format_uzbek_datetime(target_dt)}\n\n"
            f"🔄 <b>Eslatma takrorlansinmi?</b>"
        )
        await callback.message.edit_text(text, reply_markup=get_repeat_keyboard(), parse_mode="HTML")

# 6. Qo'lda vaqt yozish
@create_router.message(ReminderState.waiting_for_time, F.text)
async def process_custom_time_text(message: Message, state: FSMContext):
    target_dt = parse_time_input(message.text)
    if not target_dt:
        text = (
            "⚠️ <b>Vaqt formatini tushunmadim.</b>\n\n"
            "Iltimos, vaqtni quyidagicha yozing:\n"
            "• <code>14:30</code> (soat va daqiqa)\n"
            "• <code>ertaga 09:00</code>\n"
            "• <code>20 daqiqa</code> yoki <code>2 soat</code>\n"
            "• <code>25.10 15:00</code>\n\n"
            "Qaytadan urinib ko'ring yoki bekor qiling:"
        )
        await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
        return

    await state.update_data(remind_at_iso=target_dt.isoformat())
    await state.set_state(ReminderState.waiting_for_repeat)
    text = (
        f"📅 <b>Belgilangan vaqt:</b> {format_uzbek_datetime(target_dt)}\n\n"
        f"🔄 <b>Eslatma takrorlansinmi?</b>"
    )
    await message.answer(text, reply_markup=get_repeat_keyboard(), parse_mode="HTML")

# 7. Takroriylikni tanlash va bazaga saqlash
@create_router.callback_query(ReminderState.waiting_for_repeat, F.data.startswith("rem_repeat:"))
async def process_repeat_selection(callback: CallbackQuery, state: FSMContext):
    repeat_type = callback.data.split(":")[1]
    repeat_labels = {
        "none": "🚫 Bir martalik",
        "daily": "🔄 Har kuni (shu vaqtda)",
        "weekly": "📆 Har hafta",
        "monthly": "🗓 Har oy"
    }
    repeat_name = repeat_labels.get(repeat_type, "Bir martalik")

    data = await state.get_data()
    from datetime import datetime
    target_dt = datetime.fromisoformat(data["remind_at_iso"])
    utc_dt = to_utc(target_dt)

    user_id = callback.from_user.id

    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if not user:
            user = User(
                telegram_id=user_id,
                username=callback.from_user.username
            )
            session.add(user)
            await session.flush()

        reminder = Reminder(
            user_id=user_id,
            text=data.get("content_text"),
            media_type=data.get("media_type", "text"),
            media_file_id=data.get("media_file_id"),
            remind_at=utc_dt,
            repeat_type=repeat_type,
            status="pending"
        )
        session.add(reminder)
        await session.commit()

    await state.clear()
    await callback.answer("✅ Eslatma saqlandi!")

    confirm_text = (
        "✅ <b>Eslatma muvaffaqiyatli saqlandi!</b>\n\n"
        f"📌 <b>Mazmuni:</b>\n«{data.get('content_text', '')}»\n\n"
        f"📅 <b>Eslatish vaqti:</b> {format_uzbek_datetime(target_dt)}\n"
        f"🔄 <b>Takrorlanish:</b> {repeat_name}\n\n"
        "🔔 <i>Belgilangan vaqtda sizga bildirishnoma keladi.</i>"
    )
    await callback.message.edit_text(confirm_text, reply_markup=get_reminder_main_keyboard(), parse_mode="HTML")
