# multiverse source reference

Source reviewed: [`91710218b4b3`](https://github.com/noel-ult/multiverse/commit/91710218b4b3dcd8a915a1466816b1e07b84882f).

This reference records the checked-in source, scripts, configuration names, and route declarations. It is a navigation aid; service availability and successful test execution require separate verification.

## Configuration names

Names below are declared by source or example files. Example-only entries may be stale; consult the linked reader and project guide before relying on them. Secret values are intentionally omitted.

| Name | Declared/read in |
| --- | --- |
| `DATABASE_URL` | [.env.example](../.env.example), [config.py](../config.py), [tests/run_tests.py](../tests/run_tests.py) |
| `FLASK_APP` | [.env.example](../.env.example) |
| `FLASK_ENV` | [.env.example](../.env.example), [config.py](../config.py) |
| `SECRET_KEY` | [.env.example](../.env.example), [config.py](../config.py) |
| `SESSION_COOKIE_SECURE` | [.env.example](../.env.example), [config.py](../config.py) |

## HTTP route declarations

Paths are **as declared in each source file**. Router/blueprint mount prefixes from the entry point must be prepended; the project guide describes the active entry point and common prefixes. Alternate entry points (such as SQLite) are listed separately by file. Authentication, request bodies, and response schemas live in the linked handlers/models.

| Source | Method | Declared path | Handler |
| --- | --- | --- | --- |
| [app/routes/auth.py](../app/routes/auth.py) | GET, POST | `/register` | `register` |
| [app/routes/auth.py](../app/routes/auth.py) | GET, POST | `/login` | `login` |
| [app/routes/auth.py](../app/routes/auth.py) | POST | `/logout` | `logout` |
| [app/routes/main.py](../app/routes/main.py) | GET | `/` | `index` |
| [app/routes/main.py](../app/routes/main.py) | GET, POST | `/create` | `create_universe` |
| [app/routes/main.py](../app/routes/main.py) | GET | `/universes` | `list_universes` |
| [app/routes/main.py](../app/routes/main.py) | GET | `/explore` | `explore` |
| [app/routes/main.py](../app/routes/main.py) | GET | `/compare/<int:id1>/<int:id2>` | `compare` |
| [app/routes/universe.py](../app/routes/universe.py) | GET | `/universe/<int:universe_id>` | `view_universe` |
| [app/routes/universe.py](../app/routes/universe.py) | POST | `/universe/<int:universe_id>/branch` | `branch_universe` |
| [app/routes/universe.py](../app/routes/universe.py) | GET | `/universe/<int:universe_id>/tree` | `universe_tree_page` |
| [app/routes/universe.py](../app/routes/universe.py) | GET | `/universe/<int:universe_id>/tree.json` | `universe_tree_json` |
| [app/routes/universe.py](../app/routes/universe.py) | GET | `/universe/<int:universe_id>/timeline.json` | `universe_timeline_json` |
| [app/routes/universe.py](../app/routes/universe.py) | GET | `/universe/<int:universe_id>/api` | `universe_api` |

## Existing documentation

Historical plans/reports describe their own revision; use current source when they disagree.

- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [DEPLOYMENT.md](../DEPLOYMENT.md)
- [README.md](../README.md)
- [docs/PROJECT_GUIDE.md](../docs/PROJECT_GUIDE.md)
- [docs/REFERENCE.md](../docs/REFERENCE.md)
- [requirements.txt](../requirements.txt)

## Source and configuration map

Generated lockfiles, binary assets, compiled output, vendored dependencies, and cached bytecode are omitted. Test files remain listed so coverage can be located.

- [.env.example](../.env.example)
- [app/__init__.py](../app/__init__.py)
- [app/models.py](../app/models.py)
- [app/routes/__init__.py](../app/routes/__init__.py)
- [app/routes/auth.py](../app/routes/auth.py)
- [app/routes/comparison.py](../app/routes/comparison.py)
- [app/routes/main.py](../app/routes/main.py)
- [app/routes/universe.py](../app/routes/universe.py)
- [app/services/__init__.py](../app/services/__init__.py)
- [app/services/auth_service.py](../app/services/auth_service.py)
- [app/services/consequence_service.py](../app/services/consequence_service.py)
- [app/services/insight_service.py](../app/services/insight_service.py)
- [app/services/universe_service.py](../app/services/universe_service.py)
- [app/static/css/style.css](../app/static/css/style.css)
- [app/static/js/main.js](../app/static/js/main.js)
- [app/static/js/tree.js](../app/static/js/tree.js)
- [app/static/js/universe.js](../app/static/js/universe.js)
- [app/templates/403.html](../app/templates/403.html)
- [app/templates/404.html](../app/templates/404.html)
- [app/templates/500.html](../app/templates/500.html)
- [app/templates/base.html](../app/templates/base.html)
- [app/templates/compare.html](../app/templates/compare.html)
- [app/templates/create.html](../app/templates/create.html)
- [app/templates/explore.html](../app/templates/explore.html)
- [app/templates/index.html](../app/templates/index.html)
- [app/templates/login.html](../app/templates/login.html)
- [app/templates/register.html](../app/templates/register.html)
- [app/templates/tree.html](../app/templates/tree.html)
- [app/templates/universe.html](../app/templates/universe.html)
- [app/templates/universes.html](../app/templates/universes.html)
- [config.py](../config.py)
- [migrations/env.py](../migrations/env.py)
- [migrations/versions/a33ea7a2997f_create_tables.py](../migrations/versions/a33ea7a2997f_create_tables.py)
- [requirements.txt](../requirements.txt)
- [reset_demo.py](../reset_demo.py)
- [run.py](../run.py)
- [seed.py](../seed.py)
- [seed_dev.py](../seed_dev.py)
- [tests/run_tests.py](../tests/run_tests.py)
- [wsgi.py](../wsgi.py)
