#!/bin/bash
# Odoo Backup — Platinum Tier Cloud VM
# Daily cron: 0 2 * * * /home/ubuntu/fte-project/scripts/backup-odoo.sh
# Retains: 7 daily + 4 weekly backups

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
DATE=$(date +%Y%m%d)
DAY_OF_WEEK=$(date +%u)  # 1=Monday, 7=Sunday
LOG="/var/log/fte/odoo-backup.log"

mkdir -p "$BACKUP_DIR/daily" "$BACKUP_DIR/weekly"

echo "=== Odoo Backup — $(date -u) ===" >> "$LOG"

# Database backup
echo "Backing up database..." >> "$LOG"
docker exec odoo-db pg_dump -U odoo odoo > "$BACKUP_DIR/daily/odoo_${DATE}.sql" 2>> "$LOG"

if [ $? -eq 0 ]; then
    echo "Database backup: OK ($BACKUP_DIR/daily/odoo_${DATE}.sql)" >> "$LOG"
else
    echo "ERROR: Database backup failed!" >> "$LOG"
    exit 1
fi

# Filestore backup
echo "Backing up filestore..." >> "$LOG"
docker cp odoo-web:/var/lib/odoo/filestore - 2>/dev/null | gzip > "$BACKUP_DIR/daily/odoo_filestore_${DATE}.tar.gz" 2>> "$LOG"
echo "Filestore backup: OK" >> "$LOG"

# Weekly backup (on Sunday)
if [ "$DAY_OF_WEEK" -eq 7 ]; then
    cp "$BACKUP_DIR/daily/odoo_${DATE}.sql" "$BACKUP_DIR/weekly/odoo_weekly_${DATE}.sql"
    cp "$BACKUP_DIR/daily/odoo_filestore_${DATE}.tar.gz" "$BACKUP_DIR/weekly/odoo_filestore_weekly_${DATE}.tar.gz"
    echo "Weekly backup created" >> "$LOG"
fi

# Cleanup: keep 7 daily backups
find "$BACKUP_DIR/daily" -name "odoo_*.sql" -mtime +7 -delete 2>/dev/null
find "$BACKUP_DIR/daily" -name "odoo_filestore_*.tar.gz" -mtime +7 -delete 2>/dev/null

# Cleanup: keep 4 weekly backups
find "$BACKUP_DIR/weekly" -name "odoo_weekly_*.sql" -mtime +28 -delete 2>/dev/null
find "$BACKUP_DIR/weekly" -name "odoo_filestore_weekly_*.tar.gz" -mtime +28 -delete 2>/dev/null

echo "Cleanup done. Backup complete." >> "$LOG"
