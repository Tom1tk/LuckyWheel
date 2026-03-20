# Lucky Wheel 🎰

A casino-style spinning wheel game with a fish mascot, streaks, and a full upgrade shop — running on a Python/Flask backend with PostgreSQL persistence and user authentication.

## Overview

Lucky Wheel is a browser-based gambling wheel built with a Python/Flask backend and a React frontend. Spin the wheel, rack up wins, collect fish clicks, and spend them in the shop on cosmetic upgrades and gameplay boosts.

All game state is stored server-side in PostgreSQL — progress persists across devices and sessions, and client-side cheating is prevented.

## Features

### Core Gameplay
- **Spinning wheel** — WIN or LOSE, styled as a neon casino wheel with smooth CSS rotation
- **Win/loss counter** — persisted in PostgreSQL across sessions and devices
- **Win-streak multiplier** — 3+ consecutive wins or losses triggers an exponentially scaling bonus (2× per additional streak step)
- **Streak panel** — appears in the left sidebar only when a streak is active (fire emoji for wins, skull for losses)
- **Streak persistence** — streak is saved server-side (refresh-to-reset exploit patched)
- **Stats popup** — 📊 button shows total spins, wins, losses, win rate, lifetime fish taps, and spendable balance

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
- Shows a fire aura when wins are ahead, a gloom aura when losses are ahead — aura size and intensity scale with the net gap (tight drop-shadow glow on the fish + large ambient blur halo behind it)
- Trail effects (sparkle/fire/rainbow/frost/thunder/galaxy) and the aura glow coexist independently
- Clickable — each click earns fish-click currency (server-side), tracked as both a spendable **Balance** and a permanent **Lifetime Taps** counter (never decremented)

### Auto-Spin
- Checkbox to enable automatic spinning on a configurable delay
- While active, manual spinning is locked out to prevent stacking
- The wheel can begin spinning while the previous result banner is still fading out

---

## Shop System

The shop is always visible as a two-column panel on the right side of the screen (cosmetics on the left, functional upgrades on the right). **Locked tiers are hidden until the prerequisite is owned** — items unlock progressively. All purchases persist server-side. Hover over any item description to see the full tooltip.

### Fish Skins
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

Each skin has custom idle/win/loss speech. Buy and equip to change the fish.

### Spin Speed
| Upgrade | Cost | Spin Duration |
|---------|------|---------------|
| Speed Boost | 50 | 4.5s → 3s |
| Turbo Spin | 200 | 3s → 1.5s |
| Hyper Spin | 600 | 1.5s → 1s |
| Ultra Spin | 2,000 | 1s → 0.75s |
| Max Spin | 6,000 | 0.75s → 0.5s |

### Auto Speed
| Upgrade | Cost | Auto-Spin Delay |
|---------|------|-----------------|
| Quick Auto | 75 | 1500ms → 1000ms |
| Rapid Auto | 300 | 1000ms → 500ms |
| Instant Auto | 1,200 | 500ms → 0ms |

### Win Multiplier
Multiplies each win's score contribution.
| Tier | Cost | Multiplier |
|------|------|-----------|
| Win ×2 | 200 | ×2 |
| Win ×4 | 800 | ×4 |
| Win ×8 | 3,200 | ×8 |
| Win ×16 | 12,800 | ×16 |
| Win ×32 | 51,200 | ×32 |
| Win ×64 | 204,800 | ×64 |
| Win ×128 | 819,200 | ×128 |

### Bonus Multiplier
Multiplies streak bonus payouts — for both win streaks **and** loss streaks. ⚠️ Higher tiers also amplify loss streak penalties.
| Tier | Cost | Multiplier |
|------|------|-----------|
| Bonus Boost | 300 | ×2 |
| Bonus Mega | 1,200 | ×5 |
| Bonus ULTRA | 4,800 | ×10 |
| Bonus ×20 | 20,000 | ×20 |
| Bonus ×50 | 80,000 | ×50 |
| Bonus ×100 | 300,000 | ×100 |

### Fish Size
| Tier | Cost | Fish Size |
|------|------|-----------|
| Big Fish | 50 | 20rem |
| Giant Fish | 200 | 28rem |
| Colossal | 800 | 40rem |

### Fish Trail
Visual trail effect on the fish. Trail and streak aura effects coexist independently.
| Tier | Cost | Effect |
|------|------|--------|
| Sparkle Trail | 125 | ✨ Gold shimmer |
| Fire Trail | 500 | 🔥 Flame glow |
| Rainbow Trail | 2,000 | 🌈 Rainbow hue |
| Frost Trail | 7,000 | ❄️ Ice crystal aura |
| Thunder Trail | 22,000 | ⚡ Electric sparks |
| Galaxy Trail | 70,000 | 🌌 Cosmic swirl |

### Click Power
Each fish click counts as more clicks server-side.
| Upgrade | Cost | Effect |
|---------|------|--------|
| Double Click | 100 | ×2 clicks |
| Double Click II | 400 | ×3 clicks |
| Double Click III | 900 | ×4 clicks |
| Double Click IV | 2,000 | ×5 clicks |
| Double Click V | 4,500 | ×6 clicks |

### Click Frenzy
Passive income — server ticks fish clicks automatically.
| Tier | Cost | Effect |
|------|------|--------|
| Frenzy I | 150 | +1 click per 5s |
| Frenzy II | 600 | +5 clicks per 5s |
| Frenzy III | 2,400 | +20 clicks per 5s |
| Frenzy IV | 9,600 | +80 clicks per 5s |
| Frenzy V | 38,400 | +320 clicks per 5s |

### Protection
| Item | Cost | Behaviour |
|------|------|-----------|
| 🛡️ Guard | 300 | 50% chance to block any loss. Breaks on success, survives on failure. |
| 🔄 Regenerating Shield | 800 | Blocks any loss when charged. Recharges after 5 wins. Never breaks. |

- **Guard** — activates on any loss. A mini-wheel spins (50/50). If it lands on the win segment, the loss is fully blocked and the guard is consumed. If it fails, the guard survives and you take the loss as normal.
- **Regenerating Shield** — blocks the next loss with 100% certainty while charged. After triggering, it recharges automatically after 5 consecutive wins.

### Wheel Theme
Changes the canvas colour palette of the wheel.
| Theme | Cost | Look |
|-------|------|------|
| Fire Theme | 250 | 🔥 Red/orange |
| Ice Theme | 1,000 | ❄️ Blue/cyan |
| Neon Theme | 4,000 | 💜 Purple/neon |
| Void Theme | 12,000 | 🌑 Deep void |
| Gold Theme | 40,000 | ✨ Pure gold |
| Golden Wheel | 300 | ✨ Radiant glow ring (independent of theme) |

### Atmosphere

#### Background Theme
| Theme | Cost | Look |
|-------|------|------|
| Ocean Casino | 100 | Deep sea blue |
| Royal Casino | 400 | Rich purple |
| Inferno Casino | 1,600 | Blazing red |
| Forest | 5,000 | 🌲 Lush green |
| Abyss | 15,000 | 🌊 Deep dark ocean |
| Cosmic | 50,000 | 🌌 Space nebula |

#### Confetti
| Tier | Cost | Count |
|------|------|-------|
| Confetti+ | 75 | ×2 |
| Confetti++ | 300 | ×5 |
| Confetti MAX | 1,200 | ×15 |
| Party Mode | 150 | Confetti on every result |

### 🎲 Special Upgrades
| Item | Cost | Effect |
|------|------|--------|
| 🍀 Fortune Charm | 500 | All streak bonuses are increased by 25% |
| 7️⃣ Lucky Seven | 1,000 | Every 7th spin is guaranteed to win |
| 🔊 Win Echo | 750 | 20% chance each win is doubled |
| 💪 Resilience | 400 | When on a win streak, losses reduce streak by 1 instead of resetting it |
| 🎰 Jackpot | 3,000 | 2% chance each spin multiplies all gains by 50× |

### 🌌 Legendary
| Item | Cost | Effect |
|------|------|--------|
| The Singularity | 1,000,000,000 | Transcend reality. Every spin is a win. |

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
│                      #            /api/equip-cosmetic, /api/fish-click,
│                      #            /api/click-frenzy, /api/stats, /api/leaderboard, /api/health
├── db.py              # psycopg2 ThreadedConnectionPool + db_connection() context manager
├── models.py          # User class, FISH_SKINS, SHOP_ITEMS, constants
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
| `/api/state` | GET | — | Full game state |
| `/api/spin` | POST | 10/sec | Server determines outcome, updates DB |
| `/api/buy` | POST | — | Purchase shop item |
| `/api/equip` | POST | — | Equip a fish skin |
| `/api/equip-cosmetic` | POST | — | Toggle a cosmetic item on/off |
| `/api/fish-click` | POST | 30/sec | Increment fish clicks |
| `/api/click-frenzy` | POST | — | Passive click income tick |
| `/api/stats` | GET | — | Personal stats (spins, wins, losses, win rate, fish clicks, lifetime taps) |
| `/api/leaderboard` | GET | — | Public — top 5 players by wins |

`/api/spin` response:
```json
{
  "result": "win",
  "angle": 2345.6,
  "wins": 10,
  "losses": 3,
  "streak": 4,
  "owned_items": ["regen_shield"],
  "shield_charges": 0,
  "regen_recharge_wins": 0,
  "shield_used": false,
  "shield_broke": false,
  "guard_triggered": false,
  "guard_blocked": false,
  "bonus_earned": 4,
  "echo_triggered": false,
  "jackpot_hit": false
}
```

`/api/leaderboard` (public, no auth required):
```json
[
  { "username": "alice", "wins": 42, "losses": 18 },
  ...
]
```
Returns top 5 players by win count. Auto-refreshed client-side every 60 seconds as a scrolling ticker.

---

## Frontend Architecture

The frontend is a pre-compiled React app. Edit `static/app.jsx` and run the Babel build step to update `static/app.js`. Key components:

| Component | Purpose |
|-----------|---------|
| `App` | Root: checks `/api/me`, renders `AuthPage` or `GameApp` |
| `AuthPage` | Login/register form with error handling |
| `GameApp` | Main game: wheel, fish, shop, all API calls |
| `Fish` | Left-side mascot — aura, mood, trail effects, click animation |
| `GuardWheel` | Mini canvas wheel overlay for guard activation (50/50 animation) |
| `StreakPanel` | Sidebar streak display (only shown at streak ≥ 2) |
| `ShopPanel` | Always-visible two-column shop (cosmetics left, functional right) |
| `ShopItem` | Individual item card (buy / equip / active states; full desc on hover) |
| `Scoreboard` | Win/loss counter below the wheel |
| `StatsPanel` | Modal overlay showing personal stats (📊 button) |
| `Confetti` | Win confetti overlay |
| `Leaderboard` | Horizontal scrolling ticker at the bottom of the right panel |
| `drawWheel` | Canvas rendering with theme support (default / fire / ice / neon / void / gold) |
| `drawGuardWheel` | Canvas rendering for the guard mini-wheel (50% green / 50% red) |

**No localStorage** — all state lives in PostgreSQL. Legacy `localStorage` keys are cleared on mount.

---

## Tech Stack

- **Backend**: Python, Flask, flask-login, flask-limiter, bcrypt
- **Database**: PostgreSQL (psycopg2 with `ThreadedConnectionPool`)
- **WSGI**: Gunicorn (gthread workers)
- **Frontend**: React 18 (CDN UMD), pre-compiled JSX via Babel CLI, vanilla CSS
- **Auth**: Server-side sessions via signed HTTP-only cookies (SameSite=Lax)
