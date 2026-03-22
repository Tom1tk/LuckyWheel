"""Shared Flask extension instances — created here, bound to the app in app.py."""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, current_user


def _rate_limit_key():
    """Key rate limits by user ID when authenticated, IP otherwise."""
    if current_user and current_user.is_authenticated:
        return f'user:{current_user.id}'
    return get_remote_address()


limiter = Limiter(
    _rate_limit_key,
    default_limits=['200 per minute'],
    storage_uri='memory://',
)

login_manager = LoginManager()
