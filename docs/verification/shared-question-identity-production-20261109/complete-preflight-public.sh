#!/bin/sh
set -eu
umask 077
cd /opt/tb-leaderboard
backup=/opt/tb-leaderboard/backups/question-identity-deploy-20261109-efc0618d
test -d "$backup" && test ! -e "$backup/preflight-complete.utc"
sha256sum --status -c "$backup/public-before.sha256"
docker exec tb-leaderboard-api-1 node -e 'const fs=require("node:fs");const l=JSON.parse(fs.readFileSync("public-library-assets.json","utf8")),r=JSON.parse(fs.readFileSync("public-release-assets.json","utf8"));const full=r.assets.filter(a=>a.sha256==="8511c31ced17ef43aac67a1a8c4f973050496092863ad7ae639b307c65079fe4");const state={readOnly:process.env.READ_ONLY==="1",libraryCommit:l.commit,libraryCount:l.assets.length,releaseCount:r.assets.length,full:full.map(a=>({name:a.name,size:a.size,sha256:a.sha256,chunkBytes:a.chunkBytes,chunks:a.chunkSha256?.length,githubDigest:a.githubDigest}))};console.log(JSON.stringify(state));if(l.assets.length!==2436||l.commit!=="fdd4dd256fe7cc205497811f97dc2cdb2fa5462f"||r.assets.length!==104||full.length!==1||full[0].size!==494336411||full[0].chunkBytes!==1048576||full[0].chunkSha256?.length!==472)throw Error("Public index boundary changed");' > "$backup/public-state.before.json"
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8080/v1/health > "$backup/health.before.json"
stat -c '%i' Caddyfile > "$backup/caddy-inode.before"
docker exec tb-leaderboard-caddy-1 sha256sum /config/tb-updates/stable/manifest-v1.json > "$backup/stable-served.before.sha256"
date -u +%Y-%m-%dT%H:%M:%SZ > "$backup/preflight-complete.utc"
printf 'preflight_complete=%s\n' "$backup"
cat "$backup/public-state.before.json" "$backup/health.before.json"
printf '\n'
