# 🤖 Multiple-Service Telegram Bot

**Multiple-Service Bot** — bir nechta mustaqil xizmatlarni bitta qulay platformada birlashtiruvchi ko'p xizmatli Telegram bot. Loyiha kengayuvchan, modulli (Modular Monolith) arxitekturada qurilgan.

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
- **To'liq Izolyatsiya:** Har bir foydalanuvchining ma'lumotlari faqat uning `user_id` siga bog'langan va boshqa foydalanuvchilarga mutlaqo ko'rinmaydi.

---

## 🛠 Texnologik Stek

- **Til:** Python 3.11+
- **Bot Framework:** aiogram 3.x (Asinxron)
- **Ma'lumotlar Bazasi:** SQLite + SQLAlchemy 2.0 (Async Engine via `aiosqlite`)
- **Kriptografiya:** `cryptography` (Fernet AES-256), `hashlib` (SHA-256)
- **Sozlamalar:** `pydantic-settings`, `python-dotenv`

---

## 📁 Loyiha Strukturasi

```
Multiple-Service_bot/
├── config/              # Sozlamalar va muhit o'zgaruvchilari
│   └── settings.py
├── core/                # Umumiy yadro tizimi
│   ├── database/        # Baza modellari va asinxron sessiyalar
│   ├── handlers/        # Asosiy menyu, xizmatlar, sozlamalar
│   ├── keyboards/       # Umumiy navigatsiya tugmalari
│   ├── middlewares/     # Foydalanuvchini avto-ro'yxatga olish
│   └── tasks/           # 20 daqiqalik avto-tozalovchi xizmat
├── services/            # Modulli xizmatlar
│   └── password_manager/# 1-Xizmat: Parollar menejeri
│       ├── handlers/    # Akkauntlar, kategoriyalar, PIN handlerlari
│       ├── keyboards.py # Inline tugmalar
│       ├── states.py    # FSM holatlari
│       └── router.py    # Modul routeri
├── utils/               # Kriptografiya va yordamchilar
│   └── crypto.py
├── main.py              # Dasturni ishga tushirish nuqtasi
├── requirements.txt     # Kerakli kutubxonalar
└── .env.example         # Muhit o'zgaruvchilari namunasi
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

### 4. Botni ishga tushirish:
```bash
python main.py
```

---

## 📄 Litsenziya

Ushbu loyiha [MIT License](LICENSE) asosida tarqatiladi.
Muallif: **Abdulxadiy Abduraximov**