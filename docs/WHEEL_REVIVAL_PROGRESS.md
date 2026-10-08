# Wheel Revival — progress log

Evidence per gate. Plan: `docs/WHEEL_REVIVAL_PLAN.md`.

## Phase 0 — Safety & baseline (G0)

| Task | Status | Evidence |
|---|---|---|
| 0.1 archive S9 Arcade | done | branch `archive/s9-arcade` @ `62393cb` (pushed); byte-identical to pre-discard tree; patch+tgz in `/home/user/backups/s9-snapshot-20261008/` |
| 0.2 staging DB dump + clean tree | done | `/home/user/backups/wheeldb_staging_pre_revival.sql.gz` (377KB, 21 COPY blocks); staging tree clean, health OK |
| 0.3 test baseline | see `docs/TEST_BASELINE.md` | run against fresh `wheeldb_test` |
| 0.4 prod test-user leak | fixed on staging | cause: tests read `DATABASE_URL`/`.env` directly, `/home/user/wheel-app/.env` is prod. Fix: `tests/conftest.py` pins session to `wheeldb_test` before collection; `test_win_amount_overflow.py` no longer reads `.env`. Regression: `tests/test_db_pin.py` (fails on old conftest, passes now). Prod users = 2153 before and after baseline |
| 0.5 migrations 069–072 | verified | applied cleanly on prod clone `wheeldb_clone_test` |
| 0.6 repo hygiene | done | origin → `Tom1tk/LuckyWheel`; `/etc/cron.d/hiatus-deploy` removed; t231–t247 + t242-chat branches deleted |
| 0.7 clone script | done | `bin/clone-prod-to.sh` — tested (2153 = 2153), refuses `wheeldb` |

Prod `users` count is 2153 at G0; 2145 of those are leaked test accounts (removed at launch, §7).

Additional G0 evidence:
- Positive control: after the post-fix run `wheeldb_test` holds 17 `^t[0-9]` users (integration tests ran, landed in the test DB); prod 2153, staging 0 new.
- No `load_dotenv(override=True)` anywhere; the server subprocess inherits the pinned URL.
- Prod write tripwire: `pg_stat_user_tables` ins/upd/del per table saved to `/home/user/backups/prod_pgstat_G0.txt` (postmaster started 2026-08-21 11:42 — counters reset on restart). Diff at every gate; only bot `login_attempts` deltas are acceptable.
- Stub race (T242 flask stub collection order): not reproduced in either baseline run; no collection errors.
- `test_mobile_e2e` 12 errors: fixture logs in as a pre-existing account `testing7` that a fresh DB doesn't have (401). Server boot path is fine (drawer tests reach assertions). Fix by registering a throwaway user — folded into RV-08.
- **Until launch, the leak fix exists only on staging: never run pytest from `/home/user/wheel-app`.** Every subagent brief carries this line.

**G0: PASSED 2026-10-08.**

## Phase 1 — Spec (G1)

**G1: PASSED 2026-10-08.** `docs/SEASON_9_SPEC.md` (d74a60c, 270a229): usage audit with queries, Season 9 "Tides" (weekly tides 9.N, medals + cosmetics + encyclopaedia persist), tickets RV-01..12 with acceptance tests. Advisor was unavailable; self-review fixed Friday-anchored idempotency and S9-only medals.

## Phase 2 — Build (G2)

| Ticket | Status | Commit | Evidence |
|---|---|---|---|
| RV-01 season config + tides | merged | 2d01b7e | 48 tides/rollover/season tests pass (DB-backed) |
| RV-03 universal auto-spin (backend) | merged | 1345936 | 31 auto-spin tests; 5 new fail on pre-change base; 24h catch-up = 28,800 spins in ~0.57s, one tick |
| RV-04 weekly community goals | merged | 8e195c9 | 23 goal tests; goal keyed on tide (season_number) not ISO week; species goal retired (species persist) |
| RV-02 persist across tides | merged | 3ad1426 | 3 new DB tests (cosmetics/species/skin persist, theme equip, auto-spin carries over); suite 884 passed + baseline 16 |
| RV-09 Tides page theme | merged | 6022025 | built by orchestrator; mockup v2 approved by user 2026-10-08; checked at 390/768/1280/1920 (phones: lighthouse tucked to edge, boat clamped on-screen) |

Suite after RV-01/03/04: 881 passed, same 16 baseline Playwright failures.

Notes:
- Staging DB carried stale schema_migrations 73-76 from the abandoned July S9 attempt, so new 073-075 were skipped. Re-cloned wheeldb_staging from prod (users 2153 = 2153) and migrated 069-075 cleanly. **Prod is at 068: launch must apply 069-075.**
- Handed to RV-02: rollover sets auto_spin_since NULL unless season_registered (now never set) → must keep auto-spin running across tides; auth.py registration still grants page_season8 → use SEASON_CONFIG theme.
- Handed to RV-07 (frontend): HiatusScreen still calls removed /api/register-season.
- Design: all visual/creative passes done by the Opus orchestrator, not subagents (user, 2026-10-08). Mockup v1 rejected as too basic; v2 must keep prior seasons' design language.
