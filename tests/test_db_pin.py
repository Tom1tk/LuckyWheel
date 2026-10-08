"""Revival 0.4: the whole pytest session must target wheeldb_test, never prod."""
import os
from urllib.parse import urlsplit


def test_session_pinned_to_wheeldb_test():
    url = os.environ.get('DATABASE_URL')
    assert url is None or urlsplit(url).path == '/wheeldb_test'
