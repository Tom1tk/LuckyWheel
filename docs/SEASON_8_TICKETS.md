# Season 8 — Authoritative Ticket List

> **Purpose:** Individual tasks extracted from `SEASON_8_BUILD_SPEC.md` with
> strict acceptance criteria. Designed for parallel execution by sub-agents.
> Each ticket is self-contained: an agent can pick it up, read the spec section
> referenced, and execute without context from other tickets (unless an
> explicit dependency is listed).
>
> **Codebase:** `/home/user/wheel-app-staging/` (Flask + PostgreSQL + React/JSX)
> **Database:** `wheeldb_staging` (staging only; never touch production `wheeldb`)
>
> **Source of truth:** `SEASON_8_BUILD_SPEC.md` (build spec) → this document
> (tickets) → `SEASON_8_PROGRESS.md` (execution record). The build spec is
> authoritative and must not be edited. If a ticket disagrees with the spec,
> the spec wins.
>
> **Status legend:** `[ ]` not started | `[~]` in progress | `[x]` done | `[!]` blocked

> **Spec hardening (2026-06-22):** This document was comprehensively updated
> to reflect the hardened spec. New tickets T69–T96 cover the bug audit
> (B1–B21 from spec §23) and the new spec features added during the hardening
> pass (zero-escrow edge case, mode-change resets, dynamic wheel graphic,
> 200-message chat history, auto-post messages, community goal milestones,
> inverted mode loss-farming, etc.). T45, T63, T11, T27, T35, T02 acceptance
> criteria updated to match the final hardened spec.

---

> **Audit note (2026-06-18):** BUG-11: The casino title still read "ENDLESS" (Season 7 branding) and the subtitle was the old Season 7 tagline "Where we're going, we won't need luck to win". Updated to "SEASON 8" and "Season 8 — Make every spin count" in commit 5acce4a. This was not covered by any specific ticket — the title/subtitle change should have been part of the season-transition polish.

> **Design audit note (2026-06-18):** Operator review of the staging build identified a missing design/CSS pass across the entire Season 8 UI. All Season 8 panels (wager, wheel mode, prestige, guard, bounties, community goal, singularity, aquarium, loadout, accessibility, onboarding, chat replays) have functional JSX and state wiring but **zero CSS**. Additionally all Season 8 panels are placed outside the main layout structure (before `.main-layout-row`), causing them to render as an unstyled column above the casino UI. See `SEASON_8_PROGRESS.md` — "UI/Design Audit — 2026-06-18" for the full breakdown (DESIGN-01 through DESIGN-08). This represents a complete missing layer of work across all UI tickets (T09, T12, T14, T16, T22, T26, T29, T31, T33, T35, T36, T37, T41) — the previous agent verified Babel compiled without errors but did not verify visual correctness.

---

## Dependency graph

```
Phase 0 (foundation)
  T01 ─┬─> T02 ─┬─> T05 ─┬─> T08
       │        │        ├─> T09
       │        ├─> T06  ├─> T10
       │        ├─> T07  ├─> T11
       │        │        ├─> T12
       T03      T04      ├─> T13
       T14      T15      ├─> T14
       T16               └─> T15
  T17 ──> T18
  T19
Phase 2+
  T20 ─> T21 ─> T22   (protection)
  T23 (themes, independent)
  T24 ─> T25 ─> T26   (fishing)
  T27 ─> T28 ─> T29   (community goals)
  T30 ─> T31          (singularity)
  T32 ─> T33          (loadouts)
  T34 ─> T35          (replays + chat)
  T36                 (legacy boards)
  T37                 (accessibility)

Phase 7 (spec hardening — bug fixes + new features from spec §23-24)
  T69  (migration 047 — hardening columns) — depends on Phase 0
  T70  (zero-escrow edge case) ─> depends on T06
  T71  (hot streak reset on loss, B1) ─> depends on T06
  T72  (banking guard, BUG-Q5) ─> depends on T08
  T73  (double-down rework to escrow last win, B19) ─> depends on T69, T08
  T74  (insurance dice-charge model, B2/B15/B16/B17) ─> depends on T69, T08
  T75  (wager panel always visible/disabled, BUG-Q7) ─> depends on T09
  T76  (mode-change resets, BUG-Q1.8) ─> depends on T08, T10
  T77  (gravity mode full mechanic + drift column) ─> depends on T11, T69
  T78  (mirror mode full mechanic — double escrow) ─> depends on T11
  T79  (inverted mode full loss-farming mechanic) ─> depends on T11, T69
  T80  (dynamic wheel graphic — server probabilities) ─> depends on T11, T77
  T81  (chat history 200 messages + cursor pagination) ─> depends on T17
  T82  (auto-post messages with configurable triggers) ─> depends on T17, T06
  T83  (per-player escalating big-win threshold) ─> depends on T69, T82
  T84  (community goal milestones 25/50/75%) ─> depends on T27, T82
  T85  (prestige scope update — wager tokens persist) ─> depends on T13
  T86  (prestige_efficiency as win retention only) ─> depends on T13
  T87  (onboarding step 5 terminal transition) ─> depends on T43
  T88  (onboarding rollover preservation, B10) ─> depends on T02
  T89  (replay system complete removal) ─> depends on T34
  T90  (auto-post messages to auto-spin path, B5) ─> depends on T18, T82
  T91  (remove bounty "all 3" chat message, B21) ─> depends on T40
  T92  (chat rate limit + trim for system messages) ─> depends on T17
  T93  (per-player cap race fix in increment_goal) ─> depends on T28
  T94  (auto-spin: budget=0 guard + first-tick gate) ─> depends on T18
  T95  (manual spin button + auto-spin start/stop) ─> depends on T18
  T96  (wheel-wrapper height budget re-tune) ─> depends on T75
```

---

## Phase 0: Foundation
### T01: Migration 031: Season 8 reset columns

- **Spec ref:** S2, S5
- **Status:** [x]
- **Parallel group:** P0-core
- **Depends on:** None
- **Files:**
  - migrations/031_season8_reset.sql
- **Acceptance criteria:**
  1. Migration file 031_season8_reset.sql exists in migrations/ directory.
  2. Adds columns to game_state: prestige_level INTEGER DEFAULT 0, prestige_count INTEGER DEFAULT 0, legacy_wins NUMERIC DEFAULT 0, onboarding_step INTEGER DEFAULT 0, auto_spin_budget INTEGER DEFAULT 0.
  3. All ALTER statements use IF NOT EXISTS (idempotent).
  4. Running python migrate.py applies the migration without error on wheeldb_staging.
  5. Running python migrate.py --status shows 031 as applied.

### T02: Extend _perform_rollover() for Season 8

- **Spec ref:** S2, S5, S19
- **Status:** [x]
- **Parallel group:** P0-serial
- **Depends on:** T01
- **Files:**
  - seasons.py
- **Acceptance criteria:**
  1. _perform_rollover() sets legacy_wins = SUM(final_wins from user_season_history for each user) at rollover.
  2. Sets prestige_level = starting prestige from legacy mapping (0 if 0, 1 if <1M, 2 if <100M, 3 if <1B, 4 if <10B, 5 if >=10B).
  3. Resets: wager_streak, active_wheel_mode → 'steady', bounty_progress (new day generates fresh), community_goal_contributions → 0, double_down_pending → FALSE, gravity_drift → 0, biggest_win_announced → 0, wager_insurance_armed → FALSE, wager_banked_losses → 0, wager_last_win_amount → 0.
  4. Preserves: prestige_level, prestige_count, legacy_wins, owned_cosmetics, active_cosmetics, aquarium_species, loadouts, cosmetic_fragments, **onboarding_step** (B10 — do NOT reset), wager_tokens.
  5. Resets community_goals table and singularity_meter (if filled, increments fill_count).
  6. Existing snapshot logic (season_snapshots, user_season_history) is unchanged.
  7. Resets wager_insurance_charges to 0 and wager_insurance_last_recharge to NOW().

### T03: Number formatting module

- **Spec ref:** S14
- **Status:** [x]
- **Parallel group:** P0-core
- **Depends on:** None
- **Files:**
  - static/js/format.js
- **Acceptance criteria:**
  1. File static/js/format.js exists.
  2. Exports format_wins(n) function.
  3. Returns raw number string for n < 1000 (e.g. "842").
  4. Returns comma-grouped string for 1000 <= n < 1M (e.g. "84,201").
  5. Returns compact string for n >= 1M (e.g. "8.42M", "8.42B").
  6. Handles 0 and negative numbers correctly.
  7. Handles null/undefined input by returning "0".

### T04: Update _MAX_WINS and remove old infinites

- **Spec ref:** S2, S5
- **Status:** [x]
- **Parallel group:** P0-core
- **Depends on:** None
- **Files:**
  - models.py
  - game.py
- **Acceptance criteria:**
  1. _MAX_WINS in models.py changed from round(9.99e99) to 5_000_000.
  2. INFINITE_UPGRADES dict: winmult_inf, bonusmult_inf, jackpot_resonance_inf, echo_amp_inf, proc_streak_inf, streak_armor_inf, lure_mastery_inf are removed.
  3. game.py _build_spin_context() no longer reads the removed inf level columns.
  4. game.py _resolve_spin() no longer references jackpot_resonance_level, echo_amp_level, proc_streak_level, streak_armor_level, lure_mastery_level.
  5. No import errors when starting the staging server.
  6. Existing spin endpoint still works (returns 50/50 win/loss, no crashes).

> **Audit note (2026-06-18):** Backend removal of old infinites was done correctly. However the UI was not updated in step with it — BUG-08: `proc_streak_inf` was still referenced in JSX (`<ProcStreakCounter>` conditional), BUG-09: `bonusmultLevel={infLevels.bonusmult_inf}` was passed to `StreakPanel` in two places but `bonusmult_inf` no longer exists in `INFINITE_UPGRADES`, causing `undefined` to be passed. Fixed in commit 5acce4a: removed the `proc_streak_inf` JSX block, hardcoded `bonusmultLevel={0}` in both occurrences.
### T05: Migration 032: Wager system columns

- **Spec ref:** S3
- **Status:** [x]
- **Parallel group:** P1-wager
- **Depends on:** T01
- **Files:**
  - migrations/032_wager_system.sql
- **Acceptance criteria:**
  1. Adds columns to game_state: wager_streak INTEGER DEFAULT 0, wager_last_stake INTEGER DEFAULT 0, double_down_pending BOOLEAN DEFAULT FALSE, wager_banked_wins INTEGER DEFAULT 0, wager_insurance_charges INTEGER DEFAULT 0.
  2. All ALTER statements use IF NOT EXISTS.
  3. python migrate.py applies without error on wheeldb_staging.

### T06: Wager logic in _resolve_spin()

- **Spec ref:** S3
- **Status:** [x]
- **Parallel group:** P1-wager
- **Depends on:** T01, T04
- **Files:**
  - game.py
  - wagers.py
- **Acceptance criteria:**
  1. wagers.py exists with stake validation (1-10 int), hot-streak calculation, double-down resolution helpers.
  2. _resolve_spin() signature accepts stake: int parameter (default 1).
  3. Win payout multiplied by stake: wins += int((effective_win_mult + bonus_earned) * stake * hot_streak_bonus).
  4. Loss penalty multiplied by stake: losses += base_loss * stake.
  5. If wager_unlock not owned, stake is forced to 1 (server-side validation).
  6. Hot streak: +5% per consecutive same-stake win, capped at +50%. Changing stake resets wager_streak.
  7. wager_safety_net: on loss at >=5x stake, base_loss reduced by 25%.
  8. POST /api/spin accepts stake in body, applies wager logic, returns wager_streak and wager_banked_wins in response.

### T07: Wager shop items in models.py

- **Spec ref:** S3
- **Status:** [x]
- **Parallel group:** P1-wager
- **Depends on:** T05
- **Files:**
  - models.py
- **Acceptance criteria:**
  1. SHOP_ITEMS has: wager_unlock (500, tier 1), wager_safety_net (2000, tier 2, requires wager_unlock), wager_hot_streak (8000, tier 2, requires wager_unlock), wager_double_down (25000, tier 3, requires wager_hot_streak), wager_insurance (50000, tier 3, requires wager_unlock).
  2. All wager items are in _FUNCTIONAL_SHOP_ITEMS set.
  3. item_tier() returns correct tier for each wager item.
  4. UPGRADE_TIER_2 contains wager_safety_net, wager_hot_streak.
  5. UPGRADE_TIER_3 contains wager_double_down, wager_insurance.

### T08: Wager API endpoints

- **Spec ref:** S3
- **Status:** [x]
- **Parallel group:** P1-wager
- **Depends on:** T06
- **Files:**
  - game.py
- **Acceptance criteria:**
  1. POST /api/wager/bank: banks wager_banked_wins into wins, resets wager_streak to 0. Returns new wins and wager_streak.
  2. POST /api/wager/double-down: resolves a double-down spin at 2x current stake. Loss loses wagered winnings; win doubles them. Sets double_down_pending = FALSE. Returns spin result + new wager state.
  3. POST /api/wager/insurance: consumes one insurance charge (if available), sets a flag so next spin is no-loss. Returns charges remaining.
  4. All endpoints require login (decorated with @login_required).
  5. All endpoints have rate limiting (@limiter.limit).
  6. All endpoints return JSON with error field on failure.

> **Bug audit note (2026-06-19):** Found while researching accurate tooltip copy for **T44**. Two of the four wager mechanics are structurally unreachable because nothing ever supplies the state their consuming endpoints check — the "spend" side was built, the "earn" side wasn't:
>
> **BUG-W01 — `wager_insurance_charges` is never incremented anywhere.** `game.py` only ever reads it (lines 497, 586, 2552) or decrements it (line 2554, inside `/api/wager/insurance`). Confirmed via repo-wide grep — no purchase or grant logic exists. Buying the `wager_insurance` shop item (50,000 wins) sets `owned_items` but does not touch `wager_insurance_charges`, which starts and stays at 0. The Insurance button (`static/app.jsx:4225`, gated on `wagerInsuranceCharges > 0`) can therefore never appear for any player, ever. Needs a decision + fix: either grant N charges on purchase (one-time), or grant a charge periodically per spec's "once per 10 spins" framing (`SEASON_8_BUILD_SPEC.md:209` — note spec also says "pay 10% of stake" per use, which isn't implemented either; current code treats it as a pure consumable charge with no stake cost).
>
> **BUG-W02 — `wager_banked_wins` is never incremented anywhere.** Same shape of bug: only ever read or reset to 0 (`game.py:585, 2473, 2590`) — confirmed via grep, nothing in `_resolve_spin()` or anywhere else adds to it. Spec (`SEASON_8_BUILD_SPEC.md:192-195`) describes hot-streak winnings accumulating into `wager_banked_wins` while the streak continues, convertible to real `wins` only when the player presses Bank — "the risk/reward tension: keep pressing for higher multiplier, or bank and start fresh." As implemented, `compute_wager_payout()` (`wagers.py`) credits the stake-multiplied, hot-streak-boosted payout directly into `wins` every spin — there is no separate "at risk" pool to bank. The Bank button (`static/app.jsx:4212`, gated on `wagerBankedWins > 0`) can therefore never appear either. This is a bigger gap than BUG-W01: it means the entire bank/streak-risk mechanic described in spec's overview was never actually wired into spin resolution, only the UI shell and the consuming endpoint were built.
>
> **Minor — criterion 5 unmet:** none of the four wager endpoints (`wager_bank`, `wager_set_stake`, `wager_double_down`, `wager_insurance`, `game.py:2460-2557`) have a `@limiter.limit(...)` decorator, unlike e.g. `/api/reel` (`@limiter.limit('5 per second')`). Low severity, but flagging since it's a named acceptance criterion.

### T09: Wager UI components

- **Spec ref:** S3, S21
- **Status:** [x]
- **Parallel group:** P1-wager
- **Depends on:** T08
- **Files:**
  - static/js/wager-ui.js
  - static/app.jsx
- **Acceptance criteria:**
  1. Stake slider (1x-10x) renders with risk labels: Safe (1-3), Bold (4-7), Reckless (8-10).
  2. Double-down button appears after a win (if wager_double_down owned and double_down_pending is true).
  3. Hot-streak meter fills with consecutive same-stake wins, shows current bonus percentage.
  4. Bank button is visible and functional (calls /api/wager/bank).
  5. Insurance toggle shows available charges (if wager_insurance owned).
  6. All wager UI uses format_wins() for number display.
  7. Frontend compiles without errors: npx babel static/app.jsx --out-file static/app.js.

> **Design audit note (2026-06-18):** All wager panel CSS classes are missing from `styles.css` (DESIGN-01): `season8-wager-panel`, `wager-stake-control`, `wager-slider`, `stake-label`, `stake-safe/bold/reckless`, `wager-hotstreak`. The wager panel renders as raw unstyled HTML. Additionally the panel is placed outside `.main-layout-row` so it has no layout context (DESIGN-02). Needs CSS and correct DOM placement (near wheel/scoreboard area inside `.casino-container`).
>
> **Note (2026-06-19):** This design audit note is now stale/resolved — `.season8-wager-panel` and all child classes have CSS (`static/styles.css:4350-4438`), and the panel is correctly nested inside `.main-layout-row > .casino-container` (`static/app.jsx:4151,4194-4228`). Was apparently fixed in a later pass without the note being struck through.
>
> **Diagnostic audit note (2026-06-19) — player reported "can't see any of the wager system in the UI":** Investigated end-to-end (shop entry → purchase endpoint → ownership gate → panel render → CSS). **No functional bug found.** Findings:
>
> 1. **Root cause confirmed via direct DB query against `wheeldb_staging`:** none of the 3 staging accounts (`testing7`, `ticktest`, `season8test`) own `wager_unlock`. The most-progressed account (`testing7`) has 122 wins; the item costs 500 wins (`models.py:221`). The entire `.season8-wager-panel` block is gated behind `ownedItems.includes('wager_unlock')` (`static/app.jsx:4195`) — by design, per spec: *"wager_unlock ... Requires: None ... without this, stake locked at 1x"* (`SEASON_8_BUILD_SPEC.md:205`). With 122 < 500 wins, the panel is correctly absent — this is not a rendering or gating bug, it's an unmet purchase threshold.
> 2. **Verified the rest of the chain is intact:** the shop correctly lists "⚡ Season 8: Wager System" → Wager Unlock (500, tier 1, no win-count tier-lock since tier 1 bypasses `UPGRADE_TIER_THRESHOLDS`) and is visible/purchasable in `ShopPanel`'s filter logic (`static/app.jsx:2581-2601`); `/api/buy` (`game.py:1340`) handles it via the generic functional-item path with no special-casing needed; `setOwnedItems(data.owned_items)` correctly updates frontend state on purchase (`static/app.jsx:3253`). All four wager endpoints exist and look spec-correct: `/api/wager/bank` (`game.py:2460`), `/api/wager/stake` (`game.py:2482`, also handles the onboarding step 1→2 hook), `/api/wager/double-down` (`game.py:2518`), `/api/wager/insurance` (`game.py:2539`).
> 3. **Minor doc inaccuracy:** this ticket's Files list names `static/js/wager-ui.js`, which doesn't exist (`ls static/js/` only shows `format.js`) — the wager UI was implemented inline in `static/app.jsx` instead. Not a functional issue, just stale ticket metadata.
> 4. **Open design question, not a bug — flagging per spec for a decision rather than assuming an answer:** spec §3's overview frames wager as a baseline mechanic ("every spin is a bet: the player chooses a stake multiplier... before spinning"), but the concrete implementation makes the *entire* system — slider, hot-streak, bank, double-down, insurance — invisible with zero affordance until 500 wins are spent. This matches the codebase's existing convention for `prestige_unlock` (also fully hidden pre-purchase, `static/app.jsx:4329`), so it's *consistent*, but it's inconsistent with wheel modes/bounties/community goal, which are unconditionally visible to all players regardless of purchases. Worth a product decision: leave as full-hide-until-owned (current behavior, consistent with prestige), or add some always-visible locked/teaser affordance (e.g. a greyed "Stake: 1×" row with a "🔒 Unlock wagering — 500 wins" hint) so new players discover the system exists before they've earned enough to buy in. No code change made pending that decision.
> 5. **To visually confirm the panel itself renders correctly once owned** (not yet verified empirically, only by reading code), grant `wager_unlock` to a staging test account and reload — flagging this as a possible next step rather than doing it unprompted, since it mutates account state even though it's test data.

> **Bug audit note (2026-06-19):** `testing7` was granted wins and purchased `wager_unlock` for visual verification (per item 5 above) — confirmed the panel renders correctly, but doing so surfaced a real layout regression:
>
> **BUG-W03 — `.wheel-wrapper`'s height budget doesn't account for the wager panel; the wheel shrinks / page grows once wagering is unlocked.** `.wheel-wrapper` (`static/styles.css:185-189`) sizes itself as `min(420px, calc(100vw - 120px), calc(100vh - 460px))` (mobile: `calc(100vh - 400px)`, `static/styles.css:2403-2406`). These budget numbers were last tuned for the content column *before* the wager panel could ever render (no test account owned `wager_unlock` at the time — see T42-era fixes earlier in this doc for the same `calc(100vh - Npx)` pattern being retuned for the mode-selector row). `.season8-wager-panel` (`static/app.jsx:4195-4228`) sits in the same column (`.casino-container`) above the wheel-mode selector and adds anywhere from ~50px (stake slider only) up to ~150px+ (stake slider + hot-streak row + bank button + double-down row + insurance row, all owned/active simultaneously, each `gap: 7px` apart per `static/styles.css:4350-4360`) depending on which wager upgrades are owned and live state (active streak, banked wins, double-down armed). The budget needs to be re-tuned to the worst case (all wager upgrades owned) — recommend re-deriving empirically (load the page with every wager upgrade owned and a hot streak active, measure actual non-wheel column height) rather than guessing a new magic number, since the previous two guesses (`-440px` → `-460px`/`-490px`) each needed a follow-up correction.
>
> **Structural observation, not just this one bug:** this is at least the third time a fixed `calc(100vh - Npx)` budget on `.wheel-wrapper` has gone stale because a new conditionally-rendered panel was added to the same column without the budget being revisited (mode selector, now wager panel) — and `.casino-container` still has more conditional panels below the wheel (prestige panel, bounty panel) that could compound the same problem as they're exercised in more states. Recommend whoever picks this up consider replacing the magic-number budget with an intrinsic/flexible sizing approach (e.g. the wheel as a flex child with `flex: 1 1 auto; min-height: 0;` inside a column that's allowed to scroll or shrink naturally, rather than the wheel pre-computing how much space everything else needs) so future panels don't require another manual recalibration. Flagging the idea, not mandating it — the minimal fix (re-tune the constant) is acceptable if a structural change is out of scope.

> **Audit note (2026-06-18):** Two acceptance criteria were not met by the original implementation. BUG-05: the double-down button logic was inverted — it showed the "Arm Double Down" button when `doubleDownPending === true` and the armed indicator when false. Fixed so the indicator (`⚡ Double-Down armed — next spin is 2× stake!`) renders when `doubleDownPending === true` and the arm button when false. BUG-06: the bank button was missing entirely from the wager panel JSX. Added a "🏦 Bank X wins" button (visible when `wagerBankedWins > 0`) that calls `/api/wager/bank` and updates `wins`, `wagerBankedWins`, `wagerStreak` state. Fixed in commit 5acce4a.

### T10: Migration 033 + wheel mode definitions

- **Spec ref:** S4
- **Status:** [x]
- **Parallel group:** P1-modes
- **Depends on:** T01
- **Files:**
  - migrations/033_wheel_modes.sql
  - wheel_modes.py
  - models.py
- **Acceptance criteria:**
  1. Migration adds active_wheel_mode VARCHAR(16) DEFAULT steady to game_state.
  2. wheel_modes.py defines WHEEL_MODES dict with steady, volatile, inverted, gravity, mirror modes.
  3. Each mode has win_pct, loss_pct, jackpot_pct defined per spec S4.
  4. Rotation function: get_rotating_mode(week_number) returns the weekly mode (week % 3: 0=inverted, 1=gravity, 2=mirror).
  5. get_available_modes(week_number) returns steady + volatile + rotating mode.
  6. models.py imports WHEEL_MODES from wheel_modes.py.

### T11: Wheel mode integration in _resolve_spin()

- **Spec ref:** S4
- **Status:** [x]
- **Parallel group:** P1-modes
- **Depends on:** T06, T10
- **Files:**
  - game.py
- **Acceptance criteria:**
  1. _build_spin_context() includes active_wheel_mode from game state.
  2. _resolve_spin() uses mode probabilities instead of secrets.choice([win, lose]).
  3. **Steady mode (default, always available):** 70% win / 28% lose / 2% jackpot. Standard mechanics.
  4. **Volatile mode (always available):** 45% win / 50% lose / 5% jackpot. Standard mechanics, double jackpot payout.
  5. **Inverted mode (weekly rotation, loss-farming):** 60% lose (good) / 35% win (bad) / 5% jackpot (super-good). Escrows losses instead of wins. Shield/guard/resilience trigger on "win" (bad). See T79 for full mechanic.
  6. **Gravity mode (weekly rotation, drift mechanic):** base 55% win / 40% lose / 5% jackpot, modified by gravity_drift (range -35 to +35, ±10 per spin). See T77 for full mechanic.
  7. **Mirror mode (weekly rotation, double escrow):** escrow is 2× normal. Two outcomes rolled independently; better result taken. See T78 for full mechanic.
  8. Jackpot outcome properly resolves (payout * 25 like existing jackpot logic).
  9. Community goal buff (if active) overrides base win_pct.
  10. Mode-change resets: wager_streak → 0, wager_insurance_armed → FALSE, double_down_pending → FALSE, gravity_drift → 0 (T76).

### T12: Wheel mode API + UI

- **Spec ref:** S4, S21
- **Status:** [x]
- **Parallel group:** P1-modes
- **Depends on:** T11
- **Files:**
  - game.py
  - static/app.jsx
- **Acceptance criteria:**
  1. GET /api/wheel-modes returns available modes + active mode.
  2. POST /api/wheel-mode sets active_wheel_mode (validates against available set).
  3. Frontend dropdown shows available modes; unavailable greyed out with tooltip.
  4. Active mode highlighted in dropdown.
  5. Mode description shown on hover.

> **Design audit note (2026-06-18):** `season8-wheel-mode` and `wheel-mode-select` have no CSS (DESIGN-01). The dropdown renders as a bare unstyled `<select>` element. It also renders unconditionally for every user (DESIGN-03) — placed before the main layout, floating above the casino UI. Needs CSS styling and a placement decision (inside the wheel area or gated behind ownership of a non-steady mode).
### T13: Prestige system logic + API

- **Spec ref:** S5
- **Status:** [x]
- **Parallel group:** P1-prestige
- **Depends on:** T01, T02
- **Files:**
  - prestige.py
  - game.py
- **Acceptance criteria:**
  1. prestige.py exists with: get_prestige_bonus(level) returning level * 0.02, get_starting_prestige(legacy_wins) returning 0-5 per mapping in S2.
  2. POST /api/prestige endpoint: requires prestige_unlock owned + wins >= 1M. Resets wins/losses/streak/non-cosmetic upgrades. Increments prestige_level (max 20).
  3. Prestige efficiency: if owned, min wins to prestige = 500K (not 1M).
  4. Prestige legacy: if owned, player keeps N functional upgrades (selected in request body).
  5. _build_spin_context() applies prestige bonus: effective_win_mult *= (1 + prestige_bonus).
  6. Response returns new prestige_level, prestige_count, reset state.

### T14: Prestige UI

- **Spec ref:** S5, S21
- **Status:** [x]
- **Parallel group:** P1-prestige
- **Depends on:** T13
- **Files:**
  - static/app.jsx
- **Acceptance criteria:**
  1. Prestige level display shows current level and bonus percentage.
  2. Prestige button visible only if prestige_unlock owned.
  3. Confirmation modal: "This will reset your wins and non-cosmetic upgrades. Continue?"
  4. Legacy wins badge shows "Seasons 1-7: X wins" using format_wins().
  5. Prestige button disabled if wins < 1M (or 500K if efficiency owned).

> **Design audit note (2026-06-18):** `season8-prestige-panel`, `prestige-badge`, `legacy-badge`, `prestige-btn` have no CSS (DESIGN-01). Confirmation modal uses `onboarding-overlay`/`onboarding-modal` classes — also no CSS, so the modal renders as raw unstyled HTML and is barely usable. Panel is outside the main layout (DESIGN-02).

### T15: Number formatting applied everywhere

- **Spec ref:** S14, S21
- **Status:** [x]
- **Parallel group:** P1-format
- **Depends on:** T03
- **Files:**
  - static/app.jsx
- **Acceptance criteria:**
  1. format_wins() imported from format.js and used in: win count display, loss count, leaderboard, shop costs, wager amounts, community goal progress, singularity meter.
  2. No raw numbers > 999 displayed without formatting anywhere in the UI.
  3. Legacy wins displayed with compact format + (legacy) label.
  4. Frontend compiles without errors.

### T16: Onboarding flow

- **Spec ref:** S15, S21
- **Status:** [!] blocked — superseded by **T43** (redesign required, see bug audit note below)
- **Parallel group:** P1-onboard
- **Depends on:** T01
- **Files:**
  - static/app.jsx
  - game.py
- **Acceptance criteria:**
  1. game_state.onboarding_step column exists (from T01).
  2. /api/state response includes onboarding_step.
  3. /api/spin response includes onboarding_advance: true when spin_count goes from 0 to 1 (step 1 complete).
  4. /api/wager/* response includes onboarding_advance when first stake > 1 used (step 2).
  5. /api/reel response includes onboarding_advance on first catch (step 3).
  6. /api/bounties response includes onboarding_advance when panel first opened (step 4).
  7. Frontend shows modal overlay when onboarding_step < 5.
  8. Each step shows arrow pointing to relevant UI element.
  9. Steps auto-advance when trigger met.

> **Design audit note (2026-06-18):** `onboarding-overlay` and `onboarding-modal` have no CSS (DESIGN-01). The onboarding modal renders as raw unstyled text on a transparent background — effectively invisible or illegible. This is the modal shared by onboarding, prestige confirmation, and legacy boards. Criteria 8 (arrow pointers to UI elements) not implemented. Criteria 7 is wired up but non-functional until CSS exists.

> **Bug audit note (2026-06-19):** CSS was since added (`static/styles.css:4240-4294`) so the modal is now visible/styled, but diagnosing a player report of onboarding being "completely broken" surfaced three foundational defects beyond CSS. This is not a small patch — see **T43** below for the redesign. Acceptance criteria 4, 5, 6, 8, and 9 are unmet; reward granting (spec §15, never covered by any acceptance criterion in this ticket) is entirely missing.
>
> **BUG-O01 — Steps 2-4 have zero backend implementation; onboarding_step can never advance past 1.**
> `game.py` contains exactly one place that writes `onboarding_step` or returns `onboarding_advance`: inside `/api/spin` (lines 813-816, 837, 860), gated on `onboarding_step == 0`, advancing 0→1 on the player's first spin only. `/api/wager/*` (criterion 4), `/api/reel` (criterion 5), and `/api/bounties` (criterion 6) — confirmed via `grep -n onboarding game.py` — contain zero onboarding references. Once a player completes their first spin, `onboarding_step` is permanently stuck at 1 and can never reach 2, 3, 4, or 5 (done), regardless of what the player does afterward.
>
> **BUG-O02 — The overlay is a full-screen blocking modal, making it structurally impossible to perform the step-2/3/4 actions it's asking for, even if BUG-O01 were fixed.**
> `.onboarding-overlay` (`static/styles.css:4240-4249`) is `position: fixed; inset: 0; z-index: 300;` with no `pointer-events: none` — it captures all clicks across the entire viewport. The only interactive element inside it is the "Skip" button (`static/app.jsx:3911`). So while step 2's modal text reads "Try setting a wager stake!", the wager slider (`.wager-stake-control`, `static/app.jsx:4151`) sits underneath the overlay and is unreachable; same for the fishing panel (`.fishing-panel`, `static/app.jsx:1442`) at step 3 and the bounty panel (`.season8-bounties-panel`, `static/app.jsx:4299`) at step 4. This directly contradicts ticket criterion 8 ("each step shows an arrow pointing to the relevant UI element") — a full-screen block and a same-page arrow are mutually exclusive; the modal must not cover the element it's pointing at.
>
> **BUG-O03 — No onboarding rewards are ever granted.**
> Spec §15's step table promises `trail_1` cosmetic (step 1), `confetti_1` cosmetic (step 2), `fish_tropical` skin (step 3), and 100 wager tokens (step 4), stating "the reward is granted automatically." All three cosmetic IDs exist only as paid shop items today (`models.py:153,179`, `static/app.jsx:103` — costing 125/75/25 tokens respectively via `models.py`/`static/app.jsx` shop defs) — confirmed via repo-wide grep that no code path grants any of them for free, nor credits the 100 wager tokens for step 4. The entire reward mechanic described in the spec was never built, and isn't covered by any of this ticket's 9 acceptance criteria — an omission in the original ticket, not just an implementation gap.
>
> **BUG-O04 — "Skip" is the only way out, and it forfeits all rewards silently.**
> Because BUG-O01 makes steps 2-4 permanently unreachable, the unconditional `onClick={() => { setShowOnboarding(false); setOnboardingStep(5); }}` (`static/app.jsx:3911`) is the *only* path every player has out of the modal. Every player who isn't stopped on step 1 forever will, by construction, hit Skip — meaning in practice zero players receive any onboarding reward, and the stated goal of "teaching the core loop" (spec §15 overview) is not met since the taught actions cannot be performed while being taught.

### T17: Migration 040 + chat message_type

- **Spec ref:** S17
- **Status:** [x]
- **Parallel group:** P0-core
- **Depends on:** None
- **Files:**
  - migrations/040_chat_types.sql
  - chat.py
- **Acceptance criteria:**
  1. Migration adds message_type VARCHAR(16) DEFAULT chat to chat_messages.
  2. chat.py post_system_message(username, message, msg_type) function exists.
  3. System messages have user_id = NULL (or reserved system user).
  4. Existing chat endpoints still work (backward compatible).

### T18: Auto-spin cap implementation

- **Spec ref:** S18
- **Status:** [x]
- **Parallel group:** P0-core
- **Depends on:** T01
- **Files:**
  - models.py
  - game.py
- **Acceptance criteria:**
  1. models.py: MAX_SPINS_PER_TICK changed from 100800 to 100.
  2. game_state.auto_spin_budget column used (from T01).
  3. POST /api/auto-spin/start: sets auto_spin_budget = 100.
  4. POST /api/auto-spin/stop: sets auto_spin_budget = 0.
  5. /api/tick: auto-spin uses stake = 1 only, does not increment wager_streak, does not set double_down_pending.
  6. /api/tick: decrements auto_spin_budget per spin. When 0, stops and returns auto_spin_active: false.
  7. /api/state response includes auto_spin_budget.

> **Audit note (2026-06-18):** Three critical bugs found in the auto-spin/manual-spin implementation — the most severe in the Season 8 audit. BUG-01: No manual spin button existed anywhere in the UI. The spec requires manual spinning as the primary mechanic but the agent only kept the old auto-spin tick loop with no way to trigger individual spins. Fixed by adding `handleManualSpin` callback (POST `/api/spin`), a `▶ Spin ◀` button below the wheel, and auto-spin start/stop controls. BUG-02: `/api/tick` budget check was conditional — when `auto_spin_budget = 0` the `spins_due = min(spins_due, budget)` guard was inside an `if budget > 0` block, allowing unlimited spins at budget=0. Fixed by returning early with `auto_spin_active: false` when budget=0. BUG-03: First-tick logic unconditionally set `auto_spin_since = NOW` whenever it was NULL, even with budget=0. This permanently blocked `/api/spin` for users who had never started auto-spin (since the guard checked only `auto_spin_since IS NOT NULL`). Fixed: first-tick activation only runs when `budget > 0`; `/api/spin` guard updated to require both `auto_spin_since IS NOT NULL` AND `budget > 0`. BUG-04: The frontend tick `useEffect` fired unconditionally every 3s regardless of `autoSpinBudget`, so the old Season 7 always-on behaviour persisted on the client. Fixed: effect now gated on `autoSpinBudget > 0`. All four fixed in commit 5acce4a.

### T19: Migration 041: Season 8 themes grant

- **Spec ref:** S16
- **Status:** [x]
- **Parallel group:** P0-core
- **Depends on:** None
- **Files:**
  - migrations/041_season8_themes.sql
- **Acceptance criteria:**
  1. Migration adds theme_tidal to SHOP_ITEMS (via code in models.py, not migration).
  2. Migration auto-grants theme_tidal to all existing users owned_items.
  3. Migration is idempotent (checks if already owned before granting).
  4. python migrate.py applies without error.
---

## Phase 2: Protection & Themes (8.2 / 8.3)

### T20: Migration 035: Protection rework columns

- **Spec ref:** S7
- **Status:** [x]
- **Parallel group:** P2-protect
- **Depends on:** T01
- **Files:**
  - migrations/035_protection_rework.sql
- **Acceptance criteria:**
  1. Adds columns: guard_charges INTEGER DEFAULT 0, guard_last_regen_spin BIGINT DEFAULT 0, resilience_last_use_spin BIGINT DEFAULT 0.
  2. All ALTER statements use IF NOT EXISTS.
  3. python migrate.py applies without error.

### T21: Protection rework logic

- **Spec ref:** S7
- **Status:** [x]
- **Parallel group:** P2-protect
- **Depends on:** T20, T06
- **Files:**
  - game.py
  - models.py
- **Acceptance criteria:**
  1. auto_guard removed from SHOP_ITEMS and _FUNCTIONAL_SHOP_ITEMS.
  2. streak_armor_inf removed from INFINITE_UPGRADES (already done in T04, verify).
  3. Auto-guard purchase logic in _resolve_spin() (lines 184-192) removed entirely.
  4. guard reworked: blocks one loss per manual trigger (not auto). Consumes one guard_charge.
  5. guard_charge shop item: 10000/level, tier 2, max 3 charges.
  6. regen_shield reworked: regenerates 1 guard charge every 50 spins (tracked via spin_count).
  7. resilience reworked: converts loss to 50% refund once per 20 spins.
  8. POST /api/guard endpoint: consumes one guard_charge, sets flag for next loss block.

### T22: Guard API + UI

- **Spec ref:** S7, S21
- **Status:** [x]
- **Parallel group:** P2-protect
- **Depends on:** T21
- **Files:**
  - game.py
  - static/app.jsx
- **Acceptance criteria:**
  1. POST /api/guard: consumes one guard_charge, returns charges remaining.
  2. Frontend shows guard charges available (0-3) with shield icon.
  3. Guard button disabled when charges = 0.
  4. Visual indicator when guard is active (waiting to block next loss).

> **Design audit note (2026-06-18):** `season8-guard-panel`, `guard-charges`, `guard-activate-btn` have no CSS (DESIGN-01). Panel is outside the main layout (DESIGN-02). Should be near the wheel area where the existing shield indicator (`shield-indicator` class) already lives in the right sidebar.

### T23: Ember + Frost theme CSS

- **Spec ref:** S16
- **Status:** [x]
- **Parallel group:** P2-themes
- **Depends on:** None
- **Files:**
  - static/styles.css
  - models.py
- **Acceptance criteria:**
  1. theme_ember added to SHOP_ITEMS (cosmetic, requires theme_tidal or None).
  2. theme_frost added to SHOP_ITEMS (cosmetic, requires theme_ember).
  3. CSS classes for theme_ember: warm orange palette, spark animation on volatile-mode wins.
  4. CSS classes for theme_frost: ice-crystal palette, cracking animation on losses.
  5. Themes can be equipped via existing /api/equip-cosmetic endpoint.
  6. Frontend applies theme class to wheel container.

---

## Phase 3: Fishing Integration (8.4)

### T24: Migration 034: Fishing integration columns

- **Spec ref:** S6
- **Status:** [x]
- **Parallel group:** P3-fish
- **Depends on:** T01
- **Files:**
  - migrations/034_fishing_integration.sql
- **Acceptance criteria:**
  1. Adds columns: wager_tokens INTEGER DEFAULT 0, aquarium_species TEXT[] DEFAULT {}.
  2. All ALTER statements use IF NOT EXISTS.
  3. python migrate.py applies without error.

### T25: Fish-to-wager + aquarium logic

- **Spec ref:** S6
- **Status:** [x]
- **Parallel group:** P3-fish
- **Depends on:** T24, T06
- **Files:**
  - game.py
  - models.py
- **Acceptance criteria:**
  1. Fish-to-wager rate table added to models.py (5/15/40/100/250/500 by tier).
  2. fish_to_wager shop item (5000 wins, tier 1) added to SHOP_ITEMS.
  3. lure_specialization shop item (10000/each, tier 2, requires fish_to_wager) added.
  4. catch_of_the_day shop item (3000 wins, tier 1) added.
  5. aquarium shop item (15000 wins, tier 2) added.
  6. POST /api/fish-to-wager endpoint: converts caught fish to wager_tokens.
  7. /api/reel response awards wager_tokens (when fish_to_wager owned) in addition to fish_clicks.
  8. Aquarium luck bonus: each unique species in aquarium_species adds +0.1% to base win%. Applied in _build_spin_context().
  9. catch_of_the_day: first catch each UTC day worth 5x wager tokens (tracked via timestamp).
  10. GET /api/aquarium endpoint returns species list, luck bonus, display data.

### T26: Fishing panel UI updates

- **Spec ref:** S6, S21
- **Status:** [x]
- **Parallel group:** P3-fish
- **Depends on:** T25
- **Files:**
  - static/app.jsx
- **Acceptance criteria:**
  1. Aquarium panel: grid of caught species (colored) and uncaught (silhouettes).
  2. Luck bonus readout: "+X.X% wheel luck".
  3. Fish-to-wager conversion button (if fish_to_wager owned).
  4. Wager token count displayed in fishing panel.
  5. Catch-of-the-day timer/bonus indicator.
---

## Phase 4: Community & Social (8.5)

### T27: Migration 037: Community goals tables

- **Spec ref:** S9
- **Status:** [x]
- **Parallel group:** P4-comm
- **Depends on:** T01
- **Files:**
  - migrations/037_community_goals.sql
- **Acceptance criteria:**
  1. Creates community_goals table (id, goal_id, season_number, week_number, target, current, completed, completed_at, started_at).
  2. Creates community_goal_contributions table (goal_id, user_id, contributed).
  3. UNIQUE(season_number, week_number) constraint on community_goals.
  4. Primary key (goal_id, user_id) on community_goal_contributions.
  5. Idempotent (CREATE TABLE IF NOT EXISTS).
  6. **milestone columns:** `milestone_25 BOOLEAN NOT NULL DEFAULT FALSE`, `milestone_50 BOOLEAN NOT NULL DEFAULT FALSE`, `milestone_75 BOOLEAN NOT NULL DEFAULT FALSE` on community_goals. Used for 25/50/75% threshold auto-post messages (T84).
  7. python migrate.py applies without error.

### T28: Community goal logic + tracking

- **Spec ref:** S9
- **Status:** [x]
- **Parallel group:** P4-comm
- **Depends on:** T27
- **Files:**
  - community_goals.py
  - game.py
  - models.py
- **Acceptance criteria:**
  1. COMMUNITY_GOAL_DEFS added to models.py with 5 goals (goal_fish5000, goal_jackpot500, goal_prestige50, goal_wager100k, goal_species100).
  2. community_goals.py: get_active_goal(conn) returns current week goal.
  3. community_goals.py: increment_goal(conn, goal_id, user_id, amount) increments goal + player contribution (enforces per-player cap).
  4. community_goals.py: check_goal_completion(conn) marks goal completed, triggers reward distribution.
  5. Weekly rotation: goal selected by week_number % len(COMMUNITY_GOAL_DEFS).
  6. Contribution hooks: /api/spin (jackpot, wager), /api/reel (fish), /api/prestige (prestige) call increment_goal after success.
  7. GET /api/community-goal endpoint returns active goal, progress, player contribution, reward info.

### T29: Community goal UI

- **Spec ref:** S9, S21
- **Status:** [x]
- **Parallel group:** P4-comm
- **Depends on:** T28
- **Files:**
  - static/app.jsx
- **Acceptance criteria:**
  1. Community goal widget: progress bar (current / target).
  2. Player contribution: "You: X / cap Y".
  3. Reward preview on hover.
  4. Uses format_wins() for number display.
  5. Updates on /api/state poll.

> **Design audit note (2026-06-18):** `season8-community-goal`, `goal-label`, `goal-desc`, `goal-progress-bar`, `goal-progress-fill`, `goal-progress-text`, `goal-contrib` have no CSS (DESIGN-01). The community goal widget renders as raw unstyled text with a progress bar div that has no height or colour. Widget is outside the main layout (DESIGN-02).

> **Audit note (2026-06-18):** BUG-10: The old Season 7 `CommunityPot` component (which represented the permanently-maxed 75% community pot) was still rendered in both the user bar and the mobile panel, alongside the new community goal widget. These are different systems — `CommunityPot` is a Season 7 relic that was replaced by Community Goals. Removed both occurrences from JSX in commit 5acce4a.

> **Bug audit note (2026-06-19):** T28 acceptance criteria 4 and 6 are not met. The community goal system shares the exact same disease as the bounty system (see T41 bug audit note above) — same two endpoints (`/api/reel`, `/api/prestige`) are missing hooks — plus an additional defect where it has no reward payout at all. Four concrete defects found:
> **Fix status (2026-06-19):** ALL FIXED. See `SEASON_8_PROGRESS.md` → "Bug Audit — 2026-06-19" for full resolution summary.
>
> **BUG-C01 — `fish_caught` metric (`goal_fish5000`) never incremented (`game.py` → `/api/reel`, `def reel_line` at line 1795).**
> The reel endpoint's successful-catch path (species rolled at line 1850, `conn.commit()` at line 1947) has no `get_active_goal` / `increment_goal` call. "Catch 5,000 fish server-wide" progress will never advance from fishing, regardless of how many fish are caught across all players. Fix: inside the success branch, before `conn.commit()` at line 1947, mirror the pattern at `game.py:795-806` (used in the spin endpoint) — call `get_active_goal(conn, season_num, week_num)` (season/week must be derived the same way as lines 796-798: `get_season_info(conn)` and `get_week_number(now_utc)`), then `if goal_def and goal_def['metric'] == 'fish_caught': increment_goal(conn, goal_def['goal_id'], current_user.id, 1); check_goal_completion(conn, goal_def['goal_id'])`.
>
> **BUG-C02 — `prestiges` metric (`goal_prestige50`) never incremented (`game.py` → `/api/prestige` POST, `def prestige_reset` at line 2510).**
> The prestige endpoint (`conn.commit()` at line 2543) has no `get_active_goal` / `increment_goal` call. "Prestige 50 times server-wide" progress will never advance. Fix: same pattern as BUG-C01 — add the goal lookup + `if goal_def and goal_def['metric'] == 'prestiges': increment_goal(conn, goal_def['goal_id'], current_user.id, 1); check_goal_completion(conn, goal_def['goal_id'])` before `conn.commit()` at line 2543.
>
> **BUG-C03 — `unique_species` metric (`goal_species100`) never incremented anywhere.**
> No code references this metric. The reel endpoint already computes `first_catch = species_id not in caught_species` at line 1875 (true exactly when a player discovers a new species) — this is the natural hook point, in the same success branch as BUG-C01. Fix: `if goal_def and goal_def['metric'] == 'unique_species' and first_catch: increment_goal(conn, goal_def['goal_id'], current_user.id, 1); check_goal_completion(conn, goal_def['goal_id'])`, added alongside the BUG-C01 fix in `/api/reel`.
>
> **BUG-C04 — Goal completion never pays out `reward_tokens` / `reward_fragments` to any player; no claim mechanism exists.**
> `check_goal_completion()` in `community_goals.py` (lines 144–169) only flips `community_pot.filled = TRUE` and sets `win_chance_pct = 55.0` — a side effect on the unrelated Season 7 `community_pot` table. It never reads `goal_def['reward_tokens']` (500) or `goal_def['reward_fragments']` (1) from `COMMUNITY_GOAL_DEFS` (`community_goals.py` lines 11–62), and never credits any contributing player's `game_state.wager_tokens` or `game_state.cosmetic_fragments`. Unlike bounties — which at least have a (broken, see BUG-B02) `/api/bounties/claim` endpoint — there is no `/api/community-goal/claim` endpoint or any other distribution path. Even a fully-completed community goal currently rewards nobody. Fix needs: (a) decide reward semantics per spec (e.g. distribute to every contributor of the completed goal, querying `community_goal_contributions` for `goal_id`), (b) implement payout inside or immediately after `check_goal_completion` returns `True`, (c) credit `reward_tokens`/`reward_fragments` to each contributor's `game_state` row, (d) consider whether `reward_buff` (+5% win% for a week) is the same thing as the `win_chance_pct = 55.0` pot side-effect already present, or a separate per-player buff that also needs implementing.

### T30: Migration 039 + singularity rework

- **Spec ref:** S13
- **Status:** [x]
- **Parallel group:** P4-sing
- **Depends on:** T27
- **Files:**
  - migrations/039_singularity_rework.sql
  - game.py
  - models.py
- **Acceptance criteria:**
  1. Creates singularity_meter table (id, total_contributed, target, filled, filled_at, fill_count).
  2. singularity removed from SHOP_ITEMS.
  3. The owned singularity check in _resolve_spin() (line 196) removed.
  4. GET /api/singularity returns meter progress, target, fill_count.
  5. POST /api/singularity/contribute: accepts amount, deducts fish_clicks, adds to meter. Enforces per-player cap (25M).
  6. When meter fills: sets filled=true, increments fill_count, triggers singularity wheel mode unlock.
  7. singularity wheel mode: 75% win, 10% loss, 15% jackpot (added to WHEEL_MODES).

### T31: Singularity UI

- **Spec ref:** S13, S21
- **Status:** [x]
- **Parallel group:** P4-sing
- **Depends on:** T30
- **Files:**
  - static/app.jsx
- **Acceptance criteria:**
  1. Singularity meter progress bar with "X / 100M fish_clicks".
  2. Contribute button with amount input.
  3. Per-player cap display: "You: X / 25M".
  4. Fill count display (if > 0): "Convergences: N".
  5. Notification when meter fills (visual + system message in chat).

> **Design audit note (2026-06-18):** `season8-singularity-panel`, `singularity-label`, `singularity-progress-bar`, `singularity-progress-fill`, `singularity-progress-text`, `singularity-fills`, `singularity-contribute-btn` have no CSS (DESIGN-01). The contribute button uses `prompt()` (a browser native dialog) for input — this was acceptable as a stub but is not a finished UI. Panel is outside the main layout (DESIGN-02).

> **Audit note (2026-06-18):** BUG-07: The singularity contribute handler deducted from `wins` (`setWins(prev => prev - amount)`) instead of `fishClicks` (`setFishClicks(prev => prev - amount)`). The spec clearly states contributions come from `fish_clicks`, not wins. The backend `/api/singularity/contribute` correctly deducts from `fish_clicks`; only the optimistic UI update was wrong. Toast message also said "wins" instead of "fish". Fixed in commit 5acce4a.

> **Audit note (2026-06-19) — regression, contradicts the BUG-07 note above:** Live-tested via browser (Playwright) by actually clicking the singularity contribute button. Got a 403 "Insufficient wins" even though the test account had 0 wins and 2 `fish_clicks`. Read the current `/api/singularity/contribute` handler (`game.py:2764-2801`) — as of today it:
> 1. Gates on `gs['wins']` (`game.py:2782`: `if int(gs['wins']) < amount: return ... 403`), not `fish_clicks`, contradicting both the spec (S13) and acceptance criterion 5 above ("deducts fish_clicks").
> 2. **Never deducts anything from `game_state` at all** — the `UPDATE` (`game.py:2784-2790`) only touches the `singularity_meter` table (`total_contributed`), with no corresponding `UPDATE game_state SET fish_clicks = fish_clicks - %s` (or wins) anywhere in the function.
>
> Net effect: players with `fish_clicks` but no `wins` are incorrectly blocked (what I hit); players who do have enough `wins` can contribute for free, repeatedly, since nothing is ever actually debited server-side — the frontend's `setFishClicks(prev => prev - amount)` optimistic update is purely cosmetic and will desync from the server on next refresh. This is either a fresh regression introduced after the 2026-06-18 fix above (possibly while touching `wins`-related code elsewhere, e.g. the wager work) or the 2026-06-18 note's claim about the backend was never actually true — git blame on `game.py`'s singularity_contribute would settle which, not done here. Not fixed as part of this pass; flagging for triage alongside T45.

### T32: Migration 038 + loadout system

- **Spec ref:** S11
- **Status:** [x]
- **Parallel group:** P4-load
- **Depends on:** T01
- **Files:**
  - migrations/038_loadouts.sql
  - game.py
- **Acceptance criteria:**
  1. Creates build_loadouts table (user_id, slot 1-3, name, config JSONB, updated_at).
  2. GET /api/loadouts returns all 3 slots.
  3. POST /api/loadouts/save: saves name + config to a slot.
  4. POST /api/loadouts/equip: applies loadout (sets equipped_class, active_wheel_mode, preferred_stake as UI default).
  5. Config JSONB schema: {equipped_class, active_wheel_mode, preferred_stake, note}.
  6. Rate limited @limiter.limit.

### T33: Loadout UI

- **Spec ref:** S11, S21
- **Status:** [x]
- **Parallel group:** P4-load
- **Depends on:** T32
- **Files:**
  - static/app.jsx
- **Acceptance criteria:**
  1. 3 loadout slots displayed with name and config summary.
  2. Save current setup button per slot.
  3. Equip loadout button (one click).
  4. Edit name field per slot.
  5. Delete/clear slot option.

> **Design audit note (2026-06-18):** `season8-loadout-panel`, `loadout-label`, `loadout-slots`, `loadout-slot`, `loadout-save-btn`, `loadout-apply-btn` have no CSS (DESIGN-01). Panel renders unconditionally for all users regardless of game state (DESIGN-04) — three "Save / Equip" button pairs visible from the very start. No edit-name field (criteria 4) or delete option (criteria 5) implemented. Panels are outside the main layout (DESIGN-02).

### T34: Replay encoding + sharing

- **Spec ref:** S12
- **Status:** [x]
- **Parallel group:** P4-replay
- **Depends on:** T06
- **Files:**
  - replays.py
  - game.py
  - chat.py
- **Acceptance criteria:**
  1. replays.py: generate_replay(username, mode, stake, result, wins_delta, timestamp, double_down) returns base64 string.
  2. Trigger conditions: jackpot hit, double-down win at 5x+ stake, hot-streak reaches 10.
  3. /api/spin and /api/wager/double-down responses include replay_string when trigger met (null otherwise).
  4. POST /api/replay/share: posts replay to chat as message_type=replay.
  5. chat.py stores replay messages with message_type=replay.

### T35: Chat revival system messages (replaces replay system)

- **Spec ref:** S12 (auto-post system messages)
- **Status:** [x]
- **Parallel group:** P4-chat
- **Depends on:** T17, T82 (auto-post), T89 (replay removal)
- **Files:**
  - chat.py
  - game.py
  - static/app.jsx
- **Acceptance criteria:**
  1. Auto-post system messages replace the v1 replay system. Replay sharing is **removed entirely** (T89).
  2. System messages have user_id = NULL, message_type = 'system' or 'event', username = 'SYSTEM'.
  3. **message_type vocabulary fix (B9):** frontend uses `!['user', 'chat'].includes(m.message_type)` to detect system messages (one-line fix in `app.jsx:2222`).
  4. Throttled: per-`event_kind` 30s throttle (T92); each event kind has its own throttle window.
  5. System messages have distinct styling (italic, muted).
  6. Auto-scroll to new messages.
  7. **Events NOT broadcast:** bounty completion stays in bounty panel only (B21 — remove chat post at `game.py:2812`). Replay cards removed.
  8. **Events broadcast (full list, see T82 for trigger constants):** jackpot (any), double-down win at effective_stake ≥5, hot streak 10, big win (per-player escalating threshold, T83), prestige, new player first spin, singularity fill, community goal milestones (25/50/75%).

---

## Phase 5: Polish & Ongoing (8.6+)

### T36: Legacy boards API + UI

- **Spec ref:** S10, S21
- **Status:** [x]
- **Parallel group:** P5-legacy
- **Depends on:** T01
- **Files:**
  - game.py
  - static/app.jsx
- **Acceptance criteria:**
  1. GET /api/legacy-boards returns all seasons from season_snapshots grouped by season_number.
  2. Frontend leaderboard panel: tab toggle [Season 8] [Hall of Fame].
  3. Hall of Fame: season dropdown (1-7), top-5 display per season.
  4. Legacy wins badge on player profile: "Seasons 1-7: X wins" using format_wins().

### T37: Accessibility pass

- **Spec ref:** S8.7
- **Status:** [x]
- **Parallel group:** P5-a11y
- **Depends on:** None
- **Files:**
  - static/app.jsx
  - static/styles.css
- **Acceptance criteria:**
  1. Reduced motion toggle: disables spark/aurora/cracking animations.
  2. High-contrast theme variant.
  3. aria-live region on spin result for screen readers.
  4. Keyboard spin: spacebar triggers spin, number keys 1-0 select stake.
  5. Settings persisted in user preferences.

> **Design audit note (2026-06-18):** `season8-a11y-panel` and `a11y-toggle` have no CSS (DESIGN-01). The accessibility panel (reduced motion + high contrast checkboxes + Hall of Fame button) renders unconditionally for all users in the unstyled top block (DESIGN-03). These settings should be in a modal/settings drawer triggered from the user bar, not always-visible floating controls. The `onboarding-overlay`/`onboarding-modal` classes used by the legacy boards modal also have no CSS.

> **Audit note (2026-06-18):** BUG-12: The spacebar keyboard shortcut handler existed but called `tick()` (the auto-spin tick function) instead of the manual spin. Since auto-spin can run without the button, this was a no-op or a spurious tick call. The comment in code said "spin" but invoked the wrong function. Fixed to call `handleManualSpin()` in commit 5acce4a.

### T38: Aurora theme

- **Spec ref:** S16
- **Status:** [x]
- **Parallel group:** P5-themes
- **Depends on:** None
- **Files:**
  - static/styles.css
  - models.py
- **Acceptance criteria:**
  1. theme_aurora added to SHOP_ITEMS (cosmetic, requires theme_frost).
  2. CSS classes: shifting greens/purples, northern-lights trail on wheel pointer.
  3. Theme equippable via /api/equip-cosmetic.

### T39: Vintage theme (tom7 callback)

- **Spec ref:** S16
- **Status:** [x]
- **Parallel group:** P5-themes
- **Depends on:** None
- **Files:**
  - static/styles.css
  - models.py
- **Acceptance criteria:**
  1. theme_vintage added to SHOP_ITEMS (cosmetic).
  2. CSS classes: retro-styled, visually references Season 1-2 aesthetics.
  3. Theme equippable via /api/equip-cosmetic.

### T40: Migration 036 + bounty system

- **Spec ref:** S8
- **Status:** [x]
- **Parallel group:** P1-bounty
- **Depends on:** T01, T06
- **Files:**
  - migrations/036_bounties.sql
  - bounties.py
  - game.py
  - models.py
- **Acceptance criteria:**
  1. Creates bounty_progress table (user_id, bounty_date, bounty_id, progress, completed, completed_at).
  2. Adds cosmetic_fragments INTEGER DEFAULT 0 to game_state.
  3. BOUNTY_DEFS added to models.py with 8 bounty definitions.
  4. bounties.py: get_daily_bounties(user_id, date) returns 3 bounties (deterministic per user+date).
  5. bounties.py: increment_bounty(conn, user_id, bounty_id, amount) updates progress.
  6. Tracking hooks in /api/spin, /api/wager/*, /api/reel, /api/prestige call increment_bounty.
  7. GET /api/bounties returns today 3 bounties with progress.
  8. POST /api/bounties/claim: claims rewards (100/250/500 tokens + fragment for all 3).
  9. Bounties reset at UTC midnight.

### T41: Bounty panel UI

- **Spec ref:** S8, S21
- **Status:** [x]
- **Parallel group:** P1-bounty
- **Depends on:** T40
- **Files:**
  - static/app.jsx
- **Acceptance criteria:**
  1. Three bounty cards with progress bars.
  2. Claim button enabled when all 3 complete.
  3. Cosmetic fragment counter displayed.
  4. Bounty descriptions human-readable (not raw IDs).
  5. Updates on /api/state poll.

> **Design audit note (2026-06-18):** `season8-bounties-panel`, `bounties-header`, `bounty-card`, `bounty-desc`, `bounty-progress-bar`, `bounty-progress-fill`, `bounty-progress-text`, `bounty-claim-btn`, `fragment-count` have no CSS (DESIGN-01). Progress bars render as zero-height invisible divs. Panel is outside the main layout (DESIGN-02). Claim button (criteria 2) claims individual bounties by ID, not all 3 at once as spec implies. No "claim all" button.

> **Bug audit note (2026-06-19):** T40 acceptance criteria 6 and 8 are not met. Three concrete defects found:
> **Fix status (2026-06-19):** ALL FIXED. See `SEASON_8_PROGRESS.md` → "Bug Audit — 2026-06-19" for full resolution summary.
>
> ~~**BUG-B01 — `bounty_fish10` never incremented (`game.py` → `/api/reel`).**~~
> ~~The reel endpoint has no `increment_bounty` call. "Catch 10 fish" progress will never advance.~~ **FIXED** (2026-06-19): `increment_bounty` call added at game.py line 1953.
>
> ~~**BUG-B02 — Five bounty types have no tracking wired at all (`game.py`).**~~
> ~~Only `bounty_jackpot`, `bounty_wager5`, and `bounty_streak10` call `increment_bounty`. The following five are never incremented anywhere: `bounty_fish10`, `bounty_prestige`, `bounty_mirror`, `bounty_bank`, `bounty_double`.~~ **ALL FIXED** (2026-06-19): Each site now calls `increment_bounty`:
> - `bounty_fish10` → game.py:1953 (reel endpoint)
> - `bounty_prestige` → game.py:2568 (prestige endpoint)
> - `bounty_mirror` → game.py:795 (spin endpoint, mirror mode check)
> - `bounty_bank` → game.py:2460 (wager/bank endpoint)
> - `bounty_double` → game.py:797 (spin endpoint, double_down_active check)
>
> ~~**BUG-B03 — `get_claim_rewards` signature mismatch; claim endpoint crashes at runtime (`game.py:2600`, `bounties.py:164`).**~~
> ~~`game.py` calls `get_claim_rewards(conn, current_user.id, bounty_id, bounty_date)` (4 args). `bounties.py` defines `def get_claim_rewards(completed_count)` (1 arg) and returns a `(tokens, fragments)` tuple.~~ **FIXED** (2026-06-19): `get_claim_rewards` now queries `bounty_progress` for completed count per user/date and returns a dict `{'tokens': N, 'cosmetic_fragments': N}`. Claim endpoint credits both `wager_tokens` and `cosmetic_fragments`.

### T42: Live-refresh bounty & community goal panels

- **Spec ref:** S8, S9, S21
- **Status:** [x]
- **Parallel group:** P5-live
- **Depends on:** T41, T29, BUG-B01/B02/B03 (fixed), BUG-C01/C02/C03 (fixed)
- **Files:**
  - static/app.jsx

**Bug report (2026-06-19):** Now that the backend tracking hooks are fixed (BUG-B01–B03, BUG-C01–C03), bounty and community-goal progress *does* advance server-side, but the frontend panels do not reflect it live. A player who catches a fish sees no change in their "Catch 10 fish" bounty card or the community goal's fish-catch progress until some unrelated event (e.g. a jackpot spin, which happens to trigger a bounty re-fetch) or the 60s season-poll forces a refresh. This reads as "still broken" even though the underlying data is now correct.

There are two distinct refresh needs, because bounties are purely personal (`bounty_progress` is keyed per `user_id`) while the community goal is shared server-wide (`community_goals.current` is incremented by every player):

1. **Personal/local — instant, event-driven.** Anything *this* player does that can move their own bounty progress or their own community-goal contribution should refresh those two panels immediately after the action's response comes back. No polling needed for this half — it's triggered by the player's own request completing.
2. **Server-wide — periodic background poll.** The community goal's total (`current`/`target`) can move from *other players'* actions at any time, independent of anything this player does. Only a timer can catch that.

**Existing precedent in the codebase (reuse these patterns, don't invent new ones):**

- **Event-driven refresh (precedent already exists, just incomplete):** `applySpinResult` (`static/app.jsx` ~line 3392-3395) already does `if (data.jackpot_hit || data.wager_streak === 10) { apiGame('/api/bounties').then(r => { if (r.ok) setBounties(r.data.bounties || []); }); }` after a spin. This is the right shape, but: (a) it only covers two of the eight bounty trigger conditions (jackpot, streak10 — missing wager5, fish10, prestige, mirror, bank, double), (b) it never refreshes `/api/community-goal` at all, and (c) the fish-catch path (`handleReel` in `FishingPanel`, ~line 1410-1434) and the AFK auto-fish tick (~line 1280-1320, the `tick()` function feeding `autoFishIntervalRef`) have no equivalent call whatsoever — these are exactly the paths BUG-B01/C01/C03 just fixed server-side.
- **Periodic background poll (precedent already exists):** The leaderboard poll (`static/app.jsx` ~line 2000-2013) is the model to copy: `useEffect` holding an `AbortController`, a `load()` that bails early via `if (document.hidden) return;` (don't poll backgrounded tabs), aborts any in-flight request before firing a new one, and `setInterval(load, 15000)` with cleanup of both the interval and the abort controller on unmount. Chat uses the identical shape at 5000ms (~line 2140-2150). 15s (leaderboard's cadence) is the recommended interval for the community goal poll — it's a "watch the number tick up" stat, not a real-time feed like chat, so there's no reason to poll faster and add server load.

**Architecture for the fix:**

1. **Extract a shared refresh helper** in the top-level `App` component (where `bounties`/`communityGoal` state already lives, `static/app.jsx` ~line 3627-3629) — something like `refreshBountiesAndGoal()` that calls `/api/bounties` and `/api/community-goal` and updates `setBounties`/`setCommunityGoal`. Replace the existing inline call at ~line 3393-3394 with this helper, and call it from every action handler that can move personal progress:
   - `applySpinResult` — expand the trigger condition to cover all spin-driven bounty/goal metrics (jackpot, wager5/wins_wagered, streak10, mirror, double), not just jackpot/streak10.
   - `handleReel` (`FishingPanel`, ~line 1410-1434) and the auto-fish `tick()` (~line 1280-1320) — currently call `onFishBucksUpdate`/`onCaughtSpeciesUpdate` on a hit; add a third callback (e.g. `onFishCaught`) following the exact same prop-drilling pattern, wired at both `<FishingPanel>` render sites (~line 3990 and ~line 4004), that the `App` component implements by calling the shared refresh helper.
   - The prestige action handler and the wager-bank action handler (wherever those POST to `/api/prestige` and the bank endpoint respectively) — call the refresh helper on success.
   - Note bounties only (not the community goal) need refreshing after bank/double/mirror, since those three are bounty-only metrics with no community-goal equivalent — the shared helper can safely refresh both every time regardless, the redundant `/api/community-goal` call is cheap and keeps the call sites simple.

2. **Add the background poll** as a new `useEffect` in `App`, modeled exactly on the leaderboard's `useEffect` (~line 2000-2013): `AbortController`, `document.hidden` guard, fetch `/api/community-goal`, `setCommunityGoal(r.data)` on success, `setInterval(load, 15000)`, cleanup both on unmount. This is additive to (1) — the event-driven refresh gives the player instant feedback on their own contribution, the poll catches everyone else's.
   - Bounties do **not** need a background poll (no other player can affect another player's personal bounty progress) — only the event-driven refresh in (1) applies to bounties.

3. **Acceptance criteria for whoever implements this:**
   1. Catching a fish (manual reel or AFK auto-fish) updates the bounty panel's fish-catch bounty progress and the community goal panel's contribution/total within one render, without waiting for any other trigger.
   2. Winning a wager-5x+ spin, hitting a streak of 10, prestiging, banking, or winning a double-down all refresh the bounty panel immediately (covering all 8 bounty types, not just jackpot/streak10).
   3. The community goal total visibly advances within ~15s of *another* player's qualifying action, without this player taking any action themselves (verify with two sessions/users).
   4. No polling occurs while `document.hidden` is true (tab backgrounded).
   5. No duplicate/overlapping requests — in-flight requests are aborted before a new poll fires (same as leaderboard/chat pattern).
   6. No new backend changes required — this is frontend-only, the tracking hooks are already fixed server-side.

**Fix status (2026-06-19):** Implemented, with two defects found in review and corrected directly (commit `54d8bb0`):

- Sub-agent correctly wired `onFishCaught` through `FishingPanel` (manual reel + AFK auto-fish tick, both render sites), made `applySpinResult` call `refreshBountiesAndGoal()` unconditionally on every spin (a cleaner solution than enumerating each of the 5 spin-driven metrics individually — satisfies criterion 2 in one call), and added the calls to `handlePrestige` and the wager-bank button handler. The 15s background poll (criteria 3, 4) was added with the correct interval and `document.hidden` guard.
- **Bug found — wrong response shape:** `refreshBountiesAndGoal()` did `setCommunityGoal(goalRes.data)`, but `/api/community-goal` returns `{goal: {...}}` (see `game.py:2664-2672`) — the panel reads `communityGoal.current/target/description/player_contribution` directly, so every spin/catch/prestige/bank action broke the panel (`NaN%` progress, blank text) until the next 15s poll cycle silently fixed it again (the poll's own handler correctly read `data.goal`). **Fixed:** changed to `setCommunityGoal(goalRes.data.goal)`.
- **Criterion 5 not actually met:** the poll created an `AbortController` and called `.abort()` on unmount, but never passed `signal: ctrl.signal` into the `apiGame()` call, so the abort was a no-op, and it didn't recreate+abort a fresh controller per tick like the leaderboard precedent. **Fixed:** `ctrl` is now reassigned to a new `AbortController` inside `load()` before each request (aborting the previous one first), and its `signal` is passed into `apiGame('/api/community-goal', { signal: ctrl.signal })`, matching the leaderboard/chat pattern exactly.

### T43: Onboarding flow redesign (supersedes T16)

- **Spec ref:** S15, S21
- **Status:** [x]
- **Parallel group:** P5-onboard
- **Depends on:** T16 (superseded, do not re-implement its design as-is — see bug audit note on T16)
- **Files:**
  - static/app.jsx
  - static/styles.css
  - game.py

**Why a redesign and not a patch:** T16's bugs (BUG-O01 through BUG-O04, see audit note above) aren't independent — BUG-O02 (full-screen blocking modal) makes the spec'd behavior structurally impossible regardless of whether BUG-O01 (missing backend triggers) is patched, because the modal physically prevents the player from reaching the UI element the step is asking them to use. Patching the backend triggers alone would not fix the experience. This needs the UI pattern rethought, not just the four missing `increment`-style hooks bolted on.

**Spec recap (`SEASON_8_BUILD_SPEC.md` §15):**

| Step | Trigger | Teaches | Reward |
|---|---|---|---|
| 1. First spin | `spin_count` 0→1 | Click to spin, win/lose | `trail_1` cosmetic |
| 2. First wager | `wager_unlock` owned, first stake > 1 | Higher stake = bigger win/loss | `confetti_1` cosmetic |
| 3. First fish | First cast + reel | Cast, wait for bite, reel | `fish_tropical` skin |
| 4. First bounty | Bounty panel opened | Daily objectives | 100 wager tokens |

`onboarding_step`: 0 = not started, 1-4 = that step completed, 5 = all done. Per spec, the reward for each step is granted automatically when the step completes — this was never built (BUG-O03) and needs to be added now, it's in scope for this ticket.

**Proposed architecture:**

1. **Replace the full-screen blocking modal with a non-blocking coach-mark/spotlight,** anchored to the relevant element instead of covering the whole screen:
   - Step 1 (before first spin): anchor to `.wheel-wrapper`.
   - Step 2: anchor to `.wager-stake-control` (`static/app.jsx:4151`).
   - Step 3: anchor to `.fishing-panel` (`static/app.jsx:1442`).
   - Step 4: anchor to `.season8-bounties-panel` (`static/app.jsx:4299`).
   - Implementation shape: a small dismissible card positioned near the anchor element (e.g. `position: absolute` relative to the anchor's bounding rect, or a `position: fixed` card pinned to a screen corner with a CSS-drawn arrow/line pointing at the anchor) — NOT a full-viewport `position: fixed; inset: 0` div. The rest of the page must remain fully interactive at all times so the player can actually perform the taught action. This is what satisfies the existing (currently unimplemented) criterion 8 from T16 — keep that criterion, this ticket is what finally implements it.
   - A small dismiss/skip control should still exist per-step (for players who don't want guidance), but skipping one step should only hide that step's card — it should still be possible to advance via natural play, and skipping should not forfeit the reward for steps already completed.

2. **Add the missing backend triggers (fixes BUG-O01), following the exact pattern already used for `onboarding_advance` in `/api/spin`:**
   - `/api/wager/*` (or wherever stake is set — check the stake-change handler) — set `onboarding_advance` / advance `onboarding_step` 1→2 when `wager_unlock` is owned and a stake > 1 is used for the first time.
   - `/api/reel` — advance 2→3 on first successful catch (`result == 'hit'`).
   - `/api/bounties` (GET) — advance 3→4 the first time this endpoint is called by a given user (i.e. first time the panel is opened/fetched) — confirm this is still the right trigger semantics, since a GET firing on every poll/page-load needs an explicit "have we already advanced past 3" guard (the existing step-1 pattern's `CASE WHEN onboarding_step = 0 THEN 1 ELSE onboarding_step END` SQL idiom is the right model — generalize it to `CASE WHEN onboarding_step = N THEN N+1 ELSE onboarding_step END` at each trigger site).
   - Step 4→5 (all done): advance once step 4's reward is granted.

3. **Add reward granting (fixes BUG-O03)**, at each of the four trigger sites above:
   - Step 1 complete → grant `trail_1` cosmetic (add to `owned_items`/`active_cosmetics` per however other free/granted cosmetics are added elsewhere in the codebase — check how prestige or season-transition grants work for precedent).
   - Step 2 complete → grant `confetti_1` cosmetic.
   - Step 3 complete → grant `fish_tropical` skin.
   - Step 4 complete → credit 100 `wager_tokens`.
   - Decide and document reward semantics if a step is "skipped" via the per-step dismiss control from (1) — recommend: dismissing the coach-mark only hides the UI, it does not skip the underlying trigger, so the reward is still granted whenever the player naturally performs the action later. There is no longer a single "Skip entire flow" button forfeiting everything, since the new design isn't blocking — open question for whoever implements this if product wants an explicit full opt-out somewhere (e.g. a settings toggle), flag it rather than assume.

4. **Acceptance criteria for whoever implements this:**
   1. The onboarding coach-mark never blocks pointer events to the rest of the page — verify by checking computed `pointer-events` / `position` and by clicking through to the anchored element while a coach-mark is showing.
   2. Each of the 4 steps has a visible arrow/pointer or equivalent visual anchor to its target element (satisfies T16's original criterion 8).
   3. Performing the real action for the current step (spin, set stake > 1, catch a fish, open bounties) advances `onboarding_step` and grants that step's reward, verified by checking `owned_items`/`active_cosmetics`/`wager_tokens` after each step — not just that the modal disappears.
   4. A player who completes all 4 steps receives all 4 rewards exactly once each — verify no double-granting on repeat triggers (e.g. opening the bounty panel a second time shouldn't grant another 100 tokens).
   5. `onboarding_step` reaches 5 only after step 4 actually completes, not via a single unconditional skip button.
   6. Existing players with `onboarding_step` already stuck at 1 from the old broken flow are handled sensibly (e.g. they resume at step 2 with the new coach-mark, rather than being stuck or having the flow silently restart from 0).

### T44: Wager system explainer tooltip

- **Spec ref:** S3, S21
- **Status:** [x]
- **Parallel group:** P5-wager
- **Depends on:** T09 (and ideally BUG-W01/BUG-W02 fixes above, so the tooltip doesn't describe mechanics that can't currently be reached — see note below)
- **Files:**
  - static/app.jsx
  - static/styles.css

**Player report (2026-06-19):** Now that the wager panel is reachable (T09 diagnostic note above — required granting wins for testing, system itself was never broken), the player who tested it could see the stake slider, hot-streak label, etc., but couldn't tell what any of it actually does or what the risk/reward tradeoff is. Spec describes a genuinely non-obvious set of mechanics (stake multiplier, hot streak, banking, double-down, insurance, safety net) with no in-game explanation anywhere. Requested: a small "(?)" button that reveals an explainer tooltip on hover, the same way wheel modes already do.

**Precedent to copy exactly** — this is a styling/content task, not a new interaction pattern:

- **JSX:** `WHEEL_MODE_INFO` (`static/app.jsx:3706-3713`) is a plain object of `{ label, desc }` keyed by mode, consumed at the button via `data-tooltip={info.desc}` (`static/app.jsx:4240`).
- **CSS:** `.wheel-mode-btn { position: relative; ... }` (`static/styles.css:4462-4463`) plus `.wheel-mode-btn[data-tooltip]:hover::after { content: attr(data-tooltip); position: absolute; bottom: calc(100% + 6px); left: 50%; transform: translateX(-50%); ...; pointer-events: none; }` (`static/styles.css:4486-4504`) — the tooltip text comes straight from the `data-tooltip` attribute via `attr()`, no extra state or JS needed to show/hide it, hover is pure CSS.

**What to build:** a small circular "(?)" button (visually distinct from the `wager-action-btn`s — e.g. a tiny `24px` circle, not full width) placed in `.season8-wager-panel` (`static/app.jsx:4196`, recommend top-right corner of the panel, next to the "Stake" label or as a panel-level header item rather than per-control, since the explainer covers the whole system, not one slider). Same `data-tooltip` + `::after` pattern as wheel modes, sized wider (`max-width` larger than the mode tooltip's 200px, since wager has more to explain — e.g. 280-320px) and probably anchored to expand left/below instead of centered-above, given the panel sits close to the left edge of `.casino-container` and a centered-above tooltip may clip off-screen on narrow viewports — verify against actual layout once built, don't assume the exact mode-tooltip positioning copies cleanly.

**Content guidance — write this from current actual behavior, not a verbatim copy of the spec text, since they've diverged:**

| Mechanic | Spec description (`SEASON_8_BUILD_SPEC.md:165-233`) | Actually implemented? |
|---|---|---|
| Stake slider 1×-10× | Higher stake = bigger wins and losses, multiplies both | Yes — `compute_wager_payout`/`compute_wager_loss` (`wagers.py`) |
| Hot streak +5%/win, cap +50% | Consecutive wins at the *same* stake stack a payout bonus; changing stake resets it | Yes — `compute_hot_streak_bonus`, `should_reset_streak` (`wagers.py`) |
| Safety net | 25% loss reduction at stake ≥5× | Yes — `apply_safety_net` (`wagers.py`) |
| Bank | Lock in accumulated "at risk" winnings so a future loss can't take them back | **No** — see BUG-W02 above: `wager_banked_wins` is never populated by anything, the button can never appear. Do not describe this as working in the tooltip until BUG-W02 is fixed. |
| Double-down | Re-spin at 2× stake, wagering the win you just got | Partially — implemented as "next spin's stake ×2" (`game.py:738-739`), not literally re-wagering the specific winnings amount as spec's wording implies. Close enough to describe in spirit, but don't claim it's wagering "your exact last win." |
| Insurance | Guarantee no-loss on next spin, consumes a charge | **No** — see BUG-W01 above: charges are never granted after purchase, the button can never appear. Do not describe this as working in the tooltip until BUG-W01 is fixed. |

Given Bank and Insurance are currently unreachable regardless of what the tooltip says (BUG-W01/W02), either: (a) hold this ticket until those are fixed and write the full 5-mechanic explainer, or (b) ship a tooltip now covering only the 3 mechanics that actually work (stake, hot streak, safety net) and add Bank/Insurance copy later once they're functional. Recommend (a) — a tooltip that explains a button the player can never make appear is its own confusing bug. Flagging the choice rather than deciding it.

**Acceptance criteria for whoever implements this:**
1. A small "(?)" affordance is visible on `.season8-wager-panel` at all times (not just on hover) and is clearly distinct from the action buttons.
2. Hovering it shows a tooltip, styled consistently with the existing wheel-mode tooltip (same dark background/border/font treatment), using the same `data-tooltip` + CSS `::after` mechanism — no new JS state.
3. Tooltip content accurately reflects current implemented behavior per the table above (or is held until BUG-W01/W02 are fixed, per the open question above).
4. Tooltip is positioned so it doesn't clip off-screen on mobile widths — verify visually, don't assume the wheel-mode tooltip's positioning rules transfer unchanged.
5. No changes needed to `.wheel-wrapper`'s height budget as part of this ticket — that's BUG-W03 above, a separate fix.

### T45: Wager redesign — stake becomes a real at-risk debit (v2 risk model)

- **Spec ref:** S3 (`SEASON_8_BUILD_SPEC.md:204-228`, hardened 2026-06-22)
- **Status:** [x]
- **Parallel group:** P5-wager
- **Depends on:** T06 (wager logic in `_resolve_spin()`), T08 (wager API endpoints) — this redesigns both
- **Files:**
  - wagers.py
  - game.py
  - static/app.jsx (tooltip copy in `WAGER_TOOLTIP`, T44 — must be rewritten once this ships)
  - SEASON_8_BUILD_SPEC.md (already hardened; see §3.1 for zero-escrow and §3.5 for double-down rework)

**Why:** Player feedback, 2026-06-19: *"Rather than wagering wins giving you increased losses and vice versa (since both are useful currencies) wouldn't it make more sense to actually wager the wins/losses value? So the player could potentially LOSE their wins/losses (like spending them) as opposed to just earning 10x all the time with no risk."*

**Final hardened mechanic (per spec §3):**
1. **Escrow:** `stake_wins = floor(current_wins * STAKE_RISK_PCT[stake])` debited from `wins` immediately, in the same transaction as the rest of spin resolution. Capped at `current_wins` (cannot go below 0).
2. **Win:** escrowed `stake_wins` is returned, plus `base_payout * effective_stake`. Player's gain on a win is unchanged.
3. **Loss:** escrowed `stake_wins` is **not** returned. `losses += base_loss * effective_stake`.
4. **Hot streak (T71):** bonus accrues to `wager_banked_wins`, realized on Bank. **A loss resets `wager_streak` to 0** and forfeits unbanked bonus.
5. **Safety net:** on a loss at ≥5x stake, refunds 25% of the escrowed `stake_wins` to `wins`. **Does NOT stack with insurance (T74, B2).**
6. **Bank (T72):** cannot bank while `double_down_pending` is true (returns 409). Banked wins are at risk on next spin (forfeited on loss).
7. **Double-down (T73):** escrows the actual `wager_last_win_amount` (set on each win to the `direct_wins` payout), NOT `compute_stake_risk(wins, stake * 2)`. If `wager_last_win_amount == 0`, double-down is a no-op.
8. **Insurance (T74):** dice-charge model — buy access (50K wins, requires `wager_unlock`), charges regen 1/10min, max 3, arm before spin (gamble — charge consumed on arm), clears regardless of outcome, caps loss at `effective_stake` and refunds escrow. **Does not stack with safety net.**
9. **Zero-escrow edge case (T70):** if `stake_wins == 0`, `effective_stake = 1`. Payout and loss are base only, no multiplier. Player can always spin at base outcome without risking anything.
10. **Panel visibility (T75):** wager panel always visible, but stake slider disabled/greyed when `wager_unlock` not owned. Tooltip: "Buy wager_unlock (500 wins)." Exception: inverted mode slider is fully functional without `wager_unlock`.
11. **Mode change (T76):** resets `wager_streak`, `wager_insurance_armed`, `double_down_pending`, `gravity_drift`.

**Acceptance criteria:**
1. `wagers.py` has `compute_stake_risk(current_wins, stake)` returning escrow amount.
2. `_resolve_spin()` debits the escrow before computing win/loss, returns it only on a win, atomically with spin resolution.
3. A wagered loss reduces the player's `wins` balance relative to its pre-spin value at stake > 1.
4. `apply_safety_net` refunds 25% of lost escrow to `wins`. Skipped when insurance fires.
5. **Hot streak resets to 0 on a loss** (T71). `wager_banked_wins` is forfeited.
6. **Banking returns 409 while `double_down_pending` is true** (T72).
7. **Double-down escrows `wager_last_win_amount`** (T73), not a percentage. No-op if amount is 0.
8. **Insurance uses dice-charge model** (T74): charges regen on a timer, arm consumes a charge, fires on loss only.
9. **Zero-escrow edge case handled** (T70): `effective_stake = 1` when `stake_wins == 0`.
10. **Wager panel always visible, disabled without unlock** (T75). Tooltip present.
11. **Mode change resets state** (T76): streak, armed, double_down, drift.
12. `WAGER_TOOLTIP` (T44) copy describes the v2 model accurately.
13. Insurance + safety net do NOT stack (B2).

> **Implementation + fix note (2026-06-19):** Implemented per the criteria above (`wagers.py::compute_stake_risk`/`STAKE_RISK_PCT`, escrow wired into every outcome branch of `_resolve_spin()`, `apply_safety_net` rewired to refund escrow, `WAGER_TOOLTIP` rewritten). Audited live via Playwright before trusting it (not just read the diff):
> - **Bug found and fixed:** `compute_stake_risk()` was called unconditionally regardless of `owns_wager_unlock` — every player, including those who never bought `wager_unlock`, was escrowing 2%+ of `wins` on every loss. `validate_stake()` already forces `actual_stake` to 1 for non-owners, but that alone doesn't stop the escrow from still applying at the stake-1 risk percentage. Verified live: a no-wager-items account with 1000 wins lost 20 wins on a single loss before the fix. Fixed in `game.py` by gating the escrow on `owns_wager_unlock` (zero escrow without it, matching base game behavior); re-verified live afterward — `wins_delta: 0` on a loss for the same account, only `losses` increments.
> - **Checked, not a bug:** a code-only read suggested double-down might pay out ~4x instead of 2x on a win (escrow refund stacking with payout). Verified live with an actual win → double-down → win sequence: triggering win was 1, double-down win paid exactly 2 — the escrow debit/refund nets to zero on any win, so it doesn't stack. No fix needed.
> - **Known approximation, not fixed (acceptable per the open question above):** double-down's escrow uses `effective_win_mult * stake` (a formula-based estimate of payout) rather than literally the specific win amount that triggered `double_down_pending`. They coincide when bonus_earned≈0 (verified live), but will diverge for wins padded by streak bonuses or jackpots — a double-down off a jackpot risks/pays the formula amount, not the actual jackpot winnings. Same caveat T44 already noted for v1's double-down.

---

## Phase 6: Cleanup / tech-debt (Ponytail over-engineering audit, 2026-06-20)

> **Provenance:** These tickets come from a whole-repo over-engineering audit
> (full report at `/home/user/wheel-app-staging-audit.md`). Scope is **complexity
> removal only** — every ticket here except T56 is a pure cleanup with **no
> intended player-visible behavior change**. T56 is a correctness fix the audit
> surfaced in passing.
>
> **Hard rule for all P6 tickets:** run `pytest` from `/home/user/wheel-app-staging/`
> **before and after** your change. The full suite must pass identically (minus
> any tests a ticket explicitly tells you to delete). If a "cleanup" changes a
> passing test's result, stop — it wasn't dead.
>
> **Shared-file warning — DO NOT parallelize blindly.** T46, T47, T50, T51, T52,
> T48, T56 all edit `models.py` and/or `game.py` (and `tests/test_models.py`). The
> `from models import (...)` block in `game.py:16-26` is a single multi-line
> statement that several tickets trim — concurrent edits will conflict. Execute the
> `P6-core` group **serially, in ticket-number order, with one agent.** Only the
> `P6-indep` group (T49 `wagers.py`, T53 `community_goals.py`, T54 `seasons.py`,
> T55 build files) touches disjoint files and may run in parallel with P6-core and
> each other.
>
> **Line numbers drift** as earlier P6 tickets land — always locate the target by
> *identifier*, not by the line number quoted here.

### T46: Delete frozen S6/S7 win/bonus multiplier functions

- **Spec ref:** Cleanup audit 2026-06-20 (`delete`, finding #1)
- **Status:** [x]
- **Parallel group:** P6-core
- **Depends on:** None
- **Files:**
  - models.py
  - game.py
  - tests/test_models.py
- **Why:** Season 8 froze all the old infinite upgrades (T04). `win_mult_from_level`
  and `bonus_mult_from_level` are now only ever called with the literal `0`
  (`game.py:170-171`, `base_win_mult = win_mult_from_level(0)` / `base_bonus_mult =
  bonus_mult_from_level(0)`), so they always return `1`. The entire S6/S7 piecewise
  curve in each function is dead in production — only `tests/test_models.py` exercises
  the non-zero paths. The functions are pure dead flexibility.
- **Acceptance criteria:**
  1. In `game.py::_build_spin_context`, replace `base_win_mult = win_mult_from_level(0)`
     with `base_win_mult = 1` and `base_bonus_mult = bonus_mult_from_level(0)` with
     `base_bonus_mult = 1`. Keep the surrounding `'effective_win_mult'` / `'bonus_mult'`
     dict entries computing exactly as before (they now multiply by the literal `1`).
  2. Delete the `win_mult_from_level` and `bonus_mult_from_level` function definitions
     from `models.py` (≈ lines 341-352).
  3. Remove `win_mult_from_level, bonus_mult_from_level` from the `from models import (...)`
     block in `game.py` (≈ line 18).
  4. Delete their tests from `tests/test_models.py`: the `win_mult_from_level` block and
     the `bonus_mult_from_level` block (≈ lines 115-141), and remove the two names from the
     `from models import (...)` line at the top of that test file (≈ line 12).
  5. `grep -rn "win_mult_from_level\|bonus_mult_from_level" .` (excluding `node_modules`)
     returns **zero** matches across `game.py`, `models.py`, and the tests.
  6. `pytest` passes. The staging server starts with no import error.
  7. Spin behavior is byte-for-byte unchanged: `effective_win_mult` and `bonus_mult` in
     the spin context evaluate to the same values as before for a default player
     (verify with the existing `tests/test_spin_logic.py` suite — it must pass unchanged).

### T47: Delete unused frozen proc-formula functions

- **Spec ref:** Cleanup audit 2026-06-20 (`delete`, finding #2)
- **Status:** [x]
- **Parallel group:** P6-core
- **Depends on:** T46
- **Files:**
  - models.py
  - game.py
  - tests/test_models.py
- **Why:** `jackpot_pct`, `echo_amp_pct`, and `proc_streak_mult` (`models.py`) are S7
  proc-rate curves. S8 hardcoded these rates in `_build_spin_context` (`jackpot_chance =
  0.01 + moon_bonus`, `echo_chance = 0.20 + moon_bonus`, `proc_streak_level` frozen to 0).
  All three are imported into `game.py:19` but **never called** in the body — only
  `tests/test_models.py` references them. (Note: the `jackpot_pct` *name* appears inside
  `_resolve_spin` but those are a **local variable** `jackpot_pct = mode['jackpot_pct']/100`
  and the dict key `mode['jackpot_pct']` — NOT the imported function. Do not touch the local
  var, the dict key, or `WHEEL_MODES`.)
- **Acceptance criteria:**
  1. Delete the `jackpot_pct`, `echo_amp_pct`, and `proc_streak_mult` function definitions
     from `models.py` (≈ lines 363-377).
  2. Remove `jackpot_pct, echo_amp_pct, proc_streak_mult` from the `from models import (...)`
     block in `game.py:19`. **Keep `lure_mastery_mult`** on that same line — it is still used
     (`game.py:1198`, `game.py:2105`).
  3. Delete their tests from `tests/test_models.py` (≈ lines 177-201: the `jackpot_pct`,
     `echo_amp_pct`, and `proc_streak_mult` test functions) and remove the three names from
     the test file's `from models import (...)` line (≈ line 14), keeping `lure_mastery_mult`.
  4. `_resolve_spin` still references the local `jackpot_pct` variable and `mode['jackpot_pct']`
     unchanged — confirm `_resolve_spin` is untouched except via T46.
  5. `pytest` passes; staging server imports cleanly.
  6. `grep -rn "def jackpot_pct\|def echo_amp_pct\|def proc_streak_mult" models.py` returns
     nothing; `grep -n "jackpot_pct\|echo_amp_pct\|proc_streak_mult" game.py` shows only the
     `_resolve_spin` local-variable / `mode[...]` / `_m[...]` uses, no import.

### T48: Collapse `_events_to_response` to a key projection

- **Spec ref:** Cleanup audit 2026-06-20 (`shrink`, finding #3)
- **Status:** [x]
- **Parallel group:** P6-core
- **Depends on:** T47
- **Files:**
  - game.py
- **Why:** `_events_to_response` (`game.py:467-495`) manually re-copies 21 keys that already
  exist verbatim in the `events` dict built by `_resolve_spin`. It's 28 lines of
  `'key': events['key']` boilerplate that drifts every time a key is added.
- **Acceptance criteria:**
  1. Replace the body of `_events_to_response` with a projection over an explicit key
     tuple, e.g. a module-level `_RESPONSE_KEYS = (...)` listing exactly the keys the
     current function returns, and `return {k: events[k] for k in _RESPONSE_KEYS}`.
  2. The returned dict has **exactly** the same keys as today — no more, no fewer. In
     particular it must still **omit** the 4 keys the current function drops (`segment_angle`,
     `streak`-vs not… — diff the current function against the `events` dict and preserve the
     omission set precisely).
  3. Preserve the current `.get()` defaults: `wager_streak` → 0, `stake` → 1,
     `wager_banked_wins` → 0. Since `_resolve_spin` always populates these, a plain
     `events[k]` is equivalent, but if you keep a defaulted subset, the output for a spin
     where they're present must be identical. Simplest safe form: all keys are always present
     in `events`, so `events[k]` is fine — verify by asserting the response dict for a sample
     spin equals the pre-refactor output.
  4. `spin()` and `tick()` responses are unchanged — verify the JSON payload key set is
     identical before/after (the existing `tests/test_spin_logic.py` covers resolution; add a
     one-line check or manual diff that `_events_to_response(events).keys()` matches the old
     hardcoded set).
  5. `pytest` passes.

### T49: Replace `STAKE_RISK_PCT` lookup table with arithmetic

- **Spec ref:** Cleanup audit 2026-06-20 (`shrink`, finding #4); see also **T45** (the v2 risk model that introduced this table)
- **Status:** [x]
- **Parallel group:** P6-indep
- **Depends on:** None
- **Files:**
  - wagers.py
- **Why:** `STAKE_RISK_PCT` (`wagers.py:14-25`) is a 10-row dict that spells out
  `stake * 0.02` (stake 1 → 0.02, …, stake 10 → 0.20). `compute_stake_risk` reads it as
  `STAKE_RISK_PCT.get(stake, 0.02)`.
- **Acceptance criteria:**
  1. Delete the `STAKE_RISK_PCT` dict.
  2. In `compute_stake_risk`, replace `current_wins * STAKE_RISK_PCT.get(stake, 0.02)` with
     `current_wins * 0.02 * max(MIN_STAKE, min(MAX_STAKE, stake))`. The clamp preserves the
     old behavior: the dict only had keys 1-10 and defaulted to `0.02` (the stake-1 value) for
     anything else; callers already pass a `validate_stake`-clamped 1-10, so the clamp is
     belt-and-suspenders, not new behavior.
  3. For every integer stake 1-10, `compute_stake_risk` returns the **same** escrow it did
     before (assert `floor(current_wins * 0.02 * stake)` for a sample `current_wins`, e.g.
     1000 → stake 1 = 20, stake 10 = 200). Add a small `assert`-based check or a `test_*`
     case if none exists.
  4. The double-down branch (`if double_down and expected_payout is not None`) is **unchanged**
     — it never used `STAKE_RISK_PCT`.
  5. `pytest` passes. T45's escrow behavior (gated on `owns_wager_unlock`) is unaffected.
  6. Add a one-line `# ponytail:` comment noting the linear risk curve so the intent reads as
     deliberate (`# ponytail: risk = 2% per stake level, was a 10-row table`).

### T50: Collapse the dict-of-one `INFINITE_UPGRADE_CURRENCY`

- **Spec ref:** Cleanup audit 2026-06-20 (`yagni`, finding #5)
- **Status:** [x]
- **Parallel group:** P6-core
- **Depends on:** T48
- **Files:**
  - models.py
  - game.py
- **Why:** After S8, only `clickmult_inf` survives in the infinite-upgrade system.
  `INFINITE_UPGRADE_CURRENCY` (`models.py:312-314`) is a one-entry dict mapping
  `clickmult_inf → 'wins'`, read at `game.py:1397` as `currency =
  INFINITE_UPGRADE_CURRENCY[item_id]  # always 'wins'` — the comment says it all.
- **Acceptance criteria:**
  1. At `game.py:1397`, replace `currency = INFINITE_UPGRADE_CURRENCY[item_id]` with
     `currency = 'wins'` (drop the now-redundant comment or keep a `# ponytail:` note).
  2. Delete the `INFINITE_UPGRADE_CURRENCY` dict from `models.py` and remove it from the
     `from models import (...)` block in `game.py` (≈ line 17).
  3. **Keep** `INFINITE_UPGRADES` and `inf_upgrade_cost` — `clickmult_inf` is a live upgrade
     with 5 real tiers plus an exponential tail, and `inf_upgrade_cost` still earns its keep.
     Do not touch `tests/test_models.py`'s `inf_upgrade_cost` / `INFINITE_UPGRADES` tests.
  4. `grep -rn "INFINITE_UPGRADE_CURRENCY" .` (excl. `node_modules`) returns zero matches.
  5. Buying `clickmult_inf` still debits `wins` exactly as before. `pytest` passes; server imports.

### T51: Remove dead `is_mode_available` and remaining dead `game.py` imports

- **Spec ref:** Cleanup audit 2026-06-20 (`delete`, findings #6 and #7)
- **Status:** [x]
- **Parallel group:** P6-core
- **Depends on:** T50
- **Files:**
  - wheel_modes.py
  - game.py
- **Why:** `is_mode_available` (`wheel_modes.py:86-88`) has exactly one consumer — a
  `game.py` import that never calls it — so the function is fully dead. Separately, several
  symbols are imported into `game.py` and never used in the body: `is_mode_available`,
  `get_daily_bounties`, `get_rotating_mode`, `MAX_STAKE`, `MIN_STAKE`. (If T49 landed,
  `MIN_STAKE`/`MAX_STAKE` may now be used there — but that's `wagers.py`, not `game.py`; in
  `game.py` they are unused regardless.)
- **Acceptance criteria:**
  1. Delete the `is_mode_available` function from `wheel_modes.py`.
  2. Remove `is_mode_available` from the `from wheel_modes import ...` line in `game.py:33`
     (keep `WHEEL_MODES`, `get_available_modes`, `get_week_number` — all used; `get_rotating_mode`
     is removed per criterion 3).
  3. From `game.py`, remove these unused imports: `get_rotating_mode` (wheel_modes line),
     `get_daily_bounties` (bounties line, `game.py:36`), and `MAX_STAKE, MIN_STAKE` (wagers
     line, `game.py:32`). **Verify each is genuinely unused in `game.py` first** with
     `grep -nw <name> game.py` — keep anything a prior P6 ticket or live code still references.
  4. `get_rotating_mode` and `get_daily_bounties` remain **defined** in their modules
     (`wheel_modes.py` / `bounties.py`) — they're called internally there; only the dead
     `game.py` imports are removed.
  5. `python -c "import game"` (with env set) succeeds; `ruff` (already in pre-commit) reports
     no unused-import (F401) violations in `game.py`. `pytest` passes.

### T52: Remove the unreachable `singularity` branch in `ITEM_CURRENCY`

- **Spec ref:** Cleanup audit 2026-06-20 (`delete`, finding #8)
- **Status:** [x]
- **Parallel group:** P6-core
- **Depends on:** T51
- **Files:**
  - models.py
- **Why:** The `ITEM_CURRENCY` build loop (`models.py:300-307`) branches on
  `if _id == 'singularity'`, but `singularity` was removed from the shop in S8 (it is now a
  server-wide community meter, not a purchasable item) and is **never a key in `ALL_ITEMS`**.
  The branch is unreachable; the `'fish_clicks'` currency class it assigns is dead.
- **Acceptance criteria:**
  1. Remove the `if _id == 'singularity': ITEM_CURRENCY[_id] = 'fish_clicks'` branch from the
     loop, leaving the `elif`/`else` (which become `if`/`else`) producing the same result for
     every real item.
  2. `ITEM_CURRENCY` is **identical** before and after for all keys in `ALL_ITEMS` (assert by
     building it both ways in a scratch check, or by a `test_*` that snapshots the dict).
  3. Update the explanatory comment block above the loop (`models.py:276-281`) to drop the
     now-irrelevant `'fish_clicks' — singularity only` line, since no item maps to it.
  4. `pytest` passes; no item's purchase currency changes.

### T53: Remove dead `reward_buff` data from community-goal defs

- **Spec ref:** Cleanup audit 2026-06-20 (`delete`, finding #9)
- **Status:** [x]
- **Parallel group:** P6-indep
- **Depends on:** None
- **Files:**
  - community_goals.py
- **Why:** Every entry in `COMMUNITY_GOAL_DEFS` carries `'reward_buff': 0.05`
  (`community_goals.py:20,30,40,50,60`), but it is **never read** anywhere. On goal
  completion the buff is hardcoded (`check_goal_completion` sets `win_chance_pct = 55.0`).
  Dead data masquerading as config.
- **Acceptance criteria:**
  1. Remove the `'reward_buff': 0.05` key (and its inline `# +5% win% for a week` comment)
     from all five goal defs.
  2. `grep -rn "reward_buff" .` (excl. `node_modules`) returns zero matches.
  3. `check_goal_completion` still sets `win_chance_pct = 55.0` on completion — unchanged.
  4. `pytest` passes. Goal completion and reward distribution behavior is unchanged.

### T54: Merge `advance_season` into `_perform_rollover` (optional, low priority)

- **Spec ref:** Cleanup audit 2026-06-20 (`yagni`, finding #10)
- **Status:** [x]
- **Parallel group:** P6-indep
- **Depends on:** None
- **Files:**
  - seasons.py
  - tests/test_spin_logic.py (only if the stub at line 54 needs the name kept)
- **Why:** `advance_season` (`seasons.py:35-52`) does a `SELECT … FOR UPDATE` then immediately
  delegates to `_perform_rollover`, its **only** caller. Two functions, one path.
- **CAUTION — this touches the once-per-week season-rollover transaction**, the single most
  destructive path in the app (it resets every player's `game_state`). The audit rates this the
  **lowest-value, highest-risk** P6 item. Recommended approach: keep the **public name**
  `advance_season` (it's the entrypoint called at `game.py:2500` and stubbed in
  `tests/test_spin_logic.py:54`) and fold the `_perform_rollover` body into it, deleting the
  private function — rather than the reverse. Do not change the `SELECT … FOR UPDATE` locking,
  the `SET LOCAL synchronous_commit = on` flush, or the commit semantics. If in any doubt,
  **skip this ticket** — the duplication is 6 lines and harmless.
- **Acceptance criteria:**
  1. `seasons.py` exposes a single `advance_season(conn)` that performs the `FOR UPDATE` fetch,
     the `None`-row guard, and the full rollover, committing internally exactly as today.
  2. `_perform_rollover` is removed; no other module imported it (verify with grep).
  3. `game.py:2500`'s call site (`advance_season(conn)`) is unchanged.
  4. The `FOR UPDATE` lock, the top-3 snapshot, `user_season_history` insert, `game_state`
     reset, `community_pot` reset, `seasons` bump, and the `synchronous_commit = on` flush all
     execute in the same order and the same single transaction as before.
  5. `pytest` passes. If you cannot prove behavioral equivalence by reading the diff, mark this
     `[!]` blocked and leave it for a human — do not guess on the rollover path.

### T55: (Decision) Stop committing the generated `static/app.js`

- **Spec ref:** Cleanup audit 2026-06-20 (`yagni`, finding #12 — build hygiene, OPTIONAL)
- **Status:** [x] won't do, intentional — see decision note below
- **Parallel group:** P6-indep
- **Depends on:** None
- **Files:**
  - .gitignore
  - .pre-commit-config.yaml
  - deploy.sh (read only — confirm it builds)
  - static/app.js (would be removed from version control, not from disk)
- **Why:** `static/app.js` (7,766 generated lines) is committed **and** guarded by the
  `no-compiled-js-divergence` pre-commit hook (`.pre-commit-config.yaml:28-35`) that fails if
  `app.jsx` is newer than `app.js` — yet `deploy.sh:61-62` already runs `make build` on every
  deploy. The committed artifact plus the staleness hook are belt-and-suspenders for a file the
  deploy regenerates anyway.
- **This is a DECISION ticket, not a mechanical one. Do not just delete the file.** There is a
  real tradeoff:
  - **Keep committing it** if anything serves the app straight from a git checkout without
    running `make build` first (e.g. a bare `gunicorn` on a freshly-pulled tree, or the
    `staging` Makefile target which does **not** build). In that case the current setup is
    correct and this ticket should be closed `[x]` as "won't do, intentional."
  - **Gitignore it** only if every serve path (local dev, staging, prod) is guaranteed to run
    `make build` first. Then: add `static/app.js` to `.gitignore`, `git rm --cached
    static/app.js`, delete the `no-compiled-js-divergence` local hook, and add a build step to
    the `staging`/`dev` Makefile targets so a fresh checkout can't serve stale/missing JS.
- **Acceptance criteria:**
  1. Confirm which serve paths build vs. don't (check `Makefile` `staging`/`staging-dev`/`dev`
     targets and `deploy.sh`). Document the finding in the ticket.
  2. If keeping: close as intentional with a one-line rationale; no code change.
  3. If removing: `.gitignore` excludes `static/app.js`, it is `git rm --cached`'d, the
     pre-commit staleness hook is deleted, and every serve target builds first. A fresh
     `git clone` + documented serve command renders the app with no manual `make build`.

> **Decision note (2026-06-20):** Investigated `Makefile` and `deploy.sh`. `staging` (`gunicorn -c
> gunicorn.conf.py server:app`) and `staging-dev` (`python server.py`) — the two targets actually
> used to run this environment — go straight to the server with no `make build`/babel step.
> `dev` is the same. Only `deploy.sh` (production promotion path) runs `make build`, and even
> there it's escapable via `--skip-build`. Since not every serve path builds first, the committed
> `static/app.js` is load-bearing (a fresh checkout + `make staging-dev` would serve stale/missing
> JS without it) and the `no-compiled-js-divergence` pre-commit hook is doing real work, not
> redundant. **Decision: keep committing it — won't do, intentional. No code changes made.**

> **Follow-on finding from T52 (2026-06-20), not fixed — out of scope:** `game.py`'s `/api/buy`
> handler (≈ line 1520) has `else:  # fish_clicks — singularity only` inside its currency-balance
> check, handling a `currency == 'fish_clicks'` case. Since `ITEM_CURRENCY` (after T52) only ever
> produces `'wins'` or `'losses'`, this `else` branch is now also unreachable — same disease as
> T52, different file. Harmless (defensive dead code, not a bug), flagged for a future cleanup
> ticket rather than fixed here since T52 was scoped to `models.py` only.

### T56: (Correctness — not over-engineering) `class_star` missing from `SHOP_ITEMS`

- **Spec ref:** Cleanup audit 2026-06-20 ("Out of scope" note — routed to correctness review)
- **Status:** [x]
- **Parallel group:** P6-core
- **Depends on:** T52
- **Files:**
  - models.py
  - static/app.jsx (verify only)
  - game.py (verify only)
- **Why:** `class_star` is offered for purchase in the frontend (`static/app.jsx:2326`, cost
  10,000,000, tier 3) and is fully wired server-side (`CLASS_MAP` and `CLASS_STAR_WIN_BONUS`
  in `game.py`; listed in `UPGRADE_TIER_3` and `_FUNCTIONAL_SHOP_ITEMS` in `models.py`) — but
  it is **absent from the `SHOP_ITEMS` dict** (only `class_earth` and `class_moon` are present,
  `models.py:193-194`). A buy request for `class_star` would not resolve against `ALL_ITEMS`,
  so the purchase path is broken. This is a real bug, included here only because the audit
  surfaced it — treat it as correctness, not cleanup.
- **Acceptance criteria:**
  1. First **confirm the bug**: trace `/api/buy` (`game.py:1384`) for `item_id='class_star'`
     and verify it fails (e.g. `KeyError`/"unknown item"/cost lookup miss) because `class_star`
     is not in `SHOP_ITEMS`/`ALL_ITEMS`. Document the exact failure mode in the ticket before
     fixing.
  2. Add `'class_star': {'cost': 10_000_000, 'requires': None}` to `SHOP_ITEMS` alongside
     `class_earth`/`class_moon` (`models.py`), matching the frontend's advertised cost/tier.
  3. Verify the frontend cost (`app.jsx:2326`, 10,000,000) and tier (3) now agree with
     `SHOP_ITEMS` + `item_tier` (it's already in `UPGRADE_TIER_3`, so `item_tier('class_star')`
     returns 3 — confirm).
  4. Buying `class_star` with sufficient `wins` succeeds end-to-end: it debits the correct
     currency (it's in `_FUNCTIONAL_SHOP_ITEMS` → `'wins'`), is added to `owned_items`, and can
     then be equipped via `/api/equip-class` (`CLASS_MAP` already maps it to `'star'`).
  5. `CLASS_STAR_WIN_BONUS` (+20% win payout while the star class is equipped) takes effect
     after purchase+equip — verify in `_build_spin_context` (`star_win_bonus`).
  6. `pytest` passes. If the intended design was actually to **retire** `class_star` (not sell
     it), flag that instead and remove the frontend offer + the dead `CLASS_STAR_*` wiring —
     but do not leave it half-wired.

> **Fix note (2026-06-20):** Confirmed the exact failure mode before fixing: `/api/buy` (`game.py`,
> `if item_id not in ALL_ITEMS: return jsonify({'error': 'Unknown item'}), 400`) rejected every
> `class_star` purchase with 400, since `ALL_ITEMS = {**FISH_SKINS, **SHOP_ITEMS}` and
> `class_star` was in neither. Searched for any "deprecated"/"retired"/"removed" comment near the
> class items — found none (the only nearby "removed" comment is about `singularity`, unrelated).
> Confirmed an oversight, not an intentional retirement. Fixed by adding
> `'class_star': {'cost': 10_000_000, 'requires': None}` to `SHOP_ITEMS` (`models.py`), one line,
> alongside `class_earth`/`class_moon`. Verified: `class_star in ALL_ITEMS` → True, cost
> 10,000,000, `ITEM_CURRENCY['class_star']` → `'wins'`, `item_tier('class_star')` → 3 — full chain
> (`/api/equip-class`'s `CLASS_MAP`, `_build_spin_context`'s `CLASS_STAR_WIN_BONUS` +20% win-bonus
> logic) was already correctly wired and needed no other changes. `pytest`: 44 passed, unchanged.

### T57: (Correctness) Win Power / Bonus Power had zero gameplay effect

- **Spec ref:** Found during a README/patch-notes accuracy pass (2026-06-21), not part of the
  original cleanup audit.
- **Status:** [x]
- **Parallel group:** none — handled directly by the main agent (operator-approved before fixing)
- **Files:**
  - game.py
  - tests/test_spin_logic.py
- **Why:** `_build_spin_context()` in `game.py` had:
  ```python
  base_win_mult = 1    # always 1 (levels frozen)
  base_bonus_mult = 1  # always 1
  ```
  hardcoded regardless of which `winmult_1`...`winmult_7` (up to 200,000 wins, advertised
  ×2→×128) or `bonusmult_1`...`bonusmult_6` (up to 80,000 wins, advertised ×2→×70) items the
  player owned — `effective_win_mult`/`bonus_mult` never read `owned_items` for these keys
  anywhere in the spin-resolution path. Buying either upgrade line drained wins for no effect.
  Predates this session — T46 (Phase 6) only replaced an already-hardcoded
  `win_mult_from_level(0)` call with the literal `1`, a faithful no-op; the actual regression
  was introduced earlier in the Season 8 build when `_build_spin_context` was rewritten for
  prestige/wager and the win/bonus-power lookup was never wired back in.
- **Fix:** Added `_winmult_level(owned)` / `_bonusmult_level(owned)` (same highest-owned-tier
  pattern as the existing `_lure_level`/`_autofisher_level` helpers) and a `_BONUS_MULT_TABLE =
  [1, 2, 4, 8, 15, 35, 70]` constant (the exact table from the deleted `bonus_mult_from_level`,
  recovered via `git show` on the pre-T46 commit). `base_win_mult = 1 << _winmult_level(owned)`,
  `base_bonus_mult = _BONUS_MULT_TABLE[_bonusmult_level(owned)]`. No infinite tail — matches the
  Season 8 removal of `winmult_inf`/`bonusmult_inf` (these are now flat, capped shop items).
- **Verification:** Added 5 regression tests to `tests/test_spin_logic.py` exercising
  `_build_spin_context` directly at level 0 / mid / max for both axes (level 7 → ×128, level 6 →
  ×70). `pytest`: 49 passed (44 existing + 5 new). `python3 -c "import game"` clean. Staging
  restarted and confirmed active (HTTP 200) with the fix live. Committed `defaded`, pushed.

### T58: (Correctness) Aquarium species never tracked; `/api/fish-to-wager` crashed and was exploitable

- **Spec ref:** Found during the same README/patch-notes accuracy pass as T57 (2026-06-21).
- **Status:** [x]
- **Parallel group:** none — handled directly by the main agent (operator-approved before fixing)
- **Files:**
  - game.py
  - static/app.jsx (+ rebuilt static/app.js)
- **Why (two separate bugs in the Season 8 fishing-integration code, spec S6):**
  1. **Dead Aquarium tracking.** `aquarium_species` (DB column) was read in `_build_spin_context`
     (wheel-luck bonus), `/api/state`, and `/api/aquarium`, but never written anywhere — no catch
     endpoint (`reel()`, `auto-fish-tick`) ever appended to it. The Aquarium panel permanently
     showed 0 species and the +0.1%/species wheel-luck bonus was permanently 0%, regardless of
     how many fish a player actually caught.
  2. **`/api/fish-to-wager` crashed, and the underlying design was exploitable.** It compared
     `FISH_CATALOG`'s string tier (`'Common'`, `'Legendary'`, etc.) against an int
     (`if tier >= len(FISH_TO_WAGER_RATES)`) — a `TypeError` on every call. Worse: it validated
     `fish_id` against the **permanent** `caught_species` Encyclopaedia list with nothing
     consumed on use, so once the type error was fixed, a player could call it repeatedly for
     any species ever caught to mint unlimited `wager_tokens`. It also referenced a column
     (`last_fish_conversion_date`) that doesn't exist anywhere in the schema — the real column
     from migration `042_catch_of_the_day.sql` is `catch_of_the_day_date`. The correct,
     already-working implementation of this exact mechanic exists separately in `reel()`
     (`game.py` ~1980-1993): it auto-awards `wager_tokens` at catch time with a correct
     `tier_map` and the correct column name. The frontend's `handleFishToWager` called the
     broken endpoint but was never wired to any button — unreachable through normal play.
- **Fix:**
  1. Aquarium: pointed all 4 read sites (`_build_spin_context`, `/api/state`, `/api/aquarium`×2)
     at `caught_species` instead of the dead `aquarium_species` column — it already tracks the
     identical "unique species ever caught" fact correctly. No migration needed (`caught_species`
     was already selected by `_load_game_state`).
  2. Fish-to-wager: deleted the `/api/fish-to-wager` endpoint and the dead `handleFishToWager`
     frontend handler entirely, rather than building the missing "pending catch queue" the
     original spec implied — the real awarding logic in `reel()` already does this job
     correctly and was untouched.
- **Verification:** `pytest`: 49 passed (unchanged from T57). `python3 -c "import game"` clean.
  JSX rebuilt (`npx babel static/app.jsx ... -o static/app.js`), no errors. Staging restarted,
  confirmed active (HTTP 200). Committed `d9f9df4`, pushed.

### T59: (Critical security) Build Loadouts let any player grant themselves every item for free

- **Spec ref:** Found during the same accuracy pass as T57/T58 (2026-06-21). Severity: critical —
  flagged to the operator with explicit urgency before touching anything.
- **Status:** [x]
- **Parallel group:** none — fixed immediately, operator-approved, ahead of all other work
  (including the documentation task this pass was originally for)
- **Files:**
  - game.py
  - static/app.jsx (+ rebuilt static/app.js)
- **Why:** `save_loadout()` (`POST /api/loadout`) stored whatever JSON the client sent verbatim
  in `build_loadouts`, no validation. `apply_loadout()` (`POST /api/loadout/apply`) then wrote
  `loadout.get('owned_items', [])` / `loadout.get('active_cosmetics', [])` **directly to
  `game_state`** with no ownership/cost check of any kind. The normal UI (a live "⚙️ Loadouts"
  panel, Save/Equip buttons) only ever round-trips the player's real current state, so clicking
  through the UI is harmless — but any logged-in player sending `POST /api/loadout` directly
  (devtools, curl with their session cookie — no special tooling) with a fabricated
  `owned_items` list containing every item ID in the game, followed by `POST
  /api/loadout/apply`, would receive the entire shop catalogue for free, completely bypassing
  the win/loss currency system. Root cause: the original design (spec S11) only ever specified
  `equipped_class` + `active_wheel_mode` in a loadout — `owned_items`/`active_cosmetics` were
  never supposed to be there.
- **Second bug found while fixing the first:** every query referenced a column `loadout_data`
  that has **never existed** — the real `build_loadouts` column (confirmed via `\d
  build_loadouts`) is `config`, and `slot` is constrained `1-3` by a `CHECK` constraint, not
  `1-5` as the Python code assumed. Every call to `save_loadout`/`get_loadout`/`apply_loadout`
  has always raised a DB error — confirmed via `SELECT count(*) FROM build_loadouts` → `0` rows,
  ever, on the live staging DB. This is also *why* the critical bug above was never actually
  exploited by a real player: the save path has never once succeeded.
- **Fix:**
  1. `save_loadout`: whitelists the stored payload to exactly `{equipped_class,
     active_wheel_mode}` regardless of what else is in the request body; corrected column name
     (`config`) and slot range (`1-3`, matching both the DB constraint and the existing 3-slot
     frontend UI — no DB/UI change needed there).
  2. `apply_loadout`: re-validates server-side before applying anything — `equipped_class` must
     be `null` or a class the player actually owns (`_LOADOUT_CLASS_ITEMS` lookup against
     `owned_items`, same check as `/api/equip-class`); `active_wheel_mode` must be `'steady'` or
     in `get_available_modes()` for the current week (same check as `/api/wheel-mode`).
     Anything that fails validation falls back to the player's current value instead of
     erroring, so a loadout saved under one week's rotation degrades gracefully in another.
     Corrected column name (`config`).
  3. `static/app.jsx`: `handleLoadoutSave` now sends `{equipped_class, active_wheel_mode}`
     (reading the existing `equippedClass`/`activeWheelMode` state) instead of
     `{owned_items, active_cosmetics}`; `handleLoadoutApply` reads `data.equipped_class` /
     `data.active_wheel_mode` from the response instead of the old `owned_items` shape.
- **Verification:** `pytest`: 49 passed (unchanged). `import game` clean, JSX rebuilt cleanly.
  End-to-end smoke test against the live staging DB (logged in as `claudeagent`): saved a
  loadout containing every functional item plus an unowned class
  (`{"equipped_class":"earth","active_wheel_mode":"volatile","owned_items":[...every item...]}`)
  — confirmed `GET /api/loadout` returned only `{equipped_class, active_wheel_mode}`, confirmed
  `POST /api/loadout/apply` left `owned_items` completely unchanged (`['wager_unlock']` before
  and after) and correctly fell back `equipped_class` to `null` (class not owned) while still
  applying `active_wheel_mode: 'volatile'` (always available, no ownership needed). Test
  artifacts cleaned up afterward (wheel mode reset to steady, test loadout row deleted).
  Staging restarted, confirmed active (HTTP 200) with the fix live before the smoke test ran.
  Committed `d714244`, pushed.

### T60-T62: Bounty claim idempotency (critical), bounty_streak10 wrong field, singularity contribute missing debit+cap

- **Spec ref:** Found by a 4-way parallel fork audit of bounties.py, community_goals.py,
  wagers.py endpoints, replays.py/chat.py, and legacy-boards/onboarding/singularity (2026-06-21),
  commissioned after T57-T59 turned up a critical exploit from documentation fact-checking alone.
- **Status:** [x]
- **Files:** game.py, models.py, static/app.jsx (+ app.js), migrations/044, migrations/045.
- **T60 (critical):** `/api/bounties/claim` had no claim-tracking — callable repeatedly forever,
  granting up to 500 `wager_tokens` + 1 cosmetic fragment on every call. Added
  `bounty_claimed_date` (migration 044, mirrors `catch_of_the_day_date`); checked/set in
  `claim_bounty()`.
- **T61 (high):** `bounty_streak10` checked `wager_streak` (never resets on a loss at the default
  1x stake) instead of the real win streak — permanently uncompletable after a player's first
  day. Switched to `events['streak'] == 10`, `amount=10` (one-shot completion).
- **T62 (high):** `/api/singularity/contribute` validated against `wins` but debited nothing
  (not wins, not fish_clicks) and enforced no per-player cap — any player could solo-fill the
  100M server-wide meter for free. The frontend already correctly treated it as a fish_clicks
  spend (`// spec S13: deducts fish_clicks, not wins`) — backend never matched. Added
  `singularity_contributions` (migration 045, keyed by `fill_count` so the cap resets each
  fill cycle), `SINGULARITY_PER_PLAYER_CAP = 25_000_000`, real debit, clamped to
  `min(requested, balance, remaining_cap)`, returns actual amount so the frontend doesn't
  over-decrement its display cache.
- **Verification:** `pytest`: 49 passed (unchanged). End-to-end against the live staging DB:
  confirmed repeat bounty claims rejected same-day; confirmed singularity contribute clamps to
  balance and to the per-player cap, rejects once capped. Committed `e399b68`, pushed.

### T63: Wager Insurance was a dead mechanic (charge spent for zero effect)

- **Spec ref:** S3.6 (insurance rework — dice-charge model, hardened 2026-06-22)
- **Status:** [x] — implemented per v1 (armed-flag pattern), but spec §3.6 hardens it further
- **Files:** game.py, seasons.py, tests/test_spin_logic.py, migrations/046, migrations/047 (T69).
- **Why:** `/api/wager/insurance` consumed a charge but nothing in the spin path ever read
  `wager_insurance_charges` — buying the 50,000-win item and activating it did nothing.
- **v1 fix:** Added `wager_insurance_armed` (migration 046), same pending-flag pattern as
  `double_down_pending`. Armed on activation, read in `spin()`, passed into `_resolve_spin` as
  `insurance_active`, cleared unconditionally after the spin (consumed regardless of outcome).
  On a loss with insurance active: loss capped at the stake amount, escrowed stake fully
  refunded.
- **Hardened per spec §3.6 (T74):** Insurance must follow the **dice-charge model**:
  - Buy `wager_insurance` (50K wins, requires `wager_unlock`) for access; cap 3 charges.
  - Charges regen 1 per 10 minutes (`WAGER_INSURANCE_RECHARGE_SECONDS = 600`, same as `DICE_RECHARGE_SECONDS`).
  - Cap at `WAGER_INSURANCE_MAX_CHARGES = 3`. Timer pauses at cap.
  - Invoke regen at the same read sites as dice: `/api/state`, spin path, `/api/wager/insurance`.
  - **Arming consumes a charge immediately** (decrements charges, resets `wager_insurance_last_recharge` to NOW if charges < max). This is a gamble — charge wasted on a win.
  - **Safety net does NOT stack with insurance** (B2): when insurance fires, skip safety net refund entirely.
  - On a win: charge wasted (no effect).
  - New column: `wager_insurance_last_recharge TIMESTAMPTZ NOT NULL DEFAULT NOW()` (migration 047).
  - Helper: `_recharge_wager_insurance(charges, last_recharge, max_charges, now_utc)`.
  - In inverted mode: insurance caps the "win" outcome (bad) and refunds the staked losses.
  - Reset on prestige (T85) and season rollover (T02).
- **Verification:** 2 new regression tests (capped+refunded vs. uncapped baseline). `pytest`: 51
  passed. End-to-end against live staging DB: armed insurance, spun until a loss landed,
  confirmed `insurance_used=true`, loss capped at stake, wins unchanged (escrow refunded).
  Committed `87b9cea`, pushed.

### T64: Double-down risk/reward asymmetry fixed; stake-ceiling clamp finding investigated and left as-is

- **Status:** [x]
- **Files:** game.py, wagers.py.
- **Real bug fixed:** `compute_stake_risk()` escrowed `effective_win_mult * stake` for
  double-down spins instead of the normal `current_wins * 0.02 * stake` — risked less than an
  equivalent-stake normal spin while paying out exactly the same. Removed the special case
  entirely; double-down now uses the identical formula as any other spin, just forced to 2x
  stake. Removed the now-unused `double_down` param from `_resolve_spin`.
- **Second finding, investigated, not changed:** the audit also flagged that doubling gets
  silently clamped to no added effect at base stake ≥5 (10→20→clamped back to 10). Proved
  mathematically that `clamp(base*2, 1, 10)` and `clamp(base, 1, 5)*2` are identical for every
  integer 1-10 — no reordering fixes this. It's an inherent consequence of the system-wide
  `MAX_STAKE=10` ceiling (also respected by `validate_stake`, the risk-label UI's
  Safe/Bold/Reckless 1-10 range). Raising it specifically for double-down would require
  threading a new ceiling through multiple independently-clamping functions plus a UI
  redesign — a bigger product decision than this fix should make unilaterally. Documented in
  a code comment and flagged here rather than shipping a no-op "fix."
- **Verification:** `pytest`: 51 passed (unchanged). `wagers.py` self-check passes. Verified
  live: double-down at stake=10 resolves correctly, normal spins unaffected. Committed
  `374653e`, pushed.

### T65: `goal_wager100k` gated on actual stake, not any win

- **Status:** [x]. Gated on `events['stake'] > 1` instead of firing on every winning spin
  regardless of stake. `pytest`: 51 passed. Committed `c48f0fc`, pushed.

### T66: HMAC-sign replay strings (closes a forgery vector before it's ever wired to chat)

- **Status:** [x]. `generate_replay`/`decode_replay` had no integrity check — any client could
  hand-craft a fake jackpot replay indistinguishable from a real one. Not exploitable today
  (replay sharing is dead: no frontend caller, nothing posts a decoded replay to chat), but
  cheap to fix now vs. expensive once real chat messages reference unsigned strings. Added an
  HMAC-SHA256 signature (`replays.py`, keyed on `WHEEL_SECRET_KEY`), verified via
  `hmac.compare_digest` before `decode_replay` returns anything. New `tests/test_replays.py` (5
  tests). `pytest`: 56 passed. Verified live: a hand-forged replay POSTed to
  `/api/replay/share` correctly 400s. Committed `4d994a7`, pushed.

### T67: Chat system messages had no rate limit and weren't trimmed

- **Status:** [x]. Spec S17 claimed a "max 1 per 30s per event type" throttle that didn't exist
  in code. Added a per-worker, in-memory throttle keyed by a new `event_kind` param (6 call
  sites each given a distinct kind, so unrelated event types throttle independently). Also
  fixed the adjacent finding that `post_system_message` never trimmed `chat_messages` the way
  `post_chat` does — added the same trim. New `tests/test_chat.py` (4 tests). `pytest`: 60
  passed. Committed `60f306d`, pushed.

### T68: Closed a per-player cap race window in `increment_goal`

- **Status:** [x]. The SELECT-then-clamp in `increment_goal()` wasn't row-locked — two
  concurrent requests near a player's cap could each read the same stale value and together
  exceed the cap. Added `SELECT ... FOR UPDATE` (after an `ON CONFLICT DO NOTHING` upsert to
  guarantee the row exists first). `pytest`: 60 passed (unchanged). Verified live:
  `/api/community-goal` and `/api/bounties` both still respond correctly. Committed `5744084`,
  pushed.

### Decision: onboarding's GET-mutation finding — flagged, not changed

The 4-way audit also flagged that `GET /api/bounties` mutates state (advances `onboarding_step`
3→4, grants 100 `wager_tokens`) inside what's nominally a read-only GET handler — non-idiomatic
REST, but the fork explicitly confirmed it's **already correctly idempotent** (row-locked,
gated on `onboarding_step == 3`) and **not exploitable**. Converting it to a separate POST
(e.g. `POST /api/bounties/viewed`, fired when the bounty panel actually opens) would need a new
endpoint plus a frontend wiring change, and risks shifting exactly when this onboarding step
fires relative to today's "the bounty status GET happened" trigger. Given it's a pure style
nitpick with zero functional bug, left as-is rather than risking a UX-timing regression for no
behavioral benefit.

## Correctness sweep summary (T57-T68), 2026-06-21

Triggered by documentation fact-checking turning up a hardcoded-multiplier bug (T57), which
prompted 4 parallel fork audits of every remaining Season 8 system. Total: 12 real issues found,
all fixed (one — the stake-ceiling clamp inside T64 — investigated and confirmed not
independently fixable without a bigger redesign; documented rather than papered over).
Severity breakdown: 1 critical (T59 loadout exploit), 1 critical (T60 bounty-claim farming), 5
high (T57 win/bonus power, T58 aquarium+fish-to-wager, T61 bounty_streak10, T62 singularity,
T63 wager insurance), 4 medium (T64 double-down asymmetry, T65 goal_wager100k, T66 replay
signing, T67 chat throttle), 1 low (T68 cap race). 60/60 tests passing (up from 44 at the start
of this sweep — 16 new regression tests added). Every fix verified end-to-end against the live
staging DB, not just unit tests, given the economic/security stakes. All committed and pushed
to `origin/staging` individually (commits `defaded` through `5744084`).

### Flagged, not fixed: Protection rework (spec S7) — `guard_charges` system is dead scaffolding

Found while fact-checking the README's Protection section (2026-06-21), outside the scope of
the 4 audit forks above. `/api/guard` decrements `guard_charges` on call, but nothing in
`_resolve_spin`/`_build_spin_context` ever reads `guard_charges` — calling it has zero effect,
the exact same bug class as T63 (Wager Insurance) before it was fixed. `guard_last_regen_spin`
is selected but never written anywhere either (the spec's "regen_shield regenerates 1 guard
charge every 50 spins" never happens). The `guard_charge` shop upgrade (+1 charge, 10,000 wins)
has no purchase-time effect either, since nothing ever reads the counter it would increment.

Unlike T63, this isn't a clean "wire up the dead thing" fix: **the old, pre-Season-8 mechanic
is still fully live and is what's actually protecting players today** —
`_resolve_spin`'s loss branch auto-blocks via a plain `'guard' in owned` check (100% block,
single-use, item removed from `owned_items` on trigger) and `regen_shield` via
`regen_recharge_wins` (auto-blocks, recharges after 5 wins) — the exact mechanic spec S7
explicitly says should be "removed entirely" in favor of the new manual-trigger charge system.
Replacing it would change live behavior for every current Guard/Regen Shield owner (passive
protection → must manually re-arm before every spin); wiring the new system in *parallel*
without removing the old one would let players double-stack two independent protections from
the same items.

**Operator decision (2026-06-21): leave the code as-is.** Document Guard/Regen Shield as they
actually behave (passive auto-block, the live mechanic), not as the spec'd manual-charge system.
`guard_charges`, `guard_charge`, `guard_last_regen_spin`, and `/api/guard` are non-functional
scaffolding — flagged here for a future decision, not referenced in player-facing docs.

## Documentation task complete — README.md + PATCH_NOTES.md updated, 2026-06-21

The original ask for this session ("update the user-facing documentation on the staging
branch") is done, after the T57-T68 correctness sweep above turned out to be a prerequisite —
it's hard to accurately document systems that don't do what they claim to.

`README.md`: removed sections describing retired mechanics (Spin/Auto Speed, Click Power/
Frenzy); rewrote Win/Bonus Power, Protection, and Special Upgrades to match actual live
behavior (not the aspirational spec); added full sections for Wager System, Wheel Modes,
Prestige, Daily Bounties, Community Goals, Singularity Meter, Aquarium, Build Loadouts, Chat,
and Hall of Fame; added 5 missing fish skins and 5 new wheel themes; rewrote the API reference
with ~20 previously-undocumented endpoints. Explicitly noted three known-incomplete spots
rather than glossing over them: Wager Tokens/Cosmetic Fragments have no spend yet, `/api/guard`
has no effect (flagged above), and replay sharing has no chat hookup yet.

`PATCH_NOTES.md`: new entry "High Stakes — 21 Jun 2026" — deliberately **not** labeled as a new
season (the season counter is still 7 in the DB; rollover is an explicit, separate,
operator-triggered action per `SEASON_8_BUILD_SPEC.md`'s own rollout-sequence section). Covers
every new system in player-facing language, plus a short, appropriately-discreet "Fixes"
section covering the T57-T68 corrections without exposing exploit mechanics in detail.

Both files committed and pushed (`ccd3530`). Staging restarted and confirmed active
afterward (HTTP 200, 60/60 tests passing) — though neither file affects runtime behavior, this
was a final sanity check after the session's cumulative changes.

---

# Phase 7: Spec Hardening (2026-06-22)

> **Provenance:** Tickets T69–T96 cover the spec hardening pass that resolved
> all open spec gaps. They include the 21 bugs (B1–B21) catalogued in
> `SEASON_8_BUILD_SPEC.md` §23 and the new features added during the hardening
> pass. Each ticket is self-contained with file paths, acceptance criteria,
> and a spec reference.
>
> **T69–T75 are the wager system hardening tickets** — these bring the
> wager implementation in line with the final spec §3 (zero-escrow, double-
> down rework, insurance rework, panel visibility, mode-change resets).
> **T76–T80 are the wheel mode hardening tickets** — gravity/mirror/inverted
> full mechanics, dynamic wheel graphic.
> **T81–T84 are the chat and auto-post tickets** — 200-message history with
> cursor pagination, auto-post messages with configurable triggers, per-
> player escalating big-win threshold, community goal milestones.
> **T85–T88 are the prestige and onboarding hardening tickets** — prestige
> scope update, prestige_efficiency as win retention, onboarding step 5
> transition, onboarding rollover preservation.
> **T89–T96 are the bug audit and minor fix tickets** — replay system
> removal, auto-post in auto-spin path, remove bounty chat message, chat
> rate limit/trim, race fix, auto-spin budget guard, manual spin button,
> wheel-wrapper height re-tune.

## Migration

### T69: Migration 047 — hardening columns

- **Spec ref:** S19 (migration list)
- **Status:** [x] (2026-06-22) — migration applied, 8 columns added, 60→75 tests pass
- **Parallel group:** P7-migration
- **Depends on:** T01
- **Files:**
  - migrations/047_hardening.sql
- **Acceptance criteria:**
  1. Adds columns to game_state:
     - `wager_last_win_amount INTEGER NOT NULL DEFAULT 0` — for double-down escrow (T73)
     - `wager_banked_losses INTEGER NOT NULL DEFAULT 0` — for inverted mode hot-streak banking (T79)
     - `wager_insurance_last_recharge TIMESTAMPTZ NOT NULL DEFAULT NOW()` — for insurance regen (T74)
     - `gravity_drift INTEGER NOT NULL DEFAULT 0` — for gravity mode (T77)
     - `biggest_win_announced INTEGER NOT NULL DEFAULT 0` — for per-player escalating threshold (T83)
  2. Optionally also add `milestone_25/50/75` to `community_goals` here if not in migration 037.
  3. All ALTER statements use IF NOT EXISTS.
  4. `python migrate.py` applies without error.
  5. `python migrate.py --status` shows 047 as applied.

## Wager system hardening

### T70: Zero-escrow edge case (effective_stake = 1 when stake_wins == 0)

- **Spec ref:** S3.1 (zero-escrow)
- **Status:** [x] (2026-06-22) — `effective_stake` computed and used in 6 call sites, 3 tests
- **Parallel group:** P7-wager
- **Depends on:** T06
- **Files:**
  - game.py
  - wagers.py
- **Acceptance criteria:**
  1. In `_resolve_spin()`, compute `effective_stake = stake if stake_wins > 0 else 1`.
  2. Use `effective_stake` for payout and loss multiplication.
  3. If `stake_wins == 0` (wins == 0 or percentage floors to 0): payout = `base_payout` only, loss = `base_loss` only.
  4. Player without `wager_unlock` is always in this state (stake forced to 1, escrow = 0).
  5. The player can always spin at base outcome without risking anything — verified by spinning with 0 wins.
  6. `pytest` passes; no regression to existing tests.

### T71: Hot streak resets to 0 on loss (B1)

- **Spec ref:** S3 (hot-streak), B1
- **Status:** [x] (2026-06-22) — `wager_streak`/`wager_banked_wins`/`wager_last_win_amount` reset on loss, 3 tests
- **Parallel group:** P7-wager
- **Depends on:** T06
- **Files:**
  - game.py
- **Acceptance criteria:**
  1. In the loss path of `_resolve_spin()` (currently `game.py:319-354`), add `wager_streak = 0`.
  2. `wager_banked_wins` is also reset to 0 on a loss (forfeited).
  3. `wager_last_win_amount` is reset to 0 on a loss.
  4. **Test:** spin 3 wins at stake 5, then 1 loss, then spin 1 win — `wager_streak` should be 1 (not 3) after the post-loss win.
  5. `pytest` passes.

### T72: Banking guard (409 while double_down_pending)

- **Spec ref:** S3.4 (banking)
- **Status:** [x] (2026-06-22) — `/api/wager/bank` returns 409 with "Cannot bank while double-down is pending" if armed; Bank button disabled in JSX, 2 tests
- **Parallel group:** P7-wager
- **Depends on:** T08
- **Files:**
  - game.py
- **Acceptance criteria:**
  1. POST `/api/wager/bank` returns 409 if `double_down_pending` is TRUE.
  2. Response body: `{"error": "Cannot bank while double-down is pending"}`.
  3. Frontend: Bank button is disabled (greyed) while `doubleDownPending === true`.
  4. Bank button is enabled when `wagerBankedWins > 0` AND `doubleDownPending === false`.
  5. **Test:** trigger double-down, attempt to bank, assert 409.
  6. `pytest` passes.

### T73: Double-down rework — escrow last win amount (B19)

- **Spec ref:** S3.5 (double-down)
- **Status:** [x] (2026-06-22) — `_resolve_spin` records `wager_last_win_amount` on win, double-down uses it as escrow, 6 tests
- **Parallel group:** P7-wager
- **Depends on:** T69 (for `wager_last_win_amount`), T08
- **Files:**
  - game.py
  - wagers.py
  - static/app.jsx
- **Acceptance criteria:**
  1. On each win, set `wager_last_win_amount` to the `direct_wins` payout portion (not including escrow return).
  2. POST `/api/wager/double-down` sets `double_down_pending = TRUE` (unchanged).
  3. On the next spin, escrow is `wager_last_win_amount` (the actual previous payout), NOT `compute_stake_risk(wins, stake * 2)`.
  4. Stake multiplier for double-down spin is 2x the player's current stake (capped at 10).
  5. **Win on double-down:** escrowed amount returned, plus `base_payout * effective_stake`. Total gain ≈ 2x previous payout.
  6. **Loss on double-down:** escrowed amount forfeited (player loses the exact winnings they had just gained).
  7. If `wager_last_win_amount == 0`: double-down is a no-op (equivalent to a normal spin at the selected stake).
  8. **Inverted mode (T79):** `wager_last_win_amount` tracks the last loss-gain amount. Double-down escrows that in losses.
  9. **Tooltip (B19) updated:** "Double-Down: risk your last winnings for a chance to double them." (`app.jsx:3722`)
  10. **Test:** win 100, double-down, win → player gains 200. Win 100, double-down, loss → player loses 100.
  11. `pytest` passes.

### T74: Insurance rework — dice-charge model (B2, B15, B16, B17)

- **Spec ref:** S3.6 (insurance)
- **Status:** [x] (2026-06-22) — `WAGER_INSURANCE_RECHARGE_SECONDS=600` + `_recharge_wager_insurance` helper, charge consumes on arm, fires on loss, skips safety net, 11 tests
- **Parallel group:** P7-wager
- **Depends on:** T69 (for `wager_insurance_last_recharge`), T08
- **Files:**
  - game.py
  - models.py
  - wagers.py
  - static/app.jsx
- **Acceptance criteria:**
  1. New constants in `models.py`:
     - `WAGER_INSURANCE_RECHARGE_SECONDS = 600` (10 min/charge)
     - `WAGER_INSURANCE_MAX_CHAGES = 3`
  2. New helper `_recharge_wager_insurance(charges, last_recharge, max_charges, now_utc)` in `wagers.py` (mirror dice helper).
  3. New column `wager_insurance_last_recharge TIMESTAMPTZ` on game_state (T69).
  4. **Charge regeneration:** 1 charge per 10 min, bulk-award on login, capped at 3. Timer pauses at cap. Invoke at `/api/state`, spin path, `/api/wager/insurance`.
  5. **Arming:** POST `/api/wager/insurance` consumes a charge immediately (decrement `wager_insurance_charges`, reset `wager_insurance_last_recharge` to NOW if charges < max). This is a gamble — charge wasted on a win.
  6. **Spin resolution:** if spin loses with insurance armed → cap `actual_loss` at `effective_stake`, refund escrowed `stake_wins`. If spin wins → charge wasted. `wager_insurance_armed` cleared regardless.
  7. **Safety net does NOT stack (B2):** when insurance fires on a loss, skip safety net refund entirely.
  8. **Inverted mode:** insurance caps the "win" outcome (bad) and refunds the staked losses.
  9. **State response (B16):** `wager_insurance_armed` is included in `/api/state`.
  10. **UI (B17):** armed indicator shows when insurance is armed (e.g. "🛡️ Insurance ARMED — next loss protected").
  11. **Tests:** insurance fires on loss, charge consumed on arm regardless of outcome, safety net skipped when insurance fires.
  12. `pytest` passes.

### T75: Wager panel always visible but disabled (panel visibility)

- **Spec ref:** S3.7 (panel visibility)
- **Status:** [x] (2026-06-22) — wager panel always renders, slider disabled when `!wager_unlock && mode !== 'inverted'`, tooltip + opacity/cursor style set
- **Parallel group:** P7-wager
- **Depends on:** T09
- **Files:**
  - static/app.jsx
- **Acceptance criteria:**
  1. Wager panel (stake slider, bank button, hot-streak meter, etc.) is **always visible** to all players.
  2. Stake slider is **disabled and greyed out** when `wager_unlock` is not owned.
  3. Disabled slider has a tooltip: "Buy wager_unlock (500 wins)."
  4. **Exception (T79):** in inverted mode, the stake slider is fully functional without `wager_unlock`.
  5. This ensures the step-2 onboarding coach-mark has a target element to point at, even before the player can afford `wager_unlock`.
  6. Visual: disabled slider has reduced opacity (e.g. 0.5), `cursor: not-allowed`.
  7. Frontend compiles without errors.

## Wheel mode hardening

### T76: Mode-change resets (BUG-Q1.8)

- **Spec ref:** S3.8 (mode change), §4 (modes)
- **Status:** [x] (2026-06-22) — `/api/wheel-mode` resets streak/insurance/double-down/gravity_drift on actual mode change (not no-op), response includes resets, 2 tests
- **Parallel group:** P7-modes
- **Depends on:** T08, T10
- **Files:**
  - game.py
- **Acceptance criteria:**
  1. POST `/api/wheel-mode` resets on mode change:
     - `wager_streak` → 0 (prevents hot-streak gaming by hopping modes)
     - `wager_insurance_armed` → FALSE (insurance does not carry across mode switches)
     - `double_down_pending` → FALSE (double-down does not carry across mode switches)
     - `gravity_drift` → 0 (resets drift when switching to or from gravity mode)
  2. Response includes all reset values.
  3. **Test:** arm insurance in mode A, switch to mode B, verify `wager_insurance_armed` is FALSE.
  4. `pytest` passes.

### T77: Gravity mode full mechanic — drift column, dynamic probabilities

- **Spec ref:** S4.1 (gravity mode)
- **Status:** [x] (2026-06-22) — `compute_gravity_probabilities` + `clamp_gravity_drift`, drift ±10/spin capped ±35, `wheel_probabilities` in state+spin, 14 tests
- **Parallel group:** P7-modes
- **Depends on:** T11, T69 (for `gravity_drift` column)
- **Files:**
  - game.py
  - wheel_modes.py
  - static/app.jsx
- **Acceptance criteria:**
  1. Base profile: 55% win / 40% lose / 5% jackpot.
  2. **Drift mechanic:**
     - After each win or jackpot: `gravity_drift = min(gravity_drift + 10, 35)`
     - After each loss: `gravity_drift = max(gravity_drift - 10, -35)`
     - Jackpot counts as a win for drift purposes.
     - **Drift resets to 0 on mode switch** (T76).
  3. **Effective probabilities:**
     - `win_pct = 55 + gravity_drift` (range: 20–90%)
     - `lose_pct = 40 - gravity_drift` (range: 5–75%)
     - `jackpot_pct = 5` (fixed)
  4. State response and spin response include drift-adjusted probabilities as `wheel_probabilities: {win_pct, lose_pct, jackpot_pct}`.
  5. `pytest` passes.

### T78: Mirror mode full mechanic — double escrow

- **Spec ref:** S4.2 (mirror mode)
- **Status:** [x] (2026-06-22) — mirror mode doubles escrow, takes better of two rolls, forfeit full 2× on double-loss, 6 tests. **[DEFERRED 2026-06-26]** The "two wheels" frontend visual was never built and will not ship for S8. Mirror removed from the weekly rotation for launch; replaced by T115 (simple win/loss% mode). Backend mechanic (wheel_modes.py / game.py) preserved for 8.X reuse.
- **Parallel group:** P7-modes
- **Depends on:** T11
- **Files:**
  - game.py
  - wheel_modes.py
- **Acceptance criteria:**
  1. Escrow = `2 * stake_wins` (double the normal escrow, debited before spin).
  2. Two outcomes are rolled independently.
  3. Player takes the **better** outcome (by rank: jackpot > win > lose).
  4. **Better = win or jackpot:** full escrow (2 * stake_wins) is returned. Payout = `base_payout * effective_stake` (normal, not doubled). The second (worse) outcome is ignored.
  5. **Better = lose (both lost):** full escrow (2 * stake_wins) is forfeited. `losses += base_loss * effective_stake` (once, not twice). Streak resets.
  6. **Safety net:** on a double-loss at ≥5x stake, refunds 25% of the FULL escrow (2 * stake_wins).
  7. **Insurance (T74):** on a double-loss, insurance caps the loss and refunds the FULL escrow.
  8. **Hot streak:** increments on a win (the better outcome).
  9. `pytest` passes.

### T79: Inverted mode — full loss-farming mechanic

- **Spec ref:** S4.3, §4.4 (inverted mode)
- **Status:** [x] (2026-06-22) — loss-farming: stake debits from losses, escrow returned on lose/jackpot (good), forfeited on win (bad), shields trigger on bad outcome, 17 tests. **Manual fix (2026-06-22):** spin response now includes `active_wheel_mode` and `message` fields (via `_build_spin_message()`); inverted semantics surfaced via message (e.g., "Loss-farmed +N losses", "Unwanted win — forfeited N losses").
- **Parallel group:** P7-modes
- **Depends on:** T11
- **Files:**
  - game.py
  - wheel_modes.py
  - static/app.jsx
- **Acceptance criteria:**
  1. Probability profile: 60% lose (good) / 35% win (bad) / 5% jackpot (super-good).
  2. **Escrow:** `stake_losses = floor(current_losses * STAKE_RISK_PCT[stake])` debited from `losses` immediately. Capped at `current_losses`.
  3. **Lose (the good outcome):**
     - Escrowed `stake_losses` returned to `losses`.
     - `losses += stake_losses + (base_loss * effective_stake * hot_streak_bonus)`.
     - `wager_streak` increments (same-stake rule).
     - `wager_banked_losses` accumulates the hot-streak bonus portion.
     - Shield/guard/resilience do NOT trigger.
  4. **Win (the bad outcome):**
     - Escrowed `stake_losses` is NOT returned (forfeited).
     - `wins += base_payout * effective_stake` (wins ARE gained; the player gains wins, undesirable in loss-farming, but no outcomes are negated).
     - `wager_streak` resets to 0.
     - `wager_banked_losses` is forfeited.
     - **Shield/guard/resilience trigger here** (the bad outcome).
  5. **Jackpot (the super-good outcome):**
     - Escrowed `stake_losses` returned.
     - `losses += stake_losses + (base_loss * effective_stake * 5)`.
     - `wager_streak` increments.
  6. **Safety net (T70):** on the bad outcome (win) at ≥5x stake, refunds 25% of staked losses.
  7. **Insurance (T74):** arms before spin, caps the bad outcome (win) and refunds escrowed losses.
  8. **Double-down (T73):** `wager_last_win_amount` tracks the last loss-gain amount. Double-down escrows that in losses.
  9. **Banking:** Bank button banks `wager_banked_losses` into `losses`. Cannot bank while `double_down_pending` is true (T72).
  10. **`wager_unlock` NOT required** in inverted mode — stake slider is fully functional without it (T75).
  11. **Frontend:** wheel labels swap — "LOSE" becomes the large/green segment (good), "WIN" becomes the smaller/red segment (bad).
  12. `pytest` passes.

### T80: Dynamic wheel graphic — server-provided probabilities

- **Spec ref:** S17 (dynamic wheel graphic)
- **Status:** [x] (2026-06-22) — `wheelProbabilities` state, `drawWheel` accepts param, falls back to `WHEEL_MODE_DRAW`, redraws on change, `static/js/wheel-modes.js` shared module, 8 tests. **Known issue (2026-06-22):** wheel canvas does not visually redraw on mode change due to React 18 useEffect closure capturing stale `wheelProbabilities`; active button changes correctly. Workaround: hard-reload.
- **Parallel group:** P7-modes
- **Depends on:** T11, T77 (gravity drift)
- **Files:**
  - game.py
  - static/app.jsx
  - static/js/wheel-modes.js
- **Acceptance criteria:**
  1. Server includes `wheel_probabilities: {win_pct, lose_pct, jackpot_pct}` in `/api/state` and spin response.
  2. Replace `WHEEL_MODE_DRAW` hardcoded table (`app.jsx:892-899`) with state from server.
  3. Store `wheelProbabilities` in state (`app.jsx`).
  4. Add `wheelProbabilities` to the redraw effect dependency array (`app.jsx:3228-3231`).
  5. `drawWheel()` uses `wheelProbabilities` if provided, falls back to `WHEEL_MODE_DRAW` for backward compat.
  6. **For inverted mode (T79):** wheel labels swap — "LOSE" becomes the large/green segment (good), "WIN" becomes the smaller/red segment (bad). The arc spans reflect the inverted profile (60% lose, 35% win, 5% jackpot).
  7. Wheel redraws whenever probabilities change (e.g., gravity drift shifts after each spin).
  8. Frontend compiles without errors.

## Chat and auto-post hardening

### T81: Chat history 200 messages + cursor pagination

- **Spec ref:** S12 (chat history)
- **Status:** [x] (2026-06-22) — `?before=<id>&limit=N` cursor pagination on `/api/chat`, scroll-near-top loads older, 6 new tests
- **Parallel group:** P7-chat
- **Depends on:** T17
- **Files:**
  - chat.py
  - static/app.jsx
- **Acceptance criteria:**
  1. **Backend (`chat.py`):**
     - Initial SELECT `LIMIT 30` → `LIMIT 50`.
     - Trim `LIMIT 50` → `LIMIT 200` in both `post_chat` and `post_system_message`.
  2. **Cursor pagination:** GET `/api/chat` supports `?before=<id>&limit=50`. Returns 50 messages with `id < <id>`, ordered `id DESC`, then reversed (oldest first).
  3. The `id` column is `BIGSERIAL` with an existing `idx_chat_messages_id_desc` index — cursor pagination is ready, no schema change needed.
  4. **Frontend (`app.jsx:2096-2276`):**
     - Initial load: fetch latest 50 messages.
     - On scroll near top (`scrollTop < threshold`): fetch `/api/chat?before=<oldestLoadedId>&limit=50`. Prepend to message list.
     - State: `loadingOlder`, `hasMore`, `oldestLoadedId`.
     - Preserve scroll position when prepending (capture `scrollHeight` before, restore offset after).
     - Poll (5s interval) continues to fetch latest 50. Merge with loaded older messages by id (dedup).
     - "Loading older…" affordance above the message list while fetching.
  5. `pytest` passes.

### T82: Auto-post messages with configurable triggers

- **Spec ref:** S12 (auto-post system messages)
- **Status:** [x] (2026-06-22) — chat_triggers.py created, 7 of 8 triggers wired in game.py (goal_milestone left for T84), 9 tests added
- **Parallel group:** P7-chat
- **Depends on:** T17, T06
- **Files:**
  - chat.py
  - game.py
  - static/app.jsx
  - chat_triggers.py (new)
- **Acceptance criteria:**
  1. New module `chat_triggers.py` with code-level constants:
     - `JACKPOT_MSG_ALWAYS = True` (any jackpot, any stake, any mode, including auto-spin)
     - `DOUBLE_DOWN_MSG_MIN_EFFECTIVE_STAKE = 5`
     - `HOT_STREAK_MSG_THRESHOLD = 10`
     - `BIG_WIN_THRESHOLD = 5000`
  2. Triggers (each posts a system message):
     - **Jackpot:** `🎰 {user} hit a JACKPOT in {mode} mode at {stake}x stake for {wins_delta} wins!` (event_kind='jackpot')
     - **Double-down win:** `🔥 {user} won a {effective_stake}x double-down for {wins_delta} wins!` (effective_stake ≥ 5, event_kind='double_down_win')
     - **Hot streak 10:** `🔥 {user} reached a 10-win hot streak!` (event_kind='hot_streak_10')
     - **Big win:** `💰 {user} won {wins_delta} wins in {mode} mode!` (T83 — per-player escalating threshold, event_kind='big_win')
     - **Prestige:** `⭐ {user} reached Prestige Level {N}!` (event_kind='prestige')
     - **New player:** `🎉 {user} spun the wheel for the first time! Welcome to Season 8!` (event_kind='new_player')
     - **Singularity fill:** `🌀 The Singularity has converged! Total contributed: {N}` (event_kind='singularity_fill')
     - **Community goal milestone:** `Community goal at {pct}%: {current} / {target}` (T84, event_kind='goal_milestone_{pct}`)
  3. Game endpoints call `post_system_message(conn, message, message_type='system', event_kind=kind)` after the primary action succeeds.
  4. System messages have `user_id = NULL, username = 'SYSTEM'`.
  5. **Throttling:** per-`event_kind` 30s throttle (T92). Each event kind has its own throttle window.
  6. `pytest` passes.

### T83: Per-player escalating big-win threshold

- **Spec ref:** S12 (big-win threshold)
- **Status:** [x] (2026-06-22) — `_maybe_announce_big_win` helper, persists `biggest_win_announced` in same transaction, 9 new tests
- **Parallel group:** P7-chat
- **Depends on:** T69 (for `biggest_win_announced` column), T82
- **Files:**
  - game.py
- **Acceptance criteria:**
  1. New column: `biggest_win_announced INTEGER NOT NULL DEFAULT 0` on `game_state` (T69).
  2. On a win: if `wins_delta >= BIG_WIN_THRESHOLD` (5000) AND `wins_delta > biggest_win_announced`: post the big-win message (T82), then UPDATE `biggest_win_announced = wins_delta`.
  3. Reset to 0 on prestige (T85).
  4. **Test:** trigger wins of 5001, 5500, 6000 — first message fires on 5001 (above threshold, > 0), second fires on 5500 (> 5001), third fires on 6000 (> 5500). Win of 5100 does not fire (5100 < 5500).
  5. `pytest` passes.

### T84: Community goal milestones (25/50/75%)

- **Spec ref:** S9 (community goals, milestone tracking)
- **Status:** [x] (2026-06-22) — milestone check in `increment_goal` after UPDATE, 5 tests added (25/50/75 crossing, 100% no-post, no double-fire)
- **Parallel group:** P7-chat
- **Depends on:** T27 (for milestone columns), T82 (for auto-post)
- **Files:**
  - community_goals.py
  - migrations/037_community_goals.sql (or 047)
- **Acceptance criteria:**
  1. Columns `milestone_25/50/75` BOOLEAN on `community_goals` (T27).
  2. After each `increment_goal` call, check if `current` crossed a 25/50/75% threshold.
  3. If so, set the corresponding `milestone_*` column to TRUE and post a system message:
     - `event_kind='goal_milestone_25'` — "Community goal at 25%: X / target"
     - `event_kind='goal_milestone_50'` — "Community goal at 50%: X / target"
     - `event_kind='goal_milestone_75'` — "Community goal at 75%: X / target"
  4. 100% is the completion event itself — no separate milestone; the completion reward distribution already fires.
  5. Milestones reset weekly with the goal (new row = fresh columns).
  6. `pytest` passes.

## Prestige hardening

### T85: Prestige scope update — wager tokens persist

- **Spec ref:** S5.3 (prestige reset scope)
- **Status:** [x] (2026-06-22) — `PRESTIGE_RESET_COLUMNS` (44 cols) + `filter_kept_items` helper, `wager_tokens`/`onboarding_step` preserved, 14 tests. **Manual fix (2026-06-22):** `_prestige_default` now returns `dt.datetime.now(timezone.utc)` for `dice_last_recharge`/`wager_insurance_last_recharge`/`fishing_cast_at`/`fishing_bite_at` (NOT NULL columns); previously returned `None` causing 500.
- **Parallel group:** P7-prestige
- **Depends on:** T13
- **Files:**
  - game.py
  - prestige.py
- **Acceptance criteria:**
  1. **Resets on prestige:** wins, losses, streak, best_streak, owned_items (minus kept+cosmetics), all inf levels, wager_streak, wager_last_stake, double_down_pending, wager_banked_wins, wager_banked_losses, wager_insurance_charges, wager_insurance_last_recharge, wager_last_win_amount, guard_charges, guard_last_regen_spin, resilience_last_use_spin, dice_charges, dice_last_recharge, dice_rolled_since_spin, pending_dice, fish_clicks, cast/reel state, fish_exchange_total, spin_count, win_count, loss_count, proc_streak, equipped_class, active_wheel_mode, gravity_drift, biggest_win_announced, bounty progress, wager_insurance_armed.
  2. **Preserves on prestige:** prestige_level, prestige_count, legacy_wins, owned_cosmetics, active_cosmetics, aquarium_species, loadouts, cosmetic_fragments, **onboarding_step** (T88), **wager_tokens** (NEW — not in v1 list, added in spec hardening).
  3. Community goal contributions and singularity contributions are in separate tables — not affected by prestige.
  4. **Test:** gain 1000 wager_tokens, prestige, verify wager_tokens still 1000.
  5. `pytest` passes.

### T86: Prestige_efficiency as win retention only

- **Spec ref:** S5 (prestige_efficiency)
- **Status:** [x] (2026-06-22) — `compute_wins_kept(wins, owned_items)`, threshold always 1M (no efficiency scaling), losses always reset, 9 tests
- **Parallel group:** P7-prestige
- **Depends on:** T13
- **Files:**
  - game.py
  - prestige.py
- **Acceptance criteria:**
  1. `prestige_efficiency` keeps `floor(wins * 0.1 * level)` wins on prestige. At level 0: `new_wins = 0`. At level 5: `new_wins = floor(wins * 0.5)`.
  2. **The 1,000,000 wins cost threshold is NOT reduced** by efficiency. Always 1,000,000 wins.
  3. **`prestige_efficiency` retains wins only, not losses.** Losses are always reset to 0 on prestige.
  4. **Test:** 2,000,000 wins with prestige_efficiency level 5 → new_wins = 1,000,000. 2,000,000 wins with level 0 → new_wins = 0.
  5. `pytest` passes.

## Onboarding hardening

### T87: Onboarding step 5 (terminal transition)

- **Spec ref:** S15 (onboarding), B13
- **Status:** [x] (2026-06-22) — `/api/bounties` advances step 3→5 in one UPDATE with 100 wager_tokens grant, response includes `onboarding_advance: true`, 3 tests added
- **Parallel group:** P7-onboard
- **Depends on:** T43
- **Files:**
  - game.py
- **Acceptance criteria:**
  1. `onboarding_step` caps at 5 (all done).
  2. When `/api/bounties` advances `onboarding_step` from 3 to 4, it also advances to 5 in the same UPDATE.
  3. Step 4 is "first bounty panel open" — the player opened it, they're done.
  4. The reward (100 wager_tokens) is granted at the 3→5 transition.
  5. Response includes `onboarding_advance: true` when step 3→5 is triggered.
  6. **Test:** GET `/api/bounties` with `onboarding_step = 3` → response has `onboarding_advance: true`, `wager_tokens` increased by 100, `onboarding_step` = 5.
  7. `pytest` passes.

### T88: Onboarding rollover preservation (B10)

- **Spec ref:** S15, S19 (rollover)
- **Status:** [x] (2026-06-22) — `onboarding_step = 0` removed from `seasons.py:139`, 3 tests added
- **Parallel group:** P7-onboard
- **Depends on:** T02
- **Files:**
  - seasons.py
- **Acceptance criteria:**
  1. `_perform_rollover()` does NOT reset `onboarding_step`. A player who completes onboarding in 8.1 never sees it again.
  2. Verify at `seasons.py:139` — the `onboarding_step = 0` line is removed.
  3. **Test:** set `onboarding_step = 5`, call `_perform_rollover()`, verify `onboarding_step` is still 5.
  4. `pytest` passes.

## Bug audit and minor fixes

### T89: Replay system complete removal

- **Spec ref:** S12 (replay system removed), B3, B4, B6, B7, B8
- **Status:** [x] (2026-06-22) — `replays.py` + `test_replays.py` deleted, replay/share endpoint + UI removed from game.py/app.jsx, no `replay` references in active code
- **Parallel group:** P7-bugfix
- **Depends on:** T34
- **Files:**
  - replays.py (delete)
  - tests/test_replays.py (delete)
  - game.py
  - static/app.jsx
- **Acceptance criteria:**
  1. Delete `replays.py` and `tests/test_replays.py` entirely.
  2. Remove `should_generate_replay` and `generate_replay` from `game.py` (lines 864-868).
  3. Remove POST `/api/replay/share` endpoint (`game.py:3023-3037`).
  4. Remove the replay card render branch in `app.jsx:2223-2233`.
  5. Remove the "Share" button from the UI (B7).
  6. The `replay_string` field in spin responses is removed (or always null).
  7. Auto-post system messages (T82) replace the replay system's role.
  8. **Note:** T66 (HMAC-sign replay strings) is rendered moot by this ticket — HMAC code is removed.
  9. `grep -rn "replay" .` (excl. node_modules, test fixtures) shows only auto-post references.
  10. `pytest` passes; staging server starts with no import error.

### T90: Auto-post messages to auto-spin path (B5)

- **Spec ref:** S12 (auto-post), B5
- **Status:** [x] (2026-06-22) — jackpot/hot-streak/big-win posting wired in `/api/tick` loop, `biggest_win_announced` persisted, 4 new tests
- **Parallel group:** P7-bugfix
- **Depends on:** T18, T82
- **Files:**
  - game.py
- **Acceptance criteria:**
  1. The `/api/tick` path (currently `game.py:1161-1213`) includes message-posting logic for auto-spin jackpots and big wins.
  2. Auto-spin jackpots post the jackpot message (T82).
  3. Auto-spin big wins post the big-win message (T82, T83).
  4. Auto-spin hot-streak 10 posts the hot-streak message.
  5. **Test:** start auto-spin, force a jackpot outcome, verify message posted to chat.
  6. `pytest` passes.

### T91: Remove bounty "all 3" chat message (B21)

- **Spec ref:** S8 (bounties), B21
- **Status:** [x] (2026-06-22) — `post_system_message` call removed, dedented `conn.commit()` re-indented in `claim_bounty()` and `prestige_reset()` (manual fix 2026-06-22), test added (mutation-tested)
- **Parallel group:** P7-bugfix
- **Depends on:** T40
- **Files:**
  - game.py
- **Acceptance criteria:**
  1. Delete the `post_system_message` call at `game.py:2812` (the "all 3 bounties complete" chat post).
  2. Bounty completions stay in bounty panel only — never broadcast to chat.
  3. **Test:** complete all 3 bounties, claim rewards, verify no system message is posted.
  4. `pytest` passes.

### T92: Chat rate limit + trim for system messages

- **Spec ref:** S12 (auto-post throttling)
- **Status:** [x] (2026-06-22) — `MAX_CHAT_MESSAGES=200` constant added, both trims use it, 7 tests in test_chat.py
- **Parallel group:** P7-bugfix
- **Depends on:** T17
- **Files:**
  - chat.py
  - tests/test_chat.py
- **Acceptance criteria:**
  1. Per-worker, in-memory throttle keyed by `event_kind` (each event kind throttles independently).
  2. Max 1 system message per 30s per event kind.
  3. `post_system_message` trims `chat_messages` to `MAX_CHAT_MESSAGES = 200` the same way `post_chat` does.
  4. Tests: 4+ tests in `tests/test_chat.py` covering throttle, trim, distinct kinds, race.
  5. `pytest` passes.

### T93: Per-player cap race fix in increment_goal

- **Spec ref:** S9 (community goals)
- **Status:** [x] (2026-06-22) — `FOR UPDATE` already in place, 9 tests added (1 real concurrent integration test, 8 mock)
- **Parallel group:** P7-bugfix
- **Depends on:** T28
- **Files:**
  - community_goals.py
- **Acceptance criteria:**
  1. `increment_goal` uses `SELECT ... FOR UPDATE` after an `ON CONFLICT DO NOTHING` upsert.
  2. The race window where two concurrent requests near a player's cap could each read the same stale value is closed.
  3. **Test:** simulate concurrent calls, verify cap is never exceeded.
  4. `pytest` passes.

### T94: Auto-spin budget=0 guard + first-tick gate

- **Spec ref:** S18 (auto-spin)
- **Status:** [ ]
- **Parallel group:** P7-bugfix
- **Depends on:** T18
- **Files:**
  - game.py
  - static/app.jsx
- **Acceptance criteria:**
  1. `/api/tick` returns early with `auto_spin_active: false` when `auto_spin_budget = 0` (BUG-02).
  2. First-tick activation (`auto_spin_since = NOW`) only runs when `budget > 0` (BUG-03). Players who have never started auto-spin are not blocked from manual spin.
  3. Frontend tick `useEffect` is gated on `autoSpinBudget > 0` (BUG-04).
  4. **Test:** call `/api/tick` with budget=0, verify returns immediately with `auto_spin_active: false`.
  5. `pytest` passes.

### T95: Manual spin button + auto-spin start/stop

- **Spec ref:** S18 (auto-spin)
- **Status:** [ ]
- **Parallel group:** P7-bugfix
- **Depends on:** T18
- **Files:**
  - game.py
  - static/app.jsx
- **Acceptance criteria:**
  1. `handleManualSpin` callback exists in `App` component.
  2. POST `/api/spin` works as a manual spin trigger.
  3. A `▶ Spin ◀` button is rendered below the wheel.
  4. Auto-spin start/stop controls are present (sets `auto_spin_budget = 100` / `0`).
  5. The `/api/spin` guard requires both `auto_spin_since IS NOT NULL` AND `budget > 0` to be blocked.
  6. **Test:** click spin button, verify `/api/spin` called and state updates.
  7. `pytest` passes.

### T96: Wheel-wrapper height budget re-tune

- **Spec ref:** S21 (frontend), BUG-W03
- **Status:** [x] (2026-06-22) — `.wheel-wrapper` cap 420→580px desktop / 320→480px mobile with `calc(100vh - 480px)`/`calc(100vh - 420px)` budget (2026-06-22 manual fix: reverted-from 460→640 commit had reduced cap to 420px; fixed to 580px); wheel now 320×320 on 1280×800 viewport (was 160×160)
- **Parallel group:** P7-bugfix
- **Depends on:** T75 (panel always visible)
- **Files:**
  - static/styles.css
- **Acceptance criteria:**
  1. `.wheel-wrapper` (`static/styles.css:185-189`) height budget accounts for the wager panel.
  2. Re-derive empirically: load the page with every wager upgrade owned and a hot streak active, measure actual non-wheel column height.
  3. Mobile breakpoint (`static/styles.css:2403-2406`) also re-tuned.
  4. **Consider (not mandate):** replace the magic-number budget with an intrinsic/flexible sizing approach (e.g. flex `flex: 1 1 auto; min-height: 0`) so future panels don't require another manual recalibration.
  5. Visual verification: the wheel does not shrink or push the page beyond the viewport when the wager panel is at its tallest (all upgrades owned, hot streak active, double-down armed, insurance armed).
  6. No regression in other panels (mode selector, prestige, bounty).

---

## Diagnostic tickets (Phase 7 follow-up)

### T97: Wheel canvas does not redraw on wheel-mode change (T80 follow-up)

- **Spec ref:** S17 (dynamic wheel graphic), BUG-W04
- **Status:** [x] (2026-06-22) — R2: redraw useEffect trimmed to [wheelTheme, activeWheelMode] deps; handleWheelModeChange now calls drawWheel(canvasRef, wheelThemeRef, mode, null) synchronously BOTH on success and in the !ok branch (which re-draws the previous mode). This forces an immediate redraw because the redraw useEffect is not firing reliably for activeWheelMode changes in this React 18 build (state updates correctly, the button's active class moves, the fiber's hook state updates, but the useEffect does not re-execute — root cause still unknown). Live verified in browser: pixel-hash sequence steady→volatile→mirror→steady→mirror returns 278526009 / 214336945 / 287808687 / 278526009 / 287808687 (each click produces the expected mode's hash). 205 pytest passed, 1 skipped.
- **Discovered:** 2026-06-22 (manual testing after Phase 7; see `MANUAL_TEST_RESULTS.md`)
- **Related ticket:** T80 (Dynamic wheel graphic — server-provided probabilities). T80 marked the work as done, but a React 18 closure/batching interaction prevents the canvas from being redrawn when the user switches modes after the first mode change.
- **Parallel group:** P7-bugfix (single ticket — needs full diagnosis)
- **Depends on:** T80
- **Files:**
  - `static/app.jsx` (lines 3317–3330 redraw `useEffect`, lines 3844–3873 `handleWheelModeChange`)
  - `static/js/wheel-modes.js` (read-only reference)
- **Symptom:**
  1. User loads the page; wheel renders correctly for the initial mode (e.g. `steady`).
  2. User clicks `Volatile` mode button. The button's `active` class moves to Volatile, React state updates correctly (verified by reading `document.querySelector('.wheel-mode-btn.active').textContent`).
  3. **The canvas pixels do not change.** Pixel-hash is identical before and after the click. The wheel still shows the previous mode's arc widths (e.g. `70/28/2` steady distribution) even though `activeWheelMode === 'volatile'`.
  4. A hard page reload (`location.href = '/?t=' + Date.now()`) makes the wheel render with the new mode's correct distribution.
  5. Subsequent mode changes (e.g. Volatile → Mirror) reproduce the same staleness: the wheel keeps showing the most-recently-rendered mode's pattern, not the current `activeWheelMode`.
- **Diagnosis (from QA agent + main-agent attempts on 2026-06-22):**
  - The canvas redraw happens via the `useEffect` at `app.jsx:3317-3330` whose deps are `[wheelTheme, activeWheelMode, wheelProbabilities]`.
  - `drawWheel()` (line 905) prefers `wheelProbabilities` over `WHEEL_MODE_DRAW[wheelMode]` when the probs arg is truthy.
  - After a spin, `wheelProbabilities` is set to the spin's probability distribution (e.g. steady `70/28/2`). The state persists across mode changes.
  - On mode change, `handleWheelModeChange` does:
    1. `setActiveWheelMode(mode)` — schedules re-render.
    2. `setWheelProbabilities(null)` — schedules re-render.
    3. Manual `drawWheel(canvas, theme, mode, null)` — should draw with the new mode's static fallback.
    4. `await apiGame('/api/wheel-mode', ...)` — returns `{mode, ok}` with no `wheel_probabilities`.
  - After the batched re-render, the useEffect should fire with the new state `(activeWheelMode=new, wheelProbabilities=null)` and draw with `drawWheel(canvas, theme, 'volatile', null)` → uses volatile's fallback.
  - **But the log shows the useEffect firing with the OLD `wheelProbabilities`** (e.g. steady's `70/28/2` even when `activeWheelMode='volatile'`). This indicates React 18 is firing the useEffect from the previous render's closure OR the `setWheelProbabilities(null)` call is being lost/overridden before the useEffect runs.
  - Verified manually that calling `drawWheel(canvas, 'default', 'volatile', null)` directly from the page console DOES produce volatile's pixel-hash. The function is correct; the React wiring is the bug.
  - The manual `drawWheel(...)` call inside `handleWheelModeChange` either doesn't run (no `[MANUAL]` log appears) or runs but is immediately overwritten by the useEffect's stale-state draw.
- **Fix approaches (in order of preference — try each, stop when one works):**
  1. **`useLayoutEffect` instead of `useEffect`** — runs synchronously after DOM mutations, before paint. May close the React 18 batching window.
  2. **`wheelProbabilitiesRef` + read ref in useEffect** — mirror the existing `wheelThemeRef` pattern. The ref always holds the latest value; the useEffect closure reads from the ref, not the captured state.
  3. **Remove `wheelProbabilities` from the deps** — the wheel only needs to use `wheelProbabilities` for gravity drift (which the spin handler can pass explicitly via a separate redraw call). The useEffect only redraws on `[wheelTheme, activeWheelMode]`. Side effect: gravity drift no longer triggers a redraw on every spin in gravity mode; the spin handler must call `drawWheel(...)` itself after setting the new `wheelProbabilities`.
  4. **`useReducer` for `(activeWheelMode, wheelProbabilities)`** — bundle the two state values into one reducer, ensuring the useEffect always sees both updates atomically.
  5. **`flushSync` after `setWheelProbabilities(null)`** — forces React to commit the state synchronously, so the useEffect fires with the new value. May cause "Cannot update a component while rendering" warnings.
- **Acceptance criteria:**
  1. Reproduce the bug deterministically: load the page, click `Volatile` mode, screenshot the wheel. Then click `Mirror`, screenshot. Then click `Steady`, screenshot. After each click, the canvas pixel-hash must differ from the previous click's hash.
  2. The wheel shows the correct arc widths for the current `activeWheelMode` at all times, without a hard reload.
  3. The 8 existing `test_dynamic_wheel.py` tests still pass.
  4. **New test:** add a Playwright-based test that clicks each mode button in sequence (steady → volatile → mirror → steady) and asserts the canvas pixel-hash changes after each click.
  5. **New test:** add a Python unit test that uses a mock canvas to verify `handleWheelModeChange` results in a drawWheel call with `wheelProbabilities=null` after a mode change.
  6. No regression: the `wheelProbabilities` state is still updated correctly by the spin handler (gravity drift still visualized on the wheel after each gravity spin).
  7. No regression: the wager panel tooltip / disabled state still works (T75).
  8. Console is clean — no React warnings about state updates during render or "cannot update unmounted component".
- **Workaround until fixed:** User can hard-reload the page after a mode change to force a re-render with the new mode's probabilities.

---

### T98: Wager stake stale-closure bug + spin response missing effective_stake

- **Spec ref:** S13 (wager), T70 (effective_stake on all wager paths)
- **Status:** [x] (2026-06-22) — B23: stakeRef added near the other refs (initialized from `gameState.wager_last_stake || 1`, mirrored by `useEffect(() => { stakeRef.current = stake }, [stake])`); `handleStakeChange` sets `stakeRef.current = newStake` BEFORE setStake; `handleManualSpin` sends `stake: stakeRef.current` instead of `stake: stake`. B24: spin response in `game.py` now includes `resp['effective_stake'] = events.get('effective_stake', 1)` and `resp['wager_last_stake'] = new_state.get('wager_last_stake', 1)`. Live verified: slider=6 → spin sent stake=6 → DB `wager_last_stake=6`, response includes `effective_stake=6` and `wager_last_stake=6`. Same React 18 closure issue as T97 — state updates correctly (label changes, fiber updates) but `useCallback` closures are not re-creating with the new value, so the spin handler was using the value from the render where it was originally created.
- **Discovered:** 2026-06-22 (live browser testing after T97 R2 — user reported wager "still feels like it doesn't quite work as it should")
- **Related ticket:** T97 (same React 18 root cause — useCallback closures in this build do not re-create when their state-deps change)
- **Parallel group:** P7-bugfix (single ticket)
- **Depends on:** T70, T75
- **Files:**
  - `static/app.jsx` (refs at 3217-3230, spin handler at 3550-3553, stake handler at 3813-3818)
  - `game.py` (spin response at 1333-1352)
  - `tests/test_wager_stake_plumbing.py` (new file, 3 tests)
- **Symptom (B23):** After changing the wager slider to a value different from the page-load value (e.g. slider was 1, user moves to 6), the next spin still uses the OLD stake (5 from a previous test, or 1 from page load). The slider UI shows the new value, the label updates ("6× Bold"), and the React state hook shows the new value via fiber inspection, but the `handleManualSpin` callback's closure captures the OLD value because `useCallback` with `[stake, ...]` deps is not re-creating the function in this build. Server-side: `wager_last_stake` does not change after a non-1 stake spin.
- **Symptom (B24):** `POST /api/spin` with `stake=5` returns `stake: 5` but the response dict is missing `effective_stake` and `wager_last_stake` keys entirely. T70 AC says the response should include `effective_stake=5`.
- **Diagnosis (same as T97):** React 18.3.1 useCallback in this build is not re-creating the function when its state-dep changes. The state itself updates (label re-renders with new value, fiber hook's `lastRenderedState` shows the new value in the latest render), but the callback function reference is cached and uses the value from the render where the callback was originally created. This affects any `useCallback` that depends on React state. The ref-mirror pattern (set ref BEFORE setState) bypasses this by letting the callback read the latest value from the ref, not the closure.
- **Fix applied:**
  1. **stakeRef** (app.jsx:3217-3230): `const stakeRef = useRef(gameState.wager_last_stake || 1);` + `useEffect(() => { stakeRef.current = stake; }, [stake]);` mirrors `stake` state into the ref, similar to the existing `wheelThemeRef` / `activeWheelModeRef` / `wheelProbabilitiesRef` mirrors.
  2. **handleStakeChange** (app.jsx:3813-3818): now sets `stakeRef.current = newStake` BEFORE `setStake(newStake)` so the ref is in sync even if the React state update is delayed.
  3. **handleManualSpin** (app.jsx:3550-3553): sends `stake: stakeRef.current` instead of `stake: stake`. The `useCallback` deps for handleManualSpin were also reduced to remove the stale-stake problem (the closure no longer depends on `stake` — it reads from the ref).
  4. **Spin response** (game.py:1333-1352): added `resp['effective_stake'] = events.get('effective_stake', 1)` and `resp['wager_last_stake'] = new_state.get('wager_last_stake', 1)` to the resp dict augmentation block (the underlying events dict already had these keys from T70's `_resolve_spin`, but the spin handler was not extracting them).
- **Acceptance criteria:**
  1. Set slider to N (N≠1), click wheel. Server `wager_last_stake` becomes N (verified via DB).
  2. Set slider to M (M≠N), click wheel. Server `wager_last_stake` becomes M. No need to reload the page.
  3. `POST /api/spin` with `stake=N` returns `stake: N, effective_stake: N, wager_last_stake: N` in the JSON response.
  4. New file `tests/test_wager_stake_plumbing.py` with 3 tests (3 passed): `test_spin_response_includes_effective_stake` (asserts the new keys in game.py), `test_handleManualSpin_reads_stakeRef_not_stake` (asserts the JSX uses `stake: stakeRef.current`), `test_stakeRef_is_defined_and_mirrored` (asserts the ref + mirror useEffect exist).
  5. The 205 prior tests still pass (208 total now).
  6. Live verified: slider=6 → spin sent stake=6 → DB `wager_last_stake=6`, response includes `effective_stake=6` and `wager_last_stake=6`.
  7. No regression on Hot Streak, Insurance, Double Down, Bank, or mode-switch reset (T71-T78).

---

### T99: Wager panel UI doesn't reflect server-side mode-switch resets

- **Spec ref:** T76 (mode change resets wager state)
- **Status:** [x] (2026-06-22) — B25: `handleWheelModeChange` now reads `wager_streak`, `wager_insurance_armed`, `double_down_pending`, and `gravity_drift` from the `/api/wheel-mode` response data and calls the corresponding setters (same pattern as the existing `wheel_probabilities` / `gravity_drift` handling at line 3873-3878). The same updates are also applied in the `!ok` branch — if the server rejects the change, the React state is restored to the pre-click values. Live verified: arm DD → click Mirror → "⚡ Double-Down armed!" disappears from the panel; arm Insurance → click Mirror → "🛡️ Insurance ARMED" disappears; UI matches DB (`double_down_pending=f, wager_insurance_armed=f, wager_streak=0, gravity_drift=0`).
- **Discovered:** 2026-06-22 (live browser testing after T98 — user noted the wager panel still showed "Double-Down armed!" / "Insurance ARMED" after a mode switch, even though the DB was correctly reset by T76)
- **Related ticket:** T76 (the SERVER reset works correctly), T97 (canvas redraw also needs handler-side help in this React 18 build)
- **Parallel group:** P7-bugfix (single ticket)
- **Depends on:** T76, T77
- **Files:**
  - `static/app.jsx` (`handleWheelModeChange` at 3847-3879)
  - `tests/test_wheel_mode_response.py` (new file, 3 tests)
- **Symptom (B25):** After a user arms Double Down (or Insurance, or builds a Hot Streak), the wager panel correctly shows "⚡ Double-Down armed!" (or "🛡️ Insurance ARMED", or "🔥 Hot Streak: N"). The user then clicks a different wheel mode (e.g., Steady → Mirror). The server correctly resets `double_down_pending=false, wager_insurance_armed=false, wager_streak=0, gravity_drift=0` (T76), BUT the React state never updates. The UI continues to show the armed indicator and the streak counter even though the DB has them cleared. A page reload fixes it (because the next `/api/state` call returns the correct values), but during normal play the UI lies.
- **Diagnosis:** The server's `set_wheel_mode` endpoint at `game.py:3667-3707` ALREADY returns the four reset values in its response:
  ```json
  { "ok": true, "mode": "mirror", "wager_streak": 0, "wager_insurance_armed": false, "double_down_pending": false, "gravity_drift": 0 }
  ```
  But the frontend `handleWheelModeChange` at `app.jsx:3847-3879` only reads `data.wheel_probabilities` and `data.gravity_drift` from the response — it ignores the other three. The `else if` branch at line 3873-3878 already has the right pattern; it just wasn't extended to all the fields.
- **Fix applied:**
  1. **Success branch** (app.jsx:3873-3878): added `if (data.wager_streak != null) setWagerStreak(data.wager_streak);`, `if (data.wager_insurance_armed != null) setWagerInsuranceArmed(data.wager_insurance_armed);`, `if (data.double_down_pending != null) setDoubleDownPending(data.double_down_pending);` after the existing `wheel_probabilities` / `gravity_drift` handlers.
  2. **Failure branch** (app.jsx:3866-3872): restored `setActiveWheelMode(prev)`, `setWheelProbabilities(null)` already there, but also need to read the previous values for `wagerStreak`, `wagerInsuranceArmed`, `doubleDownPending`, `gravity_drift` BEFORE the optimistic update and restore them on `!ok`. Added the four capture lines before `setActiveWheelMode(mode)` and the four restore lines after `setActiveWheelMode(prev)`.
- **Acceptance criteria:**
  1. Arm Double Down → `doubleDownPending=true` in UI → click Mirror → "⚡ Double-Down armed!" indicator disappears.
  2. Arm Insurance (with charges available) → `wagerInsuranceArmed=true` → click another mode → "🛡️ Insurance ARMED" indicator disappears.
  3. Build a Hot Streak (3+ wins) → click another mode → "🔥 Hot Streak: N" indicator disappears.
  4. UI matches DB after every mode-switch: `wager_streak=0, wager_insurance_armed=false, double_down_pending=false, gravity_drift=0`.
  5. Failure path (e.g., mode not available this week) still rolls back the wager state if the optimistic update was applied — the panel reverts to its pre-click state.
  6. New file `tests/test_wheel_mode_response.py` with 3 tests (3 passed): the wheel-mode response includes the four reset fields when the mode changes; it includes the mode but not the reset fields when the mode is unchanged (no-op); `handleWheelModeChange` reads all four reset fields from the response data.
  7. The 208 prior tests still pass.
  8. No regression on the T97 R2 wheel canvas redraw or the T98 spin stake fix.

---

### T100: 1× wager position must always be zero-escrow (no risk)

- **Spec ref:** S13 / "Zero-escrow edge case" (spec line 230-237), `wager_unlock` shop item line 250
- **Status:** [~] (2026-06-23) — **SUPERSEDED by T102 (wager redesign).** User redesign 2026-06-23 replaces the 1× to 10× multiplier system with a 0% to 30% (initial) percentage system. The 1× = zero rule is no longer needed because 0% becomes a real slider position. Ticket kept for traceability but no work planned.
- **Discovered:** 2026-06-23 (user review of wager-stale fix — T98 — surfaced that 1× still escrows 2% of wins once `wager_unlock` is owned, contradicting the spec's "1x should not wager ANYTHING" intent)
- **Related ticket:** T70 (zero-escrow when `stake_wins` happens to floor to 0), T45 (v2 escrow model), T99 (panel state reset on mode change)
- **Bug ID:** B26
- **Parallel group:** P7-bugfix (single ticket)
- **Depends on:** T70
- **Files:**
  - `wagers.py` (`compute_stake_risk` at 20-34)
  - `game.py` (`_resolve_spin` inverted-mode branch at 396-409, normal-mode branch at 410-431)
  - `tests/test_1x_zero_escrow.py` (new file)
- **Symptom (B26):** A player who has purchased `wager_unlock` (500 wins) can move the slider to 1× and still have `stake_wins = floor(current_wins * 0.02 * 1)` escrowed on every spin. For a player with 50+ wins, that's 1+ win at risk per loss. This violates the spec's "1x should not wager ANYTHING" intent — the 1× position should always be zero-escrow, base payout, base loss, regardless of whether the player owns `wager_unlock` or how many wins they have.

  Repro:
  1. As `testerplay`, ensure `wager_unlock` is owned (yes, purchased earlier)
  2. Have 1000+ wins (yes, 46,088)
  3. Set slider to 1×, click spin
  4. Observe `wins -= floor(46088 * 0.02 * 1) = 921` debited on each spin (escrow)
  5. On a loss, the 921 wins are forfeited; on a win, the 921 wins are returned
  6. **This is real risk at the 1× position** — opposite of spec intent

  Pre-purchase (`wager_unlock` not owned): the `else 0` branch on game.py:414 forces `stake_wins = 0`, so 1× is already zero-escrow. The bug only manifests after purchase — which is the entire point of buying `wager_unlock` in the first place.

- **Diagnosis:** `compute_stake_risk(wins, stake)` in wagers.py:20-34 returns `floor(wins * 0.02 * stake)` for any stake including 1. There is no special-case for `stake == 1` (or `stake <= MIN_STAKE`). The spec's "zero-escrow edge case" (line 230-237) is implemented as a passive check ("if `stake_wins == 0` due to insufficient wins, the multiplier collapses to 1") but does NOT special-case the 1× slider position as a hard rule.

  Similarly in `game.py:398-402`, the inverted-mode branch computes `stake_losses = floor(losses * 0.02 * stake)` without special-casing stake=1. A player in inverted mode with 50+ losses who moves the slider to 1× still has 1+ loss escrowed per spin.

  The spec's design intent — confirmed by user feedback 2026-06-23 — is that 1× should be a true "safe" floor, with:
  - **No escrow** (`stake_wins = 0`, no debit)
  - **Payout = `base_payout * 1` = `base_payout`** (no multiplier)
  - **Loss = `base_loss * 1` = `base_loss`** (no multiplier)
  - **Hot streak and other bonuses still apply on top** (separate concept)
  - **Banked wins NOT at risk** (separate escrow system, not affected)

- **Fix options:**
  1. **In `compute_stake_risk` (wagers.py):** add `if stake <= MIN_STAKE: return 0` at the top. Cleanest, most localized, testable in isolation. The DD override path in game.py:424-425 (which uses `wager_last_win_amount`, not `compute_stake_risk`) is unaffected by this change — DD's own escrow path remains.
  2. **In `_resolve_spin` (game.py):** add a guard `if actual_stake <= 1: stake_wins = stake_losses = 0; effective_stake = 1` at the top of the escrow section, then short-circuit the rest. More invasive but more explicit at the call site.
  3. **In `game.py:414` normal-mode and `game.py:401` inverted-mode:** change the condition to `if stake > 1 and owns_wager_unlock: ... else 0`. Most surgical, no change to `compute_stake_risk`'s math.

  **Recommended: Option 1** (modify `compute_stake_risk`). Universal rule, single source of truth, easy to test in isolation, and the function name itself implies "risk per stake level" — no risk at the minimum level is consistent with the function's purpose.

  **For inverted mode:** also patch the inline math at `game.py:401-402` to special-case `stake == 1`, since the inverted branch doesn't call `compute_stake_risk` (it has its own inline `int(losses * 0.02 * actual_stake)`).

- **Open design question (TBD with user):** Does the Double-Down override (`game.py:424-425`, `stake_wins = wager_last_win_amount`) still fire at stake=1?
  - **Option A** (preserve DD always): DD override ignores stake position; if player has DD armed, they risk `wager_last_win_amount` regardless of slider. The user has explicitly opted into DD, so the 1× slider is overridden.
  - **Option B** (suppress DD at stake=1): DD override requires `actual_stake > 1`. At stake=1, DD is a no-op. Player must move to stake=2+ for DD to risk anything.

  **Recommendation: Option B** for spec consistency. "1x should not wager ANYTHING" includes DD — the player has to opt into risk by moving off 1×. If the user wants DD to be possible at 1×, they can arm DD then move the slider to 2+.

  **Default if user does not respond before work starts: Option B** (most consistent with the "no risk at 1×" rule).

  **User design clarification (2026-06-23):** "Double down should only work when there is an amount escrowed." This is a stronger rule than Option B — it ties DD's activation to the existence of escrow (`stake_wins > 0` in normal mode, `stake_losses > 0` in inverted mode), not to the stake slider position. Implications:
  1. At stake=1, escrow is always 0 (T100 fix), so DD is automatically a no-op.
  2. At stake=2+ with insufficient wins to escrow (i.e. `< 50` wins), the zero-escrow edge case also applies and DD is also a no-op.
  3. The DD override at `game.py:424-425` (`stake_wins = wager_last_win_amount`) must be guarded with an additional check: it should only fire if the normal escrow path would have produced a non-zero amount. Otherwise, a player at stake=1 with DD armed and a non-zero `wager_last_win_amount` could DD with no escrow — violating the rule.
  4. Implementation: change `if double_down_active and owns_wager_unlock and wager_last_win_amount > 0:` to `if double_down_active and owns_wager_unlock and wager_last_win_amount > 0 and stake_wins > 0:`. The `stake_wins > 0` check ensures the player is actually in a wagered state before DD can take over.
  5. Same guard for inverted mode at `game.py:406`: add `stake_losses > 0` to the condition.

- **Acceptance criteria:**
  1. As `testerplay` (owns `wager_unlock`, 46,088 wins), set slider to 1×, click spin. Server-side `stake_wins = 0` and `effective_stake = 1`. No wins debited.
  2. As `testerplay`, set slider to 2×, click spin. Server-side `stake_wins = floor(46088 * 0.02 * 2) = 1843`. Escrow works as before.
  3. As `testerplay`, set slider to 10×, click spin. Server-side `stake_wins = floor(46088 * 0.02 * 10) = 9217`. Escrow works as before.
  4. In inverted mode, same: 1× escrows 0 from losses, 2× escrows `floor(losses * 0.02 * 2)`.
  5. Unit test: `compute_stake_risk(1000, 1) == 0`.
  6. Unit test: `compute_stake_risk(1000, 2) == 40` (existing behavior preserved — `floor(1000 * 0.02 * 2) = 40`).
  7. DD interaction per chosen design (A or B) — tested.
  8. Mirror mode at stake=1: `stake_wins = 0 * 2 = 0` (already 0, no change).
  9. The 211 prior tests still pass.
  10. New file `tests/test_1x_zero_escrow.py` with at least 5 tests: 1× normal, 2× regression, 10× regression, 1× inverted, 1× DD-suppressed (or DD-preserved per chosen design).

- **Impact:**
  - Existing player behavior at 1× changes: no more 2% of wins at risk per loss. This is the intended fix.
  - All other stakes (2-10) unchanged.
  - Mirror mode doubling at stake=1 still works: `0 * 2 = 0`.
  - Hot streak still builds on consecutive 1× wins (separate counter, no change).
  - Banked wins are NOT affected (separate escrow system, untouched by this fix).
  - DD behavior changes per chosen design (A or B).
  - The 1× floor is now a TRUE safety net — the player can always recover from a losing streak by dropping to 1×, rebuilding wins, then re-escalating.

---

# Phase 7 Implementation Plan (parallelization)

The T69–T96 tickets are organized into 10 implementation phases. Within each phase, tickets are executed by sub-agents in parallel where the file sets are disjoint. Between phases, the main agent audits all completed work before the next phase begins.

**Constraints applied to every phase:**
1. **No unfinished dependencies** — every ticket's `Depends on` chain must be fully done (status `[x]`) before that phase starts.
2. **Disjoint file sets within a phase** — parallel tickets must not edit the same file, to prevent merge conflicts.
3. **Serial work within a phase** — tickets that share files run serially under a single agent, in ticket-number order (Phase 6 cleanup precedent).
4. **Main-agent audit gate** — after every phase, the main agent runs `pytest` from `/home/user/wheel-app-staging/`, smoke-tests staging (HTTP 200), and verifies each ticket's acceptance criteria before unblocking the next phase.

**File-conflict matrix** (which tickets share files with which):

| File | Tickets that touch it |
|---|---|
| `migrations/047_hardening.sql` | T69 (alone) |
| `seasons.py` | T88 (alone) |
| `chat.py` | T81, T82, T92 |
| `chat_triggers.py` (new) | T82 (alone) |
| `static/app.jsx` | T73, T74, T75, T77, T79, T80, T81, T82, T89, T94, T95 — for T69–T96 subset: T73, T74, T75, T77, T79, T80, T81, T82, T89 |
| `game.py` | T70, T71, T72, T73, T74, T76, T77, T78, T79, T80, T82, T83, T85, T86, T87, T89, T90, T91, T94, T95 — for T69–T96 subset: T70, T71, T72, T73, T74, T76, T77, T78, T79, T80, T82, T83, T85, T86, T87, T89, T90, T91 |
| `wagers.py` | T70, T73, T74 |
| `models.py` | T74 (alone) |
| `wheel_modes.py` | T77, T78, T79 |
| `community_goals.py` | T84, T93 |
| `prestige.py` | T85, T86 |
| `replays.py` (delete) | T89 (alone) |
| `tests/test_replays.py` (delete) | T89 (alone) |
| `static/styles.css` | T96 (alone) |
| `static/js/wheel-modes.js` (new) | T80 (alone) |

`game.py` and `static/app.jsx` are the bottlenecks — most tickets touch them.

### Sub-phase 1: P7-foundation (5 parallel)

| Ticket | Files | Deps satisfied |
|---|---|---|
| **T69** Migration 047 — hardening columns | `migrations/047_hardening.sql` | T01 [x] |
| **T88** Onboarding rollover preservation (B10) | `seasons.py` | T02 [x] |
| **T91** Remove bounty "all 3" chat message (B21) | `game.py` (1-line delete) | T40 [x] |
| **T92** Chat rate limit + trim for system messages | `chat.py`, `tests/test_chat.py` | T17 [x] |
| **T93** Per-player cap race fix in `increment_goal` | `community_goals.py` | T28 [x] |

All file sets are disjoint. All dependencies already marked `[x]`. No work in this phase touches the same file as another.

**Main-agent audit at end of Sub-phase 1:** verify `pytest` passes, staging is HTTP 200, migration 047 applied, no regressions in T02's rollover behavior.

### Sub-phase 2: P7-auto-post-foundation (1 ticket, solo)

| Ticket | Files | Deps satisfied |
|---|---|---|
| **T82** Auto-post messages with configurable triggers | `chat_triggers.py` (new), `chat.py`, `game.py`, `static/app.jsx` | T17 [x], T06 [x] |

Solo because it touches 4 files (1 new + 3 existing) and creates the auto-post infrastructure that Sub-phases 3–5 depend on. T92 (Sub-phase 1) already added the throttling primitive; T82 wires up the trigger constants and per-event-kind dispatch. After this sub-phase, all chat auto-post plumbing is in place.

**Main-agent audit at end of Sub-phase 2:** verify `chat_triggers.py` constants are correct (matches spec §12), system messages post on the 8 trigger conditions, no duplicate fires.

### Sub-phase 3: P7-auto-post + UI (4 parallel)

| Ticket | Files | Deps satisfied |
|---|---|---|
| **T84** Community goal milestones (25/50/75%) | `community_goals.py` | T27 [x], T82 [x] |
| **T75** Wager panel always visible but disabled | `static/app.jsx` | T09 [x] |
| **T87** Onboarding step 5 (terminal transition) | `game.py` | T43 [x] |
| **T96** Wheel-wrapper height budget re-tune (depends T75) | `static/styles.css` | T75 — same sub-phase |

T96 starts after T75 completes (within the same sub-phase). All file sets are disjoint. T84 wires the auto-post to community goals (T82's foundation). T75/T96 deliver the wager panel + visual layout. T87 closes the onboarding gap.

**Main-agent audit at end of Sub-phase 3:** verify auto-post milestone messages fire at 25/50/75%, wager panel renders for all players (enabled/disabled correctly), onboarding step 4 → 5 transition grants 100 tokens, wheel-wrapper doesn't shrink viewport.

### Sub-phase 4: P7-chat-pagination + big-win (2 parallel)

| Ticket | Files | Deps satisfied |
|---|---|---|
| **T81** Chat history 200 messages + cursor pagination | `chat.py`, `static/app.jsx` | T17 [x] |
| **T83** Per-player escalating big-win threshold | `game.py` | T69 [x], T82 [x] |

T81 extends chat retention and adds scroll lazy-loading. T83 uses T69's `biggest_win_announced` column with T82's auto-post to fire escalating big-win messages. Disjoint files.

**Main-agent audit at end of Sub-phase 4:** verify 200-message retention works, cursor pagination `?before=<id>&limit=50` works, big-win message doesn't spam (escalating threshold gates correctly).

### Sub-phase 5: P7-auto-spin-path (1 ticket, solo)

| Ticket | Files | Deps satisfied |
|---|---|---|
| **T90** Auto-post messages to auto-spin path (B5) | `game.py` | T18 [x], T82 [x] |

Solo because it's a small focused change to the `/api/tick` endpoint and benefits from being a discrete commit. Adds message-posting to the auto-spin path so auto-spins that hit jackpots/big-wins still generate chat activity.

**Main-agent audit at end of Sub-phase 5:** verify auto-spin jackpots post messages, auto-spin hot-streak 10 posts message, no regression in auto-spin cap behavior (T18).

### Sub-phase 6: P7-wager-backend-core (5 serial, single agent)

| Ticket | Files | Deps satisfied |
|---|---|---|
| **T70** Zero-escrow edge case | `game.py`, `wagers.py` | T06 [x] |
| **T71** Hot streak resets to 0 on loss (B1) | `game.py` | T06 [x] |
| **T72** Banking guard (409 while `double_down_pending`) | `game.py` | T08 [x] |
| **T76** Mode-change resets | `game.py` | T08 [x], T10 [x] |
| **T78** Mirror mode full mechanic (double escrow) | `game.py`, `wheel_modes.py` | T11 [x] |

All 5 touch `game.py`. Executed by a single agent in ticket-number order (Phase 6 cleanup precedent — see top of Phase 6 section in this doc). T78 also touches `wheel_modes.py`, so the agent handles both files.

These are the core wager mechanics that all other wager tickets build on. T70 fixes the "can always spin at base outcome" guarantee. T71 closes the hot-streak-not-resetting bug. T72 prevents banking exploits. T76 prevents hot-streak gaming via mode hopping. T78 implements mirror mode's double-escrow mechanic.

**Main-agent audit at end of Sub-phase 6:** verify zero-escrow path (win with 0 wins → base payout), hot streak resets on loss, `/api/wager/bank` returns 409 when `double_down_pending`, mode change resets all state, mirror mode double-escrow + double-outcome resolution.

### Sub-phase 7: P7-wager-features (2 serial, single agent)

| Ticket | Files | Deps satisfied |
|---|---|---|
| **T73** Double-down rework (escrow `wager_last_win_amount`) | `game.py`, `wagers.py`, `static/app.jsx` | T69 [x], T08 [x] |
| **T74** Insurance rework (dice-charge model) | `game.py`, `models.py`, `wagers.py`, `static/app.jsx` | T69 [x], T08 [x] |

Both touch `game.py` + `wagers.py` + `static/app.jsx`. Serial under one agent. T74 also touches `models.py` (new constants). T73 reworks double-down to escrow the actual last win amount (not a percentage). T74 implements the dice-charge model with regen-on-timer, max 3, gamble-on-arm.

**Main-agent audit at end of Sub-phase 7:** verify double-down escrow uses `wager_last_win_amount`, insurance charges regen at 10 min/charge, insurance armed indicator shows in UI, safety net does NOT stack with insurance (B2).

### Sub-phase 8: P7-prestige (2 serial, single agent)

| Ticket | Files | Deps satisfied |
|---|---|---|
| **T85** Prestige scope update (wager tokens persist) | `game.py`, `prestige.py` | T13 [x] |
| **T86** `prestige_efficiency` as win retention only | `game.py`, `prestige.py` | T13 [x] |

Both touch `game.py` + `prestige.py`. Serial under one agent. T85 updates the prestige reset scope per spec §5.3 (wager tokens persist). T86 clarifies that `prestige_efficiency` retains wins only (not losses) and the cost threshold is not reduced.

**Main-agent audit at end of Sub-phase 8:** verify wager tokens survive prestige, `prestige_efficiency` keeps `floor(wins * 0.1 * level)`, prestige still costs 1M wins.

### Sub-phase 9: P7-wheel-modes (3 serial, single agent)

| Ticket | Files | Deps satisfied |
|---|---|---|
| **T77** Gravity mode full mechanic | `game.py`, `wheel_modes.py`, `static/app.jsx` | T11 [x], T69 [x] |
| **T79** Inverted mode full loss-farming | `game.py`, `wheel_modes.py`, `static/app.jsx` | T11 [x], T69 [x] |
| **T80** Dynamic wheel graphic (depends T77) | `game.py`, `static/app.jsx`, `static/js/wheel-modes.js` (new) | T11 [x], T77 — same sub-phase |

All 3 touch `game.py` + `wheel_modes.py` (T77, T79) or `game.py` + `static/app.jsx` (T80). Serial under one agent. T77 implements gravity drift mechanics. T79 implements the loss-farming inverted mode (most complex wheel mode). T80 implements the dynamic wheel graphic that reflects server-provided probabilities (depends on T77's drift-adjusted probabilities).

**Main-agent audit at end of Sub-phase 9:** verify gravity drift accumulates correctly, inverted mode escrows losses on the "win" outcome, dynamic wheel redraws when probabilities change, wheel label swap in inverted mode.

### Sub-phase 10: P7-cleanup (1 ticket, solo)

| Ticket | Files | Deps satisfied |
|---|---|---|
| **T89** Replay system complete removal | `replays.py` (delete), `tests/test_replays.py` (delete), `game.py`, `static/app.jsx` | T34 [x] |

Final cleanup. T82 (Sub-phase 2) auto-post system messages replace the replay system's role. T66 (HMAC-sign replay strings) is rendered moot by this ticket. Solo because it deletes files and would conflict with any concurrent `app.jsx` or `game.py` work.

**Main-agent audit at end of Sub-phase 10:** verify `replays.py` and `tests/test_replays.py` deleted, no `replay` references in `game.py` or `app.jsx` (except auto-post message renders), staging still HTTP 200, `pytest` passes.

---

### Sub-phase Summary

| Sub-phase | Tickets | Parallel? | Files in play |
|---|---|---|---|
| 1 | T69, T88, T91, T92, T93 | 5 parallel | disjoint |
| 2 | T82 | solo (foundation) | chat_triggers.py (new) + 3 existing |
| 3 | T84, T75, T87, T96 | 4 parallel (T96 after T75) | disjoint |
| 4 | T81, T83 | 2 parallel | disjoint |
| 5 | T90 | solo | game.py |
| 6 | T70, T71, T72, T76, T78 | 5 serial (1 agent) | all touch game.py |
| 7 | T73, T74 | 2 serial (1 agent) | both touch game.py + wagers.py + app.jsx |
| 8 | T85, T86 | 2 serial (1 agent) | both touch game.py + prestige.py |
| 9 | T77, T79, T80 | 3 serial (1 agent, T80 after T77) | all touch game.py |
| 10 | T89 | solo (cleanup) | file deletions + game.py + app.jsx |

**Total: 10 sub-phases, 28 tickets.** Sub-phases 1, 3, 4 are fully parallel. Sub-phases 6, 7, 8, 9 are serial (single agent per sub-phase). Sub-phases 2, 5, 10 are solo (single ticket each).

---

# Spec §23 Bug Cross-Reference

The following bugs are catalogued in `SEASON_8_BUILD_SPEC.md` §23 and addressed by
the tickets above. Use this as a quick lookup.

| Bug | Description | Location | Ticket | Status |
|---|---|---|---|---|
| B1 | `wager_streak` not reset on loss | `game.py:319-354` | T71 | [ ] |
| B2 | Insurance + safety net double-refund | `game.py:344-353` | T74 | [ ] |
| B3 | `should_generate_replay` hardcodes `double_down=False` | `game.py:864` | T89 | [ ] |
| B4 | `generate_replay` omits `double_down=` kwarg | `game.py:865-868` | T89 | [ ] |
| B5 | Auto-spin path never generates messages | `game.py:1161-1213` | T90 | [ ] |
| B6 | `/api/replay/share` doesn't post to chat | `game.py:3023-3037` | T89 | [ ] |
| B7 | No frontend "Share" button | `app.jsx` | T89 | [ ] |
| B8 | Replay card renders plain text | `app.jsx:2223-2233` | T89 | [ ] |
| B9 | `message_type` vocabulary mismatch | `app.jsx:2222` | T35 | [ ] |
| B10 | Rollover resets `onboarding_step` | `seasons.py:139` | T88 | [ ] |
| B11 | Step 2 onboarding advance not in `/api/wager/stake` | `game.py:2626` | T45 | [x] (in T43) |
| B12 | Step 3 onboarding advance not in `/api/reel` | `game.py:2099-2114` | T43 | [x] |
| B13 | `onboarding_step` never reaches 5 | `game.py` | T87 | [ ] |
| B14 | `fish_tropical` not auto-equipped | `game.py:2091-2092` | T43 | [x] |
| B15 | Insurance charge consumed on win | `game.py:2668-2671` | T74 | [ ] |
| B16 | `wager_insurance_armed` not in `/api/state` | `game.py:652-656` | T74 | [ ] |
| B17 | No "armed" indicator for insurance | `app.jsx:4224-4226` | T74 | [ ] |
| B18 | No rate limits on wager endpoints | `game.py:2571, 2629, 2650` | T08 | [x] (in T08) |
| B19 | Double-down tooltip misleading | `app.jsx:3722` | T73 | [ ] |
| B20 | Community goal milestones not posted | `community_goals.py` | T84 | [ ] |
| B21 | "All 3 bounties" message in chat | `game.py:2812` | T91 | [ ] |
| B22 | Wheel canvas does not redraw on mode change | `app.jsx:3317-3330` | T97 | [x] (in T97) |
| B23 | Spin uses stale `stake` from closure (slider=6 → spin sent 5) | `app.jsx:3552` | T98 | [x] (in T98) |
| B24 | Spin response missing `effective_stake` and `wager_last_stake` | `game.py:1333-1352` | T98 | [x] (in T98) |
| B25 | Wager panel UI doesn't update after mode switch (DD armed / insurance armed stay visible) | `app.jsx:3840-3872` | T99 | [x] (in T99) |
| B26 | 1× wager position still escrows 2% of wins after `wager_unlock` purchase | `wagers.py:20-34` | T100 | [~] (superseded by T102) |
| B27 | No UI indicator for current "stake value" (amount at risk on next spin) | `app.jsx:4355-4410` | T101 | [~] (superseded by T105) |
| B28 | Double-Down should be true all-or-nothing (currently insurance/safety net still fire) | `game.py:568-579` | T103 | [ ] |
| B29 | Wager system is opaque (0.02 × multiplier hard to reason about) | `wagers.py:20-34`, `game.py:380-431` | T102 | [ ] |
| B30 | Stake extension shop items missing (no way to unlock 35/40/45%) | `models.py:SHOP_ITEMS` | T104 | [ ] |
| B31 | Stake value not displayed in wager panel | `app.jsx:4355-4410` | T105 | [ ] |

---

### T101: Wager panel — show current "stake value" (amount at risk on next spin) at all times

- **Spec ref:** S13 wager system, missing UI element for live stake-value display
- **Status:** [~] (2026-06-23) — **SUPERSEDED by T105 (stake value display in redesigned percentage system).** The formula simplifies dramatically with T102's percentage-based redesign: `stake_value = floor(wins × stake_pct / 100)`. Ticket kept for traceability; the new T105 captures the simplified design.
- **Discovered:** 2026-06-23 (user feedback: "Can you also add a ticket to always show the current escrow amount (call it stake value, in the wager element at the bottom) at any time? This should be kept updated after each spin with the new amount.")
- **Related ticket:** T100 (1× = zero stake value), T98 (spin response includes `effective_stake` and `wager_last_stake`), T99 (wager panel state sync on mode switch)
- **Bug ID:** B27
- **Parallel group:** P7-bugfix (single ticket)
- **Depends on:** T100 (the displayed stake value must use the T100-zeroed-at-1x rule, not the old 2%-per-stake rule)
- **Files:**
  - `static/app.jsx` (wager panel JSX at 4355-4410, slider handler at 3813-3819, DD arm handler at 3960-3969)
  - `static/styles.css` (new `.wager-stake-value` styles)
  - `tests/test_stake_value_display.py` (new file)
- **User requirement (verbatim):** "Always show the current escrow amount (call it stake value, in the wager element at the bottom) at any time. This should be kept updated after each spin with the new amount."

---

### Background: what the wager system actually does on a spin (normal mode)

To make this ticket precise, here is the exact step-by-step. Say a player has 1,000 wins, slider at 5×, no Double-Down armed, no Hot Streak yet.

**Before the spin:**
- `wins = 1,000`
- `wager_streak = 0` (consecutive same-stake wins counter)
- `wager_banked_wins = 0` (the hot-streak bonus pool — empty)
- `wager_last_stake = 1` (whatever you used last time)
- `stake = 5` (current slider position)

**Step 1 — compute the stake value (the "escrow") and debit wins:**
- `stake_value = floor(1000 × 0.02 × 5) = 100`
- `wins = 1000 - 100 = 900` (you see 900 in your bank; the 100 is "in play")
- **This 100 is the amount at risk for THIS spin.** Returned to you on a win, forfeited on a loss. After T100: if `stake == 1`, this is always 0 regardless of wins or `wager_unlock` ownership.

**Step 2 — spin the wheel:**
- RNG rolls. One of: `win` (70% in Steady), `lose`, or `jackpot` (rare).

**Step 3 — resolve based on outcome:**

| Outcome | What happens to the 100 | What happens to wins | What happens to losses | Hot Streak effect |
|---|---|---|---|---|
| **win** | Returned: `wins += 100` | `wins += base_payout × effective_stake` (e.g. +20 wins) | unchanged | bonus portion of payout (5% × 20 = 1) goes to `wager_banked_wins` (not to your wins directly) |
| **lose** | Forfeited: gone | unchanged | `losses += base_loss × effective_stake` (e.g. +1) | `wager_streak = 0`, `wager_banked_wins = 0` (any accumulated bonus is wiped) |
| **jackpot** | Returned | `wins += base_payout × effective_stake × 5` (5× normal win) | unchanged | bonus portion goes to `wager_banked_wins` |

**Step 4 — the Bank button (separate, only on player action):**

The hot-streak bonus pool (`wager_banked_wins`) is **not** added to your `wins` automatically. It only gets realized when you click the **Bank** button (which appears as `🏦 Bank 3` once the pool is non-zero). If you don't bank and lose next spin, the pool is forfeited. That's the spec's "tension" (line 225-227): bank now (safe) or keep spinning (risk losing the bonus for a chance at a bigger streak).

**Net result of one 5× win (continuing the example):**
- `wins = 900 + 100 + 20 = 1020` (escrow returned + payout)
- `wager_streak = 1`
- `wager_banked_wins = 1` (the +5% bonus portion)
- `wager_last_stake = 5`, `wager_last_win_amount = 20`

**Net result of one 5× loss:**
- `wins = 900` (escrow forfeited — the 100 is GONE)
- `losses += 1`
- `wager_streak = 0`, `wager_banked_wins = 0` (everything wiped)
- `wager_last_win_amount = 0`

---

### Symptom (B27)

The wager panel currently shows:
- Stake slider (1× to 10×) with label "1× Safe" / "2× Safe" / "5× Bold" / etc.
- Hot Streak indicator (only when `wagerStreak > 0`)
- **Bank button** (only when `wagerBankedWins > 0 && !doubleDownPending`)
- Double-Down armed indicator (only when `doubleDownPending == true`)
- Insurance button / armed indicator

**What's missing:** a live display of the *current* stake value (the 100 in our example). Players can move the slider to 5× but have no way to see at a glance that they've just put 100 wins at risk. The only feedback is the post-spin toast.

Players currently have three options to learn the stake value:
1. Do the math manually: `floor(current_wins × 0.02 × stake)`
2. Spin and read the response toast
3. Reload the page (doesn't help — stake value is per-spin, not stored anywhere)

This makes the wager system feel opaque, especially for new players, and discourages experimentation with higher stakes.

---

### Definition of "stake value" (the value to display)

The stake value is the amount of wins (or, in inverted mode, losses) that would be debited from the player **on the next spin, given the current slider position and current wins/losses**. This is the "predicted escrow" — the same number that `_resolve_spin` computes as `stake_wins` (or `stake_losses` in inverted mode).

The formula mirrors `_resolve_spin`'s logic (game.py:398-431, wagers.py:20-34), with the T100 zero-at-1× rule applied:

```
stake_value = 0  if stake == 1
stake_value = 0  if not owns_wager_unlock  (and not in inverted mode)
stake_value = 0  if current_wins < 50 in normal mode  (2% × 1 floors to 0)
stake_value = wager_last_win_amount  if double_down_active and stake_wins > 0
stake_value = floor(current_wins × 0.02 × stake)  (normal mode, no DD)
stake_value = floor(current_losses × 0.02 × stake)  (inverted mode, no DD)
stake_value = wager_last_win_amount × 2  (mirror mode + DD)
```

Note: this is the stake value for the **NEXT** spin, not the previous spin's. The previous spin's escrow is already resolved (returned on win, forfeited on loss).

---

### Fix plan

1. **Server-side helper** (wagers.py, new function): extract a pure function `compute_stake_value(wins, losses, stake, owns_wager_unlock, is_inverted, dd_active, wager_last_win_amount) -> int` that returns the stake value per the formula above. Pure function, no DB access, easy to unit test. Used by both the spin handler (to set `stake_wins`/`stake_losses`) and the new `/api/state` response (to expose the current stake value).

2. **New response field** (game.py, state handler + spin handler): add `stake_value` to the response of `/api/state` and `/api/spin`. This is the live value the frontend should display — no need for the frontend to recompute. (The frontend CAN recompute it as a fallback if the field is missing, but the server is the source of truth.)

3. **Frontend state** (app.jsx): add a `stakeValue` state variable, initialized from `gameState.stake_value` and updated on:
   - Slider change (`handleStakeChange` at 3813-3819) — recompute locally (the slider position is local state; we don't want a server round-trip on every slider tick)
   - Spin completion — the response's `stake_value` is the new truth
   - `/api/state` refresh (after page load, after mode switch via T99) — the response's `stake_value` is the new truth
   - DD arm (`handleDoubleDown` at 3960-3969) — recompute locally, the DD override applies
   - Wins/losses update (e.g., after a non-wager spin, or after banking) — recompute locally

4. **Wager panel display** (app.jsx:4355-4410): add a new line *at the bottom* of the wager element (per user: "in the wager element at the bottom"), after the existing insurance / DD / bank indicators:
   - `💰 Stake value: 1,234` (normal mode, stake value in wins)
   - `💀 Stake value: 56` (inverted mode, stake value in losses)
   - `🛡️ No stake (safe)` (when stake value is 0 — i.e. at 1× per T100, or player lacks `wager_unlock`, or wins are too low)
   - `⚡ Stake value: 5,000 (Double-Down)` (when DD is armed and stake value is non-zero)

5. **Live update logic:** the displayed value must update *synchronously* on slider change (so the player sees the new amount immediately, before committing to a spin) and on spin completion. The slider's `handleStakeChange` already exists — adding one `setStakeValue` call there is enough. Spin completion already gets the response data — adding one more setState is enough.

6. **Tests** (test_stake_value_display.py, new file):
   - Unit test: `compute_stake_value(1000, 0, 1, True, False, False, 0) == 0` (T100 regression: 1× = 0)
   - Unit test: `compute_stake_value(1000, 0, 5, True, False, False, 0) == 100` (floor(1000 × 0.02 × 5))
   - Unit test: `compute_stake_value(1000, 0, 5, True, False, True, 200) == 200` (DD overrides)
   - Unit test: `compute_stake_value(1000, 0, 5, False, False, False, 0) == 0` (no wager_unlock)
   - Unit test: `compute_stake_value(0, 1000, 5, True, True, False, 0) == 100` (inverted mode, losses as source)
   - Unit test: `compute_stake_value(1000, 0, 5, True, False, False, 0)` at 10× = 200
   - Component test (frontend assertion): the JSX renders the stake value line with the correct format
   - Component test: the stake value updates on slider change (assertion in the JSX handler)
   - Live test: as `testerplay` with 46,088 wins, move slider to 5×, see "💰 Stake value: 4,608"

---

### Acceptance criteria

1. As `testerplay` (owns `wager_unlock`, 46,088 wins), set slider to 1×. Wager panel shows `🛡️ No stake (safe)` at the bottom.
2. As `testerplay`, set slider to 5×. Wager panel shows `💰 Stake value: 4,608` at the bottom (live, before any spin).
3. As `testerplay`, set slider to 10×. Wager panel shows `💰 Stake value: 9,217` at the bottom.
4. As `testerplay`, set slider to 1× again. Wager panel shows `🛡️ No stake (safe)` — the value updates **immediately** on slider change, not after a spin.
5. As `testerplay`, arm Double-Down with the slider at 5× (after a win has set `wager_last_win_amount`). Wager panel shows `⚡ Stake value: {wager_last_win_amount} (Double-Down)`.
6. As `testerplay`, complete a spin (win). The displayed stake value updates to reflect the new wins (e.g., 1020 wins × 0.02 × 5 = 102 stake value).
7. As `testerplay`, complete a spin (loss at 5×). The displayed stake value updates to reflect the reduced wins (e.g., 920 wins × 0.02 × 5 = 92 stake value).
8. In inverted mode, the display switches to `💀 Stake value: {amount}` using losses as the source.
9. If the player does not own `wager_unlock`, the display always shows `🛡️ No stake (safe)` regardless of slider position.
10. The 211 prior tests still pass.
11. New file `tests/test_stake_value_display.py` with at least 6 tests (4 server-side math, 2 frontend assertion).

---

### Display UX considerations

- Place the stake-value display **at the bottom** of the wager element (per user request), after the existing insurance / DD / bank indicators.
- Use a clear emoji prefix to distinguish normal mode (💰 wins) vs inverted mode (💀 losses) vs safe state (🛡️ no stake).
- When DD is armed, show the amount AND the reason (e.g., `⚡ Stake value: 5,000 (Double-Down)`) so the player knows why the value is what it is.
- The `🛡️ No stake (safe)` state should be visually distinct (greyed-out or with a shield emoji) to make it clear there's no risk on the next spin.
- The display should update **before** the next spin animation starts, not after, so the player sees what they're risking when they click spin.

---

### Implementation sketch (refined)

```jsx
// New helper in wagers.py:
def compute_stake_value(wins, losses, stake, owns_wager_unlock, is_inverted,
                       dd_active, wager_last_win_amount):
    """Return the wins/losses that would be escrowed on the next spin."""
    if stake <= 1:  # T100: 1× is always zero-escrow
        return 0
    if is_inverted:
        owns_wager_unlock_eff = True  # T79: inverted doesn't require wager_unlock
    else:
        owns_wager_unlock_eff = owns_wager_unlock
    if not owns_wager_unlock_eff:
        return 0
    if is_inverted:
        stake_value = int(max(0, losses) * 0.02 * stake)
    else:
        stake_value = int(max(0, wins) * 0.02 * stake)
    if dd_active and wager_last_win_amount > 0 and stake_value > 0:
        stake_value = wager_last_win_amount
    return stake_value

// In game.py state handler resp dict:
resp['stake_value'] = compute_stake_value(
    wins=gs.get('wins', 0),
    losses=gs.get('losses', 0),
    stake=gs.get('wager_last_stake', 1),  # last stake, not current slider
    owns_wager_unlock='wager_unlock' in gs.get('owned_items', []),
    is_inverted=gs.get('active_wheel_mode') == 'inverted',
    dd_active=gs.get('double_down_pending', False),
    wager_last_win_amount=gs.get('wager_last_win_amount', 0),
)

// In app.jsx, in the wager panel JSX (after the bank button, before the closing div):
<div className="wager-stake-value">
  {stakeValue > 0 ? (
    <span>
      {activeWheelMode === 'inverted' ? '💀' : '💰'} Stake value: {fmt(stakeValue)}
      {doubleDownPending && ' (Double-Down)'}
    </span>
  ) : (
    <span className="wager-no-stake">🛡️ No stake (safe)</span>
  )}
</div>
```

---

### Open design questions (TBD with user)

1. **Live update granularity:** should the stake value update LIVE as the slider drags, or only on slider release? The user said "at all times" which I interpret as live. The handler fires on `onChange` (not `onMouseUp`), so a one-line `setStakeValue` call inside `handleStakeChange` will make it live. If live updates feel jittery, we can switch to `onMouseUp` (slider release) without changing the API.

2. **Banked wins display:** the `🏦 Bank 3` button already shows the hot-streak bonus pool. Should the stake-value display *also* mention banked wins (e.g., `💰 Stake value: 100 (Bank: 3)`)? I lean toward keeping them separate — the bank button is the dedicated UI for that — but it's a one-line change if you want them combined.

3. **"At risk" vs "Wagered" wording:** the user said "stake value" — that's the wording I'll use. If you'd prefer "amount at risk" or "escrow" or just a number with no label, easy to swap.

---

### Impact

- Adds one new pure function (`compute_stake_value` in wagers.py) — easy to test, used by both server and frontend.
- Adds one new response field (`stake_value`) on `/api/state` and `/api/spin`.
- Adds one new state variable (`stakeValue`) and one new UI line in the wager panel.
- No regression on existing functionality.
- The wager system becomes more transparent — players can see what they're risking before they click spin.

---

### T102: Wager system redesign — flat-percentage stake instead of multiplier

- **Spec ref:** S13 (wager system overhaul — **spec updated 2026-06-23**), T45 (v2 escrow), T70 (zero-escrow — superseded), T100 (1× = zero — superseded)
- **Status:** [x] (2026-06-23) — **REWORKED per user design.** The initial T102 implementation (0-30% flat-percentage with `effective_stake = stake_pct / 100` as the multiplier) had a critical bug: at typical base_payout values, the integer truncation produced 0 payouts on every win, so the player could never come out ahead. The user proposed a simpler flow on 2026-06-23: **payout = the wager amount** (not base_payout × percentage). 100 wins, 10% stake, win → 110 wins (refund 10 + payout 10). All bonuses (regular win streak, hot streak, jackpot) are applied multiplicatively to the NET. Hot streak bonus portion is banked separately (legacy mechanic preserved per user "Keep bank button and bank the hot streak bonus separately"). Implementation: replaced `compute_wager_payout(base_payout, effective_stake, hot_streak_bonus)` with `compute_wager_payout(payout, hot_streak_bonus)` where `payout = stake_wins` (the wager) at stake > 0% or `base_payout` (effective_win_mult + win_streak_bonus) at 0%. Inverted mode uses the same pattern with `stake_losses` as the payout source. UI fix: hot streak indicator and bank button both gated on `wager_hot_streak` ownership (so players without the unlock don't see misleading streak text). **245 tests pass, 1 skipped.** Verified live in browser: 100K wins, 10% stake, win → 110K (player gains 10K = exactly the wager per the user's design). 4 wins in a row at 10%: +11K, +12.1K, +13.3K, then a loss = -14.6K (the wager). Hot streak bonus banked correctly (5/10/15/20/25% per consecutive win). T70, T100, T101, T105 close as implemented/merged. T103 (DD no-mitigation) is in flight. T104 shop UI display is a follow-up.
- **Discovered:** 2026-06-23 (user redesign: "the multiplier is simply a slider of how much value you want to stake... why is it multiplied by 0.02? This makes the numbers very anti-intuitive at a glance. This system feels overcomplicated.")
- **Related ticket:** T70 (superseded), T100 (superseded), T101 (superseded → T105), T103, T104, T105
- **Bug ID:** B29
- **Parallel group:** P7-bugfix (single, large)
- **Depends on:** None (this IS the redesign that other tickets depend on)
- **Files:**
  - `wagers.py` (replace `compute_stake_risk`, add `compute_stake_value`, new constants `MIN_STAKE_PCT=0`, `BASE_MAX_STAKE_PCT=30`, `STAKE_PCT_STEP=5`)
  - `game.py` (`_resolve_spin` at 380-431, `set_wheel_mode` at 3667, state handler, spin response at 1333-1352)
  - `models.py` (add 3 `wager_stake_extend_N` shop items)
  - `static/app.jsx` (stake slider 3780-3830, wager panel 4355-4410, tooltips)
  - `migrations/048_*.sql` (repurpose `wager_last_stake` semantics + add `wager_stake_pct` column if needed for clarity)
  - `tests/test_wager_redesign.py` (new file, ~20 tests)
  - `SEASON_8_BUILD_SPEC.md` (S13 section needs rewriting — note for user)

---

### The redesign

**Old system (current):**
- Slider: 1× to 10× (integer multiplier)
- `stake_value = floor(wins × 0.02 × stake)` — at 1× = 2% of wins, at 10× = 20% of wins
- The `× 0.02` factor and "multiplier" terminology make the actual risk hard to reason about
- `effective_stake` is the multiplier (1-10), used as a payout/loss multiplier
- T100's "1× = zero" was a special-case fix to make 1× truly safe

**New system (proposed):**
- Slider: **0% to 30%** (initial), with shop upgrades extending to 35% / 40% / 45%
- Steps: **5%** (discrete positions)
- `stake_value = floor(wins × stake_pct / 100)` — the displayed number IS the number
- `effective_stake = stake_pct / 100` (a fraction 0.00 to 0.45), used as the payout/loss multiplier
- 0% is the safe position: `stake_value = 0`, base payout, base loss
- No special-case for "zero escrow" — the player chooses 0% explicitly
- Slider length stays constant; upgrades add more tick positions to the right (5% step, more steps = higher max)

**Concrete example (1,000 wins):**
- 0% → stake 0, payout base 1, loss base 1
- 5% → stake 50, payout 0.05× base, loss 0.05× base
- 10% → stake 100, payout 0.10× base, loss 0.10× base
- 30% → stake 300, payout 0.30× base, loss 0.30× base
- 45% (with all upgrades) → stake 450, payout 0.45× base, loss 0.45× base

The number on the slider tells the player exactly what they're risking. "I'm putting 10% of my wins on this spin" is intuitive; "I'm putting 5× of my wins on this spin" was not.

---

### Migration from old to new

**`wager_last_stake` column** (currently INTEGER 1-10) — repurpose to hold the new stake percentage (0, 5, 10, 15, ..., 50):
- Old 1× → new 0% (matches the T100 spirit: 1× was effectively safe)
- Old 2× → new 5%
- Old 3× → new 10%
- ...
- Old 10× → new 45% (slight cap; existing 10× users lose 5% of their max range but gain the simpler UI)
- Migration SQL: `UPDATE game_state SET wager_last_stake = (wager_last_stake - 1) * 5`

**`MIN_STAKE` and `MAX_STAKE` constants** in `wagers.py`:
- Replace `MIN_STAKE=1, MAX_STAKE=10` with `MIN_STAKE_PCT=0, BASE_MAX_STAKE_PCT=30, STAKE_PCT_STEP=5`
- New dynamic: `MAX_STAKE_PCT = BASE_MAX_STAKE_PCT + 5 * (count of wager_stake_extend_N items owned)` (0 → 30, 1 → 35, 2 → 40, 3 → 45)

**`validate_stake(stake, owns_wager_unlock)`** in `wagers.py`:
- Old: returns stake clamped to [1, 10], or 1 if not owns_wager_unlock
- New: returns stake_pct clamped to [0, MAX_STAKE_PCT_FOR_PLAYER], rounded to nearest 5%, or 0 if not owns_wager_unlock

**`compute_stake_risk(wins, stake)`** in `wagers.py:20-34`:
- Old: `floor(wins × 0.02 × max(MIN_STAKE, min(MAX_STAKE, stake)))` (capped at wins)
- New: `int(max(0, wins) × min(MAX_STAKE_PCT, stake) / 100)` (capped at wins, no `× 0.02`)

**`effective_stake` semantics**:
- Old: the multiplier (1-10), used as a payout/loss multiplier (e.g., payout = base_payout × 5)
- New: the percentage as a fraction (0.0 to 0.45), used as a payout/loss multiplier (e.g., payout = base_payout × 0.10)
- All call sites that use `effective_stake` continue to work — the multiplier is just smaller

**Spin response** (game.py:1333-1352, per T98 fix):
- `resp['stake']` — keep, but now stores `stake_pct` (0-50)
- `resp['effective_stake']` — keep, but now stores `stake_pct / 100` (0.0-0.45)
- `resp['wager_last_stake']` — keep, but now stores `stake_pct` (0-50)

**Inverted mode** (game.py:398-409) — same percentage applies to `current_losses` instead of `current_wins`:
- `stake_losses = int(max(0, losses) × stake_pct / 100)`
- Effective stake (loss-farming multiplier) = stake_pct / 100

**Mirror mode** (game.py:418-419) — same as old: doubles the stake value:
- Old: `stake_wins = stake_wins * 2`
- New: `stake_wins = stake_wins * 2` (still works since `stake_wins = int(wins × stake_pct / 100) × 2` = `int(wins × 2 × stake_pct / 100)`)

---

### Impact on other mechanics

**Hot Streak** (T70, game.py:586-625, wagers.py compute_wager_payout):
- Old: `payout += base_payout × effective_stake × hot_streak_bonus` (e.g., +25% on a 5-streak at 5× = +1.25× base)
- New: this formula still works mechanically, but the values are ~50× smaller. To preserve the "feel" of hot streak as a meaningful bonus, change the bonus to apply to the **stake return** instead of the payout multiplier:
- New formula: on a hot-streak win, `wager_banked_wins += int(stake_value × hot_streak_bonus)` (e.g., 10% stake (100 wins) with 5-streak (+25%) → banked bonus = 25 wins)
- This keeps the bonus in the same ballpark as before, just expressed as a flat amount
- The bank button still banks `wager_banked_wins` as before

**Insurance** (T74, game.py:568-574):
- Old: caps loss at `effective_stake` (multiplier of base_loss)
- New: caps loss at `int(base_loss × effective_stake)` = `int(base_loss × stake_pct / 100)` — a much smaller cap, but proportional to the percentage. At 30% with insurance, you lose at most 30% of base_loss.
- (Insurance does NOT fire on Double-Down — see T103.)

**Safety Net** (T72, game.py:578-579):
- Old: at 5×+ stake, refunds 25% of `stake_wins`
- New: at **15%+** stake (per user), refunds 25% of `stake_value`
- Implementation: change the threshold check from `actual_stake >= 5` to `stake_pct >= 15`
- 25% of stake value is returned to the player on a loss

**Double-Down** — see T103 (separate ticket; DD is a "true all-or-nothing" that sidesteps the percentage system entirely)

**Mirror mode** — unchanged: doubles the stake value, take-better mechanic
**Inverted mode** — unchanged in structure: percentage applies to losses instead of wins
**Bank button** — unchanged: banks `wager_banked_wins` (with new bonus formula above)

---

### UI changes

**Slider** (app.jsx, current at 3780-3830):
- Replace `<input type="range" min="1" max="10" step="1" value={stake}>` with `<input type="range" min="0" max={maxStakePct} step="5" value={stakePct}>` where `maxStakePct` is computed from the player's owned upgrades
- The slider's visual width stays the same; more tick positions are added as the player upgrades
- The label next to the slider (currently "1× Safe" / "5× Bold" / "10× All-in") becomes a percentage label:
  - 0% → "Safe"
  - 5-10% → "Cautious" (or just the %)
  - 15-20% → "Bold" (or just the %)
  - 25-30% → "Risky" (or just the %)
  - 35-45% → "All-in" (or just the %)
- The user said the labels should reflect the new system — I'll propose simple `{stakePct}%` for v1 and add the "Safe / Bold" tags in a follow-up if desired.

**Stake value display** (T105) — see separate ticket. The new display shows the live stake value with the percentage:
- `💰 Stake value: 100 (10% of 1,000 wins)` (normal mode)
- `💀 Stake value: 50 (10% of 500 losses)` (inverted mode)
- `🛡️ No stake (safe)` (when stake_pct == 0)
- `⚡ Stake value: 5,000 (Double-Down)` (when DD is armed — see T103)

**Shop** — see T104 for the 3 new `wager_stake_extend_N` items.

---

### Acceptance criteria

1. Migration: existing players with `wager_last_stake` = 1-10 are migrated to 0, 5, 10, ..., 45 respectively. Verified by checking a known user before/after the migration.
2. Slider: initial max is 30% (positions 0, 5, 10, ..., 30, 7 positions). With wager_stake_extend_1, max is 35% (8 positions). With all 3, max is 45% (10 positions).
3. Player without `wager_unlock`: slider is locked at 0% (no positions selectable).
4. `compute_stake_risk(1000, 10) == 100` (10% of 1000 wins).
5. `compute_stake_risk(1000, 0) == 0` (0% is always zero).
6. `compute_stake_risk(1000, 30) == 300` (30% of 1000 wins).
7. `compute_stake_risk(0, 30) == 0` (no wins to risk, even at max percentage).
8. Spin with stake_pct=10 at 1000 wins: stake_value = 100 debited, win returns 100 + base_payout × 0.10, loss forfeits 100 + base_loss × 0.10 added to losses.
9. Spin with stake_pct=0 at 1000 wins: stake_value = 0, win returns 0 + base_payout × 1, loss adds base_loss × 1 to losses. No risk.
10. Hot Streak: 5-streak at 10% stake = 25 wins banked (was 1.25× base_payout before).
11. Insurance: at 10% stake, loss capped at `int(base_loss × 0.10)`.
12. Safety Net: at 15% stake, loss refunds 25% of stake_value. At 10% stake, no safety net fires.
13. Mirror mode at 10% stake: stake_value = 200, take-better mechanic, refund on win, forfeit on double-loss.
14. Inverted mode at 10% stake: stake_value = `int(losses × 0.10)`, deducted from losses; refund + base_loss × 0.10 on 'lose' outcome (good).
15. Spin response includes `stake`, `effective_stake` (now 0.0-0.45), and `wager_last_stake` (now 0-50).
16. Slider UX: 5% steps, fixed visual length, more positions added with upgrades.
17. The 211 prior tests still pass (after rewriting the wager tests for the new formula).
18. New file `tests/test_wager_redesign.py` with at least 15 tests covering: migration, slider, compute_stake_risk, spin resolution, hot streak formula, insurance, safety net, mirror, inverted, double-down (see T103).

---

### Spec rewrite note

The user is the spec author. The `SEASON_8_BUILD_SPEC.md` S13 section needs to be updated to reflect the new percentage system. Options:
1. **I rewrite S13** as part of T102 implementation. You review and approve.
2. **You rewrite S13** yourself, and I implement T102 against your updated spec.

Either way, the spec should be the source of truth before T102 is marked done. Recommendation: **option 1** (I write a draft, you review) to keep momentum.

---

### Impact

- The wager system becomes dramatically more transparent — players can see exactly what they're risking.
- All existing wager tests need to be rewritten with the new formula (most are 1-line changes).
- The spec needs a corresponding rewrite (S13 section).
- Migration is a single SQL UPDATE (no downtime, no data loss beyond the 10× → 45% cap).
- Shop becomes 2 more expensive (4 wager items total: unlock + 3 extends) — better progression for the wager system.

---

### T103: Double-Down as true all-or-nothing (no loss mitigation)

- **Spec ref:** S13 double-down mechanic, T73 (current DD implementation — significantly reworked by this ticket)
- **Status:** [ ]
- **Discovered:** 2026-06-23 (user redesign: "this should be a ridiculous snowball mechanic with insanely high risk, truly all or nothing. I think in the same vein, insurance should NOT work on double downs, this would be far too safe. I think double down should not work with ANY form of loss mitigation and should be a true spin of the wheel (only outcome counts).")
- **Related ticket:** T73 (current DD — mostly superseded by behavior change), T74 (insurance), T72 (safety net), T102 (wager redesign)
- **Bug ID:** B28
- **Parallel group:** P7-bugfix (single)
- **Depends on:** T102 (new percentage system)
- **Files:**
  - `game.py` (DD override at 424-425 and inverted-mode DD at 406-407, all mitigation paths in `lose` branches)
  - `static/app.jsx` (DD tooltip text at 3835-3845, DD button label at 3960-3969)
  - `tests/test_double_down_all_or_nothing.py` (new file)

---

### The redesign

**Current behavior (T73):**
- DD escrows `wager_last_win_amount` (the actual last payout)
- On a DD win: returns the escrow + 2× base_payout (or 2× the last win amount in some versions)
- On a DD loss: forfeits the escrow + insurance MAY fire (capping the loss) + safety net MAY fire (refunding 25%) + guard/shield/resilience MAY fire

**New behavior (per user, 2026-06-23):**
1. **DD stakes `wager_last_win_amount`** — the entire previous win. The percentage slider position is **completely ignored** for that spin. The amount wagered may exceed what the player's max percentage would normally allow (e.g., a player capped at 30% can DD with 45% of their wins if their last win was 45% of their bankroll). This is the "ridiculous snowball" — the risk grows with each successful DD chain.
2. **No loss mitigation fires on a DD spin.** Specifically:
   - ❌ **Insurance does NOT fire** (per user, "this would be far too safe")
   - ❌ **Safety Net does NOT fire** (per user, same reasoning — applies regardless of stake_pct)
   - ❌ **Guard does NOT fire** (per user, "should not work with ANY form of loss mitigation")
   - ❌ **Shield (regen_shield) does NOT fire** (same)
   - ❌ **Resilience does NOT fire** (same)
   - ✅ **Only the win/lose/jackpot outcome matters** ("true spin of the wheel")
3. **Payout on a DD win:** the standard "DD win" formula (escrow returned + payout). The exact multiplier is up to design — see options below.
4. **Tooltip update** — communicate the "no protections" rule to the player.

**DD payout options (your call):**
- **A.** Payout = base_payout × 2 (double the base, regardless of DD stake amount). Simple, predictable.
- **B.** Payout = stake_value × 2 (double the amount you staked). The DD risk and reward scale together.
- **C.** Payout = base_payout + (stake_value - base_payout) (the "leftover" from the previous spin). Most faithful to the current "you win your last win amount" logic.

Recommendation: **Option A** for simplicity. The player understands "DD = 2× base_payout, no protections, true all-or-nothing".

---

### Implementation

**Server-side** (game.py):

```python
# In _resolve_spin(), in the normal-mode branch (line 410-431):
# Existing logic computes stake_wins via compute_stake_risk or via DD override.
# The new rule: if DD is active, ALL loss-mitigation paths in the 'lose' branch
# must be guarded with `if not double_down_active`.

# Add a top-level flag:
dd_active = double_down_active and stake_wins > 0  # DD only valid if escrow > 0

# In the 'lose' branch (line 537-579), wrap each mitigation with `not dd_active`:
if not dd_active and 'regen_shield' in owned and regen_recharge_wins == 0:
    # shield logic
elif not dd_active and 'guard' in owned:
    # guard logic
else:
    # normal loss path (no mitigations if dd_active)
    ...
    if not dd_active and insurance_active:
        # insurance logic
    ...
    if not dd_active and 'wager_safety_net' in owned:
        # safety net logic
```

Same pattern for inverted mode at game.py:440-535.

**Payout on DD win** (line 580-625):
- Currently: `wins += direct_wins + (escrow returned if win)` — DD doesn't change the payout formula, just the escrow
- New: payout calculation unchanged, but mitigation paths (insurance capping, etc.) must also be guarded
- For Option A: `direct_wins = int(base_payout × 2 × effective_stake)` where `effective_stake = 1` for DD (since DD uses the actual stake_value, not the percentage multiplier)

**Insurance spec update** (wagers.py and game.py):
- Current: insurance is "armed" via the Insurance button, then fires on the next loss
- New: insurance does NOT arm if DD is armed. If a player arms DD while insurance is already armed, insurance is consumed but does nothing (or is auto-disarmed — your call).
- Implementation: in the Insurance arm handler, if `double_down_active`, return an error or auto-disarm. In the loss branch, the `not dd_active` guard handles the rest.

**Guard/Shield/Resilience** (these are NOT wager items but general protection items):
- These currently fire on any loss
- New: do not fire on DD losses
- Implementation: same `not dd_active` guard in the loss branch

---

### UI changes

**Tooltip** (app.jsx, around 3835-3845 where the wager system is explained):

Current tooltip (rough): "Wager: stake multiplier 1×-10×. Hot Streak: consecutive wins +5% bonus. Safety Net: 25% refund at 5×+ stake. Double-Down: risk your last winnings for a chance to double them. Insurance: protects next spin."

New tooltip (proposed):
```
Wager Slider: 0% (safe) to 30% (max). Upgrades extend to 45%.
- 0% = no risk, base payout
- Each step = 5% of your wins (or losses in inverted mode)

Hot Streak: consecutive same-stake wins earn +5% bonus per win (max +50%),
bankable at any time. Bank button appears when bonus > 0.

Safety Net: at 15%+ stake, refund 25% of lost stake on a loss.

Double-Down: ⚠️ ALL OR NOTHING. Wager your entire last win for a 2× payout.
NO INSURANCE. NO SAFETY NET. NO PROTECTIONS. True spin of the wheel —
only the outcome counts.

Insurance: guarantees no loss on next spin (consumes a charge).
Does NOT apply to Double-Down spins.
```

**DD button** (app.jsx, around 3960-3969):
- The button label can stay "⚡ Arm Double Down" / "⚡ Double-Down armed!"
- Add a warning indicator when DD is armed: ⚠️ "All-or-nothing — no protections"
- The "armed" indicator could include a shield-with-slash icon to emphasize the no-mitigation rule

**Shop item description** (models.py, `wager_double_down`):
- Current: "Arm 2x stake for next spin"
- New: "⚠️ Wager your entire last win for a 2× payout. NO INSURANCE, SAFETY NET, OR PROTECTIONS. True all-or-nothing. Sidesteps your normal stake %."

---

### Acceptance criteria

1. Arm Double-Down (DD) with the slider at any position (0% to 45%). DD stakes `wager_last_win_amount`, NOT `floor(wins × stake_pct / 100)`.
2. The DD spin can stake more than the player's max percentage would allow (e.g., DD at 30% cap can still stake 45% of wins if the last win was 45% of bankroll). Verified by setting `wager_last_win_amount` to 45% of `wins` via direct DB and observing the DD spin stakes that amount.
3. On a DD loss: insurance does NOT fire. Safety net does NOT fire. Guard does NOT fire. Shield does NOT fire. Resilience does NOT fire. Only the base loss is added to `losses`.
4. On a DD win: payout is 2× base_payout (or per chosen option), escrow is returned, standard hot-streak bonus applies.
5. Hot Streak increments on a DD win (same-stake rule doesn't apply since DD is special).
6. If a player has DD armed AND insurance armed, the next DD spin does NOT consume the insurance charge (or does consume it but does nothing — your call). Test both options.
7. Tooltip displays the "no protections" rule clearly. Shop item description is updated.
8. DD is a no-op if `wager_last_win_amount == 0` (no prior win to risk). The button is disabled or shows "no prior win".
9. The 211 prior tests still pass (some T73 tests may need updating for the no-mitigation rule).
10. New file `tests/test_double_down_all_or_nothing.py` with at least 8 tests:
    - DD stakes wager_last_win_amount, not percentage
    - DD does not fire insurance on loss
    - DD does not fire safety net on loss
    - DD does not fire guard on loss
    - DD does not fire shield on loss
    - DD does not fire resilience on loss
    - DD can exceed max percentage
    - DD is no-op when wager_last_win_amount == 0

---

### Impact

- DD becomes a true high-risk high-reward play. Players can snowball wins or lose everything in one spin.
- The "insurance + DD" combo is no longer possible, eliminating a safe-DD exploit.
- Tooltip and shop descriptions are updated to set correct player expectations.
- All existing DD tests need updating for the no-mitigation rule.
- The wager system as a whole becomes more "honest" — each mechanic has clear, non-overlapping rules.

---

### T104: Stake extension shop upgrades (3 items, +5% each)

- **Spec ref:** S13 (wager system), user redesign 2026-06-23: "Upgrade path providing 5%, 10 then 15"
- **Status:** [ ]
- **Discovered:** 2026-06-23 (user redesign of stake system)
- **Related ticket:** T102 (wager redesign), T105 (stake value display)
- **Bug ID:** B30
- **Parallel group:** P7-bugfix (single)
- **Depends on:** T102
- **Files:**
  - `models.py` (add 3 items to `SHOP_ITEMS`)
  - `migrations/048_*.sql` (no migration needed — items are code-defined)
  - `static/app.jsx` (shop panel auto-discovers new items, no JSX change needed)
  - `tests/test_stake_extensions.py` (new file)

---

### The new shop items

**Item 1: `wager_stake_extend_1`**
- Cost: 5,000 wins
- Tier: 2 (requires `wager_unlock`)
- Effect: extends the max stake from 30% to 35%
- Description: "Extend max stake from 30% to 35%. Each upgrade adds 5% more risk capacity."

**Item 2: `wager_stake_extend_2`**
- Cost: 15,000 wins
- Tier: 3 (requires `wager_stake_extend_1`)
- Effect: extends the max stake from 35% to 40%
- Description: "Extend max stake from 35% to 40%."

**Item 3: `wager_stake_extend_3`**
- Cost: 40,000 wins
- Tier: 4 (requires `wager_stake_extend_2`)
- Effect: extends the max stake from 40% to 45%
- Description: "Extend max stake from 40% to 45%."

**User's "5%, 10, 15" reading** — this is interpreted as 3 upgrades of +5% each (5/10/15 cumulative), max 30% → 35% → 40% → 45%. If the user wanted different extensions (e.g., +5/+10/+15 for max 60%), they can correct this ticket.

**Note on max:** the user's earlier message said "up to 50%" but the "5%, 10, 15" pattern gives 45%. Confirming 45% as the max — if 50% is still desired, add a 4th upgrade of +5% (tier 5, 100,000 wins). I went with 3 upgrades per the most recent message.

---

### Implementation

**models.py** — add to `SHOP_ITEMS`:

```python
{
    'id': 'wager_stake_extend_1',
    'name': 'Stake +5% (Tier 1)',
    'cost': 5000,
    'tier': 2,
    'requires': 'wager_unlock',
    'desc': 'Extend max stake from 30% to 35%.',
},
{
    'id': 'wager_stake_extend_2',
    'name': 'Stake +5% (Tier 2)',
    'cost': 15000,
    'tier': 3,
    'requires': 'wager_stake_extend_1',
    'desc': 'Extend max stake from 35% to 40%.',
},
{
    'id': 'wager_stake_extend_3',
    'name': 'Stake +5% (Tier 3)',
    'cost': 40000,
    'tier': 4,
    'requires': 'wager_stake_extend_2',
    'desc': 'Extend max stake from 40% to 45%.',
},
```

**game.py / state handler** — `MAX_STAKE_PCT` computation:
```python
extend_count = sum(1 for item in ['wager_stake_extend_1', 'wager_stake_extend_2', 'wager_stake_extend_3']
                   if item in owned_items)
max_stake_pct = BASE_MAX_STAKE_PCT + (extend_count * 5)  # 30 → 35 → 40 → 45
resp['max_stake_pct'] = max_stake_pct
```

**Frontend** (app.jsx, slider component):
```jsx
const maxStakePct = (gameState.max_stake_pct || 30);  // from state response
<input type="range" min="0" max={maxStakePct} step="5" value={stakePct} ... />
```

The slider length stays the same in the layout — more tick positions are added as the max grows (per user: "with the upgrades simple adding more steps to the slider (not changing length)").

---

### Acceptance criteria

1. Player with no stake extensions: slider max = 30% (positions 0, 5, 10, ..., 30, 7 positions).
2. Player with `wager_stake_extend_1`: slider max = 35% (8 positions).
3. Player with `wager_stake_extend_1` + `wager_stake_extend_2`: slider max = 40% (9 positions).
4. Player with all 3 extensions: slider max = 45% (10 positions).
5. Items are gated by `requires`: `extend_2` requires `extend_1`, `extend_3` requires `extend_2`. UI hides the "Buy" button if the prerequisite is missing.
6. Items have the right costs in the shop panel.
7. Items persist correctly: buying `extend_1`, refreshing the page, max stake is still 35%.
8. The 211 prior tests still pass.
9. New file `tests/test_stake_extensions.py` with at least 4 tests:
   - `compute_max_stake_pct(owned_items)` returns correct value for each combination
   - Shop panel displays the 3 new items
   - Items are gated by `requires` correctly
   - The migration from old max (10) to new max (30 + 5*N) doesn't break

---

### Impact

- Wager system has a clearer progression: 500 (unlock) → 5K (extend 1) → 15K (extend 2) → 40K (extend 3) = ~60K total for max wager access. Reasonable cost curve.
- The slider's UX is improved (more positions, fixed width).
- Shop panel auto-discovers the items (no manual UI wiring needed for the panel itself).
- The wager system has 4 items total (unlock + 3 extends), making it a meaningful sub-progression within the shop.

---

### T105: Stake value display in wager panel (T101 update for redesigned system)

- **Spec ref:** S13 (wager system)
- **Status:** [ ]
- **Discovered:** 2026-06-23 (T101 user request, updated for T102's redesign)
- **Related ticket:** T101 (superseded by this ticket), T102 (wager redesign)
- **Bug ID:** B31
- **Parallel group:** P7-bugfix (single)
- **Depends on:** T102 (new percentage system)
- **Files:**
  - `wagers.py` (new `compute_stake_value` helper, sibling to `compute_stake_risk`)
  - `game.py` (state handler + spin response include `stake_value` and `max_stake_pct`)
  - `static/app.jsx` (new wager panel line at 4355-4410, slider handler updates `stakeValue` state)
  - `tests/test_stake_value_display.py` (new file)

---

### The new display

**Current state of the wager panel** (app.jsx:4355-4410):
- Stake slider (1× to 10×) with label
- Hot Streak indicator (when `wagerStreak > 0`)
- Bank button (when `wagerBankedWins > 0 && !doubleDownPending`)
- Double-Down armed indicator (when `doubleDownPending == true`)
- Insurance button / armed indicator
- **No display of the current stake value** (the new system's "escrow" amount)

**New line at the bottom of the wager element** (per user: "in the wager element at the bottom"):

```
Stake value: 100        (10% of 1,000 wins)
```

or in the safe state:

```
🛡️ No stake (safe)
```

or with DD armed:

```
⚡ Stake value: 5,000  (Double-Down)
```

**Three display states:**

| State | Format | Example |
|---|---|---|
| Normal mode, stake_pct > 0 | `💰 Stake value: {amount} ({pct}% of {wins} wins)` | `💰 Stake value: 100 (10% of 1,000 wins)` |
| Inverted mode, stake_pct > 0 | `💀 Stake value: {amount} ({pct}% of {losses} losses)` | `💀 Stake value: 50 (10% of 500 losses)` |
| Double-Down armed | `⚡ Stake value: {wager_last_win_amount} (Double-Down)` | `⚡ Stake value: 5,000 (Double-Down)` |
| Safe (stake_pct == 0) | `🛡️ No stake (safe)` | `🛡️ No stake (safe)` |

Note: the DD row REPLACES the normal row when DD is armed (since DD stakes the actual last win, not the percentage).

---

### Formula (much simpler with T102)

```python
# New helper in wagers.py:
def compute_stake_value(wins, losses, stake_pct, owns_wager_unlock, is_inverted,
                        dd_active, wager_last_win_amount):
    """Return the wins/losses that would be escrowed on the next spin.
    
    Returns 0 if:
    - stake_pct == 0
    - not owns_wager_unlock (and not in inverted mode)
    - DD is armed but wager_last_win_amount == 0 (no prior win)
    
    For DD: returns wager_last_win_amount (sidesteps the percentage system).
    Otherwise: returns floor(wins_or_losses * stake_pct / 100).
    """
    if dd_active and wager_last_win_amount > 0:
        return wager_last_win_amount
    if stake_pct == 0:
        return 0
    if is_inverted:
        owns_wager_unlock_eff = True  # T79: inverted doesn't require wager_unlock
    else:
        owns_wager_unlock_eff = owns_wager_unlock
    if not owns_wager_unlock_eff:
        return 0
    base = losses if is_inverted else wins
    return int(max(0, base) * stake_pct / 100)
```

**Much simpler than the old T101 formula** (which had to handle the `0.02 × multiplier` math).

---

### State updates (frontend)

The `stakeValue` state is updated on:
- **Slider change** (`handleStakeChange`) — compute locally from the new `stake_pct` and current `wins`/`losses`
- **Spin completion** — the response's `stake_value` is the new truth
- **`/api/state` refresh** — the response's `stake_value` is the new truth
- **DD arm** (`handleDoubleDown`) — if DD is armed, stake_value jumps to `wager_last_win_amount`
- **Mode switch** (T99) — the response's `stake_value` is updated for the new mode
- **Wins/losses update** (e.g., after a non-wager spin, after banking) — recompute locally

---

### Acceptance criteria

1. As `testerplay` (owns `wager_unlock`, 46,088 wins), set slider to 0%. Wager panel shows `🛡️ No stake (safe)` at the bottom.
2. As `testerplay`, set slider to 10%. Wager panel shows `💰 Stake value: 4,608 (10% of 46,088 wins)` at the bottom (live, before any spin).
3. As `testerplay`, set slider to 30%. Wager panel shows `💰 Stake value: 13,826 (30% of 46,088 wins)` at the bottom.
4. As `testerplay`, set slider to 0% again. Wager panel shows `🛡️ No stake (safe)` — the value updates **immediately** on slider change, not after a spin.
5. As `testerplay`, arm Double-Down (with a prior win, `wager_last_win_amount = 5,000`). Wager panel shows `⚡ Stake value: 5,000 (Double-Down)` — the percentage row is replaced.
6. As `testerplay`, complete a spin (win). The displayed stake value updates to reflect the new wins (e.g., 50,000 wins × 10% = 5,000 stake value).
7. As `testerplay`, complete a spin (loss at 10%). The displayed stake value updates to reflect the reduced wins (e.g., 46,000 wins × 10% = 4,600 stake value).
8. In inverted mode, the display switches to `💀 Stake value: {amount} ({pct}% of {losses} losses)`.
9. If the player does not own `wager_unlock`, the display always shows `🛡️ No stake (safe)` regardless of slider position.
10. The 211 prior tests still pass.
11. New file `tests/test_stake_value_display.py` with at least 6 tests:
    - `compute_stake_value(1000, 0, 0, True, False, False, 0) == 0` (0% = 0)
    - `compute_stake_value(1000, 0, 10, True, False, False, 0) == 100` (10% of 1000)
    - `compute_stake_value(1000, 0, 30, True, False, False, 0) == 300` (30% of 1000)
    - `compute_stake_value(1000, 0, 10, True, False, True, 5000) == 5000` (DD overrides)
    - `compute_stake_value(1000, 0, 10, False, False, False, 0) == 0` (no wager_unlock)
    - `compute_stake_value(0, 1000, 10, True, True, False, 0) == 100` (inverted, 10% of losses)
    - Component test: the JSX renders the stake value line with the correct format
    - Component test: the stake value updates on slider change

---

### Display UX considerations

- Place the stake-value display **at the bottom** of the wager element (per user request), after the existing insurance / DD / bank indicators.
- Use a clear emoji prefix to distinguish normal mode (💰 wins) vs inverted mode (💀 losses) vs safe state (🛡️ no stake) vs DD (⚡ Double-Down).
- The `🛡️ No stake (safe)` state should be visually distinct (greyed-out or with a shield emoji) to make it clear there's no risk on the next spin.
- The display should update **before** the next spin animation starts, not after, so the player sees what they're risking when they click spin.
- DD row REPLACES the percentage row when DD is armed (the percentage is irrelevant for a DD spin).
- If a player has insurance armed but DD is also armed, the insurance doesn't fire on a DD loss — the display can show a small note like "(insurance inactive during DD)" for clarity.

---

### Impact

- Adds one new pure function (`compute_stake_value` in wagers.py) — easy to test, used by both server and frontend.
- Adds two new response fields (`stake_value`, `max_stake_pct`) on `/api/state` and `/api/spin`.
- Adds one new state variable (`stakeValue`) and one new UI line in the wager panel.
- The formula is now a one-liner instead of a multi-line conditional — much more maintainable.
- The wager system becomes more transparent — players can see what they're risking before they click spin.

---

### T106: Tier gating by cumulative_wins (lifetime value of wins gained)

**Background:** The current tier-2/3 unlock thresholds (1,000 / 5,000) are
based on `win_count` (count of winning spins). This was designed for the
auto-spin era where every player spun 100+ times per session. With
wager-driven manual play, the count is too slow — a typical mid-game
player wins 1-2 wins per non-wagered spin and would need ~5,000 manual
spins to unlock Tier 3.

**Decision:** change the tier-gating metric from `win_count` to
`cumulative_wins` (lifetime value of wins gained). The new metric
reflects the wager-era scale: a single win at 30% stake can be 30% of
bankroll (vs 1-3 wins on a non-wagered spin).

**New thresholds:**

| Tier | Old (`win_count`) | New (`cumulative_wins`) |
|------|------------------:|------------------------:|
| 2    | 1,000             | 10,000                  |
| 3    | 5,000             | 100,000                 |

The 10× scale reflects the higher wins/spin under the wager system. The
10× ratio between tier 2 and tier 3 is preserved.

**Implementation:**

1. **Migration `049_cumulative_wins.sql`**: add `cumulative_wins BIGINT
   DEFAULT 0` to `game_state`. Backfill with current `wins` balance.
2. **`models.py`**: change `UPGRADE_TIER_THRESHOLDS` to `{2: 10_000, 3:
   100_000}`.
3. **`game.py`**: add `cumulative_wins` to the `_GAME_STATE_SQL` SELECT
   and the `/api/state` SELECT. In the manual spin and auto-spin tick
   UPDATEs, increment `cumulative_wins += max(0, wins_delta)`. In the
   buy endpoint, change the tier check from `gs['win_count'] <
   threshold` to `int(gs.get('cumulative_wins', 0)) < threshold`. The
   error message surfaces both the threshold and the player's current
   value.
4. **Tests** `tests/test_cumulative_wins.py` (10 tests): thresholds,
   field in state response, manual spin UPDATE, auto-spin tick UPDATE,
   tier gate logic, source checks, source checks for shop item,
   source checks for the auto-spin gate.

**Properties of `cumulative_wins`:**

- **Incremented by** `wins_delta` on every winning spin (manual + auto).
- **Never decremented** by purchases, wager losses, or prestige. It
  tracks the lifetime VALUE gained, not the value held.
- **Resets on season rollover** (consistent with `wins`).
- **Survives prestige** (also consistent with `wins`).

**Acceptance criteria:**

1. As a player with `cumulative_wins < 10,000`, attempting to buy a
   tier-2 item (e.g. `regen_shield`) returns 403 with the new error
   message `"Unlocks at 10,000 total wins gained (you have N)"`.
2. As a player with `cumulative_wins >= 10,000`, the same purchase
   succeeds.
3. As a player with `cumulative_wins < 100,000`, attempting to buy a
   tier-3 item (e.g. `fortune_charm`) returns 403 with `"Unlocks at
   100,000 total wins gained (you have N)"`.
4. After a winning spin, `cumulative_wins` increases by exactly
   `wins_delta`.
5. After a losing spin, `cumulative_wins` is unchanged.
6. After a shop purchase, `cumulative_wins` is unchanged (only `wins`
   decreases).
7. `/api/state` returns `cumulative_wins: int` field.
8. 245 prior tests still pass + 10 new tests = 255 passed, 1 skipped.

---

### T107: Auto-spin as shop upgrade

**Background:** The auto-spin button was a Season 7 default that killed
engagement. Season 8 removed it as the default loop but kept the
infrastructure (100 spins per activation, 0% stake, no DD/insurance).
The user wants the auto-spin button back, but as a **paid shop upgrade**,
not a default. This rewards active players while keeping the
convenience available to anyone willing to invest.

**Decision:**

- New shop item `auto_spin_unlock` (5,000 wins, Tier 1, no requires).
- When the player owns the item, an **auto-spin checkbox toggle**
  (`.autospin-row` style — restored from the S5/S6/S7 pre-removal
  gold-glow checkbox from initial commit `30def55`) appears in the
  wager panel.
- The checkbox label shows `Auto Spin` when inactive and
  `Auto Spin (N left)` when active (the remaining budget).
- **While auto-spin is active, the stake slider is hidden** in the UI
  (the player can't choose a stake, since auto-spin always uses 0%).
- DD and insurance buttons remain visible but are no-ops during
  auto-spin (the server already prevents them from arming).

**Why checkbox style instead of a button?** The operator wanted the
S5/S6/S7 pre-removal toggle look. The initial commit (`30def55`)
shipped a gold-bordered checkbox with a glowing "✓" indicator and
gold "Auto Spin" label — the button that landed in T107's first
implementation was unfamiliar to long-time players. Reverted to
match.

**Why hide only the stake slider?** DD and insurance require the player
to explicitly arm them; if they happen to be armed when auto-spin starts,
the server-side already prevents them from firing. The stake slider is
the only one that would be actively confusing — the player might think
their slider value is being used, but auto-spin ignores it.

**Implementation:**

1. **`models.py`**: add `'auto_spin_unlock': {'cost': 5_000, 'requires':
   None}` to `SHOP_ITEMS`. Tier 1.
2. **`game.py`**: in `auto_spin_start()`, return 403 if `'auto_spin_unlock'
   not in owned_items`. The "already active" check is `since-set AND
   budget > 0` (matches `/api/state`'s `auto_spin_active` gate) — a
   stale `auto_spin_since` with `auto_spin_budget = 0` is limbo state
   and must NOT block a fresh start.
3. **`app.jsx`**:
   - Add `autoSpinActive` and `autoSpinBudget` React state.
   - Sync from `/api/state` and `/api/tick` responses.
   - Add `handleStartAutoSpin` and `handleStopAutoSpin` callbacks.
   - In the wager panel, render the checkbox only if the player
     owns `auto_spin_unlock`. Use `.autospin-row` + `.autospin-label`
     markup; checkbox `onChange` calls start or stop.
   - Wrap the stake slider + dependent elements in `!autoSpinActive &&
   ...` to hide them.
   - Add a `useEffect` on `autoSpinActive` that polls `/api/tick` every
     3s while active.
4. **`static/styles.css`**: add `.autospin-row`, `.autospin-label`,
   `.autospin-row input[type="checkbox"]` (and `:checked`) rules.
   Mirrors the legacy S5/S6/S7 gold-glow style.
5. **Tests** `tests/test_cumulative_wins.py` T107 section: shop item
   exists, auto-spin/start source has the gate, JSX has the conditional
   hide + start/stop handlers, polling useEffect, checkbox markup,
   limbo-state check, CSS styles.

**Acceptance criteria:**

1. As a player without `auto_spin_unlock`, the wager panel shows no
   auto-spin toggle.
2. As a player without `auto_spin_unlock`, calling `POST /api/auto-spin/start`
   returns 403 with `"Buy auto_spin_unlock from the shop"`.
3. As a player with `auto_spin_unlock`, the wager panel shows a
   `.autospin-row` checkbox + `.autospin-label` (gold-glow style).
4. Checking the box calls `POST /api/auto-spin/start` and the server
   starts the auto-spin (auto_spin_active: true, auto_spin_budget: 100).
5. The label changes to `Auto Spin (N left)`.
6. The stake slider, hot streak indicator, bank button, DD button, and
   insurance button all **disappear** while auto-spin is active.
7. The `/api/tick` is polled every 3s while active; spin_count
   increments and auto_spin_budget decrements over time.
8. Unchecking the box calls `POST /api/auto-spin/stop`; auto_spin_active
   becomes false; stake slider reappears.
9. **Limbo-state recovery**: a player with stale `auto_spin_since` (from
   a prior session) and `auto_spin_budget = 0` can start a fresh
   auto-spin (the check requires both since-set AND budget > 0).
10. 260 tests pass (255 prior + 5 new for T107 polish).

---

### T108: Season 8 casino page background (Canvas scene + theme colour system)

- **Spec ref:** S16 (themes) — extends the per-season *page background* line
  (`page_season5` Bioluminescence, `page_season6` Night Ocean,
  `page_season7` Wormhole) with `page_season8` Casino. Distinct from the
  wheel-skin themes (tidal/ember/frost…), which are CSS effects on the wheel.
- **Status:** [x] done — operator approved 2026-06-23
- **Iteration log:**
  - 2026-06-23 v1: scene + theme system + cosmetic plumbing + default-equip.
  - 2026-06-23 fix: **low-spec rendered blank/white** — `frame()` early-returned
    because the low-spec branch set `running=false` before the single static
    paint. Reworked so low-spec paints one frame (and repaints on resize) and
    only the non-low-spec path schedules `requestAnimationFrame`.
  - 2026-06-23 recolor: added `body.page-season8` CSS overriding `--p`→green /
    `--s`→red (project-wide, via the existing CSS-var system) + a solid dark
    background so the page is never blank-white even if the canvas fails to load.
  - 2026-06-23 scene v2 (operator feedback): added a floor with a horizon +
    perspective lines; grounded every table with a contact shadow, side-thickness
    skirt and pedestal base (no more floating-platform look); authentic poker
    details researched from real tables — padded leather rail w/ sheen, wood
    racetrack ring, gold betting line, slotted dealer chip tray, felt stitching.
    Cards are now face-down (shape pattern) — removed all text glyphs per
    "no text or numbers in the background".
  - 2026-06-23 scene v3: side tables tucked to the walls near the horizon so
    they never overlap the main table; added many more props around the table
    (chip stacks, face-down cards, dice, a card deck, cocktail glasses) at seat
    positions, perspective-scaled.
  - 2026-06-23 scene v4: removed the side tables; added slot machines lining
    both walls (3/side, seeded once → random positions/colours/symbols/cadence,
    so no flicker). Each cabinet: marquee w/ chasing lights + candle, 3-reel
    window with shape-only symbols (cherry/lemon/diamond/bell/bar/star/clover)
    that spin on staggered cycles, button deck, coin tray, side lever that
    pulls on spin. NOTE: in-app the side UI panels cover most of the gutters,
    so slots are mainly visible in the preview / on wider viewports.
  - 2026-06-23 approved: operator signed off, no further changes requested.
- **Discovered:** 2026-06-23 (operator request)
- **Parallel group:** P-themes (independent)
- **Files:**
  - `static/js/casino-bg.js` (new — vanilla Canvas scene module, `window.createCasinoScene(canvas, opts)`)
  - `static/casino-preview.html` (new — standalone no-auth preview harness for iteration/screenshots)
  - `static/index.html` (load casino-bg.js before app.js; bump app.js cache version)
  - `static/app.jsx` (`CasinoBackground` wrapper component; `casino` palette in `THEME_COLORS`; `page_season8` in shop + cosmetic ID sets; `wheelTheme`/`pageThemeClass`/`casinoActive` wiring; mount + seabed hide)
  - `models.py` (`page_season8` in `SHOP_ITEMS`)
  - `migrations/050_season8_theme.sql` (grant `page_season8` to all staging users)
  - `migrations/051_season8_theme_equip.sql` (force-equip `page_season8` for all existing users)
  - `auth.py` (new players start with `page_season8` owned + equipped)
  - `game.py` (`page_season8` → `page_theme` cosmetic slot)

---

### Problem

The Season 8 page-background slot is empty. Previous seasons each shipped a
full-page background that the wheel composites on top of (S6 ocean, S7
wormhole Canvas). S8 needs a casino-themed scene, and the operator wants the
colour scheme (green = wins, red = losses) driven by a **switchable theme
system**, not hardcoded per element.

### Proposed solution

A perspective casino room drawn with HTML5 Canvas: a central green poker
table on which the wheel (a separate, composited element) sits; surrounding
dimmer tables and ambient elements (chips, cards, wall sconces, hanging
spotlight) for depth. Slow, simple ambient animation (breathing spotlight,
drifting motes) — busy but not overstimulating. All colours come from a
single `palette` object shared with the wheel's `THEME_COLORS.casino` entry,
so themes stay switchable via the cosmetic store and nothing is hardcoded.
Reuses the existing per-season cosmetic plumbing (`page_seasonN` →
`wheelTheme` + page background, mounted like `WormholeBackground`) and the
existing `static/js/` shared-module + standalone-preview-HTML precedents.

### Acceptance criteria

1. Owning + equipping `page_season8` from the store renders the casino
   background; un-equipping/switching to another `page_seasonN` restores it.
2. Wheel segments turn green (win) / red (lose) when the casino theme is
   active, from `THEME_COLORS.casino` — same palette source the background reads.
3. Central poker table is sized/positioned so the live wheel sits centred on
   its felt; the wheel is composited on top (not painted into the background).
4. Scene has perspective depth (background tables/elements) and reads as a
   casino without clutter; animation is slow and subtle.
5. `lowSpec` mode degrades gracefully (reduced/halted animation), matching how
   `WormholeBackground` honours `static`/low-spec.
6. The seabed ocean iframe is hidden while the casino theme is active.
7. `static/casino-preview.html` renders the scene standalone (no auth) for
   iteration.
8. All prior tests still pass; no production DB touched (staging only).
9. The shop displays `page_season8` as "Owned" and "Equipped" for all players granted the theme via migration 051 (i.e. `owned_items` written directly by SQL, not via `/api/buy`). Verify on a test account by checking the shop tile shows the correct state badges.

### Open questions (for operator during iteration)

- Final palette: exact greens/reds and whether the rail/felt should lean more
  classic-green or match the S8 green/red brand more aggressively.
- How "busy" — number of background tables, chips, ambient elements.
- ~~Whether to auto-grant + force-equip for the patch week~~ — RESOLVED
  (2026-06-23, operator): all players get the casino theme equipped by default
  during S8 — existing users via migration 051, new users via the registration
  default in `auth.py`. Players can switch to any other theme in the shop.

---

### T109: Migrate main server from 7.7 → Season 8 (production rollout)

- **Spec ref:** `SEASON_8_MIGRATION_PLAN.md` (the authoritative procedure
  for this ticket — this ticket is a summary; the plan is the source of
  truth for the actual steps, schedule, and verification checklist).
- **Status:** [ ] not started — scheduled for 2026-06-27 00:00 BST
  (the `seasons.ends_at` in `wheeldb` is `2026-06-26 23:59:00+01`).
- **Iteration log:**
  - 2026-06-23 v1: ticket + plan doc created, all open questions
    resolved.
  - 2026-06-23 S7 timer fix committed (`3c67350`) and merged into
    staging (`4d8316f`); `sync-staging.yml` workflow disabled (`7b3cf3f`).
- **Discovered:** 2026-06-23 (operator request — "we have historically
  ALWAYS had issues with this migration, I want this week to be the
  first smooth one").
- **Parallel group:** MIGRATION (must run alone — the site is live).
- **Files:**
  - `docs/SEASON_8_MIGRATION_PLAN.md` (new — the full plan, 640 lines)
  - `/home/user/wheel-app/seasons.py` (the rollover mechanism — already
    on S8 reset in staging; will merge across via §6.3)
  - `/home/user/wheel-app/migrations/031–051` (S8 schema — already
    written, need to be promoted from staging)
  - `/home/user/wheel-app/migrations/052_user_season_history_s8.sql`
    (new — adds S8 columns to `user_season_history` so the rollover's
    INSERT SELECT doesn't silently drop them; required before the
    rollover fires)
  - `/etc/cron.d/wheel-rollover` (new — one-shot cron, fires
    `bin/rollover.sh` at 23:00 UTC Fri 26 Jun)
  - `/home/user/wheel-app/bin/rollover.sh` (new — wrapper that loads
    `ADMIN_SECRET` from `.env` and POSTs to `/api/admin/advance-season`)
  - `/home/user/wheel-app/.github/workflows/sync-staging.yml.disabled`
    (renamed from `.yml` 2026-06-23 to disable the master→staging
    auto-merge during the migration window)
  - `SEASON_8_PROGRESS.md` (gets a "Migration 2026-06-27" section
    after the rollover)

#### Problem

The main server (`wheeldb`, port 5000) is currently in season 7.7. The
entire Season 8 design (wager system, prestige, bounties, community
goals, singularity, loadouts, casino theme, 22 migrations' worth of
schema) has been built and tested in `wheel-app-staging/`. We need to
get it onto the live server and execute the season rollover cleanly.

Historical breakage (from `wheel-app` git log):
- `1b2d07f` — season_number wrong (mid-season fix bumped number)
- `50d37ff` — `user_season_history` INSERT missing new S7 columns
- `2d541dc` — `community_pot` not being reset on rollover
- `d56c505` — upgrade levels / stat columns not being reset
- `8b54343` — DB migrations not applied to staging
- `915a2bf` — duplicate route after merge

**Pattern:** every season's reset UPDATE forgets the new fields. The
fix is "remember to update the reset UPDATE" — easy to forget on a
stressful migration night. This plan makes it impossible to forget
by adding a **dry-run verification on staging** as a hard gate (§6.1
in the plan).

#### Scope (in)

- Promote the 22 S8 migrations (031–052) from staging to main
- Promote the S8 code (game.py, models.py, seasons.py, app.jsx, …) to main
- Update main's `seasons.py` reset UPDATE to cover S8 fields
- Update main's `seasons.py` `user_season_history` INSERT to cover S8 fields
- Update main's `seasons.py` `community_pot` reset to S8 starting values
- Add `migrations/052_user_season_history_s8.sql` (the missing history table columns)
- Install the cron (`/etc/cron.d/wheel-rollover` + `bin/rollover.sh`)
  to fire the rollover at the scheduled time
- Verify the rollover end-to-end on staging first, then on main
- Patch-note the S8 launch

#### Scope (out)

- Season 9 mechanics (this is a 7.7 → 8 transition, not 8 → 9)
- Theme changes beyond what S8 already ships (Casino background is in)
- New columns not already in the S8 design
- The top-3 vs top-5 winners inconsistency (tracked separately)
- Frontend re-skin for the rollover announcement (existing hiatus page works)
- The 8.1, 8.2 sub-season model (follow-up design ticket T110, after
  S8 launch)

#### Acceptance criteria

The migration is "done" when ALL of the following are true:

**Pre-completed (2026-06-23)**
1. ✅ S7 timer fix committed to master (`3c67350`) and merged into
   staging (`4d8316f`).
2. ✅ `sync-staging.yml` workflow disabled (`7b3cf3f`) so it doesn't
   interfere with the manual staging → master promotion.
3. ✅ `seasons.name` for the new S8 decided → **`'Casino'`** (themed,
   matches the new `page_season8` background).
4. ✅ Trigger mechanism decided → **cron-driven**
   (`/etc/cron.d/wheel-rollover` + `bin/rollover.sh`); operator-fallback
   curl available for emergency use only.

**Pre-migration (§6 in the plan)**
5. S8 reset logic re-verified on staging (rollover dry-run, all
   S8 fields reset, `legacy_wins` accumulates, pot resets, snapshots
   inserted, history inserted, season row bumped).
6. `migrations/052_user_season_history_s8.sql` written, applied to
   staging, applied to main.
7. S8 working tree in staging committed + pushed to `origin/staging`
   (one or more atomic commits covering the new files + modified files).
8. Staging merged into master; 22 migrations (031–052) applied to
   `wheeldb` without errors.
9. Gunicorn restarted; live site still on 7.7; login + spin still
   works (proves S8 code is inert on 7.7 game_state).
10. Cron entry installed in `/etc/cron.d/wheel-rollover`; `bin/rollover.sh`
    in place; manual pre-rollover backup taken at 22:30 BST Friday.

**Migration night (§7 in the plan)**
11. T-30 pre-flight completed (7.7 still active, no errors in 24h,
    cron in place, staging up as fallback).
12. T-5 pre-flight completed (7.7 still active, staging up).
13. T-0 rollover fires (cron); `SEASON_ROLLOVER_DONE` in gunicorn log
    within 5 seconds.
14. T+5: `seasons` row bumped, name = `'Casino'`, 3 new
    `season_snapshots` rows, 8 new `user_season_history` rows,
    `community_pot` reset.
15. T+15: login as one user, verify S8 UI live, casino background
    rendering, wager panel works.
16. T+1h: no errors in gunicorn log since the rollover.

**Post-migration (§8 in the plan)**
17. Spot-check confirms `legacy_wins = (old value) + (final wins)`
    for all 8 users — not just `final wins`.
18. Spot-check confirms all S8 fields reset to defaults (wager_streak,
    wager_banked_wins, prestige_*, auto_spin_budget, active_wheel_mode,
    guard_*, resilience_*).
19. Announcement made (patch notes / chat / etc. — operator task).
20. `SEASON_8_PROGRESS.md` updated with the migration record.
21. T109 status updated with the actual timestamp + deviations.

**Rollback (if needed, §9 in the plan)**
22. If anything in steps 13–18 fails: site stopped, pre-rollover
    backup restored, gunicorn restarted, problem diagnosed on staging,
    re-attempted next window.

#### Operator decisions (resolved 2026-06-23)

1. ✅ **S8 season name** → **`'Casino'`**. The rollover will set
   `seasons.name = 'Casino'` in the same UPDATE that bumps
   `season_number`.
2. ✅ **`ends_at` strategy** → keep the 7-day pattern. The intent
   going forward is **smaller weekly sub-seasons** (8.1, 8.2, …) with
   balance changes and new features (e.g. new wheel spin modes) — but
   the first rollover (this one) is still a full reset. Sub-season
   model is follow-up design work, not part of this migration.
3. ✅ **Pre-registration for auto-spin start** → not needed for S8.
   Auto-spin is shop-gated (T107, `auto_spin_unlock` at 5,000 wins).
   The `season_registered` flag becomes informational only; the
   rollover still resets it to FALSE but nothing depends on it.
4. ✅ **Community pot buff duration** → keep 7d. Reset applies to
   each 8.1 sub-season as well (pot starts fresh each sub-season).
5. ✅ **Trigger mechanism** → **cron-driven** (`/etc/cron.d/wheel-rollover`
   + `bin/rollover.sh`). Manual fallback curl is for emergency only.
6. ✅ **Uncommitted JSX edits in master** → resolved. The 2 uncommitted
   files were the S7 timer fix (unrelated to S8), committed as
   `3c67350` and merged to staging as `4d8316f`.
7. ✅ **`sync-staging.yml` workflow** → **disabled** (commit `7b3cf3f`).
   Renamed to `.yml.disabled` so the master → staging auto-merge
   doesn't fire on the next master push. Re-enable after the migration
   by renaming back.

#### Schedule

| When | What | Owner |
|---|---|---|
| **Tue 23 Jun** | Plan + T109 written, all decisions resolved | (DONE) |
| **Tue 23 Jun** | S7 timer fix committed + merged to staging | (DONE) |
| **Tue 23 Jun** | `sync-staging.yml` workflow disabled | (DONE) |
| **Wed 24 Jun** | §6.1 dry-run S8 rollover on staging | Dev |
| **Wed 24 Jun** | §6.2 write + apply `052_user_season_history_s8.sql` | Dev |
| **Wed 24 Jun** | §6.6 install `/etc/cron.d/wheel-rollover` + `bin/rollover.sh` | Dev |
| **Thu 25 Jun** | §6.3 commit S8 working tree to staging + push to origin | Dev |
| **Thu 25 Jun** | §6.3 promote staging → master + apply 22 migrations | Dev |
| **Thu 25 Jun** | §6.3 smoke test (7.7 still works on S8 code) | Dev |
| **Fri 26 Jun 03:00** | Daily backup runs (existing cron) | (automated) |
| **Fri 26 Jun 22:30** | §6.7 manual pre-rollover backup | Dev |
| **Fri 26 Jun 23:30** | T-30 pre-flight | Dev |
| **Fri 26 Jun 23:55** | T-5 pre-flight | Dev |
| **Sat 27 Jun 00:00 BST** | T-0 rollover fires | **Cron** (operator-fallback only) |
| **Sat 27 Jun 00:05–01:00** | Post-rollover verification | Dev |
| **Sat 27 Jun** | Announcement + T109 close-out | Operator |

#### Definition of "smooth" (per operator 2026-06-23)

> "I want this week to be the first smooth one."

Means:
- No silent failures (all verification checks pass)
- No rollback required
- No data loss (snapshots + history complete + `legacy_wins`
  accumulated correctly)
- All 3 active players can log in and play S8 within 15 minutes of T-0
- No follow-up tickets filed for missed-reset bugs in the first 24h


### T110: Wager tokens — spending mechanic

- **Status:** [x] (2026-06-26) — operator-confirmed option (a): 1 token = 1 insurance charge (capped at WAGER_INSURANCE_MAX_CHARGES). New POST /api/wager/insurance/buy endpoint; new wager-panel button '🪙 Buy Insurance (1 token)'. 12 tests. Note: this is the SECOND T110 — the original T110 (commit adb4764) implemented paying high-stake spin costs with tokens; this one ADDS a separate spending path.
- **Discovered:** 2026-06-26 (operator: "Are wager tokens implemented yet?")
- **Files:**
  - `game.py`
  - `static/app.jsx`

**Current state:** Earning is complete. `wager_tokens` column exists (migration 034). Tokens
are awarded on fishing catches (reel endpoint), bounty claims, and community goal completion.
The column survives prestige (T85). Token count is in `/api/state`.

**What's missing:** There is no spending path. Players accumulate tokens with no way to spend
them. Spec intent: tokens are spent in the wager panel to activate a modifier. Exact mechanic
requires operator sign-off before implementation.

#### Acceptance criteria

1. At least one spending action exists in the wager panel (mechanic TBD by operator — see open question below).
2. The wager panel displays the player's current token count at all times.
3. Spending debits `wager_tokens` atomically (safe under concurrent spins).
4. Tokens cannot go below 0.
5. `pytest` passes.

#### Open question

What does a wager token buy? Operator to decide one of: (a) free one-spin insurance, (b) temporary stake percentage boost for N spins, (c) double-down top-up. T110 cannot be implemented until this is answered.

---

### T111: Prestige tooltip — clarify what "2%" affects

- **Status:** [x] (2026-06-26) — accurate tooltip. Original AC proposed loss-protection wording ('saves 2% of your wins when you lose a spin') but the actual code is a +2% WIN multiplier (prestige.py:78, game.py:227). New tooltip: 'Each level adds +2% to your win payout (e.g. level 5 = 1.10x, level 20 = 1.40x). Doesn't affect losses or jackpots.' 5 tests. Note: this is the SECOND T111 — the original T111 (commit e2ed881) added PRESTIGE_LEVEL_MULTIPLIER for scaling; this one fixes the user-facing tooltip.
- **Discovered:** 2026-06-26 (operator: "Prestige tooltip still doesn't explain what the '2%' increase actually does or what value it increases")
- **Files:**
  - `static/app.jsx` (prestige panel tooltip text only)

**Problem:** The tooltip shows "2%" with no explanation. Players do not know what increases or why it matters.

**What 2% means (per spec + live code):** `prestige_efficiency = prestige_level * 2`. On a
losing spin, `floor(wins × prestige_efficiency / 100)` wins are retained instead of lost.
Each prestige level saves 2% of your wins from a loss; at level 5 (max), 10% of wins are
protected on every loss.

#### Acceptance criteria

1. Prestige panel tooltip reads (or equivalent, operator to approve exact wording): "Each Prestige level saves 2% of your wins when you lose a spin. At level 5, 10% of your wins are protected from losses."
2. Tooltip wording matches the actual formula in `game.py` (`prestige_efficiency`).
3. No other text or layout changes.

---

## T112: Vertical wager panel (left of wheel, anchored to center)

- **Status:** [ ] (planned 2026-06-23)
- **Discovered:** 2026-06-23 (operator review of current horizontal layout)
- **Goal:** Recover horizontal real estate around the wheel by flipping the
  wager panel from horizontal (below the wheel, full width) to vertical
  (tall, narrow column to the left of the wheel, anchored to viewport
  center). The wheel grows back to use the freed space.
- **Visual target:** "similar shape, just flipped 90 degrees" — keep the
  panel's identity (dark glass, purple border, gold accents) but
  rearranged so the long axis is vertical.

### Layout direction

Current horizontal order (top → bottom inside the panel):
1. Stake slider + label `Stake` + percentage readout
2. Hot Streak indicator (if active)
3. Bank button (if applicable)
4. Double-Down armed indicator OR Arm button
5. Insurance armed indicator OR Activate button
6. Stake value display (live cost preview)

New vertical order (top → bottom inside the panel, long axis vertical):
1. `STAKE` label (top)
2. Percentage readout (e.g. "10%")
3. Stake value display (live cost preview — small)
4. Vertical stake slider (0 at BOTTOM, max at TOP; thumb moves UP as
   the player increases stake)
5. `?` tooltip trigger (BOTTOM end of the slider, mirrors the
   horizontal layout's ?-icon-on-the-end convention)
6. Hot Streak indicator (small, above the action buttons)
7. Bank button
8. Double-Down indicator / Arm button
9. Insurance indicator / Activate button

### Anchor + positioning

- Position the panel to the **left of the wheel**, anchored to the
  vertical center of the viewport (or the wheel, whichever is taller).
- Use a fixed/sticky positioning scheme so the panel does not scroll
  away with the wheel.
- Width should be ~80–110px (narrow column); height should be tall enough
  to fit all controls stacked without truncation at 1366×768 (the
  reference resolution per the existing `MEDIA-QUERY-1366` notes).
- Add a comfortable gap (e.g. 24–32px) between the wager panel and the
  wheel's left edge so they do not touch.
- On viewports narrower than 1366px, fall back to the existing
  horizontal layout (do not break mobile/tablet). Use the existing
  `@media (max-width: 1366px)` breakpoint convention.

### Slider orientation (vertical, bottom-to-top)

- The `<input type="range">` becomes vertical via CSS
  `writing-mode: vertical-lr` (or `vertical-rl`) on the element, with
  width/height swapped.
- Visual order: min value (0) at the **bottom** of the slider track,
  max value (45) at the **top**. This matches "stake goes up from the
  bottom" — increasing stake = thumb moves up.
- Re-evaluate tick markers (currently `step="5"`). Keep step=5 but
  verify the thumb position reads correctly in the new orientation.
- Confirm the `stake-pct` change handler still works (the value is a
  number; the orientation is purely visual).

### "?" tooltip trigger

- The existing `.wager-tooltip-trigger` is positioned next to the
  slider (`<span className="wager-tooltip-trigger" data-tooltip={WAGER_TOOLTIP}>?</span>`).
- In the vertical layout, place it at the BOTTOM end of the slider
  (below the slider track, near the 0% position). This mirrors the
  horizontal layout's convention of putting the ?-icon on the trailing
  end of the slider.
- The tooltip content is unchanged (the `WAGER_TOOLTIP` constant in
  `app.jsx` line 3889-3898). Note: WAGER_TOOLTIP is STALE (T94
  follow-up, 4 incorrect claims about DD 2× and insurance) — fix
  separately, do not block this ticket on it.

### Text and element re-arrangement

- The `Stake` label moves to the TOP of the panel (was the left side
  of the horizontal slider row).
- The percentage readout (`stake-label` `10%`) moves BELOW the label
  and ABOVE the slider, so it reads as a header pair (Label + %).
- The stake value display (live cost preview) sits BELOW the percentage
  and ABOVE the slider. It is a short line ("💰 1,000" or "🛡️ No stake")
  — keep it one line; do not wrap.
- All action buttons (Hot Streak, Bank, DD, Insurance) stack below
  the slider. Reduce horizontal padding inside the buttons to fit the
  narrow column. Icons stay; text labels may need to be abbreviated or
  dropped (e.g. "🏦 Bank 1.2K" instead of "🏦 Bank 1,234").

### "Earn back the wheel's size" — wheel sizing

- The current `.wheel-wrapper` width/height is `min(580px,
  calc(100vw - 120px), calc(100vh - 480px))` (line 187-188 of
  `styles.css`). The `-120px` is the horizontal reservation for the
  side panels (left/right margins).
- After the wager panel moves to the left of the wheel, the wheel can
  grow to use the freed horizontal space. Change the formula to
  something like `min(640px, calc(100vw - 240px), calc(100vh - 480px))`
  — the `-240px` reserves room for the wager panel on the left.
- Verify the new wheel size does not push the title out of view or
  overlap the fishing panel (which is bottom-left, in the
  `mobile-fish-panel` container — see `@media` rules at line 2407+).

### Non-overlap + nice spacing (Playwright audit, AC)

- Use Playwright to verify on **three** resolutions:
  1. 1920×1080 (desktop)
  2. 1366×768 (small desktop)
  3. 1280×720 (worst-case desktop)
- For each resolution, screenshot the casino area and assert:
  1. Wager panel does not overlap the wheel (use
     `element.boundingBox()` to compare).
  2. Wager panel does not overlap the fishing panel (mobile or
     inline variant).
  3. Wager panel does not overlap the title / subtitle.
  4. Wager panel does not extend below the viewport's visible area
     (no vertical clipping at 1366×768).
  5. Slider is reachable (no element above it in the panel is
     blocking pointer events).
- Add a Playwright test under `tests/playwright/` (new file
  `test_wager_panel_layout.py`) that loads the page at each
  resolution and asserts the four overlap checks.

### Files to touch

- `static/styles.css`:
  - `.season8-wager-panel` — change to vertical layout, fixed/sticky
    positioning to the left of the wheel, narrow width, taller
    height, anchor to vertical center.
  - `.wager-stake-control` — switch to vertical flex (label, %,
    value, slider, ?) stacked.
  - `.wager-slider` — `writing-mode: vertical-lr` + swapped
    width/height.
  - `.wheel-wrapper` — update the `-120px` reservation to `-240px`
    (or however much the wager panel + gap needs).
  - New `@media (max-width: 1366px)` rule — fall back to horizontal
    layout for narrower viewports.
- `static/app.jsx` (no logic change needed, but verify the JSX order
  matches the new visual order):
  - `.wager-stake-control` children: re-order so the ?-icon is at
    the bottom and the slider is vertical.
  - The `?` tooltip trigger (`<span className="wager-tooltip-trigger"
    data-tooltip={WAGER_TOOLTIP}>?</span>`) — ensure it is rendered
    after the slider in the JSX, so visual "after" = "below" in
    the new vertical orientation.
- `tests/playwright/test_wager_panel_layout.py` (NEW): three
  resolutions × four overlap checks.

### Acceptance criteria

1. On 1920×1080, the wager panel renders as a narrow vertical column
   anchored to the left of the wheel, vertically centered.
2. The wheel is visibly larger than before (≥ 10% wider on the
   horizontal axis at 1920×1080).
3. The stake slider's thumb is at the BOTTOM when stake=0 and at the
   TOP when stake=max.
4. The `?` tooltip icon is at the BOTTOM end of the slider.
5. The wager panel does not overlap the wheel, the fishing panel, or
   the title at any of {1920×1080, 1366×768, 1280×720}.
6. At 1366×768, the wager panel is fully visible (no vertical
   clipping).
7. On viewports narrower than 1366px, the layout falls back to the
   existing horizontal layout.
8. Auto-spin still hides the slider correctly (no regression of
   T107).
9. All existing wager tests still pass (pytest 261 → 262+).
10. The new Playwright layout test passes.

### Parallel group

- Can run in parallel with T108, T110, T111 (the other 4 tickets in
  this batch) because the wager panel is its own CSS+JSX island and
  does not touch any of the other tickets' files. Worktree: yes
  (separate branch, separate worktree).
- After merge: any conflict in `static/styles.css` is limited to the
  `.season8-wager-panel` block (T108 might also touch it) and
  `.wheel-wrapper` width formula (T108 might also touch it). Other
  conflict surfaces are minimal.

### Depends on

- T108 (DD/Insurance disarm) — both touch the wager panel JSX
  block. The shared JSX region is the DD/Insurance action buttons
  (lines 4602-4613 of app.jsx). T108's changes must be merged
  first so T112's re-order can reference the final button list.
- T110 (wager tokens spending) — also builds into the wager panel.
  T112's vertical layout should be the final composition that
  T110's tokens UI sits inside. T110 should add its UI in a way
  that fits the new vertical orientation (likely: a small "🪙 N
  tokens" line near the stake value, or a token-cost indicator
  next to the percentage).

### Order of execution

- **Run after T108, T110** (both touch the wager panel JSX).
- **Can run in parallel with T109 (Bonus Power desc), T111
  (Prestige scaling)** which do not touch the wager panel.


---

### T113: Aquarium panel — text colour + luck tooltip

- **Status:** [x] (2026-06-26) — aquarium species text now `color: #e0e0e0` (was inheriting black); new `(.aquarium-info-icon)` with tooltip 'Each unique fish species you catch adds +0.1% to your base win chance.' 5 tests.
- **Discovered:** 2026-06-26 (operator: "Aquarium text is black, impossible to read")
- **Files:**
  - `static/styles.css`
  - `static/app.jsx` (aquarium panel — add `(?)` tooltip)

**Problem:** Aquarium panel text renders black on a dark background, making it unreadable.

**What the aquarium tells the player:** Each unique species in `aquarium_species` adds
+0.1% to the player's base win chance. This luck bonus is the only visible benefit of
collecting fish. Without a tooltip, players have no idea why the aquarium matters.

#### Acceptance criteria

1. All text in the aquarium panel is readable — white or light-grey, matching the
   wager/fishing panel text colour convention.
2. A `(?)` icon on the aquarium panel header shows a tooltip: "Each unique fish species
   you catch adds +0.1% to your base win chance."
3. No layout or structural changes beyond colour + tooltip.

---

### T114: Pre-release: disable onboarding modal

- **Status:** [x] (2026-06-26) — `showOnboarding` hardcoded to `false` (initial state + gameState refresh). `onboarding_step` preserved in backend for T43. 3 tests.
- **Discovered:** 2026-06-26 (operator: "Can we disable the onboarding for now, it's
  faulty and we don't have time to fix")
- **Depends on:** none (independent frontend hotfix)
- **Files:**
  - `static/app.jsx`

**Context:** The onboarding modal is broken in three distinct ways (T43: steps 2-4 never
advance; overlay blocks all pointer events; no rewards granted). Fixing it properly is T43,
which is out of scope for S8 launch tonight.

**Fix:** Suppress the modal entirely by treating all players as `onboarding_step = 5`
(done) in the frontend render condition. One-line change to the JSX gate on `showOnboarding`.

#### Acceptance criteria

1. The onboarding modal never appears, regardless of `onboarding_step` value in state.
2. No backend or DB changes — `onboarding_step` preserved for when T43 ships.
3. Other modals that share `onboarding-overlay` CSS class (prestige confirmation, legacy
   boards) still render correctly.

---

### T115: "Long Shot" wheel mode — replaces Mirror in weekly rotation

- **Status:** [x] (2026-06-26) — `WHEEL_MODES['long_shot']` (20% win / 60% loss / 20% jackpot ×10); `_ROTATING_MODES = ['inverted', 'gravity', 'long_shot']`; `WHEEL_MODE_INFO['long_shot'] = 'Long Shot'`. 6 tests.
- **Discovered:** 2026-06-26 (operator: mirror doesn't work yet, replace with win/loss%-only
  mode; defer two-wheels concept to 8.X — see T78)
- **Depends on:** T11 (wheel modes foundation)
- **Files:**
  - `wheel_modes.py` (add `'long_shot'` entry; update `_ROTATING_MODES`)
  - `static/app.jsx` (mode display name + description in wheel-mode indicator)
  - any test asserting `get_rotating_mode()` returns `'mirror'` at slot 2

**Context:** `_ROTATING_MODES = ['inverted', 'gravity', 'mirror']` — `week % 3 == 2`
currently yields `'mirror'`. Mirror backend is complete (T78 [x]) but the frontend two-wheels
UI was never built and is deferred to 8.X. Slot 2 is replaced with Long Shot — a pure
probability shift, no new mechanics, no new columns, no new endpoints.

**Spec (operator-confirmed 2026-06-26):**

| Field | Value |
|---|---|
| `win_pct` | 20 |
| `loss_pct` | 60 |
| `jackpot_pct` | 20 |
| `jackpot_multiplier` | 10 |
| `description` | `'Most spins lose. Jackpots hit often but pay less.'` |

Probabilities sum to 100. Jackpot multiplier is 10× (vs steady 25×, volatile 50×) —
jackpots are ~10× more frequent than steady but pay ~2.5× less each.

#### Implementation

**`wheel_modes.py`** — two edits:

```python
    'long_shot': {
        'win_pct': 20,
        'loss_pct': 60,
        'jackpot_pct': 20,
        'description': 'Most spins lose. Jackpots hit often but pay less.',
        'jackpot_multiplier': 10,
    },
```

```python
_ROTATING_MODES = ['inverted', 'gravity', 'long_shot']
```

**`static/app.jsx`** — add `'long_shot': 'Long Shot'` to whichever `MODE_LABELS` /
`WHEEL_MODE_NAMES` map (or inline conditional) formats the mode key for display.

#### Acceptance criteria

1. `WHEEL_MODES['long_shot']` exists with exactly the values in the table above.
2. `get_rotating_mode()` returns `'long_shot'` when `week % 3 == 2`.
3. Wheel-mode indicator displays `"Long Shot"` (not the raw key) with the description
   `"Most spins lose. Jackpots hit often but pay less."`
4. A spin in Long Shot mode resolves with the correct 20/60/20 probabilities — cover
   with a `test_long_shot_probabilities` test alongside the existing mode tests.
5. `pytest` clean (no regressions).

---

### T116: Wager panel arm buttons — truncation fix

- **Status:** [x] (2026-06-26) — DD button label shortened '⚡ Arm Double-Down (all-or-nothing)' → '⚡ Double Down'. Insurance label was already 2 words. 'all-or-nothing' warning preserved in button `title` attribute. Added `white-space: normal; line-height: 1.2;` to `.wager-action-btn`, `.wager-cancel-btn`, `.wager-double-down-armed`. 6 tests.
- **Discovered:** 2026-06-26 (operator: "'Arm Double Down' and 'Arm Insurance' buttons are
  truncated — make them wrap, max 2 words")
- **Files:**
  - `static/app.jsx` (button label text)
  - `static/styles.css` (allow wrap on arm buttons if `white-space: nowrap` is set)

**Fix:** Two changes:
1. Allow text wrap on the arm buttons (`white-space: normal` if currently overridden).
2. Shorten labels to ≤2 words. Drop the "Arm" prefix — context is clear from the panel.
   Labels become: **"Double Down"** and **"Insurance"**.
   If the armed/disarmed toggle must be visible in the label, use **"Arm DD"** / **"Arm Ins."**
   instead (operator to confirm preference).

#### Acceptance criteria

1. Both buttons display their full label without truncation at 1366×768 and 1920×1080.
2. Labels are ≤2 words.
3. Button height expands to fit wrapped text — panel does not clip or scroll.
4. Armed/disarmed visual state (colour or icon change) is not regressed.

---

### T117: Bounty claim overhaul — fix broken `Claim` button, lower token amounts, reset at 23:59

- **Status:** [x] (2026-06-26) — bug fixed: server response now uses `bounty_id` key (was `id`), and frontend reads the correct key. Per-bounty rewards 1/2/3 tokens (was 100/250/500). Cosmetic fragment 3/3 bonus removed. Per-bounty `claimed` flag on `bounty_progress` (migration 053). 9/9 bounty tests pass; full suite 373 pass. Note: `bounty_claimed_date` column on game_state left in place (T43/T119 territory).
- **Discovered:** 2026-06-26 (operator: "Bounty claiming doesn't work — click gives 'bounty_id required' error. Amounts should be way lower. Reset at 23:59.")
- **Depends on:** none (independent hotfix)
- **Files:**
  - `static/app.jsx` (bounty claim handler + JSX — `bounty-card` and the per-bounty `Claim` button)
  - `game.py` (claim endpoint reward table + reset-hour logic)
  - `bounties.py` (reward curve + reset-time helper)
  - `tests/test_bounties.py` (new file; covers all ACs)

**Problem 1 — claim button is broken.** Frontend handler `handleBountyClaim(bountyId)` at
`static/app.jsx:4150` posts `{bounty_id: bountyId}` to `/api/bounties/claim`. The endpoint
(`game.py:3551`) reads `bounty_id` and returns 400 "bounty_id required" if missing. The bug
is on the *frontend* side: `get_bounty_status()` in `bounties.py:152` returns each bounty as
`{'id': b['id'], ...}` (key is **`id`**, not `bounty_id`). The map at `static/app.jsx:4846`
iterates `bounties.map(b => ... b.bounty_id ...)` — so `b.bounty_id` is `undefined` for every
bounty, the request body is `{}`, and the API rightly rejects. Confirmed via direct call to
`/api/bounties` in staging; response payload shows `"id": "bounty_jackpot"`, not `bounty_id`.

**Problem 2 — token amounts are way too high.** Current curve (`bounties.py:183-187`):
1 completed = 100 tokens, 2 completed = 250, 3 completed = 500. Plus 1 cosmetic fragment
for the 3/3. These are per-day totals (not per-bounty), so a player who completes all 3
bounties once a day gets 500 tokens. Operator wants this dropped dramatically since the
new insurance economy (T119) makes tokens the *only* way to refill insurance charges,
and bounties are the *only* renewable source outside the new daily-claim flow.

**Problem 3 — reset timing.** Bounty date is currently `now_utc.date()` (`game.py:1001`),
so bounties reset at UTC 00:00 (= BST 01:00). Operator wants reset at UTC 23:59 so the
end-of-day effect is more discoverable (player sees "reset in 5 minutes" at 23:54 BST).
Operator confirmed UTC (not BST) via clarification. Note: the *bounty's progress* still
ends at the same moment regardless of whether we call the boundary "00:00" or "23:59" —
the substantive change is the test/UI language and the moment a new "day" begins.

**Per-bounty vs per-claim semantics (clarified via question).** Operator wants
**per-bounty**: each completed bounty has its own `Claim` button. Claiming bounty #1
grants 1 token, bounty #2 grants 2, bounty #3 grants 3. Completing and claiming all
three = 6 tokens/day. The API contract is "claim THIS bounty" (1:1), so the
`bounty_id` field actually becomes meaningful. The `tokens` value is derived from the
*bounty's position in the deterministic 3-bounty set* (returned by
`get_daily_bounties`), not from the total-completion count.

#### Acceptance criteria

1. The `Claim` button on each completed bounty works end-to-end. No "bounty_id required"
   error. The frontend reads `b.id` from the response and passes it to the handler as
   `bounty_id`. `handleBountyClaim` is updated to use the correct key.
2. Each bounty's `Claim` button grants the correct token amount per position:
   - Bounty #1 in the deterministic set → 1 token
   - Bounty #2 → 2 tokens
   - Bounty #3 → 3 tokens
   - Maximum per day from bounties: 6 tokens
3. The cosmetic-fragment reward for completing all 3 is **removed** (no more 1-fragment
   bonus at 3/3). Cosmetic fragments are now awarded only via other paths (TBD).
4. Bounties reset at **UTC 23:59** (= BST 00:59 next day). Frontend shows a countdown
   to the next reset ("Resets in 4h 32m"). The progress is wiped at the boundary
   regardless of claim status — a player who didn't claim at 23:58 BST loses that
   day's progress at 00:00 BST.
5. The `/api/bounties` response payload is consistent: `bounty_id` is the key name on
   every bounty (not `id`). Update `bounties.py:152-159` to use `bounty_id`. Update
   `game.py:1086` (top-level bounties echo) if it re-keys. The frontend reads
   `b.bounty_id` everywhere.
6. New endpoint: keep `/api/bounties/claim` POST, but it now reads `bounty_id` and
   awards the position-based amount. The `bounty_claimed_date` gate is replaced with
   per-bounty `claimed_at` tracking (a column on `bounty_progress` or a separate
   `bounty_claims` table — implementer to choose, but the gate must be per-bounty so
   the player can claim 1, 2, 3 in any order without losing the others).
7. The migration to add the per-bounty `claimed_at` (or new table) is shipped with the
   ticket. Idempotent: `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.
8. The `Cosmetic Fragments` counter in the bounties panel header is removed (no
   fragments awarded from bounties anymore).
9. Backend: `bounty_claimed_date` column is dropped if no longer needed (verify
   nothing else reads it — T43 onboarding gate may still need it; if so, leave it).
10. Tests in `tests/test_bounties.py`:
    - `test_claim_button_sends_bounty_id` — POST with `{bounty_id: "bounty_jackpot"}`
      returns 200; without it returns 400 with a clear error.
    - `test_per_bounty_token_amounts` — claim bounty #1, get 1 token; #2 get 2; #3
      get 3; total = 6 across a full clean day.
    - `test_claim_independence` — claiming #1 doesn't lock #2 or #3.
    - `test_reset_at_2359_utc` — manually advance the bounty_date in DB to 23:59 UTC;
      spin/buy/redeem and confirm a new day's bounties are returned.
    - `test_no_cosmetic_fragments_awarded` — `response['rewards']` for a 3/3 claim
      has `cosmetic_fragments: 0`.
    - `test_payload_uses_bounty_id_key` — `/api/bounties` response payload contains
      `bounty_id` for every entry (regex check).

#### Implementation sketch

**`bounties.py`:**
```python
# At line 152, rename 'id' → 'bounty_id' (matches game.py's claim handler):
result.append({
    'bounty_id': b['id'],           # was 'id'
    'description': b['description'],
    'target': b['target'],
    'progress': row['progress'] if row else 0,
    'completed': row['completed'] if row else False,
    'reward_tokens': b['reward_tokens'],
    'position': <1|2|3 from selected.index>,  # NEW: 1-indexed position
    'claimed': row['claimed'] if row else False,  # NEW: per-bounty claim flag
})

# Add to BOUNTY_DEFS entries: per-position reward is now in the data, not the function.
# Update get_claim_rewards to take a bounty_id arg and return that bounty's reward:
def get_claim_rewards_for_bounty(conn, user_id, bounty_date, bounty_id):
    """Return {'tokens': N, 'cosmetic_fragments': 0} for the given bounty.
    Position in the deterministic 3-bounty set maps to 1/2/3 tokens."""
    selected = get_daily_bounties(user_id, bounty_date)
    for i, b in enumerate(selected):
        if b['id'] == bounty_id:
            return {'tokens': i + 1, 'cosmetic_fragments': 0}
    return None
```

**`game.py:3551` — claim handler:**
```python
bounty_id = (request.json or {}).get('bounty_id')
if not bounty_id:
    return jsonify({'error': 'bounty_id required'}), 400
# Replace 'bounty_claimed_date' check with per-bounty progress.claimed check.
# On success, set bounty_progress.claimed = TRUE (new column) and award
# get_claim_rewards_for_bounty(...).
```

**Migration `migrations/053_bounty_per_claim.sql`:**
```sql
ALTER TABLE bounty_progress
  ADD COLUMN IF NOT EXISTS claimed      BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS claimed_at   TIMESTAMPTZ;
-- Idempotent. The legacy `bounty_claimed_date` column on game_state is left in
-- place (T43 onboarding gate still references it; remove in a follow-up).
```

**`static/app.jsx:4846-4856`:**
```jsx
{bounties.map(b => (
  <div key={b.bounty_id} className="bounty-card">
    <div className="bounty-desc">{b.description}</div>
    <div className="bounty-progress-bar">
      <div className="bounty-progress-fill" style={{...}} />
    </div>
    <div className="bounty-progress-text">{fmt(b.progress)} / {fmt(b.target)}</div>
    {b.completed && !b.claimed && (
      <button className="bounty-claim-btn" onClick={() => handleBountyClaim(b.bounty_id)}>
        Claim +{b.position} token{b.position > 1 ? 's' : ''}
      </button>
    )}
    {b.claimed && <span className="bounty-claimed">✓ +{b.position} claimed</span>}
  </div>
))}
```

**Reset helper** (`bounties.py`):
```python
def get_bounty_reset_seconds(now_utc):
    """Seconds until the next UTC 23:59 boundary."""
    boundary = now_utc.replace(hour=23, minute=59, second=0, microsecond=0)
    if now_utc >= boundary:
        boundary += dt.timedelta(days=1)
    return int((boundary - now_utc).total_seconds())
```

#### Open question

None — all material decisions confirmed by operator.

---

### T118: Season 8 theme — backfill missing users on staging

- **Status:** [x] (2026-06-26) — `bin/backfill_season8_theme.py` created. Idempotent, refuses to run on non-staging DBs, supports `--dry-run`. 8/8 tests pass. 2 staging users updated (the rest were already covered by migration 050/051 + auth.py grant at registration).
- **Discovered:** 2026-06-26 (operator: "Season 8 theme cosmetic in the shop needs to be marked as owned and equipped for all players")
- **Depends on:** none
- **Files:**
  - `static/app.jsx` (the `/api/state` handler — add a self-heal on first load)
  - (no migration — staging-only; main already has migrations 050/051)

**Scope per operator clarification:** "This is a non-issue for staging as it's not real
live users, all testing users. It just needs to be able to work for all users on main when
we get to the reset. Make it work for testing7 on staging and it'll work for all users
on main." Staging currently has 10/125 users missing the theme; main has migrations 050+051
already applied and the registration flow (`auth.py:121-125`) grants `page_season8` to
every new user. The backfill is only needed for staging.

**What main will have at reset time:**
- Migration 050 grants `page_season8` to all existing users (owned).
- Migration 051 equips `page_season8` for all users (active).
- `auth.py:121-125` grants + equips it to every new registration after main cut-over.
- Net effect: every user on main will own and equip the S8 theme. No action needed.

**What staging needs:**
- A one-shot SQL to backfill the 10 missing users so testing7 and friends can validate
  the full game loop on staging without 1-2 visual oddities.
- The fix is **runtime**, not migration-based: we don't add a 052 migration because
  the deployment pipeline would replay it on main and the column is already correct
  there.

#### Acceptance criteria

1. All 125 staging users own `page_season8` in `owned_items` AND have it in
   `active_cosmetics` after the fix is applied.
2. The fix is a single SQL `UPDATE` (or a one-line Python script in
   `bin/backfill_season8_theme.py` that the operator runs once on staging).
3. New user registrations on staging continue to work as before (`auth.py:121-125`
   unchanged).
4. No production-impacting change: zero code change in `auth.py` or any migration.
5. The shop renders `page_season8` as "✓ Equipped" for all users in staging post-fix.

#### Implementation sketch

**`bin/backfill_season8_theme.py`** (new file, not a migration):
```python
"""One-shot backfill: grant + equip page_season8 to all staging users missing it.
Safe to re-run (idempotent). DO NOT run on main — migrations 050/051 already
cover main."""
import os, sys, psycopg2

db_url = os.environ.get('DATABASE_URL', '').split()
if 'wheeldb_staging' not in db_url[0]:
    print('REFUSING to run: DATABASE_URL does not point to wheeldb_staging')
    sys.exit(1)

conn = psycopg2.connect(db_url[0])
with conn.cursor() as cur:
    cur.execute("""
        UPDATE game_state SET
            owned_items = array_append(owned_items, 'page_season8'),
            active_cosmetics = array_append(
                ARRAY(SELECT c FROM unnest(active_cosmetics) AS c
                      WHERE c NOT LIKE 'page_season%'),
                'page_season8'
            )
        WHERE NOT ('page_season8' = ANY(owned_items))
           OR NOT ('page_season8' = ANY(active_cosmetics))
    """)
    print(f'Updated {cur.rowcount} users')
conn.commit()
```

Operator runs once on staging. New users continue to be granted via `auth.py:121-125`.

#### Open question

None.

---

### T119: Insurance system overhaul — flatten earning to 3 sources, remove recharge, rename to `insurance_tokens`

- **Status:** [ ] (planned 2026-06-26)
- **Discovered:** 2026-06-26 (operator: "Where is the user supposed to get insurance tokens from? Make 3 free/day, 1/2/3 from bounties, 5 on initial purchase. Remove other sources.")
- **Depends on:** T117 (bounty 1/2/3 token amounts) — T117 sets the per-bounty reward, T119
  wires the new `insurance_tokens` column to that reward.
- **Files:**
  - `static/app.jsx` (all references to `wagerTokens` → `insuranceTokens`; new daily-claim
    section above bounties panel; insurance buy UI cleanups)
  - `game.py` (insurance claim endpoint; new `insurance_tokens` column migration; remove
    all `wager_tokens` earning paths except the three sources; rename references)
  - `wagers.py` (remove `_recharge_wager_insurance` and `WAGER_INSURANCE_RECHARGE_SECONDS`)
  - `db.py`, `migrate.py` (column rename + drop)
  - `models.py` (drop `FISH_TO_WAGER_RATES` and the fishing token award path)
  - `static/styles.css` (`.wager-insurance-armed` readable colour; new
    `.free-tokens-section` styling)
  - `tests/test_insurance_tokens.py` (new file; replaces parts of
    `test_wager_tokens.py` + `test_insurance_buy_with_tokens.py`)

**Context (operator-confirmed 2026-06-26):** The current insurance system has a tangle of
overlapping token sources that confuse players:

| Source | Where | Status |
|---|---|---|
| Fishing catches (reel) | `game.py:2555-2594` (FISH_TO_WAGER_RATES) | **Remove** |
| Insurance charges recharge 1/10min | `wagers.py:167-175` (WAGER_INSURANCE_RECHARGE_SECONDS) | **Remove** |
| Onboarding step 3 grant (+100) | `game.py:3534` | **Remove** |
| Bounty daily claim (100/250/500) | `bounties.py:183-187` | **Replace with T117's 1/2/3 per-bounty** |
| Spending: insurance buy (1 token = 1 charge) | `game.py:3320-3360` | **Keep** |
| Spending: stake cost at high-stake ≥ 30% | `game.py:436, 465` | **Keep** |
| Initial purchase of `fish_to_wager` | never granted — must add **+5 once** | **Add** |

Operator wants the system reduced to exactly three sources:

1. **3 free tokens/day** from a claim button in a "Free Tokens" section above the bounties
   panel. Once-per-day, resets at UTC 23:59 (same as bounties). Section disappears (or
   collapses) once claimed.
2. **1/2/3 tokens per bounty** as set by T117 (max 6/day from bounties).
3. **5 tokens once** when the player first purchases the `fish_to_wager` upgrade (which
   itself is renamed to keep clarity, see Implementation sketch).

The column name also changes: `wager_tokens` → `insurance_tokens` throughout. The shop item
`fish_to_wager` is renamed to `insurance_unlock` (still costs 5,000 wins; the
"fish-to-tokens" semantic is dead).

**Problems with the current insurance button (also part of this ticket):**
1. The "🛡️ Insurance ARMED" indicator at `static/app.jsx:4659` has no explicit
   `color:` rule — it inherits the casino theme's default text colour which the operator
   reports as black-on-dark (unreadable). Compare `.wager-double-down-armed` at
   `static/styles.css:4269` which has `color: #ffd700` (gold). The insurance armed
   indicator needs the same treatment.
2. The "🪙 Buy Insurance (1 token)" button at `static/app.jsx:4667` shows up
   alongside the armed indicator, creating a confusing flow. The fix is to hide the buy
   button whenever insurance is armed (one state at a time, not both).
3. The frontend shows `wagerInsuranceCharges` (capped 3) and `wagerTokens` as two
   separate concepts. After T119, charges are derived from "tokens spent on insurance"
   — the player pays tokens for charges, and the max charges cap is removed (insurance
   has no max-charge cap; you can have as many as you've bought with tokens). The
   `/api/wager/insurance` endpoint should consume 1 token per arm (rather than decrement
   a free-recharging charge counter).

#### Acceptance criteria

**Column & schema:**
1. New column `insurance_tokens INT NOT NULL DEFAULT 0` on `game_state`. The old
   `wager_tokens` column is dropped via `migrations/054_rename_wager_to_insurance_tokens.sql`:
   ```sql
   ALTER TABLE game_state RENAME COLUMN wager_tokens TO insurance_tokens;
   ```
   (renames in place; preserves data. Operator chose rename over add+copy for simplicity).
2. `wager_insurance_charges` and `wager_insurance_armed` columns are also renamed to
   `insurance_charges` and `insurance_armed` (consistency).
3. `wager_insurance_last_recharge` is dropped (no more recharge).
4. `WAGER_INSURANCE_RECHARGE_SECONDS` is removed from `models.py`. `_recharge_wager_insurance`
   is removed from `wagers.py`. The `wager_insurance_max_charges` key in `/api/state` is
   removed.
5. `FISH_TO_WAGER_RATES` is removed from `models.py`. The `wager_tokens_awarded` block in
   `game.py:2555-2594` (the reel fishing award) is removed entirely. The condition
   `'fish_to_wager' in owned` is gone from `reel()`.
6. The onboarding step 3 grant at `game.py:3530-3537` is removed (no more 100 tokens on
   onboarding step 3).

**Earning paths (only 3):**
7. **Free daily claim:** new endpoint `POST /api/insurance/claim-free`. Awards 3 tokens
   once per UTC day. Gate on a new column `insurance_free_claimed_date DATE` (or reuse
   `bounty_claimed_date` — implementer to choose, but the gate must be daily).
   Atomic check: only credit if today's date != the column. Frontend: a new section above
   the bounties panel showing a "🪙 Claim 3 free tokens" button until clicked; once
   clicked, shows "✓ Claimed today — 3 tokens" for the rest of the day. Section collapses
   to a single line after claim (or disappears entirely — operator to pick).
8. **Bounty rewards:** 1/2/3 per bounty (T117). The `get_claim_rewards_for_bounty` in
   `bounties.py` returns `{'tokens': position, 'cosmetic_fragments': 0}`; the `game.py`
   claim handler adds to `insurance_tokens` instead of `wager_tokens`.
9. **Initial purchase:** when the player first buys `insurance_unlock` (the renamed
   `fish_to_wager`), the buy endpoint grants `+5` to `insurance_tokens` exactly once. A
   new boolean column `insurance_unlock_grant_given BOOLEAN DEFAULT FALSE` (or a check
   for `5` in the column — implementer to pick) prevents double-grant. After the
   initial grant, the item behaves as a normal purchased upgrade (no further token
   generation).

**Spending paths (unchanged, renamed):**
10. **Insurance buy (1 token = 1 charge):** `POST /api/wager/insurance/buy` is renamed
    to `POST /api/insurance/buy` and continues to work as before. The cap of
    `WAGER_INSURANCE_MAX_CHARGES` (currently 3) is removed — players can have as many
    charges as they've bought.
11. **Stake cost at high-stake ≥ 30%:** the spend path in `_resolve_spin` (game.py:436, 465)
    is updated to read `insurance_tokens` and decrement it. The `pay_with_tokens` flag
    in the request body still works.
12. **Activating insurance on a spin:** `POST /api/wager/insurance` (T74's original
    "arm insurance" endpoint) is updated to consume 1 insurance_token per arm instead of
    decrementing `wager_insurance_charges`. The "armed" state is preserved in
    `insurance_armed` (renamed from `wager_insurance_armed`).

**UI:**
13. The wager panel shows the player's `insuranceTokens` balance with the label
    "🪙 Insurance tokens" (no more "wager tokens").
14. The free-tokens section is above the bounties panel, single-row height, themed to
    match the bounties panel.
15. The "🛡️ Insurance (N)" button label uses the current `insuranceCharges` count.
    Clicking it arms insurance and consumes 1 token (toast: "🛡️ Insurance armed
    (1 token used)"). The "🛡️ Insurance ARMED (click to cancel)" indicator is given
    explicit `color: #44ddff` (cyan) and a subtle border, matching the
    `.wager-double-down-armed` style. The cancel button refund rule from T108
    (charge is NOT refunded) now reads: "the 1 token is NOT refunded".
16. The "🪙 Buy Insurance (1 token)" button is hidden when `insuranceArmed` is true.
17. The "Pay with tokens" toggle in the wager panel is renamed to "Pay with insurance
    tokens" and the description is updated.

**Tests:**
18. New `tests/test_insurance_tokens.py` (~25 tests):
    - `test_no_recharge_in_state` — `/api/state` no longer includes
      `wager_insurance_max_charges` or `wager_insurance_last_recharge`.
    - `test_fishing_does_not_award_tokens` — `reel()` for a user owning
      `insurance_unlock` does not increase `insurance_tokens`.
    - `test_free_claim_3_tokens` — first call to `/api/insurance/claim-free` returns
      3 tokens, second call in same UTC day returns 409 "Already claimed today".
    - `test_free_claim_resets_at_2359_utc` — manually advance
      `insurance_free_claimed_date` to yesterday; claim succeeds.
    - `test_initial_purchase_grants_5` — buying `insurance_unlock` increments
      `insurance_tokens` by 5.
    - `test_initial_purchase_no_double_grant` — buying a second `insurance_unlock` (e.g.
      an admin grants via DB) does NOT increment tokens a second time.
    - `test_arm_consumes_token` — `POST /api/insurance/arm` (renamed) with
      `tokens >= 1` succeeds and decrements tokens by 1.
    - `test_arm_no_tokens_returns_403` — same call with `tokens == 0` returns 403.
    - `test_buy_charge_no_cap` — buying 10 charges in a row succeeds (no cap).
    - `test_stake_spends_tokens` — `_resolve_spin` with `stake_pct >= 30` and
      `pay_with_tokens=True` decrements `insurance_tokens`.
    - `test_button_color_readable` — Playwright check that
      `.wager-insurance-armed` has `color` not equal to the body background.
    - `test_buy_button_hidden_when_armed` — when `insuranceArmed == true`, the
      "Buy Insurance" button is not in the DOM.
    - `test_column_renamed` — DB schema check: `insurance_tokens` exists,
      `wager_tokens` does not.
    - `test_onboarding_grant_removed` — registering a new user, manually setting
      `onboarding_step = 3`, hitting any spin endpoint, does NOT increment tokens.

#### Implementation sketch

**Migration `migrations/054_rename_wager_to_insurance_tokens.sql`:**
```sql
-- T119: rename wager_tokens to insurance_tokens (operator chose rename over copy).
-- Also rename insurance charge/arm columns and drop recharge timestamp.
ALTER TABLE game_state RENAME COLUMN wager_tokens            TO insurance_tokens;
ALTER TABLE game_state RENAME COLUMN wager_insurance_charges  TO insurance_charges;
ALTER TABLE game_state RENAME COLUMN wager_insurance_armed    TO insurance_armed;
ALTER TABLE game_state DROP  COLUMN wager_insurance_last_recharge;
-- New: gate the daily free-claim.
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS insurance_free_claimed_date DATE;
-- New: gate the initial-purchase 5-token grant.
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS insurance_unlock_grant_given BOOLEAN DEFAULT FALSE;
-- Drop onboarding-related column? No — keep for T43.
```

**`game.py:3320` — insurance buy endpoint (renamed):**
```python
@game_bp.route('/api/insurance/buy', methods=['POST'])
@login_required
@csrf.exempt
def insurance_buy_with_tokens():
    # ... same as /api/wager/insurance/buy but reads/writes insurance_tokens
    # and has no max-charges cap.
```

**`game.py` — new free-claim endpoint:**
```python
@game_bp.route('/api/insurance/claim-free', methods=['POST'])
@login_required
@csrf.exempt
def insurance_claim_free():
    err = require_json()
    if err:
        return err
    FREE_PER_DAY = 3
    today = dt.datetime.now(timezone.utc).date()
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            if gs.get('insurance_free_claimed_date') == today:
                return jsonify({'error': 'Already claimed today'}), 409
            cur.execute(
                '''UPDATE game_state
                   SET insurance_tokens = insurance_tokens + %s,
                       insurance_free_claimed_date = %s
                   WHERE user_id = %s''',
                (FREE_PER_DAY, today, current_user.id),
            )
    return jsonify({'ok': True, 'tokens_awarded': FREE_PER_DAY,
                    'insurance_tokens': int(gs.get('insurance_tokens', 0)) + FREE_PER_DAY})
```

**`static/app.jsx:4658-4668` — insurance button block:**
```jsx
{ownedItems.includes('insurance_unlock') && insuranceArmed && (
  <button className="wager-insurance-armed wager-cancel-btn" onClick={handleCancelInsurance}>
    🛡️ Insurance ARMED (click to cancel)
  </button>
)}
{ownedItems.includes('insurance_unlock') && !insuranceArmed && insuranceTokens >= 1 && (
  <button className="wager-action-btn" onClick={handleInsurance}>
    🛡️ Arm Insurance ({insuranceTokens} tokens)
  </button>
)}
{!insuranceArmed && ownedItems.includes('insurance_unlock')
  && insuranceTokens >= 1 && insuranceCharges < 99 && (
  <button className="wager-action-btn wager-buy-insurance-btn"
          onClick={handleBuyInsuranceWithTokens}>
    🪙 Buy 1 charge (1 token)
  </button>
)}
```

**`static/styles.css:4269` — add explicit colour:**
```css
.wager-insurance-armed {
  font-size: 0.8rem;
  color: #44ddff;            /* NEW: cyan, readable on casino dark bg */
  font-weight: 700;
  text-align: center;
  padding: 4px 8px;
  border: 1px solid #44ddff; /* NEW: matching border */
  border-radius: 4px;
  animation: pulse-glow 1.2s ease-in-out infinite alternate;
  white-space: normal;
  line-height: 1.2;
}
```

**Free-tokens section in JSX (above bounties panel):**
```jsx
<div className="free-tokens-section">
  {insuranceFreeClaimedToday ? (
    <div className="free-tokens-claimed">✓ 3 free tokens claimed today</div>
  ) : (
    <button className="free-tokens-claim-btn"
            onClick={handleClaimFreeTokens}>
      🪙 Claim 3 free tokens
    </button>
  )}
</div>
```

#### Open question

None — operator confirmed: 3 free/day, 1/2/3 per bounty, 5 on initial purchase, no other
sources, all UI strings renamed.

---

### T120: Remove Hall of Fame — 🏆 button, modal, and `/api/legacy-boards` endpoint

- **Status:** [x] (2026-06-26) — 🏆 button removed from user-bar, `showLegacyBoards` modal block deleted, `handleShowLegacyBoards` + state removed, `/api/legacy-boards` endpoint deleted. `legacy_wins` data column preserved. README updated. 359 → 373 pass (no regressions).
- **Discovered:** 2026-06-26 (operator: "What is the 'Hall of Fame' button at the top supposed
  to do? This seems like a misplaced duplication of the 'Past Winners' section of the
  leaderboard. Remove it.")
- **Depends on:** none
- **Files:**
  - `static/app.jsx` (delete the 🏆 button + the `showLegacyBoards` modal block + the
    `handleShowLegacyBoards` handler + the `legacyBoards` state)
  - `game.py` (delete the `/api/legacy-boards` endpoint at line 3781-3794)
  - `tests/test_legacy_boards.py` (delete or convert to a smoke test that the endpoint
    no longer exists)

**Context:** The 🏆 button in the user-bar (`static/app.jsx:4484`) opens a modal titled
"🏆 Hall of Fame — Legacy Wins" which is a top-50 leaderboard of all-time `legacy_wins`
across all seasons. The "Past Winners" tab in the regular leaderboard panel
(`static/app.jsx:2129-2146`) shows season winners for the *current season*. These are
different views, but the operator considers the Hall of Fame redundant — the
`legacy_wins` data is still tracked (it's preserved on prestige and visible in the
prestige panel as a "Legacy: N wins" badge), but a global all-time leaderboard isn't
needed for S8 launch.

**Operator decision (2026-06-26):** Remove the 🏆 button, the modal, AND the API endpoint.
The `legacy_wins` data itself is preserved — only the leaderboard view goes away. If we
want a "Legacy" panel later in 8.X, we can re-add it with different framing.

#### Acceptance criteria

1. The 🏆 button is removed from the user-bar. The user-bar now has: 👤 name, 📊 Stats,
   📖 Fish Encyclopaedia, ⚡ Low-Spec, 🖱️ Parallax (if wormhole), 💬 Chat (desktop),
   📋 Patch Notes, Logout.
2. The `showLegacyBoards` state and `handleShowLegacyBoards` handler are removed from
   `app.jsx`. The modal JSX block (lines 4397-4421) is deleted.
3. The `/api/legacy-boards` endpoint in `game.py` is deleted.
4. The `legacy_boards` import in `tests/test_legacy_boards.py` is removed; the file
   either:
   - (a) is deleted entirely (operator to choose), OR
   - (b) becomes a 2-line smoke test that `GET /api/legacy-boards` returns 404.
5. No other code references `legacyBoards`, `setShowLegacyBoards`, or
   `handleShowLegacyBoards`. The operator can verify with `grep -n "legacy" static/app.jsx`
   to ensure no orphan references remain (the data column `legacy_wins` should still
   appear in DB queries — that's fine).
6. `pytest` passes (no regression on the other 360 tests).
7. Playwright check: the user-bar in staging shows 8 buttons (was 9) on a 1920×1080
   viewport.

#### Implementation sketch

**`static/app.jsx` changes:**
```diff
@@ line 4484 @@
-        <button className="stats-btn" title="Hall of Fame — Legacy Wins" onClick={handleShowLegacyBoards}>🏆</button>
         <button className="logout-btn" onClick={handleLogout}>Logout</button>

@@ lines 3897-3898 @@
-  const [showLegacyBoards, setShowLegacyBoards]     = useState(false);
-  const [legacyBoards, setLegacyBoards]             = useState([]);

@@ lines 4257-4261 @@
-  const handleShowLegacyBoards = useCallback(async () => {
-    setShowLegacyBoards(true);
-    const { ok, data } = await apiGame('/api/legacy-boards');
-    if (ok) setLegacyBoards(data.boards || []);
-  }, []);

@@ lines 4397-4421 @@
-  {/* Legacy boards modal (T36) */}
-  {showLegacyBoards && (
-    <div className="onboarding-overlay" onClick={() => setShowLegacyBoards(false)}>
-      ...full modal block...
-    </div>
-  )}
```

**`game.py:3781-3794`:** delete the endpoint. No other code calls it (verify with
`grep -rn "legacy-boards" .` before deletion).

**`tests/test_legacy_boards.py`:** delete the file. The endpoint didn't have a test in
`tests/` before, but if the operator added one in earlier seasons it should be removed.

#### Open question

None.

---

### T121: Prestige rework — drop efficiency/legacy, move trigger to shop with confirmation modal

- **Status:** [x] (2026-06-26) — `prestige_efficiency` and `prestige_legacy` removed from shop; `/api/buy` returns 403 'Item retired' for them. `get_legacy_keep_count` and `compute_wins_kept` both return 0. Side-panel Prestige button + `showPrestigeConfirm` modal deleted. Shop buy of `prestige_unlock` opens a patch-notes-style confirmation modal (title "⚠️ Prestige Reset", Confirm/Cancel); Confirm calls atomic `/api/prestige` (deducts 1M wins on first buy, adds the unlock, and resets state in one tx). Threshold still scales by 1.05× per level (T111). 22 new tests in `tests/test_prestige.py`; full suite 395 pass, 1 skip.
- **Discovered:** 2026-06-26 (operator: "Remove prestige_efficiency + prestige_legacy. No
  side-panel button. Buying prestige in the shop shows a confirmation modal first.")
- **Depends on:** none (independent of T117/T118/T119)
- **Files:**
  - `models.py` (mark `prestige_efficiency` and `prestige_legacy` as deprecated —
    removed from the buyable item list)
  - `static/app.jsx` (remove side-panel Prestige button + `showPrestigeConfirm` modal;
    wire shop buy for `prestige_unlock` to show confirmation modal first)
  - `static/styles.css` (new `.prestige-confirm-modal` class for the patch-notes-style
    modal; can reuse `.onboarding-modal` for now and add a dedicated variant later)
  - `game.py` (modify `/api/prestige` to be atomic — adding the item AND performing the
    reset in a single call; reject purchases of deprecated items)
  - `prestige.py` (drop `compute_wins_kept` efficiency-based calc; `get_legacy_keep_count`
    returns 0; `PRESTIGE_RESET_COLUMNS` retains `wins` reset to 0 — no carry-over)
  - `tests/test_prestige.py` (new file; ~15 tests replacing `test_prestige_scaling.py`)

**Operator's vision (2026-06-26):** "Prestige needs a brief re-work. I don't like the
idea of the additional prestige upgrades such as efficiency and legacy, can these be
removed for now. I also don't want a button for prestige in the side panel, it should
simply happen when the player buys it in the shop. Before triggering the prestige,
clicking buy in the shop should popup a message in the middle of the screen (similar
method to patch notes, copy from that section of code implementation) that warns them
that prestige will reset all upgrades and apply a permanent stacking increase (basically
explain how it works, act's as a confirmation) with a 'confirm prestige' button and a
'cancel' button. Cancel should simply close the popup, confirm should begin the
prestige sequence."

**Sub-tasks:**

A. **Remove `prestige_efficiency` and `prestige_legacy` from the shop.**
   - In `models.py:233-235`, keep `prestige_unlock` but mark `prestige_efficiency` and
     `prestige_legacy` as `RETIRED` (e.g. by moving them to a `RETIRED_ITEMS` constant
     that's no longer referenced from the buyable list).
   - In the `static/app.jsx:2465-2466` shop definition, delete those two entries.
   - The `/api/buy` endpoint should return 403 if the player tries to buy a `RETIRED`
     item. (Per operator: "removed from shop and buy api disabled in case someone tries
     to buy it maliciously.") Operator confirmed no real players own these — but the
     defense-in-depth is still in place.
   - For any player who somehow has them in `owned_items` (staging legacy data, future
     edge cases), they remain in the owned list but the prestige code no longer
     references them. `get_legacy_keep_count` returns 0 always. `compute_wins_kept`
     always returns 0 (no efficiency carry-over).

B. **Remove the side-panel Prestige button.**
   - In `static/app.jsx:4824-4837`, delete the `season8-prestige-panel` div, the
     Prestige button, and the `showPrestigeConfirm` modal block at line 4383-4395.
   - Remove the `setShowPrestigeConfirm` and `showPrestigeConfirm` state.
   - The legacy-wins badge can stay in the prestige panel (it's a passive display).

C. **Wire the shop buy to show a confirmation modal first.**
   - In `static/app.jsx`, the `ShopItem` component's `onBuy` handler for `prestige_unlock`
     needs special handling. Easiest implementation: in the shop's `onBuy` prop
     (`handleBuyItem`), check if the item id is `prestige_unlock`; if so, set a new
     state `showPrestigeBuyConfirm` to true and store the item's display cost in another
     state. The buy is NOT performed until the modal confirms.
   - The modal is built from the same primitives as `PatchNotesPanel`
     (`static/app.jsx:2942-2964`): a `.stats-overlay` div with a centred card, close
     button, body content. The body contains:
     - Title: "⚠️ Prestige Reset"
     - Body: warning text + the player-facing explanation
     - Buttons: "Confirm Prestige" (primary, calls `/api/prestige`) and "Cancel"
       (secondary, closes the modal)
   - On confirm, the modal closes, `/api/prestige` is called, and the response updates
     the same local state that `handlePrestige` did (setWins(0), setPrestigeLevel(...),
     etc.). The player sees their wins go to 0 and their prestige level go up by 1.

D. **Make `/api/prestige` atomic: it both buys the unlock and performs the reset.**
   - The current flow: `/api/buy prestige_unlock` adds the item (1M wins deducted), then
     a separate `/api/prestige` POST does the reset. There's a race window: a player
     could buy the unlock, the buy succeeds, but the prestige call fails — leaving the
     player with 0 wins and the unlock but no prestige applied. T121 collapses this to
     one atomic call.
   - New behaviour: `POST /api/prestige` accepts no body. It:
     1. Loads the player state FOR UPDATE.
     2. If `prestige_unlock` is NOT in `owned_items` and wins >= 1,000,000, deduct
        1,000,000 wins and add the item.
     3. If `prestige_unlock` is in `owned_items` and wins >= `get_prestige_threshold`,
        just perform the prestige reset.
     4. If wins < threshold, return 403 with the current wins + threshold.
     5. Perform the reset (set `prestige_level = current + 1`, etc.).
   - One transaction, no race. The shop buy and the prestige are the same call.
   - Backwards-compat: existing callers of `/api/prestige` (none in JSX after T121 since
     the side-panel button is gone) continue to work — they just pay the 1M if they
     didn't own the unlock yet.

E. **Remove `compute_wins_kept` efficiency-based carry-over.**
   - The current `compute_wins_kept` returns `int(wins * 0.1 * efficiency_level)`. With
     efficiency retired, this is always 0. Replace with a simple
     `def compute_wins_kept(wins, owned_items): return 0`. The prestige reset
     (`game.py:3439`) then sets `wins = 0` cleanly.
   - Update `PRESTIGE_RESET_COLUMNS` to confirm `wins` is in the reset list (it already
     is — `prestige.py:23`).

F. **Drop `get_legacy_keep_count` influence.**
   - `get_legacy_keep_count` currently returns `_count_owned(owned_items, 'prestige_legacy')`.
     With legacy retired, this is always 0. Replace the body with `return 0`. The
     `filter_kept_items` call at `game.py:3440` will then keep only cosmetic items
     (wager items are also dropped per the existing `WAGER_ITEM_IDS` logic — that's
     already correct).
   - The `prestige.py:138-143` helper can stay in place but always return 0, OR be
     deleted entirely. The implementer should delete it to keep the surface area clean.

#### Acceptance criteria

1. `prestige_efficiency` and `prestige_legacy` do not appear in the shop JSX
   (`grep -n "prestige_efficiency\|prestige_legacy" static/app.jsx` returns no shop
   definitions).
2. The `/api/buy` endpoint returns 403 `{'error': 'Item retired'}` for these two
   item IDs. Direct API test: `POST /api/buy` with `{'item_id': 'prestige_efficiency'}`
   returns 403.
3. The side-panel Prestige button and its confirmation modal are deleted. The
   `season8-prestige-panel` JSX block no longer renders a `<button>Prestige</button>`.
4. The `legacy_wins` display badge (line 4828) remains visible if the player has
   `legacy_wins > 0`.
5. The shop's `prestige_unlock` item, when clicked, opens a centred modal (the
   `showPrestigeBuyConfirm` state). The modal has the title "⚠️ Prestige Reset" and
   a body that explains:
   - **What happens:** Your wins, losses, streak, and all non-cosmetic upgrades will
     be reset. Your **prestige level** will increase by 1, granting a permanent
     +2% to your win payout. Cosmetic items, your aquarium, and your legacy wins
     are preserved.
   - **Why it matters:** Each prestige level makes every future win worth more.
     Higher levels cost more wins to achieve (the threshold scales by 1.05× per
     level), so the bonus compounds. The maximum is level 20 (+40% wins).
   - **Cancellation:** No penalty. Click "Cancel" and nothing changes.
6. The modal's "Confirm Prestige" button calls `POST /api/prestige` with `{}` body.
   On success, the local state updates (wins → 0, prestige level → +1, legacy wins
   → previous wins + previous legacy wins). A toast appears: ` Prestiged to Level
   {N}!`.
7. The modal's "Cancel" button just closes the modal. No API call. No state change.
8. `POST /api/prestige` is atomic: if the player doesn't own `prestige_unlock` and
   wins >= 1M, the call deducts 1M wins, adds the item, and performs the reset in
   one transaction. If wins < 1M, returns 403 with the current wins and the threshold.
9. The legacy_keep and efficiency carry-over are dead code: `compute_wins_kept`
   returns 0 unconditionally, and the new `wins` after prestige is 0. Test asserts
   that a player with 1.5M wins and 0 owned efficiency/legacy items prestiged with
   the new flow ends with wins == 0 and legacy_wins == 1,500,000.
10. Tests in `tests/test_prestige.py` (~15 tests):
    - `test_efficiency_not_in_shop` — `grep` test on static/app.jsx for the literal
      strings.
    - `test_legacy_not_in_shop` — same for `prestige_legacy`.
    - `test_buy_efficiency_returns_403` — direct API test.
    - `test_buy_legacy_returns_403` — same.
    - `test_prestige_endpoint_atomic` — fresh user with 1.5M wins, no owned items,
      POST /api/prestige → wins=0, prestige_level=1, legacy_wins=1,500,000,
      prestige_unlock in owned_items.
    - `test_prestige_endpoint_insufficient_wins` — fresh user with 999,999 wins,
      POST /api/prestige → 403 with `current_wins: 999999, threshold: 1000000`.
    - `test_prestige_endpoint_already_owned` — user owns `prestige_unlock` and
      has 1.1M wins, POST /api/prestige → wins=0, prestige_level=1, no extra 1M
      deduction (the second-buy is free).
    - `test_prestige_resets_columns` — full `PRESTIGE_RESET_COLUMNS` list is
      checked to be 0/false/empty after prestige.
    - `test_prestige_preserves_cosmetics` — `active_cosmetics`, `aquarium_species`,
      `cosmetic_fragments` are unchanged.
    - `test_prestige_threshold_scales` — after reaching level 1, the next
      threshold is `round(1_000_000 * 1.05) == 1,050,000`.
    - `test_no_legacy_carryover` — owning 3 prestige_legacy items does not change
      the items kept (the filter returns only cosmetics).
    - `test_no_efficiency_carryover` — owning 3 prestige_efficiency items does
      not change the post-prestige wins (always 0).
    - `test_modal_renders_in_shop` — Playwright check that clicking the
      `prestige_unlock` item in the shop opens a modal with title "⚠️ Prestige
      Reset" and both buttons.
    - `test_modal_cancel_no_api_call` — Playwright check that clicking Cancel
      does NOT trigger a network call to `/api/prestige`.
    - `test_modal_confirm_triggers_prestige` — Playwright check that clicking
      Confirm fires `POST /api/prestige` (network spy).
    - `test_side_panel_button_removed` — Playwright check that `.prestige-btn`
      is not in the DOM.

#### Implementation sketch

**`models.py:233-235`** — split into active vs retired:
```python
PRESTIGE_ITEMS = {
    'prestige_unlock': {'cost': 1_000_000, 'requires': None},
}
RETIRED_ITEMS = {
    'prestige_efficiency': {'cost': 500_000,   'requires': 'prestige_unlock',
                            'retired_in': 'T121'},
    'prestige_legacy':     {'cost': 1_000_000, 'requires': 'prestige_unlock',
                            'retired_in': 'T121'},
}
# Update the `models.ITEM_DEFS` dict (or whatever feeds the shop) to read from
# PRESTIGE_ITEMS for prestige and not include RETIRED_ITEMS.
```

**`/api/buy` guard:**
```python
if item_id in RETIRED_ITEMS:
    return jsonify({'error': 'Item retired'}), 403
```

**`prestige.py:138-143`** — `get_legacy_keep_count` always returns 0:
```python
def get_legacy_keep_count(owned_items):
    """Retired in T121: no functional upgrades are kept on prestige. Players
    must re-buy their items after each prestige."""
    return 0
```

**`prestige.py:146-154`** — `compute_wins_kept` always returns 0:
```python
def compute_wins_kept(wins, owned_items):
    """Retired in T121: prestige_efficiency no longer exists. Wins are
    fully reset to 0 on prestige; the legacy_wins column carries the
    prior total forward."""
    return 0
```

**`game.py:3406-3490`** — atomic prestige endpoint:
```python
@game_bp.route('/api/prestige', methods=['POST'])
@login_required
@csrf.exempt
def prestige_reset():
    """Atomic prestige: deduct 1M wins (if not yet owned), add the unlock,
    and reset state. All in one transaction."""
    err = require_json()
    if err:
        return err
    PRESTIGE_COST = 1_000_000
    with db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            gs = _load_game_state(cur, current_user.id, for_update=True)
            already_owned = 'prestige_unlock' in gs['owned_items']
            current_wins = int(gs['wins'])
            current_level = gs.get('prestige_level', 0)
            if current_level >= MAX_PRESTIGE_LEVEL:
                return jsonify({'error': 'Already at max prestige'}), 403
            if already_owned:
                threshold = get_prestige_threshold(gs['owned_items'], current_level)
                if current_wins < threshold:
                    return jsonify({'error': f'Need {threshold} wins to prestige',
                                    'current_wins': current_wins, 'threshold': threshold}), 403
                cost = 0
            else:
                if current_wins < PRESTIGE_COST:
                    return jsonify({'error': f'Need {PRESTIGE_COST} wins to prestige',
                                    'current_wins': current_wins, 'threshold': PRESTIGE_COST}), 403
                cost = PRESTIGE_COST
            new_wins = 0
            new_level = current_level + 1
            new_prestige_count = gs.get('prestige_count', 0) + 1
            new_legacy_wins = int(gs.get('legacy_wins', 0)) + current_wins
            kept_items = filter_kept_items(gs['owned_items'], 0)  # 0 functional kept
            if not already_owned:
                kept_items = list(kept_items) + ['prestige_unlock']
            # ... same UPDATE pattern as before, with cost applied to wins
            cur.execute('''UPDATE game_state SET
                              wins = wins - %s,
                              prestige_level = %s,
                              prestige_count = %s,
                              legacy_wins = %s,
                              owned_items = %s,
                              ... (all PRESTIGE_RESET_COLUMNS) ... = defaults
                           WHERE user_id = %s''',
                        (cost, new_level, new_prestige_count, new_legacy_wins,
                         kept_items, current_user.id))
        # ... post system message + bounty increment + community goal
    return jsonify({'prestige_level': new_level, ...})
```

**`static/app.jsx:4824-4837`** — delete the side-panel Prestige button block.

**`static/app.jsx:4383-4395`** — delete the old `showPrestigeConfirm` modal block.

**New state + modal in `static/app.jsx`:**
```jsx
const [showPrestigeBuyConfirm, setShowPrestigeBuyConfirm] = useState(false);
const [prestigeBuyCost, setPrestigeBuyCost]               = useState(1_000_000);

const handleShopBuy = useCallback(async (item) => {
  if (item.id === 'prestige_unlock') {
    setPrestigeBuyCost(wins >= 1_000_000 && !ownedItems.includes('prestige_unlock')
                       ? 1_000_000 : 0);
    setShowPrestigeBuyConfirm(true);
    return;
  }
  // ... existing buy logic for other items
}, [wins, ownedItems]);

const handleConfirmPrestigeBuy = useCallback(async () => {
  setShowPrestigeBuyConfirm(false);
  const { ok, data } = await apiGame('/api/prestige', { method: 'POST', body: '{}' });
  if (ok) {
    setPrestigeLevel(data.prestige_level);
    setPrestigeCount(data.prestige_count);
    setLegacyWins(data.legacy_wins);
    setWins(0);
    setLosses(0);
    setStreak(0);
    setSpinCount(0);
    setWagerStreak(0);
    setWagerLastStake(0);
    showToast(` Prestiged to Level ${data.prestige_level}!`);
    refreshBountiesAndGoal();
    refreshPrestigeInfo();
  } else {
    showToast(data.error || 'Prestige failed');
  }
}, [showToast]);
```

**New modal JSX (placed where the old `showPrestigeConfirm` modal was):**
```jsx
{showPrestigeBuyConfirm && (
  <div className="stats-overlay" onClick={() => setShowPrestigeBuyConfirm(false)}>
    <div className="patch-notes-card prestige-confirm-card"
         onClick={e => e.stopPropagation()}
         style={{ maxWidth: '460px' }}>
      <div className="stats-title">⚠️ Prestige Reset</div>
      <button className="stats-close-btn"
              onClick={() => setShowPrestigeBuyConfirm(false)}>✕</button>
      <div className="patch-notes-body" style={{ padding: '8px 0' }}>
        <p style={{ color: '#ccc', lineHeight: 1.6, fontSize: '0.82rem' }}>
          Prestige will <strong style={{ color: '#ff8866' }}>reset your wins, losses,
          streak, and all non-cosmetic upgrades</strong> to zero. In return, your
          <strong style={{ color: 'var(--p)' }}> prestige level goes up by 1</strong>,
          granting a permanent <strong style={{ color: 'var(--p)' }}>+2% to your
          win payout</strong>.
        </p>
        <p style={{ color: '#aaa', lineHeight: 1.6, fontSize: '0.78rem' }}>
          Each level compounds: level 5 = 1.10× wins, level 20 = 1.40× wins (max).
          Higher levels cost more wins to achieve (threshold scales by 1.05× per
          level). Your <strong style={{ color: '#44ddff' }}>cosmetics, aquarium
          species, and legacy wins are preserved</strong>.
        </p>
        {prestigeBuyCost > 0 && (
          <p style={{ color: '#ffd700', fontSize: '0.75rem' }}>
            Cost: {fmt(prestigeBuyCost)} wins (first prestige only).
          </p>
        )}
      </div>
      <div style={{ display: 'flex', gap: '12px', justifyContent: 'center',
                    marginTop: '16px' }}>
        <button className="prestige-confirm-btn"
                onClick={handleConfirmPrestigeBuy}
                style={{ background: 'linear-gradient(135deg, #ff8866, #ff4444)',
                         color: '#fff', padding: '10px 24px', border: 'none',
                         borderRadius: '5px', cursor: 'pointer', fontFamily: 'inherit',
                         fontSize: '0.85rem', letterSpacing: '2px', textTransform: 'uppercase' }}>
          Confirm Prestige
        </button>
        <button onClick={() => setShowPrestigeBuyConfirm(false)}
                style={{ background: 'rgba(255,255,255,0.1)', color: '#ccc',
                         padding: '10px 24px', border: '1px solid #555',
                         borderRadius: '5px', cursor: 'pointer', fontFamily: 'inherit',
                         fontSize: '0.85rem', letterSpacing: '2px', textTransform: 'uppercase' }}>
          Cancel
        </button>
      </div>
    </div>
  </div>
)}
```

#### Open question

None — operator confirmed all material decisions.

---
