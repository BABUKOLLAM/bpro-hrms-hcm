#!/usr/bin/env bash
# Restores a database + filestore from a backup produced by
# backup_db.sh. DESTRUCTIVE: drops the target database first if it
# already exists. Always test a restore on a throwaway database name
# before you ever need to do it for real - a backup you haven't
# rehearsed restoring is not a verified backup.
#
# Usage: scripts/restore_db.sh <backup_dir> <target_db_name>
# Example: scripts/restore_db.sh backups/acme_prod_20260401_020000 acme_prod_restored

set -euo pipefail

BACKUP_DIR="${1:?Usage: restore_db.sh <backup_dir> <target_db_name>}"
TARGET_DB="${2:?Usage: restore_db.sh <backup_dir> <target_db_name>}"

if [ ! -f "${BACKUP_DIR}/db.dump" ]; then
    echo "No db.dump found in ${BACKUP_DIR} - is this a valid backup directory?" >&2
    exit 1
fi

read -r -p "This will DROP database '${TARGET_DB}' if it exists, then restore from ${BACKUP_DIR}. Continue? [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Aborted."
    exit 1
fi

echo "[$(date)] Dropping '${TARGET_DB}' if it exists..."
docker compose exec -T db dropdb -U odoo --if-exists "$TARGET_DB"

echo "[$(date)] Creating '${TARGET_DB}'..."
docker compose exec -T db createdb -U odoo "$TARGET_DB"

echo "[$(date)] Restoring database dump..."
docker compose exec -T db pg_restore -U odoo -d "$TARGET_DB" --no-owner < "${BACKUP_DIR}/db.dump"

if [ -f "${BACKUP_DIR}/filestore.tar.gz" ]; then
    echo "[$(date)] Restoring filestore..."
    docker compose exec -T odoo rm -rf "/var/lib/odoo/filestore/${TARGET_DB}"
    # The archive's top-level folder is named after the ORIGINAL
    # database, not necessarily TARGET_DB (e.g. restoring a prod
    # backup into a differently-named scratch DB to verify it) -
    # extract to a temp name, then move into place under the target
    # name so the filestore path Odoo expects always matches.
    docker compose exec -T odoo mkdir -p /tmp/restore_filestore
    docker compose exec -T odoo tar -xzf - -C /tmp/restore_filestore < "${BACKUP_DIR}/filestore.tar.gz"
    ORIGINAL_NAME=$(docker compose exec -T odoo bash -c "ls /tmp/restore_filestore | head -1" | tr -d '\r')
    docker compose exec -T odoo mv "/tmp/restore_filestore/${ORIGINAL_NAME}" "/var/lib/odoo/filestore/${TARGET_DB}"
    docker compose exec -T odoo rm -rf /tmp/restore_filestore
else
    echo "[$(date)] No filestore.tar.gz in backup - attachments/PDFs will be missing after restore."
fi

echo "[$(date)] Restore complete. Log in and verify before treating '${TARGET_DB}' as trustworthy."
