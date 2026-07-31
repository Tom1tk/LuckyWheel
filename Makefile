.PHONY: build watch install-js-deps dev test test-db-create test-db-drop test-db-migrate test-db-reset

# One-time: install Babel toolchain
install-js-deps:
	npm install -D @babel/core @babel/cli @babel/preset-react

# Transpile app.jsx → app.js (run after every JSX change)
build: static/app.js

static/app.js: static/app.jsx babel.config.json
	npx babel static/app.jsx -o static/app.js

# Watch mode: auto-rebuild on JSX change
watch:
	npx babel static/app.jsx -o static/app.js --watch

# Run dev server (requires .env)
dev:
	python server.py

# Run the test suite (uses wheeldb_test by default; override with
# DATABASE_URL=postgresql://... if you want a different DB)
test:
	DATABASE_URL=$$(grep ^DATABASE_URL= .env | sed 's|/wheeldb$$|/wheeldb_test|') \
	  python3 -m pytest -q

# ── Test DB (T246) ──────────────────────────────────────────────────────────
# `wheeldb_test` is a clone of the production schema used by the test
# suite. The default pytest flow (above) points at it; these targets let
# you create / reset it without re-running the full test suite.

# Create wheeldb_test (idempotent). Run as the postgres superuser.
test-db-create:
	sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='wheeldb_test'" | grep -q 1 \
	  || sudo -u postgres createdb -O wheelapp wheeldb_test

# Drop wheeldb_test. Use before a full reset.
test-db-drop:
	sudo -u postgres dropdb --if-exists wheeldb_test

# Apply schema.sql + every migration in order. Idempotent: schema.sql uses
# CREATE TABLE IF NOT EXISTS, migrations are wrapped in IF NOT EXISTS / DO
# blocks where they aren't.
test-db-migrate:
	sudo -u postgres psql -d wheeldb_test -f schema.sql
	for m in migrations/0*.sql; do \
	  cat "$$m" | sudo -u postgres psql -d wheeldb_test >/dev/null 2>&1 || \
	    echo "WARNING: $$m failed"; \
	done

# Drop, recreate, and re-migrate from scratch.
test-db-reset: test-db-drop test-db-create test-db-migrate
	@echo "wheeldb_test is fresh; run \`make test\` to use it."

# ── Staging ─────────────────────────────────────────────────────────────────

# Run staging server with gunicorn on port 5001
staging:
	cd /home/user/wheel-app-staging && PORT=5001 gunicorn -c gunicorn.conf.py server:app

# Run staging dev server (Flask built-in) on port 5001
staging-dev:
	cd /home/user/wheel-app-staging && PORT=5001 python server.py

# Apply pending migrations to staging DB
migrate-staging:
	cd /home/user/wheel-app-staging && python migrate.py

# Apply pending migrations to production DB
migrate-prod:
	python migrate.py

# Show migration status for staging
migrate-staging-status:
	cd /home/user/wheel-app-staging && python migrate.py --status

# Show migration status for production
migrate-prod-status:
	python migrate.py --status
