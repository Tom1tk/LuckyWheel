# T109 rollover wrapper. Loads ADMIN_SECRET from main's .env (never typed
# in shell history), POSTs to /api/admin/advance-season. Called by
# /etc/cron.d/wheel-rollover. Set executable via chmod +x. See
# SEASON_8_MIGRATION_PLAN.md §6.6.
#!/bin/bash
set -euo pipefail
SECRET=$(grep ^ADMIN_SECRET /home/user/wheel-app/.env | cut -d= -f2)
RESP=$(curl -fsS -X POST -H "X-Admin-Secret: ${SECRET}" \
    http://localhost:5000/api/admin/advance-season)
echo "$(date -Iseconds) rollover fired: ${RESP}"