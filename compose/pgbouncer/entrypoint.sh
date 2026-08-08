#!/bin/sh
set -eu

if [ -z "${DB_USER:-}" ] || [ -z "${DB_PASSWORD:-}" ]; then
  echo "DB_USER and DB_PASSWORD must be set for PgBouncer auth" >&2
  exit 1
fi

# Credentials come from env; never commit plaintext userlist to git.
printf '"%s" "%s"\n' "$DB_USER" "$DB_PASSWORD" > /tmp/userlist.txt

exec pgbouncer /etc/pgbouncer/pgbouncer.ini
