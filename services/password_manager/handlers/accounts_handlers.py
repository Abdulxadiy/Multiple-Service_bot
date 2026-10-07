from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from core.database.session import async_session_maker
from core.database.models import Category, Account, User
from utils.crypto import (
    encrypt_password,
    decrypt_password,
    verify_secret,
    generate_strong_password
)
from utils.security import pin_tracker, upgrade_pin_hash_if_needed
from core.tasks.cleaner import register_auto_delete_message
from services.password_manager.states import (
    AccountAddStates,
    AccountEditStates,
    PINVerifyStates
)
from services.password_manager.keyboards import (
    get_accounts_keyboard,
    get_account_detail_keyboard,
    get_password_input_keyboard,
    get_skip_keyboard,
    get_pin_prompt_keyboard,
    get_confirm_delete_keyboard,
    get_edit_fields_keyboard
)

accounts_router = Router(name="accounts_router")

# --- KATEGORIYA ICHIDAGI AKKAUNTLAR RO'YXATI ---

@accounts_router.callback_query(F.data.regexp(r"^pm:cat:(\d+)$"))
async def list_category_accounts(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    cat_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        cat_result = await session.execute(
            select(Category).where(Category.id == cat_id, Category.user_id == user_id)
        )
        category = cat_result.scalar_one_or_none()
        if not category:
            await callback.answer("Kategoriya topilmadi!", show_alert=True)
            return

        acc_result = await session.execute(
            select(Account).where(Account.category_id == cat_id, Account.user_id == user_id).order_by(Account.title)
        )
        accounts = acc_result.scalars().all()

    if not accounts:
        text = (
            f"📂 <b>Kategoriya:</b> {category.name}\n\n"
            f"Ushbu kategoriyada hozircha akkauntlar mavjud emas.\n"
            f"Yangi akkaunt ma'lumotlarini qo'shish uchun pastdagi tugmani bosing:"
        )
    else:
        text = (
            f"📂 <b>Kategoriya:</b> {category.name}\n\n"
            f"Kerakli akkauntni tanlang yoki yangisini qo'shing:"
        )

    await callback.message.edit_text(
        text,
        reply_markup=get_accounts_keyboard(cat_id, accounts),
        parse_mode="HTML"
    )

# --- YANGI AKKAUNT QO'SHISH (FSM) ---

@accounts_router.callback_query(F.data.startswith("pm:acc:add:"))
async def start_add_account(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    cat_id = int(callback.data.split(":")[3])
    user_id = callback.from_user.id

    # 1. Foydalanuvchida PIN bormi?
    async with async_session_maker() as session:
        user_res = await session.execute(select(User).where(User.telegram_id == user_id))
        user = user_res.scalar_one_or_none()

    if not user or not user.pin_hash:
        await callback.message.answer(
            "🛡 <b>PIN-kod talab qilinadi!</b>\n\n"
            "Parollaringizni xavfsiz saqlash va ko'rish uchun oldin PIN-kod o'rnatishingiz zarur.\n"
            "Buning uchun pastdagi tugmani bosing:",
            reply_markup=get_account_detail_keyboard(0, cat_id),
            parse_mode="HTML"
        )
        return

    await state.set_state(AccountAddStates.waiting_for_title)
    await state.update_data(category_id=cat_id)
    text = (
        "➕ <b>Yangi akkaunt qo'shish</b>\n\n"
        "1️⃣ Akkaunt nomini kiriting:\n"
        "<i>(Masalan: Mening 5-chi Google akkauntim, Asosiy GitHub, Uy Wi-Fi)</i>"
    )
    await callback.message.answer(text, parse_mode="HTML")

@accounts_router.message(AccountAddStates.waiting_for_title)
async def process_account_title(message: Message, state: FSMContext):
    title = message.text.strip() if message.text else ""
    if not title or len(title) > 100:
        await message.answer("⚠️ Nom 1 tadan 100 tagacha belgidan iborat bo'lishi kerak. Qayta kiriting:")
        return

    await state.update_data(title=title)
    await state.set_state(AccountAddStates.waiting_for_login)
    text = (
        "2️⃣ <b>Login / Username / Email:</b>\n\n"
        "Loginni yozing yoki login kerak bo'lmasa <b>O'tkazib yuborish</b> tugmasini bosing:"
    )
    await message.answer(text, reply_markup=get_skip_keyboard("pm:skip_login"), parse_mode="HTML")

@accounts_router.callback_query(F.data == "pm:skip_login", AccountAddStates.waiting_for_login)
async def skip_account_login(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(login=None)
    await prompt_password_step(callback.message, state)

@accounts_router.message(AccountAddStates.waiting_for_login)
async def process_account_login(message: Message, state: FSMContext):
    login = message.text.strip() if message.text else None
    await state.update_data(login=login)
    await prompt_password_step(message, state)

async def prompt_password_step(target_msg: Message, state: FSMContext):
    await state.set_state(AccountAddStates.waiting_for_password)
    text = (
        "3️⃣ <b>Parol:</b>\n\n"
        "Parolni kiriting yoki tasodifiy <b>🎲 Kuchli parol yaratish</b> tugmasini bosing:"
    )
    await target_msg.answer(text, reply_markup=get_password_input_keyboard(), parse_mode="HTML")

@accounts_router.callback_query(F.data == "pm:gen_pwd", AccountAddStates.waiting_for_password)
async def generate_password_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🎲 Kuchli parol generatsiya qilindi!")
    gen_pwd = generate_strong_password(16)
    await state.update_data(password=gen_pwd)

    text = (
        f"🎲 <b>Yaratilgan kuchli parol:</b>\n"
        f"<code>{gen_pwd}</code>\n\n"
        f"<i>(Nusxalash uchun ustiga bosing)</i>\n\n"
        "Ushbu parol qabul qilindi. Endi 4-bosqichga o'tamiz."
    )
    await callback.message.answer(text, parse_mode="HTML")
    await prompt_note_step(callback.message, state)

@accounts_router.message(AccountAddStates.waiting_for_password)
async def process_account_password(message: Message, state: FSMContext):
    password = message.text.strip() if message.text else ""
    try:
        await message.delete()
    except Exception:
        pass

    if not password:
        await message.answer("⚠️ Parol bo'sh bo'lishi mumkin emas. Qayta kiriting:")
        return

    await state.update_data(password=password)
    await prompt_note_step(message, state)

async def prompt_note_step(target_msg: Message, state: FSMContext):
    await state.set_state(AccountAddStates.waiting_for_note)
    text = (
        "4️⃣ <b>Qo'shimcha eslatma (ixtiyoriy):</b>\n\n"
        "Eslatma yoki havola yozing yoki <b>O'tkazib yuborish</b> tugmasini bosing:"
    )
    await target_msg.answer(text, reply_markup=get_skip_keyboard("pm:skip_note"), parse_mode="HTML")

@accounts_router.callback_query(F.data == "pm:skip_note", AccountAddStates.waiting_for_note)
async def skip_account_note(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await finalize_account_save(callback.message, state, note=None, user_id=callback.from_user.id)

@accounts_router.message(AccountAddStates.waiting_for_note)
async def process_account_note(message: Message, state: FSMContext):
    note = message.text.strip() if message.text else None
    await finalize_account_save(message, state, note=note, user_id=message.from_user.id)

async def finalize_account_save(target_msg: Message, state: FSMContext, note: str | None, user_id: int):
    data = await state.get_data()
    category_id = data.get("category_id")
    title = data.get("title")
    login = data.get("login")
    plain_password = data.get("password")

    # AES-256 orqali shifrlaymiz
    encrypted_pwd = encrypt_password(plain_password)

    async with async_session_maker() as session:
        new_account = Account(
            category_id=category_id,
            user_id=user_id,
            title=title,
            login=login,
            encrypted_password=encrypted_pwd,
            note=note
        )
        session.add(new_account)
        await session.commit()

        # Kategoriya va yangilangan akkauntlarni olamiz
        cat_res = await session.execute(select(Category).where(Category.id == category_id))
        category = cat_res.scalar_one_or_none()

        acc_res = await session.execute(
            select(Account).where(Account.category_id == category_id, Account.user_id == user_id).order_by(Account.title)
        )
        accounts = acc_res.scalars().all()

    await state.clear()
    cat_name = category.name if category else "Kategoriya"
    await target_msg.answer(
        f"✅ <b>{title}</b> akkaunti muvaffaqiyatli saqlandi va AES-256 bilan shifrlandi!\n\n"
        f"📂 <b>Kategoriya:</b> {cat_name}",
        reply_markup=get_accounts_keyboard(category_id, accounts),
        parse_mode="HTML"
    )

# --- AKKAUNTNI KO'RISH (PIN SO'RASH VA AVTO-O'CHIRISH) ---

@accounts_router.callback_query(F.data.regexp(r"^pm:acc:(\d+)$"))
async def request_pin_to_view(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    account_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id

    # Brute-force blokirovkasi tekshiruvi
    is_locked, remaining_secs = pin_tracker.is_locked(user_id)
    if is_locked:
        wait_min = (remaining_secs // 60) + 1
        await callback.message.answer(
            f"⏳ <b>Xavfsizlik blokirovkasi!</b>\n\n"
            f"Siz bir necha bor xato PIN kiritgansiz. Seyf himoya rejimida.\n"
            f"Iltimos, <b>{wait_min} daqiqa</b>dan so'ng qayta urinib ko'ring.",
            parse_mode="HTML"
        )
        return

    async with async_session_maker() as session:
        user_res = await session.execute(select(User).where(User.telegram_id == user_id))
        user = user_res.scalar_one_or_none()

    if not user or not user.pin_hash:
        await callback.message.answer(
            "🛡 Parollarni ko'rish uchun oldin PIN-kod o'rnatishingiz zarur.\n"
            "Iltimos, ⚙️ Sozlamalar bo'limidan PIN o'rnating.",
            parse_mode="HTML"
        )
        return

    await state.set_state(PINVerifyStates.waiting_for_pin)
    await state.update_data(account_id=account_id)

    text = (
        "🔒 <b>Akkaunt ma'lumotlarini ko'rish</b>\n\n"
        "Iltimos, o'z PIN-kodingizni kiriting:"
    )
    await callback.message.answer(text, reply_markup=get_pin_prompt_keyboard(account_id), parse_mode="HTML")

@accounts_router.message(PINVerifyStates.waiting_for_pin)
async def process_pin_and_show_account(message: Message, state: FSMContext):
    entered_pin = message.text.strip() if message.text else ""
    user_id = message.from_user.id

    try:
        await message.delete()
    except Exception:
        pass

    # Brute-force blokirovkasi tekshiruvi
    is_locked, remaining_secs = pin_tracker.is_locked(user_id)
    if is_locked:
        wait_min = (remaining_secs // 60) + 1
        await message.answer(
            f"⏳ <b>Xavfsizlik blokirovkasi!</b>\n\n"
            f"Seyf vaqtincha bloklangan. Iltimos, <b>{wait_min} daqiqa</b>dan so'ng qayta urinib ko'ring.",
            parse_mode="HTML"
        )
        await state.clear()
        return

    data = await state.get_data()
    account_id = data.get("account_id")

    async with async_session_maker() as session:
        user_res = await session.execute(select(User).where(User.telegram_id == user_id))
        user = user_res.scalar_one_or_none()

        if not user or not verify_secret(entered_pin, user.pin_hash or ""):
            attempts, is_now_locked, left = pin_tracker.record_failure(user_id)
            if is_now_locked:
                await state.clear()
                await message.answer(
                    "🚫 <b>Xavfsizlik choralari ishga tushdi!</b>\n\n"
                    "PIN-kod ketma-ket 5 marta noto'g'ri kiritildi. "
                    "Seyf 10 daqiqaga bloklandi.",
                    parse_mode="HTML"
                )
                return

            await message.answer(
                f"❌ <b>Noto'g'ri PIN-kod!</b> (Qolgan urinishlar: {left} ta)\n"
                "Qaytadan kiriting yoki agar unutgan bo'lsangiz tiklash tugmasini bosing:",
                reply_markup=get_pin_prompt_keyboard(account_id or 0),
                parse_mode="HTML"
            )
            return

        # To'g'ri PIN kiritilganda blok holatini tozalaymiz
        pin_tracker.record_success(user_id)
        # Agar eski xesh bo'lsa, uni xavfsiz PBKDF2 ga yangilaymiz
        await upgrade_pin_hash_if_needed(session, user, entered_pin)

        acc_res = await session.execute(
            select(Account).where(Account.id == account_id, Account.user_id == user_id)
        )
        account = acc_res.scalar_one_or_none()
        if not account:
            await state.clear()
            await message.answer("❌ Akkaunt topilmadi!")
            return

        cat_res = await session.execute(select(Category).where(Category.id == account.category_id))
        category = cat_res.scalar_one_or_none()
        cat_name = category.name if category else "Kategoriya"

    await state.clear()

    # AES-256 deshifrlash
    try:
        plain_password = decrypt_password(account.encrypted_password)
    except Exception:
        plain_password = "[Xatolik: parolni ochib bo'lmadi]"

    login_str = f"👤 <b>Login:</b> <code>{account.login}</code>\n" if account.login else ""
    note_str = f"📝 <b>Eslatma:</b> <i>{account.note}</i>\n" if account.note else ""

    display_text = (
        f"📂 <b>Kategoriya:</b> {cat_name}\n"
        f"🏷 <b>Nomi:</b> {account.title}\n"
        f"{login_str}"
        f"🔑 <b>Parol:</b> <code>{plain_password}</code>\n"
        f"{note_str}\n"
        f"⏳ <i>Xavfsizlik choralari: Ushbu ma'lumot 20 daqiqadan so'ng chatdan avtomatik o'chirib tashlanadi!</i>"
    )

    sent_msg = await message.answer(
        display_text,
        reply_markup=get_account_detail_keyboard(account.id, account.category_id),
        parse_mode="HTML"
    )

    # 20 daqiqalik avto-o'chirish navbatiga qo'shamiz
    await register_auto_delete_message(chat_id=message.chat.id, message_id=sent_msg.message_id, minutes=20)

# --- AKKAUNTNI O'CHIRISH (DELETE) ---

@accounts_router.callback_query(F.data.startswith("pm:acc:del_confirm:"))
async def confirm_delete_account(callback: CallbackQuery):
    await callback.answer()
    acc_id = int(callback.data.split(":")[3])
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        acc_res = await session.execute(
            select(Account).where(Account.id == acc_id, Account.user_id == user_id)
        )
        account = acc_res.scalar_one_or_none()

    if not account:
        await callback.answer("Akkaunt topilmadi!", show_alert=True)
        return

    text = f"⚠️ Haqiqatdan ham <b>{account.title}</b> akkauntini o'chirib tashlamoqchimisiz?"
    confirm_cb = f"pm:acc:del_yes:{acc_id}"
    cancel_cb = f"pm:cat:{account.category_id}"
    await callback.message.edit_text(text, reply_markup=get_confirm_delete_keyboard(confirm_cb, cancel_cb), parse_mode="HTML")

@accounts_router.callback_query(F.data.startswith("pm:acc:del_yes:"))
async def delete_account_confirmed(callback: CallbackQuery):
    await callback.answer()
    acc_id = int(callback.data.split(":")[3])
    user_id = callback.from_user.id

    async with async_session_maker() as session:
        acc_res = await session.execute(
            select(Account).where(Account.id == acc_id, Account.user_id == user_id)
        )
        account = acc_res.scalar_one_or_none()
        if account:
            cat_id = account.category_id
            await session.delete(account)
            await session.commit()

            acc_list_res = await session.execute(
                select(Account).where(Account.category_id == cat_id, Account.user_id == user_id).order_by(Account.title)
            )
            accounts = acc_list_res.scalars().all()
        else:
            cat_id = 0
            accounts = []

    await callback.message.edit_text(
        "🗑 Akkaunt muvaffaqiyatli o'chirildi.",
        reply_markup=get_accounts_keyboard(cat_id, accounts),
        parse_mode="HTML"
    )

# --- AKKAUNTNI TAHRIRLASH (EDIT) ---

@accounts_router.callback_query(F.data.startswith("pm:acc:edit:"))
async def choose_edit_field(callback: CallbackQuery):
    await callback.answer()
    acc_id = int(callback.data.split(":")[3])
    text = "✏️ <b>Qaysi ma'lumotni o'zgartirmoqchisiz?</b>"
    await callback.message.edit_text(text, reply_markup=get_edit_fields_keyboard(acc_id), parse_mode="HTML")

@accounts_router.callback_query(F.data.startswith("pm:edit_field:"))
async def prompt_new_field_value(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split(":")
    field = parts[2]
    acc_id = int(parts[3])

    await state.set_state(AccountEditStates.waiting_for_new_value)
    await state.update_data(account_id=acc_id, field=field)

    field_names = {
        "title": "yangi nomini",
        "login": "yangi login / username / emailini",
        "password": "yangi parolini",
        "note": "yangi eslatmasini"
    }
    field_prompt = field_names.get(field, "yangi qiymatini")

    if field == "password":
        await callback.message.answer(
            f"✏️ Akkauntning {field_prompt} kiriting yoki 🎲 'Kuchli parol yaratish' tugmasini bosing:",
            reply_markup=get_password_input_keyboard()
        )
    else:
        await callback.message.answer(f"✏️ Akkauntning {field_prompt} kiriting:")

@accounts_router.callback_query(F.data == "pm:gen_pwd", AccountEditStates.waiting_for_new_value)
async def generate_password_for_edit(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🎲 Kuchli parol yaratildi!")
    gen_pwd = generate_strong_password(16)
    data = await state.get_data()
    acc_id = data.get("account_id")
    user_id = callback.from_user.id

    encrypted_pwd = encrypt_password(gen_pwd)
    async with async_session_maker() as session:
        acc_res = await session.execute(
            select(Account).where(Account.id == acc_id, Account.user_id == user_id)
        )
        account = acc_res.scalar_one_or_none()
        if account:
            account.encrypted_password = encrypted_pwd
            await session.commit()
            cat_id = account.category_id
        else:
            cat_id = 0

    await state.clear()
    await callback.message.answer(
        f"✅ <b>Parol muvaffaqiyatli yangilandi!</b>\n\n"
        f"Yangi parol: <code>{gen_pwd}</code>",
        reply_markup=get_account_detail_keyboard(acc_id, cat_id),
        parse_mode="HTML"
    )

@accounts_router.message(AccountEditStates.waiting_for_new_value)
async def save_edited_field_value(message: Message, state: FSMContext):
    new_val = message.text.strip() if message.text else ""
    data = await state.get_data()
    acc_id = data.get("account_id")
    field = data.get("field")
    user_id = message.from_user.id

    try:
        await message.delete()
    except Exception:
        pass

    async with async_session_maker() as session:
        acc_res = await session.execute(
            select(Account).where(Account.id == acc_id, Account.user_id == user_id)
        )
        account = acc_res.scalar_one_or_none()
        if not account:
            await state.clear()
            await message.answer("❌ Akkaunt topilmadi!")
            return

        if field == "title":
            account.title = new_val
        elif field == "login":
            account.login = new_val
        elif field == "password":
            account.encrypted_password = encrypt_password(new_val)
        elif field == "note":
            account.note = new_val

        await session.commit()
        cat_id = account.category_id

    await state.clear()
    await message.answer(
        f"✅ <b>Akkaunt ma'lumoti muvaffaqiyatli yangilandi!</b>",
        reply_markup=get_account_detail_keyboard(acc_id, cat_id),
        parse_mode="HTML"
    )
