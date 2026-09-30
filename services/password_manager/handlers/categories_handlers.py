from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from core.database.session import async_session_maker
from core.database.models import Category, Account, User
from services.password_manager.states import CategoryStates
from services.password_manager.keyboards import (
    get_categories_keyboard,
    get_accounts_keyboard,
    get_confirm_delete_keyboard
)

categories_router = Router(name="categories_router")

@categories_router.callback_query(F.data == "svc:passwords")
async def show_categories(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        # Foydalanuvchining faqat o'ziga tegishli kategoriyalari
        result = await session.execute(
            select(Category).where(Category.user_id == user_id).order_by(Category.name)
        )
        categories = result.scalars().all()

    if not categories:
        text = (
            "🔐 <b>Login va Parollar Seyfi</b>\n\n"
            "Sizda hozircha birorta ham kategoriya yo'q.\n"
            "Parollaringizni tartibli saqlash uchun (masalan: <i>Google, Telegram, Banklar, Ish</i>) "
            "dastlab yangi kategoriya yarating:"
        )
    else:
        text = (
            "🔐 <b>Login va Parollar Seyfi</b>\n\n"
            "Kerakli kategoriyani tanlang yoki yangi kategoriya qo'shing:"
        )

    await callback.message.edit_text(
        text,
        reply_markup=get_categories_keyboard(categories),
        parse_mode="HTML"
    )

@categories_router.callback_query(F.data == "pm:cat:add")
async def start_add_category(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(CategoryStates.waiting_for_category_name)
    text = (
        "➕ <b>Yangi kategoriya yaratish</b>\n\n"
        "Kategoriya nomini kiriting (masalan: <code>Google</code>, <code>Instagram</code>, <code>Banklar</code>):"
    )
    await callback.message.answer(text, parse_mode="HTML")

@categories_router.message(CategoryStates.waiting_for_category_name)
async def process_category_name(message: Message, state: FSMContext):
    cat_name = message.text.strip() if message.text else ""
    if not cat_name or len(cat_name) > 60:
        await message.answer("⚠️ Kategoriya nomi 1 tadan 60 tagacha belgidan iborat bo'lishi kerak. Qaytadan kiriting:")
        return

    user_id = message.from_user.id
    async with async_session_maker() as session:
        # Bunday nomli kategoriya allaqachon bormi?
        existing = await session.execute(
            select(Category).where(Category.user_id == user_id, Category.name.ilike(cat_name))
        )
        if existing.scalar_one_or_none():
            await message.answer(f"⚠️ Sizda <b>{cat_name}</b> nomli kategoriya allaqachon mavjud! Boshqa nom kiriting:")
            return

        new_cat = Category(user_id=user_id, name=cat_name)
        session.add(new_cat)
        await session.commit()

        # Yangilangan ro'yxatni olamiz
        result = await session.execute(
            select(Category).where(Category.user_id == user_id).order_by(Category.name)
        )
        categories = result.scalars().all()

    await state.clear()
    await message.answer(
        f"✅ <b>{cat_name}</b> kategoriyasi muvaffaqiyatli yaratildi!",
        reply_markup=get_categories_keyboard(categories),
        parse_mode="HTML"
    )

@categories_router.callback_query(F.data.startswith("pm:cat:del_confirm:"))
async def confirm_delete_category(callback: CallbackQuery):
    await callback.answer()
    cat_id = int(callback.data.split(":")[3])
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        result = await session.execute(
            select(Category).where(Category.id == cat_id, Category.user_id == user_id)
        )
        cat = result.scalar_one_or_none()

    if not cat:
        await callback.answer("Kategoriya topilmadi!", show_alert=True)
        return

    text = (
        f"⚠️ <b>Diqqat!</b>\n\n"
        f"Haqiqatdan ham <b>{cat.name}</b> kategoriyasini o'chirmoqchimisiz?\n"
        f"<i>Uning ichidagi barcha akkaunt va parollar ham butunlay o'chiriladi!</i>"
    )
    confirm_cb = f"pm:cat:del_yes:{cat_id}"
    cancel_cb = f"pm:cat:{cat_id}"
    await callback.message.edit_text(text, reply_markup=get_confirm_delete_keyboard(confirm_cb, cancel_cb), parse_mode="HTML")

@categories_router.callback_query(F.data.startswith("pm:cat:del_yes:"))
async def delete_category_confirmed(callback: CallbackQuery):
    await callback.answer()
    cat_id = int(callback.data.split(":")[3])
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        result = await session.execute(
            select(Category).where(Category.id == cat_id, Category.user_id == user_id)
        )
        cat = result.scalar_one_or_none()
        if cat:
            await session.delete(cat)
            await session.commit()

        # Yangi ro'yxat
        result = await session.execute(
            select(Category).where(Category.user_id == user_id).order_by(Category.name)
        )
        categories = result.scalars().all()

    await callback.message.edit_text(
        "🗑 Kategoriya va unga tegishli barcha ma'lumotlar o'chirildi.",
        reply_markup=get_categories_keyboard(categories),
        parse_mode="HTML"
    )
