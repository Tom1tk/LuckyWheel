"""T245: Unit tests for the loadout subsystem extracted from ``game.py``.

These tests exercise the route-level functions in ``loadout.py``
directly — no Flask request context, no real DB. A ``MockCursor``
and ``MockConn`` stand in for the real ``psycopg2`` objects, with
every call recorded for assertion.

The T239 / T243 / T244 integration tests in
``tests/test_critical_routes.py`` still cover the full HTTP
contract against a real server. This file pins the in-process
logic so the extraction stays green.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from loadout import (
    COSMETIC_SLOTS,
    VALID_FISH_IDS,  # re-export sanity check
    get_loadout,
    save_loadout_core,
    equip_fish_core,
    equip_class_core,
    equip_cosmetic_core,
)


# ──────────────────────────────────────────────────────────────────────────
# Mocks
# ──────────────────────────────────────────────────────────────────────────


class MockCursor:
    """In-memory stand-in for a psycopg2 cursor.

    `queue_fetchone` is a list of dicts the next fetchone() calls
    will return. `queue_fetchall` is a list of dicts the next
    fetchall() call will return. `execute_calls` records every
    (sql, params) tuple for later inspection.
    """

    def __init__(
        self,
        queue_fetchone=None,
        *,
        fetchone_default=None,
        queue_fetchall=None,
    ):
        self.queue_fetchone = list(queue_fetchone or [])
        self.fetchone_default = fetchone_default
        self.queue_fetchall = list(queue_fetchall or [])
        self.execute_calls = []
        self.rowcount = 1

    def execute(self, sql, params=None):
        self.execute_calls.append((sql.strip(), params))
        return self

    def fetchone(self):
        if self.queue_fetchone:
            return self.queue_fetchone.pop(0)
        return self.fetchone_default

    def fetchall(self):
        if self.queue_fetchall:
            return self.queue_fetchall
        return []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class MockConn:
    """Mock connection — records cursor() opens, commits, rollbacks."""

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
# COSMETIC_SLOTS
# ──────────────────────────────────────────────────────────────────────────


class TestCosmeticSlots:
    def test_known_cosmetic_maps_to_slot(self):
        assert COSMETIC_SLOTS["bg_ocean"] == "bg"
        assert COSMETIC_SLOTS["theme_fire"] == "wheel"
        assert COSMETIC_SLOTS["fishsize_small"] == "size"
        assert COSMETIC_SLOTS["page_season8"] == "page_theme"
        assert COSMETIC_SLOTS["auto_guard"] == "auto_guard"

    def test_non_cosmetic_not_in_map(self):
        # Functional shop items should NOT be in COSMETIC_SLOTS.
        assert "wager_unlock" not in COSMETIC_SLOTS
        assert "fish_to_wager" not in COSMETIC_SLOTS
        assert "wager_insurance" not in COSMETIC_SLOTS
        assert "lure_1" not in COSMETIC_SLOTS

    def test_default_fish_id_is_valid(self):
        # 'default' must be a valid fish id (off-skin). It's not in
        # COSMETIC_SLOTS — equipping a fish never touches that map.
        assert "default" in VALID_FISH_IDS
        assert "default" not in COSMETIC_SLOTS


# ──────────────────────────────────────────────────────────────────────────
# get_loadout
# ──────────────────────────────────────────────────────────────────────────


class TestGetLoadout:
    def test_returns_empty_dict_when_no_rows(self):
        cur = MockCursor(queue_fetchall=[])
        result = get_loadout(cur, user_id=7)
        assert result == {"loadouts": {}}
        assert len(cur.execute_calls) == 1
        assert "FROM build_loadouts" in cur.execute_calls[0][0]

    def test_returns_indexed_dict_from_rows(self):
        cur = MockCursor(
            queue_fetchall=[
                {"slot": 1, "config": {"equipped_class": "earth"}},
                {"slot": 2, "config": {"equipped_class": "moon"}},
                {"slot": 3, "config": {"equipped_class": None}},
            ]
        )
        result = get_loadout(cur, user_id=7)
        assert result == {
            "loadouts": {
                1: {"equipped_class": "earth"},
                2: {"equipped_class": "moon"},
                3: {"equipped_class": None},
            }
        }


# ──────────────────────────────────────────────────────────────────────────
# save_loadout_core
# ──────────────────────────────────────────────────────────────────────────


class TestSaveLoadoutCore:
    def test_valid_slot_succeeds(self):
        cur = MockCursor()
        conn = MockConn()
        result = save_loadout_core(
            cur, conn, user_id=7, slot=2, raw_loadout={"equipped_class": "earth"}
        )
        assert result == {"ok": True, "slot": 2}
        # INSERT ... ON CONFLICT was issued.
        assert len(cur.execute_calls) == 1
        sql, params = cur.execute_calls[0]
        assert "INSERT INTO build_loadouts" in sql
        assert "ON CONFLICT" in sql
        # params: (user_id, slot, Json(loadout_data))
        assert params[0] == 7
        assert params[1] == 2
        # The third arg is a psycopg2.extras.Json wrapper; its
        # underlying dict has only the spec-allowed fields. Use the
        # ``.adapted`` attribute that psycopg2 exposes on the
        # adapter.
        wrapped = params[2]
        assert wrapped.adapted == {
            "equipped_class": "earth",
            "active_wheel_mode": "steady",
        }

    def test_default_active_wheel_mode_is_steady(self):
        cur = MockCursor()
        conn = MockConn()
        # No active_wheel_mode provided in raw → default 'steady'.
        save_loadout_core(cur, conn, user_id=7, slot=1, raw_loadout={})
        params = cur.execute_calls[0][1]
        wrapped = params[2]
        assert wrapped.adapted["active_wheel_mode"] == "steady"
        assert wrapped.adapted["equipped_class"] is None

    def test_drops_owned_items_and_active_cosmetics(self):
        # Spec S11: client-supplied owned_items/active_cosmetics
        # must never be persisted (exploit fix — used to let any
        # player grant themselves every item for free).
        cur = MockCursor()
        conn = MockConn()
        save_loadout_core(
            cur,
            conn,
            user_id=7,
            slot=1,
            raw_loadout={
                "equipped_class": "earth",
                "active_wheel_mode": "gravity",
                "owned_items": ["wager_unlock", "lure_5"],
                "active_cosmetics": ["bg_ocean"],
            },
        )
        params = cur.execute_calls[0][1]
        wrapped = params[2]
        data = wrapped.adapted
        assert "owned_items" not in data
        assert "active_cosmetics" not in data
        assert data == {
            "equipped_class": "earth",
            "active_wheel_mode": "gravity",
        }

    def test_slot_zero_returns_400(self):
        cur = MockCursor()
        conn = MockConn()
        result = save_loadout_core(cur, conn, user_id=7, slot=0, raw_loadout={})
        assert result == (400, {"error": "Slot must be 1-3"})
        assert cur.execute_calls == []

    def test_slot_four_returns_400(self):
        cur = MockCursor()
        conn = MockConn()
        result = save_loadout_core(cur, conn, user_id=7, slot=4, raw_loadout={})
        assert result == (400, {"error": "Slot must be 1-3"})
        assert cur.execute_calls == []

    def test_negative_slot_returns_400(self):
        cur = MockCursor()
        conn = MockConn()
        result = save_loadout_core(cur, conn, user_id=7, slot=-1, raw_loadout={})
        assert result == (400, {"error": "Slot must be 1-3"})


# ──────────────────────────────────────────────────────────────────────────
# equip_fish_core
# ──────────────────────────────────────────────────────────────────────────


class TestEquipFishCore:
    def _row(self, **kw):
        defaults = {"owned_items": []}
        defaults.update(kw)
        return defaults

    def test_default_fish_succeeds_without_ownership_check(self):
        cur = MockCursor(queue_fetchone=[self._row(owned_items=[])])
        conn = MockConn()
        result = equip_fish_core(cur, conn, user_id=7, fish_id="default")
        assert result == {"equipped_fish": "default"}
        # SELECT + UPDATE
        selects = [
            c
            for c in cur.execute_calls
            if c[0].startswith("SELECT") and "owned_items" in c[0]
        ]
        updates = [c for c in cur.execute_calls if c[0].startswith("UPDATE")]
        assert len(selects) == 1
        assert len(updates) == 1
        assert updates[0][1] == ("default", 7)

    def test_owned_fish_succeeds(self):
        cur = MockCursor(
            queue_fetchone=[self._row(owned_items=["fish_shark", "fish_tropical"])]
        )
        conn = MockConn()
        result = equip_fish_core(cur, conn, user_id=7, fish_id="fish_tropical")
        assert result == {"equipped_fish": "fish_tropical"}

    def test_invalid_fish_id_returns_400(self):
        cur = MockCursor()
        conn = MockConn()
        result = equip_fish_core(cur, conn, user_id=7, fish_id="nope_not_a_skin")
        assert result == (400, {"error": "Invalid fish"})
        # No DB read or write was issued.
        assert cur.execute_calls == []

    def test_unowned_fish_returns_403(self):
        cur = MockCursor(queue_fetchone=[self._row(owned_items=["fish_tropical"])])
        conn = MockConn()
        result = equip_fish_core(cur, conn, user_id=7, fish_id="fish_ufo")
        assert result == (403, {"error": "Fish not owned"})
        # SELECT was issued but no UPDATE.
        updates = [c for c in cur.execute_calls if c[0].startswith("UPDATE")]
        assert updates == []


# ──────────────────────────────────────────────────────────────────────────
# equip_class_core
# ──────────────────────────────────────────────────────────────────────────


class TestEquipClassCore:
    def _row(self, **kw):
        defaults = {"owned_items": []}
        defaults.update(kw)
        return defaults

    def test_valid_class_owned_succeeds(self):
        cur = MockCursor(queue_fetchone=[self._row(owned_items=["class_earth"])])
        conn = MockConn()
        result = equip_class_core(cur, conn, user_id=7, class_id="class_earth")
        assert result == {"ok": True, "equipped_class": "earth"}
        updates = [c for c in cur.execute_calls if c[0].startswith("UPDATE")]
        assert len(updates) == 1
        assert updates[0][1] == ("earth", 7)

    def test_unequip_with_none_succeeds(self):
        # None means "unequip" — always allowed (no ownership check).
        cur = MockCursor(queue_fetchone=[self._row(owned_items=[])])
        conn = MockConn()
        result = equip_class_core(cur, conn, user_id=7, class_id=None)
        assert result == {"ok": True, "equipped_class": None}
        updates = [c for c in cur.execute_calls if c[0].startswith("UPDATE")]
        assert len(updates) == 1
        assert updates[0][1] == (None, 7)

    def test_invalid_class_id_returns_400(self):
        cur = MockCursor()
        conn = MockConn()
        result = equip_class_core(cur, conn, user_id=7, class_id="class_void")
        assert result == (400, {"error": "Invalid class"})
        # No DB access.
        assert cur.execute_calls == []

    def test_unowned_class_returns_400(self):
        cur = MockCursor(queue_fetchone=[self._row(owned_items=["class_earth"])])
        conn = MockConn()
        result = equip_class_core(cur, conn, user_id=7, class_id="class_moon")
        assert result == (400, {"error": "Class not owned"})
        # SELECT was issued, no UPDATE.
        updates = [c for c in cur.execute_calls if c[0].startswith("UPDATE")]
        assert updates == []

    def test_moon_and_star_mappings(self):
        for class_id, value in [
            ("class_moon", "moon"),
            ("class_star", "star"),
        ]:
            cur = MockCursor(queue_fetchone=[{"owned_items": [class_id]}])
            conn = MockConn()
            result = equip_class_core(cur, conn, user_id=7, class_id=class_id)
            assert result == {"ok": True, "equipped_class": value}, class_id


# ──────────────────────────────────────────────────────────────────────────
# equip_cosmetic_core
# ──────────────────────────────────────────────────────────────────────────


class TestEquipCosmeticCore:
    def _row(self, **kw):
        defaults = {"owned_items": [], "active_cosmetics": []}
        defaults.update(kw)
        return defaults

    def test_invalid_cosmetic_returns_400(self):
        cur = MockCursor()
        conn = MockConn()
        result = equip_cosmetic_core(cur, conn, user_id=7, item_id="not_a_cosmetic")
        assert result == (400, {"error": "Invalid cosmetic item"})
        assert cur.execute_calls == []

    def test_unowned_cosmetic_returns_400(self):
        cur = MockCursor(
            queue_fetchone=[self._row(owned_items=[], active_cosmetics=[])]
        )
        conn = MockConn()
        result = equip_cosmetic_core(cur, conn, user_id=7, item_id="bg_royal")
        assert result == (400, {"error": "Not owned"})
        # No UPDATE.
        updates = [c for c in cur.execute_calls if c[0].startswith("UPDATE")]
        assert updates == []

    def test_equip_first_time(self):
        cur = MockCursor(
            queue_fetchone=[self._row(owned_items=["bg_royal"], active_cosmetics=[])]
        )
        conn = MockConn()
        result = equip_cosmetic_core(cur, conn, user_id=7, item_id="bg_royal")
        assert result == {"active_cosmetics": ["bg_royal"]}
        updates = [c for c in cur.execute_calls if c[0].startswith("UPDATE")]
        assert len(updates) == 1
        assert updates[0][1] == (["bg_royal"], 7)

    def test_toggle_off_when_already_active(self):
        # Re-equipping an already-active cosmetic UN-equips it
        # (the same toggle UX the React client relies on).
        cur = MockCursor(
            queue_fetchone=[
                self._row(owned_items=["bg_royal"], active_cosmetics=["bg_royal"])
            ]
        )
        conn = MockConn()
        result = equip_cosmetic_core(cur, conn, user_id=7, item_id="bg_royal")
        assert result == {"active_cosmetics": []}

    def test_equip_replaces_same_slot(self):
        # A different bg is already active — equipping a new bg
        # replaces the old one. Other slots are untouched.
        cur = MockCursor(
            queue_fetchone=[
                self._row(
                    owned_items=["bg_ocean", "bg_royal", "fishsize_small"],
                    active_cosmetics=["bg_ocean", "fishsize_small"],
                )
            ]
        )
        conn = MockConn()
        result = equip_cosmetic_core(cur, conn, user_id=7, item_id="bg_royal")
        assert set(result["active_cosmetics"]) == {"bg_royal", "fishsize_small"}
        assert "bg_ocean" not in result["active_cosmetics"]

    def test_equip_does_not_touch_other_slots(self):
        # Toggling a page_theme must leave bg/size/... alone.
        cur = MockCursor(
            queue_fetchone=[
                self._row(
                    owned_items=["page_season8", "bg_ocean"],
                    active_cosmetics=["page_season7", "bg_ocean"],
                )
            ]
        )
        conn = MockConn()
        result = equip_cosmetic_core(cur, conn, user_id=7, item_id="page_season8")
        # page_season7 (same slot) is replaced; bg_ocean is kept.
        assert "page_season8" in result["active_cosmetics"]
        assert "page_season7" not in result["active_cosmetics"]
        assert "bg_ocean" in result["active_cosmetics"]
