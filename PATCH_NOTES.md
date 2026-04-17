# Patch Notes

---

## Season 6 — Night Ocean — 17 Apr 2026

Season 6 overhauls fishing, balance, and the UI theme. The passive fish-clicking mechanic is replaced with an active **Cast & Reel** minigame; ability costs are significantly repriced to match the new economy; and the entire colour system is now driven by a CSS palette that carries forward cleanly into future seasons.

### Cast & Reel Fishing Minigame

The passive fish-clicking mechanic has been replaced with an active, timing-based **Cast & Reel** minigame. Active players now clearly outpace AFK/bot play at every upgrade tier.

**Loop:**
- Click **🎣 CAST** to drop your line. Shadow fish appear in the water as you wait.
- A bobber animates in the water. When the fish bites, it flashes and a **bite bar** begins depleting.
- **Click to reel** before the bar empties to catch the fish. Click too early (before the bite) and it's an instant miss.
- The server holds all timing — bite window, catch validation, and value calculation are anti-cheat authoritative.

**Fish Catalog — 13 Species**

Each catch awards Fish Bucks (formerly "Fish Clicks" — DB column unchanged):

| Tier | Species | Value |
|------|---------|-------|
| Common | 🐟 Minnow, 🦐 Shrimp, 🐠 Clownfish, 🐡 Pufferfish | 1–3 🐟 |
| Uncommon | 🦀 Crab, 🦑 Squid, 🐙 Octopus | 8–12 🐟 |
| Rare | 🦞 Lobster, 🐬 Dolphin, 🦈 Shark | 20–40 🐟 |
| Legendary | 🐋 Blue Whale, 🧜 Mermaid, ⭐ Lucky Fish | 75–120 🐟 |

**Lucky Fish** — catching a ⭐ sets a flag that doubles the value of your *next* successful catch.

**Fish Encyclopaedia:**
- New **📖 Fish Encyclopaedia** button (top-left). Shows all 13 species.
- Undiscovered entries appear as silhouettes with `???` name, value, and rarity.
- Entries unlock permanently on first catch. Progress counter shown.
- Completing the Encyclopaedia (all 13 species) unlocks the Master Lure and Master Auto-Fisher upgrades.

### 🎣 Fishing Gear — New Shop Section

All items cost Wins. Lure and Auto-Fisher chains replace the retired Click Frenzy items.

**Lure Upgrades** — reduce bite wait time and multiply catch value:
| Upgrade | Cost | Bite Speed | Value Multiplier |
|---------|------|-----------|-----------------|
| Lure I | 100 | 10% faster | 1.5× |
| Lure II | 500 | 20% faster | 2× |
| Lure III | 2,500 | 35% faster | 5× |
| Lure IV | 15,000 | 50% faster | 10× |
| ⭐ Master Lure | 500,000 | 65% faster | 20× + +1% legendary chance each |

Master Lure requires completing the Encyclopaedia. It also increases each legendary species' catch weight by +1 percentage point (Whale: 0.5% → 1.5%, Mermaid: 0.2% → 1.2%, Lucky: 0.3% → 1.3%).

**Auto-Cast** (1,000 wins) — automatically re-casts when idle. You still tap the bite window manually.

**Auto-Fisher Upgrades** — unlock the Auto-Fish tickbox; handle cast and reel automatically:
| Upgrade | Cost | Catch Rate | Pool |
|---------|------|-----------|------|
| Auto-Fisher I | 300 | 45% | Common + Uncommon |
| Auto-Fisher II | 2,000 | 55% | Common + Uncommon |
| Auto-Fisher III | 12,000 | 65% | Common + Uncommon |
| 🤖 Master Auto-Fisher | 500,000 | 75% | Common + Uncommon + **Rare** |

Master Auto-Fisher requires the Encyclopaedia. Auto-Fish never catches Whale, Mermaid, or Lucky Fish at any level. Auto-Fish fires every 6 seconds; rate-limited server-side.

**Precise Angler Upgrades** — reward fast reflexes with a catch value multiplier. Tier 2 (1,000 wins) required. Multipliers are exclusive — the highest gate hit wins:
| Upgrade | Cost | Threshold | Multiplier |
|---------|------|-----------|-----------|
| Precise Angler | 50,000 | ≤ 50% through bar | 1.2× |
| Precise Angler II | 100,000 | ≤ 20% through bar | 1.5× |
| 🎯 Master Angler | 500,000 | ≤ 15% through bar | 2× |

Master Angler requires the Encyclopaedia. All Precise Angler multipliers stack independently with Lure and Lucky Fish multipliers.

The catch popup and last-caught line both show the precise multiplier and percentage when a bonus triggers (e.g. `🎯 1.5x @ 17.2%`).

**Stats: Fastest Catch** — the Stats panel now shows a **Fastest Catch** row (under Season Fish Bucks) tracking the player's best (lowest) precise percentage from manual fishing.

### Balance Changes

#### Streak Bonus: Buffed Mid/High Range + Hard Cap
High streaks now pay significantly more. The soft-cap introduced in Season 5 was too aggressive — the mid and late curve segments have been boosted, and a hard cap replaces the old unbounded slow linear tail.

| Streak | S5 Bonus | S6 Bonus | Change |
|--------|---------|---------|--------|
| 15 | 4,096 | 4,096 | unchanged |
| 35 | 12,096 | 20,096 | +66% |
| 50 | 19,596 | 38,096 | +94% |
| 75 | 32,096 | 68,096 | +112% |
| 100 | 37,096 | 83,096 | +124% |
| 150 | 47,096 | **113,096** (cap) | +140% |

These are raw bonus values before Win Multiplier, Bonus Multiplier, Win Echo, and Fortune Charm.

#### Tier 3 Gate Lowered: 10,000 → 5,000 Wins
Tier 3 upgrades (Win Echo, Jackpot, Fortune Charm, Lucky Seven, Resilience, Dice upgrades) now unlock at **5,000 wins** instead of 10,000.

#### Upgrade Pacing: Cheaper Infinite Scaling
Win Power and Bonus Power infinite levels now scale more gently:

| Upgrade | Old Base | Old Scale | New Base | New Scale |
|---------|---------|---------|---------|---------|
| Win Power (inf) | 500,000 | ×1.25/lvl | 400,000 | ×1.18/lvl |
| Bonus Power (inf) | 250,000 | ×1.25/lvl | 200,000 | ×1.18/lvl |

#### Ability Repricing
Bonus ability costs have been significantly raised to match the richer Season 6 economy. These are now late-game investments rather than early purchases:

| Ability | Old Cost | New Cost |
|---------|---------|---------|
| Fortune Charm | 50,000 | 1,000,000 |
| Lucky Seven | 100,000 | 7,000,000 |
| Win Echo | 75,000 | 1,000,000 |
| Resilience | 5,000,000 | 10,000,000 |
| Jackpot | 300,000 | 3,000,000 |

**Streak Armor Infinite** tier costs have also been raised substantially (Lv 1: 500 → 500,000, scaling to Lv 10: 50,000 → 2,750,000) to reflect its defensive power at high streaks.

#### New Dice Upgrades
Two new Tier 3 dice upgrades:

- **🎲 Overcharge** (100,000 wins) — raises max dice charges from 3 → **4**.
- **🎲 Extra Die** (1,000,000 wins) — roll **3 dice** instead of 2. Range expands to 3–18. When 3 dice are in play they arrange in a triangle layout. New triple outcomes:
  - **Triple 6s (6,6,6)**: streak **×3** (Blessed Triple!)
  - **Triple 1s (1,1,1)**: streak **÷3** (Cursed Triple!)
  - Pair of 6s: streak ×2 (unchanged) / Pair of 1s: streak ÷2 (unchanged)

Extra Die requires Dice Charge III. Both upgrades are Tier 3 (5,000 wins gate).

#### Community Pot: Slower Cap Growth
The pot target now grows by **×1.25** per fill instead of ×1.5. After 10 fills the target is ~9,300 instead of ~57,700.

### Night Ocean Theme

Season 6 ships with a new **CSS palette variable system**. Every colour in the UI — buttons, glows, borders, progress bars, season countdown, active ability highlights — is now driven by a small set of CSS custom properties (`--p`, `--p-lt`, `--p-md`, etc.) set in `:root`. Future seasons override the palette in a single `body.page-seasonN {}` block with no manual per-element changes needed.

**Season 6 palette — Night Ocean:**
- **Primary**: deep violet-indigo (`#7766FF`) — readable against the dark background (≥4.5:1 contrast)
- **Primary light**: periwinkle (`#9988FF`) — used for UI text, glows, and active highlights
- **Secondary**: coral-red (`#CC2244`) — loss accents and the season countdown badge
- **Background**: near-black navy (`#020810`)

The season countdown timer now uses the secondary (coral) colour across all seasons that don't override it, replacing the leftover orange from Season 4. The community pot label and count text now track the primary palette instead of a hardcoded dark grey. Active ability buttons in the shop now use a palette-driven indigo gradient instead of a hardcoded green.

**🌙 Season 6 Theme** is available in the shop (Cosmetics → Page Themes, 1,000 losses) and is auto-granted to all players on rollover.

### Chat Window Improvements
- The chat panel is now **resizable** from the bottom-right corner (drag handle shown). Size persists across sessions via `localStorage`.
- A small **✕** close button added to the top-right of the chat panel. Re-open via the 💬 button in the top-left user bar.

---

## Balance Hotfix — 11 Apr 2026

### Click Power Rebalanced
The Click Power infinite upgrade formula has been changed to grow more gradually, preventing compounding click/frenzy income from scaling out of control at higher levels.

- **New formula**: each level adds **+0.25× multiplier** (was +1× per level).
  - Lv 1: ×1.25 (was ×2), Lv 4: ×2.0 (was ×5), Lv 8: ×3.0 (was ×9)
- **Tier costs lowered** to reflect the reduced per-level value:
  - Lv 1–5: 75 / 250 / 600 / 1,400 / 3,000 wins (was 100 / 400 / 900 / 2,000 / 4,500)
- Infinite levels beyond Lv 5 are unchanged (10,000 × 1.5^n). The upgrade still scales without limit.
- Frenzy passive ticks continue to scale with Click Power.

### Win Power & Bonus Power: Post-Tier Costs Reduced
The infinite levels beyond the fixed tier ladders were prohibitively expensive relative to their gains following the Season 5 streak bonus soft-cap. Both have been brought down:

**Win Power** (levels 8+):
- Base cost: 1,000,000 → **500,000** wins
- Scaling: ×1.4 → **×1.25** per level

**Bonus Power** (levels 7+):
- Base cost: 500,000 → **250,000** wins
- Scaling: ×1.4 → **×1.25** per level

Fixed tier ladders and multiplier values are unchanged.

---

## Season 5 — 10 Apr 2026

### Streak Bonus: Soft Cap
The streak bonus formula has been soft-capped to keep late-game streaks rewarding without becoming infinite.

- **Streaks 1–15**: identical to before — exponential growth (×2 per step, up to 4,096 at streak 15).
- **Streaks 16–35**: cubic growth — still large but tapering off (up to ~12,096 at streak 35).
- **Streaks 36–75**: linear growth at +500 per streak step.
- **Streak 76+**: slow linear growth at +200 per streak step.

Existing strategies are unchanged for the majority of players; the cap only affects streaks beyond 15.

### Dice Roll Rework: Charge System
The Dice Roll mechanic has been overhauled. It no longer costs Losses — instead it uses a charge-based system.

- **Charges**: you start with 1 maximum charge. Each charge replenishes every **10 minutes** automatically. A countdown timer shows when the next charge arrives.
- **Requirement**: you must have a **win streak of 3 or more** to roll. The dice can no longer be used on a loss streak.
- **Effect**: the sum of both dice (2–12) is added directly to your win streak.
- **Snake Eyes (1+1)**: cursed roll — your win streak is **halved**. High risk at high streaks!
- **New upgrades** in the shop let you increase your maximum charge capacity (see below).

### Community Pot: 30-Minute Win Rate Windows
The Community Pot has been completely reworked for Season 5.

- **30-minute win rate boost**: filling the pot activates a **30-minute server-wide win rate boost** for all players. The boosted rate is shown in the Community Pot panel during the window, along with a countdown timer.
- **Stacking rate**: each fill permanently increases the boost rate by **+0.5%** (50.0% → 50.5% → 51.0% → …), capped at **75%**. The accumulated rate carries forward between fills, so each window is stronger than the last.
- **Between fills**: win rate returns to the standard 50/50 until the pot is filled again. The pot display shows what rate the next fill will grant.
- **Target scaling**: the target now scales by **50% per fill** (instead of the old ×10 Fibonacci escalation). There is no ceiling — targets grow as long as the community keeps filling.
- **Season reset**: the pot target resets to 1,000 at the start of Season 5.
- **12-hour decay**: if the pot goes unfilled for 12 hours, the target shrinks by 20% (floored at 500) — pulling it back when community activity drops.
- **Window expiry**: once the 30-minute window closes, the pot advances to the next (50% larger) target and resets for the next round.

### Upgrade Tier Gating
Functional upgrades are now gated behind total win milestones to create a clearer early/mid/late-game progression.

| Tier | Unlocks at | Items unlocked |
|------|------------|----------------|
| Tier 1 | Always | Speed upgrades, Guard, basic Frenzy, Win/Bonus/Click Power, etc. |
| Tier 2 | 1,000 wins | Regenerating Shield, Auto-Guard, Final Frenzy, Extra Dice Charge |
| Tier 3 | 10,000 wins | Fortune Charm, Lucky Seven, Win Echo, Jackpot, Resilience, Max Dice Charge |

Locked items appear in the shop as greyed-out entries showing the required win count.

### New Upgrades

#### 🎲 Dice Charges
Two new upgrades extend your maximum dice charge capacity:

| Upgrade | Cost | Effect |
|---------|------|--------|
| Extra Charge | 2,000 wins (Tier 2) | Max charges: 1 → 2 |
| Max Charge | 15,000 wins (Tier 3, requires Extra Charge) | Max charges: 2 → 3 |

#### 🛡️ Streak Armor (Infinite Upgrade)
Requires **Resilience**. Each level adds **+1%** to the Resilience save chance, which starts at 50% and is hard-capped at 60% (10 levels max).

| Level | Cost | Save Chance |
|-------|------|-------------|
| 1 | 500 wins | 51% |
| 2 | 2,000 wins | 52% |
| 3 | 4,500 wins | 53% |
| … | … | … |
| 10 | 50,000 wins | 60% (MAX) |

### Jackpot Rebalanced
- **Multiplier reduced**: ×50 → **×25**.
- **Trigger chance reduced**: 2% → **1%** per win.
- **New — Jackpot Echo**: after a Jackpot hit there is a **5% chance** the next spin also triggers a Jackpot (×25). The echo can only chain once per spin.

### Season 5 Bioluminescence Theme
A new page theme — **Bioluminescence** — is the default look for Season 5. Cyan and coral accents replace the previous season's palette, covering the wheel, chat, leaderboard, and all UI chrome. It is also available as a purchasable cosmetic (1,000 Losses) for players who switch to another theme and want to return.

The **Season 4 Theme** (deep violet) is now available in the Page Theme shop for 1,000 Losses.

### Dice Roll: Blessed Roll & Spin Gate
Two additional dice mechanics added:

- **Double Sixes (6+6)**: blessed roll — your win streak is **doubled**. The rarest outcome and the highest reward.
- **Spin gate**: you must spin at least once between dice rolls. Rolling twice in a row without spinning in between is blocked. This prevents using the dice to repeatedly stack the streak without playing.

### Mobile: Dice Panel on Main Page
The Dice Roll panel is now visible on the main page on mobile, matching the desktop layout. It was previously not shown on small screens.

### Ocean Casino: Default Background & Animated Seabed
Ocean Casino is now the **default background** for all players — no purchase required to see it. Players who buy and equip a different background will override it as before.

The Ocean Casino background now features an **animated seabed scene** rendered behind the main UI. A static fallback is used automatically in Low-Spec Mode.

---

## Latest — 4 Apr 2026

### Mobile Responsiveness
The game is now fully playable on phones and tablets. Desktop layout is completely unchanged.

- **Bottom toolbar** — a fixed tab bar appears on screens ≤ 768 px with five buttons: Shop 🏪, Leaderboard 🏆, Fish 🐟, Season Winners 🏅, and Stats 📊.
- **Shop drawer** — the right-side panel (shop + sidebar) slides in from the right edge when tapped, and dismisses via the backdrop or a second tap on the toolbar button.
- **Fish & Community Pot** — the fish mascot and Community Pot are combined into a single overlay card, opened with the 🐟 toolbar button. The Community Pot is hidden from the crowded top bar on mobile.
- **Leaderboard & Season Winners** — both panels are hidden by default and toggled via the toolbar. The leaderboard docks above the toolbar; season winners appear as a full-width overlay below the top bar.
- **Backdrop dismiss** — tapping outside any open panel closes it.
- **Wheel scaling** — the wheel adapts to fill the available screen width/height on small viewports.
- **Compact top bar** — username hidden, community pot moved to the fish panel, reduced height to maximise vertical space.

---

## 4 Apr 2026

### Season 4 Balancing: Economy Overhaul
- **Functional upgrade chains repriced with ~10× per tier scaling.** Late-game functional items now cost millions of Wins — Max Spin (1M), Instant Auto (1M), Final Frenzy (30M). Cosmetic item prices are unchanged.
- **Special Upgrades repriced ×100.** Fortune Charm, Lucky Seven, Win Echo, and Jackpot are now 100× their previous cost. Resilience is ×10, now costing 5,000,000 Wins.

### New Fish Skins (Season 4)
Five new cosmetic fish skins added, continuing the existing loss-cost chain from Whale (2,000):
| Skin | Cost | Emoji |
|------|------|-------|
| Seal | 3,500 | 🦭 |
| Shrimp | 6,000 | 🦐 |
| Coral | 10,000 | 🪸 |
| Mermaid | 17,500 | 🧜 |
| Crocodile | 30,000 | 🐊 |

### Season 3 Page Theme
- A new **Season 3 Theme** cosmetic is now available in the Page Theme section of the shop (5,000 Losses).
- Applies the purple & orange colour scheme from Season 3 — useful if you're running a different page theme and want to switch back.
- Also fixes a pre-existing bug where the Season 2 page theme could not actually be equipped (it was missing from the server-side cosmetic slot registry).

### 🎲 Dice Roll
A new high-risk mechanic has been added between the wheel and the shop panel.

- **Cost**: spending all your current Losses (zeroed out on roll).
- **Effect**: two dice are rolled (each 1–6). The sum (2–12) **amplifies your current streak** — it extends a win streak further, or deepens a loss streak further.
- **Win streak**: roll adds to your streak (e.g. streak 5 + roll 9 → streak 14).
- **Loss streak**: roll subtracts from your streak (e.g. streak −3 + roll 7 → streak −10).
- **Zero streak**: the Roll button is disabled — there is no streak to amplify.
- **Reward**: streak bonuses are exponential (×2 per step from streak 3+), so boosting a win streak can unlock massive multipliers immediately.
- **Risk**: your entire loss balance is consumed, and rolling on a loss streak makes it worse. The dice do **not** guarantee a win on your next spin.
- The Roll button shows the exact loss cost before you commit. It is disabled if you have 0 losses, streak is zero, or a spin is in progress.

### Leaderboard: Hide Zero-Win Players
- Players with 0 wins are now hidden from the public leaderboard. Only players who have earned at least one win appear in the top 10.

---

## 28 Mar 2026

### Quality of Life
- **Shop prices** now use the same abbreviated format as win/loss counters (e.g. `10K`, `1M`, `70K`) instead of raw numbers.
- **Community Pot**: the flat `+10k` contribution button has been replaced with a **+10%** button that contributes 10% of the current pot target. The amount scales as the pot grows (100M target → +10M, 1B target → +100M, etc.).
- **Community Pot**: the "All in" button now correctly caps at whatever is remaining to fill the pot, rather than donating the player's full click balance.
- **Win counter**: wins are now capped at `9.99e99` to prevent the score displaying as `Infinity` at extreme multiplier values.

---

## 27 Mar 2026

### Season 3: Community Pot & Win Rate Boost
- Introduced the **Community Pot**, a global objective where all players can contribute their Fish Clicks.
- When the pot reaches its target, a **1-hour 75% Win Rate Boost** is activated for everyone on the server.
- The pot target starts at 100 million and multiplies by 10 each time it is completed.
- New `/api/community-pot/state` and `/api/community-pot/contribute` endpoints added.
- Current pot progress and active boost status are visible to all players.

### Multi-Currency Shop System
- The shop has been refactored to use a logical multi-currency system to balance progression:
    - **Functional Upgrades** (Speed, Multipliers, Click Frenzy, Protection, Special Upgrades) now cost **Wins**.
    - **Cosmetic Items** (Skins, Fish Size, Trails, Themes, Backgrounds, Page Themes) now cost **Losses**.
    - **The Singularity** remains the ultimate goal, costing **1 Billion Fish Clicks**.
- Existing players' balances are preserved, and item costs have been adjusted to suit the new currencies.
- **Auto-Guard** now costs **500 Wins** to trigger (was 500 Fish Clicks).

### New Cosmetic Content
- **Season 2 Page Theme**: A new premium theme added to the shop for those who want to relive the glory of the previous season.

### Enhanced Stats & Season History
- The Stats panel (📊) now includes a **Season History** section.
- Track your finishing position and final win count for all completed seasons.

### Technical Improvements
- The `/api/spin` response now returns `wins_delta` and `losses_delta` instead of absolute totals, improving client-side animation sync and preventing race conditions.
- Database schema updated (Migration 008) to support the Community Pot and history tracking.

---

## 24 Mar 2026

### Community Leaderboard Panel
- Leaderboard redesigned from a horizontal scrolling ticker to a vertical panel at the bottom-left, styled to match the Season Winners box.
- Expanded from top 5 to top 10 players.
- Now tracks and displays each player's **all-time highest win streak** (persisted in the database).
- Current active win streak shown per player — hidden if none.
- Active win streaks glow with an escalating fire effect: colour shifts from warm orange at streak 1 through to bright red with a multi-layer glow at streak 10+.
- Fish click balance counter moved above the leaderboard in the same bottom-left stack.
- Leaderboard refreshes every 5 seconds.

### Shop Collapse Toggle
- A `›` button in the top-right of the shop panel slides the shop fully off-screen.
- The button stays pinned in place — clicking `‹` brings the shop back. Smooth 0.3s transition.

### Rising Fire Effect
- A full-viewport fire effect now rises behind all game UI, scaling with your win streak.
- Built with HTML5 Canvas — no external libraries.
- **Embers** mode: rising particle sparks, visible from streak 3.
- **Inferno** mode: classic cellular automaton heat buffer with upward propagation, visible from streak 10.
- **Mix** mode (default): embers and inferno layered together with additive blending for the most dramatic look.
- Fire height scales linearly with streak — the screen is filled around streak 30, reaching a full inferno at 50+.
- Intensity lerps smoothly toward the current streak value each frame: wins cause the fire to grow gradually, and a loss causes it to fall gracefully rather than cut out abruptly.
- Low-Spec Mode and OS `prefers-reduced-motion` suppress the effect entirely.

---

## 23 Mar 2026

### Bug Fix: Fish Clicks Appearing to Drop After Each Spin
- Fixed a race condition where frenzy tick responses and spin responses could arrive out of order at the client.
- With high Click Power (e.g. ×20), each frenzy tick grants +10,000 fish clicks. If the spin response (carrying a stale pre-frenzy balance) arrived after the frenzy response, it would overwrite the display — making it look like ~10k clicks were removed per spin.
- The spin endpoint now sends a **`fish_clicks_delta`** (0 normally, −500 when Auto-Guard fires) instead of an absolute balance. The client applies it as a delta, so response ordering no longer matters.

---

### Bug Fix: Auto-Guard Guard State Not Reflected in UI
- After Auto-Guard restored a broken Guard, the "🛡️ Guard ready" indicator and shop state never updated to show Guard as owned — even though the backend had correctly re-added it.
- Fixed: the spin response now properly syncs Guard ownership in the frontend.

---

### Bug Fix: Auto-Guard Description Clarified
- Description now reads **"500 fish clicks"** instead of "500 clicks" to make clear the cost is in the in-game currency (flat, not scaled by Click Power).

---

### Anti-Click-Farming: DB-Level Click Budget
- The `/api/fish-click` endpoint now enforces a **75 raw clicks per 5-second rolling window** per user, tracked atomically in PostgreSQL with `FOR UPDATE`.
- Previously, the per-worker Flask-Limiter (`memory://` storage) could be bypassed in a 4-worker setup, giving up to 40× the intended click rate via scripted requests.
- Requests exceeding the budget still return 200 but award 0 clicks — no error shown, no disruption for normal play.
- Flask-Limiter on fish-click tightened from 10/s to 5/s as a first-pass filter.
- `/api/click-frenzy` now has a 2-second server-side cooldown (enforced in the DB) and a 1/s Flask-Limiter.

---

### Bug Fix: Guard No Longer Hidden in Shop
- Guard now stays visible in the shop permanently, even after purchasing Auto-Guard. Previously it was incorrectly treated as a superseded tier and hidden.

---

### Auto-Guard
- New upgrade in the **Protection** section (costs **10,000 clicks**, requires Guard).
- Toggle it on/off like Final Frenzy.
- When enabled and your Guard breaks, a new Guard is automatically purchased for **500 clicks** immediately before your next spin.
- If you have fewer than 500 clicks when it tries to trigger, Auto-Guard disables itself and shows a **"Not enough clicks"** warning.

---

### Low-Spec Mode Persists Per User
- Low-Spec Mode preference is now saved to your account in the database.
- Toggling it on one device/session will be remembered when you log in elsewhere.
- The ⚡ toggle in the top bar works the same as before.

---

### Infinite Upgrades — Win Power, Bonus Power & Click Power
The fixed upgrade chains for Win Power, Bonus Power, and Click Power have been replaced with a single upgradeable item per category that can be purchased unlimited times.

**Win Power**
- Levels 1–7 match the old tier costs and multipliers exactly (x2 → x128).
- Level 8+ continues at **+16 multiplier per level** (x144, x160, …), with costs scaling at **×1.4 per level** starting from 1,000,000.

**Bonus Power**
- Levels 1–6 match the old tier costs and multipliers exactly (x2 → x100).
- Level 7+ continues at **+10 per level**, costs scale at **×1.4 per level** from 500,000.

**Click Power**
- Levels 1–5 match the old tier costs and multipliers exactly (x2 → x6).
- Level 6+ continues at **+1 per level**, costs scale at **×1.5 per level** from 10,000.
- Click multiplier applies to both manual fish clicks **and** all Frenzy tiers.

> Existing users are automatically migrated — no power is lost. Your highest owned tier becomes your starting level.

Shop items now display current level and multiplier: **Lv3 · x8 → x16**.

---

## 22 Mar 2026

### Frenzy Scales with Click Power
- Passive click Frenzy ticks are now multiplied by your Click Power tier.
- Example: Frenzy I + Click Power level 2 (Triple Click) = **2 passive clicks per 5s** instead of 1.
- Applies to all Frenzy tiers including Final Frenzy.
- Shop descriptions updated to reflect scaling.

### Rate Limiter Fixed for Shared Networks
- The API rate limiter now tracks limits **per user account** instead of per IP address.
- Previously, all users on the same network shared one rate limit bucket — one user hitting the limit would cause 429 errors for everyone else.
- Unauthenticated requests still fall back to IP-based limiting.

### Fish-Click API Capped at 10 Per Request
- The `/api/fish-click` endpoint now accepts a maximum of **10 clicks per request**.
- Prevents exploits that manually send inflated click counts (e.g. `count=1000`).

---

## 21 Mar 2026

### Final Frenzy is Now Toggleable
- Final Frenzy now works as a toggle (like cosmetics) rather than a permanent owned state.
- **Active**: 500 auto-clicks every 5s, manual fish clicking disabled.
- **Inactive**: falls back to Frenzy V behaviour (100 clicks/5s), manual clicking re-enabled.
- Toggle in the shop using the Active/Equip button.

### Performance & Low-Spec Mode
- Added **Low-Spec Mode** toggle (⚡ button in the top bar, saved to localStorage):
  - Disables all infinite CSS animations.
  - Removes GPU-heavy drop-shadow filters, fish aura, wheel glow, and ambient border pulse.
  - Blocks confetti particles.
- Automatic respect for the OS **prefers-reduced-motion** setting.
- Fish aura blur capped at 120px (was 600px).
- Thunder aura animation slowed from 0.3s → 0.8s (was causing excessive repaints).
- Added `will-change` hints to wheel canvas and bulbs.
- Confetti auto-clears after 3.5s so DOM elements don't persist.

### Bug Fixes
- **Shop snap-back**: items bought between spins (e.g. buying a guard mid-result) are no longer wiped when the spin result is applied.
- **Streak counter animation**: fixed a bug where the streak animation replayed on every increment, making updates appear invisible.
- **Shield indicator**: repositioned above the streak panel so it no longer jumps when the streak panel appears/disappears.

---

### New Upgrade: Final Frenzy
- Costs **100,000 clicks**, requires Frenzy V.
- Grants **500 auto-clicks every 5 seconds**.
- Disables manual fish clicking while active.

---

## 20 Mar 2026

### Shop: Special Upgrade Popups & Stacking Display
- Special upgrades (Fortune Charm, Lucky Seven, Win Echo, Jackpot, Resilience) now show a popup notification when they trigger during a spin.
- Shop now collapses owned upgrade tiers — only the most recent tier and the next available tier are shown, keeping the list clean.
- Loss streak tracking added to the database (`loss_count` column) for future use.

### Staging Environment & Deploy Tooling
- New staging environment at port 5001 (`wheeldb_staging` database, `staging` git branch).
- Database migration system: numbered SQL files in `migrations/`, run with `python3 migrate.py`.
- `deploy.sh` script to merge staging → master, run migrations, rebuild JSX, and reload gunicorn.
- `--yes` flag added to `deploy.sh` for unattended/automated deploys.

### Major Gameplay Expansion
New upgrades and cosmetics added:

**Functional Upgrades**
- **Fortune Charm** (500) — 25% chance to boost streak bonus payouts by 25%.
- **Lucky Seven** (1,000) — every 7th spin is guaranteed a win.
- **Win Echo** (750) — 20% chance to double wins earned on any win.
- **Resilience** (500,000) — 50% chance that a loss on a win streak only drops the streak by 1 instead of resetting it.
- **Jackpot** (3,000) — 1% chance per win to multiply gains by 50×.

**New Cosmetics**
- Fish size upgrades: Big Fish, Giant Fish, Colossal (scales the fish sprite).
- Fish trail effects: Sparkle, Fire, Rainbow, Frost, Thunder, Galaxy.
- Wheel themes: Fire, Ice, Neon, Void, Gold.
- Background atmospheres: Ocean, Royal, Inferno, Enchanted Forest, The Abyss, Cosmic Casino.
- Page theme: Season 1 (classic gold & orange).
- Golden Wheel glow ring.
- Confetti upgrades: Confetti+, Confetti++, Confetti MAX.
- Party Mode: confetti on every spin.

**Legendary**
- **The Singularity** (1,000,000,000) — every spin is a win.

### Wins Column: Arbitrary Precision
- `wins` column migrated from `BIGINT` to `NUMERIC` — supports arbitrarily large win totals.
- Removed the previous 100 billion win bonus cap.

---

## 19 Mar 2026

### Major Refactor & UI Overhaul
- Backend split into modules: `game.py`, `models.py`, `db.py`, `seasons.py`, `security.py`.
- Full roulette-style green/red colour theme.
- Shop split into **Cosmetics** and **Upgrades** tabs.
- Leaderboard bar pinned to the bottom of the screen.
- Layout and spacing improvements across all screen sizes.

### Seasons System
- Season 1 launched. Seasons track per-user win/loss history and freeze a top-5 leaderboard snapshot at the end of each season.
- Season info shown in the UI; season transitions announce in a toast.

### Click Frenzy Upgrades (Frenzy I–V)
Passive auto-click upgrades, each triggered every 5 seconds:
- **Frenzy I** (150) — +1 click/5s
- **Frenzy II** (600) — +5 clicks/5s
- **Frenzy III** (2,400) — +20 clicks/5s
- **Frenzy IV** (9,600) — +50 clicks/5s
- **Frenzy V** (38,400) — +100 clicks/5s

### Spin Speed Upgrades
- **Speed Boost** (50) — 4.5s → 3s
- **Turbo Spin** (200) — 3s → 1.5s
- **Hyper Spin** (600) — 1.5s → 1s
- **Ultra Spin** (2,000) — 1s → 0.75s
- **Max Spin** (6,000) — 0.75s → 0.5s

### Auto-Speed Upgrades
- **Quick Auto** (75) — auto-spin delay 1.5s → 1s
- **Rapid Auto** (300) — 1s → 0.5s
- **Instant Auto** (1,200) — 0.5s → 0 (no delay)

### Click Power Upgrades
- **Double Click** through **Hexa Click** — multiplies fish clicks per tap from ×2 up to ×6.

### Guard
- **Guard** (300) — 50% chance to block any loss. Breaks on a successful block, survives on failure.
- **Regenerating Shield** (800) — blocks any loss when charged; recharges after 5 wins, never breaks.
- Animated shield feedback shown in the result banner when a shield activates or breaks.

### Authentication & Accounts
- Full account system: register/login with username and password.
- Single active session enforced — logging in elsewhere signs out your previous session.
- Device-ID cookie tracking (1-year cookie) instead of IP-based account limits.
- Rate-limited login attempts with escalating lockouts: 5 fails → 1 min, 10 fails → 5 min, 20 fails → 1 hour.
- Username comparison is case-insensitive.
- Fixed mobile login autocapitalisation.

### Leaderboard
- Top 5 players by wins shown in a pinned bottom bar.
- Auto-refreshes every 60 seconds.

### Mobile & Layout
- Fully responsive layout scaling across all screen sizes.
- Fixed auto-spin not triggering on the first spin when checking the auto-spin box.

### Bug Fixes
- Fixed exponential loss streak bug that caused losses to compound incorrectly at high streak counts.
- Fixed auto-spin stalling after a spin completed.
- Fixed Iron Shield going to negative charges.
- Fixed shield-charge refresh exploit.
- Large numbers (wins, clicks) are now abbreviated (e.g. 1.2M, 4.5B).
- Slot machine emoji favicon added.

---

## Initial Release — 19 Mar 2026

- Casino spin wheel with **Win** / **Lose** outcomes (50/50).
- Fish mascot with idle, happy, and sad states.
- Click the fish to earn fish clicks (in-game currency).
- Win/loss streak tracking with escalating streak bonuses from win streak 3+.
- Bonus Power upgrades multiply streak bonus payouts (and loss streak penalties).
- Auto-spin toggle.
- Shop with fish skin cosmetics (Tropical, Puffer, Octopus, Shark, Dolphin, Squid, Turtle, Crab, Lobster, Whale).
- PostgreSQL backend with server-side game logic.
