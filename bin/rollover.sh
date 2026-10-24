#!/usr/bin/env bash
# RV-10: weekly tide rollover, run by wheel-rollover.timer (Fri 21:00 London).
#
# Flow: check a tide is due -> clone prod to a rehearsal DB -> release staging
# (prod only, bin/release.sh) -> rehearse the rollover on the clone -> back up prod
# -> advance prod -> verify prod -> drop rehearsal.
# The release goes first so the new tide is advanced by the code that will run it.
# A failed release rolls itself back and the tide still advances, on the old code.
# Any failure writes $FAIL_MARKER (step and log path) and exits 1. The rehearsal DB
# is kept on failure for inspection. "No tide due" exits 0.
set -Eeuo pipefail
{  # parse the whole script up front: the release rewrites this file mid-run

APP_DIR="${APP_DIR-/home/user/wheel-app}"
PROD_DB="${PROD_DB-wheeldb}"
REHEARSAL_DB="${REHEARSAL_DB-wheel_rollover_rehearsal}"
LIVE_URL="${LIVE_URL-http://localhost:5000}"
BACKUP_CMD="${BACKUP_CMD-/home/user/backup-wheeldb.sh}"
FAIL_MARKER="${FAIL_MARKER-$APP_DIR/ROLLOVER_FAILED}"
POST_CHECK="${POST_CHECK-python3 $APP_DIR/bin/post_rollover_check.py}"
LOG_DIR="${LOG_DIR-$APP_DIR/logs}"
RELEASE_CMD="${RELEASE_CMD-}"  # set on the prod unit only: ships origin/staging before the advance
LOCK_FILE="/tmp/wheel-rollover-$PROD_DB.lock"  # per DB: staging and prod timers fire at the same minute
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

RELEASE_FAILED=""
if [[ -n "$RELEASE_CMD" ]]; then
    STEP="release"
    if ! APP_DIR="$APP_DIR" PROD_DB="$PROD_DB" REHEARSAL_DB="$REHEARSAL_DB" BACKUP_CMD="$BACKUP_CMD" $RELEASE_CMD; then
        RELEASE_FAILED=1
        echo "$(date -Is) release failed; the tide advances on the current code"
    fi
fi

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
if [[ -n "$RELEASE_FAILED" ]]; then
    STEP="release"
    fail "release failed and rolled back; the tide advanced on the old code"
fi
exit 0
}
