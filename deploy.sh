#!/usr/bin/env bash
# deploy.sh — Promote staging → production
#
# Usage: ./deploy.sh [--skip-build] [--yes]
#
# What it does:
#   1. Checks production worktree is clean
#   2. Merges staging → master
#   3. Dry-runs migrations, prompts to confirm
#   4. Applies migrations to production DB
#   5. Rebuilds JSX (unless --skip-build)
#   6. Clears stale .pyc bytecode cache
#   7. Hard-restarts gunicorn via systemctl (falls back to HUP)

set -euo pipefail

PROD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGING_DIR="/home/user/wheel-app-staging"
SKIP_BUILD=false
AUTO_YES=false

for arg in "$@"; do
  [[ "$arg" == "--skip-build" ]] && SKIP_BUILD=true
  [[ "$arg" == "--yes" ]] && AUTO_YES=true
done

cd "$PROD_DIR"

echo "==> Checking production working tree..."
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "ERROR: Production working tree has uncommitted changes. Stash or commit first."
  exit 1
fi

echo "==> Current branch: $(git branch --show-current)"
git checkout master 2>/dev/null || true

echo "==> Merging staging → master..."
git merge staging --no-edit

echo "==> Migration dry-run (production DB)..."
python3 migrate.py --dry-run

echo ""
if [[ "${AUTO_YES}" != true ]]; then
  read -rp "Apply these migrations to production? [y/N] " confirm
  if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted. No migrations applied, merge is in place."
    exit 0
  fi
fi

echo "==> Applying migrations to production..."
python3 migrate.py

if [[ "$SKIP_BUILD" == false ]]; then
  echo "==> Rebuilding JSX..."
  make build
fi

echo "==> Clearing stale bytecode..."
find "$PROD_DIR" -path "$PROD_DIR/__pycache__/*.pyc" -delete 2>/dev/null || true

echo "==> Restarting gunicorn..."
if echo "1234" | sudo -S systemctl restart wheel-app 2>/dev/null; then
  echo "    systemctl restart wheel-app: OK"
elif [[ -f gunicorn.ctl ]]; then
  kill -HUP "$(cat gunicorn.ctl)"
  echo "    HUP sent to $(cat gunicorn.ctl)"
elif pgrep -f 'gunicorn.*server:app' > /dev/null; then
  kill -HUP "$(pgrep -f 'gunicorn.*server:app' | head -1)"
  echo "    HUP sent to gunicorn"
else
  echo "WARNING: No running gunicorn found. Start it manually."
fi

echo ""
echo "==> Deploy complete."
