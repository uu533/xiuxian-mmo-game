#!/bin/bash
# Xiuxian MMO Game - SQLite Backup Script
# Usage: ./backup_sqlite.sh
# Requires: rsync (optional for remote backup), standard bash tools
# Backup path: /home/ubuntu/xiuxian-backups/
# Retention: keeps last 14 days

set -euo pipefail

# === Configuration ===
BACKUP_ROOT="${BACKUP_ROOT:-/home/ubuntu/xiuxian-backups}"
PROJECT_ROOT="${PROJECT_ROOT:-/opt/xiuxian-game/app}"
DB_FILE="game.db"
RETENTION_DAYS=14

# === Sanity Checks ===
if [[ ! -f "${PROJECT_ROOT}/${DB_FILE}" ]]; then
    echo "ERROR: Database file not found at ${PROJECT_ROOT}/${DB_FILE}" >&2
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_ROOT}"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="xiuxian_backup_${TIMESTAMP}.db"
BACKUP_PATH="${BACKUP_ROOT}/${BACKUP_NAME}"

# === Backup ===
echo "Backing up ${PROJECT_ROOT}/${DB_FILE} to ${BACKUP_PATH}"
cp "${PROJECT_ROOT}/${DB_FILE}" "${BACKUP_PATH}"

# Verify backup integrity
if ! sqlite3 "${BACKUP_PATH}" "PRAGMA integrity_check;" > /dev/null 2>&1; then
    echo "ERROR: Backup integrity check failed!" >&2
    rm -f "${BACKUP_PATH}"
    exit 1
fi

echo "Backup created successfully: ${BACKUP_PATH}"

# === Cleanup old backups ===
echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_ROOT}" -name "xiuxian_backup_*.db" -type f -mtime "+${RETENTION_DAYS}" -delete
echo "Cleanup done."

# Report backup count
BACKUP_COUNT=$(find "${BACKUP_ROOT}" -name "xiuxian_backup_*.db" -type f | wc -l)
echo "Current backup count: ${BACKUP_COUNT}"