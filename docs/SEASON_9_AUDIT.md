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
| Wheel modes | Steady (70/30), Volatile, plus one weekly rotating mode (inverted / gravity / long_shot) | Mode buttons + odds text | Fixed: rotation now flips with the tide (Friday 21:00 UK) |
| Inverted mode | 60% LOSE slice is drawn bright (it is the good slice); labels now tell the truth | New copy: LOSE pays out 💀 losses, the currency for cosmetics | Live from the tide turn, Fri 9 Oct 21:00 |
| Jackpot | Mode-dependent multiplier (×5 inverted, mode value normally, ×25 echo / item) | Banner now shows the real multiplier (fixed in this pass) | none |

## 3. Side panels

| Panel | What it gives | Communicated? | Gap |
|---|---|---|---|
| Dice roll | At streak ≥3, roll 2 dice (3 with Extra Die); the total is added to the streak. Double 6 doubles, double 1 halves. 1 charge per 10 min | Tooltip rewritten this pass | Teal now; purple fixed |
| Stake (Wager) | Risk 5–30% of wins on the next spin; win pays it back double | Redesigned this pass: safe/bold/reckless steps + explainer | Double Down pending, Insurance armed and Hot Streak states **not verified visually** (claudeqa1 can't reach them) |
| Bounties | 3 daily tasks; slot 1/2/3 pays 1/2/3 **insurance tokens** (max 6/day) | Subtitle + reward now on each row (this pass) | Tokens now have a use (§4). `bank` and `double` bounties need tier items most players don't own. The mirror bounty could never complete and was removed (this pass) |
| Free tokens | 3 tokens | "Claim 3 free tokens", tooltip says what they do | none |
| Community goal ("land 100 jackpots server-wide") | On completion: 500 insurance tokens + 1 cosmetic fragment to each contributor, **and** the pot fills for 7 days | Subtitle states both rewards | Fragments have no spend path |
| Happy hour | More legendary fish until 21:00 UTC (its 2× pot contributions are invisible in S9, so the banner no longer mentions them) | Banner shows the end time in local time | none |
| Fishing | Catch fish for wins; Encyclopaedia of species | Panel + first-time panel tips | none found |
| Chat | Server chat | Starts closed under 900px tall (it was overlapping fishing) | none |

## 4. Tokens

**Correction:** the earlier report said tokens only worked with Insurance or fish_to_wager. Wrong: the backend has always supported paying a stake with tokens (1 token = 1 🏆, stake ≥30%, not with Double Down), but the client hid the toggle behind fish_to_wager, which can't be bought.

**Decision:** the token balance shows for anyone holding tokens, with a "stake 30% to use them" hint, and the "Pay stake with 🪙 tokens" toggle appears at a 30% stake. Tokens also arm Insurance.

## 5. Decisions taken (were "your call")

1. **Community goal:** a full pot now adds +5% to the current mode's win chance for the rest of the tide. It no longer replaces every mode with 55% and no jackpots.
2. **Guard Charge and the Guard Block button:** removed (item, regen, `/api/guard`). Guard shows "Guard ready".
3. **Catch of the Day:** implemented. The first catch each UTC day is worth 5×.
4. **Lure Specialization:** removed from the shop.
5. **Insurance copy:** "Spend 1 🪙 to insure a spin: if it loses, your stake comes back (the loss still counts)".
6. **Tokens:** see §4.
7. **Inverted mode:** see §2.
8. **Clocks:** wheel modes rotate with the tide.
9. **Tier gates:** the lifetime 10K/100K gate is removed. Upgrades reset every tide, so price is the only gate. cumulative_wins is still tracked.

Not changed: the `bank` and `double` bounties still need Hot Streak or Double Down.

## 6. Upgrades

Functional items reset each tide. Cosmetics persist. There are no tier gates (T1–T3 below are historical labels).

| Group | Items | Does | Copy accurate? |
|---|---|---|---|
| Win Power I–III | 200 / 600 / 2K | +20/40/60% win multiplier | Yes |
| Bonus Power I–III | 300 / 900 / 2.8K | 2×/4×/8× streak bonus | Yes |
| Wager Unlock (T1) | 500 | Enables the stake panel | Yes (rewritten) |
| Stake Extender I–III (T1) | 5K / 15K / 40K | Max stake 35/40/45% | Yes |
| Safety Net (T2) | 2K | Refunds 25% of a lost stake at 15%+ | Yes |
| Hot Streak (T2) | 8K | +5% per same-stake win, cap +50% | Yes |
| Double Down (T3) | 25K | Bet the whole last win, all or nothing | Yes (rewritten) |
| Insurance (T3) | 50K | Refunds the stake on a loss | Yes (fixed) |
| Guard | 1K | Blocks the next loss automatically | Yes (rewritten) |
| Regenerating Shield | 5K | Blocks a loss; recharges after 5 wins | Yes |
| Resilience | 20K | 50%: a loss drops the streak by 1 instead of resetting it | Yes |
| Fortune Charm / Win Echo | 1M each | 25%: +25% streak bonus / 20%: double a win | Yes |
| Jackpot | 3M | 1% ×25 on a win, 5% echo | Yes |
| Lucky Seven | 7M | Every 7th spin wins | Yes |
| Class: Earth / Moon / Star (T3) | 10M each | +25% fish / +5% procs / +20% Win Power | Yes |
| Lure I–IV, Master Lure | 100 → 500K | Faster bites, catch value ×1.5 → ×20 | Yes; Master needs the full Encyclopaedia (enforced) |
| Auto-Cast, Auto-Fisher I–IV | 1K; 300 → 500K | Auto-casting / auto-catching | Yes |
| Precise Angler I–III | 50K / 100K / 500K | Bonus for an early reel | Yes |
| Catch of the Day | 3K | First catch each day ×5 | Yes (implemented) |
| Fish skins (25 → 2.4M), themes, trails, confetti, backgrounds, panel sizes | various | Cosmetic | Yes |

**Economy note:** cumulative wins are bimodal in prod. 5 players are past 100K (max ~1e38 from the exponential streak bonus) and everyone else is under 10K. Nobody sits in between, so every item priced above ~50K is effectively for those 5 players only.

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
