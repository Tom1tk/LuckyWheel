# Season 9 — "Tides" — design spec

Phase 1 output of `WHEEL_REVIVAL_PLAN.md`. Every decision here was made by the orchestrator, per D3 and D7. G1 has no human gate.

**One-line pitch:** a calm, readable wheel game that resets every Friday night. Each week is a new **tide** (Season 9.1, 9.2, …) with its own podium. Your **medals** and **collection** stay with you forever.

---

## 1. Feature usage audit

**Source.** Prod `wheeldb`, read-only, on 2026-10-08. "Real" players are `users.ip_address IS DISTINCT FROM '127.0.0.1'`, which gives 8 accounts. S8 is the live (unrolled) season, so `game_state` is S8 data.

**Queries used** (run as `wheelapp`):
```sql
select u.username, g.spin_count, g.catch_count, g.total_fish_clicks, g.dice_charges, g.wager_last_stake,
       g.prestige_count, g.equipped_class, g.active_wheel_mode, g.fish_exchange_total,
       array_length(g.aquarium_species,1), array_length(g.caught_species,1), g.insurance_tokens,
       g.guard_charges, g.auto_fish_enabled, array_length(g.owned_items,1), g.onboarding_step
from users u join game_state g on g.user_id=u.id where u.ip_address is distinct from '127.0.0.1';
select u.username, count(*) from build_loadouts b join users u on u.id=b.user_id group by 1;
select u.username, s.contributed from singularity_contributions s join users u on u.id=s.user_id;
select u.username, c.goal_id, c.contributed from community_goal_contributions c join users u on u.id=c.user_id;
select u.username, count(distinct bounty_date) from bounty_progress b join users u on u.id=b.user_id group by 1;
select ... from chat_messages where created_at between '2026-06-26 23:00' and '2026-06-28';  -- launch-day chat
```

| System | Real players who used it in S8 (of 8) | Signal | Call |
|---|---|---|---|
| Spin / wheel | 5 spun (453, 235, 76, 10, 5 spins); 3 never spun | the core loop | **Keep**, centre stage |
| Fishing (catch) | 6 caught fish | widely used, mostly passive | **Keep** |
| Fish clicks (manual) | 0 | dead | **Retire** the manual click counter from the UI |
| Encyclopaedia (species) | 2 (13, 3 species) | the collector hook | **Keep and persist across tides** |
| Aquarium | 0 | dead | **Retire** (hide panel, keep data) |
| Dice | no usage counter; `dice_charges` sits at its cap for most players | likely low | **Keep, hidden until first 3-streak** |
| Wager / insurance | 2 (dylan, tom7 staked) | niche, complex | **Keep, already purchase-gated** (`wager_unlock`) |
| Prestige | 4 (20, 4, 2, 3) | **runaway**: dylan hit P20 in ~15 h, and chat said "your honour he's hacking" | **Retire.** The weekly reset *is* the prestige loop |
| Classes | 1 (dylan) | 10M purchase, late game | **Keep** (shop-gated) |
| Loadouts | 2 | UI clutter, panel always visible | **Retire** (hide panel) |
| Singularity | 2 | server meter nobody read | **Retire** |
| Community goals | 4 contributed; none filled | targets 5–10× too large | **Keep, retuned to a weekly ~5-player scale** |
| Bounties | 4 (7, 4, 3, 1 days) | daily-return hook that worked | **Keep** |
| Guard / regen | 1 | niche protection | **Keep** (shop-gated) |
| Auto-spin | gated at 5k wins | S1–S6 had a free toggle | **Universal from spin 1**, with resume + offline catch-up |
| Chat | 5 talked | the social glue ("Lets Kill Tom!") | **Keep**, plus tide system messages |
| Onboarding | dead code since T114 | "Christ what's all this" | **Replace** with progressive disclosure (§2) |
| Community pot | component unmounted | dead | **Retire** endpoints from UI scope (already invisible) |

**The S8 "timed out" complaint** ("Why is my ass getting timed out", 27 Jun 13:44) is not a chat block or a login lockout. `chat_spam_tracking` shows block_count 0 for that player, and `login_attempts` has no failures. The remaining candidates are the 30 s **tab lock** (423, shown as a raw toast) and a flask-limiter 429. `apiFetch` has no 429 case, and the per-worker in-memory limiter storage makes it noisy. RV-11 fixes both message paths.

## 2. Day-one experience: the first 60 seconds

A returning player who logs in on launch night sees:

1. A **tide banner** across the top: "🌊 Season 9 · Tide 1 — resets Fri 21:00 (6d 23h)". The banner shows last tide's podium once one exists.
2. The **wheel**, the scoreboard, and an **Auto-spin** toggle, all on and usable from spin 1.
3. A right column showing only the **Leaderboard (this tide)**, **Shop**, and **Chat**.
4. A one-time, dismissible **"What's new in Season 9"** card with three lines: "Every Friday the tide turns: wins reset, medals are forever." / "Auto-spin is free and keeps going while you're away (up to 24 h)." / "Your fish collection carries over."

**Progressive disclosure** replaces the dead coach-marks. Each panel appears when it first becomes relevant, using `tide_spins` (this tide's `spin_count`) and ownership:

| Panel | Appears when |
|---|---|
| Fishing | `spin_count ≥ 10` or already caught a fish this tide |
| Bounties | `spin_count ≥ 25` |
| Dice | first time `streak ≥ 3` (then stays) |
| Community goal | `spin_count ≥ 50` |
| Wager, Guard, Lucky Seven, Classes | on purchase (existing gates) |
| Hall of Fame | always (a button in the tide banner) |

A panel appearing for the first time gets a one-shot "New!" pulse. That is all the onboarding there is. `onboarding_step` and the coach-mark JSX are deleted.

## 3. Weekly sub-season ("tide") model

### 3.1 Representation (smallest change)

- The schema already does most of this. There is **one** `seasons` row, and `advance_season()` increments the internal `season_number`, snapshots the top 3 into `season_snapshots`, writes `user_season_history`, and resets `game_state`. **A tide is just an ordinary `advance_season()`.** The unattended weekly job therefore runs on the oldest, most-exercised code path.
- Migration: `seasons.sub_number INTEGER NULL`. On S9, `player_facing_number = 9` stays fixed and `sub_number` goes 1, 2, 3, …. The label is `f"{pfn}.{sub}"` when `sub_number` is set, else `str(pfn)`.
- New table `season_log(season_number INT PRIMARY KEY, label TEXT NOT NULL, name TEXT, started_at TIMESTAMPTZ, ended_at TIMESTAMPTZ)`. `advance_season` inserts the **ending** season's row (`ON CONFLICT DO NOTHING`).
  - It is backfilled for past seasons from `season_snapshots` / patch-notes dates, best effort. The internal → player-facing map comes from the museum research in Phase 5.
  - This one table gives the Hall of Fame and the README museum a label for every internal season number.
- `advance_season(conn, player_facing_number=None, name=None, sub_number=None)`:
  - On launch: `advance_season(conn, 9, 'Tides', 1)`.
  - On weekly runs with no args, the default is: if the current row has `sub_number`, then pfn stays the same and `sub_number + 1`. Otherwise the existing pfn+1 behaviour applies.

### 3.2 What resets weekly vs persists

| Resets every tide (existing `advance_season` reset list) | Persists across S9 | Why |
|---|---|---|
| wins, losses, streaks, spin/win/loss counts | **Medals** (gold/silver/bronze counts, derived from `season_snapshots` + `season_log`) | the long-term chase that no one can run away with |
| all functional shop items and upgrade levels | **Cosmetic items + active cosmetics** (themes, trails, confetti, backgrounds, page themes, fish size) | losing cosmetics weekly feels like punishment; they cost *losses*, not wins |
| wager state, insurance, guard, dice, class | **Encyclopaedia** (`caught_species`) | a slow collection goal across tides |
| prestige (retired anyway), legacy_wins | `cumulative_wins` (already persists; tier gating) | unchanged |
| community goal progress (new goal set each tide) | chat, account | — |

- **Cosmetic** means `ITEM_CURRENCY[item] == 'losses'`, the existing split in `models.py` (`models.py:342`, everything not in `_FUNCTIONAL_SHOP_ITEMS`, fish skins included). `equipped_fish` is kept if its skin is still owned. The reset becomes `owned_items = (cosmetics owned) ∪ {season theme, auto_spin_unlock}`, and `active_cosmetics` is kept where still owned.
- `caught_species` is removed from the reset list.

### 3.3 Hall of Fame

- Medals count **S9 tides only** (`season_log.label LIKE '9.%'`). Older seasons appear in the tide list as history but award no medals.
- `GET /api/hall-of-fame` returns two things:
  - `{tides: [{label, name, ended_at, podium: [{position, username, wins}]}], medals: [{username, gold, silver, bronze}]}`, newest first.
  - Real users only. The podium is already filtered at snapshot time.
- **Panel**: the podium list per tide, plus a medal table. It opens from the tide banner.

### 3.4 Rollover chat message

A system message is posted after each tide:

> 🌊 Tide 9.N has turned! 🥇 A · 🥈 B · 🥉 C — Tide 9.N+1 starts now. Good luck!

It is posted via the existing system-message path, which has a per-worker throttle. The message is inserted directly so the throttle can't drop it.

## 4. Rollover automation (D6)

- **Season config** (`season_config.py`, a plain dict, no new dependency) holds `theme_item`, `name`, community-pot reset values, and the weekly community-goal set. `seasons.py` reads it instead of the hardcoded `'page_season8'`, `'Casino'` and `40000`. This removes the S8 launch-bug class.
- **`bin/rollover.sh`** is run by `wheel-rollover.timer` (`OnCalendar=Fri 21:00 Europe/London`, `Persistent=true`) → `wheel-rollover.service` (oneshot, as `user`). It runs these steps:
  1. **Idempotency.** `advance_season` sets `ends_at` to the **next Friday 21:00 Europe/London** (not now+7d), so the launch tide simply runs until the first Friday. The job no-ops (exit 0, "tide not due") unless the current `ends_at <= now()`. A second run in the same week is therefore a no-op, and `Persistent=true` catches up after downtime.
  2. `bin/clone-prod-to.sh wheel_rollover_rehearsal`.
  3. `bin/advance_tide.py --db wheel_rollover_rehearsal` (asserts `current_database()`).
  4. `bin/post_rollover_check.py --db wheel_rollover_rehearsal`. Any failure means abort.
  5. Back up prod (`backup-wheeldb.sh`), then `bin/advance_tide.py --db wheeldb`.
  6. `bin/post_rollover_check.py --db wheeldb`.
  7. Post the chat message (step 3.4 is done inside `advance_tide.py` in the same transaction), then drop the rehearsal DB.
  - Any failure: exit non-zero, write `/home/user/wheel-app/ROLLOVER_FAILED` with the log path, and leave prod untouched if the failure came before step 5. systemd journal keeps the log.
- **`post_rollover_check.py`** asserts all of the following:
  - The `seasons` label advanced by exactly 1.
  - The new `season_log` row exists.
  - Every `game_state` has `wins = 0` and owns `auto_spin_unlock` + the configured theme.
  - No owned or active item is missing from `SHOP_ITEMS` ∪ retired cosmetics.
  - Cosmetics count per user ≥ before (a sample).
  - `caught_species` is unchanged.
  - The snapshot rows exist (when ≥1 real player had wins > 0).
  - The users count is unchanged.
  - `/api/season` and `/api/hall-of-fame` return 200. This is checked only against the live service when `--db wheeldb`.

## 5. Theme & name — "Tides"

- **Name and arc.** "Tides" ties back to the S5–S6 ocean era, and fishing is the system that survived the most seasons. The weekly reset reads as a natural tide.
- **Page theme `page_season9`.**
  - Deep navy → teal vertical gradient (`#0b1d33 → #0f4c5c`).
  - A slow two-layer CSS wave band along the bottom edge (pure CSS, `transform` animation, disabled by low-spec mode and `prefers-reduced-motion`).
  - Sea-glass accent `#7fd1c7`, sand text accents `#f2e3c6`.
- **Wheel.** Sea-glass teal / sand / coral (`#ff7f6e`) segments. The jackpot keeps the blue the user picked.
- **No new background script.** The S9 Arcade assets are scrapped.
- Mockup: `docs/img/s9-tides-mockup.png` (CSS mockup, see §7 RV-09 for the real build).

## 6. Friction fixes

- **Auto-spin.**
  - Salvage mig 076: grant `auto_spin_unlock` to all players, at registration, and on every reset. The 5k gate is gone.
  - On reload, **resume** instead of stopping. The client sees `auto_spin_active: true` and keeps ticking.
  - **Offline catch-up**: the stale cutoff is raised from 60 s to 24 h. Ticks process due spins in chunks of `MAX_SPINS_PER_TICK`, and a "While you were away: N spins, +X wins" summary is shown.
  - Fix the latent `/api/register-season` bypass by deleting the route; `HiatusScreen` is dead.
- **429 / 423 handling.**
  - `apiFetch` maps 429 → "Slow down a moment — try again in a few seconds." and 423 → "The wheel is open in another tab/device — this tab is paused." with a **"Play here"** button. That button takes the lock over via `/api/tab/heartbeat` with `takeover: true`.
  - Bite-poll limit 4/s → 8/s (the client polls at exactly 4/s today).
  - Set `REDIS_URL` if Redis is available on the box; otherwise leave the in-memory limiter but raise the per-route limits that polling clients sit at (bite-poll only).
- **Numbers.** With a weekly reset, magnitudes stay in the millions–billions. `format_wins` is kept, and the scientific/"pascal" formats are capped at the K/M/B/T suffixes the UI already has.

## 7. Tickets (Phase 2)

**Owners:**
- "sub" means a Haiku subagent working in its own worktree off `staging`.
- "orch" means the orchestrator.
- Tickets that touch `app.jsx` / `styles.css` run **serially**.
- Each ticket must meet the definition of done in plan §5.2.
- **Brief line for every agent: never run pytest from `/home/user/wheel-app` (prod `.env`).**

| # | Ticket | Files | Acceptance tests (must fail before the change) | Owner | Group |
|---|---|---|---|---|---|
| RV-01 | Season config + tide model | `season_config.py` (new), `seasons.py`, `migrations/073_season_tides.sql` (`sub_number`, `season_log`) | `advance_season(conn, 9, 'Tides', 1)` sets label "9.1"; a no-arg call then gives "9.2"; a `season_log` row is written for the ended season; the theme comes from config (a test patches config → reset grants that item) | sub | backend-1 |
| RV-02 | Persist cosmetics + encyclopaedia across tides | `seasons.py` | after rollover the user keeps `trail_2`/`theme_ice`/`page_season5` and active cosmetics, loses `winmult_3`/`wager_unlock`, keeps `caught_species`; owns `auto_spin_unlock` + theme | sub | backend-1 (after RV-01) |
| RV-03 | Universal auto-spin, resume + 24 h catch-up | `models.py`, `auth.py`, `game.py` (`/api/tick` stale cutoff, delete `/api/register-season`), migration 074 (= salvaged 076), `app.jsx` resume | new user owns `auto_spin_unlock`; tick after a 2 h gap processes due spins (capped by chunking) and returns a catch-up summary; tick after >24 h processes 24 h; `/api/register-season` 404 | sub (backend), then frontend serial | backend-2 → FE |
| RV-04 | Weekly community goals | `community_goals.py`, `season_config.py`, migration 075 | goal set rotates per tide; targets are a ~5-player/week scale (fish 1,500, jackpots 100, wager 25k, species 100); `goal_prestige50` removed | sub | backend-3 |
| RV-05 | Hall of Fame backend + rollover chat message | `seasons.py`, `game.py` (`/api/hall-of-fame`) | endpoint returns tides newest-first with podium + medal counts; test users excluded; rollover inserts the 🌊 system message | sub | backend-1 (after RV-02) |
| RV-06 | Retire prestige, loadouts, singularity, aquarium, manual fish-click UI, onboarding code | `models.py` (`RETIRED_ITEMS`), `game.py`, `app.jsx` | `/api/buy prestige_unlock` → 403; panels absent from the DOM; data is not deleted | sub | FE serial #1 |
| RV-07 | Progressive disclosure + "What's new" card | `app.jsx`, `styles.css` | Playwright: fresh user sees only wheel/scoreboard/leaderboard/shop/chat; after 10 spins fishing appears; card dismiss persists (localStorage, try/catch) | sub | FE serial #2 |
| RV-08 | Tide banner + Hall of Fame panel; fix the `test_mobile_e2e` fixture (register a throwaway user instead of `testing7`) | `app.jsx`, `styles.css`, `tests/test_mobile_e2e.py` | banner shows "Season 9 · Tide N" + countdown; HoF panel lists tides/medals; the 12 mobile_e2e errors become passes or real failures | sub | FE serial #3 |
| RV-09 | Tides page + wheel theme | `styles.css`, `app.jsx` (theme map), `models.py` (`page_season9`) | `page_season9` in SHOP_ITEMS; screenshot desktop + mobile reviewed by orch; reduced-motion disables waves | sub, orch review | FE serial #4 |
| RV-10 | Rollover automation (incl. `ends_at` = next Fri 21:00 London) | `bin/rollover.sh`, `bin/advance_tide.py`, `bin/post_rollover_check.py`, `deploy/wheel-rollover.{service,timer}` | on two clones: run with `ends_at` in the past advances + checks green; immediate re-run is a no-op ("tide not due"); `ends_at` after a Wednesday launch is that Friday 21:00 London; an injected check failure leaves the "prod" clone untouched and writes the marker; `systemd-analyze calendar` shows the next Friday 21:00 | sub, orch audit | ops |
| RV-11 | 429/423 messages, tab takeover, bite-poll limit | `app.jsx`, `game.py`, `extensions.py` | unit test on the limit string; Playwright: two contexts → second gets the "Play here" banner and can take over | sub | FE serial #5 |
| RV-12 | Patch notes for S9 + README season text draft | `patch_notes` source, docs | the patch notes endpoint returns the S9 entry | orch | docs |

**Migration numbering.** Staging's last migration is 072, so the new ones are 073 `season_tides`, 074 `auto_spin_universal`, and 075 `community_goals_weekly`. Salvaged 073/074 (Arcade theme, singularity retune) are dropped.

**Salvage decisions closed:**
- Prestige titles: **scrapped**, because prestige is retired.
- Dragonfish: **scrapped**, no new content needed.
- Arcade themes/skins/`arcade-bg.js`: **scrapped**.

**🤖 G1 check:**
- Every §1 call has a reason.
- Every ticket has acceptance tests.
- Migrations are numbered without collision.
- Reset/persist lists are consistent with RV-02.
- Retire list is consistent with RV-06.
- Disclosure gates are consistent with RV-07.
