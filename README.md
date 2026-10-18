# 🤖 Multiple-Service Telegram Bot (v1.8.0)

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

## 🛠 Texnologik Stek

- **Til:** Python 3.11+ (Python 3.14 qo'llab-quvvatlanadi)
- **Bot Framework:** aiogram 3.x (Asinxron)
- **Ma'lumotlar Bazasi:** SQLite / PostgreSQL + SQLAlchemy 2.0 (Async Engine via `aiosqlite`/`asyncpg`)
- **Speech-to-Text (STT):** Google Speech Recognition (uz-UZ) va Groq Whisper Large V3
- **Audio Konvertatsiya:** `ffmpeg` (OGG Opus to 16kHz WAV)
- **Kriptografiya:** `cryptography` (Fernet AES-256), `hashlib` (SHA-256)
- **Sozlamalar:** `pydantic-settings`, `python-dotenv`

---

## 📁 Loyiha Strukturasi

```
Multiple-Service_bot/
├── config/                  # Sozlamalar va muhit o'zgaruvchilari
│   └── settings.py
├── core/                    # Umumiy yadro tizimi
│   ├── database/            # Baza modellari (User, Account, Reminder)
│   ├── handlers/            # Asosiy menyu, xizmatlar, sozlamalar
│   ├── keyboards/           # Umumiy navigatsiya tugmalari
│   ├── middlewares/         # Anti-flood va user tracking
│   └── tasks/               # Fondagi tozalovchi va reminder workerlar
├── services/                # Modulli xizmatlar
│   ├── password_manager/    # 1-Xizmat: Parollar seyfi
│   └── reminder_service/    # 2-Xizmat: Eslatmalar va bildirishnomalar
│       ├── handlers/        # Eslatma yaratish, harakatlar, ro'yxat
│       ├── keyboards.py     # Eslatmalar tugmalari
│       ├── states.py        # FSM holatlari
│       ├── stt.py           # Ovozni matnga o'girish (STT)
│       └── utils.py         # Toshkent vaqti va aqlli time parser
├── utils/                   # Kriptografiya va xavfsizlik
│   └── crypto.py
├── main.py                  # Dasturni ishga tushirish nuqtasi
├── requirements.txt         # Kerakli kutubxonalar
└── .env.example             # Muhit o'zgaruvchilari namunasi
```

---

## 🚀 O'rnatish va Ishga Tushirish

### 1. Loyihani klonlash:
```bash
git clone https://github.com/Abdulxadiy/Multiple-Service_bot.git
cd Multiple-Service_bot
```

### 2. Virtual muhit yaratish va kutubxonalarni o'rnatish:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Muhit o'zgaruvchilarini sozlash:
`.env.example` dan nusxa olib `.env` yarating:
```bash
cp .env.example .env
```
`.env` fayliga Telegram [@BotFather](https://t.me/BotFather) dan olingan bot tokeningizni kiriting:
```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
```

### 4. Botni ishga tushirish (Lokal rejimda):
```bash
python main.py
```

---

## 🐳 Docker & Docker Compose orqali Ishga Tushirish (Production)

1. `.env` faylini sozlang:
```bash
cp .env.example .env
nano .env # BOT_TOKEN, ENCRYPTION_KEY va parollarni kiriting
```

2. Konteynerlarni bir buyruq bilan ko'taring:
```bash
docker-compose up -d --build
```

3. Loglarni kuzatish:
```bash
docker-compose logs -f bot
```

---

## ☁️ AWS ga Joylash (Production Best Practices)

- **AWS EC2:** Docker & Docker Compose orqali botni fon rejimida uzluksiz yurgizish.
- **AWS RDS PostgreSQL:** Ishonchli, avtomatik zaxiralanuvchi ma'lumotlar bazasi.
- **AWS S3 Backup:** `scripts/backup_db.sh` orqali har kuni bazani S3 ga avtomatik zaxiralash.

---

## 📄 Litsenziya

Ushbu loyiha [MIT License](LICENSE) asosida tarqatiladi.
Muallif: **Abdulxadiy Abduraximov**
