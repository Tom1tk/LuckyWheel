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
