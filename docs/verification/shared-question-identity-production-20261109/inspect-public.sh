#!/bin/sh
set -eu
cd /opt/tb-leaderboard
test "$(pwd -P)" = /opt/tb-leaderboard
test ! -L runtime
df -Pk .
stat -c 'caddy_inode=%i' Caddyfile
docker ps --format '{{.Names}} {{.ID}} {{.Image}}'
find runtime -maxdepth 1 -type f -printf '%f\n' | sort
for file in src/question-identities.mjs src/ranking-rules.mjs src/ranking-dominance.mjs src/mysql-store.mjs src/team-training.mjs src/sticker-scenes.mjs SOURCE SOURCE.json SOURCE-COMMIT SOURCE-INFO.json BUILD-INFO.json runtime-manifest.sha256 package.json public-library-assets.json public-release-assets.json public-required-downloads.json; do
 if test -f "runtime/$file"; then sha256sum "runtime/$file"; fi
done
docker exec tb-leaderboard-api-1 node -e 'const fs=require("node:fs");const l=JSON.parse(fs.readFileSync("public-library-assets.json","utf8"));const r=JSON.parse(fs.readFileSync("public-release-assets.json","utf8"));console.log(JSON.stringify({readOnly:process.env.READ_ONLY==="1",librarySchema:l.schema,libraryKeys:Object.keys(l),libraryCount:(l.assets||l.items||[]).length,releaseKeys:Object.keys(r),releaseCount:(r.assets||r.items||[]).length,full:r.assets?.filter(a=>a.bytes===494336411).map(a=>({name:a.name,chunks:a.chunks?.length,sha256:a.sha256}))}));'
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8080/v1/health
printf '\n'
docker exec tb-leaderboard-caddy-1 sha256sum /config/tb-updates/stable/manifest-v1.json
