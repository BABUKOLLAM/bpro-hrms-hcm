#!/usr/bin/env bash
# Backs up the running Postgres database (and, optionally, the Odoo
# filestore — attachments, generated PDFs) to a timestamped archive
# under backups/. Intended to be run from a daily cron job; this
# script does not itself schedule anything.
#
# Usage: scripts/backup_db.sh <db_name> [backups_dir]
#
# Example crontab entry (daily at 02:00, keeping the repo's own
# backups/ directory - point BACKUP_DIR elsewhere if you'd rather
# back up to separate storage, e.g. an attached volume or object
# storage synced by a separate tool):
#   0 2 * * * cd /path/to/bpro-hrms-hcm && ./scripts/backup_db.sh <db_name> >> /var/log/bpro-backup.log 2>&1

set -euo pipefail

DB_NAME="${1:?Usage: backup_db.sh <db_name> [backups_dir]}"
BACKUP_DIR="${2:-$(dirname "$0")/../backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DEST="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}"

mkdir -p "$DEST"

echo "[$(date)] Backing up database '${DB_NAME}' to ${DEST}"

# Database dump - custom format (-Fc) so it can be restored selectively
# and is already compressed, unlike a plain SQL dump.
docker compose exec -T db pg_dump -U odoo -Fc "$DB_NAME" > "${DEST}/db.dump"

# Filestore - attachments, generated payslip/letter/report PDFs live
# on disk, not in Postgres. Back it up alongside the DB dump so a
# restore is actually complete, not just the rows.
if docker compose exec -T odoo test -d "/var/lib/odoo/filestore/${DB_NAME}"; then
    docker compose exec -T odoo tar -czf - -C /var/lib/odoo/filestore "$DB_NAME" \
        > "${DEST}/filestore.tar.gz"
else
    echo "[$(date)] No filestore directory found for '${DB_NAME}' - skipping (nothing uploaded yet?)"
fi

echo "[$(date)] Backup complete: ${DEST}"

# Prune backups older than 30 days - adjust the retention window to
# the client's actual policy (and to your available storage).
find "$BACKUP_DIR" -maxdepth 1 -type d -name "${DB_NAME}_*" -mtime +30 -exec rm -rf {} \;
