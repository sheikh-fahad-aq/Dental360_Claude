---
name: be-platform
description: Flask app wiring, config, auth and deploy for the appointment backend — create_app() blueprint registry, config.py, app/extensions.py, require_api_and_bearer, the PUBLIC_ENDPOINTS bypass, /api/create_api_key, /api/upload, run.py, Dockerfile, cicd.yml. Use when registering a blueprint, when a route 404s, when changing SECRET_KEY / DATABASE_URL / FLASK_CONFIG, when debugging a 401/403 from x-api-key or Bearer, or when touching app/__init__.py or util/decorators.py. Not models.py (be-data-model).
---

## Scope

The plumbing every other backend skill sits on: the `create_app()` factory and its blueprint
registry, the config classes, the `db`/`migrate` singletons, the auth decorators, the `/api/*`
JSON error envelope, two utility blueprints (api-key issuing, S3 upload), and the container +
CI/CD path to production. It owns **no feature routes** — a feature skill owns the logic, this
skill owns the two lines that make it reachable. Maturity **live**.

## Files

| Path | Role |
|---|---|
| `360_Flask_Appointment/app/__init__.py` | **(entry)** `create_app()` — config, extensions, 20 `register_blueprint` calls, scheduler start, error handlers. 87 lines; read whole. |
| `360_Flask_Appointment/config.py` | `Config` / `DevelopmentConfig` / `ProductionConfig`, chosen by `FLASK_CONFIG`, default `config.ProductionConfig` (`app/__init__.py:18`). |
| `360_Flask_Appointment/app/extensions.py` | The `db` and `migrate` singletons. 6 lines. |
| `360_Flask_Appointment/app/util/decorators.py` | **The auth contract.** 462 lines; read whole before changing auth. |
| `360_Flask_Appointment/app/util/api_errors.py` | `register_api_json_error_handlers` — any `HTTPException` under `/api` becomes `{success:false,error}` instead of Werkzeug HTML. Registered at `app/__init__.py:84-85`. |
| `360_Flask_Appointment/app/routes.py` | `main` blueprint — one route, `POST /api/create_api_key`. |
| `360_Flask_Appointment/app/util/upload.py` | `upload_bp` — S3 upload; module-level `boto3.client` at line 15. |
| `360_Flask_Appointment/run.py` | Dev WSGI entry; also the gunicorn target (`run:app`). 19 lines. |
| `360_Flask_Appointment/Dockerfile` | python:3.10-slim, gunicorn, `EXPOSE 5000`. |
| `360_Flask_Appointment/requirements.txt` | **UTF-16 LE with BOM** — `grep` sees binary. Use `iconv -f UTF-16LE -t UTF-8`. |
| `360_Flask_Appointment/.github/workflows/cicd.yml` | Build/push image, then deploy on a self-hosted runner. |

Touches `app/models.py` (`ApiKey`, `APILog` — `be-data-model`) and `app/chart_session_scheduler.py` (started by `create_app`, owned by `be-charting`).

## Contract

Backend — the two routes this slice owns, both **unauthenticated**:

- `POST /api/create_api_key` — mints `secrets.token_hex(32)`, rows into `api_keys`. `app/routes.py:21`
- `GET|POST /api/upload` — multipart to S3, returns a public URL. `app/util/upload.py:27`

Neither is called from `PMS_React` (verified). What the SPA depends on is the header pair:
`PMS_React/src/api/client.js:49-56` sets `x-api-key` (`src/api/config.js:52`) and
`Authorization: Bearer <token>`, sent same-origin through the `/__appointment_api` +
`/__chart_api` proxies (`vite.config.js:51,57`, `vercel.json`) — `CORS(app, ...)` at
`app/__init__.py:34` is not what makes the browser work, the proxy is.

## Invariants

1. **A new blueprint is two edits** — the module, *and* both the import and the
   `register_blueprint(..., url_prefix='/api')` in `app/__init__.py`. Miss the second and you
   get a silent 404 with no log line anywhere.
2. **Everything mounts at `url_prefix='/api'`.** Sole exception is `main`
   (`app/__init__.py:79`), bare because its route string already carries `/api`. Do not copy.
3. **`require_api_and_bearer` is the only auth decorator for new work** — 40 applications
   across 15 modules, mostly one blueprint-wide `before_request` gate rather than per-route.
   Two exceptions, neither a precedent: `require_v1_hmac_auth` on v1 create
   (`app/appointments_v1_routes.py:41`, see `be-appointments`) and the public gate in 4.
   `validate_api_key` / `validate_bearer_token` alone are legacy (`appointment_routes.py:6`).
4. **A patient-facing endpoint drops Bearer, never `x-api-key`.** Copy
   `app/treatment_plans_v2_routes.py:184-206`: a module-level `PUBLIC_ENDPOINTS` set of
   `blueprint.function` names, tested in the blueprint `before_request`, falling through to a
   `@validate_api_key`-only gate. Three are on it, all `/api/v2/treatment-plans/shared/<token>`
   (`GET`, `POST .../verify`, `POST .../decisions`), each with its own second factor.
5. **Never hand-roll an auth check in a route.** `x-api-key` matches an env key
   (`API_KEY`/`api_key`/`X_API_KEY`/`API_KEYS`) first, then the `api_keys` table
   (`decorators.py:85-105`); Bearer costs an **outbound HTTP call** to Auth
   (`decorators.py:157`) — a live dependency, so Auth down means 502.
6. **Import `db` from `app.extensions`.** A second `SQLAlchemy()` breaks Alembic.
7. **Keep the process single.** `init_scheduler` runs from `create_app()`
   (`app/__init__.py:81-82`); `run.py:19` passes `use_reloader=False` for that reason.
8. **Never add a literal secret.** Violations present are under Traps; do not extend them.
   New config reads `os.environ` with a safe default or fails loudly.

## Working here

Registering a new blueprint — the full recipe:

1. Create `app/<feature>_routes.py` with `<feature>_routes = Blueprint("<feature>_routes",
   __name__)`. The Blueprint *name* must be unique app-wide or registration raises.
2. Write route paths **without** `/api` (`@bp.route("/v2/things")` → `/api/v2/things`).
3. Gate the whole blueprint with one `before_request` calling a `@require_api_and_bearer`
   no-op (`app/waitlist_v2_routes.py:34-41` is the smallest example), or decorate each route.
4. In `app/__init__.py`, add the import *inside* `create_app()` (lines 39-58 — they are
   function-local on purpose, to dodge the circular import with `app.routes`).
5. Add `app.register_blueprint(<feature>_routes, url_prefix='/api')` to the block at lines
   60-79. **This is the step that gets forgotten.**
6. New tables: `flask db migrate -m "..."`, then `flask db upgrade`; never edit an applied one.
7. Prove it registered — `references/deploy-and-env.md` §6; no test catches a missed step 5.

## Traps

- **`SECRET_KEY` is a committed literal that env cannot override.** `app/__init__.py:28`
  assigns it *after* `app.config.from_object(...)`, so the read at `config.py:8` is inert
  even when the var is set — every Flask session cookie and `itsdangerous` signature this
  app produces is forgeable by anyone holding the repo. Unfixed; the fix is one line.
- **Other hardcoded secrets** — inline OpenAI key + host (`app/__init__.py:11-14`), prod
  Postgres credentials twice (`app/__init__.py:23-25`, `config.py:21-23`). Full inventory:
  `references/deploy-and-env.md` §2. Do not add more (§7.2).
- **Will not boot without `OPENAI_API_KEY`.** `app/appointment_routes.py:27` calls
  `openai.OpenAI(api_key=...)` unguarded at module scope — it raises on `None`, and that
  import runs inside `create_app()`.
- **Docker runs 4 workers, the scheduler is in-process** (`Dockerfile:30`), so the chart auto-draft job fires 4× per interval in production. Unresolved; `references/deploy-and-env.md` §4.
- **`python run.py` never starts the scheduler.** `run.py:19` passes `debug=True`, and
  `chart_session_scheduler.py:117` returns early unless `WERKZEUG_RUN_MAIN == "true"` — never
  set here, because `use_reloader=False`. Only the gunicorn container runs the job.
- **Three role/dashboard decorators are dead and 500 if used** — `decorators.py:355,383,414`
  reference `Role`/`Dashboard`, undefined everywhere; the `NameError` is swallowed and
  returned as a 500. **There is no working role gating in this backend** (CLAUDE.md §7.7).
- **`/api/create_api_key` is unauthenticated** — anyone reaching the host can mint a valid
  API key (`app/routes.py:21`). Uploads are world-readable (`upload.py:43` sets
  `ACL: "public-read"`) and keyed by `secure_filename`, so same names overwrite. Not PHI-safe.
- **CI runs no tests**, and triggers on push to `main` only (`cicd.yml:6`) — never on the
  `fahad` / `feature/charting` branches. Its `docker run` (`:91`) passes no `DATABASE_URL`
  and no `SECRET_KEY`, so production uses the fallbacks in `config.py:21` / `__init__.py:28`.
- **Dev port is 5002, not 5001** — `run.py:17` reads `APPOINTMENT_DEV_PORT` (default 5002);
  the container binds 5000. CLAUDE.md §1 still says 5001 and is stale on this point.
- **pytest lives only in the venv** — `env/Scripts/python -m pytest tests/` works (9.1.1,
  300 tests collect); it is in neither `requirements.txt` nor the global interpreter.
- `360_Flask_Appointment/routes_backup.py` and `app/appointment_status_routes.py` are dead;
  the latter is a re-export shim registered nowhere.

## See also

`main-architecture` (hub/index) · `be-data-model` (`ApiKey`, `APILog`, migrations) ·
`be-charting` (the scheduler `create_app()` starts) · `be-appointments` (legacy blueprint, v1
HMAC) · `be-treatment-plans` (the three public endpoints) · `references/deploy-and-env.md`
(env-var inventory, pinned versions, CI/CD step list).
