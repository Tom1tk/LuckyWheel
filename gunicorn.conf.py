import os
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = 4
worker_class = 'gthread'
threads = 4
timeout = 30
keepalive = 5
# preload_app must be False: psycopg2 connection pools are not fork-safe.
# Each worker calls create_app() → init_pool() independently after fork.
preload_app = False

# Send logs to stdout/stderr (systemd / Docker friendly)
accesslog = '-'
errorlog  = '-'
loglevel  = 'info'
