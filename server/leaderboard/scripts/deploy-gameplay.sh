#!/bin/bash
# Run only after deployment authorization, from the existing installation.
# No volume/config replacement, database restore or automatic deployment retry.
set -euo pipefail
umask 077
project=$(pwd -P)
test "$project" = /opt/tb-leaderboard || { printf 'Use the existing deployment directory.\n' >&2; exit 1; }
test "$#" = 2 || { printf 'Provide staged runtime and reviewed full source commit.\n' >&2; exit 1; }
stage=$(realpath -- "$1")
commit=$2
test "$stage" = "$project/runtime.next-1.4.1"
printf '%s\n' "$commit" | grep -Eq '^[0-9a-f]{40}$'
test ! -L "$stage" && test ! -L "$project/runtime"
for required in package.json BUILD-INFO.json runtime-manifest.sha256 src/gameplay.mjs src/duel-problems.json mysql/013_leader_days.sql mysql/014_shared_translations.sql mysql/015_gameplay.sql mysql/016_social_replies.sql src/sticker-rewards.mjs src/sticker-rewards.json scripts/audit-preserved-data.mjs scripts/verify-gameplay-restore.mjs; do
  test -f "$stage/$required"
done
(cd "$stage" && sha256sum --status -c runtime-manifest.sha256)
docker compose config --quiet
old_health=$(curl --fail --silent --max-time 3 http://127.0.0.1:8080/v1/health)
printf '%s' "$old_health" | grep -q '"version":"1.2.9"'
# The complete, compressed production backup must already be restored and
# rehearsed on the same MySQL version. Do not generate another raw SQL dump on
# this small production disk or retry failed backups automatically.
test -s "$stage/restore-verification.json"
backup_meta=$(docker compose run --rm --no-deps -T -v "$stage:/audit:ro" -v "$project/runtime:/baseline:ro" api node /audit/scripts/verify-gameplay-restore.mjs /audit /baseline "$commit")
read -r backup_sha backup_bytes backup_path <<< "$backup_meta"
test "$(stat -c %s -- "$backup_path")" = "$backup_bytes"
printf '%s  %s\n' "$backup_sha" "$backup_path" | sha256sum --status -c -
free_kib=$(df -Pk "$project" | awk 'NR==2 {print $4}')
test "$free_kib" -ge 262144 || { printf 'Less than 256 MiB free; existing service retained.\n' >&2; exit 1; }
stamp=$(date -u +%Y%m%dT%H%M%SZ)
evidence="$project/backups/deploy-gameplay-1.4.1-$stamp"
test ! -e "$evidence"
mkdir -m 700 "$evidence"
config_fingerprints() {
  for file in .env Caddyfile compose*.yaml compose*.yml; do
    test ! -f "$file" || sha256sum -- "$file"
  done
}
dependencies() {
  for service in mysql redis caddy; do
    id=$(docker compose ps -q "$service")
    test -n "$id"
    docker inspect --format '{{.Id}} {{json .Mounts}}' "$id"
  done
}
audit() {
  docker compose run --rm --no-deps -T -v "$1:/audit:ro" api node /audit/scripts/audit-preserved-data.mjs
}
config_fingerprints > "$evidence/config.before.sha256"
dependencies > "$evidence/dependencies.before"
docker compose run --rm --no-deps -T -v "$stage:/audit:ro" api node /audit/scripts/audit-preserved-data.mjs --stage-gameplay "$commit"
audit "$stage" > "$evidence/preflight.json"
# Retain the reviewed restore receipt and reference the existing complete backup.
# Runtime rollback never restores SQL over live data.
cp -- "$stage/restore-verification.json" "$evidence/restore-verification.json"
printf '%s  %s\n' "$backup_sha" "$backup_path" > "$evidence/mysql-online.sha256"
backup="$evidence/runtime.before"
stopped=0
restore_runtime() {
  result=$?
  trap - EXIT INT TERM
  if [ "$result" -ne 0 ] && [ "$stopped" = 1 ]; then
    recovered=1
    docker compose stop --timeout 30 api || recovered=0
    if [ -d "$backup" ]; then
      if [ -e "$project/runtime" ]; then mv -- "$project/runtime" "$evidence/runtime.failed" || recovered=0; fi
      if [ ! -e "$project/runtime" ]; then mv -- "$backup" "$project/runtime" || recovered=0; else recovered=0; fi
    fi
    docker compose up --no-build --no-deps -d api || recovered=0
    if [ "$recovered" = 1 ]; then
      printf 'Previous runtime restored. Existing database, additive tables and all evidence retained.\n' >&2
    else
      printf 'Operator recovery needed; original database was not overwritten. Evidence: %s\n' "$evidence" >&2
    fi
  fi
  exit "$result"
}
trap restore_runtime EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
stopped=1
docker compose stop --timeout 30 api
audit "$stage" > "$evidence/fingerprint.before.json"
for migration in 013_leader_days.sql 014_shared_translations.sql 015_gameplay.sql 016_social_replies.sql; do
  docker compose exec -T mysql sh -c 'MYSQL_PWD="$(cat /run/secrets/mysql_root_password)" exec mysql -u root tb_leaderboard' < "$stage/mysql/$migration"
done
audit "$stage" > "$evidence/fingerprint.after.json"
(cat "$evidence/fingerprint.before.json"; cat "$evidence/fingerprint.after.json") |
  docker compose run --rm --no-deps -T -v "$stage:/audit:ro" api node /audit/scripts/audit-preserved-data.mjs --compare-admin > "$evidence/preservation.log"
mv -- "$project/runtime" "$backup"
mv -- "$stage" "$project/runtime"
docker compose up --no-build --no-deps -d api
attempt=0
until health=$(curl --fail --silent --max-time 3 http://127.0.0.1:8080/v1/health) &&
  printf '%s' "$health" | grep -q '"ok":true' &&
  printf '%s' "$health" | grep -q '"version":"1.4.1"' &&
  printf '%s' "$health" | grep -q '"accountStateProtocol":1' &&
  printf '%s' "$health" | grep -q '"gameplayProtocol":1'; do
  attempt=$((attempt+1))
  test "$attempt" -lt 20
  sleep 1
done
printf '%s\n' "$health" > "$evidence/health.json"
config_fingerprints > "$evidence/config.after.sha256"
cmp -s "$evidence/config.before.sha256" "$evidence/config.after.sha256"
dependencies > "$evidence/dependencies.after"
cmp -s "$evidence/dependencies.before" "$evidence/dependencies.after"
printf '%s\n' "$commit" > "$evidence/source-commit"
trap - EXIT INT TERM
printf 'Shared runtime 1.4.1 healthy; original data/config/volumes preserved. Evidence: %s\n' "$evidence"
