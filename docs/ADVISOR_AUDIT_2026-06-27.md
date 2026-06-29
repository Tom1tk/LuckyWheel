# Advisor Audit — 2026-06-27 (tickets T231–T240)

> **Purpose:** Shared context for tickets **T231–T240** in
> `SEASON_8_TICKETS.md`. These tickets come from a read-only senior-advisor
> audit of the codebase (not from `SEASON_8_BUILD_SPEC.md`). Where an existing
> ticket says "Spec ref: S17", these say "Advisor ref: §<n> of this doc".
> Each ticket is still self-contained; this doc holds the cross-cutting
> context (codebase anchor, conventions, verification, dependency graph) and
> the one design that is too large to inline (the `game.py` extraction, §7).

> **Codebase / source of truth:** `/home/user/wheel-app` (the **live** code).
> Staging (`/home/user/wheel-app-staging`, DB `wheeldb_staging`) is the
> dev/test branch and is currently **behind** live. All excerpts and line
> numbers in T231–T240 are anchored to **`/home/user/wheel-app` at commit
> `e4c97b4`**. Follow the team's normal flow (develop/test on staging, promote
> to live); if staging line numbers differ, re-locate by **symbol name**, not
> line number, and re-run the drift check below.

> **Status legend (matches the rest of the doc):** `[ ]` not started |
> `[~]` in progress | `[x]` done | `[!]` blocked

---

## §1. Drift check (every ticket — run first)

These tickets were written against `e4c97b4`. Before starting any ticket:

```bash
cd /home/user/wheel-app
git rev-parse --short HEAD          # if not e4c97b4, code may have drifted
git diff --stat e4c97b4..HEAD -- <the ticket's "Files">
```

If an in-scope file changed since `e4c97b4`, compare the ticket's
"Current state" excerpt against the live code before editing. On a mismatch,
treat it as a **STOP** condition for that ticket and report back.

## §2. Verification commands

| Purpose | Command | Expected |
|---------|---------|----------|
| Pure unit tests (no DB) | `python3 -m pytest tests/test_models.py tests/test_format_wins_python.py -q` | all pass |
| Full suite | `python3 -m pytest -q` | see note ↓ |
| Single file | `python3 -m pytest tests/<file>.py -q` | all pass |
| Lint | `ruff check .` | exit 0 |
| Format check | `ruff format --check .` | exit 0 |
| JSX build | `make build` | regenerates `static/app.js`, exit 0 |

**Note on the full suite (this is finding T231):** today `python3 -m pytest`
is **not cleanly green** — `tests/test_auto_spin.py` installs `sys.modules`
stubs at import time (`tests/test_auto_spin.py:40-55`) that leak into the
Playwright `test_mobile_*` files when they are collected in the same process,
producing ~16 spurious errors/failures. The same mobile files pass in
isolation. Until **T231** lands, the trustworthy gate is:

```bash
python3 -m pytest -q -k "not mobile"
```

After T231, plain `python3 -m pytest -q` must be green and is the gate for all
other tickets here.

**DB-backed tests** currently require a reachable Postgres (`wheeldb_staging`)
and read connection details from the test files — see **T234** (move those
credentials to env) and **T232** (`conftest.py`).

## §3. Conventions executors must match

- **DB access:** `with db_connection() as conn:` (from `db.py`), then
  `with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:`.
  The caller commits (`conn.commit()`); the context manager rolls back on
  exception/early-return. Row-locking for read-modify-write uses
  `_load_game_state(cur, user_id, for_update=True)`.
- **All SQL is parameterized** (`%s` placeholders). Never interpolate request
  data into SQL. (Column names currently interpolated from hardcoded
  whitelists — `game.py:2203`, `chat.py:215` — are out of scope here; noted as
  a low-severity hardening item, not planned.)
- **Feature modules are flat top-level `.py` files holding pure / helper
  functions** (`wagers.py`, `prestige.py`, `bounties.py`, `community_goals.py`,
  `wheel_modes.py`, `seasons.py`). **Route handlers stay in `game.py`** on the
  `game_bp` blueprint and call into those modules. Match this split (it is the
  basis of §7).
- **Pure game-data/math functions** live in `models.py` and are unit-tested in
  `tests/test_models.py` with **no DB and no Flask**.
- **Style:** PEP 8, `ruff` + `ruff format` + `isort --profile=black`
  (see `.pre-commit-config.yaml`). Type-annotate new function signatures.
- **Logging:** module logger `log = logging.getLogger('wheel')`; route error
  handlers log with an UPPER_SNAKE label + `user_id` and return JSON
  `{'error': ...}` with a status code (see `game.py` `spin()` `except`).
- **Tests:** `pytest`, function names `test_*`. Pure logic → model-style unit
  test; endpoint behavior → integration test hitting the route.

## §4. Commit / branch conventions (from `git log`)

- Conventional-commit style, ticket-tagged:
  `fix(perf): T237 composite leaderboard index`,
  `test(spin): T239 characterization tests for _resolve_spin`.
- One commit per ticket (or per logical step in the larger ones).
- Do **not** push or deploy unless the operator says so. Promotion to live
  follows the existing staging→prod flow (`deploy.sh` / `Makefile`).

## §5. Dependency graph for T231–T240

```
Bundle A — verification foundation (do first)
  T231 (flaky gate) ─┬─> T232 (conftest.py)
                     └─> T233 (make test + docs)

Bundle B — security + correctness (independent of A; can run in parallel)
  T234 (DB creds → env + rotate)
  T235 (insurance/token refund fix)
  T236 (close CSRF-exempt inconsistency)

Bundle C — performance (independent)
  T237 (composite leaderboard index)
  T238 (/api/state DB consolidation)

Bundle D — game.py refactor (gated on A)
  T231,T232 ─> T239 (characterization + integration tests) ─> T240 (extract fishing pilot)
```

Recommended order: **T231 → T232 → T234/T235/T236/T237/T238 (any order) →
T233 → T239 → T240.** T235 (money) and T234 (credential) are the highest-value
of the parallel set.

## §6. Status table (executors update this)

| Ticket | Title | Bundle | Effort | Depends on | Status |
|--------|-------|--------|--------|------------|--------|
| T231 | Fix flaky pytest baseline (stub leak) | A | M | — | [x] |
| T232 | Add `tests/conftest.py` shared fixtures | A | S | T231 | [x] |
| T233 | `make test` target + README "Running Tests" | A | S | T231 | [x] |
| T234 | Move staging DB creds out of tests → env + rotate | B | S | — | [x] |
| T235 | Fix insurance/token escrow refund underpayment | B | S | — | [x] |
| T236 | Close CSRF-exempt inconsistency on session routes | B | M | — | [x] |
| T237 | Composite leaderboard index (migration 071) | C | S | — | [x] |
| T238 | Consolidate `/api/state` database access | C | S | — | [x] |
| T239 | Characterization + integration tests (spin + routes) | D | L | T231,T232 | [x] |
| T240 | Extract fishing subsystem from `game.py` (pilot) | D | L | T239 | [x] |
| T241 | Hide test users from `/api/leaderboard` (server-side filter) | D | S | — | [x] |
| T242 | Convert 22 stub-installing test files to `setup_module`/`teardown_module` | A | M | T231 | [ ] |
| T243 | Extract `dice.py` from `game.py` | D | M | T240 | [ ] |
| T244 | Extract `shop.py` from `game.py` (ARCH-04 dedup) | D | M | T240 | [ ] |
| T245 | Extract `loadout.py` from `game.py` (`COSMETIC_SLOTS`) | D | M | T240 | [ ] |
| T246 | Set up `wheeldb_test` (route pytest off prod) | B | M | T234 | [ ] |
| T247 | `/api/state` further consolidation (move more to SQL) | C | S | T238 | [ ] |

## §7. `game.py` extraction design (for T240 and follow-ups)

**Problem.** `game.py` is 4,220 lines / 49 routes / ~67 functions — ~9× the
next-largest module (`models.py`, 452). `_resolve_spin` alone is ~594 lines
(`game.py:272-866`) with 32 parameters. Every feature change carries the whole
file. (Findings ARCH-01/ARCH-02.)

**Approach — match the existing convention, don't invent a new one.** The team
already extracts feature *logic* into helper modules and keeps *route handlers*
in `game.py` (e.g. `/api/wager/*` handlers live in `game.py` but call
`wagers.py`). So extraction = move the testable logic + DB helpers of a
subsystem into a new `<feature>.py`, leave a **thin** route handler in
`game.py` that parses the request, opens the transaction, calls the module,
and builds the response. Do **not** introduce new blueprints in T240 (bigger
change, higher risk; revisit only if the thin-handler approach proves
insufficient).

**Subsystem map (target end-state, in priority order):**

| New module | Routes that stay thin in `game.py` | Logic/helpers to move |
|------------|-----------------------------------|-----------------------|
| `fish.py` *(T240 pilot)* | `/api/cast`, `/api/bite-poll`, `/api/reel`, `/api/auto-fish-tick`, `/api/auto-fish-enabled` | `cast_line`/`bite_poll`/`reel_line`/`auto_fish_tick` bodies, `_get_total_fish_clicks` (`game.py:97`), fish-economy helpers in `game.py` that aren't already in `models.py` |
| `dice.py` *(follow-up)* | `/api/roll-dice` | `_recharge_dice` (`game.py:77`), dice resolution logic in `roll_dice` |
| `shop.py` *(follow-up)* | `/api/buy` | `buy()` body (~208 lines, `game.py:2135`), extracted balance-check/cost-deduct helpers (ARCH-04 dedup folds in here) |
| `loadout.py` *(follow-up)* | `/api/loadout` GET/POST, `/api/equip`, `/api/equip-class`, `/api/equip-cosmetic` | loadout get/save/apply logic, **`COSMETIC_SLOTS`** dict (`game.py:45-62`, ARCH-06 — move alongside `SHOP_ITEMS` semantics) |

**Why fishing is the pilot:** self-contained (its own routes, its own DB
columns), no entanglement with `_resolve_spin`'s money math, and it has clear
HTTP boundaries — the lowest-risk seam to prove the recipe. Once T240 lands and
is green, the follow-up tickets replicate the exact recipe per row above.

**Hard prerequisite:** the moved logic must be covered by tests *before* it
moves (T239). Refactor with a green baseline, move in small commits
(add new module → switch the route to call it → delete the old inline code),
keep the suite green between every commit.

**Out of scope for the whole extraction effort:** changing any HTTP
request/response shape (the React frontend in `static/app.jsx` depends on it),
touching `_resolve_spin`'s logic (move-only if at all — its split is ARCH-02,
a separate future effort gated on T239), and changing DB schema.
