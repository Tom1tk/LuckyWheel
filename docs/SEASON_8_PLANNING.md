# Lucky Wheel — Season 8 Planning Document

> Prepared from live database analytics (wheeldb, 8 registered users),
> `PATCH_NOTES.md` (Seasons 1–7), `schema.sql`, `models.py`, and chat history.
> No code changes — planning only.

---

## TL;DR

The game is not dying because of bugs. It is dying because **it was solved**.
Three players reached the ceiling, found one optimal build, and ran it 1.1
million times each on auto-spin. The wheel spins itself now. There is nothing
left to buy, no reason to choose differently, and no reason to come back.

Season 8 must be **drastically different** in three concrete ways:

1. **Kill auto-spin as the default loop.** Make the spin a *decision* again.
2. **Collapse the economy.** Numbers in the billions are meaningless; reset to
   a scale where a "big win" is comprehensible.
3. **Add weekly variety, not weekly grind.** The 8.1 / 8.2 model should change
   *what* the optimal play is each week, not just add more numbers to chase.

Players told you they will return **only if it is drastically different**.
This document treats that as the success criterion.

---

## Table of Contents

1. [Where the game is now](#1-where-the-game-is-now-season-7-state)
2. [Player analysis](#2-player-analysis)
3. [Season history & economy inflation](#3-season-history--economy-inflation)
4. [Core problems diagnosed](#4-core-problems-diagnosed)
5. [Season 8 design pillars](#5-season-8-design-pillars)
6. [New upgrade ideas](#6-new-upgrade-ideas)
7. [New feature ideas](#7-new-feature-ideas)
8. [Themes & UX improvements](#8-themes--ux-improvements)
9. [The weekly reset model (8.1, 8.2, …)](#9-the-weekly-reset-model-81-82-)
10. [Phased roadmap](#10-phased-roadmap)
11. [Risks & open questions](#11-risks--open-questions)

---

## 1. Where the game is now (Season 7 state)

Season 7 ("Endless") introduced server-side auto-spin every 3 seconds, four
infinite upgrade axes (`jackpot_resonance`, `echo_amp`, `proc_streak`,
`streak_armor`), and a three-class system (Earth / Moon / Star).

The database already shows a `season_number = 8` row (started 2026-05-09,
end date placeholdered at 2099-01-01) **with no content and no patch notes**.
Season 8 has technically "started" on the server but ships nothing.

**Hard numbers from the live DB:**

| Metric | Value |
|---|---|
| Registered users | 8 |
| Users who ever spun | 6 |
| Truly engaged players (≥1.1M spins) | 3 (tom7, worm67, dylan) |
| Former #1 players who quit | 2 (f22, griffin) |
| Users who never played | 2 |
| Top win count | 21.8B (tom7) |
| Spin counts of the 3 active players | 1.11M / 1.14M / 1.11M |
| Total chat messages, all-time | ~50 |
| Singularity (ultimate goal) purchases | 0 |

The three active players are within ~3% of each other on spin count — a
signature of auto-spin. Nobody is *playing* differently; everyone is running
the same idle loop and letting the server spin for them.

---

## 2. Player analysis

### The three survivors

| Player | Wins | Win% | Class | Items | winmult | bonusmult | Infinite upgrades | Fishing |
|---|---|---|---|---|---|---|---|---|
| **tom7** | 21.8B | 58.8% | Star | 26 | 81 | 93 | all maxed (JR 10/10, EA 10/10, PS 15/15, SA 10/10, lure_mastery 40) | deep — 3.9B fish_clicks |
| **worm67** | 16.9B | 57.8% | Star | 77 | 79 | 88 | partial | mid (lure_mastery 4) |
| **dylan** | 3.6B | 57.0% | Moon | 27 | 87 | 89 | partial | **zero** (never touched fishing) |

**tom7** is the completionist-power player: fewest items (26 — only bought
what works) but every infinite upgrade maxed and the deepest fishing engagement
of anyone (3.9B fish_clicks, lure_mastery 40). Pure optimization, zero
collection. The Singularity (cost: 1e67 fish_clicks) is unreachable even for
him — it was never purchased by anyone.

**worm67** is the collector: 77 items (nearly everything in the shop), but
lower lure_mastery (4) and partially-maxed infinites. Plays for breadth, not
depth. Win count still 16.9B — the economy is so inflated that even a
sub-optimal build produces billions.

**dylan** ignored fishing entirely (zero lure_mastery, zero fish_exchange)
and still hit 3.6B wins and Moon class. This proves fishing is **optional** to
the core loop — a whole subsystem that a dedicated player never engaged with.

### The churned winners

- **f22**: Season 1 & 2 #1. 34K spins, 8.7K wins. Quit before Season 3.
- **griffin**: Season 3 #1. 11.6K spins, 539K wins. Quit after Season 3.

Both left during the era of uncapped exponential scoring (Seasons 1–4 hit
**googol-scale numbers** — 400+ digit win counts). The game became
unintelligible: a win of $10^{10^{20}}$ is not a number a human can feel. They
won, saw the ceiling, and left. **f22's 8.7K wins would be invisible on today's
leaderboard** — tom7 has 21.8 billion.

### The casual tier

- **chudwigvanbetahoven**: 4.8M wins, 110K spins, 7 items. The only player in
  the "middle." Still 4,500× behind tom7.
- **2 users**: registered, never spun once.

### What the data says about *why* they play

- **tom7** optimizes. Chat log, May 10: *"i miss the old wheel."* He keeps
  playing because the loop exists, not because it's fun. He explicitly
  nostalgia-posts about earlier seasons.
- **worm67** collects. 77 items vs 26. He wants completion, not leaderboard
  rank.
- **dylan** dabbles. Moon class (not Star), skipped fishing, still billions
  ahead. He's here because friends are.
- **dylan, June 16**: *"who still playing"* — the most recent chat message.
  This is a player asking why anyone bothers.

There is no social reason to stay. 50 total chat messages across the entire
lifetime. The community is three people running the same idle loop.

---

## 3. Season history & economy inflation

| Season | Theme | Notable change | Max score observed | Problem |
|---|---|---|---|---|
| 1 | Launch | Basic wheel | moderate | — |
| 2 | Growth | Streak bonuses | ~10^10-scale | exponential streaks unbounded |
| 3 | Explosion | More multipliers | googol-scale (400+ digits) | numbers meaningless |
| 4 | Peak chaos | Continued inflation | googol-scale | players churn (f22, griffin leave) |
| 5 | Soft cap | 96.7B max win | 96.7B | cap makes ceiling obvious |
| 6 | Cast & Reel | Fishing added, 269B max | 269B | fishing optional, ignored by dylan |
| 7 | Endless | Auto-spin every 3s, 4 infinite axes, classes | 83B | idle game; engagement collapses |
| 8 | (empty) | placeholder row, no content | — | not shipped |

### The inflation arc

Seasons 1–4 let streak bonuses compound exponentially with no cap. Win counts
reached numbers with hundreds of digits. This is not a balance issue — it's a
**legibility issue**. A player cannot care about gaining $10^{10^{20}}$ wins.
The number has no human meaning. f22 and griffin, the first two #1 players,
both quit during this era.

Season 5 introduced a soft cap (96.7B). Good intent, but a cap makes the
ceiling *visible* — once you can see the top, the climb ends. Season 6 raised
it to 269B with fishing. Season 7's auto-spin then let players hit it without
playing.

### Why auto-spin killed the game

Season 7's server-side auto-spin (every 3 seconds) turned an active decision
game into a pure idle game. The proof is in the spin counts: tom7, worm67, and
dylan all sit at **1.11M–1.14M spins**, within 3% of each other. That is not
three humans playing differently — that is three clients running the same
automated loop for the same number of hours.

An idle game with 8 registered users and 3 active players has no future. The
spin must become a **decision** again, or the game has no game.

---

## 4. Core problems diagnosed

### P1 — The game was solved
All three active players converged on **Star class + maxed infinite upgrades +
protection stacking**. The class system (Season 7) was meant to create build
diversity. It failed: 2 of 3 use Star. The four infinite upgrade axes were
meant to offer branching progression. They didn't branch — they were all
maxed. There is one optimal build and everyone found it.

### P2 — Auto-spin removed the player
Server-side auto-spin every 3s means the optimal strategy is to log in, enable
it, and close the tab. Spin counts prove it (1.11M / 1.14M / 1.11M). The player
is not making decisions. They are spectating a spreadsheet.

### P3 — Numbers are meaningless
21.8 billion wins. 269B max. Googol-scale history. The community pot is
permanently maxed at its 75% cap. A player cannot feel a win they cannot
comprehend. Inflation has destroyed the signal value of every number in the
game.

### P4 — No mid-tier content
The gap between casual (4.8M wins) and dedicated (21.8B) is **4,500×**. There
is nothing for a new or returning player to aim at that feels achievable. The
2 users who registered and never spun saw a wall and left.

### P5 — Fishing is orphaned
dylan, a dedicated player, never touched fishing (zero lure_mastery, zero
fish_exchange). It's a whole subsystem disconnected from the core loop. It
doesn't gate anything, doesn't unlock anything meaningful, and its rewards
(fish_clicks) only feed the Singularity — which **no one has ever bought**
(1e67 cost is unreachable even for tom7 with 3.9B fish_clicks).

### P6 — The Singularity is a dead goal
Costs 1e67 fish_clicks. tom7 has 3.9B. The gap is 58 orders of magnitude.
This "ultimate goal" has never been purchased and mathematically cannot be
reached under any current loop. It exists only as a permanent failure state.

### P7 — The community is dead
~50 chat messages total. Last meaningful exchange: tom7 "i miss the old wheel"
(May 10) and dylan "who still playing" (June 16). There is no social fabric.
A multiplayer game with no social reason to log in has no retention.

### P8 — No reason to return
The playerbase explicitly said: *we will return, but only if it is drastically
different.* Season 7 was not different — it was Season 6 with automation. The
"drastically different" bar is the success criterion for Season 8.

---

## 5. Season 8 design pillars

Everything below traces back to one of these four pillars. If a proposed
feature doesn't serve a pillar, it doesn't ship in Season 8.

### Pillar A — The spin is a decision
Every spin should involve a choice with a tradeoff. No more pure
"click to win." Choices: how much to wager, which wheel mode, when to bank vs
press, which risk tier. Auto-spin may exist as a *limited convenience* (e.g.
100 spins, then stop), never as the default engagement mode.

### Pillar B — Legible numbers
A big win should be a number a human can feel. Target range: **hundreds to
low millions** for normal play, **tens of millions** for endgame. This
requires an economy reset and a hard cap on compounding multipliers. No more
billions, ever.

### Pillar C — Weekly variety, not weekly grind
The 8.1 / 8.2 model changes *what* the optimal play is each week — not just
adds more numbers to stack. One week favors aggression, the next favors
banking, the next favors fishing. The meta should rotate so the "solved"
build from week N is suboptimal in week N+1.

### Pillar D — A reason to log in that isn't the wheel
Social hooks, shared goals, limited-time events, collection mechanics that
can't be idled. The wheel is the engine, but it can't be the *only* reason to
open the game.

---

## 6. New upgrade ideas

All upgrade proposals are evaluated against the pillars. Costs are **reset
economy** costs (hundreds-to-millions range, not billions).

### 6.1 Wager system (replaces flat auto-spin)

The core rework. Each spin is a **bet**:

| Upgrade | Effect | Cost (wins) | Tier |
|---|---|---|---|
| `wager_unlock` | Unlocks the wager input — choose 1×–10× stake per spin | 500 | 1 |
| `wager_safety_net` | On a loss at ≥5× stake, recover 25% of wagered wins | 2,000 | 2 |
| `wager_hot_streak` | Each consecutive win at the same stake tiers raises payout +5% (caps at +50%) | 8,000 | 2 |
| `wager_double_down` | After a win, optionally re-spin at 2× stake using the winnings | 25,000 | 3 |
| `wager_insurance` | Pay 10% of stake to guarantee no-loss on next spin (once per 10 spins) | 50,000 | 3 |

**Why:** Makes every spin a decision (Pillar A). High-stake spins create
risk/reward the old flat-spin loop never had. Hot-streak rewards active
attention — you must *choose* to keep pressing.

### 6.2 Wheel modes (rotating)

Replace the single static wheel with selectable modes. Each mode changes the
risk profile:

| Mode | Profile | When |
|---|---|---|
| **Steady** | 70% small wins, 5% loss, no jackpot | always available |
| **Volatile** | 40% loss, 10% big win, 2% jackpot | always available |
| **Inverted** | Losses become small wins, wins become small losses | weekly rotation |
| **Gravity** | Outcomes drift toward the last result (streaks amplify) | weekly rotation |
| **Mirror** | Two spins resolve simultaneously; take the better | weekly rotation |

**Why:** Kills the single optimal strategy (Pillar C). The "solved" build for
Steady is wrong for Volatile. Weekly rotation means last week's optimal is
this week's liability.

### 6.3 Prestige upgrades (replace infinite upgrades)

The Season 7 infinite upgrades (`winmult_inf`, `bonusmult_inf`, etc.) failed
because they had no ceiling — players just maxed them. Replace with a
**prestige** system:

- **Prestige** resets your wins and non-cosmetic upgrades, but grants a
  permanent `prestige_level` (1–20).
- Each prestige level gives +2% base win value — **flat, not compounding**.
- Prestige is the *only* way to exceed the soft cap.
- Cosmetics and collection progress are permanent (not reset).

| Upgrade | Effect | Cost | Notes |
|---|---|---|---|
| `prestige_unlock` | Enables the prestige action | 1,000,000 wins (one-time) | Tier 3 |
| `prestige_efficiency` | Reduces win-loss on prestige by 10% per level | 500K wins/level, max 5 | softens the reset sting |
| `prestige_legacy` | Keep 1 owned functional upgrade per level on prestige | 1M wins/level, max 3 | strategic choice: what to keep |

**Why:** Prestige creates a reason to reset *voluntarily* (Pillar A), gives
returning players a permanent identity (Pillar D), and caps compounding so
numbers stay legible (Pillar B). A prestige-20 player has +40% — meaningful,
not 21.8 billion.

### 6.4 Fishing integration (fixes P5)

Fishing must connect to the core loop or be cut. Proposal: **fishing feeds the
wheel, not a separate currency sink.**

| Upgrade | Effect | Cost | Notes |
|---|---|---|---|
| `fish_to_wager` | Caught fish convert to wager tokens at a set rate | 5,000 wins | bridges fishing → wheel |
| `lure_specialization` | Choose a fish family; +50% value for that family, −25% for others | 10,000 wins/each | creates fishing builds |
| `catch_of_the_day` | First catch each day is worth 5× | 3,000 wins | daily login hook |
| `aquarium` | Display caught fish; each unique species gives +0.1% wheel luck | 15,000 wins + fish | collection → power, gently |

**Why:** Gives dylan a reason to fish. Makes fishing a *build choice* (Pillar
A) rather than an isolated grind. The aquarium ties collection (worm67's
motivation) to the wheel without making it mandatory.

### 6.5 Defensive / utility upgrades (rework)

The old protection stack (`guard`, `auto_guard`, `regen_shield`, `resilience`,
`streak_armor_inf`) let players negate loss entirely. In a wager system, that
breaks the risk loop. Rework:

| Upgrade | Effect | Cost | Notes |
|---|---|---|---|
| `guard` | Blocks one loss per session (manual trigger) | 1,000 wins | active, not passive |
| `guard_charge` | +1 guard charge, max 3 | 10,000 wins/level | scarce |
| `regen_shield` | Regenerates 1 guard charge every 50 spins | 5,000 wins | slow, not infinite |
| `resilience` | Convert a loss into a 50% refund once per 20 spins | 20,000 wins | fallback, not immunity |

**Removed:** `auto_guard` (passive immunity), `streak_armor_inf` (infinite
stacking). Protection must be **scarce and active**, not a permanent wall.

---

## 7. New feature ideas

### 7.1 Daily bounties

Each day, 3 rotating objectives drawn from a pool:

- "Win 5 spins at 5× stake"
- "Catch 10 fish"
- "Land a jackpot in Volatile mode"
- "Prestige once"
- "Win 3 Mirror-mode doubles"

**Reward:** wager tokens, cosmetic fragments, or a one-day buff. **Why:**
gives a reason to log in daily that isn't "run the auto-spinner" (Pillar D).
Forces engagement with the new wheel modes and wager system. Bounties are the
opposite of idle — they require *specific actions*.

### 7.2 Community goal (replaces Community Pot)

The Community Pot is permanently maxed at 75% — it's dead content. Replace
with a **rotating shared goal**:

- **Weekly:** all players collectively catch 5,000 fish / land 500 jackpots /
  prestige 50 times.
- On completion, **all participants** get a cosmetic or a week-long buff.
- Contribution is capped per player so one whale (tom7) can't solo it.

**Why:** rebuilds the social fabric (Pillar D). The 3 active players currently
have no shared objective. A capped-contribution goal means dylan and
chudwigvanbetahoven matter, not just tom7.

### 7.3 Leaderboard reset + legacy boards

Season 8 wipes the active leaderboard (the billions are gone). But preserve
Seasons 1–7 as **legacy boards** — a Hall of Fame. f22 and griffin are still
#1 of their seasons there. tom7's 21.8B is memorialized, not erased.

**Why:** returning players (f22, griffin) keep their legacy. The live board
becomes legible again (Pillar B). The Hall of Fame gives the game *history* —
something the 50-message chat never built.

### 7.4 Build loadouts

Let players save and name 3 loadouts — combinations of class, active
upgrades, and wheel-mode preference. Quick-swap between them.

**Why:** weekly mode rotation (Pillar C) means the optimal build changes. If
swapping is painful, players won't experiment. Loadouts lower the cost of
adaptation. worm67 (77 items) benefits most — he has the inventory to build
diverse loadouts.

### 7.5 Replays & big-win sharing

When a player hits a jackpot or a 10× wager win, generate a shareable replay
string (or animated GIF). Post to chat with one click.

**Why:** the chat is dead (50 messages). Give players something to *show*.
A 10× double-down jackpot is a moment; right now it's a line in a log. Sharing
creates the social loop the game has never had.

### 7.6 The Singularity, reworked

The Singularity (1e67 fish_clicks) was never bought. Rework it as a
**server-wide community unlock** rather than a personal purchase:

- Requires the entire server to collectively contribute a *legible* amount
  (e.g. 100M fish_clicks total — reachable, not 58 orders of magnitude away).
- On unlock, triggers a server-wide event (cosmetic transformation, new wheel
  mode, a one-time narrative beat).
- Then resets — a new community goal takes its place.

**Why:** the Singularity is currently a permanent failure state (P6). As a
shared, reachable, repeating goal it becomes the centerpiece of the social
loop (Pillar D) instead of a tombstone.

---

## 8. Themes & UX improvements

### 8.1 Number formatting — the single most important UX fix

21,843,192,441 wins is not readable. The game must format numbers to human
scale **everywhere**:

- < 1,000: raw (`842`)
- 1,000–999,999: comma-grouped (`84,201`)
- 1,000,000–999,999,999: compact (`8.42M`)
- ≥ 1,000,000,000: compact (`8.42B`) — but this range should be *rare* after
  the economy reset, reserved for legacy/Hall-of-Fame display only.

**Why:** Pillar B in its purest form. A player must be able to glance at their
win count and *feel* it. This is free to implement and changes the entire
perceived texture of the game.

### 8.2 New wheel themes (seasonal)

Rotate the cosmetic wheel themes with each weekly patch to signal "this week
is different":

| Theme | Visual | Patch |
|---|---|---|
| **Tidal** (8.1) | Water-color blues, fish swim across the wheel on big wins | launch |
| **Ember** (8.2) | Warm oranges, sparks fly on volatile-mode wins | week 2 |
| **Frost** (8.3) | Ice-crystal shards, cracking animation on losses | week 3 |
| **Aurora** (8.4) | Shifting greens/purples, northern-lights trail on the pointer | week 4 |
| **Vintage** (8.5) | Deliberate retro look — *"the old wheel"* tom7 misses | week 5 |

The **Vintage** theme is a direct callback to tom7's May 10 chat message:
*"i miss the old wheel."* Ship it as a love letter to the engaged player who
never left.

### 8.3 Wager UI rework

The current wheel is a single spin button. The wager system needs:
- A **stake slider** (1×–10×) with clear risk labeling (Safe / Bold / Reckless).
- A **double-down button** that appears only after a win.
- A **hot-streak meter** that fills with consecutive same-stake wins.
- A **bank button** to lock in winnings and reset the hot-streak (the
  bank-vs-press decision is the core tension).

### 8.4 Onboarding flow (fixes P4)

New players (the 2 who registered and never spun) saw a wall. Add a 4-step
onboarding:
1. **First spin** — guided, free, explains the wheel.
2. **First wager** — guided 1× bet, explains risk.
3. **First fish** — one cast, explains the loop bridge.
4. **First bounty** — shows the daily objective panel.

Reward each step with a cosmetic. Total cost to the economy: negligible.
**Why:** the mid-tier gap (P4) starts at the door. If step 1 doesn't hook,
step 1,000,000 never happens.

### 8.5 Fishing panel clarity

dylan never engaged with fishing. The panel likely doesn't communicate its
value. Improvements:
- Show the **conversion rate** to wager tokens prominently (`1 fish = 12
  wager tokens`).
- Show **catch-of-the-day** bonus as a countdown timer.
- Show **aquarium progress** (species caught / total) with a luck bonus readout.
- Add a **"why fish?"** tooltip on first hover.

### 8.6 Chat revival

50 messages is a dead channel. To revive it:
- **Auto-post big wins** (jackpot, 10× double-down) to chat with a one-click
  share — the player doesn't have to type.
- **Bounty completion announcements** ("tom7 completed: Land a jackpot in
  Volatile mode").
- **Community-goal progress milestones** ("2,400 / 5,000 fish this week").
- Keep raw chat — but seed it with game events so it's never empty.

### 8.7 Accessibility

The existing `fishsize_*` items (all cost 1, framed as accessibility features)
are a good instinct. Extend:
- **Reduced motion** toggle (disables spark/aurora animations).
- **High-contrast** theme variant.
- **Screen-reader-friendly** outcome announcements (aria-live region on spin
  result).
- **Keyboard spin** — spacebar to spin, number keys for wager tiers.

---

## 9. The weekly reset model (8.1, 8.2, …)

You want weekly **updates**, not weekly **seasons**. The distinction matters:
the season (8) is the era; the point releases (8.1, 8.2) are the updates that
keep it alive. This is the right model — it gives players a reason to check in
weekly without the fatigue of full season resets.

### Design rule: each week changes the meta, not the numbers

A weekly update that just adds +1 upgrade level is not "drastically
different" — it's the same grind. Each 8.x should shift **what optimal play
means**:

| Patch | Theme | Meta shift | Ship content |
|---|---|---|---|
| **8.1** | Launch / Tidal | Economy reset + wager system + prestige. The foundational change. | wager upgrades, prestige, number formatting, onboarding, Tidal theme |
| **8.2** | Ember / Volatility week | Introduce Volatile + Inverted wheel modes as the rotation. Aggressive play favored. | wheel-mode selector, hot-streak meter, Ember theme |
| **8.3** | Frost / Banking week | Introduce Gravity mode. Banking becomes optimal; hot-streaks dangerous. | bank button, guard rework, Frost theme |
| **8.4** | Aurora / Fishing week | Fishing integration ships. Fish-to-wager, aquarium, catch-of-the-day. | fishing rework, aquarium, Aurora theme |
| **8.5** | Vintage / Community week | Community goal + reworked Singularity. Social loop goes live. | community goals, Singularity rework, replays, Vintage theme |
| **8.6** | Prestige week | Prestige loadouts, legacy boards, Hall of Fame. | build loadouts, legacy boards |
| **8.7+** | Rotation | Cycle wheel modes, rotate bounties, introduce new community goals. | ongoing variety |

### Weekly reset mechanics

- **Bounties** reset daily (not weekly) — gives a reason to log in every day.
- **Community goals** reset weekly — the shared objective changes every 7 days.
- **Wheel-mode rotation** changes weekly — last week's optimal build is
  suboptimal this week.
- **Leaderboard** does NOT reset weekly — it's a season-long ladder. Weekly
  resets are for *content*, not *progress*.
- **Prestige** is always available — players choose when to reset, the game
  doesn't force it.

### What NOT to reset weekly

- Cosmetics (permanent — worm67's 77 items stay).
- Prestige level (permanent — the whole point).
- Legacy boards (permanent — history is history).
- Collection progress / aquarium (permanent).

### Patch cadence reality check

You have **3 active players**. Weekly patches are ambitious for a team of any
size serving 3 players — but the 8.x model is what they asked for ("drastically
different"). Prioritize: 8.1 must land the economy reset + wager system, because
everything else depends on it. If 8.2 slips a week, the rotation just shifts.
Do not let the cadence pressure dilute 8.1's foundations.

---

## 10. Phased roadmap

### Phase 0 — Pre-launch cleanup (before 8.1)

- [ ] Remove or severely limit server-side auto-spin. It can remain as a
      capped convenience (e.g. 100 spins, then manual reset), never default.
- [ ] Economy reset: convert existing win counts to a legacy "Season 1–7"
      stat. Season 8 wins start at 0. Players keep cosmetics and a
      `legacy_prestige` badge scaled from their old standing.
- [ ] Migrate the existing `season_number = 8` placeholder row: set a real
      end date or convert to the rolling 8.x model with per-patch metadata.
- [ ] Number formatting (8.1 UX) — ship this *first*, before anything else,
      so every subsequent feature displays in legible scale.

### Phase 1 — 8.1 Launch

- [ ] Wager system (6.1): `wager_unlock`, stake slider, double-down.
- [ ] Prestige system (6.3): `prestige_unlock`, flat +2%/level, cap at 20.
- [ ] Number formatting (8.1).
- [ ] Onboarding flow (8.4).
- [ ] Tidal theme.
- [ ] Daily bounties v1 (7.1) — start with 3 simple objectives.

### Phase 2 — 8.2 / 8.3 (weeks 2–3)

- [ ] Wheel-mode selector (6.2): Steady + Volatile always available; Inverted
      + Gravity as weekly rotation.
- [ ] Bank button + hot-streak meter (8.3).
- [ ] Guard rework (6.5): remove `auto_guard`, `streak_armor_inf`; make
      protection scarce and active.
- [ ] Ember + Frost themes.

### Phase 3 — 8.4 (week 4)

- [ ] Fishing integration (6.4): fish-to-wager, lure specialization,
      catch-of-the-day, aquarium.
- [ ] Fishing panel clarity (8.5).
- [ ] Aurora theme.

### Phase 4 — 8.5 (week 5)

- [ ] Community goals (7.2): replace dead Community Pot.
- [ ] Singularity rework (7.6): server-wide unlock, repeating.
- [ ] Replay sharing (7.5): big-win GIFs to chat.
- [ ] Chat revival (8.6): auto-post events.
- [ ] Vintage theme — the "old wheel" callback.

### Phase 5 — 8.6+ (week 6 onward)

- [ ] Build loadouts (7.4).
- [ ] Legacy boards / Hall of Fame (7.3).
- [ ] Accessibility pass (8.7).
- [ ] Ongoing weekly rotation: bounties, community goals, wheel modes.

---

## 11. Risks & open questions

### R1 — Economy reset backlash
The three active players have 3.6B–21.8B wins. Resetting to 0 is a hard sell,
even with a legacy badge. **Mitigation:** legacy boards (7.3) memorialize
their old standing; prestige level (6.3) gives a permanent identity that
*starts* from their prior engagement (e.g. tom7 starts Season 8 at prestige 5
based on his Season 1–7 totals). The reset is of *numbers*, not of *identity*.

### R2 — Wager system complexity
The wager system adds decision overhead to what was a zero-thought loop. Some
players (tom7, the optimizer) will love it; others may find it tedious.
**Mitigation:** 1× stake is always available and behaves like the old spin.
The wager system adds *options*, not obligations. But the default must still
require a choice (stake selection), not revert to one-click auto-spin.

### R3 — Weekly cadence sustainability
You have 3 players. Is a weekly patch cycle sustainable for you as the
developer? **Open question.** The roadmap above is ambitious. If cadence
slips, prioritize: 8.1 (foundation) > 8.4 (fishing, fixes P5) > 8.5
(community, fixes P7). The themes and wheel-mode rotations are the cheapest
to produce and can fill gaps.

### R4 — Does "drastically different" mean "reset" or "evolve"?
The playerbase said they want drastic difference. The economy reset and
auto-spin removal are drastic. But the *core loop* (spin a wheel, win/lose,
upgrade) is preserved — it's the decisions *around* it that change. This is
intentional: a wheel game that stops being a wheel game loses its identity.
**Open question for you:** is the wager + modes + prestige rework drastic
enough, or do they want a more fundamental genre shift?

### R5 — Fishing's role
Two options: (a) integrate fishing into the wheel loop (6.4), or (b) cut it.
dylan's zero-engagement proves the current middle ground (exists but doesn't
matter) is the worst option. This document proposes (a). If 8.4 ships and
fishing still sees no engagement, (b) becomes the right call.

### R6 — The 2 dormant users + 2 never-played users
4 of 8 registered users are inactive. The onboarding flow (8.4) targets the
never-played pair. The churned winners (f22, griffin) are the real prize —
they said they'd return if the game is drastically different. The legacy
boards (7.3) + the Vintage theme (8.5) are the explicit hooks for them:
*your history is preserved, the game is new, come see.*

### R7 — Auto-spin removal may shrink "engagement" metrics
Spin counts will drop from 1.1M to... whatever 3 humans actively clicking
produces. This is **correct and intended** — 1.1M auto-spins is not
engagement, it's a bot. But if you measure success by spin count, the numbers
will look worse before they look better. Retention and daily-active (not spin
count) is the metric to watch.

---

## Appendix: Player retention priorities

| Player | Status | Hook | Risk |
|---|---|---|---|
| tom7 | active, nostalgic | Vintage theme, prestige, optimizer's paradise (wager modes) | may resist auto-spin removal |
| worm67 | active, collector | aquarium, 77-item loadouts, cosmetic themes | may resist economy reset |
| dylan | active, fading | fishing integration, bounties, social loop | "who still playing" — highest churn risk |
| f22 | churned (S1–2 #1) | legacy board, Vintage theme, Hall of Fame | may not return at all |
| griffin | churned (S3 #1) | legacy board, Hall of Fame | may not return at all |
| chudwigvanbetahoven | casual | onboarding, mid-tier bounties, legible numbers | gap still large |
| 2 never-played | dormant | onboarding flow | unknown |

---

*End of document. This is a planning document only — no code changes have been
made. All figures are from the live `wheeldb` database, `PATCH_NOTES.md`, and
`models.py` as of 2026-06-17.*
