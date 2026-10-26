#!/bin/sh
# Existing 001–009 runtime installation only. No database/config replacement.
# Usage from /opt/tb-leaderboard:
# sh runtime.next-1.2.4/scripts/deploy-training-list-likes.sh runtime.next-1.2.4 REVIEWED_COMMIT
set -eu
umask 077
project=$(pwd -P)
test "$project" = /opt/tb-leaderboard || { printf 'Run from /opt/tb-leaderboard.\n' >&2; exit 1; }
test "$#" = 2 || { printf 'Provide staged runtime and reviewed full Git commit.\n' >&2; exit 1; }
stage=$(realpath -- "$1")
commit=$2
case "$stage" in "$project"/runtime.next-1.2.4) ;; *) printf 'Unexpected stage path.\n' >&2; exit 1;; esac
printf '%s\n' "$commit" | grep -Eq '^[0-9a-f]{40}$'
test ! -L "$stage"
test ! -L "$project/runtime"
test -f runtime/src/server.mjs
for required in package.json BUILD-INFO.json runtime-manifest.sha256 mysql/010_training_list_likes.sql scripts/audit-preserved-data.mjs; do
  test -f "$stage/$required"
done
version=$(sed -n 's/.*"version": *"\([0-9.]*\)".*/\1/p' "$stage/package.json" | head -n 1)
test "$version" = 1.2.4
(cd "$stage" && sha256sum --status -c runtime-manifest.sha256)
docker compose config --quiet
stamp=$(date -u +%Y%m%dT%H%M%SZ)
evidence="$project/backups/deploy-training-list-likes-$version-$stamp"
test ! -e "$evidence"
mkdir -m 700 "$evidence"
mkdir -m 700 "$evidence/config"
config_fingerprints() {
  for file in .env Caddyfile compose*.yaml compose*.yml; do
    test ! -f "$file" || sha256sum -- "$file"
  done
}
config_fingerprints > "$evidence/config.sha256"
for file in .env Caddyfile compose*.yaml compose*.yml; do
  test ! -f "$file" || cp -p -- "$file" "$evidence/config/"
done
# Keep dependencies and their persistent-volume bindings fixed throughout.
dependencies() {
  for service in mysql redis caddy; do
    id=$(docker compose ps -q "$service")
    test -n "$id"
    docker inspect --format '{{.Id}} {{json .Mounts}}' "$id"
  done
}
dependencies > "$evidence/dependencies.before"
audit() {
  docker compose run --rm --no-deps -T -v "$1:/audit:ro" api node /audit/scripts/audit-preserved-data.mjs
}
verify_preserved() {
  (cat "$evidence/fingerprint.before.json"; cat "$evidence/fingerprint.after.json") |
    docker compose run --rm --no-deps -T -v "$1:/audit:ro" api node /audit/scripts/audit-preserved-data.mjs --compare
}
# Validate source identity and old schema while the current API is still up.
docker compose run --rm --no-deps -T -v "$stage:/audit:ro" api node /audit/scripts/audit-preserved-data.mjs --stage "$commit"
audit "$stage" > "$evidence/fingerprint.preflight.json"
# mysqldump is online and consistent; committed activity remains in the original
# live database. Never restore this dump automatically over newer user writes.
sh scripts/backup.sh > "$evidence/online-backup.log"
dump=$(sed -n 's/^Backup saved: //p' "$evidence/online-backup.log")
case "$dump" in backups/mysql-*.sql.gz) ;; *) printf 'Online backup receipt is invalid.\n' >&2; exit 1;; esac
test -s "$dump"
gzip -t -- "$dump"
sha256sum -- "$dump" > "$evidence/online-backup.sha256"
backup="$evidence/runtime.before"
stopped=0
restore() {
  result=$?
  trap - EXIT INT TERM
  if [ "$result" -ne 0 ] && [ "$stopped" = 1 ]; then
    recovered=1
    docker compose stop api || recovered=0
    if [ -d "$backup" ]; then
      if [ -e "$project/runtime" ]; then
        mv -- "$project/runtime" "$evidence/runtime.failed" || recovered=0
      fi
      if [ ! -e "$project/runtime" ]; then mv -- "$backup" "$project/runtime" || recovered=0; else recovered=0; fi
    fi
    docker compose up --no-build --no-deps -d api || recovered=0
    if [ "$recovered" = 1 ]; then
      printf 'Deployment failed; previous API restored. Original database, additive tables and private evidence retained.\n' >&2
    else
      printf 'Deployment failed; operator recovery required. Private evidence retained at %s.\n' "$evidence" >&2
    fi
  fi
  exit "$result"
}
trap restore EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
stopped=1
docker compose stop --timeout 30 api
# Freeze evidence only after in-flight requests have drained. The second
# fingerprint is checked before the new API can settle rewards or accept work.
audit "$stage" > "$evidence/fingerprint.before.json"
docker compose exec -T mysql sh -c 'MYSQL_PWD="$(cat /run/secrets/mysql_root_password)" exec mysql -u root tb_leaderboard' < "$stage/mysql/010_training_list_likes.sql"
audit "$stage" > "$evidence/fingerprint.after.json"
verify_preserved "$stage" > "$evidence/preservation-check.log"
mv -- "$project/runtime" "$backup"
mv -- "$stage" "$project/runtime"
docker compose up --no-build --no-deps -d api
attempt=0
until health=$(curl --fail --silent --max-time 3 http://127.0.0.1:8080/v1/health) &&
  printf '%s' "$health" | grep -q '"ok":true' &&
  printf '%s' "$health" | grep -q '"version":"1.2.4"' &&
  printf '%s' "$health" | grep -q '"accountStateProtocol":1' &&
  printf '%s' "$health" | grep -q '"publicProgressProtocol":1' &&
  printf '%s' "$health" | grep -q '"socialProtocol":1' &&
  printf '%s' "$health" | grep -q '"publicAppearanceProtocol":1' &&
  printf '%s' "$health" | grep -q '"trainingListLikesProtocol":1'; do
  attempt=$((attempt+1))
  test "$attempt" -lt 20
  sleep 1
done
printf '%s\n' "$health" > "$evidence/health.json"
config_fingerprints > "$evidence/config.after.sha256"
cmp -s "$evidence/config.sha256" "$evidence/config.after.sha256"
dependencies > "$evidence/dependencies.after"
cmp -s "$evidence/dependencies.before" "$evidence/dependencies.after"
cp -- "$project/runtime/mysql/010_training_list_likes.sql" "$project/mysql/010_training_list_likes.sql"
chmod 644 "$project/mysql/010_training_list_likes.sql"
printf '%s\n' "$commit" > "$evidence/source-commit"
trap - EXIT INT TERM
printf 'TB %s healthy with publicAppearanceProtocol 1. Preserved data fingerprints match; original config, dependencies and volumes retained.\nEvidence: %s\n' "$version" "$evidence"
