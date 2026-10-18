import re
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from services.currency_service.cbu_api import (
    fetch_cbu_rates,
    convert,
    POPULAR_CURRENCIES,
    CURRENCY_FLAGS
)
from services.currency_service.states import CurrencyState
from services.currency_service.keyboards import (
    get_currency_main_keyboard,
    get_calculator_keyboard,
    get_cancel_keyboard
)
from services.finance_service.utils import format_money

currency_router = Router(name="currency_router")

def build_rates_text(rates: dict) -> str:
    """Markaziy Bank kurslari chiroyli matnini shakllantirish"""
    usd_info = rates.get("USD", {})
    date_str = usd_info.get("date", "Bugun")

    text = (
        "🏦 <b>O'zbekiston Respublikasi Markaziy Banki (CBU)</b>\n"
        f"🗓 <b>Rasmiy valyuta kurslari (Sana: {date_str})</b>\n\n"
    )

    for ccy in POPULAR_CURRENCIES:
        info = rates.get(ccy)
        if not info:
            continue
        flag = CURRENCY_FLAGS.get(ccy, "🏳️")
        nominal = info.get("nominal", 1)
        rate = info.get("rate", 0)
        diff = info.get("diff", 0)

        # Diff belgisi (+ yoki -)
        if diff > 0:
            diff_str = f"📈 <i>+{diff}</i>"
        elif diff < 0:
            diff_str = f"📉 <i>{diff}</i>"
        else:
            diff_str = "<i>0.00</i>"

        nom_prefix = f"{nominal} " if nominal > 1 else "1 "
        formatted_rate = f"{rate:,.2f}".replace(",", " ")
        text += f"{flag} <b>{nom_prefix}{ccy}</b> = <code>{formatted_rate} so'm</code> ({diff_str})\n"

    text += (
        "\n💡 <i>Tezkor hisoblash uchun tugmalardan foydalaning yoki "
        "shunchaki «100$» yoki «5000 rub» deb yozing!</i>"
    )
    return text

@currency_router.callback_query(F.data == "svc:currency")
async def handle_currency_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    rates = await fetch_cbu_rates()
    text = build_rates_text(rates)
    await callback.message.edit_text(text, reply_markup=get_currency_main_keyboard(), parse_mode="HTML")

@currency_router.callback_query(F.data == "cur:refresh")
async def handle_currency_refresh(callback: CallbackQuery):
    await callback.answer("🔄 Yangi kurslar yuklanmoqda...")
    rates = await fetch_cbu_rates(force_refresh=True)
    text = build_rates_text(rates)
    try:
        await callback.message.edit_text(text, reply_markup=get_currency_main_keyboard(), parse_mode="HTML")
        await callback.answer("✅ Kurslar muvaffaqiyatli yangilandi!")
    except Exception:
        await callback.answer("Kurslar allaqachon eng so'nggi holatda.")

@currency_router.callback_query(F.data.startswith("cur_preset:"))
async def handle_currency_preset(callback: CallbackQuery):
    parts = callback.data.split(":")
    amount = float(parts[1])
    ccy = parts[2]

    rates = await fetch_cbu_rates()
    result_uzs = convert(amount, ccy, "UZS", rates)

    flag = CURRENCY_FLAGS.get(ccy, "")
    formatted_uzs = f"{result_uzs:,.2f}".replace(",", " ")
    formatted_amt = f"{int(amount):,}".replace(",", " ")

    msg = f"💱 <b>Natija:</b>\n\n{flag} <b>{formatted_amt} {ccy}</b> = <code>{formatted_uzs} so'm</code>"
    await callback.answer(f"{formatted_amt} {ccy} = {formatted_uzs} so'm", show_alert=True)

@currency_router.callback_query(F.data == "cur:calc")
async def handle_calc_menu(callback: CallbackQuery):
    await callback.answer()
    text = (
        "🧮 <b>Valyuta Kalkulyatori:</b>\n\n"
        "Qaysi yo'nalishda hisoblamoqchisiz?"
    )
    await callback.message.edit_text(text, reply_markup=get_calculator_keyboard(), parse_mode="HTML")

@currency_router.callback_query(F.data.startswith("cur_mode:"))
async def handle_calc_mode_select(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.split(":")[1]
    from_ccy, to_ccy = mode.split("_")
    await callback.answer()
    await state.set_state(CurrencyState.waiting_for_convert_input)
    await state.update_data(from_ccy=from_ccy, to_ccy=to_ccy)

    from_flag = CURRENCY_FLAGS.get(from_ccy, "")
    to_flag = CURRENCY_FLAGS.get(to_ccy, "")

    text = (
        f"🧮 <b>Konvertatsiya:</b> {from_flag} <b>{from_ccy}</b> ➡️ {to_flag} <b>{to_ccy}</b>\n\n"
        f"Miqdorni kiriting (masalan: <code>100</code> yoki <code>2500000</code>):"
    )
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

@currency_router.message(CurrencyState.waiting_for_convert_input, F.text)
async def process_custom_convert(message: Message, state: FSMContext):
    clean_text = re.sub(r"[\s,]", "", message.text.strip())
    try:
        amount = float(clean_text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "⚠️ Noto'g'ri miqdor kiritildi. Faqat musbat raqam kiriting (masalan: <code>150</code> yoki <code>500000</code>):",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    from_ccy = data.get("from_ccy", "USD")
    to_ccy = data.get("to_ccy", "UZS")

    rates = await fetch_cbu_rates()
    res = convert(amount, from_ccy, to_ccy, rates)

    from_flag = CURRENCY_FLAGS.get(from_ccy, "")
    to_flag = CURRENCY_FLAGS.get(to_ccy, "")

    formatted_from = f"{amount:,.2f}".replace(",", " ").rstrip("0").rstrip(".")
    formatted_to = f"{res:,.2f}".replace(",", " ")

    rate_info = rates.get(from_ccy if from_ccy != "UZS" else to_ccy, {})
    nominal = rate_info.get("nominal", 1)
    base_rate = rate_info.get("rate", 1)

    await state.clear()
    result_text = (
        "🧮 <b>Hisoblash natijasi:</b>\n\n"
        f"{from_flag} <b>{formatted_from} {from_ccy}</b> = {to_flag} <code>{formatted_to} {to_ccy}</code>\n\n"
        f"📌 <i>Rasmiy kurs: 1 {rate_info.get('ccy', '')} = {base_rate:,.2f} so'm</i>"
    )
    await message.answer(result_text, reply_markup=get_calculator_keyboard(), parse_mode="HTML")

# Tezkor matn orqali valyuta hisoblash (masalan: "100$", "50 eur", "5000 rub")
@currency_router.message(F.text.regexp(r"^(\d+(?:[\s.,]\d+)*)\s*(\$|usd|доллар|eur|yevro|евро|rub|рубл[ья]?|som|so['’`]?m)\b", flags=2))
async def handle_quick_currency_text(message: Message, state: FSMContext):
    # Agar boshqa biror FSM holatida bo'lsa xalal bermaymiz
    if await state.get_state() is not None:
        return

    text = message.text.lower().strip()
    match = re.match(r"^(\d+(?:[\s.,]\d+)*)\s*(\$|usd|доллар|eur|yevro|евро|rub|рубл[ья]?|som|so['’`]?m)\b", text)
    if not match:
        return

    amt_str, symbol = match.groups()
    amt_str = re.sub(r"[\s,]", "", amt_str)
    try:
        amount = float(amt_str)
        if amount <= 0:
            return
    except ValueError:
        return

    # Belgini aniqlash
    if symbol in ["$", "usd", "доллар"]:
        from_ccy = "USD"
        to_ccy = "UZS"
    elif symbol in ["eur", "yevro", "евро"]:
        from_ccy = "EUR"
        to_ccy = "UZS"
    elif symbol in ["rub", "рубль", "рубля"]:
        from_ccy = "RUB"
        to_ccy = "UZS"
    elif "so" in symbol:
        from_ccy = "UZS"
        to_ccy = "USD"
    else:
        return

    rates = await fetch_cbu_rates()
    res = convert(amount, from_ccy, to_ccy, rates)

    from_flag = CURRENCY_FLAGS.get(from_ccy, "")
    to_flag = CURRENCY_FLAGS.get(to_ccy, "")

    formatted_from = f"{amount:,.2f}".replace(",", " ").rstrip("0").rstrip(".")
    formatted_to = f"{res:,.2f}".replace(",", " ")

    reply_text = (
        f"💱 <b>Valyuta hisoblagich (CBU):</b>\n\n"
        f"{from_flag} <b>{formatted_from} {from_ccy}</b> = {to_flag} <code>{formatted_to} {to_ccy}</code>"
    )
    await message.reply(reply_text, parse_mode="HTML")
