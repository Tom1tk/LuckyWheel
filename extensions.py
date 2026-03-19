"""Shared Flask extension instances — created here, bound to the app in app.py."""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager

limiter = Limiter(
    get_remote_address,
    default_limits=['200 per minute'],
    storage_uri='memory://',
)

login_manager = LoginManager()
