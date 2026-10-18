<div align="center">

# 🤖 Multiple-Service Telegram Bot

**Kuchli, xavfsiz va ko'p xizmatli zamonaviy Telegram platformasi**

[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://docs.aiogram.dev)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Latest Release](https://img.shields.io/badge/Release-v2.0.0-success?style=for-the-badge)](https://github.com/Abdulxadiy/Multiple-Service_bot/releases)

<p align="center">
  <a href="#-haqida">Haqida</a> •
  <a href="#-xizmatlar-tavsifi">Xizmatlar</a> •
  <a href="#-arxitektura">Arxitektura</a> •
  <a href="#-texnologik-stek">Texnologiyalar</a> •
  <a href="#-ornatish-va-ishga-tushirish">O'rnatish</a> •
  <a href="#-muhit-ozgaruvchilari">Sozlamalar</a> •
  <a href="#-xavfsizlik">Xavfsizlik</a> •
  <a href="#-muallif-va-litsenziya">Litsenziya</a>
</p>

</div>

---

## 📌 Haqida

**Multiple-Service Bot** — kundalik hayot va biznesda eng ko'p kerak bo'ladigan mustaqil xizmatlarni yagona qulay ekotizimda birlashtiruvchi professional Telegram bot. 

Loyiha **Modular Monolith** (modulli monolit) me'morchiligi asosida ishlab chiqilgan. Har bir xizmat to'liq alohida modul sifatida ishlaydi, shaxsiy ma'lumotlar bazasi modellari, FSM holatlari va handlerlariga ega bo'lib, loyihani yangi xizmatlar bilan oson kengaytirish imkonini beradi.

---

## 🎛 Xizmatlar Tavsifi

### 🔐 1. Login va Parollar Seyfi (Password Vault)
Parollar va maxfiy ma'lumotlarni bank darajasidagi xavfsizlik bilan saqlash moduli.
- **AES-256 Shifrlash:** Har bir parol xalqaro **Fernet (AES-256-CBC)** shifrlash standarti bilan bazada saqlanadi.
- **PIN-kod Himoyasi:** Seyfga kirish uchun kamida 4 xonali shaxsiy PIN o'rnatiladi (**SHA-256 + Salt** xeshlangan).
- **20 Daqiqalik Avto-O'chirish:** Chatda ochilgan maxfiy login va parollar 20 daqiqadan so'ng Telegram chatidan avtomatik o'chiriladi.
- **Ikki bosqichli PIN tiklash:** Maxfiy 8 xonali tiklash kodi yoki seyfdagi ixtiyoriy bitta ma'lumotni kiritish orqali.
- **1-Bosishda Nusxalash:** Monospaced (`<code>...</code>`) formati orqali parollarni bir marta bosishda xavfsiz nusxalash.
- **🎲 Kuchli Parol Generatori:** Harflar, raqamlar va maxsus belgilar asosida 16 xonali kriptobardosh parollar yaratish.

---

### 📝 2. Eslatmalar va Bildirishnomalar (Reminders & Tasks)
Vaqt va rejalarni o'z vaqtida bildirishnoma bilan eslatuvchi intellektual tizim.
- **🎙 AI Ovozli Eslatmalar (Speech-to-Text):** Uzun eslatmalarni yozish shart emas — shunchaki ovozli xabar (voice) yuboring, bot uni o'zbek tilidagi aniq matnga o'giradi.
- **❓ Ovozni Tasdiqlash ("To'g'rimi?"):** Ovoz matnga aylangach, bot foydalanuvchidan matn to'g'riligini tasdiqlashni so'raydi (`✅ Ha, to'g'ri`, `✍️ Tahrirlash`, `🔄 Qayta aytish`).
- **🕒 O'zbekiston Vaqti (UTC+5 Asia/Tashkent):** Server qayerda joylashganidan qat'i nazar, barcha muddatlar Toshkent vaqti bilan hisoblanadi.
- **⚡️ Aqlli Vaqt Parseri:** `15 daqiqa`, `30m`, `1 soat`, `3h`, `1d`, `14:30`, `ertaga 09:00`, `25.10 18:00` kabi tabiiy yozuvlarni bir zumda tushunadi.
- **🔄 Takrorlanish Tartibi:** Bir martalik, har kuni (bir vaqtda), har hafta yoki har oy takrorlanish tartiblari.
- **✅ Bajarildi & 7 Kunlik Arxiv:** Eslatma kelganda `✅ Bajarildi` bosilsa, qayta eslatilmaydi, lekin bazada 7 kun saqlanadi. 7 kun to'lgach fondagi avto-tozalovchi xizmat tomonidan o'chiriladi.
- **⏰ Keyinroq Eslatilsin (Snooze):** Bildirishnoma kelganda `+15m`, `+1h`, `+3h`, `Ertaga 09:00`, `Ertaga shu vaqt` tugmalari bilan rejalashtirish.

---

### 💰 3. Moliya va Hamyon (Personal Finance & Expense Tracker)
Shaxsiy byudjet, daromadlar va xarajatlarni engil va zavq bilan yuritish xizmati.
- **🎙 AI Ovozli Boshqaruv:** Xarajat va daromadlarni ovozli xabar bilan aytish: *«Tushlikka 35 ming ketdi»*, *«Oylik 3 million tushdi»* — bot ovozni tushunadi, summani ajratadi va hamyonga yozadi!
- **💳 Ko'p Hamyonli Tizim:** `💳 Karta`, `💵 Naqd pul`, `🏦 Jamg'arma` kabi alohida hamyonlar va umumiy balans.
- **⚡️ Bir Zumda Kiritish (Instant Input):**
  - `35000 tushlik` ➡️ 🍔 Oziq-ovqat chiqimi (35 000 so'm)
  - `+2500000 oylik` ➡️ 💼 Maosh daromadi (+2 500 000 so'm)
  - `50k taxi` ➡️ 🚕 Transport chiqimi (50 000 so'm)
- **📂 Avtomatik Kategoriya Ajratish:** Matndagi so'zlarga qarab avtomatik kategoriya belgilaydi (Oziq-ovqat, Transport, Kommunal, Xaridlar, Dorixona, Kafe va h.k.).
- **📊 Tahliliy Hisobotlar:** Kunlik, haftalik va oylik hisobotlar hamda eng ko'p pul sarflangan TOP kategoriyalar foizlari bilan.

---

### 💱 4. Valyuta Kurslari va Konvertor (CBU Live Rates & Calculator)
O'zbekiston Respublikasi Markaziy Bankining (CBU) rasmiy ma'lumotlariga asoslangan jonli valyuta moduli.
- **🏦 Rasmiy Markaziy Bank Kurslari:** USD, EUR, RUB, KZT, TRY, GBP, AED, CNY kurslari har kuni avtomatik yangilanadi.
- **📈 O'zgarish Dinamikasi:** Kurslarning kechagiga nisbatan o'zgarishi ko'rinib turadi (`+44.25` / `-12.50`).
- **🧮 Valyuta Kalkulyatori:** Xorijiy valyutani so'mga yoki so'mni chet el valyutasiga bir zumda konvertatsiya qilish.
- **⚡️ Chatda Tezkor Hisoblagich:** Shunchaki `100$`, `50 eur` yoki `5000 rub` deb yozilsa, bot darhol so'mdagi qiymatini qaytaradi.
- **⚡️ 1 Soatlik Aqlli Kesh (Smart Cache):** Server tezkorligini ta'minlash uchun CBU ma'lumotlari keshlanadi, bu esa javob tezligini 0.1 soniyaga yetkazadi.

---

## 🏛 Arxitektura

Loyiha yuqori yuklamalarga chidamli, asinxron va hodisalarga asoslangan (event-driven) modulli tuzilishga ega:

```
                          ┌──────────────────────────┐
                          │   Telegram Update Stream │
                          └─────────────┬────────────┘
                                        │
                                        ▼
                          ┌──────────────────────────┐
                          │   Aiogram 3 Dispatcher   │
                          │ ├─ Anti-Flood Throttling │
                          │ └─ User Auto-Tracking    │
                          └─────────────┬────────────┘
                                        │
         ┌───────────────┬──────────────┼───────────────┬───────────────┐
         ▼               ▼              ▼               ▼               ▼
   ┌───────────┐   ┌───────────┐  ┌───────────┐   ┌───────────┐   ┌───────────┐
   │   Base    │   │ Password  │  │ Reminder  │   │  Finance  │   │ Currency  │
   │  Router   │   │  Vault    │  │  Service  │   │  Service  │   │  Service  │
   └───────────┘   └───────────┘  └───────────┘   └───────────┘   └───────────┘
         │               │              │               │               │
         └───────────────┴──────────────┼───────────────┴───────────────┘
                                        ▼
                          ┌──────────────────────────┐
                          │    SQLAlchemy 2.0 Async  │
                          │   (PostgreSQL / SQLite)  │
                          └─────────────┬────────────┘
                                        │
               ┌────────────────────────┴────────────────────────┐
               ▼                                                 ▼
   ┌───────────────────────┐                         ┌───────────────────────┐
   │  Auto-Delete Cleaner  │                         │    Reminder Worker    │
   │   (Every 15 seconds)  │                         │  (Notifications & STT)│
   └───────────────────────┘                         └───────────────────────┘
```

---

## 🛠 Texnologik Stek

| Yo'nalish | Texnologiya | Tavsif |
| :--- | :--- | :--- |
| **Dasturlash tili** | Python 3.11 / 3.12 / 3.14 | Zamonaviy tipizatsiyalangan asinxron Python |
| **Bot Framework** | aiogram 3.x | Yuqori tezlikdagi to'liq asinxron Telegram framework |
| **ORM / Ma'lumotlar bazasi** | SQLAlchemy 2.0 + asyncpg / aiosqlite | PostgreSQL (Production) va SQLite (Local development) |
| **Migratsiyalar** | Alembic | Baza sxemalarini versiyalash va xavfsiz yangilash |
| **Nutqni aniqlash (STT)** | Google Speech Recognition & Groq Whisper Large V3 | O'zbek tilidagi ovozli xabarlarni yuqori aniqlikda matnga o'girish |
| **Audio qayta ishlash** | `ffmpeg` | Telegram OGG Opus formatini 16kHz WAV ga konvertatsiya qilish |
| **Kriptografiya** | Cryptography (Fernet AES-256) + Hashlib | Parollarni simmetrik shifrlash va PIN kodlarni tuz bilan xeshlash |
| **Sozlamalar va Validatsiya** | Pydantic Settings & Python-Dotenv | Xavfsiz muhit o'zgaruvchilari boshqaruvi |
| **Konteynerlashtirish** | Docker & Docker Compose | Bir necha soniyada to'liq izolyatsiyalangan serverga ko'tarish |

---

## 📁 Loyiha Strukturasi

```text
Multiple-Service_bot/
├── alembic/                         # Ma'lumotlar bazasi migratsiyalari
├── config/                          # Loyiha konfiguratsiyasi
│   └── settings.py                  # Pydantic Settings sozlamalari
├── core/                            # Tizimning umumiy yadrosi
│   ├── database/                    # Baza modellari va asinxron sessiyalar
│   │   ├── base.py                  # DeclarativeBase
│   │   ├── models.py                # User, Account, Reminder, Wallet, Transaction
│   │   └── session.py               # Async engine va sessionmaker
│   ├── handlers/                    # Bosh menyu, yordam va navigatsiya
│   ├── keyboards/                   # Reply va Inline asosiy klaviaturalar
│   ├── middlewares/                 # Throttling (Anti-flood) va User-Tracking
│   └── tasks/                       # Fondagi asinxron vazifalar (Workerlar)
│       ├── cleaner.py               # 20 daqiqalik parollarni tozalovchi
│       └── reminder_worker.py       # Eslatmalarni jo'natish va 7 kunlik tozalash
├── services/                        # Mustaqil xizmat modullari
│   ├── password_manager/            # 1-Xizmat: Login va Parollar Seyfi
│   │   ├── handlers/                # Akkauntlar, kategoriyalar, PIN boshqaruvi
│   │   ├── keyboards.py             # Seyf klaviaturalari
│   │   ├── router.py                # Parol menejeri routeri
│   │   └── states.py                # FSM holatlari
│   ├── reminder_service/            # 2-Xizmat: Eslatmalar va Bildirishnomalar
│   │   ├── handlers/                # Eslatma yaratish, boshqarish, tarix
│   │   ├── keyboards.py             # Eslatmalar klaviaturalari
│   │   ├── router.py                # Eslatmalar routeri
│   │   ├── states.py                # FSM holatlari
│   │   ├── stt.py                   # Ovozni matnga o'girish (STT) xizmati
│   │   └── utils.py                 # Toshkent vaqti va aqlli time-parser
│   ├── finance_service/             # 3-Xizmat: Moliya va Hamyon
│   │   ├── handlers/                # Hamyon boshqaruvi, kirim-chiqim, hisobotlar
│   │   ├── keyboards.py             # Moliya klaviaturalari
│   │   ├── router.py                # Moliya routeri
│   │   ├── states.py                # FSM holatlari
│   │   └── utils.py                 # Summa parseri, kategoriyalash, hisobotlar
│   └── currency_service/            # 4-Xizmat: Valyuta Kurslari va Konvertor
│       ├── cbu_api.py               # Markaziy Bank (CBU) API va kesh
│       ├── handlers/                # Jonli kurslar va kalkulyator handlerlari
│       ├── keyboards.py             # Valyuta klaviaturalari
│       ├── router.py                # Valyuta routeri
│       └── states.py                # FSM holatlari
├── utils/                           # Kriptografik va xavfsizlik utilitlari
│   ├── crypto.py                    # AES-256 shifrlash/deshifrlash
│   └── security.py                  # PIN xeshlash va tekshirish
├── scripts/                         # Ma'muriy skriptlar
│   ├── backup_db.sh                 # Avtomatik S3 zaxira nusxalash
│   └── migrate_sqlite_to_pg.py      # SQLite dan PostgreSQL ga ma'lumot ko'chirish
├── Dockerfile                       # Minimal va xavfsiz Dockerfile (non-root)
├── docker-compose.yml               # PostgreSQL + Bot orkestratsiyasi
├── main.py                          # Loyihaning kirish nuqtasi
├── requirements.txt                 # Tashqi kutubxonalar ro'yxati
└── .env.example                     # Muhit o'zgaruvchilari namunasi
```

---

## 🚀 O'rnatish va Ishga Tushirish

### 1-Usul: Lokal Ishga Tushirish (Development)

#### 1. Repository'ni klonlash:
```bash
git clone https://github.com/Abdulxadiy/Multiple-Service_bot.git
cd Multiple-Service_bot
```

#### 2. Virtual muhit yaratish va kutubxonalarni o'rnatish:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **Eslatma:** Ovozli xabarlarni matnga o'girish uchun tizimingizda `ffmpeg` o'rnatilgan bo'lishi kerak:
> - Ubuntu / Debian: `sudo apt update && sudo apt install -y ffmpeg`
> - Arch Linux: `sudo pacman -S ffmpeg`
> - macOS: `brew install ffmpeg`

#### 3. Sozlamalarni kiritish:
`.env.example` faylidan nusxa olib `.env` yarating:
```bash
cp .env.example .env
```
`.env` fayliga Telegram [@BotFather](https://t.me/BotFather) dan olingan bot tokeningizni kiriting:
```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
```

#### 4. Botni ishga tushirish:
```bash
python main.py
```

---

### 2-Usul: Docker & Docker Compose orqali Ishga Tushirish (Production)

Docker yordamida bot va PostgreSQL ma'lumotlar bazasini bir buyruq bilan to'liq izolyatsiyalangan holatda ishga tushirishingiz mumkin:

#### 1. Muhit parametrlarini sozlash:
```bash
cp .env.example .env
nano .env # BOT_TOKEN, ENCRYPTION_KEY va parollarni kiriting
```

#### 2. Konteynerlarni yig'ish va ishga tushirish:
```bash
docker-compose up -d --build
```

#### 3. Ishlash holatini tekshirish va loglarni kuzatish:
```bash
docker-compose logs -f bot
```

---

## ⚙️ Muhit O'zgaruvchilari (.env)

| Parametr | Majburiy | Standart qiymat | Tavsif |
| :--- | :---: | :--- | :--- |
| `BOT_TOKEN` | **Ha** | *Bo'sh* | Telegram @BotFather dan olingan bot tokeni |
| `DATABASE_URL` | Yo'q | `sqlite+aiosqlite:///bot.db` | Async database ulanish URL (PostgreSQL yoki SQLite) |
| `ENCRYPTION_KEY` | **Ha (Prod)** | `.secret_key` dan | Parollarni AES-256 shifrlash kaliti (Fernet 44-belgili) |
| `GROQ_API_KEY` | Yo'q | *Bo'sh* | Bepul Groq Whisper Large V3 API kaliti (ixtiyoriy) |
| `AUTO_DELETE_MINUTES` | Yo'q | `20` | Parollar chatdan necha daqiqada o'chirilishi |
| `ENVIRONMENT` | Yo'q | `production` | Ishlash muhiti (`production` / `development`) |
| `RATE_LIMIT_DELAY` | Yo'q | `0.5` | Anti-flood chegarasi (soniyada xabarlar oralig'i) |
| `MAX_PIN_ATTEMPTS` | Yo'q | `5` | PIN kodni ketma-ket noto'g'ri kiritish limiti |
| `PIN_LOCKOUT_MINUTES` | Yo'q | `10` | Noto'g'ri kiritilganda seyfni bloklash vaqti (daqiqa) |
| `AWS_S3_BACKUP_BUCKET`| Yo'q | *Bo'sh* | Avtomatik zaxira nusxalash uchun AWS S3 bucket nomi |

---

## 🛡 Xavfsizlik Tamoyillari

Loyiha axborot xavfsizligining eng yuqori standartlariga amal qiladi:
1. **Zero-Knowledge Encryption:** Sizning parollaringiz hatto server administratori yoki ma'lumotlar bazasiga kirish huquqiga ega shaxs uchun ham ko'rinmaydi. Ular faqatgina `ENCRYPTION_KEY` orqali ochiladi.
2. **Brute-Force va Flood Himoyasi:** 5 marta ketma-ket noto'g'ri PIN kiritilsa, seyf 10 daqiqaga to'liq bloklanadi. Har bir so'rov `ThrottlingMiddleware` filtri orqali tekshiriladi.
3. **Foydalanuvchilar To'liq Izolyatsiyasi:** Barcha ma'lumotlar faqat Telegram `user_id` bilan bog'langan. Hech bir foydalanuvchi boshqasining ma'lumotlarini ko'ra olmaydi.
4. **Chat Tozaligi:** Olingan maxfiy ma'lumotlar 20 daqiqadan so'ng chatdan yo'q qilinadi, shunda uchinchi shaxslar telefoningizni qo'liga olganda ham ma'lumotlar ochiq qolmaydi.

---

## 📄 Muallif va Litsenziya

Loyiha ochiq kodli bo'lib, **[MIT License](LICENSE)** litsenziyasi asosida tarqatiladi.

- **Dasturchi:** [Abdulxadiy Abduraximov](https://github.com/Abdulxadiy)
- **GitHub Repository:** [Multiple-Service_bot](https://github.com/Abdulxadiy/Multiple-Service_bot)
- **Savol va takliflar:** [Issues](https://github.com/Abdulxadiy/Multiple-Service_bot/issues) bo'limida qoldirishingiz mumkin.
