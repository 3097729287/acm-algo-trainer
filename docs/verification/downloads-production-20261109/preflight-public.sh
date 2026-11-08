#!/bin/sh
set -eu
umask 077
cd /opt/tb-leaderboard
evidence=/opt/tb-leaderboard/backups/downloads-deploy-20261109-c2b754eb
test ! -e "$evidence"
available=$(df -Pk . | awk 'NR==2 {print $4}')
test "$available" -gt 307200
mkdir -m 700 "$evidence"
for file in Caddyfile runtime/src/server.mjs runtime/src/release-stream.mjs runtime/public-release-assets.json runtime/runtime-manifest.sha256 runtime/BUILD-INFO.json runtime/package.json; do
  test -f "$file" && test ! -L "$file"
  name=$(printf '%s' "$file" | tr / _)
  cp -p "$file" "$evidence/$name.before"
  sha256sum "$file"
done > "$evidence/public-before.sha256"
for file in runtime/src/required-downloads.mjs runtime/public-required-downloads.json; do
  if test -e "$file"; then
    test -f "$file" && test ! -L "$file"
    name=$(printf '%s' "$file" | tr / _)
    cp -p "$file" "$evidence/$name.before"
    printf 'present %s\n' "$file"
  else printf 'absent %s\n' "$file"; fi
done > "$evidence/required-before.txt"
stat -c '%i' Caddyfile > "$evidence/caddy-inode.before"
docker ps --format '{{.Names}} {{.ID}} {{.Image}}' > "$evidence/containers.before"
docker inspect --format '{{.Name}} {{json .Mounts}}' tb-leaderboard-api-1 tb-leaderboard-mysql-1 tb-leaderboard-redis-1 tb-leaderboard-caddy-1 > "$evidence/mounts.before"
docker exec tb-leaderboard-api-1 node -e 'console.log(JSON.stringify({cwd:process.cwd(),paths:Object.fromEntries(["RELEASE_ASSETS_FILE","LIBRARY_ASSETS_FILE","REQUIRED_DOWNLOADS_FILE","REQUIRED_DOWNLOADS_DIR"].map(key=>[key,process.env[key]||null]))}))' > "$evidence/public-paths.json"
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8080/v1/health > "$evidence/health.before.json"
sha256sum runtime/public-library-assets.json > "$evidence/library-index.before.sha256"
if test -f updates/stable/manifest-v1.json; then sha256sum updates/stable/manifest-v1.json > "$evidence/stable-host.before.sha256"; fi
docker exec tb-leaderboard-caddy-1 sha256sum /config/tb-updates/stable/manifest-v1.json > "$evidence/stable-served.before.sha256"
printf 'space_available_kib=%s\n' "$available"
cat "$evidence/public-paths.json" "$evidence/required-before.txt" "$evidence/caddy-inode.before" "$evidence/health.before.json"
printf '\nbackup=%s\n' "$evidence"
