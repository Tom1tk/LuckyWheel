"""RV-10: the due check in bin/advance_tide.py (pure, no database)."""
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PATH = Path(__file__).resolve().parent.parent / 'bin' / 'advance_tide.py'
_spec = importlib.util.spec_from_file_location('advance_tide', _PATH)
advance_tide = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(advance_tide)

NOW = datetime(2026, 10, 9, 21, 0, tzinfo=timezone.utc)


def test_not_tide_when_sub_number_is_missing():
    assert advance_tide.tide_status(None, NOW - timedelta(days=1), NOW) == 'not_tide'


def test_not_due_when_ends_at_is_missing():
    assert advance_tide.tide_status(1, None, NOW) == 'not_due'


def test_not_due_while_ends_at_is_in_the_future():
    assert advance_tide.tide_status(1, NOW + timedelta(seconds=1), NOW) == 'not_due'


def test_due_once_ends_at_has_passed():
    assert advance_tide.tide_status(1, NOW - timedelta(minutes=1), NOW) == 'due'


def test_due_exactly_at_ends_at():
    assert advance_tide.tide_status(1, NOW, NOW) == 'due'
