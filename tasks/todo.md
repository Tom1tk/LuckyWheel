# Staging Branch & Server Setup

## Tasks

- [x] Read existing files (server.py, gunicorn.conf.py, schema.sql, Makefile)
- [ ] Create .gitignore
- [ ] Modify gunicorn.conf.py — PORT from env
- [ ] Modify server.py — PORT from env for dev server
- [ ] Create migrations/000_baseline.sql
- [ ] Create migrate.py
- [ ] Modify Makefile — add staging targets
- [ ] Create deploy.sh
- [ ] Create wheeldb_staging database
- [ ] Seed staging DB with schema.sql
- [ ] Git: commit current changes, create staging branch, add worktree
- [ ] Create /home/user/wheel-app-staging/.env
- [ ] Verify: staging server runs on 5001
- [ ] Verify: git worktree list shows both

## Review
TBD

---

# Season 8 — Known Issues & Backlog

## Bounty System (Incomplete Implementation)

Investigated 2026-06-19. The bounty UI and DB infrastructure (`bounty_progress` table, `bounties.py`) are in place, but the tracking and claim flow have multiple gaps.

### BUG-B01 — `bounty_fish10` never incremented
- **File:** `game.py` → `/api/reel` endpoint (~line 1792)
- **Issue:** The reel (fish catch) endpoint has no `increment_bounty` call. The "Catch 10 fish" bounty progress will never advance regardless of how many fish are caught.
- **Fix needed:** After a successful catch, call `increment_bounty(conn, current_user.id, 'bounty_fish10', bounty_date)` inside the reel endpoint (mirroring the pattern used in the spin endpoint at lines 788–794).

### BUG-B02 — `get_claim_rewards` signature mismatch (claim endpoint crashes)
- **File:** `game.py:2600` vs `bounties.py:164`
- **Issue:** `game.py` calls `get_claim_rewards(conn, current_user.id, bounty_id, bounty_date)` (4 args), but `bounties.py` defines `def get_claim_rewards(completed_count)` (1 arg). Any attempt to claim a bounty throws a `TypeError`. Additionally, the return value is a `(tokens, fragments)` tuple but the endpoint reads it as a dict (`.get('cosmetic_fragments')`).
- **Fix needed:** Rewrite `get_claim_rewards` to accept the right args (or fix the call site), and align the return type with how the endpoint consumes it.

### BUG-B03 — Five bounty types have no tracking wired up
- **File:** `game.py`
- **Issue:** Only `bounty_jackpot`, `bounty_wager5`, and `bounty_streak10` call `increment_bounty`. The following five have definitions but are never incremented:
  - `bounty_prestige` — prestige endpoint needs a hook
  - `bounty_mirror` — mirror-mode win path in spin endpoint needs a hook
  - `bounty_bank` — wager bank action needs a hook
  - `bounty_double` — double-down win path needs a hook
  - `bounty_fish10` — see BUG-B01
- **Fix needed:** Add `increment_bounty` calls at the relevant action sites for each bounty type.
