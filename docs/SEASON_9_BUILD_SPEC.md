# Lucky Wheel — Season 9 Build Spec ("Arcade")

Build spec for Season 9. Backend: `wheel-app-staging`. The live Season 8 data
analysis that motivates this spec is in SEASON_9_PLANNING.md.

Theme name: **Arcade** — neon synthwave. Tagline: *"Insert coin. One more spin."*

---

## 1. Content

### 1.1 Page theme `page_season9` — "Arcade" 🕹️
- New page theme (cost 1,000, like other season themes).
- Grants the **Arcade background** (a canvas scene, mirroring the Casino
  background pattern from S8).
- Auto-granted to all players on the S9 rollover (like `page_season8` was);
  new registrations receive it.
- Precedence: `page_season9` supersedes `page_season8` in
  wheel-theme / page-theme / background memos.

### 1.2 Wheel themes (cost ladder mirrors S8 theme chain)
| Item            | Cost  | Requires     | Palette               |
|-----------------|-------|--------------|-----------------------|
| `theme_arcade`  | 250   | —            | neon magenta / cyan   |
| `theme_pixel`   | 1,000 | theme_arcade | 8-bit green / white   |
| `theme_holo`    | 4,000 | theme_pixel  | iridescent purple     |

### 1.3 Fish skins (top of the skin ladder)
| Item            | Cost    |
|-----------------|---------|
| `fish_joystick` | 3,000,000 |
| `fish_pixel`    | 4,500,000 |
| `fish_ghost`    | 6,000,000 |

### 1.4 Dragonfish 🐲 (new legendary catch)
- Catalog entry: value 150, weight 0.15, tier Legendary.
- Never catchable by auto-fish (added to `_AUTO_FISH_LEGENDARY`).

---

## 2. Gameplay

### 2.1 Zealot wheel mode
- `win 50 / lose 42 / jackpot 8`, `jackpot_multiplier 100`.
- Rotating modes become `['inverted', 'gravity', 'mirror', 'long_shot',
  'zealot']`, indexed by `week_number % 5`.
- **This makes `mirror` reachable** (it was defined but never in rotation —
  its bounty was unclaimable). This is a bug fix, not just a feature.
- New bounty `bounty_zealot`: "Land 2 zealot jackpots"
  (metric `zealot_jackpots_today`, target 2).

### 2.2 Prestige titles
- Ladder from level 0 ("Novice") to level 20 ("Legend").
- `get_prestige_title(level)` in prestige.py; surfaced in `/api/state`
  (`prestige_title`), `/api/leaderboard` (per-player `title`), the Prestige
  panel badge, and the prestige chat message.

---

## 3. Economy fixes (the Season 9 core)

### 3.1 Vault payout cap
- When `wins >= 1,000,000` before a spin, a winning spin's `wins_delta` is
  capped at `max(1,000,000, wins * 2)`.
- **Overflow is not lost** — it is moved to `wager_banked_wins` (the "Vault")
  and claimed via the existing Bank button. The Bank button becomes visible
  whenever `wager_banked_wins > 0` (previously required owning
  `wager_hot_streak`).
- Spin response gains `vaulted` (amount moved to the vault), surfaced as a
  toast.
- Applied inside `_resolve_spin` so both `/api/spin` and `/api/tick` inherit it.

### 3.2 Stake decay (wealth-adaptive max stake)
- `compute_max_stake_pct(owned_items, wins=0)` reduces max stake as the
  player's balance grows:
  | Wins        | Max-stake adjustment |
  |-------------|----------------------|
  | < 1M        | base (30 + 5/ext)    |
  | 1M – 10M    | −5                   |
  | 10M – 100M  | −10                  |
  | 100M – 1B   | −15                  |
  | ≥ 1B        | −20 (floor 10)       |
- `_resolve_spin` passes current `wins`; `/api/state`, the wheel-mode endpoint
  and the WagerPanel slider read the same decayed value so the UI stays in sync.

### 3.3 Singularity retune
- Target `100,000,000` → `5,000,000` (migration 074 updates the meter row;
  game.py fallback updated to match).
- Per-player cap `25,000,000` → `2,000,000` (models.py) — 2–3 active players
  can fill a cycle; one player cannot solo it.

### 3.4 Community-goal retune
| Goal        | Target old → new | Cap old → new |
|-------------|------------------|---------------|
| fish        | 5,000 → 1,500    | 500 → 300     |
| jackpot     | 500 → 100        | 50 → 15       |
| prestige    | 50 → 20          | 10 → 5        |
| wager       | 100,000 → 25,000 | 15,000 → 5,000 |
| species     | 100 → 100        | 15 → 15 (kept) |
- Migration 075 updates existing `community_goals` rows to the new targets.

### 3.5 Community pot
- Rollover target `40,000` → `5,000` (still a 5-player-scale sink).

---

## 4. Rollover

- `advance_season`:
  - `new_theme = 'page_season9'` (was hardcoded `page_season8`).
  - `name = 'Arcade'` (was hardcoded `'Casino'`).
  - pot target `5000`.
- `/api/admin/advance-season` accepts optional JSON `{ "pfn": 9, "name": "Arcade" }`
  so the staging rollover can set player-facing 9 explicitly.
- `auth.py` register grants `page_season9`; `loadout.py` classifies it as a
  page theme.

---

## 5. Migrations

| # | File | Purpose |
|---|------|---------|
| 073 | `073_season9_theme.sql` | grant + equip `page_season9` to all users |
| 074 | `074_singularity_retune.sql` | singularity meter target 100M → 5M |
| 075 | `075_community_goals_retune.sql` | update existing goal rows to new targets |

---

## 6. Frontend

- `THEME_COLORS`: + `arcade`, `pixel`, `holo`.
- `WHEEL_MODE_DRAW` / `WHEEL_MODE_INFO`: + `zealot`.
- `ArcadeBackground` component (mirror `CasinoBackground`) + render gate.
- `wheelTheme` / `bgClass`-style / `pageThemeClass` memos: + S9 entries, with
  `page_season9` above `page_season8`.
- `FISH_SKINS`: + 3 skins. `SHOP_SECTIONS`: + "🕹️ Season 9: Arcade" section.
- `COSMETIC_IDS` / `COSMETIC_SECTION_IDS`: + new item ids.
- Bank button: show whenever `wagerBankedWins > 0 && !doubleDownPending`.
- Prestige panel + leaderboard: display title.
- `styles.css`: `body.page-season9` block (palette vars, title glow, score
  overrides, `.arcade-title`); arcade fallback gradient.
- `static/js/arcade-bg.js` (new canvas scene, `window.createArcadeScene`);
  loaded from `static/index.html`.

---

## 7. Tests

New:
- `test_zealot_mode.py` — mode def, rotation layout, reachability.
- `test_prestige_titles.py` — title ladder, clamp, chat message.
- `test_stake_decay.py` — `compute_max_stake_pct` decay table.
- `test_payout_vault.py` — `_resolve_spin` caps wins_delta ≥ 1M and vaults overflow.
- `test_season9_theme.py` — models/SHOP/FISH_SKINS/migration coverage.
- `test_dragonfish.py` — catalog + auto-fish exclusion.
- `test_singularity_retune.py` / `test_community_goal_retune.py`.

Updated:
- `test_long_shot_mode.py` — rotation is now 5 modes.
- `test_chat_triggers.py` — `prestige_msg` (title) and `new_player_msg`
  ("Season 9").

---

## 8. Docs / ops

- Docs: `SEASON_9_*` (planning/build-spec/tickets/progress), PATCH_NOTES "Season 9
  — Arcade" section (after S8), README Season 9 updates.
- Apply migrations to `wheeldb_staging`; restart `wheel-app-staging`; verify
  `/api/state` on :5001; rollover staging (pfn 9, name Arcade); commit.
