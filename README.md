# 🤖 Multiple-Service Telegram Bot (v2.0.0)

**Multiple-Service Bot** — bir nechta mustaqil foydali xizmatlarni bitta qulay platformada birlashtiruvchi ko'p xizmatli Telegram bot. Loyiha kengayuvchan, toza va modulli (Modular Monolith) arxitekturada qurilgan.

---

## 🔐 1-Xizmat: Login va Parollar Menejeri (Password Vault)

Ushbu modul foydalanuvchilarning login, parol va maxfiy ma'lumotlarini bank darajasidagi xavfsizlik bilan saqlash uchun mo'ljallangan.

### 🛡 Asosiy Xususiyatlar:
- **AES-256 Shifrlash:** Barcha parollar bazada xalqaro **AES-256 (Fernet)** standarti orqali shifrlangan holatda saqlanadi.
- **PIN-kod Himoyasi:** Shaxsiy seyfga kirish uchun kamida 4 xonali PIN o'rnatiladi. PIN kod bazada **SHA-256 + Salt** bilan xeshlanadi.
- **20 Daqiqalik Avto-O'chirish (Auto-Delete):** Ko'rilgan maxfiy login va parollar 20 daqiqadan so'ng chatdan avtomatik yo'q qilinadi.
- **2 Xil Usulda PIN Tiklash (Recovery):**
  1. *Tiklash Kodi (Recovery Code):* 8 xonali maxfiy kod orqali.
  2. *Bilim Asosida Tiklash (Knowledge-based):* Seyfda saqlangan ixtiyoriy bitta login/parolni to'g'ri kiritish orqali.
- **1-Bosishda Nusxalash:** Monospaced (`<code>...</code>`) formati orqali parollarni bir marta teginishda xavfsiz nusxalash.
- **🎲 Kuchli Parol Generatori:** Katta/kichik harflar, raqamlar va maxsus belgilar asosida 16 xonali murakkab parollar yaratish.
- **To'liq Izolyatsiya:** Har bir foydalanuvchining ma'lumotlari faqat uning `user_id` siga bog'langan.

---

## 📝 2-Xizmat: Eslatmalar va Bildirishnomalar (Reminder & Task Manager)

Ushbu xizmat muhim ishlar, to'lovlar, uchrashuvlar va rejalar uchun o'z vaqtida bildirishnoma yuboruvchi intellektual tizimdir.

### 🌟 Asosiy Imkoniyatlar:
- **🎙 Ovozli Eslatmalar (Speech-to-Text):** Uzun eslatmalarni klaviaturada yozib o'tirmasdan, audio (ovozli xabar) shaklida yuborishingiz mumkin. Bot ovozni o'zbek tilidagi aniq matnga o'giradi.
- **❓ Ovozni Tasdiqlash ("To'g'rimi?"):** Ovoz matnga o'girilgach, bot foydalanuvchidan matn to'g'riligini tasdiqlashni so'raydi (`Ha, to'g'ri`, `Matnni tahrirlash`, `Qayta aytish`).
- **🕒 O'zbekiston Vaqti (UTC+5 Asia/Tashkent):** Server vaqti qanday bo'lishidan qat'i nazar, barcha eslatmalar Toshkent vaqti bilan hisoblanadi.
- **⚡️ Aqlli Vaqt Parsing:** Tabiiy va tezkor formatlarni tushunadi: `15 daqiqa`, `30m`, `1 soat`, `3h`, `1d`, `14:30`, `ertaga 09:00`, `25.10 18:00`.
- **🔄 Takrorlanuvchi Rejalar:** Bir martalik, har kuni (shu vaqtda), har hafta yoki har oy takrorlanish tartibi.
- **✅ Bajarildi:** Bildirishnoma kelganda `✅ Bajarildi` bosilsa, qayta eslatilmaydi, lekin bazadan darhol o'chirilmaydi.
- **🗑 7 Kundan So'ng Avtomatik Tozalanish:** Bajarilgan eslatmalar aynan 7 kun o'tgach fondagi xizmat tomonidan avtomatik o'chiriladi.
- **⏰ Keyinroq Eslatilsin (Snooze):** Bildirishnoma kelganda qulay tugmalar orqali keyinga surish imkoniyati (`+15 daqiqa`, `+1 soat`, `+3 soat`, `Ertaga 09:00`, `Ertaga shu vaqtda` yoki `Boshqa vaqt`).
- **📋 Faol Eslatmalar va 7 Kunlik Tarix:** Faol eslatmalarni boshqarish, bekor qilish yoki bajarilganlarni bir zumda tozalash.

---

## 💰 3-Xizmat: Moliya va Hamyon (Personal Finance & Expense Tracker)

Shaxsiy byudjet, daromadlar va xarajatlarni oson va qulay yuritish xizmati.

### 💵 Asosiy Xususiyatlar:
- **🎙 AI Ovozli Boshqaruv:** Xarajat va daromadlarni shunchaki ovozli xabar qilib aytish (masalan: *«Tushlikka 35 ming ketdi»*, *«Oylik 3 million tushdi»*).
- **💳 Ko'p Hamyonli Tizim:** `💳 Karta`, `💵 Naqd pul`, `🏦 Jamg'arma` kabi alohida hamyonlar va umumiy balans nazorati.
- **⚡️ Tezkor Kiritish (Instant Smart Input):** Shunchaki xabar yozish orqali xarajat/daromad qo'shish:
  - `35000 tushlik` ➡️ 🍔 Oziq-ovqat chiqimi (35 000 so'm)
  - `+2500000 oylik` ➡️ 💼 Maosh daromadi (+2 500 000 so'm)
  - `50k taxi` ➡️ 🚕 Transport chiqimi (50 000 so'm)
- **📂 Avtomatik Kategoriya Ajratish:** Matndagi so'zlarga qarab avtomatik kategoriya belgilash (Oziq-ovqat, Transport, Kommunal, Xaridlar, Sog'liq, Kafe va b.).
- **📊 Batafsil Hisobotlar va Tahlil:** Kunlik, haftalik va oylik hisobotlar, eng ko'p xarajat qilingan TOP kategoriyalar foizlari bilan.
- **📜 Oxirgi Amallar Tarixi:** Xarajatlar va tushumlar ketma-ketligi.

---

## 💱 4-Xizmat: Valyuta kurslari va Konvertor (CBU Rates & Calculator)

O'zbekiston Respublikasi Markaziy Banki (CBU) rasmiy kurslari asosida ishlovchi jonli valyuta moduli.

### 🌐 Imkoniyatlar:
- **🏦 Rasmiy Markaziy Bank Kurslari:** USD, EUR, RUB, KZT, TRY, GBP, AED va CNY kurslari har kuni avtomatik yangilanadi.
- **📈 O'zgarish Dinamikasi:** Har bir valyuta kursi kechagiga nisbatan qanchaga ko'tarilgani yoki tushgani ko'rinib turadi (`+44.25` / `-12.50`).
- **🧮 Valyuta Kalkulyatori:** Xorijiy valyutani so'mga yoki so'mni valyutaga bir zumda o'girib hisoblash.
- **⚡️ Tezkor Xabar Tahlili:** Chatda shunchaki `100$`, `50 eur` yoki `5000 rub` deb yozilsa, bot darhol so'mdagi qiymatini hisoblab beradi.
- **⚡️ 1 Soatlik Aqlli Kesh (Smart Cache):** Server va bot tezkorligini ta'minlash uchun CBU ma'lumotlari keshlanadi va ortiqcha kutishlarning oldi olinadi.

---

## 🛠 Texnologik Stek

- **Til:** Python 3.11+ (Python 3.14 qo'llab-quvvatlanadi)
- **Bot Framework:** aiogram 3.x (Asinxron)
- **Ma'lumotlar Bazasi:** SQLite / PostgreSQL + SQLAlchemy 2.0 (Async Engine via `aiosqlite`/`asyncpg`)
- **Tashqi API:** CBU JSON API (Markaziy Bank rasmiy valyuta API)
- **Speech-to-Text (STT):** Google Speech Recognition (uz-UZ) va Groq Whisper Large V3
- **Audio Konvertatsiya:** `ffmpeg` (OGG Opus to 16kHz WAV)
- **Kriptografiya:** `cryptography` (Fernet AES-256), `hashlib` (SHA-256)
- **Sozlamalar:** `pydantic-settings`, `python-dotenv`

---

## 📁 Loyiha Strukturasi

```
Multiple-Service_bot/
├── config/                  # Sozlamalar va muhit o'zgaruvchilari
├── core/                    # Umumiy yadro tizimi (Baza, Middleware, Cleaner)
├── services/                # Modulli xizmatlar
│   ├── password_manager/    # 1-Xizmat: Parollar seyfi
│   ├── reminder_service/    # 2-Xizmat: Eslatmalar va bildirishnomalar (STT)
│   ├── finance_service/     # 3-Xizmat: Moliya va hamyon
│   └── currency_service/    # 4-Xizmat: Valyuta kurslari va kalkulyator
├── utils/                   # Kriptografiya va xavfsizlik
├── main.py                  # Dasturni ishga tushirish nuqtasi
├── requirements.txt         # Kerakli kutubxonalar
└── .env.example             # Muhit o'zgaruvchilari namunasi
```

---

## 📄 Litsenziya

Ushbu loyiha [MIT License](LICENSE) asosida tarqatiladi.
Muallif: **Abdulxadiy Abduraximov**
