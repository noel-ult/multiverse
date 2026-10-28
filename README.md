# Multiverse

<!-- documentation-navigation -->
[Developer guide](docs/PROJECT_GUIDE.md) · [Source reference](docs/REFERENCE.md) · [Contributing](CONTRIBUTING.md)
<!-- /documentation-navigation -->


Multiverse is an interactive alternate-reality simulator. Each decision creates a child reality with its own state, consequences, milestones, timeline, and place in a navigable SVG tree.

> Status: actively developed locally. AWS infrastructure is intentionally not deployed yet.

## Why it stands out

Multiverse is designed as a personal **Reality Laboratory**, not a linear game. A user can return to any prior moment, test a contrasting choice, inspect the resulting trade-offs, and compare the realities side by side. The interactive map also includes a searchable Reality Explorer for navigating larger branching timelines.

## Features

- Account registration, login, secure sessions, CSRF protection, and ownership isolation
- Create root realities; branch through deterministic decisions and unlockable paths
- Reality scores, status, state-change panels, consequences, milestones, timelines, siblings, and child paths
- Responsive dashboard, comparison screen, interactive tidy SVG tree with zoom/pan/fit/reset, and accessible empty/error states
- Reality Laboratory command centre, deterministic state insights, and a searchable keyboard-friendly Tree Explorer
- Local canonical demo data and standalone integration-style tests

## Architecture

Flask application factory → blueprints/routes → services (auth, universe, consequence) → SQLAlchemy models → SQLite locally or MySQL-compatible RDS in production. The browser uses server-rendered Jinja views and small vanilla JavaScript modules; no AI or frontend framework is used.

## Local setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/flask --app wsgi:app db upgrade
.venv/bin/python run.py
```

Set `SECRET_KEY` to a long random value. `DATABASE_URL` defaults to `sqlite:///multiverse.db`; use a MySQL PyMySQL URL when needed. Set `SESSION_COOKIE_SECURE=true` only behind HTTPS. Production startup refuses a missing `SECRET_KEY` when `FLASK_ENV=production`.

## Database and tests

```bash
.venv/bin/flask --app wsgi:app db migrate -m "description"
.venv/bin/flask --app wsgi:app db upgrade
.venv/bin/python tests/run_tests.py
```

## Demo data

Run `.venv/bin/python reset_demo.py` and explicitly enter `y`. It refuses non-SQLite databases and resets only the `demo` account. Credentials: `demo` / `demo123`. It creates `START → STUDY → (WORK, SLEEP)` and `START → GO OUT → PLAY GAME` through the real branch service.

## Routes

`/`, `/login`, `/register`, `/logout` (POST), `/universes`, `/explore`, `/create`, `/universe/<id>`, `/universe/<id>/branch` (POST), `/universe/<id>/tree`, `/universe/<id>/timeline.json`, `/compare/<id1>/<id2>`.

## AWS target architecture (not deployed)

Browser → EC2 → Nginx → Gunicorn → Flask → Amazon RDS MySQL

This repository is ready for that deployment stage, but no EC2, RDS, Nginx, HTTPS, domain, or AWS resource is provisioned by this project.

<!-- developer-handbook-20261028 -->
[Developer guide](docs/PROJECT_GUIDE.md) · [Source reference](docs/REFERENCE.md) · [Verification and operations](docs/OPERATIONS.md)
<!-- /developer-handbook-20261028 -->
