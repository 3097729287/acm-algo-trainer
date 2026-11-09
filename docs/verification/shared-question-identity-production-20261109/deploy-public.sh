#!/bin/sh
set -eu
umask 077
project=/opt/tb-leaderboard
stage=$project/runtime.next-question-identity-efc0618d
backup=$project/backups/question-identity-deploy-20261109-efc0618d
cd "$project"
test "$(pwd -P)" = "$project"
test "$(realpath "$stage")" = "$stage"
test ! -L "$stage" && test ! -L runtime
test -f "$backup/preflight-complete.utc"
test ! -e "$backup/deploy-started.utc"
test "$(cat "$backup/question-identity-before.txt")" = absent
test ! -e runtime/question-identity-20261109.json
test "$(stat -c '%i' Caddyfile)" = 784925
test "$(df -Pk . | awk 'NR==2 {print $4}')" -gt 262144
sha256sum --status -c "$backup/public-before.sha256"
(cd "$stage" && sha256sum --status -c expected.sha256)
chmod 755 "$stage" "$stage/src"
chmod 644 "$stage"/*.json "$stage"/*.mjs "$stage"/*.sha256 "$stage"/src/*.mjs
docker run --rm --network none --read-only -v "$stage:/candidate:ro" node:24-bookworm-slim node /candidate/validate-candidate.mjs > "$backup/candidate-validation.json"
cp -p "$stage/deploy-public.sh" "$backup/deploy-public.sh"
cp -p "$stage/question-identity-20261109.json" "$backup/source-overlay.json"
sha256sum --status -c "$backup/public-before.sha256"
date -u +%Y-%m-%dT%H:%M:%SZ > "$backup/deploy-started.utc"
changed=0
rollback(){
 result=$?
 trap - EXIT INT TERM
 if test "$result" -ne 0 && test "$changed" = 1; then
  printf 'rollback_requested\n' > "$backup/phase.txt"
  for name in ranking-rules.mjs ranking-dominance.mjs mysql-store.mjs team-training.mjs sticker-scenes.mjs; do
   cat "$backup/runtime_src_$name.before" > "runtime/src/$name"
  done
  cat "$backup/runtime_runtime-manifest.sha256.before" > runtime/runtime-manifest.sha256
  # Only files newly created by this operation are removed on rollback.
  rm -f runtime/src/question-identities.mjs runtime/question-identity-20261109.json
  docker restart --time 30 tb-leaderboard-api-1 > "$backup/rollback-api-restart.txt" || true
 fi
 exit "$result"
}
trap rollback EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
changed=1
for name in question-identities.mjs ranking-rules.mjs ranking-dominance.mjs mysql-store.mjs team-training.mjs sticker-scenes.mjs; do
 cat "$stage/src/$name" > "runtime/src/$name"
 chmod 644 "runtime/src/$name"
done
cat "$stage/question-identity-20261109.json" > runtime/question-identity-20261109.json
cat "$stage/runtime-manifest.sha256" > runtime/runtime-manifest.sha256
chmod 644 runtime/question-identity-20261109.json runtime/runtime-manifest.sha256
printf 'program_copied_restart_requested\n' > "$backup/phase.txt"
docker restart --time 30 tb-leaderboard-api-1 > "$backup/api-restart.txt"
printf 'api_restarted\n' > "$backup/phase.txt"
attempt=0
until curl --fail --silent --max-time 3 http://127.0.0.1:8080/v1/health > "$backup/health.after.json"; do
 attempt=$((attempt+1));test "$attempt" -lt 20;sleep 1
done
cmp -s "$backup/health.before.json" "$backup/health.after.json"
(cd runtime && sha256sum --status -c "$stage/expected.sha256")
awk '$2!~/^runtime\/src\// && $2!="runtime/runtime-manifest.sha256"' "$backup/public-before.sha256" > "$backup/unchanged-public.sha256"
sha256sum --status -c "$backup/unchanged-public.sha256"
docker inspect --format '{{.Name}} {{json .Mounts}}' tb-leaderboard-api-1 tb-leaderboard-mysql-1 tb-leaderboard-redis-1 tb-leaderboard-caddy-1 > "$backup/mounts.after"
cmp -s "$backup/mounts.before" "$backup/mounts.after"
docker exec tb-leaderboard-caddy-1 sha256sum /config/tb-updates/stable/manifest-v1.json > "$backup/stable-served.after.sha256"
cmp -s "$backup/stable-served.before.sha256" "$backup/stable-served.after.sha256"
test "$(stat -c '%i' Caddyfile)" = 784925
docker exec tb-leaderboard-api-1 node -e 'const fs=require("node:fs");const l=JSON.parse(fs.readFileSync("public-library-assets.json","utf8")),r=JSON.parse(fs.readFileSync("public-release-assets.json","utf8"));console.log(JSON.stringify({readOnly:process.env.READ_ONLY==="1",libraryCommit:l.commit,libraryCount:l.assets.length,releaseCount:r.assets.length,full:r.assets.filter(a=>a.sha256==="8511c31ced17ef43aac67a1a8c4f973050496092863ad7ae639b307c65079fe4").map(a=>({name:a.name,size:a.size,sha256:a.sha256,chunkBytes:a.chunkBytes,chunks:a.chunkSha256?.length,githubDigest:a.githubDigest}))}));' > "$backup/public-state.after.json"
cmp -s "$backup/public-state.before.json" "$backup/public-state.after.json"
test "$(df -Pk . | awk 'NR==2 {print $4}')" -gt 262144
date -u +%Y-%m-%dT%H:%M:%SZ > "$backup/deployed-at.utc"
printf 'complete\n' > "$backup/phase.txt"
trap - EXIT INT TERM
printf 'Six reviewed program files deployed; one API restart; health, indices, mounts, Caddy and stable169 unchanged.\n'
cat "$backup/candidate-validation.json"
