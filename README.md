# Lucky Wheel 🎰

A casino-style spinning wheel game with a fish mascot, streaks, and a full upgrade shop — running on a Python/Flask backend with PostgreSQL persistence and user authentication.

📋 **[Patch Notes](https://github.com/Tom1tk/fishspin/wiki/Patch-Notes)**

## Overview

Lucky Wheel is a browser-based gambling wheel built with a Python/Flask backend and a React frontend. Spin the wheel, rack up wins, collect fish clicks, and spend them in the shop on cosmetic upgrades and gameplay boosts.

All game state is stored server-side in PostgreSQL — progress persists across devices and sessions, and client-side cheating is prevented.

## Features

### Core Gameplay
- **Spinning wheel** — WIN or LOSE, styled as a neon casino wheel with smooth CSS rotation
- **Win/loss counter** — persisted in PostgreSQL across sessions and devices
- **Win-streak multiplier** — 3+ consecutive wins or losses triggers a scaling bonus. Exponential (×2 per step) up to streak 15, then buffed cubic and linear growth, with a hard cap at streak 150 (~113,096 raw bonus)
- **Streak panel** — appears in the left sidebar only when a streak is active (fire emoji for wins, skull for losses)
- **Streak persistence** — streak is saved server-side (refresh-to-reset exploit patched)
- **Stats popup** — 📊 button shows total spins, wins, losses, win rate, season fish bucks, fastest catch percentage, and **complete Season History**
- **Community Pot** — All players can contribute Fish Bucks to a global pot. When the target is reached, a **30-minute win rate boost** activates for all players. Each fill permanently stacks +0.5% onto the boost rate (capped at 75%), so every window is stronger than the last. Between fills the game returns to 50/50. After the window expires, the pot resets with a **25%-higher target** (×1.25). Target decays 20% every 12 hours if unfilled.
- **Dice Roll** — A charge-based high-risk mechanic between the wheel and shop. Roll two dice (or three with the Extra Die upgrade) to add the sum (2–18) to your current win streak. Requires a win streak of 3+. Snake eyes halves your streak; a pair of sixes doubles it. With three dice: triple 1s ÷3, triple 6s ×3. Charges recharge every 10 minutes (max 1–4, upgradeable in the shop).

### Wager System
Every spin is a bet. Once unlocked, choose a stake from 1× to 10× before spinning — higher stakes amplify both wins and losses.
- **Stake escrow** — before the spin resolves, a percentage of your current wins (2% × stake) is debited up front and held at risk. Win it back plus your payout; lose it and it's gone for that spin.
- **Hot streak** — consecutive wins at the *same* stake add +5% to payout each, capped at +50% (streak 10). Changing stake resets the streak. The bonus portion banks separately rather than paying out immediately.
- **Bank** — lock in your banked hot-streak winnings into your wins total at any time, resetting the streak. The risk/reward tension: keep pushing for a bigger multiplier, or bank and start fresh.
- **Double Down** — after owning the upgrade, arm your next spin to use 2× your chosen stake (full effect at stake 1–4; clamped at the 10× stake ceiling for stake 5+, same as any other spin).
- **Safety Net** — on a loss at 5×+ stake, recover 25% of the escrowed stake back into wins.
- **Insurance** — arm it before a spin (consumes one of up to 3 charges from each purchase) to cap that spin's loss at your stake amount and get the escrowed stake back, if you lose.

### Wheel Modes
Switch the wheel's odds profile at will. **Steady** and **Volatile** are always available; one additional mode rotates weekly.

| Mode | Win % | Loss % | Jackpot % | Jackpot ×| Notes |
|------|-------|--------|-----------|----------|-------|
| Steady (default) | 70% | 28% | 2% | 25× | Small wins, rare losses |
| Volatile | 45% | 50% | 5% | 50× | High variance, double jackpot payout |
| Inverted *(rotates)* | 60% | 35% | 5% | 25× | |
| Gravity *(rotates)* | 55% | 40% | 5% | 25× | Outcomes drift toward the last result |
| Mirror *(rotates)* | 65% | 30% | 5% | 25× | Two spins resolve; you take the better result |
| Singularity | 75% | 10% | 15% | 50× | Unlocked server-wide once the Singularity Meter fills |

The rotating slot cycles Inverted → Gravity → Mirror by ISO week number. This jackpot chance/multiplier applies to **every** player on every spin regardless of owning the Jackpot upgrade — Jackpot (below) adds a *separate*, additional proc chance on top of ordinary wins.

### Prestige
A flat, capped reset path for players who've maxed Win Power and Bonus Power. Requires the **Prestige Unlock** upgrade (1,000,000 wins) and at least 1,000,000 wins (reduced 10%/level by Prestige Efficiency, to a 500,000 floor) to activate.
- Resets wins, losses, streak, and most functional upgrades; cosmetics, Aquarium progress, and your Prestige level itself are kept.
- Each Prestige level grants a permanent **+2% flat bonus to win value**, up to level 20 (+40%).
- **Prestige Legacy** lets you keep one extra owned functional upgrade per level on reset (max 3).
- Returning players who played in earlier seasons start with a head-start Prestige level based on their historical all-time wins.

### Authentication
- Register with a username (3–32 alphanumeric) and password (6+ chars)
- One account per device (enforced via a long-lived `device_id` cookie; multiple users on the same IP are fine)
- Strict single-session enforcement — logging in on a new device boots the previous session
- 30-day persistent login sessions (signed HTTP-only cookies)
- Brute-force protection: escalating lockouts after 5/10/20 failed attempts per username (1min/5min/1hr)
- All login and registration attempts are logged with IP, normalised username, User-Agent, and rejection reason

### Fish Mascot & Cast & Reel Fishing
- A fish lives on the left side of the screen, centred vertically (desktop); accessible via the 🐟 toolbar button on mobile
- Reacts to spin results (happy on win, sad on loss, idle otherwise)
- Shows a fire aura when wins are ahead, a gloom aura when losses are ahead — aura size and intensity scale with the net gap (tight drop-shadow glow on the fish + large ambient blur halo behind it)
- Trail effects (sparkle/fire/rainbow/frost/thunder/galaxy) and the aura glow coexist independently
- The equipped fish emoji acts as your fisher — holds a rod and stands at the water's edge

**Cast & Reel** (Season 6) — replaces passive fish clicking with an active timing minigame:
- Click **🎣 CAST** to drop your line. Shadow fish drift near the bobber while you wait.
- When the fish bites, a bite bar begins depleting — **click to reel** before it empties.
- Click too early (before the bite indicator) and it's an instant miss.
- Catch one of **13 species** across Common, Uncommon, Rare, and Legendary tiers. Each awards **Fish Bucks** scaled by your Lure level.
- **Lucky Fish (⭐)** — a rare Legendary catch that doubles the value of your next successful reel.
- **Auto-Cast** — re-casts automatically; you still handle the bite window.
- **Auto-Fish** — fully automated; catches Common and Uncommon species (Rare unlocked by Master Auto-Fisher). Never catches Legendary fish.
- **Fish Encyclopaedia** (📖 top-left) — tracks all 13 species. Completing it unlocks Master Lure and Master Auto-Fisher.
- All timing is server-authoritative — the bite window and catch validation cannot be spoofed client-side.

### Auto-Spin
- Checkbox to enable automatic spinning on a configurable delay
- While active, manual spinning is locked out to prevent stacking
- The wheel can begin spinning while the previous result banner is still fading out

### Seasons
- Seasons track per-user win/loss history and freeze a top-5 leaderboard snapshot at end-of-season
- **Season History** — users can view their final wins and finishing positions for all past seasons in the stats popup
- Season info shown in the UI; transitions announced via toast
- The active leaderboard (bottom-left) displays the top 10 players, including their current and all-time best streaks
- **Season 7 is open-ended** — no automatic reset. The "Season ends in" countdown shows **∞?** and seasons are advanced manually.
- **🏆 Hall of Fame** — a separate legacy leaderboard (toolbar button) shows the top-5 snapshot from every past season, independent of the live top-10 board.

### Daily Bounties
Three objectives are selected per player each UTC day (deterministic — the same three all day, reset at midnight UTC), drawn from a pool including catching fish, landing a jackpot, reaching a win streak, banking wager winnings, and more. Completing bounties pays out in **Wager Tokens**, with a bonus **Cosmetic Fragment** for clearing all three in one day. Progress and claiming are in the bounty panel; rewards can only be claimed once per day.

### Community Goals
A weekly server-wide objective — one of five rotating goals (catch fish, land jackpots, prestige, wager wins, or discover unique species), selected by week number. Everyone's progress contributes toward one shared target, with a per-player contribution cap so a single player can't solo it. Completing the goal grants every contributor a week-long +5% win-rate buff plus Wager Tokens and a Cosmetic Fragment. Distinct from (and runs alongside) the Community Pot above.

### Singularity Meter
A second, much larger server-wide effort: all players can voluntarily contribute Fish Bucks toward a shared 100,000,000 target (each player capped at 25,000,000 per fill cycle). When the meter fills, the **Singularity** wheel mode (see Wheel Modes) unlocks for everyone for the rest of the season, and the meter resets to fill again.

### Aquarium
Every unique species you've caught through Cast & Reel is tracked permanently (the same list backing the Fish Encyclopaedia). With the Aquarium upgrade owned, each unique species caught adds +0.1% to your wheel win chance — up to +1.3% with the full 13-species catalogue — a gentle, collection-based bonus that rewards completionists without being mandatory.

### Build Loadouts
Save up to 3 named loadouts (equipped class + active wheel mode) and switch between them in one click — useful for quickly adapting to the weekly mode rotation without re-clicking through menus.

### Chat
A persistent chat channel (bottom-right panel, resizable) where players can talk, alongside automatic system announcements for jackpots, prestige level-ups, bounty completions, and Singularity Meter fills.

### Rising Fire Effect
- A full-viewport canvas fire effect rises behind all game UI, scaling with win streak intensity
- **Mix** mode (default) — embers and a cellular automaton inferno layered with additive blending
- Embers appear from streak 3; inferno ignites from streak 10; screen fills around streak 30
- Intensity lerps smoothly — wins cause the fire to grow, a loss makes it fall gradually rather than cutting out
- Suppressed automatically in Low-Spec Mode and when OS `prefers-reduced-motion` is set

### Mobile Support
- Fully playable on phones and tablets (≤ 768 px breakpoint); desktop layout is completely unchanged
- **Bottom toolbar** — five icon buttons toggle panels: Shop 🏪, Leaderboard 🏆, Fish+Community Pot 🐟, Season Winners 🏅, Stats 📊
- **Slide-in drawers** — the shop/sidebar panel slides in from the right; leaderboard, season winners, and fish panels open as overlays
- **Tap-to-dismiss backdrop** — tapping outside any open panel closes it
- **Community Pot** moved into the fish panel on mobile to avoid crowding the top bar

### Performance
- **Low-Spec Mode** (⚡ button in the top bar) — disables infinite CSS animations, GPU-heavy drop-shadows, confetti, fish aura, and fire effect; respects OS `prefers-reduced-motion`
- Preference is saved per user in the database and synced across devices

### Anti-Cheat
- All game logic runs server-side; clients cannot submit win/loss outcomes, fish catches, or spin results
- Stake escrow, wager state, and Prestige all re-validate ownership/affordability server-side rather than trusting client-supplied amounts
- Replay strings are HMAC-signed so a hand-crafted string can't impersonate a real win
- **Wins are capped at 5,000,000** (`_MAX_WINS`) to keep numbers legible — Prestige is the intended path past the cap
- Rate limiter keys on **user account** rather than IP (prevents shared-network collisions)

---

## Shop System

The shop is always visible as a two-column panel on the right side of the screen (cosmetics on the left, functional upgrades on the right). **Locked tiers are hidden until the prerequisite is owned** — items unlock progressively. All purchases persist server-side. Hover over any item description to see the full tooltip.

### Currencies
- **Wins**: Used for all functional upgrades and gameplay boosts.
- **Losses**: Used for all cosmetic items (skins, trails, themes, backgrounds).
- **Fish Bucks**: Earned through Cast & Reel fishing. Used for the Fish Exchange (convert to Wins) and the Singularity Meter.
- **Wager Tokens** and **Cosmetic Fragments**: Earned from Daily Bounties and Community Goals. Currently accumulate as a balance with no spend yet — a future cosmetic-redemption sink is planned but not live.

### Tier Gating (Season 5)
Functional upgrades are gated behind total win milestones. Locked items appear greyed out with the required win count shown.

| Tier | Unlocks at | Example items |
|------|------------|---------------|
| Tier 1 | Always available | Guard, Win/Bonus Power, Wager Unlock, fishing gear |
| Tier 2 | 1,000 total wins | Regenerating Shield, Guard Charge, Aquarium, Lure Specialization, Precise Angler, Dice Charge II |
| Tier 3 | 5,000 total wins | Fortune Charm, Lucky Seven, Win Echo, Jackpot, Resilience, Class System, Prestige, Wager Double Down/Insurance, Max Dice Charge, Overcharge, Extra Die |

### Fish Skins (Costs Losses)
| Skin | Cost | Emoji |
|------|------|-------|
| Tropical Fish | 25 | 🐠 |
| Pufferfish | 50 | 🐡 |
| Octopus | 75 | 🐙 |
| Shark | 100 | 🦈 |
| Dolphin | 150 | 🐬 |
| Squid | 200 | 🦑 |
| Turtle | 350 | 🐢 |
| Crab | 600 | 🦀 |
| Lobster | 1,000 | 🦞 |
| Whale | 2,000 | 🐳 |
| Seal | 3,500 | 🦭 |
| Shrimp | 6,000 | 🦐 |
| Coral | 10,000 | 🪸 |
| Mermaid | 17,500 | 🧜 |
| Crocodile | 30,000 | 🐊 |
| Rocket | 50,000 | 🚀 |
| Comet | 85,000 | ☄️ |
| Saturn | 145,000 | 🪐 |
| Alien | 250,000 | 👽 |
| UFO | 425,000 | 🛸 |

Each skin has custom idle/win/loss speech. Buy and equip to change the fish.

### Win Power (Costs Wins)
Multiplies each win's score contribution. Caps at level 7 — there is no infinite tail; further win-value scaling beyond this comes from Prestige.

| Level | Cost | Multiplier |
|-------|------|-----------|
| Lv 1–7 | 200 / 600 / 2,000 / 6,400 / 20,000 / 64,000 / 200,000 | ×2 → ×128 |

The shop card shows current level and next multiplier: **Lv3 · ×8 → ×16**.

### Bonus Power (Costs Wins)
Multiplies streak bonus payouts — for both win streaks **and** loss streaks. ⚠️ Higher levels also amplify loss streak penalties. Caps at level 6 — no infinite tail.

| Level | Cost | Multiplier |
|-------|------|-----------|
| Lv 1–6 | 300 / 900 / 2,800 / 8,500 / 26,000 / 80,000 | ×2 → ×70 |

### Fishing Panel Size (Costs 1 Loss — accessibility)
Resizes the Cast & Reel panel. Priced at 1 loss each as an accessibility option, not a progression item.

| Tier | Cost | Panel Size |
|------|------|-----------|
| Compact | 1 | 50% |
| Big Panel | 1 | 130% |
| Giant Panel | 1 | 160% |
| Colossal | 1 | 200% |

### Fish Trail (Costs Losses)
Visual trail effect on the fish. Trail and streak aura effects coexist independently.
| Tier | Cost | Effect |
|------|------|--------|
| Sparkle Trail | 125 | ✨ Gold shimmer |
| Fire Trail | 500 | 🔥 Flame glow |
| Rainbow Trail | 2,000 | 🌈 Rainbow hue |
| Frost Trail | 7,000 | ❄️ Ice crystal aura |
| Thunder Trail | 22,000 | ⚡ Electric sparks |
| Galaxy Trail | 70,000 | 🌌 Cosmic swirl |

### 🎣 Fishing Gear (Costs Wins)

**Lure Upgrades** — reduce bite wait time and multiply catch value. Both manual and Auto-Fish benefit.

| Upgrade | Cost | Bite Speed | Value Multiplier |
|---------|------|-----------|-----------------|
| Lure I | 100 | 10% faster | 1.5× |
| Lure II | 500 | 20% faster | 2× |
| Lure III | 2,500 | 35% faster | 5× |
| Lure IV | 15,000 | 50% faster | 10× |
| ⭐ Master Lure | 500,000 | 65% faster | 20× + +1% per legendary |

Master Lure requires completing the Fish Encyclopaedia (all 13 species caught).

**Auto-Cast** (1,000 wins) — automatically re-casts the line when idle. You still handle the bite window.

**Auto-Fisher** — unlock and improve the Auto-Fish tickbox. Auto-Fish fires every 6s, is rate-limited server-side, and never catches Legendary fish at any level.

| Upgrade | Cost | Catch Rate | Species Pool |
|---------|------|-----------|--------------|
| Auto-Fisher I | 300 | 45% | Common + Uncommon |
| Auto-Fisher II | 2,000 | 55% | Common + Uncommon |
| Auto-Fisher III | 12,000 | 65% | Common + Uncommon |
| 🤖 Master Auto-Fisher | 500,000 | 75% | Common + Uncommon + Rare |

Master Auto-Fisher requires completing the Fish Encyclopaedia.

**Precise Angler** (Tier 2, 1,000 wins) — rewards fast reflexes. Multipliers are exclusive; highest gate hit wins.

| Upgrade | Cost | Threshold | Multiplier |
|---------|------|-----------|-----------|
| Precise Angler | 50,000 | ≤ 50% through bar | 1.2× |
| Precise Angler II | 100,000 | ≤ 20% through bar | 1.5× |
| 🎯 Master Angler | 500,000 | ≤ 15% through bar | 2× |

Master Angler requires completing the Fish Encyclopaedia. Precise Angler multipliers stack with Lure and Lucky Fish multipliers independently.

**Fishing integration** — bridges fishing into the wider economy:

| Item | Cost | Effect |
|------|------|--------|
| Fish-to-Wager | 5,000 | Each catch also awards Wager Tokens, scaled by species rarity (5 for Common up to 100 for Legendary) |
| Catch of the Day | 3,000 | First catch each UTC day awards 5× Wager Tokens |
| Aquarium | 15,000 | Each unique species you've ever caught adds +0.1% wheel win chance (see Aquarium above) |
| Lure Specialization | 10,000 | Requires Fish-to-Wager. Choose a fish family for +50% value, -25% for others |

### Protection (Costs Wins)
| Item | Cost | Behaviour |
|------|------|-----------|
| 🛡️ Guard | 1,000 | Blocks the next loss. Single-use — consumed when it triggers, must be repurchased. |
| 🔄 Regenerating Shield | 5,000 | Blocks the next loss when charged. Recharges automatically after 5 consecutive wins. Never permanently breaks. |
| 💪 Resilience | 20,000 | While on a win streak, a loss has a 50%+ chance (higher with Moon class) to reduce your streak by 1 instead of resetting it, rather than blocking the loss outright. |

### Wheel Theme (Costs Losses)
Changes the canvas colour palette of the wheel. Two independent chains — own and switch between either freely.
| Theme | Cost | Look |
|-------|------|------|
| Fire Theme | 250 | 🔥 Red/orange |
| Ice Theme | 1,000 | ❄️ Blue/cyan |
| Neon Theme | 4,000 | 💜 Purple/neon |
| Void Theme | 12,000 | 🌑 Deep void |
| Gold Theme | 40,000 | ✨ Pure gold |
| Tidal Theme | 250 | 🌊 Cool blue/teal, wave animation |
| Ember Theme | 1,000 | 🔥 Warm orange, spark animation |
| Frost Theme | 4,000 | ❄️ Ice-crystal palette, crack animation |
| Aurora Theme | 12,000 | 🌌 Shifting greens/purples, northern lights |
| Vintage Theme | 40,000 | 📼 Retro sepia tones |
| Golden Wheel | 300 | ✨ Radiant glow ring (independent of theme) |

### Atmosphere (Costs Losses)

#### Background Theme
Ocean Casino is the **default background** for all players in Season 6 (animated seabed scene; static fallback in Low-Spec Mode). Purchasing and equipping a different background overrides it.

| Theme | Cost | Look |
|-------|------|------|
| Ocean Casino | 100 | Deep sea blue (Season 5 default — animated seabed) |
| Royal Casino | 400 | Rich purple |
| Inferno Casino | 1,600 | Blazing red |
| Forest | 5,000 | 🌲 Lush green |
| Abyss | 15,000 | 🌊 Deep dark ocean |
| Cosmic | 50,000 | 🌌 Space nebula |

#### Page Theme
| Theme | Cost | Look |
|-------|------|------|
| Season 1 | 1,000 | Classic gold & orange |
| Season 2 | 1,000 | Green & red |
| Season 3 | 1,000 | Purple & orange |
| Season 4 | 1,000 | Deep violet |
| Season 5 | 1,000 | Bioluminescent cyan & coral |
| Season 6 🌙 | 1,000 | Night ocean — deep indigo & violet |
| Season 7 | 1,000 | Current season default |

#### Confetti
| Tier | Cost | Count |
|------|------|-------|
| Confetti+ | 75 | ×2 |
| Confetti++ | 300 | ×5 |
| Confetti MAX | 1,200 | ×15 |
| Party Mode | 150 | Confetti on every result |

### 🎲 Dice Charges (Costs Wins)
| Item | Cost | Effect | Tier |
|------|------|--------|------|
| Extra Charge | 2,000 | Max dice charges: 1 → 2 | Tier 2 (1k wins) |
| Max Charge | 15,000 | Max dice charges: 2 → 3 | Tier 3 (5k wins) |
| 🎲 Overcharge | 100,000 | Max dice charges: 3 → 4 | Tier 3 (5k wins) |
| 🎲 Extra Die | 1,000,000 | Roll 3 dice. Triple 6s ×3, Triple 1s ÷3 | Tier 3 (5k wins) |

### 🎲 Special Upgrades (Costs Wins)
All Special Upgrades require Tier 3 (5,000 total wins) to unlock. The infinite upgrade axes that used to extend these (Jackpot Resonance, Echo Amplification, Streak Armor, Proc Streak, Lure Mastery) have been retired in favour of flat rates plus Prestige for further scaling — see Prestige above.

| Item | Cost | Effect |
|------|------|--------|
| 🍀 Fortune Charm | 1,000,000 | 25%+ chance (higher with Moon class) that a win's streak bonus is amplified ×1.25 |
| 7️⃣ Lucky Seven | 7,000,000 | Every 7th spin is guaranteed to win |
| 🔊 Win Echo | 1,000,000 | Flat 20%+ chance (higher with Moon class) each ordinary win is doubled |
| 🎰 Jackpot | 3,000,000 | Flat 1%+ chance (higher with Moon class) an ordinary win also triggers a 25× jackpot payout, independent of the wheel mode's own jackpot odds (see Wheel Modes). 5% chance of a Jackpot Echo carrying to the next win. |

### Wager & Prestige Upgrades (Costs Wins)

| Item | Cost | Requires | Effect |
|------|------|----------|--------|
| Wager Unlock | 500 | — | Unlocks the stake slider (1×–10×); without it, stake is locked at 1× |
| Wager Hot Streak | 8,000 | Wager Unlock | Enables the hot-streak payout bonus |
| Wager Safety Net | 2,000 | Wager Unlock | 25% escrow refund on a loss at 5×+ stake |
| Wager Double Down | 25,000 | Wager Hot Streak | Enables the Double Down button |
| Wager Insurance | 50,000 | Wager Unlock | Grants 3 Insurance charges per purchase |
| Prestige Unlock | 1,000,000 | — | Enables the Prestige action |
| Prestige Efficiency | 500,000/level | Prestige Unlock | -10% to the win threshold needed to Prestige, per level (max 5, floor 500,000) |
| Prestige Legacy | 1,000,000/level | Prestige Unlock | Keep 1 extra owned functional upgrade per level on Prestige (max 3) |

### 🌌 Class System (Costs Wins — Tier 3)
Each class costs **10,000,000 Wins**. All three can be owned simultaneously; only one can be equipped at a time. Equipping a new class replaces the previous one. Toggle equip by clicking an already-equipped class.

| Class | Effect |
|-------|--------|
| 🌍 Earth | +25% to all fish income (manual reels and Auto-Fish) |
| 🌙 Moon | +5% added to every proc rate (Jackpot, Win Echo, Fortune Charm, Resilience) |
| ⭐ Star | +20% applied to all win multiplier payouts |

### 🔄 Fish Exchange
Converts Fish Bucks into Wins at a diminishing rate. Available in the shop's functional tab when Fish Bucks > 0. Two buttons: **10%** (10% of current balance) or **ALL** (entire balance).

**Rate**: `1.0 / (1 + total_ever_exchanged / 50,000,000)` — starts at 1:1, halves at 50M lifetime exchanged, continues declining. The live rate is shown before each conversion.

> The old "Singularity" legendary item (1,000,000,000 Fish Bucks, every spin a win) has been retired — it was never reachable. The Singularity is now a server-wide community meter; see Singularity Meter above.

---

## Running Locally

### Requirements
- Python 3.8+
- PostgreSQL 14+
- Node.js (for the one-time JSX build step)

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up PostgreSQL

```bash
# Create DB user and database
sudo -u postgres psql -c "CREATE USER wheelapp WITH PASSWORD '<your-password>';"
sudo -u postgres psql -c "CREATE DATABASE wheeldb OWNER wheelapp;"
```

Then apply the baseline schema and run migrations:

```bash
PGPASSWORD='<your-password>' psql -U wheelapp -d wheeldb -h localhost -f schema.sql
DATABASE_URL="postgresql://wheelapp:<your-password>@localhost/wheeldb" python migrate.py
```

### 3. Configure environment

Both variables are **required** — the server will refuse to start without them.

```bash
export DATABASE_URL="postgresql://wheelapp:<your-password>@localhost/wheeldb"
export WHEEL_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export PORT=5000   # optional, defaults to 5000
```

For convenience, copy `.env.example` to `.env` — `python-dotenv` will load it automatically.

### 4. Build the frontend

The JSX source must be transpiled once (and again after any `app.jsx` changes):

```bash
npx babel static/app.jsx --presets @babel/preset-react,@babel/preset-env -o static/app.js
```

### 5. Start the server

**Production (recommended):**
```bash
gunicorn -c gunicorn.conf.py server:app
```

**Development:**
```bash
python server.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser. You'll be prompted to register or log in.

---

## Staging Environment

A separate staging environment runs on port 5001 against a `wheeldb_staging` database, using a git worktree on the `staging` branch.

```
/home/user/wheel-app/           ← master (production, port 5000, wheeldb)
/home/user/wheel-app-staging/   ← staging (port 5001, wheeldb_staging)
```

**Start staging dev server:**
```bash
cd /home/user/wheel-app-staging && PORT=5001 python server.py
```

**Promote to production:**
```bash
cd /home/user/wheel-app && ./deploy.sh
```

`deploy.sh` merges staging → master, applies pending migrations, rebuilds the frontend, and reloads gunicorn.

---

## Database Migrations

Schema changes are managed with numbered SQL files and a lightweight migration runner.

```bash
python migrate.py              # apply pending migrations
python migrate.py --status     # show applied / pending migrations
python migrate.py --dry-run    # preview without executing
```

Migration files live in `migrations/NNN_description.sql`. Applied versions are tracked in the `schema_migrations` table in each database.

---

## Project Structure

```
wheel-app/
├── server.py          # Thin entry point: create_app() → gunicorn target
├── app.py             # Flask app factory: config, extensions, blueprints, error handlers
├── auth.py            # Blueprint: /api/me, /api/register, /api/login, /api/logout
├── game.py            # Blueprint: /api/state, /api/spin, /api/buy, /api/equip,
│                      #            /api/equip-cosmetic, /api/equip-class, /api/wager/*,
│                      #            /api/wheel-mode(s), /api/prestige, /api/bounties*,
│                      #            /api/community-goal, /api/singularity*, /api/loadout*,
│                      #            /api/aquarium, /api/guard, /api/legacy-boards,
│                      #            /api/stats, /api/leaderboard, /api/health
├── db.py              # psycopg2 ThreadedConnectionPool + db_connection() context manager
├── models.py          # User class, FISH_SKINS, SHOP_ITEMS, INFINITE_UPGRADES, helper functions
├── wagers.py          # Stake validation, hot-streak, escrow risk calculation
├── wheel_modes.py     # Wheel mode definitions + weekly rotation
├── prestige.py        # Prestige bonus/threshold calculation
├── bounties.py        # Daily bounty selection, progress, rewards
├── community_goals.py # Weekly community goal lifecycle
├── replays.py         # Signed replay string encode/decode for big wins
├── chat.py            # Blueprint: /api/chat, system message posting
├── security.py        # check_lockout(), record_attempt(), clear_attempts(), require_json()
├── extensions.py      # Flask-Limiter and Flask-Login instances
├── migrate.py         # SQL migration runner (apply / status / dry-run)
├── deploy.sh          # Production deploy: merge staging → migrate → build → reload
├── gunicorn.conf.py   # Gunicorn config: 4 gthread workers × 4 threads, PORT from env
├── schema.sql         # PostgreSQL baseline schema
├── migrations/        # Numbered SQL migration files (NNN_description.sql)
├── requirements.txt   # Python dependencies
├── .env.example       # Required environment variable template
└── static/
    ├── index.html     # Slim HTML shell
    ├── app.jsx        # React source (edit this)
    ├── app.js         # Compiled output (generated by Babel — do not edit directly)
    └── styles.css     # All CSS
```

---

## API Reference

All game endpoints require authentication (session cookie). POST endpoints require `Content-Type: application/json`.

### Auth
| Endpoint | Method | Rate Limit | Description |
|----------|--------|------------|-------------|
| `/api/me` | GET | — | Returns `{username}` or `{username: null}` |
| `/api/register` | POST | 5/hr | Create account |
| `/api/login` | POST | 10/min | Authenticate |
| `/api/logout` | POST | — | Clear session |

### Game
| Endpoint | Method | Rate Limit | Description |
|----------|--------|------------|-------------|
| `/api/health` | GET | — | DB connectivity check → `{"status":"ok"}` or 503 |
| `/api/state` | GET | — | Full game state (wager, prestige, bounties, community goal, etc.) |
| `/api/spin` | POST | 10/sec | Server determines outcome, updates DB. Body: `{stake, tab_id}` |
| `/api/buy` | POST | — | Purchase shop item |
| `/api/equip` | POST | — | Equip a fish skin |
| `/api/equip-cosmetic` | POST | — | Toggle a cosmetic item on/off |
| `/api/equip-class` | POST | — | Equip or unequip a class item (`{"item_id": "class_earth"}`) |
| `/api/community-pot/state` | GET | — | Current pot progress and target |
| `/api/community-pot/contribute` | POST | 5/sec | Contribute Fish Bucks to the global pot |
| `/api/cast` | POST | 5/sec | Start a fishing session — returns `{bite_at, expires_at}` |
| `/api/reel` | POST | 5/sec | Attempt a reel — server validates timing, returns catch result |
| `/api/auto-fish-tick` | POST | 1/5sec | One automated catch cycle (requires Auto-Fisher I+) |
| `/api/settings` | POST | — | Persist user preferences (e.g. `low_spec_mode`) |
| `/api/stats` | GET | — | Personal stats (including Season History and fastest catch %) |
| `/api/leaderboard` | GET | — | Public — top 10 players |
| `/api/legacy-boards` | GET | — | Public — top-5 snapshot from every past season |
| `/api/fish-exchange` | POST | — | Convert Fish Bucks → Wins (`{"mode": "10pct"}` or `{"mode": "all"}`) |
| `/api/wager/stake` | POST | — | Set preferred stake (1-10; clamped to 1 without Wager Unlock) |
| `/api/wager/bank` | POST | 5/sec | Bank hot-streak winnings into wins, reset the streak |
| `/api/wager/double-down` | POST | 5/sec | Arm the next spin at 2× stake |
| `/api/wager/insurance` | POST | 5/sec | Arm Insurance for the next spin (consumes a charge) |
| `/api/guard` | POST | 5/sec | Manually trigger a guard charge — currently has no effect (see note below) |
| `/api/wheel-modes` | GET | — | Available modes for the current week + your active mode |
| `/api/wheel-mode` | POST | — | Set active wheel mode (`{"mode": "volatile"}`) |
| `/api/prestige` | GET / POST | 5/min | Get prestige status / perform a Prestige reset |
| `/api/bounties` | GET | — | Today's 3 bounties with progress |
| `/api/bounties/claim` | POST | 5/min | Claim rewards for completed bounties (once per day) |
| `/api/community-goal` | GET | — | Active weekly goal, progress, your contribution |
| `/api/singularity` | GET | — | Singularity Meter progress and fill count |
| `/api/singularity/contribute` | POST | 5/sec | Contribute Fish Bucks to the Singularity Meter (`{"amount": int}`) |
| `/api/aquarium` | GET | — | Your caught-species collection and current luck bonus |
| `/api/loadout` | GET / POST | — | List / save a build loadout (slot 1-3, equipped class + wheel mode) |
| `/api/loadout/apply` | POST | — | Apply a saved loadout |
| `/api/chat` | GET / POST | 30/min, 1/sec | Read / post chat messages |
| `/api/replay/share` | POST | — | Decode and validate a replay string (not currently posted to chat — see note below) |

> **Guard and Insurance, note:** `/api/wager/insurance` works as documented (caps the next loss at your stake, refunds the escrow). `/api/guard`, however, currently has no effect on spin outcomes — Guard and Regenerating Shield protection still come from the older passive mechanic (a plain "owned" check, not the `guard_charges` this endpoint spends). This is a known gap, not yet fixed — see `docs/SEASON_8_TICKETS.md`.
>
> **Replay sharing, note:** spins can generate a signed replay string for jackpots, big double-down wins, and max hot-streaks, returned in `/api/spin`'s response. `/api/replay/share` will decode and verify one, but nothing currently posts the result to chat — there's no in-game button for this yet.

`/api/spin` response (abridged — see `_RESPONSE_KEYS` in `game.py` for the full set):
```json
{
  "result": "win",
  "angle": 2345.6,
  "wins_delta": 4,
  "losses_delta": 0,
  "streak": 4,
  "owned_items": ["regen_shield"],
  "active_cosmetics": ["theme_tidal"],
  "stake": 3,
  "wager_streak": 1,
  "wager_banked_wins": 0,
  "active_wheel_mode": "steady",
  "regen_recharge_wins": 0,
  "shield_used": false,
  "shield_used_type": null,
  "guard_triggered": false,
  "guard_blocked": false,
  "insurance_used": false,
  "bonus_earned": 4,
  "echo_triggered": false,
  "jackpot_hit": false,
  "resilience_triggered": false,
  "lucky_seven_triggered": false,
  "fortune_charm_triggered": false,
  "auto_guard_failed": false,
  "proc_streak": 3
}
```

`wins_delta` and `losses_delta` represent the change in currency from this spin (net of any stake escrow). The client adds these to its local state to avoid race conditions.

`/api/leaderboard` (public, no auth required):
```json
[
  { "username": "alice", "wins": 42, "losses": 18, "streak": 5, "best_streak": 12 },
  ...
]
```
Returns top 10 players by win count. Auto-refreshed client-side every 5 seconds.

---

## Frontend Architecture

The frontend is a pre-compiled React app. Edit `static/app.jsx` and run the Babel build step to update `static/app.js`. Key components:

| Component | Purpose |
|-----------|---------|
| `App` | Root: checks `/api/me`, renders `AuthPage` or `GameApp` |
| `AuthPage` | Login/register form with error handling |
| `GameApp` | Main game: wheel, fish, shop, all API calls |
| `Fish` | Left-side mascot — aura, mood, trail effects |
| `FishingPanel` | Cast & Reel minigame — bobber, bite bar, shadow fish, Auto-Cast/Auto-Fish toggles |
| `FishEncyclopedia` | Modal showing all 13 catchable species (silhouettes until discovered) |
| `GuardWheel` | Mini canvas wheel overlay shown when Guard/Regen Shield triggers |
| `StreakPanel` | Sidebar streak display (only shown at streak ≥ 2) |
| `ShopPanel` | Two-column shop (cosmetics left, functional right); collapsible via a pinned `›`/`‹` toggle button |
| `ShopItem` | Individual item card (buy / equip / active states; full desc on hover) |
| `Scoreboard` | Win/loss counter below the wheel |
| `StatsPanel` | Modal overlay showing personal stats (📊 button) |
| `Confetti` | Win confetti overlay |
| `Leaderboard` | Vertical panel (bottom-left) — top 10 players, plus a 🏆 Hall of Fame modal for past-season snapshots |
| `FireEffect` | Full-viewport canvas fire effect behind all UI — ember particles + cellular automaton inferno, scaled by win streak |
| `ChatPanel` | Resizable bottom-right chat panel — player messages + automatic system announcements |
| Onboarding coach-marks | Non-blocking overlay guiding new players through their first spin, wager, catch, and bounty view |
| Wager controls | Stake slider, hot-streak meter, Bank/Double Down/Insurance buttons in the shop's functional column |
| Bounty/Community Goal panels | Progress bars + claim button for daily bounties and the active weekly goal |
| Loadout panel | 3-slot save/equip UI for class + wheel mode combos |
| `drawWheel` | Canvas rendering with theme support (default / fire / ice / neon / void / gold / tidal / ember / frost / aurora / vintage) |
| `drawGuardWheel` | Canvas rendering for the guard mini-wheel |

**Mobile layout** is handled entirely in CSS (`@media (max-width: 768px)`) and a small amount of React state (`isMobile`, `mobilePanel`) in `GameApp`. No separate mobile components — the same components are reused, conditionally positioned via CSS class toggles.

**Minimal localStorage** — game state lives in PostgreSQL, but UI preferences (low-spec mode, parallax toggle, chat panel size/open state, patch-notes-seen dismissal) persist in `localStorage`. Legacy keys from older versions are cleared on mount.

---

## Tech Stack

- **Backend**: Python, Flask, flask-login, flask-limiter, bcrypt
- **Database**: PostgreSQL (psycopg2 with `ThreadedConnectionPool`)
- **WSGI**: Gunicorn (gthread workers)
- **Frontend**: React 18 (CDN UMD), pre-compiled JSX via Babel CLI, vanilla CSS
- **Auth**: Server-side sessions via signed HTTP-only cookies (SameSite=Lax)
