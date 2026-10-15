#!/usr/bin/env bash
# Tide release: ship origin/staging to prod right after the tide advances.
# Called by rollover.sh when RELEASE_CMD is set (the prod unit only), while the
# advanced rehearsal DB still exists. Fast-forward only. A RELEASE_HOLD file in
# $APP_DIR skips the release. On failure after the switch the old code is restored
# and restarted; migrations are not reversed, so they must stay additive.
set -Eeuo pipefail

APP_DIR="${APP_DIR-/home/user/wheel-app}"
PROD_DB="${PROD_DB-wheeldb}"
REHEARSAL_DB="${REHEARSAL_DB:?REHEARSAL_DB must be set}"
SERVICE="${SERVICE-wheel-app}"
HEALTH_URL="${HEALTH_URL-http://localhost:5000/api/season}"
BACKUP_CMD="${BACKUP_CMD-/home/user/backup-wheeldb.sh}"
REMOTE="${REMOTE-origin}"
cd "$APP_DIR"

die() { echo "release: $1" >&2; exit 1; }
dsn() {  # the configured DSN with the database swapped, as advance_tide.py does
    python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); import advance_tide as a; print(a.dsn_for(sys.argv[2]))' \
        "$APP_DIR/bin" "$1"
}
check_db() {
    [[ "$(psql "$1" -X -qAt -c 'SELECT current_database()')" == "$2" ]] || die "DSN does not reach $2"
}

if [[ -e RELEASE_HOLD ]]; then
    echo "release held (RELEASE_HOLD present); prod stays on $(git rev-parse --short HEAD)"
    exit 0
fi

git fetch -q "$REMOTE"
[[ "$(git symbolic-ref --short HEAD)" == master ]] || die "prod checkout is not on master"
git diff --quiet HEAD || die "prod checkout has uncommitted changes"
PREV="$(git rev-parse HEAD)"
NEXT="$(git rev-parse "$REMOTE/staging")"
[[ "$PREV" == "$(git rev-parse "$REMOTE/master")" ]] || die "prod HEAD is not $REMOTE/master"
if [[ "$PREV" == "$NEXT" ]]; then
    echo "release: nothing to release"
    exit 0
fi
git merge-base --is-ancestor "$PREV" "$NEXT" || die "master has commits staging lacks: merge master into staging"
git diff --quiet "$PREV" "$NEXT" -- requirements.txt || die "requirements.txt changed: release by hand"
# ponytail: the advance runs before the release, on the old code. Until the order is
# swapped, a staging change to the advance itself has to be released by hand.
git diff --quiet "$PREV" "$NEXT" -- seasons.py bin/advance_tide.py bin/post_rollover_check.py \
    || die "staging changes the tide advance: release by hand"
echo "release: $(git rev-parse --short "$PREV") -> $(git rev-parse --short "$NEXT") ($(git rev-list --count "$PREV..$NEXT") commits)"

# Rehearse staging's migrations on the advanced clone. Explicit DATABASE_URL: run
# without it, migrate.py would fall back to a .env.
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
git archive "$NEXT" migrate.py migrations | tar -x -C "$tmp"
REHEARSAL_DSN="$(dsn "$REHEARSAL_DB")"
check_db "$REHEARSAL_DSN" "$REHEARSAL_DB"
DATABASE_URL="$REHEARSAL_DSN" python3 "$tmp/migrate.py"

PROD_DSN="$(dsn "$PROD_DB")"
check_db "$PROD_DSN" "$PROD_DB"
$BACKUP_CMD

restart() {
    find . -name __pycache__ -not -path "./node_modules/*" -exec rm -rf {} +
    if [[ -n "$SERVICE" ]]; then
        sudo -n systemctl restart "$SERVICE"
    fi
}
rollback() {
    echo "release: failed, restoring $(git rev-parse --short "$PREV")" >&2
    git reset -q --hard "$PREV" && restart
}
trap 'rollback; rm -rf "$tmp"' ERR

git merge -q --ff-only "$NEXT"
DATABASE_URL="$PROD_DSN" python3 migrate.py
restart
for _ in $(seq 30); do
    curl -fs -o /dev/null "$HEALTH_URL" && break
    sleep 1
done
curl -fsS -o /dev/null "$HEALTH_URL"
git push -q "$REMOTE" master
trap - ERR
echo "release complete: prod on $(git rev-parse --short HEAD)"
