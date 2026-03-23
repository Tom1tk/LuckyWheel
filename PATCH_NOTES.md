# Patch Notes

---

## Latest — 23 Mar 2026

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
