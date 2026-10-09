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
| RV-06 retire prestige/loadouts/singularity/aquarium/onboarding | merged | e1bdce2 | 8 routes 410, prestige_unlock/aquarium buy 403 (RETIRED_S9_ITEMS); leaderboard ranks by wins; 12 new tests; suite 820 passed + 14 baseline (2 baseline e2e deleted with aquarium); prestige_level reset + aquarium dropped at rollover so no bonus survives launch; singularity meter unfilled on prod clone so mode unreachable; copy: "Welcome to the Tides!", "🎣 Fishing" |
| RV-05 Hall of Fame + rollover message | merged | 2009355 | built by orchestrator; GET /api/hall-of-fame (tides newest first + S9-only medals); 🌊 message on tide->tide only, unthrottled; start_weekly_goal wired into advance_season; bug fixed: podium skipped 0-win players (would have awarded medals on a dead tide); suite 824 passed + 14 baseline |
| RV-07 progressive disclosure + What's new | merged | 3faa312 | built by orchestrator; Fishing at 10 spins or any fish this tide, Bounties 25, Dice at first 3-streak, Community goal 50; unlocks persist in localStorage `tidesSeenPanels` (spin_count resets each tide); panels open on load are silent, in-session unlocks pulse sea-glass + "✨ New: …" toast; one-time S9 card (`whatsNewSeen_s9`) after patch notes; HiatusScreen register-season call removed; checked in browser at 390/1280 (card, gating, 9→10 spin unlock, reload persistence); e2e helper seeds all panels unlocked; suite 824 passed + 14 baseline |
| RV-08 tide banner + Hall of Fame panel + e2e fixture | merged | 8ca02e0 | built by orchestrator; user-bar banner "🌊 Season 9 · Tide N · resets Fri 21:00 · countdown · last-tide podium · 🏛 Hall of Fame" (podium/resets hidden ≤1100px; phones show "🌊 9.N + countdown", tap opens HoF); old SeasonInfo kept for non-tide seasons; /api/state season now carries sub_number; HoF panel: S9 medal table + past tides with podiums, empty/error states; checked at 390/768/1280 with mocked Tide 2 + real empty endpoint. e2e fixture registers a throwaway user: 11 errors → passes; exposed a real bug: Leaderboard rendered nothing with 0 rows (every Friday after reset) → now shows "No wins yet. Spin to take the top spot."; suite 833 passed + 5 baseline (drawer ×4, centering ×1 — both still log in as testing7) |
| RV-11 429/423 messages + tab takeover + bite-poll limit | merged | fc52734 | built by orchestrator; apiFetch maps limiter 429 (HTML body) → "Slow down a moment — try again in a few seconds.", 423 → "The wheel is open in another tab — this tab is paused." banner (What's-new card style) with **Play here** → `/api/tab/heartbeat` `takeover: true`; spin no longer double-toasts on 423; bite-poll 4/s → 8/s; no Redis on the box so limiter stays in-memory. Copy says "tab", not "tab/device": logging in elsewhere ends the first session (401), so only same-browser tabs hit 423. tests/test_tab_takeover.py (Playwright two tabs: banner → Play here → old tab 423, new tab spins); checked at 390/1280; suite 835 passed + 5 baseline |
| RV-10 weekly rollover automation | merged | 767c99b, 90e9ef7, 68e636a (merge 7739f49) | `bin/advance_tide.py` (Friday-anchored, idempotent, asserts DB, `--check-only` exit 10 = due), `bin/post_rollover_check.py` snapshot/verify (label, season_log, wins reset, theme + auto-spin grants, known items incl. fish skins, cosmetics/species kept on 50-user sample, snapshot rows, users ≥, live /api/season + /api/hall-of-fame), `bin/rollover.sh` (flock, rehearse on prod clone → backup → prod → verify; any failure writes `ROLLOVER_FAILED` and leaves prod untouched), `deploy/wheel-rollover.{service,timer}` Fri 21:00 Europe/London, Persistent (**not installed**). Acceptance: 9.2→9.3 all PASS on rehearsal + stand-in; re-run = not due, exit 0; forced check failure = exit 1, marker, prod untouched. Found the bigint overflow → migration 077. wins_reset is skipped when `--live-url` is set (auto-spin earns wins within seconds on a live DB). Live HTTP checks first exercised in Phase 3.2. Suite 844 passed + 5 baseline |
| RV-12 S9 patch notes + README season text | merged | 7c8158e | written by orchestrator; `PATCH_NOTES.md` leads with "Season 9 — Tides" (heading has no date: **stamp the launch date at launch**); tests/test_patch_notes_s9.py; panel checked at 390/1280; README blurb in `docs/README_S9_DRAFT.md` for Phase 5. H2 checklist note: shop still lists "Auto-Spin Unlock · 5K" (shows ACTIVE for everyone) |

Suite after RV-01/03/04: 881 passed, same 16 baseline Playwright failures.

Notes:
- Staging DB carried stale schema_migrations 73-76 from the abandoned July S9 attempt, so new 073-075 were skipped. Re-cloned wheeldb_staging from prod (users 2153 = 2153) and migrated 069-075 cleanly. **Prod is at 068: launch must apply 069-075.**
- Handed to RV-02: rollover sets auto_spin_since NULL unless season_registered (now never set) → must keep auto-spin running across tides; auth.py registration still grants page_season8 → use SEASON_CONFIG theme.
- Handed to RV-07 (frontend): HiatusScreen still calls removed /api/register-season.
- Design: all visual/creative passes done by the Opus orchestrator, not subagents (user, 2026-10-08). Mockup v1 rejected as too basic; v2 must keep prior seasons' design language.
- season_log backfill: **migration 076** (this). Map resolved from git history: internal 1–6 = S1–S6; 7 = S7 (24 Apr auto-rollover into the hiatus "Mid-Season 6.7", S7 Endless from 30 Apr, podium = 9 May "correct S7 winners"); 8 = "7.7" (9 May–26 Jun, High Stakes was a mid-season update); internal 9 = S8 Casino, labelled by advance_season at launch. Dates from season_snapshots; tested twice on a staging clone (8 rows, second run no-op), applied to wheeldb_staging. HoF: only labels ≥9 with a dot read "Tide", so 7.7 shows "Season 7.7"; list heading "Past tides" → "History". Suite 836 passed + 5 baseline. **Launch must apply 069–077.** 077 widens user_season_history win columns to NUMERIC: RV-10 rehearsal found advance_season overflowing bigint on a ~1e38 prod player (launch would have aborted); launch S8→9.1 then rehearsed OK on a prod clone with 069–077.

## Phase 3 — Staging rehearsal (G3)

| Task | Status | Evidence |
|---|---|---|
| 3.1 re-clone prod → staging, migrate | done | backup `/home/user/backups/wheeldb_staging_pre_phase3.sql.gz`; clone users 2153 = 2153; 069–077 applied cleanly |
| 3.2 launch + weekly rollover | done | `advance_season(conn, 9, 'Tides', 1)`: S8 → 9.1, wins reset, season_log 9 rows, /api/season + /api/hall-of-fame 200. `bin/rollover.sh` against wheeldb_staging (tide forced due): rehearsal + live 9.1 → 9.2, all checks PASS incl. live_season / live_hall_of_fame (first run of the live checks), exit 0. **Launch decision (H3):** S8 podium would be dylan ~1.04e38 wins (44 losses, the overflow player), then 149, then 62 |
| 3.3 browser E2E 1366×768 + 390×844 | done | register, What's new, banner, 12 spins, auto-spin start/resume/stop, shop buy, equip theme, Hall of Fame PASS at 1366; banner, spins, auto-spin, HoF PASS at 390; fishing cast → bite → reel PASS at both (orchestrator re-check). Chat: POST 201, but the feed hides localhost-registered posters by design (chat.py), so not checkable from the box. Found + fixed: (a) page load stopped server-side auto-spin (T216 leftover; made "While you were away" unreachable) → 08bfbc0, `tests/test_auto_spin_resume.py` fails before / passes after; (b) phones: the spinning wheel canvas widened the page to ~424 px on 390, zooming out and pushing the countdown off-screen → `overflow-x: clip` ≤768 px, 51cc51a (424 → 390 measured) |
| 3.4 console errors | done | 0 console errors/warnings, 0 pageerrors, 0 HTTP ≥ 400 across all runs; collectors proven by a probe that triggers each |
| 3.5 timer on staging | done | `wheel-rollover-staging.{service,timer}` (APP_DIR staging, PROD_DB wheeldb_staging, LIVE_URL :5001, own rehearsal DB, `/home/user/backup-wheeldb-staging.sh`) installed; one-off test schedule fired 17:51 under systemd: 9.2 → 9.3 all PASS, Result=success; test drop-in removed, next run Fri 2026-10-09 21:00 BST. Found + fixed: staging and prod shared one flock file, so at Friday 21:00 one would exit 0 and skip its tide for a week → lock per DB, b35549b |

Staging reset for H2: fresh prod clone, 069–077, launched to 9.1 (users 2153). The staging timer will turn it to 9.2 on Fri 9 Oct 21:00.

Notes for H2/H3:
- Hall of Fame entries for test users created from localhost are filtered like chat; real players are unaffected.
- ~~Mobile "last catch" chip off-screen~~ fixed e868839. ~~Stale heartbeat comments~~ and ~~Auto-Spin Unlock in the shop~~ fixed aa59a0a.

**G3: PASSED 2026-10-08.** Next: H2, tom7 playtests staging with `docs/PLAYTEST_CHECKLIST.md`.

### H2 round 1 (2026-10-08, tom7 feedback)

- **S8 podium (H3):** keep as is, dylan ~1.04e38 first. Auto-Spin Unlock removed from the shop (aa59a0a).
- Fixed and checked by Playwright E2E on `claudeqa1`: Long Shot drew the Steady wheel (missing `WHEEL_MODE_DRAW` row; new `tests/test_wheel_mode_draw_table.py`); wheel covered "click to spin" on desktop; hub star sat low; stake slider (set 20% → server 20% → loss took 20%); mobile pointer/subtitle, Long Shot wrapping, balance over stake panel (e92370d). Stake panel under the pointer below 1366 px, mobile catch chip, result lines over the spin prompt, doubled Patch Notes title (e868839).
- Incident: an earlier reset of testing7 wiped its purchases mid-playtest; `wager_unlock` re-granted, three other items need re-buying. QA now uses `claudeqa1` only.
- README (readme-revival 1c1a44f): rebuilt hero GIF (≈1 s per season, ends on the banner, per-era wheel and clicker fish), per-season clips, `docs/SEASON_MUSEUM.md`.
- Known, left as is: the one-off "✨ NEW: …" unlock chip briefly covers WINS/LOSSES; the YOU WIN banner briefly overlaps the shop edge at 1366 px.

### H2 round 2 (2026-10-09): Season 9 "Charts" rework

Spec: `docs/SEASON_9_DEEP_SPEC.md` (Charts talent trees, Surge, fish fight, 46-species catalogue). Tickets D1–D5.

- **D1 backend:** `talents.py`, migration 078, `/api/charts` GET/POST (refund once per London day), gear shop locked (403), staked spin costs 1 🪙 chip, Surge in spin + tick, Spring Tide / Rogue Wave rules, staked jackpot ×5, REGEN 25, goal reward 10 chips, rollover clears Chart/Surge/chips and keeps `fish_records`. Tests: `tests/test_charts.py`, rollover case in `tests/test_season_tides.py`.
- **D3 backend:** `fish_catalog.py` (46 species; London window / tide / migrant availability; Deep Sea filter and ×1.5 bite wait), `GET /api/fish-catalog`, size (kg) and size-scaled 🐟 value, `fish_records`, Surge from catches at all three sites (manual reel, auto-fish tick, AFK catch-up; ×0.25 auto, none for Rogue Wave). Junk is worth 0. Manual reel uses neutral quality 0.5 until the D4 fight. Tests: `tests/test_fish_catalog.py`.
- **D2 Charts UI** (cb5361b): 🧭 Charts panel (three trees, row/keystone locks with the spec tooltips, pending → "Set course", "Re-chart (1 left today)" / "Re-chart tomorrow"), pulsing dot while points are unspent; keystone client rules (Spring Tide hides stake + dice, Rogue Wave dice ×2 speed / +2 charges); shop functional tab replaced by the Charts notice. E2E on `claudeqa1` / `claudeqa2`: allocate, lock rules, set course, re-chart.
- **D4 Fight** (5345171): `/api/reel` now hooks (species hidden), `POST /api/land {landed, quality}` (≥ 60% of `fight_s`, ≤ 45 s, quality clamped), Catch of the Day ×5 universal, Precise Angler removed, wins exchange closed (403). Client tension fight (hold mouse / touch / Space; Space no longer spins the wheel during a fight), snap / slip, Steady Hands zone. Tests: `tests/test_fight.py` (13 live), `TestLandLine`; E2E mouse, Space, snap, slip.
- **D5 polish** (489c2ec): Encyclopaedia reads `/api/fish-catalog` (now also returns the player's `caught` + `records`): 46 entries sorted junk → legendary, "Discovered N / 46 · Tide: High (turns in Xh Ym)", Biting now badge, when-icons (🌅 ☀️ 🌇 🌙 / 🌊 🏖️ / 🧭), hints, record kg, hue-rotate. 🌊 Surge chip under the scoreboard ("🌊 Surge ×M · N spins", hidden for Rogue Wave), kept in sync from spin, tick, land, auto-fish and bounty claims. Bounties show and toast their Surge reward (`reward_surge` in `/api/bounties`). Tab-less shop (notice → fish exchange → skins → cosmetics). "Claim 3 free stake chips". What's New and PATCH_NOTES rewritten for Charts / Fight / Surge / 46 species.
- **E2E (2026-10-09, `claudeqa1`, 1366×768 + 390×844):** What's New 3 lines; encyclopaedia 46 entries, header, 24 biting badges, hints, records, junk first; Surge chip matches server (13 → 12 after one spin); bounty labels in Surge; no shop tabs; cosmetic buy; mobile fight lands (Minnow 0.034 kg, +7 Surge, new record); mobile encyclopaedia no horizontal scroll; 0 pageerrors. Re-chart: first allowed, second same day 409 "You can re-chart once a day — come back tomorrow.", adding points back allowed, UI shows "Re-chart tomorrow". Full pytest: 1035 passed.
- Known, left as is: `isMobile` is read once at load (pre-existing), so resizing desktop → phone without a reload hides the fishing panel.
- **Bounty pool** (found in D5 E2E): 4 of 6 bounties needed Riptide gear (stake, jackpot, bank, double-down), so a Swell or Angler player could finish at most 2 of 3. The pool is now build-neutral: Catch 10 fish, Reach a 10-spin win streak, Land 5 fish in a fight, Land a rare or legendary fish, Land a trophy fish (size ratio ≥ 0.9). Tests: `test_every_bounty_is_open_to_every_chart_build`, `TestLandLine::test_land_bounties`. Rogue Wave still earns bounty Surge it can't spend, which is part of that keystone's trade.
- **Rollover rehearsal on the new schema** (2026-10-09 01:45): cloned `wheeldb_staging` → `wheel_d5_rehearsal`, forced the tide due, ran `advance_tide.py` + `post_rollover_check.py verify`: 9.1 → 9.2, all checks PASS. Direct query afterwards: 0 rows with a Chart, Surge or chips; `fish_records` and `caught_species` kept (claudeqa1 3 records / 3 species, claudeqa2 likewise). New `charts_reset` check in `post_rollover_check.py` (PASS after the rollover; FAIL when one row was given Surge 3 by hand). Rehearsal DB dropped.
- Points are calendar-based (`talents.tide_day`), so between Fri 21:00 and the end of the rollover run (a few minutes) the panel can read "10 / 1 points" and saving fails with "Not enough points"; spins keep the old build. The rollover then clears the Chart. If the rollover fails (ROLLOVER_FAILED marker), this state persists until it is re-run.
- **Charts levels** (2026-10-09, tester feedback): points are now 1 + 1 free a day + bought, capped at 14; a bought point costs 1,000 × 6ⁿ wins, spent, reset each tide (migration 079 `chart_points_bought`, `POST /api/charts/level-up`, `charts_reset` check covers it). The shop's notice is replaced by a visual Chart strip (level, XP bar, talent icons) that opens the panel. What's New flag bumped to `whatsNewSeen_s9_levels`. Existing staging Charts built under the old 4 + day rule read as over-spent ("10 / 8 placed") until tonight's rollover clears them; prod starts empty.
- **Perf** (2026-10-09, tester: "lags on spin end", "low spec click lags"): spin results are server-side on click (~7 ms); the lag was two full-screen canvases repainting each frame. Tides background now paints its still layer once and animates at 1×DPR / 30 fps; the fire canvas stops clearing when there is no streak. 4× CPU throttle: idle 19 → 60 fps, spinning 9 → 60 fps, low-spec toggle ~490 → ~270–380 ms.
