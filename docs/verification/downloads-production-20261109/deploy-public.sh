#!/bin/sh
set -eu
umask 077
project=/opt/tb-leaderboard
stage=$project/runtime.next-downloads-c2b754eb
evidence=$project/backups/downloads-deploy-20261109-c2b754eb
cd "$project"
test "$(pwd -P)" = "$project"
test "$(realpath "$stage")" = "$stage"
test ! -L "$stage" && test ! -L runtime
test -f Caddyfile && test ! -L Caddyfile
sha256sum --status -c "$evidence/public-before.sha256"
test "$(stat -c '%i' Caddyfile)" = "$(cat "$evidence/caddy-inode.before")"
available=$(df -Pk . | awk 'NR==2 {print $4}')
test "$available" -gt 262144
chmod 755 "$stage" "$stage/src"
chmod 644 "$stage"/*.json "$stage"/src/*.mjs "$stage/Caddyfile" "$stage/runtime-manifest.sha256" "$stage/required-original.zip"
docker run --rm --network none -v "$stage:/candidate:ro" -v "$evidence:/before:ro" node:24-bookworm-slim node /candidate/validate-payload.mjs > "$evidence/payload-validation.json"
for file in server.mjs release-stream.mjs required-downloads.mjs; do
 docker run --rm --network none -v "$stage:/candidate:ro" node:24-bookworm-slim node --check "/candidate/src/$file"
done
docker cp "$stage/Caddyfile" tb-leaderboard-caddy-1:/tmp/downloads-candidate-c2b754eb.Caddyfile
docker exec tb-leaderboard-caddy-1 caddy validate --config /tmp/downloads-candidate-c2b754eb.Caddyfile --adapter caddyfile > "$evidence/caddy-validation.txt" 2>&1
cp -p /tmp/tb-downloads-preflight-c2b754eb.sh "$evidence/preflight-public.sh"
cp -p "$stage/deploy-public.sh" "$evidence/deploy-public.sh"
cp -p "$stage/deployment-manifest.json" "$evidence/deployment-manifest.json"
changed=0
caddy_changed=0
rollback() {
 result=$?
 trap - EXIT INT TERM
 if test "$result" -ne 0 && test "$changed" = 1; then
  for file in src/server.mjs src/release-stream.mjs public-release-assets.json runtime-manifest.sha256; do
   name=$(printf 'runtime/%s' "$file" | tr / _)
   cat "$evidence/$name.before" > "runtime/$file"
  done
  if test "$caddy_changed" = 1; then
   cat "$evidence/Caddyfile.before" > Caddyfile
   docker exec tb-leaderboard-caddy-1 caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile || true
  fi
  docker restart --time 30 tb-leaderboard-api-1 > "$evidence/rollback-api-restart.txt" || true
  printf 'Public program rollback requested; original private data and inactive reviewed input retained.\n' >&2
 fi
 exit "$result"
}
trap rollback EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
sha=500178587e4c656cf2ef1b5ab009a1ce5d47d48a356a2004e7b65364052129b6
test ! -L runtime/required-downloads
mkdir -p runtime/required-downloads
chmod 755 runtime/required-downloads
test ! -e "runtime/required-downloads/$sha.zip"
mv "$stage/required-original.zip" "runtime/required-downloads/$sha.zip"
changed=1
for file in src/required-downloads.mjs src/release-stream.mjs public-required-downloads.json public-release-assets.json runtime-manifest.sha256 src/server.mjs; do
 cat "$stage/$file" > "runtime/$file"
 chmod 644 "runtime/$file"
done
cp -p "$stage/deployment-manifest.json" runtime/downloads-transport-20261109.json
docker restart --time 30 tb-leaderboard-api-1 > "$evidence/api-restart.txt"
attempt=0
until curl --fail --silent --max-time 3 http://127.0.0.1:8080/v1/health > "$evidence/health.after.json"; do
 attempt=$((attempt+1));test "$attempt" -lt 20;sleep 1
done
cmp -s "$evidence/health.before.json" "$evidence/health.after.json"
caddy_changed=1
cat "$stage/Caddyfile" > Caddyfile
test "$(stat -c '%i' Caddyfile)" = "$(cat "$evidence/caddy-inode.before")"
docker exec tb-leaderboard-caddy-1 caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile > "$evidence/caddy-reload.txt" 2>&1
sha256sum --status -c "$stage/deployed.expected.sha256"
sha256sum --status -c "$evidence/library-index.before.sha256"
if test -f "$evidence/stable-host.before.sha256"; then sha256sum --status -c "$evidence/stable-host.before.sha256"; fi
docker exec tb-leaderboard-caddy-1 sha256sum /config/tb-updates/stable/manifest-v1.json > "$evidence/stable-served.after.sha256"
cmp -s "$evidence/stable-served.before.sha256" "$evidence/stable-served.after.sha256"
docker inspect --format '{{.Name}} {{json .Mounts}}' tb-leaderboard-api-1 tb-leaderboard-mysql-1 tb-leaderboard-redis-1 tb-leaderboard-caddy-1 > "$evidence/mounts.after"
cmp -s "$evidence/mounts.before" "$evidence/mounts.after"
awk '$2=="runtime/BUILD-INFO.json" || $2=="runtime/package.json"' "$evidence/public-before.sha256" > "$evidence/unchanged-program-metadata.sha256"
sha256sum --status -c "$evidence/unchanged-program-metadata.sha256"
available=$(df -Pk . | awk 'NR==2 {print $4}')
test "$available" -gt 262144
printf '%s\n' "$available" > "$evidence/available-kib.after"
stat -c '%i' Caddyfile > "$evidence/caddy-inode.after"
date -u +%Y-%m-%dT%H:%M:%SZ > "$evidence/deployed-at.utc"
trap - EXIT INT TERM
printf 'Program and approved public indices deployed; health unchanged, Caddy inode and stable169 preserved; available_kib=%s\n' "$available"
cat "$evidence/payload-validation.json"
