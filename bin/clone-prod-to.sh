#!/bin/bash
# Clone the production DB (wheeldb) into <target_db>, replacing it.
# Usage: sudo bin/clone-prod-to.sh <target_db>
# Runs pg_dump as the postgres superuser (wheelapp lacks CREATEDB).
# Read-only on prod; refuses to target wheeldb itself.
set -euo pipefail

TARGET="${1:?usage: clone-prod-to.sh <target_db>}"
if [[ "$TARGET" == "wheeldb" || ! "$TARGET" =~ ^(wheeldb|wheel)_[a-z0-9_]+$ ]]; then
  echo "refusing target '$TARGET' (must look like wheeldb_<name> or wheel_<name>, never wheeldb)" >&2
  exit 1
fi

PG="sudo -u postgres"
$PG dropdb --if-exists "$TARGET"
$PG createdb -O wheelapp "$TARGET"
$PG pg_dump --no-owner wheeldb | $PG psql -q -v ON_ERROR_STOP=1 -d "$TARGET" >/dev/null
# Restored objects are owned by postgres; hand them to the app role.
$PG psql -q -d "$TARGET" -c "REASSIGN OWNED BY postgres TO wheelapp" 2>/dev/null || \
$PG psql -q -d "$TARGET" <<'SQL'
DO $$DECLARE r record; BEGIN
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname='public' LOOP
    EXECUTE 'ALTER TABLE public.'||quote_ident(r.tablename)||' OWNER TO wheelapp'; END LOOP;
  FOR r IN SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema='public' LOOP
    EXECUTE 'ALTER SEQUENCE public.'||quote_ident(r.sequence_name)||' OWNER TO wheelapp'; END LOOP;
  FOR r IN SELECT p.oid::regprocedure AS f FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' LOOP
    EXECUTE 'ALTER FUNCTION '||r.f||' OWNER TO wheelapp'; END LOOP;
END$$;
SQL

src=$($PG psql -At -d wheeldb -c "select count(*) from users")
dst=$($PG psql -At -d "$TARGET" -c "select count(*) from users")
echo "cloned wheeldb -> $TARGET (users: prod=$src clone=$dst)"
[[ "$src" == "$dst" ]]
