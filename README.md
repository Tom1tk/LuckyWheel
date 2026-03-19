# Lucky Wheel 🎰

A casino-style spinning wheel game with a fish mascot, streaks, and a full upgrade shop — running on a Python/Flask backend with PostgreSQL persistence and user authentication.

## Overview

Lucky Wheel is a browser-based gambling wheel built with a Python/Flask backend and a React frontend loaded entirely from CDN (no build step required). Spin the wheel, rack up wins, collect fish clicks, and spend them in the shop on cosmetic upgrades and gameplay boosts.

All game state is stored server-side in PostgreSQL — progress persists across devices and sessions, and client-side cheating is prevented.

## Features

### Core Gameplay
- **Spinning wheel** — WIN or LOSE, styled as a neon casino wheel with smooth CSS rotation
- **Win/loss counter** — persisted in PostgreSQL across sessions and devices
- **Win-streak multiplier** — 3+ consecutive wins or losses triggers an exponentially scaling bonus (2× per additional streak step)
- **Streak panel** — appears on the right side only when a streak is active (fire emoji for wins, skull for losses)
- **Streak persistence** — streak is saved server-side (refresh-to-reset exploit patched)

### Authentication
- Register with a username (3–32 alphanumeric) and password (6+ chars)
- One account per device (enforced via a long-lived `device_id` cookie; multiple users on the same IP are fine)
- Strict single-session enforcement — logging in on a new device boots the previous session
- 30-day persistent login sessions (signed HTTP-only cookies)
- Brute-force protection: escalating lockouts after 5/10/20 failed attempts per username (1min/5min/1hr)
- All login and registration attempts are logged with IP, normalised username, User-Agent, and rejection reason

### Fish Mascot
- A fish lives on the left side of the screen, centred vertically
- Reacts to spin results (happy on win, sad on loss, idle otherwise)
- Shows a fire aura when wins are ahead, a gloom aura when losses are ahead — aura size scales with the gap
- Clickable — spins on click, each click earns fish-click currency (server-side)
- **Fish clicks are your shop currency** — accumulates and persists across sessions

### Auto-Spin
- Checkbox to enable automatic spinning on a configurable delay
- While active, manual spinning is locked out to prevent stacking

---

## Shop System

Fish clicks are spent in the shop (🛒 button, top-right). All purchases persist server-side. **Locked tiers are hidden until the prerequisite is owned** — shop items unlock progressively.

### Fish Skins
| Skin | Cost | Emoji |
|------|------|-------|
| Tropical Fish | 25 | 🐠 |
| Pufferfish | 50 | 🐡 |
| Octopus | 75 | 🐙 |
| Shark | 100 | 🦈 |
| Dolphin | 150 | 🐬 |

Each skin has custom idle/win/loss speech. Buy and equip to change the fish.

### Spinner Speed
| Upgrade | Cost | Spin Duration |
|---------|------|---------------|
| Speed Boost | 50 | 4.5s → 3s |
| Turbo Spin | 200 | 3s → 1.5s |

### Auto Speed
| Upgrade | Cost | Auto-Spin Delay |
|---------|------|-----------------|
| Quick Auto | 75 | 1500ms → 1000ms |
| Rapid Auto | 300 | 1000ms → 500ms |
| Instant Auto | 1200 | 500ms → 0ms |

### Win Multiplier
Multiplies each win's score contribution.
| Tier | Cost | Multiplier |
|------|------|-----------|
| Win ×2 | 200 | ×2 |
| Win ×4 | 800 | ×4 |
| Win ×8 | 3200 | ×8 |
| Win ×16 | 12800 | ×16 |

### Bonus Multiplier
Multiplies streak bonus payouts.
| Tier | Cost | Multiplier |
|------|------|-----------|
| Bonus Boost | 300 | ×2 |
| Bonus Mega | 1200 | ×5 |
| Bonus ULTRA | 4800 | ×10 |

### Fish Size
| Tier | Cost | Fish Size |
|------|------|-----------|
| Big Fish | 50 | 20rem |
| Giant Fish | 200 | 28rem |
| Colossal | 800 | 40rem |

### Fish Trail
Visual trail effect on the fish.
| Tier | Cost | Effect |
|------|------|--------|
| Sparkle Trail | 125 | ✨ Sparkle |
| Fire Trail | 500 | 🔥 Fire |
| Rainbow Trail | 2000 | 🌈 Rainbow |

### Click Power & Click Frenzy
| Upgrade | Cost | Effect |
|---------|------|--------|
| Double Click | 100 | Each fish click counts as 2 |
| Frenzy I | 150 | +1 click per 5s (passive) |
| Frenzy II | 600 | +5 clicks per 5s |
| Frenzy III | 2400 | +20 clicks per 5s |

### Streak Shield
Shields protect your win streak by absorbing a loss. All three can be owned simultaneously and are consumed in priority order: **Shield → Reinforced → Regenerating**.

| Item | Cost | Behaviour |
|------|------|-----------|
| 🛡️ Shield | 150 | Blocks 1 loss, then breaks. Must be repurchased. |
| ⚔️ Reinforced Shield | 600 | Blocks 3 losses, then breaks. Must be repurchased. |
| 🔄 Regenerating Shield | 800 | Blocks 1 loss, recharges after 3 wins, loops forever. Never permanently breaks. |

- Shields only activate while you are on a **win streak** — they prevent it from being broken.
- No prerequisite between shields — all three are independently purchasable at any time.
- Refreshing the page does **not** restore charges (exploit patched).

### Wheel Theme
Changes the canvas colour palette of the wheel.
| Theme | Cost | Look |
|-------|------|------|
| Fire Theme | 250 | 🔥 Red/orange |
| Ice Theme | 1000 | ❄️ Blue/cyan |
| Neon Theme | 4000 | 💜 Purple/neon |
| Golden Wheel | 300 | ✨ Radiant glow ring |

### Atmosphere
#### Confetti
| Tier | Cost | Count |
|------|------|-------|
| Confetti+ | 75 | ×2 |
| Confetti++ | 300 | ×5 |
| Confetti MAX | 1200 | ×15 |
| Party Mode | 150 | Confetti on every result |

#### Background Theme
| Theme | Cost | Look |
|-------|------|------|
| Ocean Casino | 100 | Deep sea blue |
| Royal Casino | 400 | Rich purple |
| Inferno Casino | 1600 | Blazing red |

### 🌌 Legendary
| Item | Cost | Effect |
|------|------|--------|
| The Singularity | 1,000,000,000 | Transcend reality. Every spin is a win. |

---

## Running Locally

### Requirements
- Python 3.8+
- PostgreSQL 14+

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up PostgreSQL

```bash
# Create DB user and database
sudo -u postgres psql -c "CREATE USER wheelapp WITH PASSWORD '<your-password>';"
sudo -u postgres psql -c "CREATE DATABASE wheeldb OWNER wheelapp;"

# Apply schema
PGPASSWORD='<your-password>' psql -U wheelapp -d wheeldb -h localhost -f schema.sql
```

### 3. Configure environment (optional)

```bash
export DATABASE_URL="postgresql://wheelapp:<your-password>@localhost/wheeldb"
export WHEEL_SECRET_KEY="<random-hex-string>"
```

If not set, the app uses hardcoded defaults from `server.py`.

### 4. Start the server

```bash
cd wheel-app
python server.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser. You'll be prompted to register or log in.

---

## Project Structure

```
wheel-app/
├── server.py          # Flask backend — auth, game logic, all API endpoints
├── schema.sql         # PostgreSQL schema (users, game_state, login_attempts)
├── requirements.txt   # Python dependencies
└── static/
    └── index.html     # Entire frontend (React via CDN, Babel standalone)
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
| `/api/state` | GET | — | Full game state |
| `/api/spin` | POST | 10/sec | Server determines outcome, updates DB |
| `/api/buy` | POST | — | Purchase shop item |
| `/api/equip` | POST | — | Equip a fish skin |
| `/api/fish-click` | POST | 30/sec | Increment fish clicks |
| `/api/click-frenzy` | POST | — | Passive click income tick |
| `/api/leaderboard` | GET | — | Public — top 5 players by wins |

`/api/spin` response:
```json
{
  "result": "win",
  "angle": 2345.6,
  "wins": 10,
  "losses": 3,
  "streak": 4,
  "owned_items": ["shield_1"],
  "shield_charges": 2,
  "regen_recharge_wins": 0,
  "shield_used": false,
  "shield_broke": false,
  "bonus_earned": 4
}
```

`/api/leaderboard` (public, no auth required):
```json
[
  { "username": "alice", "wins": 42, "losses": 18 },
  ...
]
```
Returns top 5 players by win count. Auto-refreshed client-side every 60 seconds.

---

## Frontend Architecture

The entire frontend lives in `static/index.html` as a single-file React app. Key components:

| Component | Purpose |
|-----------|---------|
| `App` | Root: checks `/api/me`, renders `AuthPage` or `GameApp` |
| `AuthPage` | Login/register form with error handling |
| `GameApp` | Main game: wheel, fish, scoreboard, shop, all API calls |
| `Fish` | Left-side mascot with aura, mood, and click animation |
| `StreakPanel` | Right-side streak display (only shown at streak ≥ 2) |
| `ShopPanel` | Full shop — locked tiers hidden until prerequisite owned |
| `ShopItem` | Individual item card (buy / equip / active states) |
| `Confetti` | Win confetti overlay |
| `Leaderboard` | Fixed bottom-right panel — top 5 players by wins, auto-refreshes every 60s |
| `drawWheel` | Canvas rendering with theme support (default / fire / ice / neon) |

**No localStorage** — all state lives in PostgreSQL. Legacy `localStorage` keys are cleared on mount.

---

## Tech Stack

- **Backend**: Python, Flask, flask-login, flask-limiter, bcrypt
- **Database**: PostgreSQL (psycopg2)
- **Frontend**: React 18 (CDN), Babel Standalone, vanilla CSS
- **Auth**: Server-side sessions via signed HTTP-only cookies (SameSite=Lax)
