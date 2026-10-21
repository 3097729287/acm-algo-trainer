#!/bin/sh
# Run on the existing /opt/tb-leaderboard runtime deployment, after review.
# Upgrade an existing 1.0.20 deployment without changing its data volumes.
# Usage: sh runtime.next-1.1.2/scripts/deploy-account-sync.sh runtime.next-1.1.2
set -eu
umask 077
project=$(pwd -P)
test "$project" = /opt/tb-leaderboard || { printf 'Run from /opt/tb-leaderboard.\n' >&2; exit 1; }
test "$#" = 1 || { printf 'Provide the staged runtime directory.\n' >&2; exit 1; }
stage=$(realpath -- "$1")
case "$stage" in "$project"/runtime.next-*) ;; *) printf 'Stage must be a runtime.next-* directory inside the project.\n' >&2; exit 1;; esac
test -f runtime/src/server.mjs
test -f "$stage/src/account-state.mjs"
test -f "$stage/mysql/006_public_progress.sql"
test -f "$stage/src/public-progress.mjs"
test -f "$stage/mysql/007_unique_nicknames.sql"
test -f "$stage/scripts/migrate-nicknames.mjs"
version=$(sed -n 's/.*"version": *"\([0-9.]*\)".*/\1/p' "$stage/package.json" | head -n 1)
test -n "$version"
if [ "$version" = 1.2.0 ]; then
  printf 'Use deploy-social.sh STAGE EXPECTED_SOURCE_COMMIT for 1.2.0 and migration 008.\n' >&2
  exit 1
fi
test -f "$stage/Caddyfile"
test -f "$stage/runtime-manifest.sha256"
(cd "$stage" && sha256sum --status -c runtime-manifest.sha256)
# Do not replace custom TLS/proxy settings. Only exact reviewed templates
# (allowing CRLF) may be upgraded automatically.
test -f "$project/Caddyfile"
legacy_caddy_sha=af785d6eba30d1713abbc2a86194787d998bda0c3ac0cd19a41f94bdef190b5f
caddy_digest() { tr -d '\015' < "$1" | sha256sum | cut -d ' ' -f 1; }
current_caddy_sha=$(caddy_digest "$project/Caddyfile")
next_caddy_sha=$(caddy_digest "$stage/Caddyfile")
if [ "$current_caddy_sha" != "$legacy_caddy_sha" ] && [ "$current_caddy_sha" != "$next_caddy_sha" ]; then
  printf 'Caddyfile differs from reviewed templates; review custom TLS/proxy settings before deployment.\n' >&2
  exit 1
fi

docker compose config --quiet
# Refuse an older/incomplete database before taking the live API down. This
# upgrade only adds 006; it never resets cloud snapshots or existing sessions.
docker compose exec -T mysql sh -c 'MYSQL_PWD="$(cat /run/secrets/mysql_root_password)" exec mysql -u root tb_leaderboard' <<'SQL'
SELECT 1 FROM account_state LIMIT 0;
SELECT 1 FROM account_login_days LIMIT 0;
SQL
sh scripts/backup.sh
stamp=$(date -u +%Y%m%dT%H%M%SZ)
backup="$project/backups/runtime-before-$version-$stamp"
proxy_backup="$project/backups/Caddyfile-before-$version-$stamp"
test ! -e "$backup"
test ! -e "$proxy_backup"
cp -- "$project/Caddyfile" "$proxy_backup"
chmod 600 "$proxy_backup"
stopped=0
proxy_changed=0
restore() {
  result=$?
  trap - EXIT INT TERM
  if [ "$result" -ne 0 ]; then
    rollback_ok=1
    if [ "$proxy_changed" = 1 ]; then
      # Write through the existing bind-mounted file, preserving its inode.
      if cp -- "$proxy_backup" "$project/Caddyfile"; then
        docker compose exec -T caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile &&
          docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile || rollback_ok=0
      else
        rollback_ok=0
      fi
    fi
    if [ "$stopped" = 1 ]; then
      # The directory also covers interruption immediately after the rename.
      if [ -d "$backup" ]; then
        docker compose stop api || rollback_ok=0
        failed="$project/backups/runtime-failed-account-sync-$(date -u +%Y%m%dT%H%M%SZ)"
        if [ -e "$project/runtime" ]; then
          if [ ! -e "$failed" ]; then
            mv -- "$project/runtime" "$failed" || rollback_ok=0
          else
            rollback_ok=0
          fi
        fi
        if [ ! -e "$project/runtime" ]; then
          mv -- "$backup" "$project/runtime" || rollback_ok=0
        else
          rollback_ok=0
        fi
      fi
      docker compose up --no-build --no-deps -d api || rollback_ok=0
    fi
    if [ "$rollback_ok" = 1 ]; then
      printf 'Deployment failed; previous runtime and Caddyfile restored. Additive tables and backups remain.\n' >&2
    else
      printf 'Deployment failed; automatic recovery needs operator review. Private recovery files remain under backups/.\n' >&2
    fi
  fi
  exit "$result"
}
trap restore EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
stopped=1
docker compose stop api
docker compose exec -T mysql sh -c 'MYSQL_PWD="$(cat /run/secrets/mysql_root_password)" exec mysql -u root tb_leaderboard' < "$stage/mysql/006_public_progress.sql"
docker compose exec -T mysql sh -c 'MYSQL_PWD="$(cat /run/secrets/mysql_root_password)" exec mysql -u root tb_leaderboard' < "$stage/mysql/007_unique_nicknames.sql"
mv -- "$project/runtime" "$backup"
mv -- "$stage" "$project/runtime"
docker compose run --rm --no-deps api node scripts/migrate-nicknames.mjs
# Preserve all existing overlays and never recreate the database dependencies.
docker compose up --no-build --no-deps -d api
attempt=0
until health=$(curl --fail --silent --max-time 2 http://127.0.0.1:8080/v1/health) &&
  printf '%s' "$health" | grep -q "\"version\":\"$version\"" &&
  printf '%s' "$health" | grep -q '"publicProgressProtocol":1'; do
  attempt=$((attempt+1))
  test "$attempt" -lt 15
  sleep 1
done
if [ "$current_caddy_sha" != "$next_caddy_sha" ]; then
  proxy_changed=1
  cp -- "$project/runtime/Caddyfile" "$project/Caddyfile"
  docker compose exec -T caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
  docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
fi
cp -- "$project/runtime/mysql/006_public_progress.sql" "$project/mysql/006_public_progress.sql"
chmod 644 "$project/mysql/006_public_progress.sql"
cp -- "$project/runtime/mysql/007_unique_nicknames.sql" "$project/mysql/007_unique_nicknames.sql"
chmod 644 "$project/mysql/007_unique_nicknames.sql"
trap - EXIT INT TERM
printf 'TB %s is healthy. Accounts, snapshots, sessions and data volumes preserved; nicknames reserved.\n' "$version"
