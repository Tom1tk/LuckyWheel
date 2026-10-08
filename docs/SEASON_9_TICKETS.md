# Lucky Wheel — Season 9 Tickets

Ticket breakdown for Season 9 ("Arcade"). Statuses: `TODO`, `IN PROGRESS`,
`DONE`. Tickets are ordered so that backend → migrations → frontend → tests →
ops each have a clean boundary.

| # | Ticket | Status |
|---|--------|--------|
| T1 | Write S9 planning + build-spec + tickets + progress docs (this set) | DONE |
| T2 | `wheel_modes.py`: add `zealot`; rotation → `['inverted','gravity','mirror','long_shot','zealot']` (week % 5) | DONE |
| T3 | `models.py`: dragonfish catalog entry (+ auto-fish exclusion); 3 fish skins; 3 wheel themes + `page_season9`; `SINGULARITY_PER_PLAYER_CAP` 2M | DONE |
| T4 | `wagers.py`: stake decay in `compute_max_stake_pct(owned_items, wins=0)` | DONE |
| T5 | `prestige.py`: `PRESTIGE_TITLES` + `get_prestige_title`; `chat_triggers.py`: title in prestige msg, "Season 9" welcome | DONE |
| T6 | `community_goals.py`: retune targets/caps | DONE |
| T7 | `seasons.py`: `new_theme='page_season9'`, `name='Arcade'`, pot target 5000, pfn/name overrides; `auth.py` grant; `loadout.py` classify | DONE |
| T8 | `game.py`: vault payout cap in `_resolve_spin` + `vaulted` event; stake-decay wins wiring; `prestige_title` in state + leaderboard; zealot bounty hook; admin pfn/name; singularity fallback target | DONE |
| T9 | `bounties.py`: `bounty_zealot` | DONE |
| T10 | Migrations 073 (theme grant), 074 (singularity retune), 075 (goal retune) | DONE |
| T11 | `app.jsx`: THEME_COLORS, WHEEL_MODE_DRAW/INFO, ArcadeBackground + gate, memos, FISH_SKINS, SHOP_SECTIONS, COSMETIC ids, Bank button, titles/leaderboard | DONE |
| T12 | `arcade-bg.js` scene + `index.html` + `styles.css` page-season9 | DONE |
| T13 | New tests + update `test_long_shot_mode.py`, `test_chat_triggers.py` | DONE |
| T14 | Verify: ruff, `make build`, test run against `wheeldb_test` (correct DATABASE_URL) | DONE |
| T15 | Apply migrations to `wheeldb_staging`, restart staging, verify :5001 | DONE |
| T16 | Rollover staging (pfn 9, Arcade), commit on `staging` | IN PROGRESS |
| T217 | Auto-spin restoration: universal `auto_spin_unlock` (auth/seasons/migration 076), `MAX_SPINS_PER_TICK` 100 → 201,600, heartbeat auto-stop 60s → 24h, client resume-on-page-load + stale toast, patch notes | DONE |

## Notes

- T4/T8 stake decay: `compute_max_stake_pct` gains a `wins` keyword arg
  (default 0 → current behaviour for tests and callers that don't pass it).
- T8 vault: cap is `max(1_000_000, wins * 2)` when pre-spin `wins >= 1_000_000`;
  overflow → `wager_banked_wins` (claimable via Bank, button now always shown
  when banked > 0).
- T13 must keep the whole suite green against `wheeldb_test`; the `make test`
  target is known-broken (grep bug) — run with
  `export DATABASE_URL=$(grep ^DATABASE_URL= .env | sed 's/^DATABASE_URL=//' | sed 's|/wheeldb$|/wheeldb_test|')`
  after `make test-db-reset`.
- T217: the S8 resume-prevention behaviour (client auto-stops an active
  server session on page load) is deliberately reversed for S9 — the client
  now resumes so `/api/tick` can catch up on offline spins. `test_auto_spin_
  visibility.py` was updated accordingly (`test_app_jsx_resumes_session_on_
  page_load`, 24h threshold guards, stale test uses a 26h window).
