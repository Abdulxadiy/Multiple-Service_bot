import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TASHKENT_TZ = ZoneInfo("Asia/Tashkent")

MONTHS_UZ = {
    1: "yanvar", 2: "fevral", 3: "mart", 4: "aprel",
    5: "may", 6: "iyun", 7: "iyul", 8: "avgust",
    9: "sentabr", 10: "oktabr", 11: "noyabr", 12: "dekabr"
}

def get_now_tashkent() -> datetime:
    """Hozirgi vaqtni Toshkent vaqt mintaqasida qaytaradi"""
    return datetime.now(TASHKENT_TZ)

def to_utc(dt: datetime) -> datetime:
    """Toshkent yoki ixtiyoriy vaqtni UTC ga o'girish"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TASHKENT_TZ)
    return dt.astimezone(timezone.utc)

def to_tashkent(dt: datetime) -> datetime:
    """UTC vaqtni Toshkent vaqtiga o'girish"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TASHKENT_TZ)

def format_uzbek_datetime(dt: datetime) -> str:
    """Foydalanuvchiga tushunarli chiroyli o'zbekcha formatda vaqtni ko'rsatish"""
    tashkent_dt = to_tashkent(dt)
    now = get_now_tashkent()
    
    today = now.date()
    target_date = tashkent_dt.date()
    time_str = tashkent_dt.strftime("%H:%M")
    
    if target_date == today:
        return f"Bugun, soat {time_str}"
    elif target_date == today + timedelta(days=1):
        return f"Ertaga, soat {time_str}"
    elif target_date == today + timedelta(days=2):
        return f"Indiniga, soat {time_str}"
    else:
        month_name = MONTHS_UZ.get(tashkent_dt.month, tashkent_dt.strftime("%B"))
        year_str = f" {tashkent_dt.year}-yil" if tashkent_dt.year != now.year else ""
        return f"{tashkent_dt.day}-{month_name}{year_str}, soat {time_str}"

def parse_time_input(input_str: str, base_time: datetime | None = None) -> datetime | None:
    """
    Foydalanuvchi yozgan vaqt matnini tahlil qiladi (parse).
    Qo'llab-quvvatlanadigan formatlar:
    - Nisbiy daqiqa/soat: '15m', '15 daqiqa', '30m', '1h', '1 soat', '3h', '1d', '2 kun'
    - Aniq soat: '14:30', '09:00', '18.00' (agar o'tgan bo'lsa ertangi kunga o'tkaziladi)
    - So'z bilan: 'bugun 20:00', 'ertaga 09:30', 'indiniga 14:00'
    - To'liq sana: '25.10 14:00', '25.10.2026 14:00', '2026-10-25 14:00'
    Qaytaradi: Tashkent timezone'dagi datetime yoki xato bo'lsa None.
    """
    if not input_str or not input_str.strip():
        return None

    now = base_time or get_now_tashkent()
    text = input_str.strip().lower()

    # 1. Nisbiy daqiqalar (masalan: 10m, 15 daqiqa, +15, 30 minut)
    match_min = re.match(r"^(\+)?\s*(\d+)\s*(m|min|daqiqa|minut)$", text)
    if match_min:
        mins = int(match_min.group(2))
        return now + timedelta(minutes=mins)

    # 2. Nisbiy soatlar (masalan: 1h, 2 soat, +3)
    match_hour = re.match(r"^(\+)?\s*(\d+)\s*(h|soat|chas)$", text)
    if match_hour:
        hours = int(match_hour.group(2))
        return now + timedelta(hours=hours)

    # 3. Nisbiy kunlar (masalan: 1d, 2 kun)
    match_day = re.match(r"^(\+)?\s*(\d+)\s*(d|kun|day)$", text)
    if match_day:
        days = int(match_day.group(2))
        return now + timedelta(days=days)

    # 4. 'bugun 18:30', 'ertaga 09:00', 'indiniga 12:00'
    match_rel_day = re.match(r"^(bugun|ertaga|indiniga)\s+(\d{1,2})[:.](\d{2})$", text)
    if match_rel_day:
        word, hour_s, min_s = match_rel_day.groups()
        hour, minute = int(hour_s), int(min_s)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            day_offset = 0 if word == "bugun" else (1 if word == "ertaga" else 2)
            target_date = (now + timedelta(days=day_offset)).date()
            result = datetime(
                target_date.year, target_date.month, target_date.day,
                hour, minute, tzinfo=TASHKENT_TZ
            )
            # Agar 'bugun' deb hozirgidan oldingi vaqtni yozgan bo'lsa, xato
            if result <= now and word == "bugun":
                return None
            return result

    # Faqat 'ertaga' deb yozsa (standart ertalab 09:00)
    if text == "ertaga":
        target_date = (now + timedelta(days=1)).date()
        return datetime(target_date.year, target_date.month, target_date.day, 9, 0, tzinfo=TASHKENT_TZ)

    # 5. Faqat soat: '14:30', '9:15', '18.00'
    match_time_only = re.match(r"^(\d{1,2})[:.](\d{2})$", text)
    if match_time_only:
        hour = int(match_time_only.group(1))
        minute = int(match_time_only.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            target_dt = datetime(
                now.year, now.month, now.day, hour, minute, tzinfo=TASHKENT_TZ
            )
            # Agar bugungi vaqt o'tib ketgan bo'lsa, ertangi kunga mo'ljallaymiz
            if target_dt <= now:
                target_dt += timedelta(days=1)
            return target_dt

    # 6. Sana va soat: '25.10 14:30', '25.10.2026 14:30'
    match_date_time = re.match(r"^(\d{1,2})[./-](\d{1,2})(?:[./-](\d{4}))?\s+(\d{1,2})[:.](\d{2})$", text)
    if match_date_time:
        day_s, month_s, year_s, hour_s, min_s = match_date_time.groups()
        day, month = int(day_s), int(month_s)
        year = int(year_s) if year_s else now.year
        hour, minute = int(hour_s), int(min_s)
        try:
            target_dt = datetime(year, month, day, hour, minute, tzinfo=TASHKENT_TZ)
            if target_dt <= now and not year_s:
                # Agar yil kiritilmagan bo'lsa va sana o'tib ketgan bo'lsa, keyingi yil
                target_dt = datetime(year + 1, month, day, hour, minute, tzinfo=TASHKENT_TZ)
            if target_dt > now:
                return target_dt
        except ValueError:
            return None

    return None
