#!/usr/bin/env bash
# Existing 1.4.3 runtime installation only; no schema migration. No database/config replacement.
# Usage from /opt/tb-leaderboard:
# bash runtime.next-1.4.3/scripts/deploy-card-packs.sh runtime.next-1.4.3 REVIEWED_COMMIT VERIFIED_REMOTE_RECEIPT_PREFIX
set -euo pipefail
umask 077
project=$(pwd -P)
test "$project" = /opt/tb-leaderboard || { printf 'Run from /opt/tb-leaderboard.\n' >&2; exit 1; }
test "$#" = 3 || { printf 'Provide staged runtime, reviewed commit and verified external backup receipt.\n' >&2; exit 1; }
stage=$(realpath -- "$1")
commit=$2
case "$stage" in "$project"/runtime.next-1.4.3) ;; *) printf 'Unexpected stage path.\n' >&2; exit 1;; esac
printf '%s\n' "$commit" | grep -Eq '^[0-9a-f]{40}$'
test ! -L "$stage"
test ! -L "$project/runtime"
test -f runtime/src/server.mjs
test -f Caddyfile && test ! -L Caddyfile
for required in package.json BUILD-INFO.json runtime-manifest.sha256 mysql/011_account_chunks.sql scripts/audit-preserved-data.mjs; do
  test -f "$stage/$required"
done
version=$(sed -n 's/.*"version": *"\([0-9.]*\)".*/\1/p' "$stage/package.json" | head -n 1)
test "$version" = 1.4.3
(cd "$stage" && sha256sum --status -c runtime-manifest.sha256)
docker compose config --quiet
stamp=$(date -u +%Y%m%dT%H%M%SZ)
evidence="$project/backups/deploy-feedback-$version-$stamp"
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
docker compose run --rm --no-deps -T -v "$stage:/audit:ro" api node /audit/scripts/audit-preserved-data.mjs --stage-packs "$commit"
audit "$stage" > "$evidence/fingerprint.preflight.json"
# The fresh consistent dump is streamed off-server before this script runs.
# Match its remote producer receipt with the locally verified SHA-256; never
# attempt a large local backup on a full service disk.
receipt=$3
case "$receipt" in "$project"/backups/service-*) ;; *) exit 1;; esac
test -f "$receipt.sha256" && test ! -L "$receipt.sha256"
test -f "$receipt.bytes" && test ! -L "$receipt.bytes"
printf '%s\n' "${TB_VERIFIED_BACKUP_SHA256:-}" | grep -Eq '^[0-9a-f]{64}$'
actual_backup=$(cut -d ' ' -f 1 "$receipt.sha256")
test "$actual_backup" = "$TB_VERIFIED_BACKUP_SHA256"
cp -p -- "$receipt.sha256" "$evidence/online-backup.sha256"
cp -p -- "$receipt.bytes" "$evidence/online-backup.bytes"
docker compose run --rm --no-deps -T --user root -v "$stage:/candidate:ro" -v "$evidence:/evidence" -v "$project/Caddyfile:/current/Caddyfile:ro" api node /candidate/scripts/prepare-release-stream-proxy.mjs /current/Caddyfile /evidence/Caddyfile.next
docker compose run --rm --no-deps -T -v "$evidence/Caddyfile.next:/candidate/Caddyfile:ro" caddy caddy validate --config /candidate/Caddyfile --adapter caddyfile
backup="$evidence/runtime.before"
stopped=0
config_changed=0
restore() {
  result=$?
  trap - EXIT INT TERM
  if [ "$result" -ne 0 ] && [ "$stopped" = 1 ]; then
    recovered=1
    if [ "$config_changed" = 1 ]; then
      cat -- "$evidence/config/Caddyfile" > "$project/Caddyfile" || recovered=0
      docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile || recovered=0
    fi
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
# Transport-only update; no schema or record changes.
audit "$stage" > "$evidence/fingerprint.after.json"
verify_preserved "$stage" > "$evidence/preservation-check.log"
mv -- "$project/runtime" "$backup"
mv -- "$stage" "$project/runtime"
config_changed=1
cat -- "$evidence/Caddyfile.next" > "$project/Caddyfile"
docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
docker compose up --no-build --no-deps -d api
attempt=0
until health=$(curl --fail --silent --max-time 3 http://127.0.0.1:8080/v1/health) &&
  printf '%s' "$health" | grep -q '"ok":true' &&
  printf '%s' "$health" | grep -q '"version":"1.4.3"' &&
  printf '%s' "$health" | grep -q '"accountStateProtocol":1' &&
  printf '%s' "$health" | grep -q '"publicProgressProtocol":1' &&
  printf '%s' "$health" | grep -q '"socialProtocol":1' &&
  printf '%s' "$health" | grep -q '"publicAppearanceProtocol":1' &&
  printf '%s' "$health" | grep -q '"trainingListLikesProtocol":1' &&
  printf '%s' "$health" | grep -q '"accountChunkProtocol":2' &&
  printf '%s' "$health" | grep -q '"originalAvatarProtocol":1'; do
  attempt=$((attempt+1))
  test "$attempt" -lt 20
  sleep 1
done
printf '%s\n' "$health" > "$evidence/health.json"
config_fingerprints > "$evidence/config.after.sha256"
# Only the reviewed public release stream route may change the Caddyfile.
expected_proxy=$(sha256sum -- "$evidence/Caddyfile.next" | cut -d ' ' -f 1)
actual_proxy=$(sha256sum -- Caddyfile | cut -d ' ' -f 1)
test "$expected_proxy" = "$actual_proxy"
grep -v '  Caddyfile$' "$evidence/config.sha256" > "$evidence/config.other.before.sha256"
grep -v '  Caddyfile$' "$evidence/config.after.sha256" > "$evidence/config.other.after.sha256"
cmp -s "$evidence/config.other.before.sha256" "$evidence/config.other.after.sha256"
dependencies > "$evidence/dependencies.after"
cmp -s "$evidence/dependencies.before" "$evidence/dependencies.after"
printf '%s\n' "$commit" > "$evidence/source-commit"
trap - EXIT INT TERM
printf 'TB %s healthy with publicAppearanceProtocol 1. Preserved data fingerprints match; only the reviewed public release stream route changed. Other configuration, dependencies and volumes retained.\nEvidence: %s\n' "$version" "$evidence"
