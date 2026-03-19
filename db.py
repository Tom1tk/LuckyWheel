import logging
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
import psycopg2.pool

log = logging.getLogger('wheel')

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def init_pool(dsn: str) -> None:
    global _pool
    _pool = psycopg2.pool.ThreadedConnectionPool(minconn=2, maxconn=20, dsn=dsn)
    log.info('DB_POOL_CREATED  minconn=2  maxconn=20')


@contextmanager
def db_connection():
    """Yield a connection from the pool.

    On normal exit: connection is returned to the pool (caller must commit).
    On exception: connection is rolled back, then returned to the pool.
    On early return: connection is rolled back (no-op if nothing written), then returned.
    """
    conn = _pool.getconn()
    conn.autocommit = False
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        # No-op if already committed; cleans uncommitted state on early return.
        try:
            conn.rollback()
        except Exception:
            pass
        _pool.putconn(conn)
