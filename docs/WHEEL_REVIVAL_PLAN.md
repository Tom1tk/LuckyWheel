# Wheel Revival — Master Plan

> **Status:** DRAFT v1 (2026-10-08). Awaiting gate **H1** (user dials in §2 decisions).
> **Owner:** tom7 (operator). **Orchestrator:** Claude (Opus) — plans, audits, owns judgement.
> **Implementers:** subagents (Haiku 5.5, xhigh) via the orchestrator rule — scoped briefs, audited diffs.
> **Repo authority:** `/home/user/wheel-app` (master, live, port 5000, `wheeldb`) is source of truth.
> `/home/user/wheel-app-staging` (staging, port 5001, `wheeldb_staging`) is where new work is built.

Three deliverables:

| Track | Deliverable | Ends at |
|---|---|---|
| **A — New Season** | A new season designed, built on staging, play-tested by tom7, launched on prod | Gate H3 → launch + 48h watch |
| **B — README revival** | GitHub README rebuilt around screenshots of every feature | Gate H4 → merged to master |
| **C — Season GIF** | Animated GIF of the wheel/page through every season, rebuilt from historical commits | Embedded in README (via B) |

---

## 0. How to use this document

- **Sections 1–2** are the thinking: a second opinion on why the game stalled, and the decisions the user must make.
- **Sections 3–8** are execution: phases, tickets, exit gates. Once §2 is dialled in (H1), the orchestrator runs 3–8 autonomously, stopping **only** at human gates.
- **Gate types**
  - 🧑 **Human gate (H*)** — stop, report, wait for the user. Never skipped, never self-approved.
  - 🤖 **Auto gate (G*)** — the orchestrator verifies with evidence (command output, screenshots, diffs) and proceeds. A failed auto gate = fix and re-run, or escalate if it fails twice.
- Progress is logged in `docs/WHEEL_REVIVAL_PROGRESS.md` (newest first), one entry per gate passed.

---

## 1. Second opinion — why Season 8 (and the game) stalled

### 1.1 What the S9 planning doc concluded
"One player solved the game in 24 hours and the numbers became unreadable" → fix with a payout vault, stake decay, and retuned community targets.

### 1.2 What the data actually shows

| Evidence | Source | What it says |
|---|---|---|
| Season winners were **10^58 → 10^300+** in S1–S4, and the group kept coming back every week | `season_snapshots` | Huge numbers are not new and were not fatal on their own. |
| S8 **casual players bounced on day one** (chud 10 spins, f22 5 spins, both last spun 27 Jun; griffin/p3nny/netenyahu never spun). The core three drifted off over 1–4 weeks (dylan 6 Jul, worm67 15 Jul, tom7 22 Jul). Chat effectively ends 27 Jun | `game_state.spin_count/last_spin_at`, `chat_messages` | Launch day lost the casuals; the core lost interest over weeks with no new launch to return for. |
| Last S8 chat lines: *"Christ what's all this"* (worm67), *"Why is my ass getting timed out"* (chud), *"WHAT is that pascal win number"*, *"too many big number"* | `chat_messages` | Overwhelm + friction (rate-limits) + a leaderboard settled on day one. |
| The onboarding modal was **disabled for the S8 launch** (T114) while S8 added ~10 new systems (wager, modes, prestige, bounties, goals, singularity, loadouts, aquarium, insurance, double-down…) | git `3674337`, S8 tickets | Biggest complexity jump in the game's history, with no onboarding. |
| **S8 is the only season where auto-spin wasn't available from the first spin**: S1–S6 had a free client-side toggle (`app.jsx` `autoSpin` state, verified at `3fa3873`…`ef5556d`), S7 made it server-side, S8 gated it behind 5k wins | git history (`git show <sha>:static/app.jsx`) | S8 removed the thing this group actually does: start the wheel and check back. |
| Each plan reverses the last: S8 killed auto-spin ("idle game killed S7"); S9 restored it and blamed big numbers instead | S8 / S9 planning docs | Pendulum design. Each season tears out what the last one bet on. |
| Cadence: **S1–S6 launched ~weekly** (21 Mar → 26 Apr). Then S7 ran **7 weeks**, S8 **expired 3 Jul and was never rolled**, S9 sat **uncommitted for 10 weeks** | `seasons`, `season_snapshots`, git | Every gap in launches = a drop in activity. Where chat exists (from S5 on), its spikes line up with launches (wk of 20 Apr, 22 Jun). |
| Population is a **fixed group of ~7 friends**; 1 real account created since March | `users` | Design for 7 friends who show up for events, not for growth or a whale economy. |

**Data caveats.** `login_attempts` keeps ~2 weeks only and is polluted by tests — not cited. Chat had test rows pruned (T241). Spin counts are per-season only (no spin log table). The S9 planning doc calls dylan "the operator"; the postmortem names tom7 — S9 doc is wrong on that point.

### 1.3 Second-opinion thesis

The game doesn't die from math. It dies from **four operational/design patterns**:

1. **Launches are the engine, and the launch cadence lapsed.** This group plays when there's a *new season to look at*. Weekly launches kept S1–S6 alive. When launches stopped (manual rollover, removed in `a2bf578`; long build cycles), so did the players.
2. **Complexity creep without onboarding.** Every season added systems and removed none. Day one of S8 presented a wall. The fix is *subtraction and progressive disclosure*, not more rules (vault + stake decay are two more rules to explain).
3. **Pendulum redesigns.** Ripping out the core loop (auto-spin) to "fix" engagement removed the reason casual friends kept a tab open.
4. **The race is decided on day one.** It isn't that numbers are *big*, it's that the week's competition is *over* within 24h, leaving 6 days with nothing to chase. (Note: per standing feedback, no new streak-mitigation mechanics are proposed — the fix is in competition *structure*, not spin math.)

### 1.4 What this implies for the new season (recommendation)

A **consolidation season**, not a content-dump season:

- **R1 — Make cadence automatic.** Scheduled rollover with a safety dry-run, plus a fixed season length. The game should never again silently expire.
- **R2 — Subtract.** Audit feature usage; *hide or retire* systems nobody used. Reveal remaining systems progressively (unlock-as-you-go), and ship a working onboarding.
- **R3 — Keep the idle loop.** Auto-spin for everyone + offline catch-up (salvage from S9 — this part of S9 was right).
- **R4 — Make every day a fresh race.** A **Daily Race** leaderboard (today's net wins, resets 00:00 UTC) alongside the season board, building on daily bounties (the one feature every active player used). A day-one runaway no longer ends the competition for the week. Season podium can be decided by *daily race points*, not by the largest compounded number — the user decides (D4).
- **R5 — One fresh coat of paint.** One new page theme + wheel theme for "it's new" launch appeal — enough to feel like a launch, small enough to ship.
- **R6 — Fix friction.** Review rate limits that hit real players (chud's timeout), remove the 2,145 test accounts polluting prod.

---

## 2. Decisions for the user (Gate H1)

Each has a recommendation. Reply with the IDs you change; anything not changed is accepted as recommended.

| ID | Decision | Options | Recommendation |
|---|---|---|---|
| **D1** | Season number & name | (a) player-facing **9**, new name · (b) keep "Arcade" name/theme · (c) other | **(a)** — S9 never launched, so the next prod season is player-facing 9. Name proposed in Phase 1 (2–3 options with theme mockups). |
| **D2** | What to salvage from the uncommitted S9 "Arcade" build | see §2.1 table | Salvage infra + auto-spin; drop vault & stake decay; content case-by-case |
| **D3** | Core direction | (a) consolidation season as per §1.4 · (b) S9 as built · (c) something else | **(a)** |
| **D4** | How the season podium is decided | (a) season total wins (as today) · (b) **daily race points** (1st=5, 2nd=3, 3rd=1 each day) · (c) both boards, podium = (a) | **(c)** for this season; revisit after |
| **D5** | Season length | 1 week · 2 weeks · 4 weeks | **2 weeks** — weekly burned content too fast; 4+ is where the group drifted |
| **D6** | Automatic rollover | (a) cron-scheduled, with pre-flight dry-run on a prod clone + auto-abort · (b) manual (status quo) | **(a)** — reverses `a2bf578`; the reason it was removed (surprise rollovers) is addressed by the pre-flight |
| **D7** | Feature retirement | Orchestrator proposes a hide/retire list from usage data in Phase 1; user approves in H1b | Approve list in H1b |
| **D8** | Prod test-account cleanup (2,145 `t…` users, 127.0.0.1, created 27 Jun–31 Jul) | delete · keep | **Delete** (after backup). The leak is still open — T246 didn't stop it (see 0.4) |
| **D9** | GIF framing | (a) wheel-only crop · (b) full page · (c) both (full page for README hero, wheel crop as a strip) | **(c)** |
| **D10** | Season → commit rule for the GIF | (a) launch commit · (b) **final commit of the season** (last look before the next launch) | **(b)** |
| **D11** | README screenshots | seeded fake users only (no real usernames/chat in a public repo) | **Seeded fake users** — not optional, listed for visibility |

### 2.1 S9 "Arcade" salvage table (D2)

The S9 work is preserved at `/home/user/backups/s9-snapshot-20261008/` (`s9-tracked.patch` + `s9-untracked.tgz` + `BASE_SHA`) and will be committed to a branch `archive/s9-arcade` in Phase 0 before anything touches staging.

| S9 item | Kind | Recommendation | Why |
|---|---|---|---|
| `advance_season(player_facing_number, name)` override | infra | **Keep** | Needed for any controlled rollover |
| Theme hardcoded in `seasons.py` (`page_season8` / `page_season9`) | infra bug class | **Replace with a parameter / season config** | Same bug class as the S8 `page_season9` launch bug; recurs every season |
| `wins_delta` post-cap sync fix | bugfix | Keep *if* vault kept; otherwise moot | — |
| `make test-db-reset` ownership grant to `wheelapp` | infra | **Keep** | Test suite can't write otherwise |
| Universal auto-spin + 24h offline catch-up + resume-on-load (T217, mig 076) | gameplay | **Keep** | R3 |
| Community goal & singularity retunes (mig 074/075) | balance | **Keep** (re-check targets vs 7 players) | Targets were unreachable |
| Payout vault cap | economy rule | **Drop** | New rule to explain; data doesn't support "big numbers" as the killer |
| Stake decay | economy rule | **Drop** | Same |
| Zealot mode (×100) | content | Drop or defer | Another mode on a pile the group didn't explore |
| Prestige titles | content | Optional (cheap, cosmetic, readable status) | — |
| Dragonfish | content | Optional (cheap) | — |
| Arcade page/wheel themes, fish skins, `arcade-bg.js` | content | Depends on D1 | Reuse if the user likes the look; else new theme |

---

## 3. Phase plan overview

```
Phase 0  Safety & baseline ............ 🤖 G0         (autonomous, runs now-ish after H1)
Phase 1  Season design spec ........... 🧑 H1b        (user approves spec + retire list + theme)
Phase 2  Build on staging ............. 🤖 G2         (subagents, tickets in §5)
Phase 3  Staging verification ......... 🤖 G3 → 🧑 H2 (tom7 play-tests ~15 min with checklist)
Phase 4  Launch on prod ............... 🧑 H3 go/no-go → 🤖 G4 post-launch checks → 48h watch
Phase 5  README revival ............... 🧑 H4         (user reviews rendered README on a branch)
Phase 6  Season GIF ................... 🤖 G6         (runs in PARALLEL from Phase 0 onwards)
```

Parallelism: **Track C (Phase 6) is independent** and starts as soon as G0 passes. Track B (Phase 5) waits on H2 so screenshots show the final season. Track A is serial.

---

## 4. Phase 0 — Safety & baseline (autonomous after H1)

| # | Task | Done when |
|---|---|---|
| 0.1 | Build branch `archive/s9-arcade` **from the snapshot only**: a scratch clone at `BASE_SHA` (`7c4f637`), `git apply s9-tracked.patch`, untar `s9-untracked.tgz`, add exactly those paths (never `git add -A`; never include `docs/WHEEL_REVIVAL_*`). Push to origin. | `git diff archive/s9-arcade` vs snapshot is empty; branch on origin |
| 0.2 | First dump `wheeldb_staging` to `/home/user/backups/wheeldb_staging_pre_revival.sql.gz`. Then discard the S9 working-tree changes in `/home/user/wheel-app-staging` (`git checkout -- .` + remove only the 18 S9 untracked paths listed in the tarball — not `git clean`), re-sync with master. | `git status` clean; `staging` 0 behind master |
| 0.3 | **Test baseline** (wrapped by 0.4's before/after prod `users` count): run full suite on master and staging; record failing test IDs in `docs/TEST_BASELINE.md`. Then attempt to fix the conftest module-stub race (T242) — if fixed in ≤1 subagent pass, baseline = 0 failures. | Baseline file exists; gate rule thereafter = "no new failures vs baseline" |
| 0.4 | **Prod-DB leak check**: record prod `users` count *before* 0.3 and compare *after*. The leak is known to be still open: T246 (`32c205e`, 29 Jun) routed pytest at `wheeldb_test`, yet test users kept appearing on prod until 31 Jul — the source is something other than pytest (suspect: E2E/Playwright or ad-hoc scripts hitting :5000). Find and fix it. | Count unchanged after both runs |
| 0.5 | Reconcile prod migrations: prod is at 068, master carries 069–072. `ip_address` already exists on prod `chat_messages` → confirm 072 is idempotent (`IF NOT EXISTS`) or mark applied. Dry-run all four against a prod clone. | `migrate.py --dry-run` on clone passes; plan for each recorded in progress log |
| 0.6 | Housekeeping: update `origin` to `git@github.com:Tom1tk/LuckyWheel.git`; remove stale `/etc/cron.d/hiatus-deploy` (points at a missing script); delete merged local branches `t231…t247`, `t242-chat`. | `git remote -v` shows LuckyWheel; cron file gone; branches gone |
| 0.7 | Create `bin/clone-prod-to.sh <dbname>`: pg_dump prod → restore into a throwaway DB (via `sudo -u postgres`, since `wheelapp` lacks CREATEDB). Used by Phases 3, 4, 6. | Script restores into `wheeldb_clone_test`; row counts match prod |

**G0 (auto):** all of 0.1–0.7 done with evidence in the progress log. 0.6 cron removal and branch deletion are covered by H1 approval of this plan; the D8 test-account deletion is **not** done here (it's in the launch runbook).

---

## 5. Phase 1–2 — Design spec and build (Track A)

### 5.1 Phase 1 — Season design spec (orchestrator, not delegated)

Output: `docs/SEASON_<N>_SPEC.md` containing:

1. **Feature usage audit** — per system, how many real players touched it in S7/S8 (from `user_season_history`, `game_state`, `bounty_progress`, `build_loadouts`, goal/singularity contributions). → proposed **keep / hide-until-unlocked / retire** list (D7).
2. **Day-one experience** — exactly what a returning player sees in their first 60 seconds; which panels are visible; the onboarding steps (fix and re-enable the T114-disabled modal, or replace it with 3 inline tips).
3. **Daily Race** spec — data model (prefer computing from existing per-spin updates; a `daily_race` table keyed `(user_id, race_date)` only if needed), endpoint, UI panel, end-of-day system chat message, podium rule per D4.
4. **Rollover automation** spec (D6) — season config row (name, pfn, theme id, length) replaces hardcoded values in `seasons.py`; cron entry calls a `bin/rollover.sh` that (1) clones prod, (2) dry-runs `advance_season` on the clone, (3) runs the post-rollover checklist (§7.3) on the clone, (4) only then rolls prod, (5) posts a system chat message. Any failure → abort + leave prod untouched + log.
5. **Theme** — 2–3 name/theme options with static mockups (screenshots of a CSS prototype), per D1.
6. **Friction fixes** — rate-limit review for `/api/spin` & friends (find what timed chud out); auto-spin defaults.
7. **Ticket list** — §5.2 skeleton refined into concrete tickets with files, acceptance tests, and owner (subagent vs orchestrator).

**🧑 H1b:** user approves spec, theme choice, and retire list. **Nothing is built before H1b.**

### 5.2 Phase 2 — Build (ticket skeleton, refined in Phase 1)

| Ticket | Scope | Files (expected) | Parallel group |
|---|---|---|---|
| RV-01 | Season config: theme/name/length out of `seasons.py` into a config row; migration | `seasons.py`, `migrations/`, `models.py` | backend-1 |
| RV-02 | Salvage infra from `archive/s9-arcade` (pfn/name override, test-db ownership) | `seasons.py`, `Makefile` | backend-1 (after RV-01) |
| RV-03 | Universal auto-spin + offline catch-up (salvage T217 + mig 076, renumbered) | `game.py`, `auth.py`, `seasons.py`, `app.jsx` | backend-2 → frontend |
| RV-04 | Community retunes (salvage 074/075, renumbered; targets re-checked for 7 players) | `community_goals.py`, `models.py`, migrations | backend-3 |
| RV-05 | Daily Race backend (table/endpoint/rollover at 00:00 UTC, system chat) | new `daily_race.py`, `game.py` hook, migration | backend-3 |
| RV-06 | Feature hide/retire per D7 (server flags, not deletion of data) | `models.py`, `game.py`, `app.jsx` | frontend |
| RV-07 | Onboarding / progressive disclosure | `app.jsx`, `styles.css` | frontend |
| RV-08 | Daily Race panel + podium display | `app.jsx`, `styles.css` | frontend |
| RV-09 | New page theme + wheel theme (+ background script if any) | `static/`, `models.py` | frontend (theme assets can be parallel) |
| RV-10 | Rollover automation: `bin/rollover.sh`, cron template, pre-flight checklist script | `bin/`, `seasons.py` | ops |
| RV-11 | Rate-limit friction fix | `extensions.py`, `game.py` | backend-2 |
| RV-12 | PATCH_NOTES + README season section (text only; screenshots in Phase 5) | docs | docs |

**Collision rule:** anything touching `static/app.jsx` / `static/styles.css` runs **serially** (one frontend agent at a time). Backend groups run in parallel only if their file sets are disjoint. Each agent works in its own worktree off `staging`; the orchestrator merges.

**Per-ticket definition of done (G2 applies per ticket):**
1. New/changed logic has at least one test that fails without the change.
2. Full suite: no new failures vs `TEST_BASELINE.md`.
3. `ruff` clean on touched Python; `npx babel` builds `app.js`; `?v=` cache-bust bumped when `app.js`/`styles.css` change.
4. Orchestrator has **read the diff** (not just the agent's report) and checked it against the ticket.
5. Merged to `staging`, pushed, staging service restarted and `/api/health` OK.

**🤖 G2:** all RV tickets merged on staging with the per-ticket evidence above.

---

## 6. Phase 3 — Staging verification (Track A)

| # | Check | Evidence |
|---|---|---|
| 3.1 | (Staging DB already dumped in 0.2.) Restore a **fresh prod clone into `wheeldb_staging`** (the old Arcade-rolled staging DB is discarded). Apply all pending migrations. | migrate status = 0 pending |
| 3.2 | **Rollover dry-run on the clone, using the real prod numbering** (prod is internal 9 / pfn 8 — staging's previous Arcade run used internal 8 / pfn 9, which did *not* exercise prod's path). Run via the RV-10 pre-flight, not by hand. | Post-rollover checklist §7.3 all green |
| 3.3 | Playwright E2E on staging (desktop 1366×768 + mobile 390×844): register → spin → auto-spin start/stop/resume-after-reload → shop buy → equip theme → fishing cast/reel → bounty view → daily race panel → chat send. | Screenshots + pass log in progress doc |
| 3.4 | Console-error sweep: zero uncaught JS errors across the E2E run. | Playwright console log |
| 3.5 | Write `docs/PLAYTEST_CHECKLIST.md` for tom7 (≤15 min, ~12 checkboxes, plus "anything feel off?" free text). | File exists |

**🤖 G3:** 3.1–3.5 green. → **🧑 H2:** tom7 plays staging (`:5001`) with the checklist. Feedback → fix tickets → re-run G3 → back to H2 until tom7 says go.

---

## 7. Phase 4 — Launch on prod (Track A)

Lessons from `SEASON_8_LAUNCH_POSTMORTEM.md` are encoded here as hard rules.

### 7.1 Pre-launch (auto, the day before)
- Full prod backup (`backup-wheeldb.sh`) + verify the dump restores into a clone.
- Final pre-flight: clone prod → apply migrations → deploy code → rollover → §7.3 checklist on the clone. Must be green within 24h of launch.
- Write the exact launch + rollback commands into the progress log (no improvising on the night).

### 7.2 🧑 H3 — Go/no-go
Orchestrator presents: pre-flight results, backup path, migration list, launch time, rollback commands. **User says go.** Outward-facing: affects the friends' accounts. Never autonomous.

### 7.3 Launch (single atomic window — no half-migrated state)
1. Maintenance flag on (or launch at a quiet hour) → backup.
2. D8: delete test accounts (`ip_address = '127.0.0.1' AND username ~ '^t[0-9]'`) and their dependent rows — row counts logged before/after.
3. `deploy.sh` (staging → master, migrate, build, restart) **immediately followed by** the rollover in the same script run. No gap between "new code live" and "new season live" (this was S8's half-migrated bug).
4. **Post-rollover checklist** (automated script, run against prod):
   - `seasons` row: `season_number`, `player_facing_number`, `name`, `started_at`, `ends_at` as configured.
   - Every real user: `wins=0`, `owned_items` and `active_cosmetics` contain the **configured** theme id and no non-existent shop item (the S8 `page_season9` bug), `auto_spin_unlock` granted.
   - `season_snapshots` has the old season's top 3; `user_season_history` rows inserted for every user.
   - `/api/health`, `/api/state`, `/api/season`, `/api/leaderboard`, `/api/chat` OK; chat shows usernames (the S8 bug #2).
   - Playwright smoke on prod with a throwaway account → screenshot → delete that account.
5. System chat message announcing the season.

### 7.4 🤖 G4 + 48h watch
- G4 = §7.3 checklist all green. Any red → roll back per the written commands, report to user.
- 48h: check `journalctl -u wheel-app` for errors and the spin/chat activity twice a day; summary to user at 48h.
- Write `docs/SEASON_<N>_LAUNCH_REPORT.md`.

---

## 8. Phase 5 — README revival (Track B)

### 8.1 Screenshot environment
- Throwaway DB `wheeldb_readme`, **seeded from scratch only** (schema + migrations + seed script — never a prod clone) with **fake users** (e.g. `reeltime`, `spinwizard`, `koi_pond`, …) and fake chat. **No real usernames or chat ever appear in a committed image** (D11).
- Run the staging code on port 5099 against that DB; seed state so each feature is visible (shop with items owned, fishing mid-reel, a populated leaderboard, an active daily race, a bounty board, prestige panel, etc.).

### 8.2 Shot list (each 1366×768 PNG unless noted, optimised with Pillow, ≤300 KB each)

| # | Shot | Notes |
|---|---|---|
| 1 | **Hero**: full page, wheel mid-spin | top of README |
| 2 | Wheel result: WIN + JACKPOT (blue segment) | short animated clip optional |
| 3 | Shop: upgrades tab + cosmetics tab | 2 images |
| 4 | Cast & Reel: bite moment + catch popup | |
| 5 | Fish Encyclopaedia / Aquarium | |
| 6 | Wager panel: stake, hot streak, bank | |
| 7 | Wheel modes selector | |
| 8 | Leaderboard + Daily Race | |
| 9 | Bounties + community goals | |
| 10 | Chat with system messages | fake users |
| 11 | Mobile view (390×844) | side-by-side pair |
| 12 | Season GIF (from Track C) | "History" section |

### 8.3 README restructure
- Hero image + one-line pitch + "Season N is live" badge-style line.
- **Feature tour**: one short section per screenshot (2–4 lines each) — replace the current 694-line wall with a scannable tour; move deep mechanics to `docs/MECHANICS.md` (nothing deleted, just moved).
- **Season history** section: the GIF + a table (season, name, dates, signature feature) built from `season_snapshots` / git (no real usernames in the public table unless the user opts in).
- Tech stack + local dev quickstart (verified: a subagent follows it from a clean clone and it works).
- Fix links: wiki Patch Notes link and every `fishspin` → `LuckyWheel`.
- Images live in `docs/img/` (not `static/`, so they aren't served by the app).

**🧑 H4:** README pushed to branch `readme-revival`; user reviews the rendered page on GitHub; approve → merge to master + push.
Auto pre-checks before H4: every image link resolves on the branch (GitHub API), total image weight ≤ 15 MB, no real usernames (grep the alt text + OCR-free check: seeded DB has no real users by construction).

---

## 9. Phase 6 — Season GIF (Track C, parallel)

### 9.1 Commit map (to be pinned in task 6.1 — **candidate** SHAs from git history)

| Frame | Season | Candidate commit (launch) | Date | Note |
|---|---|---|---|---|
| 0 | Prototype | `30def55` | 19 Mar | Flask-only, static wheel, no DB — simplest frame |
| 1 | S1 | `3fa3873` (roulette green/red) | 20 Mar | First Postgres era |
| 2 | S2 | *find: commits 21–26 Mar* | 21 Mar | snapshot S1 dated 21 Mar |
| 3 | S3 | `7454a97` (blue/orange) | 27 Mar | |
| 4 | S4 | `bc578ba` | 4 Apr | |
| 5 | S5 Ocean Casino | `2be6a2c` → `b1689b2` | 10 Apr | animated seabed |
| 6 | S6 Night Ocean | `ef5556d` | 17 Apr | |
| 7 | S7 Endless | `d8094d3` → `919df43` (wormhole) | 26–30 Apr | |
| 8 | S7.7 | `6d0bba6` | 9 May | |
| 9 | S8 Casino | `bebda5d` → `f77fb55` (blue jackpot) | 26 Jun | |
| 10 | New season | launch commit from Phase 4 | — | added after launch |

Per D10 the pinned commit is the **last commit before the next season's first commit**. Task 6.1 produces the pinned table with one-line justification per row; that table is the contract for rendering.

### 9.2 Render harness (`/home/user/season-gif/` — outside every repo tree; committed to the repo only if the user wants it kept)
For each pinned commit:
1. `git archive <sha> | tar -x -C /home/user/season-gif/eras/<n>/` — **not** worktrees (the user just cleaned 18 up), and **never inside a repo tree** (`load_dotenv()` walks up parent dirs and would find the staging `.env`).
2. Shared venv with that era's `requirements.txt` (stable across eras; flask-limiter storage forced to `memory://`).
3. Throwaway DB `wheelgif_<n>` via `sudo -u postgres createdb -O wheelapp` (`wheelapp` lacks CREATEDB). Load that commit's `schema.sql` then its migrations with its own `migrate.py`. Set `DATABASE_URL` **explicitly** in the env (and an empty `.env` in the era dir).
4. **Pre-boot guard:** grep the era tree for hardcoded DSNs/defaults (`wheeldb`, `postgresql://`, `DATABASE_URL` fallbacks) and boot-time writers (S7 server-side auto-spin worker, `ensure_current_season`). Patch the extracted copy to the throwaway DSN or abort the era. Then, after boot, **assert the server is connected to `wheelgif_<n>`** before any capture (query `current_database()` via a probe, or check the server log). Abort the era otherwise — this is the guard that protects prod.
5. Serve on port `5100+n`; fresh Playwright context per era (device-id cookie, rate limits). Register a user, seed the season row / theme so that era's look renders, capture: full page 1280×800 + wheel element crop; optionally a 1.5 s spin as frames.
6. Tear down: stop server, `dropdb wheelgif_<n>`.
7. `app.js` is tracked at every Postgres-era commit, so no per-era Babel build. If an era's CDN script URL no longer resolves, pin it to the equivalent unpkg version via a route intercept (logged, not edited in the source).

### 9.3 Assembly
- Pillow: per frame, caption bar "Season N — Name · Mon YYYY", 1.2 s hold + 0.3 s crossfade, loop forever. Two outputs: `season-history.gif` (full page, ≤ 8 MB, 960px wide) and `season-wheels.gif` (wheel crop, ≤ 3 MB). Also an MP4 via Playwright's bundled ffmpeg if size forces it (GitHub renders both).
- Contact sheet PNG of all frames for quick review.

**🤖 G6:** every map row rendered (or explicitly documented as unrenderable with the reason and a fallback frame), GIFs within size limits, contact sheet reviewed by the orchestrator (each frame visually distinct and matches its era's theme from the patch notes), all `wheelgif_*` DBs dropped, prod `users` count unchanged. GIF goes into Phase 5 → reviewed by the user at H4.

---

## 10. Orchestration rules for autonomous execution

- **Agents:** Haiku 5.5 subagents for search, mechanical edits, tests, render runs; orchestrator does design (Phase 1), merges, and every audit. Workflows under 5 agents.
- **Briefs** are self-contained: goal + why, exact files/functions, constraints (no prod DB, worktree path, collision rule), done-criteria with the verify command, what to return (`file:line`, diff summary, raw test output tail).
- **Audit every result:** read the diff; re-run the verify command yourself; reject "tests pass" without output.
- **Safety invariants (checked at every gate):**
  - Nothing writes to `wheeldb` except Phase 4 launch steps after H3 (and 0.6/D8 as specified). Every script that touches a DB prints `current_database()` first.
  - The prod `users` count is recorded at each gate; any unexplained change = stop.
  - No push to `master` except Phase 4 (after H3) and Phase 5 (after H4). Staging/feature branches pushed after each commit (standing preference).
  - No new streak-mitigation mechanics (standing feedback).
- **Escalate to the user** when: an auto gate fails twice; a decision in §2 turns out to be ambiguous in practice; any step would touch prod data outside the launch runbook; scope grows beyond a ticket.
- **Progress log** entry per gate: what passed, evidence (commands + key output), next step.

---

## 11. Risks

| Risk | Mitigation |
|---|---|
| Group doesn't come back regardless | Launch cadence + Daily Race give recurring reasons; cheap to try. Post-launch report measures it (spins/day, active users/day). |
| Auto-rollover misfires on prod | Pre-flight on a prod clone, auto-abort, system chat on success only; user can disable the cron with one command (documented). |
| Old commits won't run (GIF) | Per-era fallback: serve static files only with a stubbed `/api/state` captured from a neighbouring era; documented per frame. |
| README exposes friends' data | Seeded fake DB by construction; H4 review. |
| Subagent edits collide in `app.jsx` | Serial frontend lane; orchestrator merges. |
| Test-suite noise hides regressions | Baseline file + "no new failures" rule; attempt to fix the race in Phase 0. |
