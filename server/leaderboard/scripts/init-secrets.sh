#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
umask 077
mkdir -p secrets backups
for name in mysql_password mysql_root_password rate_limit_salt redis_password; do
  if [ ! -s "secrets/$name" ]; then
    if [ -e "secrets/$name" ]; then
      printf 'Refusing to overwrite empty existing secret: %s\n' "$name" >&2
      exit 1
    fi
    openssl rand -hex 32 > "secrets/$name"
  fi
done
redis_password=$(cat secrets/redis_password)
redis_hash=$(printf '%s' "$redis_password" | sha256sum | cut -d ' ' -f 1)
printf 'user default on #%s ~* &* +@all\n' "$redis_hash" > secrets/redis_acl.tmp
chmod 444 secrets/redis_acl.tmp
mv -f secrets/redis_acl.tmp secrets/redis_acl
# Compose bind-mounts secret files. The unprivileged API user must be able to read
# them; the 0700 parent prevents other host users from accessing their contents.
chmod 700 secrets backups
chmod 444 secrets/mysql_password secrets/rate_limit_salt secrets/redis_password
chmod 400 secrets/mysql_root_password
printf 'Secret files are ready; existing values were preserved.\n'
