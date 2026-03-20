.PHONY: build watch install-js-deps dev

# One-time: install Babel toolchain
install-js-deps:
	npm install -D @babel/core @babel/cli @babel/preset-react

# Transpile app.jsx → app.js (run after every JSX change)
build: static/app.js

static/app.js: static/app.jsx babel.config.json
	npx babel static/app.jsx -o static/app.js

# Watch mode: auto-rebuild on JSX changes
watch:
	npx babel static/app.jsx -o static/app.js --watch

# Run dev server (requires .env)
dev:
	python server.py

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
