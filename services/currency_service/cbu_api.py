import time
import logging
import aiohttp

logger = logging.getLogger("cbu_service")

CBU_API_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
CACHE_TTL = 3600  # 1 soat (soniyalarda)

_cached_rates = {}
_last_fetch_time = 0

POPULAR_CURRENCIES = ["USD", "EUR", "RUB", "KZT", "TRY", "GBP", "AED", "CNY"]

CURRENCY_FLAGS = {
    "USD": "🇺🇸",
    "EUR": "🇪🇺",
    "RUB": "🇷🇺",
    "KZT": "🇰🇿",
    "TRY": "🇹🇷",
    "GBP": "🇬🇧",
    "AED": "🇦🇪",
    "CNY": "🇨🇳",
    "UZS": "🇺🇿"
}

async def fetch_cbu_rates(force_refresh: bool = False) -> dict:
    """O'zbekiston Markaziy Bankining rasmiy kurslarini asinxron olish (kesh bilan)"""
    global _cached_rates, _last_fetch_time

    now = time.time()
    if not force_refresh and _cached_rates and (now - _last_fetch_time < CACHE_TTL):
        return _cached_rates

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MultipleServiceBot/1.0"
    }

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(CBU_API_URL, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    rates_map = {}
                    for item in data:
                        ccy = item.get("Ccy")
                        rates_map[ccy] = {
                            "code": item.get("Code"),
                            "ccy": ccy,
                            "name_uz": item.get("CcyNm_UZ"),
                            "rate": float(item.get("Rate", 0)),
                            "diff": float(item.get("Diff", 0)),
                            "date": item.get("Date"),
                            "nominal": int(item.get("Nominal", 1))
                        }
                    _cached_rates = rates_map
                    _last_fetch_time = now
                    logger.info("Markaziy Bank valyuta kurslari muvaffaqiyatli yangilandi.")
                    return _cached_rates
                else:
                    logger.error(f"CBU API xatosi, status: {response.status}")
    except Exception as e:
        logger.error(f"CBU API dan kurslarni yuklashda xatolik: {e}")

    # Agar xatolik bo'lsa va eski kesh bo'lsa qaytaramiz
    if _cached_rates:
        return _cached_rates

    # Favqulodda zaxira (fallback)
    return {
        "USD": {"rate": 12055.0, "diff": 0.0, "date": "Bugun", "name_uz": "AQSH dollari", "nominal": 1},
        "EUR": {"rate": 13570.0, "diff": 0.0, "date": "Bugun", "name_uz": "Yevro", "nominal": 1},
        "RUB": {"rate": 144.0, "diff": 0.0, "date": "Bugun", "name_uz": "Rossiya rubli", "nominal": 1}
    }

def convert(amount: float, from_ccy: str, to_ccy: str, rates: dict) -> float:
    """Valyutani boshqasiga konvertatsiya qilish"""
    from_ccy = from_ccy.upper()
    to_ccy = to_ccy.upper()

    if from_ccy == to_ccy:
        return amount

    # Barcha hisob-kitob so'm (UZS) orqali
    if from_ccy == "UZS":
        to_rate = rates[to_ccy]["rate"] / rates[to_ccy]["nominal"]
        return amount / to_rate

    from_rate = rates[from_ccy]["rate"] / rates[from_ccy]["nominal"]
    amount_in_uzs = amount * from_rate

    if to_ccy == "UZS":
        return amount_in_uzs

    to_rate = rates[to_ccy]["rate"] / rates[to_ccy]["nominal"]
    return amount_in_uzs / to_rate
