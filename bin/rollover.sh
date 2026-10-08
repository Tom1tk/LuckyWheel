#!/usr/bin/env bash
# RV-10: weekly tide rollover, run by wheel-rollover.timer (Fri 21:00 London).
#
# Flow: check a tide is due -> clone prod to a rehearsal DB and rehearse the
# rollover there -> back up prod -> advance prod -> verify prod -> drop rehearsal.
# Any failure writes $FAIL_MARKER (step and log path) and exits 1. The rehearsal DB
# is kept on failure for inspection. "No tide due" exits 0.
set -Eeuo pipefail

APP_DIR="${APP_DIR-/home/user/wheel-app}"
PROD_DB="${PROD_DB-wheeldb}"
REHEARSAL_DB="${REHEARSAL_DB-wheel_rollover_rehearsal}"
LIVE_URL="${LIVE_URL-http://localhost:5000}"
BACKUP_CMD="${BACKUP_CMD-/home/user/backup-wheeldb.sh}"
FAIL_MARKER="${FAIL_MARKER-$APP_DIR/ROLLOVER_FAILED}"
POST_CHECK="${POST_CHECK-python3 $APP_DIR/bin/post_rollover_check.py}"
LOG_DIR="${LOG_DIR-$APP_DIR/logs}"
LOCK_FILE=/tmp/wheel-rollover.lock
STEP="startup"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "another rollover is already running; exiting"
    exit 0
fi

ts="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/rollover-$ts.log"
exec > >(tee -a "$LOG") 2>&1

fail() {
    echo "$(date -Is) ROLLOVER FAILED at step '$STEP': $1"
    printf 'time=%s\nstep=%s\nlog=%s\n' "$(date -Is)" "$STEP" "$LOG" > "$FAIL_MARKER" \
        || echo "could not write $FAIL_MARKER" >&2
    exit 1
}
trap 'fail "command failed (line $LINENO, exit $?)"' ERR

if [[ "$REHEARSAL_DB" == wheeldb || ! "$REHEARSAL_DB" =~ ^wheel_[a-z0-9_]+$ ]]; then
    fail "refusing rehearsal DB name '$REHEARSAL_DB'"
fi

STEP="check tide due"
rc=0
OUT="$(python3 "$APP_DIR/bin/advance_tide.py" --db "$PROD_DB" --check-only 2>&1)" || rc=$?
echo "$OUT"
case "$rc" in
    0) echo "nothing to do: no tide due"; exit 0 ;;
    2) echo "no-op: season is not a tide (season launch is manual)"; exit 0 ;;
    10) ;;
    *) fail "tide check exited $rc" ;;
esac

STEP="clone prod to rehearsal"
SOURCE_DB="$PROD_DB" "$APP_DIR/bin/clone-prod-to.sh" "$REHEARSAL_DB"

STEP="rehearsal"
python3 "$APP_DIR/bin/post_rollover_check.py" snapshot --db "$REHEARSAL_DB" \
    --out "$LOG_DIR/rollover-$ts-rehearsal-before.json"
python3 "$APP_DIR/bin/advance_tide.py" --db "$REHEARSAL_DB"
$POST_CHECK verify --db "$REHEARSAL_DB" --before "$LOG_DIR/rollover-$ts-rehearsal-before.json"

STEP="back up prod"
$BACKUP_CMD

STEP="snapshot prod"
python3 "$APP_DIR/bin/post_rollover_check.py" snapshot --db "$PROD_DB" \
    --out "$LOG_DIR/rollover-$ts-prod-before.json"

STEP="advance prod"
rc=0
ADV_OUT="$(python3 "$APP_DIR/bin/advance_tide.py" --db "$PROD_DB" 2>&1)" || rc=$?
echo "$ADV_OUT"
[[ "$rc" -eq 0 ]] || fail "advance exited $rc"
ADV_LINE="$(grep -m1 '^advanced ' <<<"$ADV_OUT" || true)"
[[ -n "$ADV_LINE" ]] || fail "advance reported no 'advanced' line"

STEP="verify prod"
LIVE_ARGS=()
if [[ -n "$LIVE_URL" ]]; then
    LIVE_ARGS=(--live-url "$LIVE_URL")
fi
$POST_CHECK verify --db "$PROD_DB" --before "$LOG_DIR/rollover-$ts-prod-before.json" \
    ${LIVE_ARGS[@]+"${LIVE_ARGS[@]}"}

STEP="drop rehearsal"
sudo -u postgres dropdb --if-exists "$REHEARSAL_DB"

echo "rollover complete ${ADV_LINE#advanced }"
