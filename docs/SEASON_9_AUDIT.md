# Season 9 "Tides": blind audit

Audited 2026-10-08 on staging (claudeqa1 / claudeqa2, Playwright at 1920, 1440, 1366, 1280, 768 and 390 widths) against the backend code. For each feature: what it does, how it is communicated, and the gap.

## 1. What is the player's goal?

**Finish a tide in the top 3 by wins to earn a permanent medal.** Wins reset when the tide turns (Friday 21:00 UK). Medals and cosmetics are kept.

How it is communicated: patch notes, one What's New line ("wins reset, medals are forever") and the Hall of Fame. **Nothing on the main screen states it.** There is no onboarding, no "your rank this tide", and no countdown framed as "time left to place". A new player sees a wheel, a shop and a pile of side panels with no reason to care about any of them.

**Gap (highest priority):** one persistent line near the scoreboard, e.g. "Tide ends in 2d 4h · you are #7 · top 3 earn a medal", would give every other system a purpose.

## 2. Core loop

| Feature | What it does | Communicated? | Gap |
|---|---|---|---|
| Spin / auto-spin | One spin every 3 s on auto; wins add to score, losses add to the loss counter | Yes | none |
| Win streak + streak bonus | Consecutive wins add an exponential bonus (streak_bonus) | Number shown, "BONUS +N" | Exponential growth reaches ~1e38 for a few players (see §6) |
| Wheel modes | Steady (70/30), Volatile, plus one weekly rotating mode (inverted / gravity / long_shot) | Mode buttons + odds text | Rotation is on the ISO week (Monday UTC); tides flip on Friday, so the two clocks disagree |
| Inverted mode | Slice labels are swapped: the big slice reads "WIN" but is a backend **loss**; the result says "YOU LOSE" and adds a loss | Odds copy "60% win · 35% loss" matches the labels, not the outcome | The loss-farming idea is never explained. Live from Mon 12 Oct (week 42) |
| Jackpot | Mode-dependent multiplier (×5 inverted, mode value normally, ×25 echo / item) | Banner now shows the real multiplier (fixed in this pass) | none |

## 3. Side panels

| Panel | What it gives | Communicated? | Gap |
|---|---|---|---|
| Dice roll | At streak ≥3, roll 2 dice (3 with Extra Die); the total is added to the streak. Double 6 doubles, double 1 halves. 1 charge per 10 min | Tooltip rewritten this pass | Teal now; purple fixed |
| Stake (Wager) | Risk 5–30% of wins on the next spin; win pays it back double | Redesigned this pass: safe/bold/reckless steps + explainer | Double Down pending, Insurance armed and Hot Streak states **not verified visually** (claudeqa1 can't reach them) |
| Bounties | 3 daily tasks; slot 1/2/3 pays 1/2/3 **insurance tokens** (max 6/day) | Subtitle + reward now on each row (this pass) | Tokens are a dead end (§4). `bank` and `double` bounties need tier items most players don't own. The mirror bounty could never complete and was removed (this pass) |
| Free tokens | 3 insurance tokens | Button now says so | Same dead end |
| Community goal ("land 100 jackpots server-wide") | On completion: 500 insurance tokens + 1 cosmetic fragment to each contributor, **and** the pot fills for 7 days | Subtitle added this pass | Tokens are a dead end, fragments have no spend path, and the pot is a **nerf** (§5) |
| Happy hour | 2× pot contributions, more legendary fish until 21:00 UTC | Banner now shows the end time in local time | none |
| Fishing | Catch fish for wins; Encyclopaedia of species | Panel + first-time panel tips | none found |
| Chat | Server chat | Starts closed under 900px tall (it was overlapping fishing) | none |

## 4. Insurance tokens: a dead end

Tokens only do something with **Insurance** (tier 3: 100K cumulative wins + 50K cost, and it resets every tide) or **fish_to_wager**, which is not in the client shop. So the goal, bounties and free-token rewards do nothing for nearly every player. Prod data: 106 of 112 players with any cumulative wins are below 10K, so tier 3 is out of reach for them.

**Decision needed:** give tokens a use every player can reach, or change what these rewards pay out.

## 5. Bugs and no-ops found (mechanics: not changed, need your call)

1. **Community goal makes the game worse.** Completion sets the pot to "filled" with win_chance 55% for 7 days (cut short at rollover). While the pot is active every spin is 55/45 with **no jackpots** in every mode, so Steady drops from 70% to 55%. The reward punishes the server.
2. **Guard "activate" button and Guard Charge (10K)** only decrement charges. Guard already blocks automatically, so these are a paid no-op.
3. **Catch of the Day (3K)** has no effect; "5x tokens" is false.
4. **Lure Specialization (10K)** requires fish_to_wager, which can't be bought, and does nothing.
5. **Insurance copy** says "Caps next loss at stake amount". The code refunds the stake, still counts the loss, and burns the charge on a win.
6. **Functional upgrades reset every tide**, but tier gates use lifetime cumulative wins. Only the patch notes say that upgrades reset.

## 6. Upgrades

Functional items reset each tide. Cosmetics persist. Tier 2 needs 10K cumulative wins and tier 3 needs 100K.

| Group | Items | Does | Copy accurate? |
|---|---|---|---|
| Win Power I–III | 200 / 600 / 2K | +20/40/60% win multiplier | Yes |
| Bonus Power I–III | 300 / 900 / 2.8K | 2×/4×/8× streak bonus | Yes |
| Wager Unlock (T1) | 500 | Enables the stake panel | Yes (rewritten) |
| Stake Extender I–III (T1) | 5K / 15K / 40K | Max stake 35/40/45% | Yes |
| Safety Net (T2) | 2K | Refunds 25% of a lost stake at 15%+ | Yes |
| Hot Streak (T2) | 8K | +5% per same-stake win, cap +50% | Yes |
| Double Down (T3) | 25K | Bet the whole last win, all or nothing | Yes (rewritten) |
| Insurance (T3) | 50K | Refunds the stake on a loss | **No** (§5.5) |
| Guard | 1K | Blocks the next loss automatically | Yes (rewritten) |
| Guard Charge | 10K | No-op | **No** (§5.2) |
| Regenerating Shield | 5K | Blocks a loss; recharges after 5 wins | Yes |
| Resilience | 20K | 50%: a loss drops the streak by 1 instead of resetting it | Yes |
| Fortune Charm / Win Echo | 1M each | 25%: +25% streak bonus / 20%: double a win | Yes |
| Jackpot | 3M | 1% ×25 on a win, 5% echo | Yes |
| Lucky Seven | 7M | Every 7th spin wins | Yes |
| Class: Earth / Moon / Star (T3) | 10M each | +25% fish / +5% procs / +20% Win Power | Yes |
| Lure I–IV, Master Lure | 100 → 500K | Faster bites, catch value ×1.5 → ×20 | Yes; Master needs the full Encyclopaedia (enforced) |
| Auto-Cast, Auto-Fisher I–IV | 1K; 300 → 500K | Auto-casting / auto-catching | Yes |
| Precise Angler I–III | 50K / 100K / 500K | Bonus for an early reel | Yes |
| Catch of the Day | 3K | No-op | **No** (§5.3) |
| Lure Specialization | 10K | Unbuyable, no effect | **No** (§5.4) |
| Fish skins (25 → 2.4M), themes, trails, confetti, backgrounds, panel sizes | various | Cosmetic | Yes |

**Economy note:** cumulative wins are bimodal in prod. 5 players are past 100K (max ~1e38 from the exponential streak bonus) and everyone else is under 10K. Nobody sits in between, so tiers 2–3 and every item priced above ~50K are effectively for those 5 players only.

## 7. Fixed in this pass (staging)

- Inverted "YOU LOSE" showed −1 losses; it now shows +1.
- Dice could be visible but unusable, and was purple; usability and colour fixed.
- Stake panel redesigned (steps, tiers, explainer), across 3 layouts.
- Jackpot banner shows the real multiplier.
- Copy on shop items, dice, happy hour, bounties, free tokens and goal says what each gives.
- Mirror bounty removed (mirror mode is never in rotation).
- Chat starts closed on short screens.

## 8. Corrections and unverified

- An earlier report said there were "no overlaps". That was wrong: chat overlapped the fishing panel on short screens. Now fixed and re-checked at 1920/1440/1366/1280.
- 1280×720 right column: the bounties panel fits with 0 px to spare by default. A visible Claim button will make the column scroll (it has `overflow-y: auto`). Not screenshotted.
- Stake states not seen in a browser: Double Down pending, Insurance armed, Hot Streak active.
- Per-tide earnings were not simulated. The price-vs-reach claims above use lifetime prod data.
