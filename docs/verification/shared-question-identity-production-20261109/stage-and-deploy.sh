#!/bin/sh
set -eu
umask 077
project=/opt/tb-leaderboard
stage=$project/runtime.next-question-identity-efc0618d
backup=$project/backups/question-identity-deploy-20261109-efc0618d
archive=/tmp/tb-question-identity-candidate-efc0618d.tar.gz
test "$(sha256sum "$archive" | cut -d ' ' -f1)" = 10c2b7cf8d7aad589ea3ecd206589466a8784ed2dbe64fe7f3c977d82284cc36
test ! -e "$stage"
test -f "$backup/preflight-complete.utc"
for name in $(tar -tzf "$archive"); do
 case "$name" in
  src/question-identities.mjs|src/ranking-rules.mjs|src/ranking-dominance.mjs|src/mysql-store.mjs|src/team-training.mjs|src/sticker-scenes.mjs|question-identity-20261109.json|runtime-manifest.sha256|expected.sha256|validate-candidate.mjs|deploy-public.sh) ;;
  *) printf 'Unexpected candidate path\n' >&2;exit 1 ;;
 esac
done
mkdir -m 755 "$stage"
tar -xzf "$archive" --no-same-owner -C "$stage"
cp -p /tmp/tb-question-identity-stage-efc0618d.sh "$backup/stage-and-deploy.sh"
sh "$stage/deploy-public.sh"
