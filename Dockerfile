# 1. Yengil va xavfsiz rasmiy Python bazaviy obraz
FROM python:3.11-slim

# Muhit o'zgaruvchilari: Python stdout/stderr buferlanmasligi va pyc fayllar yozilmasligi
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Ishchi papka
WORKDIR /app

# Tizim paketlarini yangilash va kerakli kutubxonalarni o'rnatish
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Talablar faylini nusxalash va o'rnatish
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha kodlarini nusxalash
COPY . /app/

# Xavfsizlik: Root bo'lmagan cheklangan foydalanuvchi yaratish (Non-root user)
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

USER botuser

# Botni ishga tushirish
CMD ["python", "main.py"]
