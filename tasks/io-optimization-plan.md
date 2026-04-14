# Wheel-App Backend I/O Optimization Plan

## Context

The wheel-app game runs on a Proxmox LXC sharing an HDD with 18 other containers. PostgreSQL runs **locally** in this same LXC, so every DB commit triggers WAL fsync to the shared disk. There is **zero caching** anywhere in the application -- every request hits PostgreSQL directly.

**Current system:** 4GB RAM (3.5GB available), 6 CPU cores, PostgreSQL 17 with default settings (`synchronous_commit = on`, `shared_buffers = 128MB`).

### Measured I/O Load Per Active User

| Source | Interval | DB Ops | Writes/min |
|--------|----------|--------|------------|
| Fish clicks | 500ms flush | SELECT FOR UPDATE + UPDATE + commit | **120** |
| Click frenzy | 5s | SELECT FOR UPDATE + UPDATE + commit | 12 |
| Auto-spin | ~1s | 2-3 SELECTs + 1-2 UPDATEs + commit | 60-120 |
| `load_user()` | Every request | SELECT | 150+ reads |
| Chat poll | 3s | SELECT | 20 reads |
| Leaderboard poll | 5s | SELECT + JOIN + ORDER BY | 12 reads |
| Season poll | 60s | SELECT | 1 read |

**With 5 active users: ~1,500+ commits/min and ~1,000+ reads/min, all fsyncing to the shared HDD.**

---

## Option A: PostgreSQL Tuning (Recommended First)

**Effort:** 30 minutes | **Risk:** Very low | **I/O Reduction:** ~70-80%

Zero code changes. Edit `postgresql.conf` and restart.

### Changes

| Setting | Current | New | Why |
|---------|---------|-----|-----|
| `synchronous_commit` | `on` | `off` | **The biggest win.** Stops waiting for WAL fsync on every commit. Commits acknowledge immediately; WAL flushes async every ~200ms. |
| `shared_buffers` | `128MB` | `2GB` | Keep entire dataset in PostgreSQL buffer cache (tables are tiny). User has RAM in abundance. Eliminates read I/O. |
| `wal_buffers` | `4MB` | `16MB` | Larger WAL buffer = fewer partial page writes. |
| `checkpoint_timeout` | `5min` | `15min` | Checkpoints (full dirty-page flush) happen 3x less often. |
| `random_page_cost` | `4` | `1.1` | Tell planner data is in RAM, prefer index scans. |

Settings already good: `max_wal_size = 1GB`, `checkpoint_completion_target = 0.9`, `work_mem = 4MB`, `effective_cache_size = 4GB`.

### Data Loss Risk

On PostgreSQL crash or power failure: lose last ~200ms of commits (1-2 game actions). Application crashes (Python exceptions) are unaffected -- those use rollback, not commit. Perfectly acceptable for a game.

---

## Option B: Application-Level Read Caching (Redis)

**Effort:** 8-12 hours | **Risk:** Low | **I/O Reduction:** Additional ~50-60% of remaining reads

Add Redis as a shared read cache across all 4 Gunicorn workers.

### What Gets Cached

| Target | File:Line | TTL | Impact |
|--------|-----------|-----|--------|
| `load_user()` | `auth.py:22` | 60s, invalidate on login/logout | Eliminates ~95% of per-request DB reads |
| Chat messages | `chat.py:107` | 3s, invalidate on POST | All users see same data; 1 DB read/3s instead of N users x 1/3s |
| Leaderboard | `game.py:1140` | 5s | Same -- shared result for all users |
| Season info | `seasons.py:23` | 60s, invalidate on rollover | Rarely changes |
| Community pot | `game.py:704` | 5s, invalidate on contribute | Rarely changes |

### Implementation

- New `cache.py` module alongside `db.py` with Redis connection pool
- `redis` added to `requirements.txt`
- Fallback: on Redis failure, fall back to direct DB query (Redis is optional perf layer)
- Each cache target: ~20-30 lines of changes per endpoint

---

## Option C: Write Batching for Fish Clicks + Click Frenzy (Redis)

**Effort:** 12-16 hours | **Risk:** Medium | **I/O Reduction:** Eliminates ~132 commits/min/user

Accumulate the two highest-frequency writes in Redis, flush to PostgreSQL periodically.

### How It Works

1. **Fish click** (`game.py:921`): Instead of SELECT FOR UPDATE + UPDATE + commit per 500ms flush:
   - `HINCRBY fish_clicks:{user_id} pending {count}` in Redis (sub-millisecond, zero disk I/O)
   - Click budget enforcement (75 clicks/5s window) moves to Redis TTL key
   - Background thread flushes all pending clicks to PostgreSQL every 10 seconds as one batch transaction

2. **Click frenzy** (`game.py:976`): Same pattern -- accumulate in Redis, batch flush.

3. **Endpoints that read `fish_clicks`** (spin, buy, state): Add Redis pending amount to DB value.

### Data Loss Risk

On Redis crash: lose up to 10 seconds of fish clicks. Trivially recoverable by clicking more.

---

## Option D: Full In-Memory Game State (Redis as Primary Store)

**Effort:** 40-60 hours | **Risk:** High | **I/O Reduction:** ~95-99%

Move entire `game_state` table into Redis. PostgreSQL becomes a periodic checkpoint store, written every 1-15 minutes.

### Why I Recommend Against This (For Now)

- The spin endpoint logic (`game.py:154-440`) has ~300 lines of complex branching (shields, guards, streaks, jackpots, echoes, fortune charms, dice recharging, community pot decay, season rollover). Translating `SELECT FOR UPDATE` transactional safety to Redis Lua scripts is error-prone.
- Options A+B+C together should achieve ~90-95% I/O reduction, which resolves the shared-disk contention.
- If that's insufficient, Option D can be built incrementally on top of the Redis infrastructure from B+C.

---

## Quick Win: Reduce Client Polling Frequency

**Effort:** 5 minutes | **Risk:** None | **I/O Reduction:** ~40% of polling reads

| Poll | Current | Suggested | File:Line |
|------|---------|-----------|-----------|
| Leaderboard | 5s | 15s | `app.jsx:894` |
| Chat | 3s | 5s | `app.jsx:992` |

These are two number changes in `app.jsx`. The leaderboard only changes when someone spins; 15s is more than responsive enough. Chat at 5s is still snappy.

---

## Recommended Implementation Order

| Phase | What | I/O Reduction | Cumulative |
|-------|------|---------------|------------|
| **1** | PostgreSQL tuning (Option A) + client polling reduction | ~75% | ~75% |
| **2** | Redis read caching (Option B) | ~15% more | ~90% |
| **3** | Fish click write batching (Option C) | ~5% more | ~95% |

Phase 1 alone should dramatically reduce the disk contention. Phases 2 and 3 add defense in depth as the player count grows.

---

## Verification

- **Before:** Run `iostat -x 5` during gameplay to measure disk utilization baseline
- **After Phase 1:** Same `iostat` -- expect write IOPS to drop ~70-80%
- **After Phase 2:** Monitor Redis with `redis-cli INFO stats` -- confirm cache hits
- **After Phase 3:** Check PostgreSQL `pg_stat_user_tables` -- confirm `game_state` `n_tup_upd` rate drops significantly

## Critical Files

- `/var/lib/postgresql/17/main/postgresql.conf` -- Phase 1 tuning
- `/home/user/wheel-app/db.py` -- Add Redis pool init (Phase 2)
- `/home/user/wheel-app/auth.py:22` -- Cache `load_user()` (Phase 2)
- `/home/user/wheel-app/chat.py:107` -- Cache chat GET (Phase 2)
- `/home/user/wheel-app/game.py:921,976,1140` -- Fish click batching + leaderboard cache (Phase 2-3)
- `/home/user/wheel-app/static/app.jsx:894,992` -- Polling interval reduction (Phase 1)
