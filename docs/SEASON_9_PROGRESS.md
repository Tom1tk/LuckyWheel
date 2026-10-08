# Lucky Wheel — Season 9 Progress

Progress log for Season 9 ("Arcade"). Newest entries on top.

## 2026-07-31 — Auto-spin + offline catch-up restored (T217)

- **Universal auto-spin:** `auto_spin_unlock` is granted to every player —
  new registrations (auth.py), season resets (seasons.py), and existing
  players via migration 076 (`migrations/076_auto_spin_universal.sql`).
  The backend gate and shop item stay (shown as "Owned"); the S8 5,000-win
  barrier is effectively gone.
- **Offline catch-up:** `MAX_SPINS_PER_TICK` raised 100 → 201,600 (~1 week
  at 3s/spin; back to S7 scale). Heartbeat auto-stop relaxed 60s → 24h
  (`/api/tick`). Client **resumes** an active server session on page load
  (reverses the S8 resume-prevention stop) so the first tick catches up on
  spins accrued while the tab was closed; a stale (>24h) tick stops and
  toasts.
- **Legibility kept:** 0%-stake auto-spin + stake-slider hiding unchanged.
- Tests: updated `test_auto_spin_visibility.py` (24h threshold guard,
  26h stale case, resume-on-load assertion) and added
  `tests/test_auto_spin_season9.py` (constants, registration/reset grants,
  migration 076, shop item, stake-hiding). Full touched-file subset green;
  ruff clean on new file.
- Patch notes: new "⚡ Auto-Spin for Everyone + Offline Catch-Up" section;
  Under-the-Hood counts bumped to 4 migrations (073–076) / 9 test files.
- Applied 076 to `wheeldb_staging` (0 pending), restarted service, verified
  live: fresh registration shows Auto Spin checkbox, start → reload → resume
  (wins tick up), manual stop clears `auto_spin_since`.

## 2026-07-31 — Implementation + staging rollover complete

- Backend done (wheel_modes/models/wagers/prestige/chat_triggers/
  community_goals/seasons/auth/loadout/bounties/game), migrations
  073–075 written. Frontend done (app.jsx/styles.css/index.html/
  arcade-bg.js/wheel-modes.js) and built (`make build`, app.js?v=79).
- New tests added: `test_zealot_mode`, `test_prestige_titles`,
  `test_stake_decay`, `test_payout_vault`, `test_season9_theme`,
  `test_dragonfish`, `test_singularity_retune`,
  `test_community_goal_retune` (57 new/updated unit tests, all passing).
  Updated stale pre-existing tests broken by S9 retunes (fish-skin price
  ceiling, community-goal caps, prestige_msg 3-arg call).
- **Found + fixed a real sync bug during testing:** the vault cap was
  applied to the persisted balance but `events['wins_delta']` stayed
  pre-cap, so the client's `setWins(prev => prev + wins_delta)` would
  drift by the vaulted amount on every capped spin. `wins_delta` now
  reflects the net post-cap change; the vaulted overflow is reported
  separately via the `vaulted` key.
- `make test-db-reset` leaves `wheeldb_test` tables owned by `postgres`
  (schema/migrations run as the superuser); granted ownership to
  `wheelapp` so the suite can write. Full run: 763 passed / 6 failed /
  132 errors (pre-existing failures + the module-stub race T242 describes
  in conftest.py — not regressions from S9).
- Staging DB (`wheeldb_staging`) applied all 16 pending migrations
  (057–070, 072 pre-S9 backlog + 073–075). Service restarted, boots
  clean, serves `arcade-bg.js?v=1`.
- **Rollover:** `advance_season(player_facing_number=9, name='Arcade')`.
  Season row now internal `season_number=8`, `player_facing_number=9`,
  name `Arcade`, 7-day window. All players granted `page_season9`;
  singularity target now 5M (progress preserved); `/api/state` returns
  `prestige_title`, decayed `max_stake_pct`, and the Arcade season block.
- Remaining (per SEASON_9_TICKETS): commit `staging` when ready.

## 2026-07-31 — Staging synced to master

- Staging was 108 commits behind master (frozen since the sync-staging
  workflow was disabled 2026-06-23). Merged `origin/master` into `staging`
  so S9 builds on current production code (all S8 hotfixes included).
- Removed the untracked `migrations/071_leaderboard_prestige_index.sql`
  (identical to master's tracked copy). Staging is now 0 behind / 2 ahead
  (postmortem doc + merge commit).

## 2026-07-31 — Planning complete

- Pulled live Season 8 (Casino era) analytics from `wheeldb`:
  - 5 real players spun; dylan hit prestige 20 + 1.03e38 wins in 453 spins;
    everyone else quit within two weeks (last chat 2026-07-07).
  - Season expired 2026-07-03, never rolled over — 4 weeks stale.
  - Singularity 147,930/100M (99.3% dylan); goals at 0–30%; fishing 0/5,000.
  - Bounties were the healthiest feature (all active players used them).
- Wrote `SEASON_9_PLANNING.md`, `SEASON_9_BUILD_SPEC.md`,
  `SEASON_9_TICKETS.md`, and this file.
- Design pillars: legible economy (vault + stake decay), community systems
  scaled to ~5 players, fresh-start rollover, keep-what-worked.
- Scope: Arcade theme + canvas bg, zealot + mirror rotation fix, dragonfish,
  prestige titles, vault cap + stake decay, singularity/goals/pot retunes,
  migrations 073–075, tests, docs, staging rollover + commit.
