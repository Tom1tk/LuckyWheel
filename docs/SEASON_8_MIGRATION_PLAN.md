# Season 8 — Migration Plan (main `wheeldb`: 7.7 → Season 8)

> **Purpose:** Step-by-step plan to promote the staging Season 8 work to
> the live production server and execute the season rollover without the
> historical breakage (wrong season numbers, missing snapshots, un-reset
> pot, upgrade levels not cleared, missing migrations).
>
> **Target window:** Friday 26 June 2026, 23:59 BST (UTC+1) — the exact
> instant `seasons.ends_at` in `wheeldb` already expires
> (`2026-06-26 23:59:00+01`). Firing right at `ends_at` removes the
> Friday/Saturday ambiguity from the earlier draft. The 03:00 UTC daily
> backup plus the manual 22:30 BST backup (§6.7) both land well before
> this, giving the full rollback window.
>
> **Authoritative refs:**
> - `SEASON_8_BUILD_SPEC.md` — what Season 8 *is* (the design)
> - `SEASON_8_TICKETS.md` — what the work *is* (per-feature AC)
> - `SEASON_8_PROGRESS.md` — what's *done* (audit trail)
> - `seasons.py` (in `wheel-app/`) — the rollover mechanism
> - `migrations/` (in `wheel-app/`) — schema history
> - This document — how to *ship it* without breaking the live server

---

## 1. TL;DR

The main server (`wheel-app/`, `wheeldb`) is currently in season
`7.7` (DB row: `season_number=8, name='7.7', ends_at=2026-06-26 23:59 BST`).
The entire Season 8 design — wager system, prestige, bounties, community
goals, singularity, loadouts, casino theme, all the schema — has been
built and tested in `wheel-app-staging/` over the last 5 weeks.

**Resolved operator decisions (2026-06-23):** the new season name is
**`Casino`**; the 7-day cadence stays (with the intent to do smaller
weekly sub-seasons like 8.1, 8.2 going forward); auto-spin is a
shop-gated upgrade (no pre-registration); the pot buff is 7d; the
rollover fires via cron (`/etc/cron.d/wheel-rollover`); the
`sync-staging.yml` GitHub workflow is **disabled** so it doesn't
interfere with the manual promotion. See §11 for all 7 decisions.

The migration has two halves:

1. **Promote the work** — push staging's 51-migration series and Season 8
   code from the `staging` branch to `master`, deploy, and **verify the
   live server still runs cleanly while still in 7.7** (i.e. the S8
   columns exist, but the live game is still in 7.7 mode).
2. **Rollover to Casino** — at the scheduled time, the cron
   (`/etc/cron.d/wheel-rollover` → `bin/rollover.sh`) POSTs to
   `/api/admin/advance-season` to snapshot the current 7.7 standings,
   reset `game_state` (with the new S8 reset clauses), reset
   `community_pot` to S8 starting values, and bump `seasons` to the
   new number + name (`'Casino'`).

The historical breakage is **always** "we forgot to add the new S8
fields to the reset UPDATE" or "we ran the migration on the wrong DB".
This plan makes both impossible to forget by adding a **dry-run
verification on staging** as a hard gate.

---

## 2. State of things (as of 2026-06-23)

### Main (`wheeldb`, port 5000)

| Thing | Value |
|---|---|
| Branch | `master` |
| Code | Season 7.7 (no wager, no prestige, no bounties, no casino) |
| `game_state` columns | 49 S7-era columns (no `wager_*`, `prestige_*`, `cumulative_wins`, `auto_spin_budget`, `guard_*`, `resilience_*`, `legacy_wins`, `caught_species`, `equipped_class`, etc.) |
| Last migration applied | `030_drop_shield_charges` (2026-05-13) |
| `seasons` row | `season_number=8, name='7.7', ends_at=2026-06-26 23:59 BST` |
| `season_snapshots` | 21 rows (3 winners × 7 seasons) |
| `user_season_history` | 50 rows |
| Active players | 3 (tom7, worm67, dylan) — see `SEASON_8_PLANNING.md` for details |
| Gunicorn PID | 48937 (running since 2026-06-17) |
| Uncommitted edits | `static/app.js`, `static/app.jsx` (do not lose) |
| Backup cron | `0 3 * * * /home/user/backup-wheeldb.sh` — 03:00 UTC daily, last 14 days retained |

### Staging (`wheeldb_staging`, port 5001)

| Thing | Value |
|---|---|
| Branch | `staging` |
| Code | Full Season 8 (wager, prestige, bounties, community goals, singularity, loadouts, casino theme) |
| `game_state` columns | 67 (all S7 + 18 new S8 columns) |
| Last migration applied | `051_season8_theme_equip` (2026-06-23) |
| `seasons` row | `season_number=7, ends_at=2026-05-01 23:59 BST` (stuck at 7, intentionally — we use it to test S8 mechanics in isolation) |
| `season_snapshots` | 6 rows (no real seasons rolled over yet) |
| Gunicorn PID | 306013 (running since 2026-06-23, reloaded multiple times) |
| `ADMIN_SECRET` | (same `.env` template; not yet confirmed set in staging) |

### The gap (what main is missing)

Main's `seasons.py` knows nothing about Season 8. The reset UPDATE in
`_perform_rollover` resets S7 fields and stops. After the migration, the
S8 fields need to be in the reset too — otherwise they leak across
seasons. See §6 below for the full list.

Main's `game_state` is missing every S8 column. The S8 schema migrations
(031, 032, 036, 038, 039, 040, 041, 042, 043, 044, 045, 046, 048, 049,
050, 051) need to land in main before the rollover, or the reset UPDATE
will fail with `column does not exist`.

---

## 3. The rollover mechanism (unchanged from main)

`POST /api/admin/advance-season` (game.py:2125), with header
`X-Admin-Secret: $ADMIN_SECRET`, calls `seasons.advance_season(conn)`:

1. Lock + read the `seasons` row (`FOR UPDATE`).
2. Snapshot top 3 → `season_snapshots` (positions 1-3).
3. Snapshot every user → `user_season_history` (full state, including
   `equipped_fish`, `equipped_class`, `owned_items`, `active_cosmetics`).
4. Reset `game_state` (wins/losses, all upgrade levels, all flags, items,
   theme). **This is the step that needs updating for S8 — see §6.**
5. Reset `community_pot` (target=40000, win_chance=51.0, filled=false).
6. Bump `seasons` (number+1, started_at=NOW(), ends_at=NOW()+7d).
7. `SET LOCAL synchronous_commit = on` + commit — force WAL flush for
   the one critical weekly tx.

The endpoint is **manual-trigger only** (commit `a2bf578` explicitly
removed auto-rollover). Whoever runs the migration curls it at the
right time. No cron, no scheduler. **This is correct by design** — we
do not want seasons advancing without operator oversight.

`ADMIN_SECRET` for main is set in `/home/user/wheel-app/.env`:
`ADMIN_SECRET=d4da0abe8a184c5958371d9123189ddcf9d9812031694b3e`

---

## 4. Historical breakage (don't repeat these)

From the commit log of `wheel-app`:

| Commit | What broke | Why |
|---|---|---|
| `1b2d07f` | season_number wrong | mid-season 7.7 fix bumped number instead of name |
| `50d37ff` | user_season_history missing columns | new S7 fields weren't in the INSERT SELECT |
| `2d541dc` | community_pot not being reset on rollover | pot reset was in a migration, not in `seasons.py` |
| `d56c505` | upgrade levels / stat columns not being reset | new S5 fields weren't in the reset UPDATE |
| `8b54343` | DB migrations 018+019 not applied to staging | staging was running on a stale DB |
| `915a2bf` | duplicate `register_season` route after merge | merge conflict not caught |
| `0c0574e` | comment-only migration files executed | `migrate.py` ran them as empty tx |

**Pattern:** every season adds new fields; the reset code never knows
about them. The fixes have all been "remember to update the reset
UPDATE" — which is easy to forget on a stressful migration night.

**The hard rule for S8:** the S8 reset UPDATE in `seasons.py` must be
written and tested on staging **before** the migration window opens.
No writing it "live" at midnight.

---

## 5. Scope

### In scope

- Promote the 21 S8 migrations (031–051) to main.
- Promote the S8 code (game.py, models.py, seasons.py, app.jsx, etc.)
  to main.
- Update main's `seasons.py` to reset S8 fields in the rollover UPDATE.
- Update main's `seasons.py` to write S8 fields into `user_season_history`.
- Update main's `seasons.py` `community_pot` reset to S8 starting values.
- Update main's `seasons.py` `get_season_info` to surface the new season
  name correctly.
- Schedule + execute the rollover at the agreed time.
- Verify the rollover end-to-end on staging first.
- Verify the rollover end-to-end on main after.
- Patch-note the S8 launch.

### Out of scope

- New Season 9 mechanics (this is a 7.7 → 8 transition, not 8 → 9).
- Theme changes beyond what S8 already ships (Casino background is in).
- Any new columns not already in the S8 design.
- The top-3 vs top-5 winners inconsistency (tracked separately).
- Any frontend re-skin work for the rollover announcement (the existing
  hiatus page works).

---

## 6. Pre-migration work (must finish before the window)

### 6.1 — Re-verify S8 reset logic on staging

The staging `seasons.py` already has the S8 reset clauses (diffed against
main — the S8 additions are the `legacy_wins` accumulate, the
prestige/wager/guard/resilience/auto-spin-budget resets, and the
`active_wheel_mode = 'steady'` clause). The staging working tree
currently has the S8 work dirty (uncommitted); the dry-run is
intentionally done against the dirty tree because that matches what
main will look like after the §6.3 promote.

Re-run by calling `POST /api/admin/advance-season` on staging, and
verify:

- [ ] `season_snapshots` got 3 new rows for the current season
- [ ] `user_season_history` got 1 new row per user
- [ ] `game_state` wins/losses/levels all reset
- [ ] `game_state` `legacy_wins` ACCUMULATED (old value + current `wins`)
- [ ] `game_state` `prestige_level`/`prestige_count` reset to 0
- [ ] `game_state` `wager_streak`/`wager_banked_wins`/etc. reset
- [ ] `game_state` `wager_banked_losses` reset to 0 — **currently
      MISSING from the reset UPDATE in `seasons.py`.** `wager_banked_wins`
      resets but its loss counterpart doesn't; same "forgot the new
      field" pattern as §4.
- [ ] `game_state` `gravity_drift` reset to 0 — **currently MISSING.**
      Carries wheel-mode bias into the new season.
- [ ] `game_state` `wager_last_win_amount` reset to 0 — **currently
      MISSING.** Stale double-down escrow would carry over.
- [ ] Decide: does `wager_tokens` persist across seasons (it's an
      earned currency, arguably fine to keep) or should it reset like
      everything else? **Currently NOT reset** — confirm this is a
      deliberate choice, not an oversight.
- [ ] `game_state` `active_wheel_mode` reset to `'steady'`
- [ ] `community_pot` reset to `target=40000`, `win_chance_pct=51.0`,
      `filled=false`, `total_contributed=0`
- [ ] `seasons` row updated: number+1, started_at=NOW, ends_at=NOW+7d
- [ ] `/api/season` returns the new number and the new ends_at

If any of those fail on staging, **fix the staging `seasons.py` first**
and re-test. Do not promote a broken reset to main.

> **Note:** the dry-run does roll staging over to a new season. The
> staging `seasons` row will go from `season_number=7, ends_at=2026-05-01`
> to `season_number=8, ends_at=2026-06-30-ish` — that's fine, the
> staging DB is a dev environment. If the dry-run is destructive in a
> way we don't want, take a staging backup first
> (`pg_dump wheeldb_staging > /tmp/staging-pre-rollover.sql`).

### 6.2 — `user_season_history` is missing the S8 columns — schema AND code

**Correction (checked against the live `wheeldb_staging` schema
2026-06-25):** the earlier claim that "staging already has these
columns" was wrong. `\d user_season_history` on staging shows only the
S7 columns — no migration in 031–051 ever touches this table (only
`000_baseline` and `026_history_upgrade_snapshot` do, both pre-S8).

Worse, even if the columns existed: the `INSERT INTO
user_season_history` inside `advance_season()` in `seasons.py` only
writes the legacy S7 fields today (`final_wins`, the upgrade levels,
etc.) — it has zero references to any S8 column. Adding the migration
alone wouldn't snapshot anything; the INSERT itself needs editing too.

Two changes needed, both **main-only** — staging has no real user
data, so there's no need to backport this to staging's migration
ledger first:

1. A new migration `052_user_season_history_s8.sql` adding the S8
   columns to `user_season_history`.
2. An edit to the `INSERT INTO user_season_history` statement in
   `seasons.py::advance_season()` to actually populate them.

Full column list (cross-checked against every S8 `game_state` column
added by migrations 031–051, not just the ones named in §1's gap
summary):

```
wager_streak, wager_last_stake, wager_banked_wins, wager_banked_losses,
wager_insurance_charges, wager_insurance_armed, wager_last_win_amount,
wager_tokens, double_down_pending, active_wheel_mode, auto_spin_budget,
guard_charges, guard_last_regen_spin, resilience_last_use_spin,
legacy_wins, prestige_level, prestige_count, cumulative_wins,
gravity_drift, biggest_win_announced
```

(`aquarium_species` deliberately excluded — `game.py:212` notes it's
never written anywhere; it's dead schema, not real player state.)

### 6.3 — Promote staging → master (the code, not the rollover)

This is a normal `deploy.sh` run with the S8 code + migrations bundled.
**Critical:** main must remain functional while still in 7.7. The S8
code must not break 7.7 play. The S8 schema migrations (031–051 + 052)
add columns with safe defaults — they should be inert on 7.7.

**Pre-step (already done 2026-06-23):** the uncommitted `static/app.js{,x}`
edits in master (S7 timer fix) have been committed (`3c67350`) and merged
into staging (`4d8316f`). The `sync-staging.yml` workflow is disabled
(`7b3cf3f`) so the next push to master won't auto-merge.

**Sub-steps (in order):**

- [ ] In staging: commit the S8 working tree as one or more atomic
      commits (all the new files: `migrations/047–051`, the `static/js/`
      modules, `static/casino-preview.{html,css,js}`, the new test
      files; plus the modified files: `game.py`, `models.py`,
      `seasons.py`, `app.jsx`, etc.). This is the S8 work the last 5
      weeks produced; the dirty working tree IS the S8 code.
- [ ] Push `origin/staging`. (Safe — the disabled workflow won't fire
      on a push to staging; it only fires on master.)
- [ ] In master: `git merge origin/staging` (or use the existing
      `deploy.sh` workflow which does this).
- [ ] Resolve any merge conflicts. Likely sources: the S7 timer fix
      already in master (the S8 app.jsx has its own SeasonInfo), the
      staging migrations vs. main's migration numbering (no overlap —
      main is at 030, staging goes 031–052, so the 052 migration just
      needs to be added to main's migrations/ dir and to main's
      `schema_migrations` table).
- [ ] Run `python3 migrate.py --dry-run` on main's DB to confirm what
      will apply. Should be 22 migrations (031–052).
- [ ] Run `python3 migrate.py` on main. If any migration fails, STOP
      and roll back. (Each migration should be individually reversible
      per the existing pattern.)
- [ ] `make build` to rebuild `static/app.js` from `static/app.jsx`.
- [ ] Restart gunicorn (`sudo systemctl restart wheel-app`, fall back
      to HUP via the `gunicorn.ctl` socket).
- [ ] Smoke test: `curl http://localhost:5000/` returns 200, `/api/season`
      returns `season_number=8, name='7.7'`, login still works, can
      still spin (this proves 7.7 still functions with S8 code live).

### 6.4 — Update main's `seasons.py` (if not already via merge)

The staging `seasons.py` is the new main `seasons.py`. The merge in
§6.3 should bring it across. After the merge, confirm:

- [ ] The reset UPDATE includes all S8 columns (see §6.1 checklist).
- [ ] The `user_season_history` INSERT includes all S8 columns (see §6.2).
- [ ] The `community_pot` reset values are S8 values.
- [ ] The `get_season_info` returns `season_name='8'` (or whatever the
      new S8 name is — see §6.5).
- [ ] `synchronous_commit=on` is still set (it is — staging kept it).
- [ ] No other side effects on the live 7.7 game (test login + spin).

### 6.5 — Decide the Season 8 name

**Decision (operator, 2026-06-23):** the new `seasons.name` will be
**`'Casino'`** (matches the new `page_season8` background, themed, and
the existing `'7.7'` precedent shows themed names are preferred over
raw numbers).

The rollover will set `seasons.name = 'Casino'` in the same UPDATE that
bumps `season_number`. The `get_season_info` already returns
`season['name'] or str(season['season_number'])`, so a non-blank name
displays correctly throughout the UI.

### 6.6 — Schedule the rollover

**Decision (operator, 2026-06-23):** **cron-driven** — a one-shot
cron entry that POSTs at the scheduled time. This is the primary
trigger; no manual fallback needed in normal operation (the
T-30 / T-5 pre-flight catches anything the cron would silently mess
up).

The schedule is **Friday 26 June 2026, 23:59 BST** — the same instant
`seasons.ends_at` already expires. In UTC that is **2026-06-26
22:59:00 UTC** (BST is UTC+1). Firing at this exact timestamp avoids
the earlier draft's confusion between "Friday" and "the first hour of
Saturday."

The cron entry will live in `/etc/cron.d/wheel-rollover`:

```
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ADMIN_SECRET_FILE=/home/user/wheel-app/.env

# Season 8 launch: Friday 26 June 2026 23:59 BST = 22:59 UTC
# One-shot — delete this file after the rollover fires (or leave for
# future rollovers and update the schedule).
59 22 26 6 * user /home/user/wheel-app/bin/rollover.sh >> /var/log/wheel-rollover.log 2>&1
```

The `rollover.sh` wrapper script (new, lives in `wheel-app/bin/`)
loads `ADMIN_SECRET` from `.env` and POSTs:

```bash
#!/bin/bash
set -euo pipefail
SECRET=$(grep ^ADMIN_SECRET /home/user/wheel-app/.env | cut -d= -f2)
RESP=$(curl -fsS -X POST -H "X-Admin-Secret: ${SECRET}" \
    http://localhost:5000/api/admin/advance-season)
echo "$(date -Iseconds) rollover fired: ${RESP}"
```

This is wrapped in a script (not inline in the crontab) so the secret
never appears in `ps` output or the crontab file itself.

### 6.7 — Pre-migration backup (belt and braces)

The 03:00 UTC daily backup (`backup-wheeldb.sh`) will run on the morning
of the migration. We want a **fresh backup taken immediately before**
the rollover as well. Either:

- Force a backup manually:
  ```
  /home/user/backup-wheeldb.sh
  ```
  immediately before the rollover, OR
- Rely on the 03:00 UTC backup and roll back to it if needed (loses up
  to ~21 hours of play data — acceptable for a season boundary where
  the next season starts from zero anyway).

**Recommendation: take a manual backup at 22:30 BST Friday, immediately
before the rollover.** That's the one we'd actually restore from.

---

## 7. Migration day procedure (Friday 26 June 2026 23:59 BST)

### T-30 minutes (23:30 BST Friday)

- [ ] Verify main is still on 7.7: `curl http://localhost:5000/api/season`
      returns `season_number=8, name='7.7'`.
- [ ] Verify `/var/log/wheel-app/` shows no errors in the last 24h.
- [ ] Verify the cron entry from §6.6 is in place and will fire.
- [ ] Run `/home/user/backup-wheeldb.sh` and verify the backup file
      exists in `/home/user/backups/` and is non-empty.
- [ ] Tail the gunicorn log: `tail -f /home/user/wheel-app/gunicorn.log`
      in a second terminal — leave it open.

### T-5 minutes (23:55 BST Friday)

- [ ] Verify main is STILL on 7.7 (any spin/tick in the last 30 min is
      fine; just confirm the season hasn't bumped).
- [ ] Verify staging is up (so we can fall back to it if main blows up):
      `curl http://localhost:5001/` returns 200.
- [ ] Verify the staging `.env` has `ADMIN_SECRET` set, OR know the
      command needed to set it.

### T-0 (23:59 BST Friday = 22:59 UTC Friday)

- [ ] **The cron fires** automatically (`/etc/cron.d/wheel-rollover`
      → `/home/user/wheel-app/bin/rollover.sh`). The wrapper script
      loads `ADMIN_SECRET` from `.env` and POSTs to
      `/api/admin/advance-season`.
- [ ] If the cron silently fails, the **operator-fallback curl** is:
      ```
      curl -fsS -X POST -H "X-Admin-Secret: $ADMIN_SECRET" \
          http://localhost:5000/api/admin/advance-season
      ```
      (Emergency use only — the cron is the primary trigger.)
- [ ] **Watch the gunicorn log** for `SEASON_ROLLOVER_START` then
      `SEASON_ROLLOVER_DONE`. The whole thing should take < 5 seconds.
- [ ] If we see `SEASON_ROLLOVER_DONE`, go to §8.
- [ ] If we see an exception, go to §9 (rollback).

### T+5 minutes (00:05 BST Saturday)

- [ ] `curl http://localhost:5000/api/season` returns the new season
      number + the new `ends_at` (should be 7 days from now).
- [ ] `psql` query: `SELECT * FROM seasons;` shows the bumped row.
- [ ] `psql` query: `SELECT COUNT(*) FROM season_snapshots WHERE season_number = 8;`
      returns 3.
- [ ] `psql` query: `SELECT COUNT(*) FROM user_season_history WHERE season_number = 8;`
      returns the user count (8 users).
- [ ] `psql` query: `SELECT total_contributed, target, win_chance_pct, filled FROM community_pot WHERE id = 1;`
      shows the reset values.
- [ ] `psql` query: spot-check one user's `game_state` row — wins=0,
      losses=0, all upgrade levels=0, `legacy_wins` is the **old value
      + their final wins** (not just their final wins), `active_wheel_mode`
      is `'steady'`.

### T+15 minutes (00:15 BST Saturday)

- [ ] Login to the live site as one of the 3 active users and verify:
      the S8 UI is live, the wager panel works, the casino background
      renders, the page theme is `page_season8`.
- [ ] If any of those fail, the S8 code didn't take. See §9.

### T+1 hour (01:00 BST Saturday)

- [ ] Confirm no errors in gunicorn log since the rollover.
- [ ] Confirm at least one user has spun and the S8 wager flow works.
- [ ] Announce the launch (patch notes / chat / etc. — out of scope for
      this document but should be on the checklist).

---

## 8. Post-migration verification checklist

(This is the same as §7 T+5/T+15, called out as a permanent checklist
for the migration record.)

### Database state

- [ ] `seasons.season_number` = previous + 1
- [ ] `seasons.name` = the new S8 name (TBD)
- [ ] `seasons.started_at` = the rollover timestamp
- [ ] `seasons.ends_at` = `started_at` + 7 days
- [ ] `season_snapshots` has 3 new rows for the old season
- [ ] `user_season_history` has 1 new row per user for the old season
- [ ] `community_pot.total_contributed` = 0
- [ ] `community_pot.target` = 40000
- [ ] `community_pot.win_chance_pct` = 51.0
- [ ] `community_pot.filled` = false
- [ ] Spot-check: every `game_state` row has `wins = 0`,
      `legacy_wins = (old legacy_wins) + (old wins)`, all upgrade levels
      = 0, `active_wheel_mode = 'steady'`, all S8 fields reset to their
      defaults (NOT carried over).

### Application state

- [ ] `/api/season` returns the new season info (number, name, ends_at)
- [ ] `latest_winners` array in `/api/season` has 3 entries for the
      previous season
- [ ] Login still works for the 3 active users
- [ ] One user can spin, see the wager panel, place a 0% stake, win
- [ ] The casino page background is rendering
- [ ] No errors in gunicorn log since the rollover

### User-facing

- [ ] Season countdown / banner in the UI shows the new season
- [ ] Patch notes (if any) are linked from the announcement
- [ ] The hiatus page (if it was shown) is gone

---

## 9. Rollback plan

If anything in §7 or §8 goes wrong:

1. **Stop the site** — `sudo systemctl stop wheel-app` (or HUP the
   gunicorn master). Prevents users from accumulating state we can't
   reverse.
2. **Restore the DB** from the manual backup taken in §6.7:
   ```
   gunzip -c /home/user/backups/wheeldb_20260626_225500.sql.gz | \
       psql -h localhost -U wheelapp -d wheeldb
   ```
   (Substitute the actual filename. Verify the count of rows in
   `game_state` and `users` matches the pre-rollover state.)
3. **Restart gunicorn.**
4. **Verify** the live site is back on 7.7 with the pre-rollover data.
5. **Diagnose** what went wrong by inspecting the gunicorn log +
   `schema_migrations` + the failed SQL.
6. **Fix on staging** (never on main). Re-test the full rollover
   procedure on staging with the fix.
7. **Re-attempt** the migration in the next window. There is no rush
   — better to ship it right than to ship it now.

**If we can't diagnose within 2 hours:** announce the rollback in
chat / patch notes. The site stays on 7.7 for another week. The S8
work in main is still there, just inert. Nothing is lost.

---

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| S8 schema migrations fail to apply on main | Low | High | Dry-run in §6.3; stop on first failure |
| S8 reset UPDATE references a column that doesn't exist | Medium | High | §6.1 dry-run on staging; §6.2 schema migration for `user_season_history` |
| `legacy_wins` doesn't accumulate (forgot `legacy_wins = legacy_wins + wins`) | Medium | Medium | §6.1 verification checklist |
| S8 code crashes on a 7.7 game_state row (unexpected NULLs, etc.) | Medium | High | §6.3 smoke test after promote |
| Staging advance-season fires by accident on main | Low | Critical | Endpoint requires secret; only cron + operator have it |
| Rollback restores wrong backup (stale, partial) | Low | Critical | Verify backup file size + table count before restoring |
| Cron doesn't fire (typo, env not loaded) | Medium | High | Pre-flight check at T-30 in §7; manual fallback |
| The new S8 name isn't set / is wrong | Low | Low | Operator decides in §6.5; can be fixed with a small UPDATE later |
| The 3 active users log in at midnight and see a half-rolled-over state | Low | High | The whole rollover is one tx, atomic; either it works or it doesn't |
| S8 code has a hidden dep on something the staging DB has but main doesn't | Medium | High | §6.3 smoke test (login + spin) catches this |

---

## 11. Operator decisions (resolved 2026-06-23)

1. ✅ **S8 season name** → **`'Casino'`** (themed, matches the new
   `page_season8` background; the `'7.7'` precedent shows themed names
   are preferred over raw numbers). The rollover will set
   `seasons.name = 'Casino'` in the same UPDATE that bumps
   `season_number`.

2. ✅ **`ends_at` strategy** → **keep the 7-day pattern**. The intent
   (per operator) is to move to **smaller weekly sub-seasons**
   (8.1, 8.2, …) featuring balance changes and new features (e.g. new
   wheel spin modes), rather than large full-mechanic rollovers. The
   weekly cadence stays; the reset scope shrinks. See §11a below for
   what this means for the rollover mechanism.

3. ✅ **Pre-registration for auto-spin start** → **not needed** for
   S8. Auto-spin is gated on the `auto_spin_unlock` shop upgrade
   (5,000 wins, T107) — players must buy it to use it. The
   `season_registered` flag becomes informational only; the rollover
   still resets it to FALSE but nothing depends on it for S8.

4. ✅ **Community pot buff duration** → **keep 7d** (the S8 value).
   Reset applies to the 8.1 sub-season as well (pot starts fresh each
   sub-season).

5. ✅ **Trigger mechanism** → **cron**. One-shot entry in
   `/etc/cron.d/wheel-rollover` calls a wrapper script
   (`bin/rollover.sh`) that loads `ADMIN_SECRET` from `.env` and POSTs
   to `/api/admin/advance-season` at the scheduled time. Manual
   fallback is the T-0 curl in §7 (for emergency use only).

6. ✅ **Uncommitted JSX edits in main** → **committed and merged to
   staging** (2026-06-23). The 2 uncommitted files were the S7 timer
   fix (commit `3c67350`), unrelated to S8. Now both `master` and
   `staging` share this fix; staging's working tree picks it up via
   the merge commit (`4d8316f`).

7. ✅ **`sync-staging.yml` workflow** → **disabled** (commit `7b3cf3f`,
   2026-06-23). The auto-merge workflow was failing on the latest
   master push (S7 timer fix) because staging's S8 working tree
   conflicts with the timer fix's `app.jsx`/`app.js` changes. Renamed
   `.github/workflows/sync-staging.yml` →
   `.github/workflows/sync-staging.yml.disabled` (GitHub Actions only
   picks up `.yml`/`.yaml` files, so the rename is the cleanest
   disable). A header comment in the disabled file explains how to
   re-enable (`git mv` back to `.yml`).

---

## 11a. Sub-season model (8.1, 8.2, …) — follow-up design

The 7-day `ends_at` cadence implies weekly sub-seasons. These need a
different reset model than the 7.7 → 8 boundary:

- **7.7 → Casino (this migration):** full reset (wins=0, levels=0,
  items reset, `legacy_wins` accumulates, etc.) — the existing
  `_perform_rollover` logic.
- **Casino → 8.1 → 8.2 → … (future sub-seasons):** **partial reset**
  — preserve wins/levels/items, but reset the community pot, update
  the name, reset `active_wheel_mode` and a few transient flags. The
  current `_perform_rollover` does a full reset; it will need a `mode`
  parameter (e.g. `'full'` vs `'sub'`) to support sub-seasons.

**Out of scope for this migration.** The 7.7 → Casino transition is a
full reset. The sub-season model is a follow-up design ticket
(T110 or similar) for after launch. For the S8.1 rollover, the
operator can either:
- Run the full reset again (acceptable for the first sub-season —
  it's the same code path as the main migration), OR
- Update the cron command to set `ends_at` without calling
  `advance_season`, leaving game state intact.

The 7-day cron will keep firing the full reset until a sub-season
mode is implemented; this is a known-design-debt item, not a
migration-night concern.

---

## 12. Schedule (T-3 days to T-0)

| When | What | Owner |
|---|---|---|
| **Tue 23 Jun (now)** | This plan document + T109 ticket approved | Operator |
| **Wed 24 Jun** | §6.1 dry-run the S8 rollover on staging | Dev |
| **Wed 24 Jun** | §6.2 add `user_season_history` S8 columns migration | Dev |
| **Wed 24 Jun** | §6.6 install `/etc/cron.d/wheel-rollover` + `bin/rollover.sh` | Dev |
| **Thu 25 Jun** | §6.3 commit S8 working-tree to staging (one big commit) | Dev |
| **Thu 25 Jun** | §6.3 promote staging → master + apply migrations | Dev |
| **Thu 25 Jun** | §6.3 smoke test (7.7 still works on S8 code) | Dev |
| **Fri 26 Jun 03:00** | Daily backup runs (existing cron) | (automated) |
| **Fri 26 Jun 22:30** | Manual pre-rollover backup (§6.7) | Dev |
| **Fri 26 Jun 23:30** | T-30 pre-flight (§7) | Dev |
| **Fri 26 Jun 23:55** | T-5 pre-flight (§7) | Dev |
| **Fri 26 Jun 23:59** | T-0 rollover fires (§7) | **Cron** (operator-fallback only) |
| **Sat 27 Jun 00:05–00:15** | T+5 / T+15 verification (§7) | Dev |
| **Sat 27 Jun 01:00** | T+1h final check (§7) | Dev |
| **Sat 27 Jun** | Announce launch, close out T109 | Operator |

---

## 13. After the migration

- T109 gets a status update with the timestamp + a summary of what
  happened (any deviations from this plan, any issues hit, any follow-up
  tickets created).
- `SEASON_8_PROGRESS.md` gets a "Migration 2026-06-27" section with
  the verification checklist completed + the new season state recorded.
- A new ticket is filed for any issue discovered during verification
  (e.g. a field that didn't reset, a UI element that didn't render).
- The 03:00 UTC backup from Friday is kept indefinitely (don't let the
  14-day retention cycle delete it) as the S8-launch reference point.

---

*This document is the source of truth for the S8 migration. If reality
diverges from this plan, update the plan in the same commit as the
divergence — don't let the plan and reality drift.*
