"""Entry point — keeps Gunicorn's `server:app` reference working."""
import logging
import os

# Load .env in development (python-dotenv is optional; ignored if not installed)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

from app import create_app  # noqa: E402 (after logging setup)

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
