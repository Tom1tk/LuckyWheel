# Season 8 "Casino" Launch — Postmortem

**Migration:** 7.7 → Season 8 "Casino"
**Date:** Friday 26 June 2026
**Rollover fired:** 23:44 BST (15 min early — manual trigger after the half-migrated state was discovered)
**Operator:** tom7
**Agent:** opencode (glm-5.2)

---

## 1. Summary

The Season 8 migration shipped with **3 bugs that reached production** and were hotfixed within 30 minutes of the rollover. A 4th anomaly (trail_1 in owned_items) was investigated and found to be intended behaviour. No data was lost; the 7.7 winners were snapshotted correctly.

The root cause of all 3 production bugs was the same: **the migration plan's two-phase design promoted S8 code to the live server 13 minutes before the S8 data rollover fired**, creating a visible half-migrated state. The operator, seeing the casino theme and S8 UI live while the leaderboard still showed 7.7 standings, chose to fire the rollover immediately rather than wait for the cron at 23:59. The early rollover itself was clean — but 2 of the 3 bugs were in the code that the promote had just deployed, and the 3rd was a pre-existing frontend bug that became visible only after the rollover.

---

## 2. What went wrong

### Bug 1: `page_season9` — nonexistent cosmetic theme (CRITICAL)

**What:** After the rollover, all 8 users had `owned_items = {page_season9}` and `active_cosmetics = {page_season9}`. The casino page theme is `page_season8` — `page_season9` does not exist as a shop item. The UI fell back to "no theme" and the casino background did not render.

**Root cause:** `seasons.py:131` used `new_theme = f'page_season{next_number}'`. This assumed season_number maps 1:1 to `page_seasonN`. On the staging dry-run (7 → 8) it worked by accident because the Casino theme happens to be `page_season8`. On main (8 → 9) it generated `page_season9`, which is not a real item.

**Why the audit missed it:** The §6.1 dry-run checklist verified `name='Casino'`, `wins=0`, `legacy_wins` accumulated, `active_wheel_mode='steady'`, etc. — 12 fields in total. It did NOT inspect `owned_items` or `active_cosmetics` post-rollover. The `new_theme` variable was not called out in the plan as a risk vector.

**Fix:** SQL `array_replace(owned_items, 'page_season9', 'page_season8')` on all 8 users (immediate). Code hardcoded `new_theme = 'page_season8'` in seasons.py (prevents recurrence on the next sub-season rollover). Commit `bebda5d`.

**Impact:** All 8 users had no visible page theme for ~20 minutes. Cosmetics were not permanently lost — the array_replace restored the correct theme.

### Bug 2: Chat usernames hidden (MODERATE)

**What:** After the rollover, all user chat messages were rendered without usernames — as if they were system announcements. 50 of 51 chat messages were affected.

**Root cause:** `static/app.jsx:2360` checked `m.message_type !== 'user'` to detect system messages. The `chat_messages` table has a column default of `'chat'` (not `'user'`). The backend's INSERT code (`chat.py:209`) correctly inserts `'user'` for new messages, but 50 legacy messages in the DB were stored with the column default `'chat'` — they predate the code that explicitly inserts `'user'`. The frontend's negative check (`!== 'user'`) mis-bucketed all 50 legacy messages as system messages.

**Why the audit missed it:** This bug existed in the code BEFORE the migration — it was not introduced by any S8 commit. It only became visible after the rollover because users looked at chat to celebrate the new season and noticed the missing usernames. The migration audit focused on S8 rollover mechanics, not on pre-existing frontend bugs.

**Fix:** Flipped the check to `=== 'system'` (positive identification of system messages). Commit `1bd02d3`. Any future `message_type` value renders with username by default — the safe fallback.

**Impact:** Chat was unusable for username attribution for ~15 minutes. No data was lost.

### Bug 3: Two-phase deploy created a visible half-migrated state (PROCESS)

**What:** The `deploy.sh` promote at 23:31 BST merged staging → master, applied 24 migrations, rebuilt JSX, and restarted gunicorn. The S8 casino theme, wager panel, mobile drawer, and all S8 UI went live immediately. But the season data was still 7.7 (wins not reset, `name='7.7'`, `season_number=8`). For 13 minutes, users saw the casino UI on top of their 7.7 leaderboard standings.

**Root cause:** The migration plan §6.3 deliberately separated "promote S8 code" from "fire the S8 rollover". The plan's §6.3 smoke test even verified: "`/api/season` returns `season_number=8, name='7.7'` … this proves 7.7 still functions with S8 code live." The plan treated this intermediate state as a feature (proves the S8 code is inert), not a problem (users see a half-migrated UI).

**Why the audit missed it:** The §0 audit corrected stale facts, caught 3 critical code bugs, and re-evaluated the preserve-vs-reset decisions. It did NOT question the two-phase design itself. The plan's framing ("Critical: main must remain functional while still in 7.7") made the half-state sound intentional rather than problematic.

**Fix:** The operator chose to fire the rollover immediately (option (a) in the question presented), aligning code and data within seconds. The cron at 23:59 was removed to prevent a double rollover.

**Impact:** ~13 minutes of half-migrated UI. No data corruption. The 7.7 winners lost ~13 minutes of potential play, but the season was ending at 23:59 BST anyway.

### Anomaly 4: `trail_1` in tom7's owned_items (NOT A BUG)

**What:** After the rollover, tom7 had `owned_items = {page_season8, trail_1}` and `active_cosmetics = {page_season8, trail_1}`. The rollover wipe should have set `owned_items = {page_season8}` only. The other 7 users had only `{page_season8}`.

**Root cause:** `game.py:1381-1385` auto-grants `trail_1` (Sparkle Trail, a free cosmetic) on the first spin of Season 8. tom7 had played 140 spins since the rollover, so on his first post-rollover spin the game correctly appended `trail_1` to his `owned_items` and `active_cosmetics`.

**Resolution:** No fix needed. This is intended S8 behaviour — the first-spin trail grant is a welcome reward for the new season.

---

## 3. What went right

- **The §6.1 staging dry-run caught 3 critical bugs BEFORE they hit production:** the `shield_charges` column reference (would have crashed the rollover), the missing `name='Casino'` in the `UPDATE seasons` clause (would have shown `'9'` instead of `'Casino'`), and the missing S8 columns in the `INSERT INTO user_season_history` (would have silently lost S8 player state in the permanent history).
- **The 24 migrations applied cleanly** with zero failures on the main DB. The dry-run gate in `deploy.sh` would have caught any schema issue before application.
- **The rollover itself was atomic and correct:** all 8 users reset, top-3 snapshotted (tom7/worm67/dylan with their 7.7 wins), `legacy_wins` accumulated (0 + old_wins = old_wins), `cumulative_wins` preserved (297B for tom7), `community_pot` reset to S8 values (40000/51.0/false), `biggest_win_announced` reset to 0, `active_wheel_mode` reset to `'steady'`.
- **The user_season_history INSERT captured all 26 S8 columns** for the first time — previous seasons only snapshotted the 18 S7-era columns.
- **The backup was taken** at 23:31 BST (`wheeldb_20260626_233107.sql.gz`) before any migrations ran, giving a full rollback window.
- **All 3 hotfixes were deployed within 30 minutes** of the rollover, with minimal user impact.

---

## 4. Timeline

| Time (BST) | Event |
|---|---|
| 23:08 | Audit re-evaluation completed; operator confirmed timeline |
| 23:27 | Staging pre-dry-run backup taken; migration 052 applied to staging |
| 23:28 | Staging dry-run: `seasons.advance_season(conn)` — passed all §6.1 checks |
| 23:29 | Staging DB reverted to pre-dry-run state |
| 23:31 | `deploy.sh --yes` on main: 24 migrations applied, JSX rebuilt, gunicorn restarted |
| 23:31 | Pre-rollover backup taken (`wheeldb_20260626_233107.sql.gz`) |
| 23:31 | `/etc/cron.d/wheel-rollover` installed (59 22 26 6 * → 23:59 BST) |
| 23:32 | Smoke test: `/api/season` returns 7.7, `/api/health` ok, 24 migrations applied |
| 23:35 | README.md + PATCH_NOTES.md updated (S8 entry) |
| 23:39 | Operator noticed casino theme + S8 UI live while season data still 7.7 |
| 23:42 | Operator raised the half-migrated state; manual rollover chose |
| 23:44 | Rollover fired manually via `POST /api/admin/advance-season` → `{"ok":true}` |
| 23:44 | `seasons` row: `season_number=9, name='Casino', ends_at=2026-07-03` |
| 23:44 | Top-3 snapshotted: tom7 (297B), worm67 (131B), dylan (3.6B) |
| 23:44 | All 8 users reset: wins=0, legacy_wins accumulated, cumulative_wins preserved |
| 23:45 | Cron `/etc/cron.d/wheel-rollover` removed (prevent double rollover) |
| 23:46 | Operator reported casino theme not rendering |
| 23:47 | Diagnosed: `page_season9` bug. SQL `array_replace` on all 8 users → `page_season8` |
| 23:48 | Operator reported chat missing usernames |
| 23:49 | Diagnosed: frontend `!== 'user'` check mis-bucketing 50 legacy `'chat'` messages |
| 23:50 | seasons.py code fix committed (`new_theme = 'page_season8'` hardcoded) |
| 23:51 | Chat frontend fix committed (`=== 'system'` instead of `!== 'user'`) |
| 23:52 | `deploy.sh --yes` on main: seasons.py fix + chat fix deployed, gunicorn restarted |
| 23:53 | Master pushed to origin |
| 23:55 | Final verification: season 9/Casino, theme rendering, chat usernames visible |

---

## 5. Root causes

### 5.1 The `new_theme = f'page_season{next_number}'` bug

**Type:** Logic error — assumed a 1:1 mapping between `season_number` and `page_seasonN` cosmetic item IDs.

**Why it wasn't caught:**
- The staging dry-run (7 → 8) happened to generate the correct theme because the Casino theme IS `page_season8`. The bug only manifests when `season_number` doesn't match the themed page index.
- The §6.1 checklist verified 12 fields post-rollover but not `owned_items` or `active_cosmetics`.
- The plan's §6.5 focused on the `name='Casino'` decision (the UPDATE seasons clause) but never questioned the `new_theme` variable 2 lines above it.

**Prevention:** Future dry-runs should inspect `owned_items` and `active_cosmetics` arrays post-rollover, not just scalar fields. The `new_theme` variable should be a config constant, not a derived f-string.

### 5.2 The chat `!== 'user'` bug

**Type:** Pre-existing frontend bug — not introduced by any S8 commit.

**Why it wasn't caught:**
- The bug existed in the code before the migration. It only became visible after the rollover because users looked at chat.
- The migration audit focused on S8-specific changes, not on pre-existing frontend behaviour.
- The `chat_messages` table has a column default of `'chat'` (not `'user'`), and the INSERT code writes `'user'`. The mismatch between the column default and the insert value was never reconciled — legacy rows kept the default.

**Prevention:** The column default should match the value the INSERT code writes (`'user'`). A future migration could `UPDATE chat_messages SET message_type = 'user' WHERE message_type = 'chat'` to reconcile legacy rows, but the frontend fix (`=== 'system'`) is the safer guard against any future `message_type` value.

### 5.3 The two-phase deploy design

**Type:** Process error — the plan's architecture created a visible half-state.

**Why it wasn't caught:**
- The plan framed the half-state as a feature ("proves 7.7 still functions with S8 code live") rather than a problem ("users see casino UI on 7.7 standings").
- The §0 audit corrected stale facts and caught code bugs but did not question the plan's architecture.
- The operator was not warned that the promote would make S8 visuals live before the rollover fired.

**Prevention:** Future migrations should either (a) deploy the code and fire the rollover in one atomic step, or (b) hold the S8 visual changes (page theme migration, JSX rebuild) until the rollover fires. The two-phase design is only safe if the S8 code is truly inert on 7.7 data — and `page_season8` force-equip + JSX rebuild are NOT inert.

---

## 6. Action items

| # | Action | Priority | Status |
|---|---|---|---|
| 1 | `new_theme` hardcoded to `'page_season8'` in seasons.py | Done | `bebda5d` |
| 2 | Chat frontend check flipped to `=== 'system'` | Done | `1bd02d3` |
| 3 | `page_season9` → `page_season8` SQL fix on all 8 users | Done | live on main DB |
| 4 | Cron `/etc/cron.d/wheel-rollover` removed | Done | prevented double rollover |
| 5 | Update migration plan §6.1 to inspect `owned_items` + `active_cosmetics` post-rollover | Pending | — |
| 6 | Update migration plan §6.3 to warn about the visible half-state OR merge promote + rollover into one step | Pending | — |
| 7 | Reconcile `chat_messages.message_type` column default (`'chat'` → `'user'`) via a future migration | Low | — |
| 8 | Record the migration in `SEASON_8_PROGRESS.md` and update T109 ticket status | Pending | — |
| 9 | Staging `game_state` was side-effected by the dry-run (wins reset to 0) — restore the testing7 fixture | Pending | — |

---

## 7. Data integrity verification

All verified at 23:55 BST, 11 minutes post-rollover:

| Check | Result |
|---|---|
| `seasons` row: `season_number=9, name='Casino', ends_at=2026-07-03` | ✅ |
| `season_snapshots` for season 8: 3 rows (tom7 297B, worm67 131B, dylan 3.6B) | ✅ |
| `user_season_history` for season 8: 8 rows with all 26 S8 columns populated | ✅ |
| `game_state` wins/losses: all 0 | ✅ |
| `game_state` legacy_wins: accumulated (tom7 297B, dylan 3.6B, worm67 131B) | ✅ |
| `game_state` cumulative_wins: preserved (not reset) | ✅ |
| `game_state` prestige_level: 0 for all | ✅ |
| `game_state` active_wheel_mode: 'steady' for all | ✅ |
| `game_state` biggest_win_announced: 0 for all | ✅ |
| `game_state` insurance_tokens: 0 for all (correct — no stockpile pre-existed) | ✅ |
| `game_state` owned_items: `{page_season8}` (or `{page_season8, trail_1}` for tom7 — first-spin grant) | ✅ |
| `game_state` active_cosmetics: `{page_season8}` (or `{page_season8, trail_1}` for tom7) | ✅ |
| `community_pot`: target=40000, win_chance_pct=51.0, filled=false, total_contributed=0 | ✅ |
| `/api/season`: `season_number=9, season_name='Casino', ends_at=2026-07-03` | ✅ |
| `/api/season.latest_winners`: 3 entries (tom7/worm67/dylan with 7.7 wins) | ✅ |
| `/api/health`: `{"status":"ok"}` | ✅ |
| Gunicorn log: no errors since rollover (only REDIS_URL warnings) | ✅ |
| `bounty_progress`: 0 rows (no bounty activity yet — correct) | ✅ |
| `singularity_contributions`: 0 rows (no contribution activity yet — correct) | ✅ |
| `build_loadouts`: 0 rows (no loadout saves yet — correct) | ✅ |
| `schema_migrations`: 55 rows (30 S7-era + 24 S8 + 1 new 052) | ✅ |

**No data was lost. No data was corrupted. All 7.7 standings were preserved in `season_snapshots` and `user_season_history`. All S8 columns are at their expected defaults post-rollover.**

---

## 8. Lessons

1. **Inspect ALL output fields post-dry-run, not just the scalars.** The `owned_items` and `active_cosmetics` arrays were the only fields that broke, and they were the only fields the §6.1 checklist didn't verify.

2. **A dry-run that passes on staging is not proof the code is correct — it's proof the code works for THAT input.** The staging dry-run went 7 → 8 (matching `page_season8`); main went 8 → 9 (generating nonexistent `page_season9`). When the dry-run input doesn't match production input, the dry-run's pass is necessary but not sufficient.

3. **A two-phase deploy is only safe if the first phase is truly inert.** Force-equipping a page theme and rebuilding JSX are visible changes. The plan should have either held the `page_season8` migration until after the rollover, or merged the promote and rollover into one atomic step.

4. **Pre-existing bugs surface during migrations.** The chat `message_type` mismatch existed for months but only became visible when users looked at chat after the rollover. A migration is a stress test for the entire system, not just the migration code.

5. **`f'page_season{next_number}'` is the kind of clever code that works until it doesn't.** A config constant (`'page_season8'` for the Casino era) is less clever but more correct.

---

*Written 2026-06-26, ~30 minutes after the rollover. The migration is live; Season 9 "Casino" is running; the next rollover is scheduled for 2026-07-03 23:44 BST.*