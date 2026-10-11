#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
umask 077
mkdir -p backups
output="backups/mysql-$(date -u +%Y%m%dT%H%M%SZ).sql"
if [ -e "$output" ] || [ -e "$output.gz" ]; then
  printf 'Backup destination already exists.\n' >&2
  exit 1
fi
trap 'rm -f "$output.part"' EXIT
docker compose exec -T mysql sh -c 'MYSQL_PWD="$(cat /run/secrets/mysql_root_password)" exec mysqldump -u root --single-transaction --routines --triggers --no-tablespaces --set-gtid-purged=OFF tb_leaderboard' > "$output.part"
test -s "$output.part"
mv "$output.part" "$output"
gzip "$output"
printf 'Backup saved: %s.gz\n' "$output"
