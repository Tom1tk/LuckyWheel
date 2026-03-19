# FishSpin 🐟

A casino-style spinning wheel game with a fish mascot, streaks, and a full upgrade shop — all running locally in your browser.

## Overview

FishSpin is a browser-based gambling wheel built with a Python/Flask backend and a React frontend loaded entirely from CDN (no build step required). Spin the wheel, rack up wins, collect fish clicks, and spend them in the shop on cosmetic upgrades and gameplay boosts.

## Features

### Core Gameplay
- **Spinning wheel** — WIN or LOSE, styled as a neon casino wheel with smooth CSS rotation
- **Win/loss counter** — persisted in `localStorage` across sessions
- **Win-streak multiplier** — 3+ consecutive wins or losses triggers an exponentially scaling bonus (2× per additional streak step)
- **Streak panel** — appears on the right side only when a streak is active (fire emoji for wins, skull for losses)

### Fish Mascot
- A fish lives on the left side of the screen, centred vertically
- Reacts to spin results (happy on win, sad on loss, idle otherwise)
- Shows a fire aura when wins are ahead, a gloom aura when losses are ahead — aura size scales with the gap
- Clickable — spins on click (spammable, each click resets the animation)
- **Fish clicks are your shop currency** — accumulates and persists across sessions

### Auto-Spin
- Checkbox to enable automatic spinning on a configurable delay
- While active, manual spinning is locked out to prevent stacking

---

## Shop System

Fish clicks are spent in the shop (🛒 button, top-right). All purchases persist.

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
| Auto Speed I | 75 | 1500ms → 1000ms |
| Auto Speed II | 250 | 1000ms → 500ms |
| Auto Speed III | 750 | 500ms → 0ms (instant) |

### Win Multiplier
Multiplies each win's score contribution.
| Tier | Cost | Multiplier |
|------|------|-----------|
| I | 100 | ×2 |
| II | 400 | ×4 |
| III | 1200 | ×8 |
| IV | 4000 | ×16 |

### Bonus Multiplier
Multiplies streak bonus payouts.
| Tier | Cost | Multiplier |
|------|------|-----------|
| I | 150 | ×2 |
| II | 600 | ×5 |
| III | 2000 | ×10 |

### Fish Size
| Tier | Cost | Fish Size |
|------|------|-----------|
| Chonky | 80 | 20rem |
| Massive | 300 | 28rem |
| Kaiju | 1000 | 40rem |

### Fish Trail
Visual trail effect on the fish.
| Tier | Cost | Effect |
|------|------|--------|
| Sparkle Trail | 60 | ✨ Sparkle |
| Fire Trail | 200 | 🔥 Fire |
| Rainbow Trail | 600 | 🌈 Rainbow |

### Click Power & Click Frenzy
Click Power doubles fish clicks per click. Click Frenzy passively generates clicks every 5 seconds.

### Streak Shield
Protects your streak when you lose.
| Tier | Cost | Charges |
|------|------|---------|
| Shield I | 120 | 1 charge |
| Shield II | 500 | 3 charges |
| Shield III | 2000 | ∞ charges |

### Wheel Theme
Changes the canvas colour palette of the wheel.
| Theme | Cost | Look |
|-------|------|------|
| Fire Wheel | 100 | 🔥 Red/orange |
| Ice Wheel | 200 | ❄️ Blue/cyan |
| Neon Wheel | 400 | 💜 Purple/pink neon |

### Atmosphere
#### Confetti Tier
More confetti on wins (and Party Mode on all results).
| Tier | Cost | Count |
|------|------|-------|
| Confetti Tier I | 50 | ×2 |
| Confetti Tier II | 200 | ×5 |
| Confetti Tier III | 750 | ×15 |

#### Background Theme
Changes the full-page background.
| Theme | Cost | Look |
|-------|------|------|
| Ocean | 80 | Deep sea blue |
| Royal | 200 | Rich purple/gold |
| Inferno | 500 | Blazing red/orange |

### Legacy Items (original shop)
| Item | Cost | Effect |
|------|------|--------|
| Golden Wheel | 300 | Gold glow on wheel border |
| Double Click | 100 | Each fish click counts as 2 |
| Party Mode | 150 | Confetti on every result, not just wins |

---

## Running Locally

### Requirements
- Python 3.7+
- Flask (`pip install flask`)

### Start the server

```bash
cd wheel-app
python server.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

No npm, no build step — the frontend is pure HTML/CSS/JS with React loaded from CDN.

---

## Project Structure

```
wheel-app/
├── server.py          # Flask backend — serves static files + /api/spin endpoint
└── static/
    └── index.html     # Entire frontend (React via CDN, Babel standalone)
```

### Backend

`/api/spin` (POST) returns:
```json
{ "result": "win" | "lose", "angle": <float> }
```

The angle is calculated so that after CSS `transform: rotate(Xdeg)`, the wheel visually lands on the correct segment. WIN angles bring a WIN segment under the pointer; LOSE angles bring a LOSE segment.

### Frontend

All game logic, shop state, and UI live in `static/index.html` as a single-file React app. Key components:

| Component | Purpose |
|-----------|---------|
| `App` | Root state: wins, losses, streak, fishClicks, ownedItems, equippedFish |
| `Fish` | Left-side mascot with aura, mood, and click animation |
| `StreakPanel` | Right-side streak display (only shown at streak ≥ 2) |
| `ShopPanel` | Full shop with all categories |
| `ShopItem` | Individual item card (buy / equip / active / locked states) |
| `Confetti` | Win confetti overlay |
| `drawWheel` | Canvas rendering with theme support (default / fire / ice / neon) |

State persisted to `localStorage`: `wins`, `losses`, `fishClicks`, `ownedItems`, `equippedFish`, `shieldCharges`.

---

## Tech Stack

- **Backend**: Python, Flask
- **Frontend**: React 18 (CDN), Babel Standalone, vanilla CSS
- **Storage**: `localStorage` (no database)
