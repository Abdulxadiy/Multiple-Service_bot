import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from services.reminder_service.utils import TASHKENT_TZ, get_now_tashkent, to_utc

EXPENSE_CATEGORIES = [
    "🍔 Oziq-ovqat",
    "🚕 Transport / Yoqilg'i",
    "🏠 Uy va Kommunal",
    "🛍 Xaridlar va Kiyim",
    "💊 Dorixona va Sog'liq",
    "☕️ Kafe va Ko'ngilochar",
    "🔄 Boshqa xarajat"
]

INCOME_CATEGORIES = [
    "💼 Oylik maosh / Avans",
    "📈 Biznes / Savdo",
    "🎁 Sovg'a / Mukofot",
    "🔄 Boshqa daromad"
]

CATEGORY_KEYWORDS = {
    "🍔 Oziq-ovqat": ["tushlik", "non", "ovqat", "bozor", "go'sht", "gosht", "supermarket", "osh", "somsa", "magazin", "shakar", "yog", "kartoshka", "sabzi"],
    "🚕 Transport / Yoqilg'i": ["taxi", "taksi", "benzin", "metan", "propan", "yolkira", "yo'lkira", "proyezd", "avtobus", "metro", "zapravka"],
    "🏠 Uy va Kommunal": ["kommunal", "gaz", "svet", "tok", "suv", "ijara", "kvartira", "wifi", "internet", "musor", "kvartplata"],
    "🛍 Xaridlar va Kiyim": ["kiyim", "shim", "kofta", "poyabzal", "oyoqkiyim", "xarid", "bozorlik", "kurtka", "texnika", "telefon"],
    "💊 Dorixona va Sog'liq": ["dori", "apteka", "doktor", "vrach", "shifoxona", "stomatolog", "analiz", "davolanish"],
    "☕️ Kafe va Ko'ngilochar": ["kafe", "restoran", "kino", "choyxona", "fastfood", "lavash", "pizza", "burger", "kofe", "coffee", "playstation"],
    "💼 Oylik maosh / Avans": ["oylik", "maosh", "avans", "ish haqi", "zarplata", "premiya"],
    "📈 Biznes / Savdo": ["savdo", "foyda", "biznes", "klient", "mijoz", "zakaz", "sotuv"]
}

def format_money(amount: int) -> str:
    """Raqamni chiroyli so'm formatiga o'tkazish (masalan: 1 250 000 so'm)"""
    formatted = f"{amount:,}".replace(",", " ")
    return f"{formatted} so'm"

def parse_money_input(text: str) -> tuple[int | None, str | None, str]:
    """
    Tezkor yozuvni tahlil qiladi (parse).
    Qaytaradi: (amount, note, transaction_type)
    Misollar:
    - '35000 tushlik' -> (35000, 'tushlik', 'expense')
    - '+2500000 oylik' -> (2500000, 'oylik', 'income')
    - '50k taxi' -> (50000, 'taxi', 'expense')
    - '100 ming dori' -> (100000, 'dori', 'expense')
    - '150 000' -> (150000, None, 'expense')
    """
    if not text:
        return None, None, "expense"

    clean_text = text.strip()
    is_income = clean_text.startswith("+")
    if is_income:
        clean_text = clean_text[1:].strip()

    # Regex orqali summani va qolgan izohni ajratib olamiz
    # Masalan: "35000 tushlik", "35k taxi", "50 ming bozor", "1 250 000"
    pattern = r"^(\d+(?:[\s.,]\d+)*)\s*(k|ming|mln|milliard)?(?:\s+(.*))?$"
    match = re.match(pattern, clean_text, re.IGNORECASE)

    if not match:
        return None, None, "expense"

    num_str, unit, note = match.groups()
    num_str = re.sub(r"[\s.,]", "", num_str)

    try:
        base_val = int(num_str)
    except ValueError:
        return None, None, "expense"

    multiplier = 1
    if unit:
        u = unit.lower()
        if u in ["k", "ming"]:
            multiplier = 1_000
        elif u == "mln":
            multiplier = 1_000_000
        elif u == "milliard":
            multiplier = 1_000_000_000

    amount = base_val * multiplier
    t_type = "income" if is_income else "expense"
    note_str = note.strip() if note else None

    return amount, note_str, t_type

def detect_category(note: str | None, default_type: str = "expense") -> str:
    """Izohdagi so'zlarga qarab avtomatik kategoriya aniqlash"""
    if not note:
        return "🔄 Boshqa daromad" if default_type == "income" else "🔄 Boshqa xarajat"

    note_lower = note.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", note_lower) or kw in note_lower:
                return category

    return "🔄 Boshqa daromad" if default_type == "income" else "🔄 Boshqa xarajat"

def get_period_boundaries(period: str) -> tuple[datetime, datetime]:
    """Toshkent vaqti bo'yicha davr chegaralarini UTC da qaytaradi"""
    now = get_now_tashkent()
    
    if period == "today":
        start_local = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=TASHKENT_TZ)
        end_local = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=TASHKENT_TZ)
    elif period == "week":
        # Dushanbadan boshlab
        weekday = now.weekday()  # 0 = dushanba
        start_of_week = now.date() - timedelta(days=weekday)
        start_local = datetime(start_of_week.year, start_of_week.month, start_of_week.day, 0, 0, 0, tzinfo=TASHKENT_TZ)
        end_local = now
    elif period == "month":
        # Shu oyning 1-kunidan
        start_local = datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=TASHKENT_TZ)
        end_local = now
    else:
        # Barchasi
        start_local = datetime(2020, 1, 1, 0, 0, 0, tzinfo=TASHKENT_TZ)
        end_local = now

    return to_utc(start_local), to_utc(end_local)

def extract_financial_from_text(sentence: str) -> tuple[int | None, str, str, str]:
    """
    O'zbek tilidagi tabiiy jumlalardan moliya ma'lumotlarini ajratib oladi.
    Qaytaradi: (amount, transaction_type, category, note)
    Misol:
    - 'Tushlikka 35 ming ketdi' -> (35000, 'expense', '🍔 Oziq-ovqat', 'Tushlikka 35 ming ketdi')
    - 'Oylik 3 million tushdi' -> (3000000, 'income', '💼 Oylik maosh / Avans', 'Oylik 3 million tushdi')
    """
    text = sentence.lower().strip()

    income_indicators = ["tushdi", "ish haqi", "avans", "foyda", "maosh", "daromad", "keldi", "kirim"]
    expense_indicators = ["ketdi", "ishlatdim", "sarfladim", "to'ladim", "toladim", "berdim", "harjladim", "chiqim", "sotib oldim"]

    t_type = "expense"
    if any(iv in text for iv in income_indicators):
        t_type = "income"

    # Raqam va birlikni topish
    num_match = re.search(r"(\d+(?:[\s.,]\d+)*)(?:\s*(k|ming|mln|million)\b)?(?:\s*so['’`]?m\b)?", text)
    amount = None
    if num_match:
        digits_str = re.sub(r"[\s.,]", "", num_match.group(1))
        val = int(digits_str)
        unit = (num_match.group(2) or "").lower()
        if unit in ["k", "ming"]:
            val *= 1_000
        elif unit in ["mln", "million"]:
            val *= 1_000_000
        amount = val

    category = detect_category(text, t_type)
    return amount, t_type, category, sentence.strip()
