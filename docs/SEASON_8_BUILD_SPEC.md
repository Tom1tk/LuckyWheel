# Season 8 — Living Design & Build Specification

> **Status:** Living document. This is the authoritative implementation plan for
> Season 8. It is not a review — it specifies *exactly* what we are building and
> how it integrates with the existing codebase.
>
> **Source of truth:** `SEASON_8_PLANNING.md` (design rationale) → this document
> (build spec) → `SEASON_8_TICKETS.md` (task breakdown) → `SEASON_8_PROGRESS.md`
> (execution record).
>
> **Hardened spec:** All spec gaps identified during audit have been resolved.
> Decisions are recorded in `SEASON_8_SPEC_GAPS_ANSWERS.md` and
> `SEASON_8_SPEC_GAPS_ANSWERS2.md`. No separate amendment document — this spec
> is fully implementable as written.
>
> **Codebase root:** `/home/user/wheel-app-staging/` (Flask + PostgreSQL + React/JSX)
> **Staging database:** `wheeldb_staging` (port 5001)
>
> **Season 7 end constraint:** The current season (7) must end gracefully using
> the existing `_perform_rollover()` mechanism in `seasons.py`. Do NOT schedule
> its end date, modify `ends_at`, or trigger rollover. The operator will provide
> direct guidance on when to end Season 7. All Season 8 code is built and tested
> on staging first; production deployment is a separate, operator-controlled step.

---

## Table of Contents

1. [Architecture overview](#1-architecture-overview)
2. [Season 8 economy reset](#2-season-8-economy-reset)
3. [Wager system](#3-wager-system)
4. [Wheel modes](#4-wheel-modes)
5. [Prestige system](#5-prestige-system)
6. [Fishing integration](#6-fishing-integration)
7. [Protection rework](#7-protection-rework)
8. [Daily bounties](#8-daily-bounties)
9. [Community goals (replaces Community Pot)](#9-community-goals)
10. [Leaderboard reset & legacy boards](#10-leaderboard-reset--legacy-boards)
11. [Build loadouts](#11-build-loadouts)
12. [Chat revival & auto-post messages](#12-chat-revival--auto-post-messages)
13. [Singularity rework](#13-singularity-rework)
14. [Number formatting](#14-number-formatting)
15. [Onboarding flow](#15-onboarding-flow)
16. [Themes](#16-themes)
17. [Dynamic wheel graphic](#17-dynamic-wheel-graphic)
18. [Auto-spin policy](#18-auto-spin-policy)
19. [Database migrations](#19-database-migrations)
20. [API surface changes](#20-api-surface-changes)
21. [Frontend changes](#21-frontend-changes)
22. [Rollout sequence](#22-rollout-sequence)
23. [Implementation bug fixes](#23-implementation-bug-fixes)
24. [Work breakdown](#24-work-breakdown)

---

## 1. Architecture overview

### Existing stack (what we build on)

All paths relative to `/home/user/wheel-app-staging/`.

| Layer | File(s) | Role |
|---|---|---|
| WSGI app | `app.py` | Flask factory; blueprints: `auth_bp`, `game_bp`, `chat_bp` |
| Game logic | `game.py` | All game endpoints: `/api/spin`, `/api/tick`, `/api/buy`, `/api/cast`, `/api/reel`, `/api/equip`, `/api/community-pot`, `/api/leaderboard`, etc. |
| Game constants | `models.py` | `SHOP_ITEMS`, `FISH_SKINS`, `INFINITE_UPGRADES`, `FISH_CATALOG`, multiplier functions, class constants |
| Season lifecycle | `seasons.py` | `ensure_current_season()` (auto-rolls on expiry), `advance_season()`, `_perform_rollover()` — resets `game_state`, snapshots to `user_season_history`, resets `community_pot` |
| DB access | `db.py` | `ThreadedConnectionPool` (2–20 conns), `@db_connection` context manager |
| Migrations | `migrate.py` + `migrations/NNN_*.sql` | Sequential SQL migration runner; tracking table `schema_migrations` |
| Frontend | `static/app.jsx` → `static/app.js` | Single-page React app (JSX compiled to JS via Babel); `static/index.html` entry point |
| Chat | `chat.py` | `chat_bp` — messages, rate limiting |
| Security | `security.py`, `auth.py` | CSRF, login_required, JSON body validation |

### Key existing patterns we follow

- **Spin resolution pipeline:** `_build_spin_context()` → `_resolve_spin()` → `_events_to_response()`. Spin logic is a pure function of immutable context + state. Season 8 wager logic slots into this pipeline.
- **Migrations:** `NNN_description.sql`, next number is `031`. Idempotent (`IF NOT EXISTS`). Tracked in `schema_migrations`.
- **Season rollover:** `_perform_rollover()` in `seasons.py` resets all `game_state` columns to defaults, snapshots to `user_season_history` + `season_snapshots`, resets `community_pot`. Season 8 must extend this to preserve prestige levels and reset wager/mode/bounty state.
- **Shop items:** `SHOP_ITEMS` dict in `models.py` with `cost` and `requires` keys. `INFINITE_UPGRADES` for repeatable axes with `tier_costs` + `inf_base_cost` + `inf_scale`.
- **Rate limiting:** `@limiter.limit()` decorators on endpoints. Wager spins reuse the existing `/api/spin` limiter.
- **Frontend:** React components in `static/app.jsx`. State polling via `/api/state`. Spin results via `/api/spin` POST.

### Season 8 new files

| File | Purpose |
|---|---|
| `bounties.py` | Daily bounty generation, tracking, completion logic |
| `community_goals.py` | Weekly community goal lifecycle (replaces `community_pot` logic in `game.py`) |
| `wagers.py` | Wager resolution helpers (stake validation, hot-streak tracking, double-down) |
| `wheel_modes.py` | Wheel mode definitions, rotation schedule, outcome-distribution tables |
| `prestige.py` | Prestige calculation, legacy badge mapping from Season 1–7 totals |
| `static/js/wager-ui.js` | Wager slider, double-down button, hot-streak meter components |

### Season 8 modified files

| File | Changes |
|---|---|
| `models.py` | Add wager/mode/prestige items to `SHOP_ITEMS`; remove `auto_guard`, `streak_armor_inf`; add `WHEEL_MODES`, `BOUNTY_DEFS`, `COMMUNITY_GOAL_DEFS`; rework `INFINITE_UPGRADES` (remove old infinites, keep prestige only) |
| `game.py` | Rework `_resolve_spin()` for wager + mode; add endpoints for wager/bounty/community-goal/prestige/loadout; remove or cap `/api/tick` auto-spin; rework `/api/community-pot` → `/api/community-goal` |
| `seasons.py` | Extend `_perform_rollover()` for prestige preservation, mode rotation, community goal reset |
| `schema.sql` | Add new tables/columns (reference; actual changes via migrations) |
| `static/app.jsx` | Wager UI, mode selector, bounty panel, prestige button, loadout manager, onboarding flow, number formatting |
| `chat.py` | Auto-post hooks for big wins, bounty completions, community goal milestones |

---

## 2. Season 8 economy reset

### What resets

When Season 7 ends via `_perform_rollover()`, the existing reset logic zeros
`wins`, `losses`, `fish_clicks`, `streak`, `best_streak`, `owned_items`,
`spin_count`, `win_count`, `loss_count`, `total_fish_clicks`, all inf levels,
`proc_streak`, `fish_exchange_total`, `equipped_class`, dice state, fishing
state, and `community_pot`. Cosmetics are preserved via `user_season_history`.

Season 8 adds to this reset:
- `wager_streak` → 0
- `active_wheel_mode` → NULL (defaults to 'steady')
- `bounty_progress` → cleared (new day generates fresh bounties)
- `community_goal_contributions` → 0 (weekly goal resets)
- `double_down_pending` → FALSE
- `gravity_drift` → 0
- `biggest_win_announced` → 0

### What does NOT reset (Season 8 additions to rollover preservation)

- `prestige_level` — permanent across the season; see §5.
- `legacy_wins` — frozen Season 1–7 total, stored at rollover; see §10.
- `owned_cosmetics` — already preserved via `user_season_history`. In Season 8,
  cosmetics are never reset (they persist across weekly 8.x patches within the
  season).
- `aquarium_species` — permanent collection; see §6.
- `loadouts` — saved build configurations persist; see §11.
- `cosmetic_fragments` — earned from bounties, not from the wheel.
- `onboarding_step` — a completed player is not re-onboarded each week.
- `wager_tokens` — earned from fishing/bounties, not from the wheel. Treated
  as a persistent collection currency.

### Legacy badge: starting prestige from Season 1–7 history

At the moment Season 7 rolls over to Season 8, each user's all-time win total
across `user_season_history` is summed. This maps to a starting `prestige_level`:

| All-time wins | Starting prestige |
|---|---|
| 0 (never played) | 0 |
| < 1M | 1 |
| < 100M | 2 |
| < 1B | 3 |
| < 10B | 4 |
| ≥ 10B | 5 |

This means tom7 (21.8B) starts Season 8 at prestige 5 (+10% base win value).
Worm67 (16.9B) also prestige 5. Dylan (3.6B) prestige 4. New players start at 0.
This gives returning players a permanent identity without unbalancing the new
economy — +10% is meaningful, not 21.8 billion.

### Economy scale target

Post-reset, the intended number range:

| Milestone | Wins |
|---|---|
| First spin | ~1–10 |
| After 1 hour active play | ~500–2,000 |
| After 1 week | ~10,000–100,000 |
| Endgame (prestige 10+) | ~100,000–1,000,000 |
| Theoretical max (prestige 20, all upgrades) | ~5,000,000 |

This is enforced by the new `_MAX_WINS` cap and flat (non-compounding) prestige
multipliers. The old `_MAX_WINS = round(9.99e99)` is replaced with a Season 8
cap of `5_000_000` (5M). See §5 for how prestige interacts with this.

---

## 3. Wager system

### Overview

Replaces the flat auto-spin loop. Every spin is a **bet**: the player chooses
a stake percentage (0% to 30% initial, up to 45% with upgrades) of their
current wins (or losses, in inverted mode) before spinning. The spin
button becomes a two-step action: select stake, then spin.

The v2 model (T45) puts existing currency at real risk: a wagered loss now
leaves the player with fewer `wins` than before the spin. Stake is an
up-front debit, not just a magnitude multiplier.

**Design decision (2026-06-23):** Replaced the original "1× to 10×
multiplier" system with a flat-percentage system ("0% to 45% of current
wins"). The multiplier × 0.02 factor was opaque to players; the
percentage is direct and intuitive. The 0% position replaces the "1× =
zero" rule (T100) and the zero-escrow edge case (T70) — the player
chooses the safe position explicitly.

**The simple flow (user design 2026-06-23):** The payout is the **wager
amount**, not a base_payout × percentage. The player can see exactly
what they stand to gain/lose.

| Stake | Escrow | On WIN | On LOSS |
|-------|-------:|-------:|--------:|
| 0%    | 0      | +base_payout wins | +base_loss losses |
| 10%   | 10% of wins | refund 10% + payout 10% (net +10% of bankroll) | -10% of bankroll |
| 30%   | 30% of wins | refund 30% + payout 30% (net +30% of bankroll) | -30% of bankroll |
| 45%   | 45% of wins | refund 45% + payout 45% (net +45% of bankroll) | -45% of bankroll |

**Concrete example (100 wins):**
- Stakes 0%, wins → 102 wins (base_payout only, +2 from base_payout)
- Stakes 10% (10 escrowed), wins → 110 wins (refund 10 + payout 10 = +20)
- Stakes 10% (10 escrowed), loses → 90 wins (escrow forfeited)

**DD (Double-Down) flow:**
- DD stakes `wager_last_win_amount` (the actual last win), not the percentage
- DD ignores the percentage slider; the wager may exceed max_stake_pct
- On WIN: refund wager + payout (matching wager). Net: +wager.
- Can be looped (compound DD) until loss or until player stops
- No loss mitigation fires on DD spins (insurance, safety net, guard, shield, resilience)

**Bonuses:** All bonuses (regular win streak, hot streak, jackpot) are
applied multiplicatively to the **NET** (the wager or base_payout at 0%).
The hot streak bonus portion is banked separately (legacy mechanic, bank button
preserved). Example: 10% stake win at streak 2 → 1000 wager × 1.10 = 1100
total, with 100 (10%) banked as hot streak bonus.

### State (new columns on game_state)

| Column | Type | Default | Purpose |
|---|---|---|---|
| `wager_streak` | INTEGER | 0 | Consecutive wins at the same stake percentage |
| `wager_last_stake` | INTEGER | 0 | Last stake percentage used (0, 5, 10, ..., 45); 0 = no prior spin this session |
| `double_down_pending` | BOOLEAN | FALSE | True after a win, before the player banks or doubles |
| `wager_banked_wins` | INTEGER | 0 | Wins locked in from hot-streak; added to wins on bank |
| `wager_banked_losses` | INTEGER | 0 | Losses locked in from inverted-mode hot-streak |
| `wager_last_win_amount` | INTEGER | 0 | Last payout amount (used for double-down escrow) |
| `wager_insurance_charges` | INTEGER | 0 | Available insurance charges (regen over time) |
| `wager_insurance_last_recharge` | TIMESTAMPTZ | NOW() | Insurance charge regen anchor |
| `gravity_drift` | INTEGER | 0 | Cumulative gravity mode drift (-35 to +35) |
| `biggest_win_announced` | INTEGER | 0 | Per-player escalating big-win threshold |

**Migration note:** existing rows in `game_state` have `wager_last_stake`
in the old 1-10 range. Migration: `stake_pct = (old_stake - 1) * 5`
(e.g., 1× → 0%, 2× → 5%, ..., 10× → 45%).

### Stake mechanics (v2 — flat-percentage at-risk stake)

- **Stake range:** 0% to 30% (initial), with shop upgrades extending the
  max to 35% / 40% / 45%. Discrete 5% steps.
- **`stake_pct`** is the slider position (0, 5, 10, ..., 45). Stored in
  `wager_last_stake` for backward compatibility (renamed semantically).
- **`effective_stake = stake_pct / 100`** — a fraction 0.00 to 0.45, used
  as the payout/loss multiplier. Replaces the old 1-10 integer multiplier.
- **Stake is an up-front debit, not just a multiplier.** Before the spin
  resolves, `stake_wins = floor(current_wins * stake_pct / 100)` is
  deducted from `wins` immediately and held as the at-risk amount for
  this spin. (Implementation in `wagers.py::compute_stake_risk`.)
- Escrow is capped at `current_wins` (cannot go below 0).
- **0% is always safe** — `stake_wins = 0`, payout = `base_payout`, loss
  = `base_loss`. The player can always drop to 0% to spin without risk.
  This replaces the old "zero-escrow edge case" (T70) and "1× = zero"
  rule (T100). No special-case code needed — the formula naturally
  produces 0 when `stake_pct = 0`.
- **Win:** the escrowed `stake_wins` is returned, plus the payout:
  `wins += stake_wins + (base_payout * effective_stake)`.
- **Loss:** the escrowed `stake_wins` is **not returned** — it is gone.
  `losses += (base_loss * effective_stake)`. This is the actual risk: a
  wagered loss now leaves the player with fewer `wins` than they had
  before.
- **Hot streak:** on each consecutive same-stake win, the bonus portion
  of the payout is added to `wager_banked_wins` and only realized on
  Bank. Specifically: `wager_banked_wins += int(stake_wins *
  hot_streak_bonus)`. A loss resets `wager_streak` to 0 and forfeits
  unbanked bonus.
- **Safety net:** on a loss at **≥15% stake**, refunds 25% of the
  escrowed `stake_wins` to `wins`. Threshold changed from 5× (old) to
  15% (new) per user decision 2026-06-23.
- **Bank:** the player presses Bank to lock in `wager_banked_wins` into
  `wins` and reset `wager_streak` to 0. The tension: keep pressing for a
  higher streak bonus, or bank and start fresh. Banked wins are at risk
  on the next spin (forfeited on a loss).
- **Double-down:** see §3.5 — a true all-or-nothing mechanic that
  sidesteps the percentage system and ignores all loss-mitigation
  features.
- **Insurance:** see §3.6 — caps loss at the stake percentage. Does
  NOT apply to double-down spins.

### Why flat percentages (design rationale)

The original 1× to 10× system with `floor(wins * 0.02 * stake)` was
mathematically compact but opaque to players. At 1×, the risk was 2% of
wins; at 5×, 10% of wins; at 10×, 20% of wins. Players had to do mental
arithmetic to understand the actual risk. The flat-percentage system
makes the slider position the literal stake — "I'm putting 10% of my
wins on this spin" requires no translation.

This also makes the 0% position natural: it's the explicit "I don't
want to risk anything" position, instead of relying on edge-case logic
to make 1× safe.

### New shop items (added to SHOP_ITEMS in models.py)

| Item ID | Cost (wins) | Tier | Requires | Effect |
|---|---|---|---|---|
| `wager_unlock` | 500 | 1 | None | Unlocks the wager slider; without this, slider locked at 0% |
| `wager_stake_extend_1` | 5,000 | 2 | `wager_unlock` | Extends max stake from 30% to 35% |
| `wager_stake_extend_2` | 15,000 | 3 | `wager_stake_extend_1` | Extends max stake from 35% to 40% |
| `wager_stake_extend_3` | 40,000 | 4 | `wager_stake_extend_2` | Extends max stake from 40% to 45% |
| `wager_safety_net` | 2,000 | 2 | `wager_unlock` | On a loss at ≥15% stake, recover 25% of escrowed wins |
| `wager_hot_streak` | 8,000 | 2 | `wager_unlock` | Each consecutive same-stake win raises banked bonus +5% (cap +50%) |
| `wager_double_down` | 25,000 | 3 | `wager_hot_streak` | Enables double-down: wager your last win amount for a 2× payout, all-or-nothing |
| `wager_insurance` | 50,000 | 3 | `wager_unlock` | Buys access to insurance system; charges regen over time (max 3) |

**Max stake progression:** 500 → 5,000 → 15,000 → 40,000 = ~60,000 wins
total for 45% max. 3 upgrade tiers, each +5%.

### Integration into _resolve_spin()

The existing `_resolve_spin()` signature gains `stake_pct`,
`wager_streak`, `wager_last_stake`, `wager_banked_wins`,
`wager_last_win_amount`, and `insurance_active` parameters. The function:

1. **Validate stake:** `stake_pct = validate_stake(stake_pct, owns_wager_unlock, owned_stake_extensions)`.
   Returns 0 if player lacks `wager_unlock`; returns `stake_pct` clamped
   to `[0, MAX_STAKE_PCT]` where `MAX_STAKE_PCT = 30 + 5 * (count of
   wager_stake_extend_N items owned)`.
2. **Compute escrow:**
   - If double-down is armed AND `wager_last_win_amount > 0`: `stake_wins
     = wager_last_win_amount`. The percentage slider is **ignored** for
     this spin (DD sidesteps the percentage system).
   - Otherwise: `stake_wins = compute_stake_risk(wins, stake_pct)` =
     `int(wins * stake_pct / 100)`, capped at `current_wins`.
3. **Debit wins:** `wins -= stake_wins`. `effective_stake = stake_pct /
   100` (always, including for DD).
4. **Resolve outcome** (mode-aware, see §4).
5. **Apply protection:** guard/shield/resilience may block the bad
   outcome (see §7 for mode-dependent trigger logic). **These are
   suppressed on DD spins** — see §3.5.
6. **Apply insurance** if armed (see §3.6). **Suppressed on DD spins.**
7. **Win path:** return escrow, apply payout, increment streak,
   accumulate banked wins (`wager_banked_wins += int(stake_wins *
   hot_streak_bonus)`).
8. **Loss path:** forfeit escrow, reset streak to 0, zero banked wins,
   apply safety net (skip if insurance fired or DD is active).
9. **Insurance armed flag** cleared after spin regardless of outcome.

The escrow/return must happen atomically within the spin resolution (same
transaction), not as a separate request, so a crash mid-spin can't leave
wins debited with no resolution recorded.

### Inverted mode

In inverted mode, the stake percentage applies to `current_losses`
instead of `current_wins`. Specifically:
- `stake_losses = int(current_losses * stake_pct / 100)`, capped at
  `current_losses`.
- `losses -= stake_losses` (debit from losses immediately).
- The "lose" outcome (good for inverted) returns the escrow and adds the
  loss-farming payout to `losses`.
- The "win" outcome (bad for inverted) forfeits the escrow and adds
  `base_payout * effective_stake` to `wins` (which the player doesn't
  want).
- The "jackpot" outcome (super-good) refunds the escrow and adds
  `5 * base_loss * effective_stake` to `losses`.

The double-down override works the same way: `wager_last_win_amount`
tracks the last loss-gain amount, and DD escrows that from losses.

**`wager_unlock` is not required for inverted mode** — the stake
slider is fully functional without it (T79).

### Banking

- Banking is available between spins (not mid-spin).
- **Cannot bank while `double_down_pending` is true.** The
  `/api/wager/bank` endpoint returns 409 in that case.
- Banking resets `wager_streak` to 0 but preserves `wager_last_stake`.
- `wager_banked_wins` is at risk on the next spin — forfeited on a loss.
  This is the tension: bank now (safe) or keep spinning (risk losing the
  banked bonus for a chance at a bigger streak).

### Double-down (true all-or-nothing)

Double-down is a **ridiculous snowball mechanic with insanely high risk**.
It is the only wager mechanic that does NOT respect the percentage
slider, and it disables all loss-mitigation features for the spin.

**Mechanic:**
- After a win, the player can arm double-down via
  `/api/wager/double-down`. This sets `double_down_pending = TRUE`.
- On the next spin, the escrow is `wager_last_win_amount` (the exact
  amount won on the previous spin), NOT `int(wins * stake_pct / 100)`.
  The percentage slider position is **completely ignored** for that
  spin.
- The DD spin can stake more than the player's max percentage would
  normally allow (e.g., a player capped at 30% can DD with 45% of
  their wins if their last win was 45% of their bankroll). This is the
  snowball — the risk grows with each successful DD chain.
- **Win:** escrowed amount is returned, plus `base_payout * 2` (the
  double payout). The player effectively doubles their previous
  winnings.
- **Loss:** escrowed amount is forfeited. The player loses the exact
  winnings they had just gained.
- If `wager_last_win_amount == 0` (first spin, or previous spin was a
  loss), double-down has nothing to escrow and is a no-op (the DD
  button is disabled or shows "no prior win to risk").

**No loss mitigation on DD spins.** Per user decision 2026-06-23:
- ❌ **Insurance does NOT fire on DD spins.** (Insurance is a player-vs-
  house protection; DD is player-vs-their-own-greed.)
- ❌ **Safety Net does NOT fire on DD spins.** (Applies regardless of
  stake percentage.)
- ❌ **Guard does NOT fire on DD spins.**
- ❌ **Shield (regen_shield) does NOT fire on DD spins.**
- ❌ **Resilience does NOT fire on DD spins.**
- ✅ **Only the win/lose/jackpot outcome matters** — "true spin of the
  wheel".

This is communicated to the player in:
- The wager panel tooltip (see §3.7)
- The shop item description for `wager_double_down`
- The DD button label (warns "All-or-nothing — no protections")

**In inverted mode:** `wager_last_win_amount` tracks the last loss-gain
amount. Double-down escrows that amount in losses. The same
no-mitigation rules apply.

**Tooltip:** "⚡ Double-Down: Wager your entire last win for a 2×
payout. ⚠️ NO INSURANCE, SAFETY NET, OR PROTECTIONS. True
all-or-nothing. Sidesteps your normal stake %."

### Insurance (dice-charge model)

Completely reworked to mirror the dice re-roll charge system. Insurance is
**bought for access**, charges **regenerate over time**, and arming is a
**gamble** (charge consumed regardless of outcome).

**Shop purchase:** `wager_insurance` (50,000 wins, requires `wager_unlock`)
buys access to the insurance system and sets the max charge cap to 3.

**Charge regeneration:** identical to dice charges:
- New constant: `WAGER_INSURANCE_RECHARGE_SECONDS = 600` (10 min/charge).
- New constant: `WAGER_INSURANCE_MAX_CHARGES = 3`.
- New helper: `_recharge_wager_insurance(charges, last_recharge, max_charges, now_utc)`.
- 1 charge accrues every 10 minutes. Bulk-awards on login. Capped at max.
  Timer pauses while at max.
- Invoke at the same read sites as dice: `/api/state`, spin path, and
  `/api/wager/insurance`.

**Arming:**
- Player arms insurance BEFORE spinning (elective, via
  `/api/wager/insurance`).
- Arming sets `wager_insurance_armed = TRUE` and **consumes a charge
  immediately** (decrements `wager_insurance_charges`, resets
  `wager_insurance_last_recharge` to NOW if charges < max).
- This is a **gamble** — the charge is consumed regardless of spin
  outcome.
- Arming insurance while double-down is armed: insurance does NOT fire
  on a DD loss. The charge is still consumed (or auto-disarmed — design
  choice; current spec: still consumed, but has no effect).

**Spin resolution:**
- If the spin **loses** AND it is NOT a double-down spin: insurance
  fires. Caps `actual_loss` at `int(base_loss * effective_stake)` and
  refunds the escrowed `stake_wins` (returns it to `wins`).
- If the spin **wins**: the charge is wasted (no effect).
- If the spin is a **double-down**: insurance does NOT fire. The charge
  was still consumed when armed; the player got nothing for it.
- `wager_insurance_armed` is cleared after the spin regardless of
  outcome.

**Safety net does NOT stack with insurance.** When insurance fires on a
loss, skip the safety net refund entirely. The insurance already refunded
100% of the escrow; safety net's 25% would stack to 125%.

**In inverted mode:** Insurance caps the "win" outcome (the bad outcome)
and refunds the staked losses. See §4.4. Same no-DD rule applies.

### Wager panel visibility

The wager panel (stake slider, bank button, hot-streak meter, stake
value display, etc.) is **always visible**. The stake slider is:

- **Disabled and greyed out** when `wager_unlock` is not owned. A
  tooltip on the disabled slider says "Buy wager_unlock (500 wins)."
- **Active with max=30%** when `wager_unlock` is owned.
- **Active with max=35/40/45%** as the player buys stake extensions.
- **Stepped at 5%** — the slider snaps to discrete positions
  (0, 5, 10, ..., max). The slider's visual width stays constant; more
  tick positions are added as the max grows.
- **0% is always selectable** — the "safe" position.

This ensures the step-2 onboarding coach-mark has a target element to point
at, even before the player can afford `wager_unlock`.

**Exception — inverted mode:** In inverted mode, the stake slider is fully
functional without `wager_unlock` (see §4.4). `wager_unlock` gates the
wins-wagering system only.

**Stake value display (T105):** the wager panel always shows the current
stake value at the bottom, so the player knows what they're risking
before clicking spin:
- `💰 Stake value: 100 (10% of 1,000 wins)` — normal mode, stake > 0%
- `💀 Stake value: 50 (10% of 500 losses)` — inverted mode, stake > 0%
- `⚡ Stake value: 5,000 (Double-Down)` — DD armed, replaces the % row
- `🛡️ No stake (safe)` — 0% position

The stake value updates synchronously on slider change, on spin
completion, on mode switch, and on DD arm.

### Mode change resets streak and armed state

When the player switches wheel mode (via `/api/wheel-mode`):
- `wager_streak` resets to 0. Prevents gaming the hot-streak system by
  hopping modes.
- `wager_insurance_armed` clears to FALSE. Insurance does not carry across
  mode switches.
- `double_down_pending` clears to FALSE. Double-down does not carry across
  mode switches.
- `gravity_drift` resets to 0 (if switching to or from gravity mode).
- `wager_banked_wins` and `wager_banked_losses` are preserved (they
  survive a mode switch — the banked pool carries over).

**Implementation:** In the `/api/wheel-mode` endpoint, set all of the above
when the mode changes. The response includes the four reset values so
the frontend can sync its React state (T99).

### Auto-spin interaction

See §18. Auto-spin (if retained in capped form) always spins at 0%
stake with no hot-streak tracking and no escrow (`effective_stake = 0`).
It is a convenience for idle moments, never the optimal strategy.

### API changes

- POST /api/spin — existing endpoint. Body now includes `stake_pct`
  (int 0-45 in 5% steps, default 0). If `wager_unlock` not owned, the
  stake is forced to 0. Response includes `stake`, `effective_stake`
  (now a fraction 0.00-0.45), `wager_last_stake` (now 0-45),
  `stake_value` (the live escrow amount), and `max_stake_pct` (the
  player's current max based on upgrades).
- POST /api/wager/bank — new. Banks `wager_banked_wins` into `wins`,
  resets `wager_streak`. Returns 409 if `double_down_pending`.
- POST /api/wager/double-down — new. Sets `double_down_pending = TRUE`.
  Returns error if `wager_last_win_amount == 0` (no prior win to risk).
- POST /api/wager/insurance — new. Arms insurance (consumes a charge).
  Note: if double-down is also armed, the insurance charge is consumed
  but has no effect on the DD spin.

---

## 4. Wheel modes

### Overview

Replace the single static wheel outcome distribution with selectable modes.
Each mode changes the probability profile of win/loss/jackpot. Two modes are
always available; two rotate weekly. Inverted mode is always available as a
loss-farming alternative (see §4.4).

### Mode definitions (added to models.py as WHEEL_MODES)

| Mode | Win% | Loss% | Jackpot% | Notes |
|---|---|---|---|---|
| steady | 70 | 28 | 2 | Default. Small wins, rare losses, standard jackpot. Always available. |
| volatile | 45 | 50 | 5 | High variance. Big wins, frequent losses, double jackpot payout. Always available. |
| inverted | 35 | 60 | 5 | Loss-farming: you want to land on "lose." See §4.4. Weekly rotation. |
| gravity | 55 | 40 | 5 | Outcomes drift toward the last result. Weekly rotation. |
| mirror | 65 | 30 | 5 | Two spins resolve simultaneously; player takes the better result. Weekly rotation. |

### Rotation schedule

Weekly modes are determined by the ISO week number modulo 3:

| ISO week % 3 | Rotating mode |
|---|---|
| 0 | inverted |
| 1 | gravity |
| 2 | mirror |

Steady and volatile are always available. The rotating mode swaps each week at
the weekly reset. Mode selection is per-player — the weekly rotation changes
which modes are *available*, not which is *active*.

### State

| Column | Type | Default | Purpose |
|---|---|---|---|
| `active_wheel_mode` | VARCHAR(16) | steady | Currently selected mode |
| `gravity_drift` | INTEGER | 0 | Gravity mode cumulative drift (-35 to +35) |

### Integration into _resolve_spin()

The outcome determination in `_resolve_spin()` uses a mode-aware probability
roll:

```python
mode = WHEEL_MODES[active_wheel_mode]
roll = random.random()
if roll < mode['jackpot_pct']:
    outcome = 'jackpot'
elif roll < mode['jackpot_pct'] + mode['win_pct']:
    outcome = 'win'
else:
    outcome = 'lose'
```

For each mode, additional mechanics apply:

### 4.1 Gravity mode

**Base profile:** win 55%, lose 40%, jackpot 5%.

**Drift mechanic:**
- After each win or jackpot: `gravity_drift = min(gravity_drift + 10, 35)`
- After each loss: `gravity_drift = max(gravity_drift - 10, -35)`
- Jackpot counts as a win for drift purposes.
- Drift accumulates across consecutive same-direction spins (cumulative).
- **Drift resets to 0 on mode switch** (switching to or from gravity).

**Effective probabilities:**
- `win_pct = 55 + gravity_drift` (range: 20–90%)
- `lose_pct = 40 - gravity_drift` (range: 5–75%)
- `jackpot_pct = 5` (fixed)
- At max win drift (+35): win 90%, lose 5%, jackpot 5%.
- At max loss drift (-35): win 20%, lose 75%, jackpot 5%.

The server must return the drift-adjusted probabilities in `/api/state`
and spin response so the frontend can render the dynamic wheel (see §17).

### 4.2 Mirror mode

**Escrow twice (double risk for double chance).**

- Escrow = `2 * stake_wins` (double the normal escrow, debited before spin).
- Two outcomes are rolled independently.
- The player takes the **better** outcome (by rank: jackpot > win > lose).
- **Better = win or jackpot:** full escrow (2 * stake_wins) is returned.
  Payout = `base_payout * effective_stake` (normal payout, not doubled). The
  second (worse) outcome is ignored — no losses increment, no streak reset.
- **Better = lose (both lost):** full escrow (2 * stake_wins) is forfeited.
  `losses += base_loss * effective_stake` (once, not twice). Streak resets.
- Safety net: on a double-loss at ≥5x stake, refunds 25% of the FULL escrow
  (2 * stake_wins).
- Insurance: on a double-loss, insurance caps the loss and refunds the FULL
  escrow.
- Hot streak: increments on a win (the better outcome).

### 4.3 Inverted mode (loss-farming mechanic)

Completely reworked. Inverted mode is for players who want to accumulate
`losses` (a spendable currency for cosmetics) rather than `wins`. The
risk/reward is inverted: you want to land on "lose." The probability profile
is inverted so the desirable outcome is the majority.

**Probability profile:** lose 60%, win 35%, jackpot 5%.

#### Escrow

Before the spin, the player puts up a **loss escrow** instead of a win escrow:
- `stake_losses = floor(current_losses * stake_pct / 100)` is debited
  from `losses` immediately (same percentage formula as the win system).
- Capped at `current_losses` (cannot go below 0 — both wins and losses are
  positive currencies).
- If `losses == 0` or `stake_pct == 0`: escrow = 0, base loss gain
  only, no stake multiplier (0% is the safe position in any mode).

#### Outcomes

**Lose (the good outcome, 60%):**
- Escrowed `stake_losses` is returned to `losses`.
- `losses += stake_losses + (base_loss * effective_stake * hot_streak_bonus)`
  — bonus losses gained.
- `wager_streak` increments (if same stake, per hot-streak rules).
- `wager_banked_losses` accumulates (the hot-streak bonus portion).
- Shield/guard/resilience do NOT trigger (this is the good outcome).

**Win (the bad outcome, 35%):**
- Escrowed `stake_losses` is NOT returned — forfeited.
- `wins += base_payout * effective_stake` — wins ARE gained (the player
  gains wins, which is undesirable in loss-farming mode, but no outcomes are
  negated).
- `wager_streak` resets to 0.
- `wager_banked_losses` is forfeited (zeroed).
- **Shield/guard/resilience trigger here** — they prevent the "win" (the bad
  outcome). If shield/guard blocks the win: escrow returned, no wins gained,
  streak preserved, `wager_banked_losses` preserved. The player is protected
  from the bad outcome, same as guard protects from a loss in normal mode.

**Jackpot (the ultimate good outcome, 5%):**
- Escrowed `stake_losses` is returned.
- `losses += stake_losses + (base_loss * effective_stake * 5)` — super-charged
  loss gain (5x multiplier).
- `wager_streak` increments.
- `wager_banked_losses` accumulates (with hot-streak bonus).
- Shield/guard/resilience do NOT trigger.

#### Safety net in inverted mode

On the bad outcome (win) at ≥5x stake, the safety net refunds 25% of the
staked losses to `losses`. Same logic as normal mode, but the "bad" outcome
is "win" instead of "lose."

#### Insurance in inverted mode

Insurance caps the bad outcome (win) and refunds the escrowed losses.
- Arm before spin (elective, charge consumed on arm — same gamble as normal
  mode).
- If the spin "wins" (bad outcome): insurance caps the win payout, refunds
  the escrowed `stake_losses`.
- If the spin "loses" (good outcome): charge wasted.
- Safety net skipped when insurance fires (same as normal mode).

#### Double-down in inverted mode

`wager_last_win_amount` tracks the last **payout** amount regardless of
currency. In inverted mode, the "payout" is the loss gain on a "lose" outcome.

- After a "lose" (good outcome), `wager_last_win_amount` is set to the loss
  gain amount (the `base_loss * effective_stake` portion, not including
  escrow return).
- Arming double-down escrows that amount in **losses** (not wins).
- If the next spin "loses" (good): escrow returned + `base_loss *
  effective_stake` (same structure as normal mode — the "doubling" comes
  from the escrow being the previous payout, so total gain ≈ 2x previous
  loss gain).
- If the next spin "wins" (bad): escrowed losses forfeited.

#### Hot streak and banking in inverted mode

- Landing on "lose" (good outcome) increments `wager_streak`.
- Hot-streak bonus (+5% per level, cap +50%) applies to the loss gain.
- `wager_banked_losses` accumulates the hot-streak bonus portion.
- Bank button banks `wager_banked_losses` into `losses` (same tension as
  wins banking: bank or keep spinning).
- Cannot bank while `double_down_pending` is true (same guard).
- `wager_banked_losses` is forfeited on a "win" (bad outcome).
- `wager_streak` resets on mode change.

#### wager_unlock not required

Inverted mode does NOT require `wager_unlock`. The stake slider is fully
functional in inverted mode regardless of `wager_unlock` ownership. The
stake operates on losses, not wins; `wager_unlock` gates the wins-wagering
system only.

**Frontend implication:** When `active_wheel_mode === 'inverted'`, the
stake slider is enabled even without `wager_unlock`. When in any other mode,
the slider is disabled without `wager_unlock` (per §3.7).

#### Losses as a currency

`losses` is a spendable currency, handled exactly the same as `wins`:
- Shop items that cost losses deduct from the `losses` counter.
- The counter can go down (from spending) as well as up (from losing in
  normal mode or gaining in inverted mode).
- The tension between spending losses on cosmetics vs. keeping them for
  inverted-mode escrow is intended.
- `losses` resets to 0 on prestige (same as `wins`).

#### Wins counter in inverted mode

The `wins` counter goes up on "win" outcomes in inverted mode. No outcomes
are negated. A player farming losses in inverted mode will also incidentally
gain wins (35% of the time), which affects the leaderboard and prestige.
This is intentional.

### 4.4 _resolve_spin() mode check

The `_resolve_spin()` function needs a mode check at the top of the outcome
handling:

```python
if active_wheel_mode == 'inverted':
    # Escrow losses instead of wins
    stake_losses = compute_stake_risk(losses, actual_stake) if owns_wager_unlock else 0
    losses -= stake_losses
    # Invert outcome desirability:
    # - "lose" is good → win path logic (escrow return + payout)
    # - "win" is bad → loss path logic (escrow forfeit + guard/shield)
    # - "jackpot" is super-good → jackpot path logic (5x loss gain)
else:
    # Normal escrow logic (wins)
    stake_wins = compute_stake_risk(wins, actual_stake) if owns_wager_unlock else 0
    wins -= stake_wins
```

The guard/shield/resilience trigger logic needs inversion:
- Normal mode: trigger on "lose" outcome.
- Inverted mode: trigger on "win" outcome.

The safety net and insurance logic needs mode-awareness:
- Normal mode: refund on "lose" at ≥5x.
- Inverted mode: refund on "win" at ≥5x.

### API changes

- POST /api/wheel-mode — new. Body: `{mode: string}`. Validates mode is in
  the currently-available set. Sets `active_wheel_mode`. On mode change:
  resets `wager_streak`, `wager_insurance_armed`, `double_down_pending`, and
  `gravity_drift`.
- GET /api/wheel-modes — new. Returns available modes for the current week
  plus the player's active mode and current `wheel_probabilities`.

### Community pot interaction

The community pot (if active) overrides the base win% with `pot_win_pct`. In
Season 8, this becomes the community goal buff (see §9). Mode probabilities
apply only when no community buff is active.

---

## 5. Prestige system

### Overview

Replaces the Season 7 infinite upgrade axes (winmult_inf, bonusmult_inf,
jackpot_resonance_inf, echo_amp_inf, proc_streak_inf, streak_armor_inf). Those
had no effective ceiling and were all maxed by the top 3 players. Prestige
provides a flat, non-compounding bonus with a hard cap.

### Mechanics

- **Prestige action:** resets wins to 0, resets non-cosmetic upgrades, but
  grants +1 prestige_level (up to max 20).
- **Bonus:** each prestige level gives +2% base win value, applied as a flat
  multiplier to effective_win_mult. Prestige 20 = +40%.
- **Cap:** prestige_level hard-capped at 20. No further progression beyond.
- **Cosmetics and collections preserved:** owned cosmetics, aquarium species,
  loadouts, legacy_wins, wager_tokens, cosmetic_fragments, and onboarding_step
  are NOT reset by prestige. See §5.3 for the full list.
- **Starting prestige:** at Season 8 rollover, each player gets a starting
  prestige_level based on their Season 1-7 all-time wins (see §2).

### New columns

| Column | Type | Default | Purpose |
|---|---|---|---|
| `prestige_level` | INTEGER | 0 | Current prestige level (0-20) |
| `prestige_count` | INTEGER | 0 | Total times prestiged (for display) |
| `legacy_wins` | NUMERIC | 0 | Frozen all-time wins from Seasons 1-7 (set at rollover, never changes) |

### New shop items

| Item ID | Cost (wins) | Tier | Requires | Effect |
|---|---|---|---|---|
| `prestige_unlock` | 1,000,000 | 3 | None | Enables the prestige action button |
| `prestige_efficiency` | 500,000/level | 3 | `prestige_unlock` | Keeps 10% of wins per level on prestige (max 5 = keep 50%) |
| `prestige_legacy` | 1,000,000/level | 3 | `prestige_unlock` | Keep 1 owned functional upgrade per level on prestige (max 3) |

### Prestige action implementation

New endpoint: `POST /api/prestige`

Logic:
1. Verify `prestige_unlock` is owned and `wins >= 1,000,000`.
2. Apply `prestige_efficiency`: keep `floor(wins * 0.1 * level)` wins.
   At level 0 (not owned): `new_wins = 0`. At level 5: `new_wins = floor(wins * 0.5)`.
3. Apply `prestige_legacy`: let the player keep N functional upgrades
   (N = `prestige_legacy` level, max 3). The player selects which to keep
   via the request body.
4. Reset: see §5.3 for the full reset list.
5. Increment `prestige_level` (if < 20) and `prestige_count`.
6. Preserve: see §5.3 for the full preserve list.

**`prestige_efficiency` retains wins only, not losses.** The cost threshold
(1,000,000 wins) is NOT reduced by efficiency — the threshold is always
1,000,000 wins.

### 5.3 Prestige reset scope

**Resets to 0/default:**
- `wins`, `losses` (both are currencies that reset)
- `streak`, `best_streak`
- `owned_items` (minus kept items via `prestige_legacy` + cosmetics)
- All inf levels
- Wager state: `wager_streak`, `wager_last_stake`, `double_down_pending`,
  `wager_banked_wins`, `wager_banked_losses`, `wager_insurance_charges`,
  `wager_insurance_last_recharge`, `wager_last_win_amount`
- `guard_charges`, `guard_last_regen_spin`, `resilience_last_use_spin`
- Dice state: `dice_charges`, `dice_last_recharge`,
  `dice_rolled_since_spin`, `pending_dice`
- Fishing state: `fish_clicks`, cast/reel state, `fish_exchange_total`
- `spin_count`, `win_count`, `loss_count`, `proc_streak`
- `equipped_class`, `active_wheel_mode`
- `gravity_drift`, `biggest_win_announced`
- Bounty progress (daily — resets at midnight anyway, but prestige clears
  it too)

**Preserved:**
- `prestige_level`, `prestige_count`, `legacy_wins`
- `owned_cosmetics`, `active_cosmetics`
- `aquarium_species`
- `loadouts`
- `cosmetic_fragments`
- `onboarding_step`
- `wager_tokens` (earned from fishing/bounties, not the wheel)
- Community goal contributions (separate table — not affected by prestige)
- Singularity contributions (separate table — not affected by prestige)

### Removal of old infinite upgrades

The following are REMOVED from `INFINITE_UPGRADES` and their columns frozen
(not dropped, but no longer purchasable or effective):

- `winmult_inf` (replaced by prestige + flat winmult_1 through winmult_7)
- `bonusmult_inf` (replaced by flat bonusmult_1 through bonusmult_6)
- `jackpot_resonance_inf` (jackpot becomes wheel-mode-based)
- `echo_amp_inf` (win_echo becomes a flat 25% proc, no upgrade)
- `proc_streak_inf` (removed entirely)
- `streak_armor_inf` (removed, see §7)
- `lure_mastery_inf` (replaced by aquarium luck bonus, see §6)

The existing columns remain in the DB for historical queries but default to 0
and are not read by `_resolve_spin()` in Season 8.

### _MAX_WINS rework

The old `_MAX_WINS = round(9.99e99)` is replaced with `_MAX_WINS = 5_000_000`.
This enforces the economy ceiling. Combined with prestige (max +40%), the
theoretical maximum win count is 5,000,000. A player at the cap must prestige
to continue progressing (which resets wins but raises their permanent bonus).

---

## 6. Fishing integration

### Overview

Season 6 fishing is disconnected from the core loop — dylan never touched it.
Season 8 bridges fishing to the wheel via wager tokens and the aquarium. Fishing
becomes a build choice, not an isolated grind.

### Fish-to-wager conversion

Caught fish convert to wager tokens at a rate determined by the fish rarity.
Wager tokens are spent on high-stake spins (above 5x) as an alternative to
spending wins.

| Fish tier | Wager tokens per catch |
|---|---|
| Common (tropical, puffer) | 5 |
| Uncommon (octopus, shark, dolphin) | 15 |
| Rare (squid, turtle, crab) | 40 |
| Epic (lobster, whale, seal) | 100 |
| Legendary (mermaid, croc, rocket) | 250 |
| Cosmic (comet, saturn, alien, ufo) | 500 |

### New columns

| Column | Type | Default | Purpose |
|---|---|---|---|
| `wager_tokens` | INTEGER | 0 | Fish-converted tokens for high-stake spins |
| `aquarium_species` | TEXT[] | {} | Unique species caught (permanent collection) |

### New shop items

| Item ID | Cost (wins) | Tier | Requires | Effect |
|---|---|---|---|---|
| `fish_to_wager` | 5,000 | 1 | None | Unlocks fish-to-wager conversion at the rates above |
| `lure_specialization` | 10,000/each | 2 | `fish_to_wager` | Choose a fish family; +50% value for that family, -25% for others |
| `catch_of_the_day` | 3,000 | 1 | None | First catch each day is worth 5× wager tokens |
| `aquarium` | 15,000 | 2 | None | Display caught fish; each unique species gives +0.1% wheel luck |

### Aquarium luck bonus

Replaces `lure_mastery_inf`. Each unique species in `aquarium_species` adds
+0.1% to the player base win%. With 20 unique species (the full `FISH_SKINS`
catalog minus default), the maximum bonus is +2.0% win%. This is a gentle
collection-to-power link that rewards worm67 (the collector) without being
mandatory.

### API changes

- POST /api/fish-to-wager — new. Converts caught fish (pending in the
  existing catch queue) to wager_tokens at the rate table.
- GET /api/aquarium — new. Returns species list, luck bonus, and display data.
- The existing /api/cast, /api/bite-poll, /api/reel, /api/auto-fish-tick
  endpoints are unchanged. The reel endpoint now also awards wager_tokens
  (in addition to fish_clicks) when `fish_to_wager` is owned.

### Lure mastery removal

`lure_mastery_inf` is removed from `INFINITE_UPGRADES`. Its column
(`lure_mastery_level`) is frozen at 0 for Season 8. The aquarium luck bonus
replaces its function (fish value multiplier) with a wheel-luck multiplier,
shifting fishing from a fish-value boost to a wheel-luck boost.

---

## 7. Protection rework

### Overview

The old protection stack (guard, auto_guard, regen_shield, resilience,
streak_armor_inf) let players negate loss entirely. In a wager system, that
breaks the risk loop. Protection becomes scarce and active.

### Removed items

| Item | Reason |
|---|---|
| `auto_guard` | Passive immunity breaks wager risk. Removed from `SHOP_ITEMS`. |
| `streak_armor_inf` | Infinite stacking. Removed from `INFINITE_UPGRADES`. |

### Reworked items

| Item ID | Cost (wins) | Tier | Effect |
|---|---|---|---|
| `guard` | 1,000 | 1 | Blocks one loss per session (manual trigger). Consumed on use. |
| `guard_charge` | 10,000/level | 2 | +1 guard charge, max 3 total. Scarce, not infinite. |
| `regen_shield` | 5,000 | 2 | Regenerates 1 guard charge every 50 spins (slow, not infinite). |
| `resilience` | 20,000 | 3 | Convert a loss into a 50% refund once per 20 spins. Fallback, not immunity. |

### New columns

| Column | Type | Default | Purpose |
|---|---|---|---|
| `guard_charges` | INTEGER | 0 | Available guard charges (0-3) |
| `guard_last_regen_spin` | BIGINT | 0 | Spin count at last guard regen |
| `resilience_last_use_spin` | BIGINT | 0 | Spin count at last resilience use |

### Implementation

The auto-guard purchase-and-block logic in `_resolve_spin()` (lines 184-192 of
game.py) is removed entirely. Guard becomes a manual trigger via a new
endpoint:

- POST /api/guard — new. Consumes one `guard_charge` to block the next loss.
  Sets a flag; the next lose outcome in `_resolve_spin()` is converted to a
  no-contest (streak unchanged, no loss).

`regen_shield` now regenerates guard charges (not shield charges). Every 50
spins (tracked via `spin_count`), if `regen_shield` owned and
`guard_charges < max`, `guard_charges += 1`.

`resilience` triggers automatically on a loss if 20+ spins since last use.
Converts the loss to a 50% refund (`losses += floor(base_loss * 0.5)`
instead of full).

### Inverted mode protection logic

Guard, shield, and resilience trigger on the **bad outcome** in each mode:
- **Normal mode:** trigger on "lose" outcome.
- **Inverted mode:** trigger on "win" outcome (the bad outcome — you want
  to lose, so the protections prevent winning).

---

## 8. Daily bounties

### Overview

Three rotating objectives per day, drawn from a pool. Gives a reason to log
in daily that requires specific actions (not idle spinning). Completing all
three awards a bonus cosmetic fragment or one-day buff.

### Bounty definitions (added to models.py as BOUNTY_DEFS)

| ID | Description | Tracking metric | Target |
|---|---|---|---|
| `bounty_wager5` | Win 5 spins at 5x+ stake | wager_wins_5x | 5 |
| `bounty_fish10` | Catch 10 fish | fish_caught_today | 10 |
| `bounty_jackpot` | Land a jackpot in any mode | jackpots_today | 1 |
| `bounty_prestige` | Prestige once | prestige_today | 1 |
| `bounty_mirror` | Win 3 mirror-mode doubles | mirror_wins_today | 3 |
| `bounty_streak10` | Reach a 10-spin win streak | max_streak_today | 10 |
| `bounty_bank` | Bank winnings 3 times | banks_today | 3 |
| `bounty_double` | Win 2 double-downs | double_downs_won_today | 2 |

### New table

```sql
CREATE TABLE IF NOT EXISTS bounty_progress (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bounty_date DATE NOT NULL,
    bounty_id   VARCHAR(32) NOT NULL,
    progress    INTEGER NOT NULL DEFAULT 0,
    completed   BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, bounty_date, bounty_id)
);
```

### Generation logic (bounties.py)

Each UTC midnight, 3 bounties are selected for each user from `BOUNTY_DEFS`.
Selection is deterministic per `(user_id, date)` using a seed =
`hash(user_id, date)`. This ensures the same 3 bounties are shown all day
regardless of which worker handles the request. Bounties reset at UTC
midnight — incomplete progress is discarded.

### Rewards

| Completion | Reward |
|---|---|
| 1 bounty | 100 wager tokens |
| 2 bounties | 250 wager tokens |
| 3 bounties (all) | 500 wager tokens + 1 cosmetic fragment |

Cosmetic fragments accumulate; 10 fragments = 1 random cosmetic from a
Season 8 exclusive set. Fragments are tracked in a new column:

| Column | Type | Default | Purpose |
|---|---|---|---|
| `cosmetic_fragments` | INTEGER | 0 | Bounty reward currency for exclusive cosmetics |

### API changes

- GET /api/bounties — new. Returns today's 3 bounties with progress.
- POST /api/bounties/claim — new. Claims rewards for completed bounties.
  Auto-claims on completion is optional; this endpoint is for manual claim.

**Chat integration:** Bounty completions are shown in the bounty panel only,
NOT broadcast to chat (see §12).

---

## 9. Community goals (replaces Community Pot)

### Overview

The Community Pot is permanently maxed at 75% — dead content. Replace with
a rotating weekly shared goal. All players contribute; on completion, all
participants receive a reward. Contribution is capped per player so one
whale cannot solo it.

### New table (replaces community_pot)

```sql
CREATE TABLE IF NOT EXISTS community_goals (
    id              SERIAL PRIMARY KEY,
    goal_id          VARCHAR(32) NOT NULL,
    season_number    INTEGER NOT NULL,
    week_number      INTEGER NOT NULL,
    target           INTEGER NOT NULL,
    current          INTEGER NOT NULL DEFAULT 0,
    completed        BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at     TIMESTAMPTZ,
    started_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    milestone_25     BOOLEAN NOT NULL DEFAULT FALSE,
    milestone_50     BOOLEAN NOT NULL DEFAULT FALSE,
    milestone_75     BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(season_number, week_number)
);

CREATE TABLE IF NOT EXISTS community_goal_contributions (
    goal_id          VARCHAR(32) NOT NULL,
    user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contributed      INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (goal_id, user_id)
);
```

### Goal definitions (COMMUNITY_GOAL_DEFS in models.py)

| Goal ID | Description | Target | Per-player cap | Metric tracked |
|---|---|---|---|---|
| `goal_fish5000` | Catch 5,000 fish server-wide | 5000 | 500 | fish_caught |
| `goal_jackpot500` | Land 500 jackpots server-wide | 500 | 50 | jackpots_landed |
| `goal_prestige50` | Prestige 50 times server-wide | 50 | 10 | prestiges |
| `goal_wager100k` | Wager 100k wins total server-wide | 100000 | 15000 | wins_wagered |
| `goal_species100` | Catch 100 unique species server-wide | 100 | 15 | unique_species |

### Weekly rotation

One goal is active per week. The goal is selected by `week_number` modulo
`len(COMMUNITY_GOAL_DEFS)`. The goal resets weekly at the same time as the
wheel-mode rotation (see §4).

### Milestone tracking

After each `increment_goal` call, check if `current` crossed a 25/50/75%
threshold. If so, set the corresponding `milestone_*` column to TRUE and post
a system message (see §12):

- `event_kind='goal_milestone_25'` — "Community goal at 25%: X / target"
- `event_kind='goal_milestone_50'` — "Community goal at 50%: X / target"
- `event_kind='goal_milestone_75'` — "Community goal at 75%: X / target"

100% is the completion event itself — no separate milestone; the completion
reward distribution already fires. Milestones reset weekly with the goal
(new row = fresh columns).

### Rewards

On completion, all players who contributed at least 1 unit receive:
- A week-long +5% win% buff (replaces the old community pot buff)
- 500 wager tokens
- 1 cosmetic fragment

### Integration

Contribution tracking hooks into existing events in `_resolve_spin()` and
fishing endpoints. A win at 5x+ stake contributes to `goal_wager100k`. A
jackpot contributes to `goal_jackpot500`. A fish catch contributes to
`goal_fish5000`. The `community_goals.py` module exposes `increment_goal()`
called from these endpoints after the primary action succeeds.

### API changes

- GET /api/community-goal — new. Returns active goal, progress, player
  contribution, milestone status, and reward info. Replaces /api/community-pot.
- The old /api/community-pot/contribute endpoint is removed.

---

## 10. Leaderboard reset & legacy boards

### Overview

Season 8 wipes the active leaderboard (the billions are gone). But Seasons
1-7 are preserved as legacy boards — a Hall of Fame. f22 and griffin keep
their #1 spots. tom7 21.8B is memorialized.

### Active leaderboard

The existing /api/leaderboard endpoint is unchanged in structure but the
data resets at rollover (wins = 0 for everyone). The leaderboard now shows
Season 8 wins only, which are in the hundreds-to-millions range (legible).

### Legacy boards

New endpoint: `GET /api/legacy-boards`

Returns an array of seasons with their top-5 snapshots from the existing
`season_snapshots` table. No new table needed — `season_snapshots` already
stores position, username, wins, losses per season. The endpoint just
queries all seasons and groups them.

Additionally, each player's `legacy_wins` (set at rollover, see §5) is
displayed on their profile as a permanent badge: "Seasons 1-7: X wins".

### Frontend

The leaderboard panel gains a tab toggle: [Season 8] [Hall of Fame]. The
Hall of Fame tab shows a dropdown of seasons 1-7, each with its top-5.

---

## 11. Build loadouts

### Overview

Let players save and name up to 3 loadouts — combinations of equipped class,
active wheel mode, and preferred wager stake. Quick-swap between them.
Lower the cost of adapting to weekly mode rotation.

### New table

```sql
CREATE TABLE IF NOT EXISTS build_loadouts (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slot       INTEGER NOT NULL CHECK (slot >= 1 AND slot <= 3),
    name       VARCHAR(32) NOT NULL DEFAULT 'Loadout 1',
    config     JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, slot)
);
```

### Config schema (JSONB)

```json
{
  "equipped_class": "star" | "moon" | "earth" | null,
  "active_wheel_mode": "steady" | "volatile" | "inverted" | "gravity" | "mirror",
  "preferred_stake": 1-10,
  "note": "optional player note"
}
```

### API changes

- GET /api/loadouts — new. Returns all 3 loadout slots.
- POST /api/loadouts/save — new. Body: `{slot: 1-3, name: string, config: obj}`.
  Saves/overwrites a loadout slot.
- POST /api/loadouts/equip — new. Body: `{slot: 1-3}`. Applies the loadout:
  sets `equipped_class`, `active_wheel_mode`, and stores `preferred_stake` as
  a UI default (does not force-apply stake on next spin).

---

## 12. Chat revival & auto-post messages

### Overview

50 messages is a dead channel. Revive it by seeding game events so the
channel is never empty. Players see activity without having to type. The
replay system (originally planned for §12 of the v1 spec) is **removed** —
auto-post system messages replace it.

### message_type vocabulary

| Value | Meaning |
|---|---|
| `user` | Normal player chat message |
| `system` | System message (event announcements) |
| `event` | Game event message (jackpot, big win, etc.) |

The migration 040 default `'chat'` is treated the same as `'user'` by the
frontend:

```js
// app.jsx — system detection:
isSystem = m.message_type && !['user', 'chat'].includes(m.message_type)
```

This ensures old `'chat'` rows from previous seasons render as normal user
chat, matching how chat looked in Seasons 1-7.

### Chat history: 200 messages with scroll lazy-loading

Retained chat history is extended from 50 to 200 messages. The frontend
loads older messages as the user scrolls up.

**Backend:**
- `chat.py` — change initial SELECT `LIMIT 30` to `LIMIT 50`.
- Trim `LIMIT 50` → `LIMIT 200` in both `post_chat` and `post_system_message`.
- Add cursor pagination to `GET /api/chat`:
  - `?before=<id>&limit=50` — returns 50 messages with `id < <id>`, ordered
    `id DESC`, then reversed (oldest first). The `id` column is `BIGSERIAL`
    with an existing `idx_chat_messages_id_desc` index — cursor pagination
    is ready, no schema change needed.

**Frontend (`app.jsx:2096-2276`):**
- Initial load: fetch latest 50 messages.
- On scroll near top (`scrollTop < threshold`): fetch
  `/api/chat?before=<oldestLoadedId>&limit=50`. Prepend to message list.
- State: `loadingOlder`, `hasMore`, `oldestLoadedId`.
- Preserve scroll position when prepending (capture `scrollHeight` before,
  restore offset after).
- Poll (5s interval) continues to fetch latest 50. Merge with loaded older
  messages by id (dedup). The poll replaces only the "head" (messages newer
  than the oldest loaded id); older loaded chunks are preserved in state.
- "Loading older…" affordance above the message list while fetching.

### Auto-post system messages

Auto-post formatted system messages when exciting events happen. No player
click needed — the server posts automatically. Replaces the v1 replay
system.

**Configurable trigger constants** (code-level, in a new `chat_triggers.py`
or top of `game.py`):

```python
JACKPOT_MSG_ALWAYS = True               # any jackpot, any stake, any mode
DOUBLE_DOWN_MSG_MIN_EFFECTIVE_STAKE = 5  # effective stake >= 5
HOT_STREAK_MSG_THRESHOLD = 10           # hot streak reaches max
BIG_WIN_THRESHOLD = 5000                # initial threshold for big-win msgs
```

**Triggers:**

| Event | Trigger condition | Message format | `event_kind` |
|---|---|---|---|
| Jackpot | Any jackpot (any stake, any mode, including auto-spin) | `🎰 {user} hit a JACKPOT in {mode} mode at {stake}x stake for {wins_delta} wins!` | `jackpot` |
| Double-down win | Effective stake ≥ 5 | `🔥 {user} won a {effective_stake}x double-down for {wins_delta} wins!` | `double_down_win` |
| Hot streak 10 | `wager_streak` reaches 10 | `🔥 {user} reached a 10-win hot streak!` | `hot_streak_10` |
| Big win | `wins_delta >= BIG_WIN_THRESHOLD` AND `wins_delta > biggest_win_announced` | `💰 {user} won {wins_delta} wins in {mode} mode!` | `big_win` |
| Prestige | Always | `⭐ {user} reached Prestige Level {N}!` | `prestige` |
| New player | First spin (`spin_count` was 0 before this spin) | `🎉 {user} spun the wheel for the first time! Welcome to Season 8!` | `new_player` |
| Singularity fill | Meter fills | `🌀 The Singularity has converged! Total contributed: {N}` | `singularity_fill` |
| Community goal milestone | 25/50/75% threshold crossed | `Community goal at {pct}%: {current} / {target}` | `goal_milestone_{pct}` |

**Per-player escalating big-win threshold:**

Big-win messages only fire when the player exceeds their own previous
biggest announced win. This prevents spamming "tom7 won 5,001!" "tom7 won
5,002!"

- New column: `biggest_win_announced INTEGER NOT NULL DEFAULT 0` on
  `game_state`.
- On a win: if `wins_delta >= BIG_WIN_THRESHOLD` AND
  `wins_delta > biggest_win_announced`: post the message, then UPDATE
  `biggest_win_announced = wins_delta`.
- Reset to 0 on prestige (the player is in a new economy).

**Auto-spin messages:** Auto-spin jackpots and big wins DO generate
messages. Add message-posting logic to the `/api/tick` path.

**Throttling:** The existing 30-second per-`event_kind` throttle applies
(`chat.py:185-211`). Each event kind has its own throttle window. Milestone
messages have per-percent event kinds.

### Implementation

`chat.py` provides `post_system_message(conn, message, message_type='system', event_kind=None)`.
Game endpoints call this after the primary action succeeds. System messages
have `user_id = NULL, username = 'SYSTEM'`.

The `message_type` column is `VARCHAR(16) NOT NULL DEFAULT 'chat'`. The
`user_id` FK is dropped (migration 043) to allow NULL for system messages.

### API changes

- GET /api/chat — modified. Supports `?before=<id>&limit=50` for pagination.
  Returns latest 50 messages by default.

### Events NOT broadcast to chat

- **Bounty completion** — shown in the bounty panel only, not in chat.
  (Prevents chat spam from individual bounty claims.)
- **Replay cards** — the v1 replay system is removed entirely. See §4 of
  the removed-features list.

---

## 13. Singularity rework

### Overview

The Singularity (1e67 fish_clicks) was never purchased by anyone. tom7 has
3.9B fish_clicks — the gap is 58 orders of magnitude. Rework as a
server-wide community unlock that is actually reachable.

### New mechanic

The Singularity becomes a repeating server-wide community goal, not a
personal purchase. It uses the community_goals framework (§9) but with a
special meta-goal that spans multiple weeks.

### Phase 1: Accumulation (weeks 1-4)

All players contribute fish_clicks to a shared Singularity meter. Target:
100,000,000 fish_clicks total (reachable, not 1e67). Per-player cap:
25,000,000. Contribution is voluntary via a new endpoint.

### Phase 2: Unlock event (week 5)

When the meter fills, a server-wide event triggers:
- All players get a one-time cosmetic: "Singularity Convergence" background
- A new wheel mode unlocks for the remainder of the season: "singularity"
  (75% win, 10% loss, 15% jackpot — the ultimate mode)
- A narrative beat plays in chat (system message — `event_kind='singularity_fill'`)

### Phase 3: Reset

After the event, the Singularity meter resets and a new community goal
takes its place. The singularity wheel mode remains unlocked for the rest
of Season 8 but the meter can fill again for a second event (different
cosmetic reward).

### New table

```sql
CREATE TABLE IF NOT EXISTS singularity_meter (
    id                  INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    total_contributed   BIGINT NOT NULL DEFAULT 0,
    target              BIGINT NOT NULL DEFAULT 100000000,
    filled              BOOLEAN NOT NULL DEFAULT FALSE,
    filled_at           TIMESTAMPTZ,
    fill_count          INTEGER NOT NULL DEFAULT 0
);
```

### API changes

- GET /api/singularity — new. Returns meter progress, target, fill_count.
- POST /api/singularity/contribute — new. Body: `{amount: int}`. Contributes
  fish_clicks to the meter. Enforces per-player cap.

### Removal

The singularity item is removed from `SHOP_ITEMS` (no longer purchasable).
The existing owned singularity check in `_resolve_spin()` (line 196: if
"singularity" in owned: outcome = win) is removed.

---

## 14. Number formatting

### Overview

The single most important UX fix. 21,843,192,441 wins is not readable. The
game must format numbers to human scale everywhere.

### Format rules

| Range | Format | Example |
|---|---|---|
| < 1,000 | raw | 842 |
| 1,000 - 999,999 | comma-grouped | 84,201 |
| 1,000,000 - 999,999,999 | compact | 8.42M |
| >= 1,000,000,000 | compact | 8.42B | (legacy/Hall-of-Fame only after reset) |

### Implementation

A shared `format_wins(n)` function is added. It must be used:
- In every API response that includes wins/losses (backend, for the raw
  number)
- In the frontend as a display filter (`app.jsx`) for all number rendering

Backend returns raw integers; the frontend applies `format_wins()` for
display. This keeps API responses machine-readable while ensuring the UI
is always legible. The function lives in a new `static/js/format.js` shared
module, imported by `app.jsx`.

### Legacy display

`legacy_wins` (Seasons 1-7 totals) may be in the billions. These are always
displayed with the compact format and a "(legacy)" label, never raw.

---

## 15. Onboarding flow

### Overview

New players (the 2 who registered and never spun) saw a wall. Add a 4-step
onboarding flow that teaches the core loop and rewards each step. Existing
players also see onboarding (they start at `onboarding_step = 0` and earn
the free cosmetics on their next relevant actions).

### Steps

| Step | Trigger | Teaches | Reward |
|---|---|---|---|
| 1. First spin | `spin_count = 0` before spin | The wheel: click to spin, win/lose | `trail_1` cosmetic (auto-equipped) |
| 2. First wager | `wager_unlock` owned, first `stake > 1` | Risk/reward: higher stake = bigger wins/losses | `confetti_1` cosmetic (auto-equipped) |
| 3. First fish | First cast + reel | Fishing loop: cast, wait for bite, reel | `fish_tropical` skin (auto-equipped) |
| 4. First bounty | Bounty panel opened (`GET /api/bounties` called) | Daily objectives | 100 wager tokens |

### Step 2 and the wager_unlock gate

Step 2's trigger requires `wager_unlock` owned. The wager panel (including
the stake slider) is **always visible but disabled** until `wager_unlock` is
purchased. The disabled slider shows a tooltip "Buy wager_unlock (500 wins)."
The step-2 coach-mark points at the disabled slider, giving the player a
target to work toward.

**Exception:** In inverted mode (§4.4), the stake slider is fully functional
without `wager_unlock`. The step-2 coach-mark still points at the slider, but
the player can interact with it directly in inverted mode (staking losses).

### Terminal step

`onboarding_step` caps at 5 (= all done). When `/api/bounties` advances
`onboarding_step` from 3 to 4, it also advances to 5 in the same UPDATE.
Step 4 is "first bounty panel open" — the player opened it, they're done.
The reward (100 wager tokens) is granted at the 3→5 transition.

### Implementation

| Column | Type | Default | Purpose |
|---|---|---|---|
| `onboarding_step` | INTEGER | 0 | 0 = not started, 1-4 = step completed, 5 = all done |

The frontend checks `onboarding_step` on `/api/state` load. If < 5, it shows
a coach-mark overlay (non-blocking card with arrow pointing at the next
target element). Each step auto-advances when the trigger condition is met
(detected in the relevant endpoint response). The reward is granted
automatically.

**Rollover:** `onboarding_step` is **preserved** across weekly rollovers. A
player who completes onboarding in 8.1 never sees it again. The
`_perform_rollover()` in `seasons.py` does NOT reset `onboarding_step`.

### API changes

- GET /api/state — response includes `onboarding_step`.
- POST /api/spin — response includes `onboarding_advance: true` when step
  1→2 is triggered.
- POST /api/wager/stake — response includes `onboarding_advance: true` when
  step 1→2 is triggered (frontend consumes this to advance the coach-mark
  immediately).
- POST /api/reel — response includes `onboarding_advance: true` when step
  2→3 is triggered.
- GET /api/bounties — response includes `onboarding_advance: true` when
  step 3→5 is triggered (3→4→5 in one update; the reward is granted at 3→5).

### Frontend

The coach-mark is a non-blocking card (not a full-screen modal). It points
at the target element with an arrow and dismisses on action. The frontend
`onboarding_advance` handler advances the coach-mark immediately on receiving
the field in any response (not waiting for the next state poll).

---

## 16. Themes

### Overview

Rotate cosmetic wheel themes with each weekly patch to signal "this week is
different". Each theme is a new entry in the existing theme/background shop
category, auto-granted to all players for the patch week.

### Theme schedule

| Patch | Theme ID | Visual |
|---|---|---|
| 8.1 | theme_tidal | Water-color blues, fish swim across wheel on big wins |
| 8.2 | theme_ember | Warm oranges, sparks fly on volatile-mode wins |
| 8.3 | theme_frost | Ice-crystal shards, cracking animation on losses |
| 8.4 | theme_aurora | Shifting greens/purples, northern-lights trail on pointer |
| 8.5 | theme_vintage | Deliberate retro look — "the old wheel" tom7 misses |

### Implementation

Themes follow the existing `theme_` pattern in `SHOP_ITEMS`. Each is a
cosmetic background auto-granted via migration (like 022_season7_theme.sql)
and equipped by default for the patch week. Players can switch to any owned
theme at any time. The visual effects (fish swimming, sparks, etc.) are CSS
animations in `styles.css` keyed off the equipped theme class.

### Vintage theme callback

`theme_vintage` (8.5) is a direct callback to tom7's May 10 chat message:
"i miss the old wheel." Ship as a retro-styled theme that visually references
Season 1-2 aesthetics.

---

## 17. Dynamic wheel graphic

### Overview

The wheel graphic dynamically adjusts based on the current probability
profile. The arc spans of the WIN/LOSE/JACKPOT segments change in real-time
to reflect drift-modified probabilities, mode changes, and inverted mode
visuals.

### Current implementation

- Wheel is canvas-based, drawn by `drawWheel()` (`app.jsx:901-1013`).
- Arc spans are driven by a hardcoded client-side table `WHEEL_MODE_DRAW`
  (`app.jsx:892-899`).
- Redrawn on mode/theme change via React effect (`app.jsx:3228-3231`).
- Spin animation is CSS rotation of the static canvas.
- `drawWheel()` already accepts arbitrary spans via `modeConfig`
  (`app.jsx:924-927`) — minimal change needed.

### Required changes

**Server-side:**
- `/api/state` and spin response must include the current effective
  probability profile: `{win_pct, lose_pct, jackpot_pct}`. This is the
  base profile adjusted by gravity drift (if active).
- New field in state response: `wheel_probabilities: {win_pct, lose_pct, jackpot_pct}`.

**Frontend:**
- Replace `WHEEL_MODE_DRAW` hardcoded table with state from server.
- Store `wheelProbabilities` in state (`app.jsx`).
- Add to the redraw effect dependency array (`app.jsx:3228-3231`):
  `useEffect(() => { drawWheel(canvas, theme, mode, probabilities); },
  [wheelTheme, activeWheelMode, wheelProbabilities])`.
- `drawWheel()` uses `wheelProbabilities` if provided, falls back to
  `WHEEL_MODE_DRAW` for backward compat.
- The wheel redraws whenever probabilities change (e.g., gravity drift
  shifts after each spin).

**For inverted mode:** The wheel labels should swap — "LOSE" becomes the
large/green segment (good), "WIN" becomes the smaller/red segment (bad).
The arc spans reflect the inverted profile (60% lose, 35% win, 5% jackpot).

---

## 18. Auto-spin policy

### Overview

Season 7 server-side auto-spin (every 3s via /api/tick) killed active
engagement. **T107 (2026-06-23):** auto-spin is now a **shop upgrade** —
players must buy `auto_spin_unlock` (5,000 wins, Tier 1, no requirements)
to use it. This rewards active players while keeping the convenience
available to anyone willing to invest.

### Decision: capped, opt-in auto-spin

Auto-spin is **gated behind `auto_spin_unlock`** (5,000 wins, T107). Once
owned, the player can start a 100-spin activation via
`POST /api/auto-spin/start { budget: 100 }`. Auto-spin uses 0% stake
(no risk), no hot-streak tracking, and never arms DD or insurance.
After 100 spins, it stops and the player must re-activate.

The wager panel hides the stake slider while auto-spin is active (the
slider would be confusing since auto-spin always uses 0% stake). DD
and insurance buttons remain visible but are no-ops during auto-spin
(the server already prevents them from arming).

### Implementation

- **Shop item** `auto_spin_unlock` added to `SHOP_ITEMS` (5,000 wins, no
  `requires`). Tier 1 (no cumulative_wins threshold).
- **`POST /api/auto-spin/start`** now returns 403 if the caller doesn't
  own `auto_spin_unlock`. Sets `auto_spin_budget = 100`.
- **`POST /api/auto-spin/stop`** clears `auto_spin_budget` and
  `auto_spin_since`.
- **`/api/tick`** decrements `auto_spin_budget` per spin. When it
  reaches 0, auto-spin stops. Unchanged from before.
- **UI**: the wager panel renders a `🔁 Start Auto-Spin (100)` button
  only if the player owns `auto_spin_unlock`. When active, it shows
  `⏹ Stop Auto-Spin (N left)`. The stake slider is hidden while active.
- **Polling**: a `useEffect` on `autoSpinActive` calls `setInterval(tick,
  3000)` to poll `/api/tick` while auto-spin is running.

### Auto-spin vs the wager system

When auto-spin is on:
- Stake slider is **hidden** (no manual input)
- DD button is visible but a no-op
- Insurance button is visible but a no-op
- Server uses `stake_wins = 0` (no risk) regardless of slider position

When auto-spin is off:
- Stake slider is visible
- DD and insurance work normally

This makes the two systems mutually exclusive — auto-spin is for idle
moments, the wager system is for active play.

### Auto-spin messages

Auto-spin jackpots and big wins DO generate auto-post chat messages (see
§12). The message-posting logic is added to the `/api/tick` path.

### Rate

Auto-spin interval remains 3s (`AUTO_SPIN_INTERVAL_SECONDS = 3.0`). 100 spins
= 5 minutes of idle spinning. This is a convenience for a bio break, not a
multi-hour idle strategy.

---

## 18a. Cumulative wins (T106) — tier-gating metric

**T106 (2026-06-23):** the tier-2/3 unlock thresholds changed from
`win_count` (count of winning spins) to `cumulative_wins` (lifetime
value of wins gained). The old metric was designed for the auto-spin era
where every player spun 100+ times per session. With wager-driven manual
play, the count is too slow — a player winning 1-2 wins per spin needed
~5,000 spins to unlock Tier 3. The new metric is the cumulative value
of wins gained over the season.

### Definition

`cumulative_wins` is a `BIGINT` column on `game_state`:
- **Incremented by** `wins_delta` on every winning spin (manual + auto)
- **Never decremented** — purchases, wager losses, prestige all leave it
  alone
- **Resets on season rollover** (consistent with `wins`)

### Thresholds

| Tier | Old (win_count) | New (cumulative_wins) |
|------|----------------:|---------------------:|
| 2    | 1,000           | 10,000               |
| 3    | 5,000           | 100,000              |

The 10× scale reflects the higher wins/spin under the wager system (a
single win at 30% stake can be 30% of bankroll, vs 1-3 wins on a
non-wagered spin). The 10× ratio between tier 2 and tier 3 is preserved.

### Migration

`049_cumulative_wins.sql` adds the column and backfills with the current
`wins` balance. Going forward, every UPDATE in the manual spin path and
the auto-spin tick path increments the field.

---

## 19. Database migrations

### Migration numbering

Next migration number is 031. Season 8 migrations are grouped by feature
for parallel development. All migrations are idempotent (IF NOT EXISTS).

### Migration list

| Migration | Feature | Tables/Columns affected |
|---|---|---|
| 031_season8_reset.sql | Economy reset + rollover extension | game_state: add `prestige_level`, `prestige_count`, `legacy_wins`, `onboarding_step`, `auto_spin_budget`; ALTER _MAX_WINS logic is code-side |
| 032_wager_system.sql | Wager system | game_state: add `wager_streak`, `wager_last_stake`, `double_down_pending`, `wager_banked_wins`, `wager_insurance_charges` |
| 033_wheel_modes.sql | Wheel modes | game_state: add `active_wheel_mode` |
| 034_fishing_integration.sql | Fishing integration | game_state: add `wager_tokens`, `aquarium_species` |
| 035_protection_rework.sql | Protection rework | game_state: add `guard_charges`, `guard_last_regen_spin`, `resilience_last_use_spin` |
| 036_bounties.sql | Daily bounties | CREATE TABLE `bounty_progress`; game_state: add `cosmetic_fragments` |
| 037_community_goals.sql | Community goals | CREATE TABLE `community_goals` (with `milestone_25/50/75` columns), `community_goal_contributions` |
| 038_loadouts.sql | Build loadouts | CREATE TABLE `build_loadouts` |
| 039_singularity_rework.sql | Singularity rework | CREATE TABLE `singularity_meter` |
| 040_chat_types.sql | Chat revival | chat_messages: add `message_type` |
| 041_season8_themes.sql | Theme grants | Auto-grant `theme_tidal` to all users |
| 043_chat_system_messages.sql | System messages | chat_messages: drop `NOT NULL` on `user_id`; drop `user_id` FK |
| 046_wager_insurance_armed.sql | Insurance armed flag | game_state: add `wager_insurance_armed` |
| 047_hardening.sql | Hardened spec columns | game_state: add `wager_last_win_amount`, `wager_banked_losses`, `wager_insurance_last_recharge`, `gravity_drift`, `biggest_win_announced` |

### Migration 047 (hardening)

```sql
-- game_state columns
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS wager_last_win_amount INTEGER NOT NULL DEFAULT 0;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS wager_banked_losses INTEGER NOT NULL DEFAULT 0;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS wager_insurance_last_recharge TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS gravity_drift INTEGER NOT NULL DEFAULT 0;
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS biggest_win_announced INTEGER NOT NULL DEFAULT 0;

-- community_goals columns (added to migration 037 retroactively, or here)
-- ALTER TABLE community_goals ADD COLUMN IF NOT EXISTS milestone_25 BOOLEAN NOT NULL DEFAULT FALSE;
-- ALTER TABLE community_goals ADD COLUMN IF NOT EXISTS milestone_50 BOOLEAN NOT NULL DEFAULT FALSE;
-- ALTER TABLE community_goals ADD COLUMN IF NOT EXISTS milestone_75 BOOLEAN NOT NULL DEFAULT FALSE;
```

### New constants (in models.py or wagers.py)

```python
WAGER_INSURANCE_RECHARGE_SECONDS = 600  # 10 min, same as DICE_RECHARGE_SECONDS
WAGER_INSURANCE_MAX_CHARGES = 3
BIG_WIN_THRESHOLD = 5000
MAX_CHAT_MESSAGES = 200  # retained chat history limit
```

### Rollover extension

`_perform_rollover()` in `seasons.py` must be extended to:
- Set `legacy_wins = SUM(final_wins from user_season_history for this user)`
  at the moment of rollover
- Set `prestige_level` = starting prestige from legacy mapping (§2)
- Reset wager state, wheel mode, bounty progress, community goal contribs
- **Preserve:** `prestige_level`, `prestige_count`, `legacy_wins`,
  `aquarium_species`, `loadouts`, `cosmetic_fragments`, `onboarding_step`,
  `wager_tokens`
- Reset `community_goals` table (new week, new goal)
- Reset `singularity_meter` only if filled (`fill_count` increments)

---

## 20. API surface changes

### Summary of all new endpoints

| Method | Path | Feature | Auth | Rate limit |
|---|---|---|---|---|
| POST | /api/spin | Modified (adds stake param) | yes | 10/s |
| POST | /api/wager/bank | Wager bank | yes | 5/s |
| POST | /api/wager/double-down | Wager double-down | yes | 5/s |
| POST | /api/wager/insurance | Wager insurance (arms) | yes | 5/s |
| GET | /api/wheel-modes | List available modes + probabilities | yes | 60/min |
| POST | /api/wheel-mode | Set active mode | yes | 20/min |
| POST | /api/prestige | Prestige action | yes | 5/min |
| POST | /api/fish-to-wager | Convert fish to tokens | yes | 5/s |
| GET | /api/aquarium | Aquarium data | yes | 60/min |
| POST | /api/guard | Manual guard trigger | yes | 5/s |
| GET | /api/bounties | Daily bounties | yes | 60/min |
| POST | /api/bounties/claim | Claim bounty rewards | yes | 5/min |
| GET | /api/community-goal | Community goal status | yes | 30/min |
| GET | /api/legacy-boards | Legacy Hall of Fame | no | 30/min |
| GET | /api/loadouts | List loadouts | yes | 60/min |
| POST | /api/loadouts/save | Save loadout | yes | 10/min |
| POST | /api/loadouts/equip | Equip loadout | yes | 10/min |
| GET | /api/singularity | Singularity meter | yes | 60/min |
| POST | /api/singularity/contribute | Contribute fish_clicks | yes | 5/s |
| POST | /api/auto-spin/start | Start capped auto-spin | yes | 5/min |
| POST | /api/auto-spin/stop | Stop auto-spin | yes | 30/min |
| GET | /api/chat | Modified (cursor pagination, 200 retained) | yes | 30/min |

### Removed endpoints

| Method | Path | Reason |
|---|---|---|
| POST | /api/community-pot/contribute | Replaced by community goals (auto-tracked) |
| GET | /api/community-pot | Replaced by /api/community-goal |
| POST | /api/replay/share | Replay system removed (replaced by auto-post messages) |

### Modified endpoints

| Method | Path | Change |
|---|---|---|
| POST | /api/spin | Body adds `stake` (int 1-10, default 1). Response adds `onboarding_advance` (bool). |
| POST | /api/tick | Capped at `auto_spin_budget`; stops at 0. Auto-post messages added. |
| GET | /api/state | Response adds: `prestige_level`, `prestige_count`, `legacy_wins`, `active_wheel_mode`, `wager_streak`, `wager_banked_wins`, `wager_banked_losses`, `wager_last_win_amount`, `wager_insurance_charges`, `wager_insurance_armed`, `wager_tokens`, `aquarium_species`, `cosmetic_fragments`, `onboarding_step`, `auto_spin_budget`, `guard_charges`, `gravity_drift`, `biggest_win_announced`, `wheel_probabilities`, bounty summaries, community goal summary. |
| GET | /api/leaderboard | No structural change; data resets at rollover. |
| GET | /api/chat | Supports `?before=<id>&limit=50` for scroll lazy-loading. Retains 200 messages. |
| GET | /api/bounties | Response includes `onboarding_advance` when step 3→5. |
| POST | /api/wager/stake | Response includes `onboarding_advance` when step 1→2. |
| POST | /api/reel | Response includes `onboarding_advance` when step 2→3. |
| POST | /api/wheel-mode | Resets `wager_streak`, `wager_insurance_armed`, `double_down_pending`, `gravity_drift` on mode change. |

---

## 21. Frontend changes

### Overview

All frontend work is in `static/app.jsx` (compiled to `app.js` via Babel). New
shared modules in `static/js/`. The changes are organized by UI panel.

### Wager UI (static/js/wager-ui.js + app.jsx)

- Stake slider (1x-10x) with risk labels: Safe (1-3), Bold (4-7), Reckless (8-10).
  **Always visible but disabled** when `wager_unlock` is not owned (tooltip:
  "Buy wager_unlock (500 wins)"). **Fully functional in inverted mode**
  without `wager_unlock`.
- Double-down button (appears after a win, if `wager_double_down` owned).
  Tooltip: "Double-Down: risk your last winnings for a chance to double them."
- Hot-streak meter (fills with consecutive same-stake wins, shows +5% per level).
- Bank button (locks in `wager_banked_wins`, resets streak). Disabled while
  `double_down_pending` is true.
- Insurance button (if `wager_insurance` owned, shows charges available and
  armed state).

### Wheel mode selector (app.jsx)

- Dropdown showing available modes for the current week.
- Active mode highlighted; unavailable modes greyed out.
- Mode description tooltip on hover.

### Bounty panel (app.jsx)

- Three bounty cards with progress bars.
- Claim button (enabled when all 3 complete).
- Cosmetic fragment counter.

### Prestige panel (app.jsx)

- Prestige level display with progress to next level.
- Prestige button (requires 1M wins + `prestige_unlock`).
- Warning modal: "This will reset your wins and non-cosmetic upgrades. Continue?"
- Legacy wins badge: "Seasons 1-7: X wins"

### Community goal widget (app.jsx)

- Progress bar: current / target.
- Player contribution: "You: X / cap Y".
- Reward preview on hover.

### Leaderboard with Hall of Fame tab (app.jsx)

- Tab toggle: [Season 8] [Hall of Fame].
- Hall of Fame: season dropdown (1-7), top-5 display.

### Onboarding coach-mark (app.jsx)

- Non-blocking card (not full-screen modal) shown when `onboarding_step < 5`.
- Step 1: arrow pointing to spin button, "Click to spin!"
- Step 2: arrow pointing to stake slider, "Try a higher stake!" (works even
  when slider is disabled — coach-mark guides the player to buy the unlock)
- Step 3: arrow pointing to fishing panel, "Cast a line!"
- Step 4: arrow pointing to bounty panel, "Check your bounties!"
- Each step auto-dismisses when trigger met. Advances immediately on
  receiving `onboarding_advance` in any response (not on next state poll).

### Number formatting (static/js/format.js)

- `format_wins(n)` function used in all number displays.
- Applied to: win count, loss count, leaderboard, shop costs, wager amounts,
  community goal progress, singularity meter.

### Aquarium panel (app.jsx)

- Grid of caught species (colored) and uncaught (silhouettes).
- Luck bonus readout: "+X.X% wheel luck"
- Fish-to-wager conversion button (if `fish_to_wager` owned).

### Loadout manager (app.jsx)

- 3 loadout slots with name, config summary.
- Save current setup to slot.
- Equip loadout (one click).

### Chat enhancements (app.jsx)

- System messages render with italic, muted styling.
- Auto-scroll to new messages.
- Scroll lazy-loading for older messages (200-message history).
- "Loading older…" affordance.

---

## 22. Rollout sequence

### Constraint

All work happens on staging (`/home/user/wheel-app-staging/`, `wheeldb_staging`,
port 5001). Season 7 ends gracefully via the existing `_perform_rollover()`
mechanism when the operator says so. Do NOT schedule its end date or modify
`ends_at`. The operator will provide direct guidance on timing.

### Phase 0: Pre-launch foundation (before 8.1)

These must be done first; everything else depends on them.

| Step | What | Files |
|---|---|---|
| 0a | Migration 031: add prestige/legacy/onboarding/auto_spin_budget columns | migrations/031_season8_reset.sql |
| 0b | Extend `_perform_rollover()` to set legacy_wins, starting prestige, reset new columns | seasons.py |
| 0c | Number formatting module | static/js/format.js |
| 0d | Update _MAX_WINS to 5_000_000 in models.py | models.py |
| 0e | Remove old infinite upgrades from INFINITE_UPGRADES; freeze columns at 0 | models.py, game.py |
| 0f | Migration 040: chat message_type column (needed early for system messages) | migrations/040_chat_types.sql |
| 0g | Migration 043: drop NOT NULL on chat_messages.user_id (for system messages) | migrations/043_chat_system_messages.sql |

### Phase 1: 8.1 Launch (core loop)

| Step | What | Files | Depends on |
|---|---|---|---|
| 1a | Migration 032: wager columns | migrations/032_wager_system.sql | Phase 0 |
| 1b | Wager logic in `_resolve_spin()` | game.py, wagers.py | 0a, 1a |
| 1c | Wager shop items in models.py | models.py | 1a |
| 1d | Wager API endpoints (/api/wager/bank, double-down, insurance) | game.py | 1b |
| 1e | Wager UI components | static/js/wager-ui.js, app.jsx | 1d |
| 1f | Migration 033: wheel mode column | migrations/033_wheel_modes.sql | Phase 0 |
| 1g | Wheel mode definitions + rotation logic | wheel_modes.py, models.py | 1f |
| 1h | Wheel mode integration in `_resolve_spin()` | game.py | 1b, 1g |
| 1i | Wheel mode API + UI | game.py, app.jsx | 1h |
| 1j | Prestige system logic + API | prestige.py, game.py | 0a, 0b |
| 1k | Prestige UI | app.jsx | 1j |
| 1l | Number formatting applied everywhere | app.jsx | 0c |
| 1m | Onboarding flow | app.jsx, game.py | 0a |
| 1n | Migration 041: grant theme_tidal | migrations/041_season8_themes.sql | Phase 0 |
| 1o | Migration 036: bounty table + columns | migrations/036_bounties.sql | Phase 0 |
| 1p | Bounty logic + API | bounties.py, game.py | 1o |
| 1q | Bounty UI | app.jsx | 1p |
| 1r | Migration 047: hardening columns (wager_last_win_amount, gravity_drift, etc.) | migrations/047_hardening.sql | Phase 0 |
| 1s | Hardened wager system (zero-escrow, hot streak reset, banking guard, double-down rework, insurance rework, panel visibility) | game.py, wagers.py, app.jsx | 1r |
| 1t | Hardened onboarding (visible-disabled panel, step 5, advance flags, rollover preservation) | game.py, app.jsx, seasons.py | 1m |
| 1u | Auto-post messages (jackpot, double-down, hot streak, big win, prestige, new player) | game.py, chat.py | 1h, 0f |

### Phase 2: 8.2 / 8.3 (weeks 2-3)

| Step | What | Depends on |
|---|---|---|
| 2a | Migration 035: protection rework columns | Phase 0 |
| 2b | Protection rework logic (remove auto_guard, rework guard/regen/resilience) | 2a, 1b |
| 2c | Guard API + UI | 2b |
| 2d | Ember + Frost theme migrations + CSS | Phase 0 |
| 2e | Migration 046: wager_insurance_armed | 1s |

### Phase 3: 8.4 (week 4)

| Step | What | Depends on |
|---|---|---|
| 3a | Migration 034: fishing integration columns | Phase 0 |
| 3b | Fish-to-wager conversion logic | 3a, 1b |
| 3c | Aquarium logic + API | 3a |
| 3d | Fishing panel UI updates | 3b, 3c |
| 3e | Aurora theme migration + CSS | Phase 0 |

### Phase 4: 8.5 (week 5)

| Step | What | Depends on |
|---|---|---|
| 4a | Migration 037: community goals tables (with milestone columns) | Phase 0 |
| 4b | Community goal logic + tracking hooks + milestone messages | 4a, 1u |
| 4c | Community goal API + UI | 4b |
| 4d | Migration 039: singularity meter table | Phase 0 |
| 4e | Singularity rework logic + API | 4d, 4b |
| 4f | Migration 038: loadouts table | Phase 0 |
| 4g | Loadout logic + API + UI | 4f |
| 4h | Mirror mode (double escrow) | 1h |
| 4i | Gravity mode (drift column, dynamic wheel) | 1h, 1r |
| 4j | Inverted mode (full loss-farming mechanic) | 1h, 1r |
| 4k | Dynamic wheel graphic (server-provided probabilities) | 1h, 1i, 4i |
| 4l | Chat history extension (200 messages, scroll lazy-loading) | 1u, 0f |
| 4m | Vintage theme migration + CSS | Phase 0 |

### Phase 5: 8.6+ (week 6 onward)

| Step | What | Depends on |
|---|---|---|
| 5a | Legacy boards API + UI | Phase 0 |
| 5b | Accessibility pass (reduced motion, high-contrast, keyboard spin) | All |
| 5c | Ongoing weekly rotation: bounties, community goals, wheel modes | 1p, 4b, 1h |

### Testing

All work is on staging. Test by:
1. Running migrations: `python migrate.py`
2. Starting staging server: `gunicorn -c gunicorn.conf.py server:app` (port 5001)
3. Manual smoke test of each new endpoint
4. Frontend rebuild: `npx babel static/app.jsx --out-file static/app.js`

### Production deployment

Production deployment is operator-controlled, NOT part of this spec. When the
operator is ready:
1. Merge staging changes to production (`/home/user/wheel-app/`).
2. Run migrations on wheeldb.
3. Restart production server.
4. The operator triggers Season 7 end (which runs `_perform_rollover`).
5. Season 8 begins.

---

## 23. Implementation bug fixes

These bugs were identified during the audit and must be fixed. They are
listed in priority order.

### 23.1 Quick fixes (no spec dependency)

| # | Bug | Location | Fix |
|---|---|---|---|
| B3 | `should_generate_replay` hardcodes `double_down=False` | `game.py:864` | **DELETE** — replay system removed |
| B4 | `generate_replay` omits `double_down=` kwarg | `game.py:865-868` | **DELETE** — replay system removed |
| B9 | `message_type` vocabulary mismatch | `app.jsx:2222` | One-line fix: `!['user', 'chat'].includes(m.message_type)` |
| B10 | Rollover resets `onboarding_step` | `seasons.py:139` | Remove `onboarding_step = 0` from rollover |
| B12 | Step 3 onboarding advance not in `/api/reel` response | `game.py:2099-2114` | Add `onboarding_advance` field |
| B14 | `fish_tropical` not auto-equipped | `game.py:2091-2092` | Add to `active_cosmetics` + set `equipped_fish` |
| B18 | No rate limits on wager endpoints | `game.py:2571, 2629, 2650` | Add `@limiter.limit('5/s')` decorators |
| B21 | "All 3 bounties" message in chat | `game.py:2812` | **DELETE** the `post_system_message` call |

### 23.2 Spec-amendment-dependent fixes

| # | Bug | Location | Fix | Depends on |
|---|---|---|---|---|
| B1 | `wager_streak` not reset on loss | `game.py:319-354` | Add `wager_streak = 0` in loss path | §3 |
| B2 | Insurance + safety net double-refund | `game.py:344-353` | Skip safety net when insurance fires | §3.6 |
| B5 | Auto-spin path never generates messages | `game.py:1161-1213` | Add message-posting logic | §12 |
| B6 | `/api/replay/share` doesn't post to chat | `game.py:3023-3037` | **DELETE** the endpoint | §12 |
| B7 | No frontend "Share" button | `app.jsx` | N/A — replay system removed | §12 |
| B8 | Replay card renders plain text | `app.jsx:2223-2233` | **DELETE** the replay branch | §12 |
| B11 | Step 2 onboarding advance not in `/api/wager/stake` | `game.py:2626` | Add `onboarding_advance` field | §15 |
| B13 | `onboarding_step` never reaches 5 | `game.py` | 3→5 transition in `/api/bounties` | §15 |
| B15 | Insurance charge consumed on win | `game.py:2668-2671` | **Rework** — charge consumed on arm (gamble, per §3.6) | §3.6 |
| B16 | `wager_insurance_armed` not in `/api/state` | `game.py:652-656` | Add to state response | §3.6 |
| B17 | No "armed" indicator for insurance | `app.jsx:4224-4226` | Add armed indicator UI | §3.6 |
| B19 | Double-down tooltip misleading | `app.jsx:3722` | Update tooltip text | §3.5 |
| B20 | Community goal milestones not posted | `community_goals.py` | Add milestone columns + `post_system_message` calls | §9 |

---

## 24. Work breakdown

Implementation tasks organized by phase. Bug fixes (B#) and work items (W#)
from §23 are referenced.

### Phase 1: Quick fixes & removals (low risk, high value)

1. **B3, B4, B6, B7, B8** — Remove replay system entirely (delete files,
   endpoints, frontend code)
2. **B9** — Fix `message_type` vocabulary (one-line frontend fix)
3. **B10** — Fix `onboarding_step` rollover preservation (one-line fix)
4. **B21** — Remove bounty message from chat
5. **B18** — Add rate limits to wager endpoints
6. **B14** — Fix `fish_tropical` auto-equip
7. **B13** — Fix onboarding step 5 transition
8. **B11, B12** — Add `onboarding_advance` to wager/stake and reel responses

### Phase 2: Wager system hardening

9. **B1** — Fix `wager_streak` reset on loss
10. Zero-escrow base-payout-only (§3.1)
11. Banking guard — cannot bank while `double_down_pending` (§3.4)
12. Double-down rework — new column, escrow last win amount (§3.5)
13. **B19** — Update double-down tooltip
14. Insurance rework — dice-charge model, new column, regen (§3.6)
15. **B2** — Fix insurance + safety net stacking
16. **B16** — Add `insurance_armed` to `/api/state`
17. **B17** — Add insurance armed indicator in frontend
18. Wager panel always visible but disabled (§3.7)
19. Mode-change resets streak and armed state (§3.8)

### Phase 3: Chat & auto-post

20. Auto-post messages with configurable triggers (§12)
21. Per-player escalating big-win threshold (§12)
22. **B5** — Add auto-post to auto-spin path
23. Chat history extension to 200 with scroll lazy-loading (§12)
24. **B20** — Community goal milestone messages (§9)

### Phase 4: Wheel modes

25. Gravity mode with drift column (§4.1)
26. Mirror mode double-escrow (§4.2)
27. Inverted mode — full loss-farming mechanic (§4.3)
28. Dynamic wheel graphic (§17)
29. Dynamic wheel for inverted mode (label swap)

### Phase 5: Prestige

30. `prestige_efficiency` as win retention (§5)
31. Prestige reset scope update (wager tokens persist) (§5.3)

### Phase 6: Onboarding flow

32. Onboarding coach-mark improvements (already partially implemented)

### Migration

33. Migration 047 — add all new columns from §19

---

*End of build specification. All spec gaps have been resolved. This document
is fully implementable as written. All decisions are recorded in
`SEASON_8_SPEC_GAPS_ANSWERS.md` and `SEASON_8_SPEC_GAPS_ANSWERS2.md`.
All paths reference `/home/user/wheel-app-staging/`. Source:
`SEASON_8_PLANNING.md`, live `wheeldb_staging` schema, `game.py`, `models.py`,
`seasons.py` as of 2026-06-17; spec hardened 2026-06-22.*
