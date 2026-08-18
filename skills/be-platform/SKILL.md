---
name: be-platform
description: Flask app wiring, config, auth and deploy for the appointment backend — the create_app() blueprint registry, config.py, app/extensions.py, require_api_and_bearer, /api/create_api_key, /api/upload, run.py, Dockerfile, cicd.yml. Use when registering a blueprint, when a route 404s, when changing SECRET_KEY / DATABASE_URL / FLASK_CONFIG, when debugging a 401/403 from x-api-key or Bearer, or when touching app/__init__.py or util/decorators.py. Not models.py or migrations (be-data-model).
---

## Scope

The plumbing every other backend skill sits on: the `create_app()` factory and its
blueprint registry, the config classes, the shared `db`/`migrate` singletons, the auth
decorators, two small utility blueprints (api-key issuing, S3 upload), and the container
+ CI/CD path to production. It owns **no feature routes** — a `be-*` feature skill owns
the logic, this skill owns the two lines in `app/__init__.py` that make it reachable.
Maturity **live** except where marked.

## Files

| Path | Role |
|---|---|
| `360_Flask_Appointment/app/__init__.py` | **(entry)** `create_app()` — config, extensions, 17 `register_blueprint` calls, scheduler start. 78 lines; read whole. |
| `360_Flask_Appointment/config.py` | `Config` / `DevelopmentConfig` / `ProductionConfig`, chosen by `FLASK_CONFIG`, default `config.ProductionConfig` (`app/__init__.py:17`). |
| `360_Flask_Appointment/app/extensions.py` | The `db` and `migrate` singletons. 6 lines. |
| `360_Flask_Appointment/app/util/decorators.py` | **The auth contract.** 319 lines; read whole before changing auth. |
| `360_Flask_Appointment/app/routes.py` | `main` blueprint — one route, `POST /api/create_api_key`. |
| `360_Flask_Appointment/app/util/upload.py` | `upload_bp` — S3 upload; module-level `boto3.client` at line 15. |
| `360_Flask_Appointment/run.py` | Dev WSGI entry; also the gunicorn target (`run:app`). |
| `360_Flask_Appointment/Dockerfile` | python:3.10-slim, gunicorn, `EXPOSE 5000`. |
| `360_Flask_Appointment/requirements.txt` | **UTF-16 LE with BOM** — `grep` sees binary. Use `iconv -f UTF-16LE -t UTF-8`. |
| `360_Flask_Appointment/.github/workflows/cicd.yml` | Build/push image, then deploy on a self-hosted runner. |

Touches `app/models.py` (`ApiKey`, `APILog` — `be-data-model`) and
`app/chart_session_scheduler.py` (started by `create_app`, owned by `be-charting`).

## Contract

Backend — the two routes this slice owns, both **unauthenticated**:

- `POST /api/create_api_key` — mints `secrets.token_hex(32)`, rows into `api_keys`. `app/routes.py:21`
- `GET|POST /api/upload` — multipart to S3, returns a public URL. `app/util/upload.py:27`

Neither is called from `PMS_React` (verified: no match for `create_api_key` or `/upload`
under `PMS_React/src`). The SPA depends on this slice's *headers*, not its routes:
`PMS_React/src/api/client.js:48-56` attaches `x-api-key` (from `VITE_APP_X_API_Key`,
`src/api/config.js:51`) and `Authorization: Bearer <token>` — exactly what
`require_api_and_bearer` checks. Those calls arrive same-origin via
`/__appointment_api/api` and `/__chart_api/api` (`vite.config.js:51,57`; `vercel.json`
rewrites in prod), so they look ordinary to Flask: `CORS(app, ...)` at
`app/__init__.py:33` is not what makes the browser work — the proxy is.

## Invariants

1. **A new blueprint is two edits** — the module, *and* both the import and the
   `register_blueprint(..., url_prefix='/api')` in `app/__init__.py`. Miss the second and
   you get a silent 404 with no log line anywhere.
2. **Everything mounts at `url_prefix='/api'`.** Sole exception is `main`
   (`app/__init__.py:72`), registered bare because its route string already carries
   `/api`. Do not copy that pattern.
3. **`require_api_and_bearer` is the only auth decorator you may apply** — 37 applications
   across 13 modules, most of them one blueprint-wide `before_request` gate rather than a
   per-route decorator. `validate_api_key` / `validate_bearer_token` alone are legacy (only
   `app/appointment_routes.py:6` still imports them).
4. **Never hand-roll an auth check in a route.** `x-api-key` matches an env key
   (`API_KEY`/`api_key`/`X_API_KEY`/`API_KEYS`) first, then the `api_keys` table
   (`decorators.py:85-102`). Bearer is validated by an **outbound HTTP call** to the Auth
   service (`decorators.py:150-176`) — a live network dependency; Auth down means 502.
5. **Import `db` from `app.extensions`.** A second `SQLAlchemy()` breaks Alembic.
6. **Keep the process single.** `init_scheduler` runs from `create_app()`
   (`app/__init__.py:74`); `run.py:8` passes `use_reloader=False` for that reason.
7. **Never add a literal secret.** Violations already present are under Traps; do not
   extend the list. New config reads `os.environ` with a safe default or fails loudly.

## Working here

Registering a new blueprint — the full recipe:

1. Create `app/<feature>_routes.py` with `<feature>_routes = Blueprint("<feature>_routes",
   __name__)`. The Blueprint *name* must be unique app-wide or registration raises.
2. Write route paths **without** `/api` (`@bp.route("/v2/things")` → `/api/v2/things`).
3. Decorate every route with `@require_api_and_bearer` from `app.util.decorators`.
4. In `app/__init__.py`, add the import *inside* `create_app()` (lines 38-54 — they are
   function-local on purpose, to dodge the circular import with `app.routes`).
5. Add `app.register_blueprint(<feature>_routes, url_prefix='/api')` to the block at lines
   56-72. **This is the step that gets forgotten.**
6. New tables: `flask db migrate -m "..."`, then `flask db upgrade`; never edit an applied one.
7. Prove the route exists — the check that catches a missed step 5, plus why no test will:
   `references/deploy-and-env.md` §6. Then `python run.py` (5001), with both headers.

## Traps

- **Hardcoded secrets, live in the tree** — a forgeable `SECRET_KEY`, an inline OpenAI key and
  production Postgres credentials, in five places across `app/__init__.py` and `config.py`.
  Inventory: `references/deploy-and-env.md` §2. Do not reproduce them, do not add more (§7.2).
- **Will not boot without `OPENAI_API_KEY`.** `app/appointment_routes.py:27` calls
  `openai.OpenAI(api_key=...)` at module scope, unguarded; the constructor raises on
  `None`, and that import runs inside `create_app()`.
- **Docker runs 4 workers, the scheduler is in-process.** `Dockerfile:30` is
  `gunicorn --workers 4 --threads 2`, so `init_scheduler` runs in all four and the chart
  auto-draft job fires 4× per interval in production. Unresolved.
- **`DEBUG=True` silently disables the scheduler.** `chart_session_scheduler.py:117`
  returns early when `app.debug` and `WERKZEUG_RUN_MAIN != "true"`; `use_reloader=False`
  means that variable is never set. Only `ProductionConfig` (the default) starts the job.
- **Three decorators are dead and 500 if used.** `validate_user_role`
  (`decorators.py:220`), `validate_user_dashboard` (`decorators.py:248`) and
  `log_api_access` (`decorators.py:288`) reference `Role`/`Dashboard`, neither imported
  there nor defined in `app/models.py`; the `NameError` is swallowed by their own `except`
  and returned as a 500. **There is no working role gating in this backend** (CLAUDE.md §7.7).
- **`/api/create_api_key` is unauthenticated** — anyone who can reach the host can mint a
  valid API key (`app/routes.py:21`). Uploads are world-readable: `app/util/upload.py:43`
  sets `ACL: "public-read"` and keys objects by `secure_filename` alone, so a same-named
  file overwrites the prior one. Neither is PHI-safe.
- **CI runs no tests**, and triggers on push to `main` only (`cicd.yml:6`) — the working
  branches are `fahad` / `feature/charting`, so it never runs on your work. Its `docker
  run` (line 91) passes no `DATABASE_URL`, so production uses the fallback in
  `config.py:21`. Port note: `run.py:8` binds 5001, the container binds 5000.
- **No test runner is installed** — not in `env/`, not globally, not in `requirements.txt`.
  `tests/` is plain `unittest`; `python -m pytest` fails, despite CLAUDE.md §1.
- `routes_backup.py` and `app/appointment_status_routes.py` are dead; the latter is a
  re-export shim registered nowhere.

## See also

`main-architecture` (hub/index) · `be-data-model` (`ApiKey`, `APILog`, migrations) ·
`be-charting` (owns the scheduler `create_app()` starts) · `be-appointments` (owns the
legacy blueprint with the module-level OpenAI client) ·
`references/deploy-and-env.md` (env-var inventory, pinned versions, CI/CD step list).
