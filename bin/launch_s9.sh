#!/bin/bash
# One-off Season 9 launch: S8 -> Tide 9.1 (WHEEL_REVIVAL_PLAN §7.3), in one window.
# Order: stop app -> backup -> merge staging -> migrate -> snapshot -> advance -> start -> verify
#        -> announce -> install weekly timer -> push master.
# REHEARSE=1 runs only the DB steps against $DB using the staging code (DB must be a wheel_* clone).
# Rollback (prod): sudo systemctl stop wheel-app; restore $BACKUP into wheeldb;
#                  git -C /home/user/wheel-app reset --hard f77fb55; sudo systemctl start wheel-app.
set -euo pipefail

STAGING=/home/user/wheel-app-staging
PROD=/home/user/wheel-app
REHEARSE="${REHEARSE:-0}"
DB="${DB:-wheeldb}"
TS=$(date +%Y%m%d_%H%M%S)
SNAP="/tmp/wheel-launch-s9-$TS.json"
STEP=start
trap 'echo "LAUNCH FAILED at step: $STEP" >&2' ERR
step() { STEP="$1"; echo "==> $(date +%T) $1"; }

BASE_URL=$(grep '^DATABASE_URL=' "$PROD/.env" | cut -d= -f2-)
export DATABASE_URL="${BASE_URL%/*}/$DB"
if [[ "$REHEARSE" == 1 ]]; then
  [[ "$DB" =~ ^wheel_[a-z0-9_]+$ ]] || { echo "rehearsal DB must be a wheel_* clone" >&2; exit 1; }
  CODE=$STAGING
else
  [[ "$DB" == wheeldb ]] || { echo "launch DB must be wheeldb" >&2; exit 1; }
  CODE=$PROD
fi
dbcheck() { python3 -c "import os,psycopg2; c=psycopg2.connect(os.environ['DATABASE_URL']).cursor(); c.execute('select current_database()'); d=c.fetchone()[0]; assert d=='$DB', d"; }
dbcheck

if [[ "$REHEARSE" != 1 ]]; then
  step "prod tree clean, staging contains master"
  git -C "$PROD" diff --quiet && git -C "$PROD" diff --cached --quiet
  [[ "$(git -C "$PROD" branch --show-current)" == master ]]
  git -C "$PROD" merge-base --is-ancestor master staging

  step "stop app"
  sudo -n systemctl stop wheel-app

  step "backup"
  BACKUP="/home/user/backups/wheeldb_launch_s9_$TS.sql.gz"
  pg_dump "$DATABASE_URL" | gzip > "$BACKUP"
  gzip -t "$BACKUP"
  [[ $(stat -c %s "$BACKUP") -gt 1000000 ]]
  echo "    backup: $BACKUP ($(du -h "$BACKUP" | cut -f1))"

  step "merge staging -> master"
  git -C "$PROD" merge --ff-only staging
fi

cd "$CODE"
step "migrate"
python3 migrate.py

step "snapshot"
python3 bin/post_rollover_check.py snapshot --db "$DB" --out "$SNAP"

step "advance S8 -> 9.1"
python3 - "$DB" <<'PY'
import os, sys, psycopg2, seasons
conn = psycopg2.connect(os.environ['DATABASE_URL'])
with conn.cursor() as cur:
    cur.execute('SELECT current_database()')
    assert cur.fetchone()[0] == sys.argv[1]
seasons.advance_season(conn, 9, 'Tides', 1)
info = seasons.ensure_current_season(conn)
assert info['season_label'] == '9.1', info
print('    now', info['season_label'], 'ends', info.get('ends_at'))
PY

LIVE=()
if [[ "$REHEARSE" != 1 ]]; then
  step "start app"
  find "$PROD" -name '*.pyc' -path '*__pycache__*' -not -path '*/node_modules/*' -delete
  sudo -n systemctl start wheel-app
  for _ in $(seq 30); do curl -sf http://localhost:5000/api/health >/dev/null && break; sleep 1; done
  curl -sf http://localhost:5000/api/health >/dev/null
  LIVE=(--live-url http://localhost:5000)
fi

step "verify (label_advanced is expected to FAIL: S8 had no tide label)"
OUT=$(python3 bin/post_rollover_check.py verify --db "$DB" --before "$SNAP" "${LIVE[@]}") || true
echo "$OUT"
FAILS=$(echo "$OUT" | grep '^FAIL' | grep -v 'label_advanced' || true)
[[ -z "$FAILS" ]]

step "announce"
python3 - "$DB" <<'PY'
import os, sys, psycopg2, chat
conn = psycopg2.connect(os.environ['DATABASE_URL'])
with conn.cursor() as cur:
    cur.execute('SELECT current_database()')
    assert cur.fetchone()[0] == sys.argv[1]
chat.post_system_message(conn, "🌊 Season 9: Tides is here! The race now runs in weekly tides: every Friday at 9pm UK time "
                               "the top three take a medal and everyone starts level. Fishing is a fight, Charts replace "
                               "the shop, and auto-spin is free for everyone. Good luck!", throttle=False)
conn.commit()
PY

if [[ "$REHEARSE" == 1 ]]; then
  echo "REHEARSAL OK"
  exit 0
fi

step "install weekly timer"
sudo -n cp "$PROD/deploy/wheel-rollover.service" "$PROD/deploy/wheel-rollover.timer" /etc/systemd/system/
sudo -n systemctl daemon-reload
sudo -n systemctl enable --now wheel-rollover.timer
systemctl list-timers wheel-rollover.timer --no-pager

step "push master"
git -C "$PROD" push origin master

echo "LAUNCH OK  backup=$BACKUP"
