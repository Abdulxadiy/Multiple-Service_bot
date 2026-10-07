#!/usr/bin/env bash
# ==============================================================================
# Multiple-Service Bot - PostgreSQL Avtomatik Zaxira Nusxalash (Backup) Skripti
# ==============================================================================
# Ushbu skriptni Linux cron job ga qo'yish mumkin (masalan har kecha 03:00 da):
# 0 3 * * * /app/scripts/backup_db.sh >> /var/log/db_backup.log 2>&1
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/tmp/bot_backups}"
mkdir -p "${BACKUP_DIR}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/botdb_backup_${TIMESTAMP}.sql.gz"

DB_CONTAINER="${DB_CONTAINER:-multiple_bot_db}"
DB_USER="${POSTGRES_USER:-botuser}"
DB_NAME="${POSTGRES_DB:-botdb}"

echo "[$(date)] 🚀 Ma'lumotlar bazasi zaxira nusxasi olinmoqda..."

# Docker orqali yoki to'g'ridan-to'g'ri pg_dump
if command -v docker &> /dev/null && docker ps | grep -q "${DB_CONTAINER}"; then
    docker exec "${DB_CONTAINER}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" | gzip > "${BACKUP_FILE}"
else
    pg_dump "${DATABASE_URL:-postgresql://${DB_USER}@localhost:5432/${DB_NAME}}" | gzip > "${BACKUP_FILE}"
fi

echo "[$(date)] ✅ Zaxira nusxa yaratildi: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"

# Agar AWS S3 bucket ko'rsatilgan bo'lsa, S3 ga yuklash
if [ -n "${AWS_S3_BACKUP_BUCKET:-}" ]; then
    echo "[$(date)] ☁️ AWS S3 ga yuklanmoqda: s3://${AWS_S3_BACKUP_BUCKET}/"
    aws s3 cp "${BACKUP_FILE}" "s3://${AWS_S3_BACKUP_BUCKET}/backups/"
    echo "[$(date)] ✅ AWS S3 ga muvaffaqiyatli yuklandi!"
fi

# 7 kundan eski lokal zaxiralarni tozalash (disk to'lib ketmasligi uchun)
find "${BACKUP_DIR}" -type f -name "botdb_backup_*.sql.gz" -mtime +7 -delete
echo "[$(date)] 🧹 7 kundan eski zaxira fayllar tozalandi."
