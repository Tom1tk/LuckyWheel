import logging
import os
from datetime import timedelta

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

log = logging.getLogger('wheel')


def create_app() -> Flask:
    # Fail fast on missing required env vars
    secret_key = os.environ.get('WHEEL_SECRET_KEY')
    if not secret_key:
        raise RuntimeError(
            'WHEEL_SECRET_KEY is not set. '
            'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise RuntimeError(
            'DATABASE_URL is not set. '
            'Example: postgresql://wheelapp:password@localhost/wheeldb'
        )

    app = Flask(__name__, static_folder='static')
    app.secret_key = secret_key
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=True,
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    )

    # Initialise connection pool
    from db import init_pool
    init_pool(db_url)

    # Initialise extensions (order matters: limiter before blueprints)
    from extensions import limiter, login_manager
    limiter.init_app(app)
    login_manager.init_app(app)

    # Register blueprints (auth also registers @login_manager.user_loader)
    from auth import auth_bp
    from game import game_bp
    from chat import chat_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(chat_bp)

    _SEABED_PATHS = {'/static/seabed-animated.html', '/static/seabed-static.html'}

    # Security headers on every response
    @app.after_request
    def add_security_headers(resp):
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        if request.path in _SEABED_PATHS:
            # These files are embedded as same-origin iframes; they use only
            # inline CSS and no external resources.
            resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
            resp.headers['Content-Security-Policy'] = (
                "default-src 'none'; "
                "style-src 'unsafe-inline';"
            )
        else:
            resp.headers['X-Frame-Options'] = 'DENY'
            resp.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' https://unpkg.com; "
                "style-src 'self' https://fonts.googleapis.com; "
                "font-src https://fonts.gstatic.com; "
                "img-src 'self' data:; "
                "connect-src 'self';"
            )
        return resp

    # JSON error handler for uncaught exceptions (avoids Flask's HTML error pages)
    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return jsonify({'error': e.description}), e.code
        log.exception('UNHANDLED_EXCEPTION')
        return jsonify({'error': 'Internal server error'}), 500

    return app
