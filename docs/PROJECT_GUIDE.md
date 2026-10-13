# Multiverse development guide

A Flask alternate-reality simulator where decisions create child universes with deterministic consequences, timelines, insights, and a navigable tree. It uses server-rendered Jinja templates and browser JavaScript.

## Setup

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/flask --app wsgi:app db upgrade
.venv/bin/python run.py
```

Open http://localhost:5000. Set a random `SECRET_KEY` in `.env`; local `DATABASE_URL` defaults to SQLite. The application factory is in `app/__init__.py`, and `wsgi.py` exposes the deployment application.

## Architecture and data flow

`app/routes/` separates auth, main pages, universes, and comparisons. `app/services/` handles account operations, universe branching, consequences, and insights. `app/models.py` defines persisted entities. Templates render server responses; `app/static/js/tree.js` manages tree interactions and the other scripts handle page behavior.

Registration/login establishes a server-side signed session cookie. Mutations require the application's CSRF handling and ownership checks. A decision derives the new universe state deterministically; no language-model provider is involved. The tree and comparison pages read related branches from the database.

## Data, tests, and deployment

Run `.venv/bin/python tests/run_tests.py` for the tracked integration-style checks. Demo/seed scripts alter database records: `reset_demo.py` prompts and is limited to SQLite demo data, while the other seed scripts should be inspected before use. Preserve databases before migrations or resets.

`FLASK_ENV=production` requires a configured secret and rejects SQLite. Use a MySQL-compatible `DATABASE_URL` with PyMySQL and the production WSGI deployment described in `DEPLOYMENT.md`. Set `SESSION_COOKIE_SECURE=true` behind HTTPS. `run.py` is a debug development entry, not the production server. No AWS infrastructure definition is tracked in this default branch.

For troubleshooting, check migration status for missing tables, CSRF/session state for rejected forms, and ownership when a universe is inaccessible. Keep workers/schedulers out of the deployment design unless they are actually added; this version is an ordinary request-driven Flask app.

## More documentation

- [Source, command, and configuration reference](REFERENCE.md)
- [Contributing](../CONTRIBUTING.md)
