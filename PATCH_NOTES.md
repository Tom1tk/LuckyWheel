# Patch Notes

---

## Latest — 4 Apr 2026

### Season 4 Balancing: Economy Overhaul
- **Price rebalancing across the entire shop.** All upgrade and cosmetic chains have been retuned with steeper cost scaling — late-game items like Max Spin, Instant Auto, Galaxy Trail, and Final Frenzy now cost millions of Wins or Losses, reflecting their power and rarity.
- **Special Upgrades repriced ×100.** Fortune Charm, Lucky Seven, Win Echo, and Jackpot are now 100× their previous cost. Resilience is ×10, now costing 5,000,000 Wins.
- Fish skin costs increased ~10×. Five new premium fish skins have been added (see below).

### New Fish Skins (Season 4)
Five new cosmetic fish have been added at progressively higher costs (paid in Losses):
| Skin | Cost | Emoji |
|------|------|-------|
| Seal | 50,000 | 🦭 |
| Shrimp | 150,000 | 🦐 |
| Coral | 500,000 | 🪸 |
| Mermaid | 1,500,000 | 🧜 |
| Crocodile | 5,000,000 | 🐊 |

### Season 3 Page Theme
- A new **Season 3 Theme** cosmetic is now available in the Page Theme section of the shop (5,000 Losses).
- Applies the purple & orange colour scheme from Season 3 — useful if you're running a different page theme and want to switch back.
- Also fixes a pre-existing bug where the Season 2 page theme could not actually be equipped (it was missing from the server-side cosmetic slot registry).

### Leaderboard: Hide Zero-Win Players
- Players with 0 wins are now hidden from the public leaderboard. Only players who have earned at least one win appear in the top 10.

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
