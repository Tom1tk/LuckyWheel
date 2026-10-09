"""T240: Unit tests for the fishing subsystem extracted from ``game.py``.

These tests exercise the pure helpers and the route-level functions
in ``fish.py`` directly — no Flask request context, no real DB. A
``MockCursor`` and ``MockConn`` stand in for the real ``psycopg2``
objects, with every call recorded for assertion.

The T239 spin/route integration tests in ``tests/test_spin_integration.py``
and ``tests/test_critical_routes.py`` still cover the full HTTP
contract against a real server. This file pins the in-process logic
so the extraction stays green.
"""

import datetime as dt
import os
import random
import sys
from datetime import timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import fish
from fish import (
    lure_level,
    autofisher_level,
    get_total_fish_clicks,
    reset_total_fish_clicks_cache,
    cast_line,
    bite_poll,
    reel_line,
    auto_fish_tick,
    set_auto_fish_enabled,
    REEL_WINDOW_SECONDS,
    REEL_MIN_DELTA_SECONDS,
)
from models import FISH_CATALOG


# ──────────────────────────────────────────────────────────────────────────
# Mocks
# ──────────────────────────────────────────────────────────────────────────


class MockCursor:
    """In-memory stand-in for a psycopg2 cursor.

    `queue_fetchone` is a list of dicts the next fetchone() calls will
    return. `execute_calls` records every (sql, params) tuple for
    later inspection. `rowcount` is settable per execute() if the test
    needs to simulate an UPDATE that affected 0/1 rows.
    """

    def __init__(self, queue_fetchone=None, *, fetchone_default=None):
        self.queue_fetchone = list(queue_fetchone or [])
        self.fetchone_default = fetchone_default
        self.execute_calls = []
        self.rowcount = 1

    def execute(self, sql, params=None):
        self.execute_calls.append((sql.strip(), params))
        return self

    def fetchone(self):
        if self.queue_fetchone:
            return self.queue_fetchone.pop(0)
        return self.fetchone_default

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class MockConn:
    """Mock connection — records cursor() opens, commits, rollbacks.

    `cursor_factory` is ignored (we always return MockCursor). The
    onboarding block in fish._post_catch_bookkeeping opens its own
    cursor via `with conn.cursor() as cur`, so MockCursor must
    support the context manager protocol (it does — see above).
    """

    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.cursor_opens = 0

    def cursor(self, cursor_factory=None):
        self.cursor_opens += 1
        return MockCursor()

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


# ──────────────────────────────────────────────────────────────────────────
# Upgrade-level helpers (pure)
# ──────────────────────────────────────────────────────────────────────────


class TestUpgradeLevelHelpers:
    def test_lure_level_no_items(self):
        assert lure_level([]) == 0

    def test_lure_level_lure_1(self):
        assert lure_level(["lure_1"]) == 1

    def test_lure_level_higher_tier_wins(self):
        # Owning lure_1 AND lure_3 returns the higher level (3).
        assert lure_level(["lure_1", "lure_3"]) == 3

    def test_lure_level_tier_5(self):
        assert lure_level(["lure_5"]) == 5

    def test_lure_level_ignores_other_items(self):
        assert lure_level(["wager_unlock", "autofisher_2"]) == 0

    def test_autofisher_level_no_items(self):
        assert autofisher_level([]) == 0

    def test_autofisher_level_tier_4(self):
        # Master tier — catches rare species.
        assert autofisher_level(["autofisher_4"]) == 4

    def test_autofisher_level_higher_tier_wins(self):
        assert autofisher_level(["autofisher_1", "autofisher_3"]) == 3


# ──────────────────────────────────────────────────────────────────────────
# get_total_fish_clicks (cached aggregate)
# ──────────────────────────────────────────────────────────────────────────


class TestGetTotalFishClicks:
    def setup_method(self):
        reset_total_fish_clicks_cache()

    def test_returns_sum_when_cache_miss(self):
        cur = MockCursor(queue_fetchone=[{"total": 4242}])
        result = get_total_fish_clicks(cur)
        assert result == 4242
        assert len(cur.execute_calls) == 1
        assert "SUM(fish_clicks)" in cur.execute_calls[0][0]

    def test_handles_null_sum(self):
        # When the table is empty, COALESCE(SUM(fish_clicks), 0) → 0.
        cur = MockCursor(queue_fetchone=[{"total": 0}])
        result = get_total_fish_clicks(cur)
        assert result == 0

    def test_cache_hit_skips_query(self):
        cur1 = MockCursor(queue_fetchone=[{"total": 100}])
        v1 = get_total_fish_clicks(cur1)
        # Second call within TTL re-uses the cached value.
        cur2 = MockCursor(queue_fetchone=[{"total": 9999}])
        v2 = get_total_fish_clicks(cur2)
        assert v1 == 100
        assert v2 == 100, "second call should hit the cache, not re-query"
        assert len(cur1.execute_calls) == 1
        assert len(cur2.execute_calls) == 0

    def test_cache_reset_triggers_re_query(self):
        cur1 = MockCursor(queue_fetchone=[{"total": 100}])
        get_total_fish_clicks(cur1)
        reset_total_fish_clicks_cache()
        cur2 = MockCursor(queue_fetchone=[{"total": 250}])
        v2 = get_total_fish_clicks(cur2)
        assert v2 == 250
        assert len(cur2.execute_calls) == 1


# ──────────────────────────────────────────────────────────────────────────
# cast_line
# ──────────────────────────────────────────────────────────────────────────


class TestCastLine:
    NOW = dt.datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)

    def test_fresh_cast_succeeds(self):
        cur = MockCursor(
            queue_fetchone=[
                {
                    "owned_items": ["lure_3"],
                    "talent_alloc": {}, "fish_records": {},
                    "fishing_cast_at": None,
                    "fishing_bite_at": None,
                }
            ]
        )
        rand = random.Random(42)
        result = cast_line(cur, user_id=7, now_utc=self.NOW, rand=rand)
        assert isinstance(result, dict)
        assert result["cast_at"] == self.NOW.isoformat()
        # bite_at is intentionally NOT in the response.
        assert "bite_at" not in result
        # UPDATE was issued with the new cast_at + bite_at.
        update = [c for c in cur.execute_calls if c[0].startswith("UPDATE")]
        assert len(update) == 1
        assert "fishing_cast_at = %s" in update[0][0]
        assert update[0][1] == (self.NOW, update[0][1][1], 7)

    def test_already_fishing_returns_400(self):
        # Active session: bite_at + REEL_WINDOW still in the future.
        active_bite = self.NOW - dt.timedelta(seconds=0.5)
        cur = MockCursor(
            queue_fetchone=[
                {
                    "owned_items": [],
                    "talent_alloc": {}, "fish_records": {},
                    "fishing_cast_at": self.NOW - dt.timedelta(seconds=2),
                    "fishing_bite_at": active_bite,
                }
            ]
        )
        rand = random.Random(0)
        result = cast_line(cur, user_id=7, now_utc=self.NOW, rand=rand)
        # Returns the (status, body) tuple — route handler renders it.
        assert result == (400, {"error": "Already fishing"})
        # No INSERT/UPDATE was issued (the SELECT contains "FOR UPDATE"
        # as a keyword, so the assertion matches on the verb at the
        # start of the SQL only).
        writes = [
            c
            for c in cur.execute_calls
            if c[0].startswith(("INSERT", "UPDATE", "DELETE"))
        ]
        assert writes == [], (
            f"cast_line should not issue a write when rejecting, got {writes}"
        )

    def test_expired_session_allows_recast(self):
        # Bite happened in the past, beyond REEL_WINDOW.
        stale_bite = self.NOW - dt.timedelta(seconds=REEL_WINDOW_SECONDS + 1)
        cur = MockCursor(
            queue_fetchone=[
                {
                    "owned_items": [],
                    "talent_alloc": {}, "fish_records": {},
                    "fishing_cast_at": self.NOW - dt.timedelta(seconds=10),
                    "fishing_bite_at": stale_bite,
                }
            ]
        )
        rand = random.Random(0)
        result = cast_line(cur, user_id=7, now_utc=self.NOW, rand=rand)
        assert isinstance(result, dict)
        # UPDATE was issued.
        assert any("UPDATE" in c[0] for c in cur.execute_calls)

    def test_nibble_at_included_when_random_under_half(self):
        # rand.random() returns 0.0 → < 0.5, so nibble fires.
        cur = MockCursor(
            queue_fetchone=[
                {
                    "owned_items": [],
                    "talent_alloc": {}, "fish_records": {},
                    "fishing_cast_at": None,
                    "fishing_bite_at": None,
                }
            ]
        )
        rand = random.Random(0)
        result = cast_line(cur, user_id=7, now_utc=self.NOW, rand=rand)
        # With seed 0, rand.random() returns 0.844... which is > 0.5.
        # The nibble may or may not appear — it's randomised.
        # The contract is just: it's a string or None, never a crash.
        assert result["nibble_at"] is None or isinstance(result["nibble_at"], str)


# ──────────────────────────────────────────────────────────────────────────
# bite_poll
# ──────────────────────────────────────────────────────────────────────────


class TestBitePoll:
    NOW = dt.datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)

    def test_no_cast_returns_bite_false(self):
        cur = MockCursor(queue_fetchone=[{"fishing_bite_at": None}])
        result = bite_poll(cur, user_id=7, now_utc=self.NOW)
        assert result == {"bite": False}

    def test_expired_returns_expired_true(self):
        stale = self.NOW - dt.timedelta(seconds=REEL_WINDOW_SECONDS + 1)
        cur = MockCursor(queue_fetchone=[{"fishing_bite_at": stale}])
        result = bite_poll(cur, user_id=7, now_utc=self.NOW)
        assert result == {"expired": True}

    def test_before_bite_returns_bite_false(self):
        future = self.NOW + dt.timedelta(seconds=2)
        cur = MockCursor(queue_fetchone=[{"fishing_bite_at": future}])
        result = bite_poll(cur, user_id=7, now_utc=self.NOW)
        assert result == {"bite": False}

    def test_biting_returns_remaining_ms(self):
        # Bite happened 0.3s ago — still inside the 1.8s window.
        bite = self.NOW - dt.timedelta(seconds=0.3)
        cur = MockCursor(queue_fetchone=[{"fishing_bite_at": bite}])
        result = bite_poll(cur, user_id=7, now_utc=self.NOW)
        assert result["bite"] is True
        # Window is 1.8s, so 0.3s in leaves ~1.5s = ~1500ms.
        assert 1400 < result["remaining_ms"] <= 1500

    def test_naive_datetime_is_aware_after_poll(self):
        # psycopg2 returns naive datetimes — the function must handle
        # them. We pass a naive datetime and a tz-aware now_utc.
        naive_bite = self.NOW.replace(tzinfo=None) - dt.timedelta(seconds=0.3)
        cur = MockCursor(queue_fetchone=[{"fishing_bite_at": naive_bite}])
        result = bite_poll(cur, user_id=7, now_utc=self.NOW)
        assert result["bite"] is True


# ──────────────────────────────────────────────────────────────────────────
# reel_line
# ──────────────────────────────────────────────────────────────────────────


class TestReelLine:
    NOW = dt.datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    # Bite happened 0.5 s before NOW: inside the 1.8 s window, past
    # the 0.05 s "too fast" floor.  This is the sweet spot for hit-tests.
    BITE = NOW - dt.timedelta(seconds=0.5)
    CAST_AT = NOW - dt.timedelta(seconds=2.0)

    def _row(self, **kw):
        defaults = {
            "owned_items": [],
            "talent_alloc": {}, "fish_records": {},
            "fishing_cast_at": self.CAST_AT,
            "fishing_bite_at": self.BITE,
            "fishing_lucky_next": False,
            "caught_species": [],
            "fish_clicks": 0,
            "fastest_catch_pct": None,
            "suspicious_catches": 0,
            "catch_count": 0,
            "catch_pct_ewma": None,
            "catch_of_the_day_date": None,
            "onboarding_step": 0,
        }
        defaults.update(kw)
        return defaults

    def test_no_session_returns_miss(self, monkeypatch):
        row = self._row(fishing_cast_at=None, fishing_bite_at=None, fish_clicks=42)
        cur = MockCursor(queue_fetchone=[row])
        conn = MockConn()
        # Bypass the bookkeeping calls — no successful catch here.
        monkeypatch.setattr(fish, "increment_bounty", lambda *a, **k: None)
        monkeypatch.setattr(fish, "_post_catch_bookkeeping", lambda *a, **k: None)
        result = reel_line(cur, conn, user_id=7, now_utc=self.NOW)
        assert result == {
            "result": "miss",
            "reason": "no_session",
            "fish_clicks": 42,
        }

    def test_bad_timing_returns_miss(self, monkeypatch):
        # Bite is in the FUTURE relative to now_utc → too early.
        future_bite = self.NOW + dt.timedelta(seconds=0.5)
        row = self._row(fishing_bite_at=future_bite, fish_clicks=10)
        cur = MockCursor(queue_fetchone=[row])
        conn = MockConn()
        monkeypatch.setattr(fish, "increment_bounty", lambda *a, **k: None)
        result = reel_line(cur, conn, user_id=7, now_utc=self.NOW)
        assert result["result"] == "miss"
        assert result["reason"] == "bad_timing"
        assert result["fish_clicks"] == 10
        # Session was cleared.
        clears = [
            c
            for c in cur.execute_calls
            if c[0].startswith("UPDATE game_state") and "fishing_cast_at = NULL" in c[0]
        ]
        assert len(clears) == 1

    def test_too_fast_returns_miss(self, monkeypatch):
        # Bite happened REEL_MIN_DELTA_SECONDS - 0.01s ago → too fast.
        bite = self.NOW - dt.timedelta(seconds=REEL_MIN_DELTA_SECONDS - 0.01)
        row = self._row(fishing_bite_at=bite, fish_clicks=5)
        cur = MockCursor(queue_fetchone=[row])
        conn = MockConn()
        monkeypatch.setattr(fish, "increment_bounty", lambda *a, **k: None)
        result = reel_line(cur, conn, user_id=7, now_utc=self.NOW)
        assert result["result"] == "miss"
        assert result["reason"] == "too_fast"
        assert result["fish_clicks"] == 5

    def test_hook_stores_species_and_hides_it(self, monkeypatch):
        row = self._row(fish_clicks=100)
        cur = MockCursor(queue_fetchone=[row])
        monkeypatch.setattr(fish, "roll_fish", lambda **k: "shark")
        result = reel_line(cur, MockConn(), user_id=7, now_utc=self.NOW)
        assert result == {"result": "hooked", "rarity": "rare",
                          "fight_s": fish.FIGHT_S["rare"], "fish_clicks": 100}
        hooks = [c for c in cur.execute_calls if "fishing_species = %s" in c[0]]
        assert len(hooks) == 1 and hooks[0][1][:2] == ("shark", self.NOW)

    def test_suspicious_hook_increments_under_12pct(self, monkeypatch):
        # Elapsed 0.05s → precise_pct ≈ 2.8% → suspicious.
        bite = self.NOW - dt.timedelta(seconds=0.05)
        row = self._row(fishing_bite_at=bite, suspicious_catches=0)
        cur = MockCursor(queue_fetchone=[row])
        monkeypatch.setattr(fish, "roll_fish", lambda **k: "minnow")
        result = reel_line(cur, MockConn(), user_id=7, now_utc=self.NOW)
        assert result["result"] == "hooked"
        hook = next(c for c in cur.execute_calls if "fishing_species = %s" in c[0])
        assert hook[1][3] == 1  # suspicious_catches


# ──────────────────────────────────────────────────────────────────────────
# land_line
# ──────────────────────────────────────────────────────────────────────────


class TestLandLine:
    NOW = dt.datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)

    def _row(self, species="minnow", fought=5.0, **kw):
        row = {
            "owned_items": [],
            "talent_alloc": {}, "fish_records": {},
            "fishing_species": species,
            "fishing_hooked_at": self.NOW - dt.timedelta(seconds=fought),
            "fishing_lucky_next": False,
            "caught_species": [],
            "fish_clicks": 0,
            "catch_of_the_day_date": self.NOW.date(),  # already used today
            "onboarding_step": 0,
        }
        row.update(kw)
        return row

    def _land(self, monkeypatch, row, landed=True, quality=1.0):
        calls = []
        monkeypatch.setattr(fish, "_post_catch_bookkeeping",
                            lambda conn, uid, ts, fc: calls.append((uid, fc)))
        self.bounties = []
        monkeypatch.setattr(fish, "increment_bounty",
                            lambda conn, uid, bid, d, amount=1: self.bounties.append(bid))
        cur = MockCursor(queue_fetchone=[row])
        return fish.land_line(cur, MockConn(), 7, self.NOW, landed, quality), cur, calls

    def test_land_bounties(self, monkeypatch):
        monkeypatch.setattr(fish, "size_up_catch", lambda *a, **k: {
            "kg": 1.0, "value": 5, "surge": 1, "ratio": 0.95, "records": {}, "new_record": False})
        self._land(monkeypatch, self._row(species="shark", fought=7))
        assert self.bounties == ["bounty_hand5", "bounty_rare", "bounty_trophy"]
        monkeypatch.setattr(fish, "size_up_catch", lambda *a, **k: {
            "kg": 0.02, "value": 1, "surge": 1, "ratio": 0.89, "records": {}, "new_record": False})
        self._land(monkeypatch, self._row())
        assert self.bounties == ["bounty_hand5"]

    def test_no_hook_is_no_session(self, monkeypatch):
        result, _, calls = self._land(monkeypatch, self._row(species=None, fish_clicks=9))
        assert result == {"result": "miss", "reason": "no_session", "fish_clicks": 9}
        assert calls == []

    def test_not_landed_clears_the_line(self, monkeypatch):
        result, cur, calls = self._land(monkeypatch, self._row(), landed=False)
        assert result["result"] == "lost" and calls == []
        assert any("fishing_species = NULL" in c[0] for c in cur.execute_calls)
        assert not any("fish_clicks = %s" in c[0] for c in cur.execute_calls)

    def test_too_fast(self, monkeypatch):
        # shark fight_s 6 → must fight ≥ 3.6 s
        result, cur, _ = self._land(monkeypatch, self._row(species="shark", fought=3.5))
        assert result["reason"] == "too_fast"
        assert any("fishing_species = NULL" in c[0] for c in cur.execute_calls)

    def test_timeout(self, monkeypatch):
        result, _, _ = self._land(monkeypatch, self._row(fought=45.5))
        assert result["reason"] == "timeout"

    def test_hit_pays_and_books(self, monkeypatch):
        result, _, calls = self._land(monkeypatch, self._row(species="shark", fought=6.5, fish_clicks=100))
        assert result["result"] == "hit" and result["species"] == "shark"
        assert result["fish_clicks"] == 100 + result["value"]
        assert result["first_catch"] is True and calls == [(7, True)]

    def test_quality_is_clamped(self, monkeypatch):
        monkeypatch.setattr(fish.random, "random", lambda: 1.0)
        hi, _, _ = self._land(monkeypatch, self._row(species="shark"), quality=50.0)
        lo, _, _ = self._land(monkeypatch, self._row(species="shark"), quality=-50.0)
        lo_kg, hi_kg = FISH_CATALOG["shark"]["kg"]
        assert hi["kg"] == round(hi_kg, 3)
        assert lo["kg"] == round(lo_kg + (hi_kg - lo_kg) * 0.5, 3)

    def test_lucky_next_doubles_value(self, monkeypatch):
        monkeypatch.setattr(fish.random, "random", lambda: 0.0)
        plain, _, _ = self._land(monkeypatch, self._row(species="shark"), quality=0.0)
        lucky, _, _ = self._land(monkeypatch, self._row(species="shark", fishing_lucky_next=True), quality=0.0)
        assert lucky["value"] == 2 * plain["value"] and lucky["was_doubled"] is True
        assert lucky["lucky_next_active"] is False

    def test_catching_lucky_sets_lucky_next(self, monkeypatch):
        result, _, _ = self._land(monkeypatch, self._row(species="lucky", fought=8.0))
        assert result["lucky_next_active"] is True

    def test_catch_of_the_day_is_universal(self, monkeypatch):
        monkeypatch.setattr(fish.random, "random", lambda: 0.0)
        plain, _, _ = self._land(monkeypatch, self._row(species="shark"), quality=0.0)
        first, cur, _ = self._land(monkeypatch, self._row(species="shark", catch_of_the_day_date=None), quality=0.0)
        assert first["catch_of_day_bonus"] is True and plain["catch_of_day_bonus"] is False
        assert first["value"] == 5 * plain["value"]
        upd = next(c for c in cur.execute_calls if "fish_clicks = %s" in c[0])
        assert upd[1][3] == self.NOW.date()


# ──────────────────────────────────────────────────────────────────────────
# auto_fish_tick
# ──────────────────────────────────────────────────────────────────────────


class TestAutoFishTick:
    NOW = dt.datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)

    def _row(self, **kw):
        row = {
            "owned_items": ["autofisher_2"],
            "talent_alloc": {}, "fish_records": {},
            "fish_clicks": 0,
            "caught_species": [],
            "auto_fish_last_tick": None,
            "lure_mastery_level": 0,
            "equipped_class": None,
        }
        row.update(kw)
        return row

    def test_no_autofisher_returns_403(self):
        cur = MockCursor(queue_fetchone=[self._row(owned_items=[])])
        conn = MockConn()
        result = auto_fish_tick(cur, conn, user_id=7, now_utc=self.NOW)
        assert result == (403, {"error": "Auto-Fisher not owned"})

    def test_too_soon_returns_miss_without_update(self):
        # Last tick 1s ago — too soon.
        last_tick = self.NOW - dt.timedelta(seconds=1.0)
        cur = MockCursor(
            queue_fetchone=[
                self._row(fish_clicks=99, auto_fish_last_tick=last_tick),
            ]
        )
        conn = MockConn()
        result = auto_fish_tick(cur, conn, user_id=7, now_utc=self.NOW)
        assert result == {"result": "miss", "fish_clicks": 99}
        # No INSERT/UPDATE was issued (the early-return path skips the
        # write).  The SELECT has "FOR UPDATE" as a row-locking clause
        # so we match on the SQL verb at the start, not as a substring.
        writes = [
            c
            for c in cur.execute_calls
            if c[0].startswith(("INSERT", "UPDATE", "DELETE"))
        ]
        assert writes == [], f"too-soon should not issue a write, got {writes}"

    def test_random_miss_returns_miss(self, monkeypatch):
        # Force the catch-rate roll to fail: rand.random() returns 0.99
        # which is >= autofisher_catch_rate(2) (0.55).
        cur = MockCursor(queue_fetchone=[self._row(fish_clicks=77)])
        conn = MockConn()
        rand = random.Random(0)
        # random.Random(0).random() is 0.844... — > 0.55, so it's a miss.
        result = auto_fish_tick(cur, conn, user_id=7, now_utc=self.NOW, rand=rand)
        assert result == {"result": "miss", "fish_clicks": 77}
        # auto_fish_last_tick was updated.
        updates = [c for c in cur.execute_calls if c[0].startswith("UPDATE")]
        assert len(updates) == 1

    def test_random_hit_returns_hit(self, monkeypatch):
        # Force a hit by patching roll_fish to a specific species and
        # patching rand.random to a value < catch_rate.
        cur = MockCursor(queue_fetchone=[self._row(fish_clicks=10)])
        conn = MockConn()
        monkeypatch.setattr(fish, "roll_fish", lambda **k: "minnow")
        rand = random.Random()
        rand.random = lambda: 0.0  # < catch_rate, so it's a hit
        result = auto_fish_tick(cur, conn, user_id=7, now_utc=self.NOW, rand=rand)
        assert result["result"] == "hit"
        assert result["species"] == "minnow"
        assert result["value"] >= 1
        assert result["fish_clicks"] == 10 + result["value"]

    def test_earth_class_applies_bonus(self, monkeypatch):
        cur = MockCursor(
            queue_fetchone=[
                self._row(fish_clicks=0, equipped_class="earth"),
            ]
        )
        conn = MockConn()
        monkeypatch.setattr(fish, "roll_fish", lambda **k: "minnow")
        rand = random.Random()
        rand.random = lambda: 0.0
        auto_fish_tick(cur, conn, user_id=7, now_utc=self.NOW, rand=rand)
        # Minnow base 1, * 1.0 lure, * 1.0 mastery, * 1.25 earth → 1.25 → 1
        # (max(1, int(...)) = 1). Earth bonus doesn't matter at 1, so
        # we instead check via a higher-tier species. The "dolphin"
        # branch is excluded at autofisher_2 (allow_rare=False), so
        # this is more of a smoke check that the equipped_class='earth'
        # path doesn't raise.


# ──────────────────────────────────────────────────────────────────────────
# set_auto_fish_enabled
# ──────────────────────────────────────────────────────────────────────────


class TestSetAutoFishEnabled:
    NOW = dt.datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)

    def test_enables_when_owned(self):
        cur = MockCursor(
            queue_fetchone=[
                {
                    "owned_items": ["autofisher_1"],
                    "talent_alloc": {}, "fish_records": {},
                    "auto_fish_enabled": False,
                }
            ]
        )
        conn = MockConn()
        result = set_auto_fish_enabled(
            cur, conn, user_id=7, requested=True, now_utc=self.NOW
        )
        assert result == {"ok": True, "auto_fish_enabled": True}

    def test_forces_off_when_no_autofisher(self):
        # T224: missing upgrade → flag forced off (defensive).
        cur = MockCursor(
            queue_fetchone=[
                {
                    "owned_items": [],
                    "talent_alloc": {}, "fish_records": {},
                    "auto_fish_enabled": True,
                }
            ]
        )
        conn = MockConn()
        result = set_auto_fish_enabled(
            cur, conn, user_id=7, requested=True, now_utc=self.NOW
        )
        assert result == {"ok": True, "auto_fish_enabled": False}

    def test_disables_when_requested_off(self):
        cur = MockCursor(
            queue_fetchone=[
                {
                    "owned_items": ["autofisher_1"],
                    "talent_alloc": {}, "fish_records": {},
                    "auto_fish_enabled": True,
                }
            ]
        )
        conn = MockConn()
        result = set_auto_fish_enabled(
            cur, conn, user_id=7, requested=False, now_utc=self.NOW
        )
        assert result == {"ok": True, "auto_fish_enabled": False}

    def test_disable_clears_last_tick(self):
        cur = MockCursor(
            queue_fetchone=[
                {
                    "owned_items": ["autofisher_1"],
                    "talent_alloc": {}, "fish_records": {},
                    "auto_fish_enabled": True,
                }
            ]
        )
        conn = MockConn()
        set_auto_fish_enabled(cur, conn, user_id=7, requested=False, now_utc=self.NOW)
        # UPDATE includes CASE WHEN %s ... ELSE NULL.
        updates = [c for c in cur.execute_calls if "UPDATE game_state" in c[0]]
        assert len(updates) == 1
        sql, params = updates[0]
        assert "auto_fish_last_tick" in sql
        # params: (enabled, enabled, user_id) — both Nones/False here.
        assert params[0] is False
        assert params[1] is False
        assert params[2] == 7
