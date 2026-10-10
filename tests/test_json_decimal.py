"""NUMERIC values must reach the client as JSON numbers, not strings."""
import os
from decimal import Decimal

os.environ.setdefault('WHEEL_SECRET_KEY', 'test')

from flask import jsonify  # noqa: E402

from app import create_app  # noqa: E402


def test_decimal_serialises_as_number():
    app = create_app()
    with app.app_context():
        body = jsonify({'d': Decimal(5) - Decimal(3), 'big': Decimal(10) ** 38, 'f': Decimal('1.5')}).get_json()
    assert body == {'d': 2, 'big': 10 ** 38, 'f': 1.5}
