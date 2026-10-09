# Wheel Revival — Master Plan

> **Status:** v2 (2026-10-08). **H1 passed**, **G0 passed** (see `WHEEL_REVIVAL_PROGRESS.md`). Phase 1 spec + Phase 6 GIFs in progress; next human gate is **H2** (playtest).
> **Owner:** tom7 (operator). **Orchestrator:** Claude (Opus) — plans, audits, owns judgement.
> **Implementers:** subagents (Haiku 5.5, xhigh) via the orchestrator rule — scoped briefs, audited diffs.
> **Repo authority:** `/home/user/wheel-app` (master, live, port 5000, `wheeldb`) is source of truth.
> `/home/user/wheel-app-staging` (staging, port 5001, `wheeldb_staging`) is where new work is built.

Three deliverables:

| Track | Deliverable | Ends at |
|---|---|---|
| **A — Season 9** | An indefinite final season with automatic weekly sub-seasons (9.1, 9.2, …), built on staging, play-tested by tom7, launched on prod | Gate H3 → launch + 48h watch |
| **B — README revival** | GitHub README rebuilt as a feature tour (latest screenshots/clips, regenerable by one command) + a **Season Museum** | Reviewed at H3, merged at launch |
| **C — Season GIFs** | A short animated clip of every season *in action*, rebuilt from historical commits; a hero GIF made of those clips | Embedded in README (via B) |

---

## 0. How to use this document

- **Sections 1–2** are the thinking: a second opinion on why the game stalled, and the decisions (now locked).
- **Sections 3–8** are execution: phases, tickets, exit gates. The orchestrator runs them autonomously, stopping **only** at H2 (playtest) and H3 (launch go/no-go + README review). The user has delegated all creative, design and gameplay decisions to the orchestrator.
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

### 1.4 What this implies for Season 9 (adopted)

A **consolidation season**, not a content-dump season — and the game's last, so it must run itself:

- **R1 — Cadence on autopilot.** Season 9 is indefinite. Every week it rolls into a new **sub-season** (9.1, 9.2, …) with a fresh race and its own podium. A systemd timer drives it; it can never silently expire again.
- **R2 — Subtract.** Audit feature usage; *hide or retire* systems nobody used. Reveal the rest progressively, and ship working onboarding.
- **R3 — Keep the idle loop.** Auto-spin for everyone + offline catch-up.
- **R4 — Every week is a fresh race.** The weekly reset is the answer to "decided on day one": a runaway wins *a week*, not the season. Podium per week = total wins (D4). A **Hall of Fame** lists every sub-season podium.
- **R5 — One fresh coat of paint.** One new page theme + wheel theme for launch appeal.
- **R6 — Fix friction.** Review rate limits that hit real players (chud's timeout); remove the 2,145 prod test accounts and close the leak.

---

## 2. Decisions (locked at H1, 2026-10-08)

| ID | Decision | Locked answer |
|---|---|---|
| **D1** | Season number & name | Player-facing **9**, new name + theme chosen by the orchestrator in Phase 1 |
| **D2** | S9 "Arcade" salvage | Orchestrator's call. Default: keep infra + long-lived features; scrap the rest (§2.1) |
| **D3** | Direction & creative authority | Consolidation season (§1.4). **Orchestrator owns all creative, design and gameplay decisions** — no H1b gate |
| **D4** | Podium | Total wins, per weekly sub-season |
| **D5** | Length | **Indefinite** final season, auto-reset **weekly** into sub-seasons 9.1, 9.2, …, each with its own podium |
| **D6** | Rollover | Automatic (systemd timer, Europe/London) with pre-flight on a prod clone + auto-abort |
| **D7** | Feature retirement | Orchestrator decides from usage data (Phase 1) |
| **D8** | Prod test accounts | Delete (after backup), in the launch window; close the leak |
| **D9** | GIFs | **Clips, not stills**: a short in-action clip per season → hero GIF made of the clips (full page) + wheel-crop strip. Feature sections below use the latest stills/clips |
| **D10** | Season → commit | Final commit of each season |
| **D11** | README | Fake seeded users only; plus a **Season Museum**: one section per season explaining what it added, what happened, and how the game grew |

**Default (orchestrator):** the public README/museum never names real players — winners appear as magnitudes and anecdotes ("the S2 winner finished on a 300-digit number"). The repo is **public**.

### 2.1 S9 "Arcade" salvage (orchestrator's call, refined in Phase 1)

The S9 work is preserved at `/home/user/backups/s9-snapshot-20261008/` (`s9-tracked.patch` + `s9-untracked.tgz` + `BASE_SHA`) and archived to branch `archive/s9-arcade` in Phase 0. Staging then restarts clean from master; salvaged pieces are re-applied as RV tickets.

| S9 item | Call | Why |
|---|---|---|
| `advance_season(player_facing_number, name)` override | **Keep** | Needed for controlled rollover |
| Theme hardcoded in `seasons.py` | **Replace with season config** | S8 launch-bug class |
| `make test-db-reset` ownership grant | **Keep** | Test suite can't write otherwise |
| Universal auto-spin + 24h offline catch-up + resume-on-load (mig 076) | **Keep** | R3 |
| Community goal & singularity retunes (074/075) | **Keep, re-check for ~7 players and a 1-week window** | Targets were unreachable |
| Vault cap, stake decay, `wins_delta` cap fix | **Scrap** | Extra rules; weekly reset handles runaways |
| Zealot mode | **Scrap** | More modes on an unexplored pile |
| Prestige titles, Dragonfish | Decide in Phase 1 (cheap, low-risk) | — |
| Arcade themes/skins, `arcade-bg.js` | Decide in Phase 1 against the new theme | — |

---

## 3. Phase plan overview

```
Phase 0  Safety & baseline ............ 🤖 G0
Phase 1  Season 9 design spec ......... 🤖 G1         (orchestrator decides; spec published, not gated)
Phase 2  Build on staging ............. 🤖 G2         (subagents, tickets in §5)
Phase 3  Staging verification ......... 🤖 G3 → 🧑 H2 (tom7 play-tests ~15 min with checklist)
Phase 5  README + museum (prep) ....... 🤖 G5         (built on branch readme-revival after H2)
Phase 4  Launch on prod ............... 🧑 H3 go/no-go (+ README review) → 🤖 G4 → 48h watch
Phase 6  Season clips & GIFs .......... 🤖 G6         (runs in PARALLEL from G0 onwards)
```

Parallelism: **Track C (Phase 6) is independent** and starts as soon as G0 passes. Track B (Phase 5) starts after H2 so it shows the final build, and must be ready by H3; the README merges to master in the launch window. Track A is serial.

---

## 4. Phase 0 — Safety & baseline

| # | Task | Done when |
|---|---|---|
| 0.1 | Build branch `archive/s9-arcade` **from the snapshot only**: a scratch clone at `BASE_SHA` (`7c4f637`), `git apply s9-tracked.patch`, untar `s9-untracked.tgz`, add exactly those paths (never `git add -A`; never include `docs/WHEEL_REVIVAL_*`). Push to origin. | `git diff archive/s9-arcade` vs snapshot is empty; branch on origin |
| 0.2 | First dump `wheeldb_staging` to `/home/user/backups/wheeldb_staging_pre_revival.sql.gz`. Then discard the S9 working-tree changes in `/home/user/wheel-app-staging` (`git checkout -- .` + remove only the 18 S9 untracked paths listed in the tarball — not `git clean`), re-sync with master. | `git status` clean; `staging` 0 behind master |
| 0.3 | **Test baseline** (wrapped by 0.4's before/after prod `users` count): run full suite on master and staging; record failing test IDs in `docs/TEST_BASELINE.md`. Then attempt to fix the conftest module-stub race (T242) — if fixed in ≤1 subagent pass, baseline = 0 failures. | Baseline file exists; gate rule thereafter = "no new failures vs baseline" |
| 0.4 | **Prod-DB leak check**: record prod `users` count *before* 0.3 and compare *after*. The leak is known to be still open: T246 (`32c205e`, 29 Jun) routed pytest at `wheeldb_test`, yet test users kept appearing on prod until 31 Jul — the source is something other than pytest (suspect: E2E/Playwright or ad-hoc scripts hitting :5000). Find and fix it. | Count unchanged after both runs |
| 0.5 | Reconcile prod migrations: prod is at 068, master carries 069–072. `ip_address` already exists on prod `chat_messages` → confirm 072 is idempotent (`IF NOT EXISTS`) or mark applied. Dry-run all four against a prod clone. | `migrate.py --dry-run` on clone passes; plan for each recorded in progress log |
| 0.6 | Housekeeping: update `origin` to `git@github.com:Tom1tk/LuckyWheel.git`; remove stale `/etc/cron.d/hiatus-deploy` (points at a missing script); delete merged local branches `t231…t247`, `t242-chat`. | `git remote -v` shows LuckyWheel; cron file gone; branches gone |
| 0.7 | Create `bin/clone-prod-to.sh <dbname>`: pg_dump prod → restore into a throwaway DB (via `sudo -u postgres`, since `wheelapp` lacks CREATEDB). Used by Phases 3, 4, 6. | Script restores into `wheeldb_clone_test`; row counts match prod |

**G0 (auto):** all of 0.1–0.7 done with evidence in the progress log. 0.6 cron removal and branch deletion were approved at H1; the D8 test-account deletion is **not** done here (it's in the launch runbook).

---

## 5. Phase 1–2 — Design spec and build (Track A)

### 5.1 Phase 1 — Season design spec (orchestrator, not delegated)

Output: `docs/SEASON_9_SPEC.md` (orchestrator decides; G1 = spec complete and self-consistent, every ticket has acceptance tests). Contents:

1. **Feature usage audit** — per system, how many real players touched it in S7/S8 (from `user_season_history`, `game_state`, `bounty_progress`, `build_loadouts`, goal/singularity contributions). → proposed **keep / hide-until-unlocked / retire** list (D7).
2. **Day-one experience** — exactly what a returning player sees in their first 60 seconds; which panels are visible; the onboarding steps (fix and re-enable the T114-disabled modal, or replace it with 3 inline tips).
3. **Weekly sub-season model** — how 9.N is represented (reuse `seasons` rows with `player_facing_number=9` + a sub-season number vs. a new column — pick the smallest change that keeps `user_season_history`/`season_snapshots` working); **what resets weekly** (wins/losses/streak/wager state/functional items) vs. **what persists** (cosmetics, encyclopaedia, cumulative/legacy wins, prestige — decided with reasons); the **Hall of Fame** (every sub-season's top 3) endpoint + panel; the rollover system chat message.
4. **Rollover automation** (D6) — season config replaces hardcoded values in `seasons.py`; a **systemd timer** (`OnCalendar=Fri 21:00 Europe/London`, `Persistent=true`) runs `bin/rollover.sh`, which (1) clones prod, (2) runs the sub-season rollover on the clone, (3) runs the post-rollover checklist (§7.3) on the clone, (4) only then rolls prod, (5) re-runs the checklist on prod, (6) posts a system chat message. Any failure → abort, prod untouched, log + a failure marker the orchestrator/user can see. Idempotent: a second run in the same week is a no-op.
5. **Theme & name** — the orchestrator picks one, prototyped as a CSS mockup screenshot in the spec.
6. **Friction fixes** — rate-limit review for `/api/spin` & friends (find what timed chud out); auto-spin defaults.
7. **Ticket list** — §5.2 skeleton refined into concrete tickets with files, acceptance tests, and owner (subagent vs orchestrator).

**🤖 G1:** spec committed to staging; usage audit numbers cited with the queries used; every decision has a one-line why.

### 5.2 Phase 2 — Build (ticket skeleton, refined in Phase 1)

| Ticket | Scope | Files (expected) | Parallel group |
|---|---|---|---|
| RV-01 | Season config: theme/name out of `seasons.py` into config; weekly sub-season model + migration | `seasons.py`, `migrations/`, `models.py` | backend-1 |
| RV-02 | Salvage infra from `archive/s9-arcade` (pfn/name override, test-db ownership) | `seasons.py`, `Makefile` | backend-1 (after RV-01) |
| RV-03 | Universal auto-spin + offline catch-up (salvage T217 + mig 076, renumbered) | `game.py`, `auth.py`, `seasons.py`, `app.jsx` | backend-2 → frontend |
| RV-04 | Community retunes (salvage 074/075, renumbered; targets re-checked for 7 players) | `community_goals.py`, `models.py`, migrations | backend-3 |
| RV-05 | Hall of Fame backend: per-sub-season podium snapshot + endpoint; rollover system chat | `seasons.py`, `game.py`, migration | backend-1 (after RV-01) |
| RV-06 | Feature hide/retire per D7 (server flags, not deletion of data) | `models.py`, `game.py`, `app.jsx` | frontend |
| RV-07 | Onboarding / progressive disclosure | `app.jsx`, `styles.css` | frontend |
| RV-08 | Sub-season banner ("Season 9.N — resets in Xd Yh") + Hall of Fame panel | `app.jsx`, `styles.css` | frontend |
| RV-09 | New page theme + wheel theme (+ background script if any) | `static/`, `models.py` | frontend (theme assets can be parallel) |
| RV-10 | Rollover automation: `bin/rollover.sh`, systemd service + timer units, post-rollover checklist script | `bin/`, `seasons.py` | ops |
| RV-11 | Rate-limit friction fix | `extensions.py`, `game.py` | backend-2 |
| RV-12 | PATCH_NOTES + README season section (text only; screenshots in Phase 5) | docs | docs |

**Collision rule:** anything touching `static/app.jsx` / `static/styles.css` runs **serially** (one frontend agent at a time). Backend groups run in parallel only if their file sets are disjoint. Each agent works in its own worktree off `staging`; the orchestrator merges and **removes the worktree immediately after merge** (no worktree clutter left behind).

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
| 3.2 | **Launch rollover (S8 → 9.1) and then a weekly rollover (9.1 → 9.2) on the clone, using the real prod numbering** (prod is internal 9 / pfn 8 — staging's previous Arcade run used internal 8 / pfn 9, which did *not* exercise prod's path). Run via the RV-10 pre-flight, not by hand. | Post-rollover checklist §7.3 all green |
| 3.3 | Playwright E2E on staging (desktop 1366×768 + mobile 390×844): register → spin → auto-spin start/stop/resume-after-reload → shop buy → equip theme → fishing cast/reel → bounty view → sub-season banner + Hall of Fame → chat send. | Screenshots + pass log in progress doc |
| 3.4 | Console-error sweep: zero uncaught JS errors across the E2E run. | Playwright console log |
| 3.5 | Install the timer on **staging** (pointed at `wheeldb_staging`) and let it fire once on a short test schedule; verify. Then write `docs/PLAYTEST_CHECKLIST.md` for tom7 (≤15 min, ~12 checkboxes, plus "anything feel off?" free text). | File exists |

**🤖 G3:** 3.1–3.5 green. → **🧑 H2:** tom7 plays staging (`:5001`) with the checklist. Feedback → fix tickets → re-run G3 → back to H2 until tom7 says go.

---

## 7. Phase 4 — Launch on prod (Track A)

Lessons from `SEASON_8_LAUNCH_POSTMORTEM.md` are encoded here as hard rules.

### 7.1 Pre-launch (auto, the day before)
- Full prod backup (`backup-wheeldb.sh`) + verify the dump restores into a clone.
- Final pre-flight: clone prod → apply migrations → deploy code → rollover → §7.3 checklist on the clone. Must be green within 24h of launch.
- Write the exact launch + rollback commands into the progress log (no improvising on the night).
- **Rehearse the whole ordered launch script on the clone, test-account delete included** (also in Phase 3). Gate: `count(username ~ '^t[0-9]') == count(ip_address='127.0.0.1')` (2145 at G0) before the delete, so no real player is matched; no FK errors or orphans afterwards; no test residue in aggregates (community-goal totals, singularity totals, chat, jackpot pool).

### 7.2 🧑 H3 — Go/no-go (+ README review)
Orchestrator presents: pre-flight results, backup path, migration list, proposed launch time (default: a Friday 21:00 UK, aligned with the weekly reset), rollback commands, **and the link to the rendered README on branch `staging`**. **User says go.** Outward-facing: affects the friends' accounts and the public repo. Never autonomous.

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
5. Install the prod rollover timer; confirm `systemctl list-timers` shows the next Friday.
6. Confirm the README images render on GitHub (`readme-revival` was merged into staging on 2026-10-09, so step 3 ships it).
7. System chat message announcing the season.

### 7.4 🤖 G4 + 48h watch
- G4 = §7.3 checklist all green. Any red → roll back per the written commands, report to user.
- 48h: check `journalctl -u wheel-app` for errors and the spin/chat activity twice a day; summary to user at 48h.
- **First weekly rollover (9.1 → 9.2):** verify the timer fired, checklist green, Hall of Fame updated. This is the real exit gate for Track A.
- Write `docs/SEASON_9_LAUNCH_REPORT.md`.

---

## 8. Phase 5 — README revival (Track B)

### 8.1 Media environment — regenerable by one command
- `make readme-media` (script under `tools/readme/`, committed): creates throwaway DB `wheeldb_readme` **seeded from scratch only** (schema + migrations + seed script — never a prod clone) with **fake users** (`reeltime`, `spinwizard`, `koi_pond`, …) and fake chat; boots the current code on port 5099; seeds each feature into a showable state; captures every shot/clip with Playwright; optimises; drops the DB. Re-running it after any future change refreshes every feature image → **sections always show latest**.
- Same prod-safety guards as §9.2 (explicit DSN, `current_database()` assertion, prod `users` count unchanged).

### 8.2 Shot list (1366×768 unless noted; stills ≤300 KB, clips ≤1.5 MB)

| # | Section | Media |
|---|---|---|
| 1 | **Hero** | Season-history GIF from Track C (full page) |
| 2 | The wheel | clip: a spin landing on WIN, then JACKPOT (blue) |
| 3 | Auto-spin & offline catch-up | still: catch-up summary toast |
| 4 | Shop | stills: upgrades tab + cosmetics tab |
| 5 | Cast & Reel fishing | clip: cast → bite → reel → catch |
| 6 | Encyclopaedia / Aquarium | still |
| 7 | Wagers | still: stake, hot streak, bank |
| 8 | Wheel modes | still |
| 9 | Weekly sub-seasons + Hall of Fame | still |
| 10 | Bounties + community goals | still |
| 11 | Chat | still (fake users, system messages) |
| 12 | Mobile | stills: 390×844 pair |

Sections retired in Phase 1 (D7) are not shown.

### 8.3 README structure
1. Hero GIF + one-line pitch + "Season 9 is live — new race every Friday".
2. **Feature tour**: one short section per media item (2–4 lines each). The current 694-line wall moves to `docs/MECHANICS.md` (nothing deleted).
3. **The Season Museum** — one section per season (Prototype → S9), each with: that season's in-action clip (from Track C, wheel crop), name + dates, *what it added*, *what happened* (records as magnitudes, notable events: the S7.7 apology, the S8 launch night, the long hiatus), and *how it shaped what came next*. Sources: `PATCH_NOTES.md`, git history, `docs/` (postmortem, planning docs), `season_snapshots` (magnitudes only). Written by the orchestrator; a subagent fact-checks each claim against its source and returns a source per claim.
4. Tech stack + local-dev quickstart (verified: a subagent follows it from a clean clone into a scratch dir and it works).
5. Fix links: wiki Patch Notes link and every `fishspin` → `LuckyWheel`.
- Media lives in `docs/img/` (not `static/`, so the app doesn't serve it).

**🤖 G5:** branch `readme-revival` pushed; every image link resolves on GitHub (API check); total media ≤ 25 MB; grep for real usernames across README, `docs/MECHANICS.md` and image alt text returns nothing; quickstart verified; museum claims each have a source. → reviewed by the user at **H3**.

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
| 10 | S9 (final) | captured from the staging build after H2 via `tools/season-gif` | — | |

Per D10 the pinned commit is the **last commit before the next season's first commit**. Task 6.1 produces the pinned table with one-line justification per row; that table is the contract for rendering.

### 9.2 Render harness (`/home/user/season-gif/` — outside every repo tree; the final script is committed to `tools/season-gif/` so the S9 clip can be re-captured later)
For each pinned commit:
1. `git archive <sha> | tar -x -C /home/user/season-gif/eras/<n>/` — **not** worktrees, and **never inside a repo tree** (`load_dotenv()` walks up parent dirs and would find the staging `.env`).
2. Shared venv with that era's `requirements.txt` (stable across eras; flask-limiter storage forced to `memory://`).
3. Throwaway DB `wheelgif_<n>` via `sudo -u postgres createdb -O wheelapp` (`wheelapp` lacks CREATEDB). Load that commit's `schema.sql` then its migrations with its own `migrate.py`. Set `DATABASE_URL` **explicitly** in the env (and an empty `.env` in the era dir).
4. **Pre-boot guard:** grep the era tree for hardcoded DSNs/defaults (`wheeldb`, `postgresql://`, `DATABASE_URL` fallbacks) and boot-time writers (S7 server-side auto-spin worker, `ensure_current_season`). Patch the extracted copy to the throwaway DSN or abort the era. Then, after boot, **assert the server is connected to `wheelgif_<n>`** before any capture. Abort the era otherwise — this is the guard that protects prod.
5. Serve on port `5100+n`; fresh Playwright context per era. Register a fake user, seed the season row / theme / a little state (some wins, a streak) so that era's look renders.
6. **Capture an in-action clip (~4 s)**: trigger a spin and record it via CDP `Page.startScreencast` (or a timed screenshot burst at ~12 fps), 1280×800 full page; the wheel crop is cut from the same frames. Keep raw PNG frames.
7. Tear down: stop server, `dropdb wheelgif_<n>`.
8. `app.js` is tracked at every Postgres-era commit, so no per-era Babel build. If an era's CDN script URL no longer resolves, route-intercept it to the equivalent pinned unpkg version (logged, source untouched).

### 9.3 Assembly
- Pillow, from the raw frames:
  - **Per-season clip** `docs/img/seasons/s<n>.gif` — wheel crop, ~480 px, ~10 fps, ≤ 1.5 MB, loops. Used in the museum.
  - **Hero** `docs/img/season-history.gif` — the full-page clips back-to-back, each with a caption bar "Season N — Name · Mon YYYY" and a short crossfade, 960 px wide, ≤ 10 MB (drop fps/colours before dropping seasons).
  - **Wheel strip** `docs/img/season-wheels.gif` — wheel-crop clips back-to-back, ≤ 4 MB.
- Contact sheet PNG (one frame per season) for the orchestrator's review.

**🤖 G6:** every map row has a clip (or is documented as unrenderable with the reason and a fallback), GIFs within size limits, contact sheet reviewed by the orchestrator (each frame visually distinct and matches its era's theme from the patch notes), all `wheelgif_*` DBs dropped, prod `users` count unchanged. Media goes into Phase 5 → reviewed by the user at H3.

---

## 10. Orchestration rules for autonomous execution

- Until the leak fix (`tests/conftest.py` pin) reaches master at launch, **never run pytest from `/home/user/wheel-app`** — its `.env` is prod. Every subagent brief says so.
- Gate tripwire: diff prod `pg_stat_user_tables` counters against `/home/user/backups/prod_pgstat_G0.txt` (users count alone misses UPDATEs).

- **Agents:** Haiku 5.5 subagents for search, mechanical edits, tests, render runs; orchestrator does design (Phase 1), merges, and every audit. Workflows under 5 agents.
- **Briefs** are self-contained: goal + why, exact files/functions, constraints (no prod DB, worktree path, collision rule), done-criteria with the verify command, what to return (`file:line`, diff summary, raw test output tail).
- **Audit every result:** read the diff; re-run the verify command yourself; reject "tests pass" without output.
- **Safety invariants (checked at every gate):**
  - Nothing writes to `wheeldb` except Phase 4 launch steps after H3 (and 0.6/D8 as specified). Every script that touches a DB prints `current_database()` first.
  - The prod `users` count is recorded at each gate; any unexplained change = stop.
  - No push to `master` except in the Phase 4 launch window (after H3), which includes the README merge. Staging/feature branches pushed after each commit (standing preference).
  - No new streak-mitigation mechanics (standing feedback).
- **Escalate to the user** when: an auto gate fails twice; a decision in §2 turns out to be ambiguous in practice; any step would touch prod data outside the launch runbook; scope grows beyond a ticket.
- **Progress log** entry per gate: what passed, evidence (commands + key output), next step.

---

## 11. Risks

| Risk | Mitigation |
|---|---|
| Group doesn't come back regardless | Weekly sub-seasons + Hall of Fame give a recurring reason; cheap to try. Post-launch report measures it (spins/day, active users/day). |
| Auto-rollover misfires on prod | Pre-flight on a prod clone, auto-abort, idempotent per week; disable with `systemctl disable --now wheel-rollover.timer` (documented in README ops section). |
| Old commits won't run (GIF) | Per-era fallback: serve static files only with a stubbed `/api/state` captured from a neighbouring era; documented per frame. |
| README exposes friends' data | Seeded fake DB by construction; museum uses magnitudes, no usernames; username grep at G5; H3 review. |
| Subagent edits collide in `app.jsx` | Serial frontend lane; orchestrator merges. |
| Test-suite noise hides regressions | Baseline file + "no new failures" rule; attempt to fix the race in Phase 0. |
