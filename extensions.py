"""Shared Flask extension instances — created here, bound to the app in app.py."""
import logging
import os

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, current_user

log = logging.getLogger('wheel')


def _rate_limit_key():
    """Key rate limits by user ID when authenticated, IP otherwise."""
    if current_user and current_user.is_authenticated:
        return f'user:{current_user.id}'
    return get_remote_address()


_redis_url = os.environ.get('REDIS_URL')
if _redis_url:
    _storage_uri = _redis_url
else:
    log.warning(
        'REDIS_URL not set — rate-limit counters are per-worker (memory). '
        'Set REDIS_URL for shared storage across gunicorn workers.'
    )
    _storage_uri = 'memory://'

limiter = Limiter(
    _rate_limit_key,
    default_limits=['200 per minute'],
    storage_uri=_storage_uri,
)

login_manager = LoginManager()
