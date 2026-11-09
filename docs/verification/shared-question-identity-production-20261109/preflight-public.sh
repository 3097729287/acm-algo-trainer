#!/bin/sh
set -eu
umask 077
cd /opt/tb-leaderboard
test "$(pwd -P)" = /opt/tb-leaderboard
test ! -L runtime
backup=/opt/tb-leaderboard/backups/question-identity-deploy-20261109-efc0618d
test ! -e "$backup"
test "$(df -Pk . | awk 'NR==2 {print $4}')" -gt 262144
test "$(stat -c '%i' Caddyfile)" = 784925
mkdir -m 700 "$backup"
for file in runtime/src/ranking-rules.mjs runtime/src/ranking-dominance.mjs runtime/src/mysql-store.mjs runtime/src/team-training.mjs runtime/src/sticker-scenes.mjs runtime/runtime-manifest.sha256 runtime/BUILD-INFO.json runtime/package.json runtime/public-library-assets.json runtime/public-release-assets.json runtime/public-required-downloads.json Caddyfile; do
 test -f "$file" && test ! -L "$file"
 name=$(printf '%s' "$file" | tr / _)
 cp -p "$file" "$backup/$name.before"
 sha256sum "$file"
done > "$backup/public-before.sha256"
if test -e runtime/src/question-identities.mjs; then
 test -f runtime/src/question-identities.mjs && test ! -L runtime/src/question-identities.mjs
 cp -p runtime/src/question-identities.mjs "$backup/runtime_src_question-identities.mjs.before"
 printf 'present\n' > "$backup/question-identity-before.txt"
else printf 'absent\n' > "$backup/question-identity-before.txt"; fi
for file in SOURCE SOURCE.json SOURCE-COMMIT SOURCE-INFO.json runtime/SOURCE runtime/SOURCE.json runtime/SOURCE-COMMIT runtime/SOURCE-INFO.json; do
 if test -f "$file" && test ! -L "$file"; then
  name=$(printf '%s' "$file" | tr / _)
  cp -p "$file" "$backup/$name.before"
  sha256sum "$file"
 else printf 'absent %s\n' "$file"; fi
done > "$backup/source-metadata-before.txt"
docker ps --format '{{.Names}} {{.ID}} {{.Image}}' > "$backup/containers.before"
docker inspect --format '{{.Name}} {{json .Mounts}}' tb-leaderboard-api-1 tb-leaderboard-mysql-1 tb-leaderboard-redis-1 tb-leaderboard-caddy-1 > "$backup/mounts.before"
docker exec tb-leaderboard-api-1 node -e 'const fs=require("node:fs");const l=JSON.parse(fs.readFileSync("public-library-assets.json","utf8")),r=JSON.parse(fs.readFileSync("public-release-assets.json","utf8"));const full=r.assets.filter(a=>a.chunks?.length===472);if(l.assets.length!==2436||l.commit!=="fdd4dd256fe7cc205497811f97dc2cdb2fa5462f"||r.assets.length!==104||full.length!==1)throw Error("Public index boundary changed");console.log(JSON.stringify({readOnly:process.env.READ_ONLY==="1",libraryCommit:l.commit,libraryCount:l.assets.length,releaseCount:r.assets.length,full:full.map(a=>({name:a.name,sha256:a.sha256,keys:Object.keys(a),chunks:a.chunks.length}))}));' > "$backup/public-state.before.json"
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8080/v1/health > "$backup/health.before.json"
stat -c '%i' Caddyfile > "$backup/caddy-inode.before"
docker exec tb-leaderboard-caddy-1 sha256sum /config/tb-updates/stable/manifest-v1.json > "$backup/stable-served.before.sha256"
printf 'backup=%s\n' "$backup"
cat "$backup/public-state.before.json" "$backup/health.before.json"
printf '\n'
