# be-platform reference — env vars, pinned versions, CI/CD

Loaded on demand. Everything here was read off the working tree; re-verify before quoting.

## 1. Environment variables actually read

Collected with
`grep -rhoE "os\.(environ\.get|getenv)\(\s*[\"'][A-Za-z_0-9]+[\"']" app/ config.py run.py`.
33 literal names, plus `API_KEY` / `api_key` / `X_API_KEY`, which are read from a tuple in
`_env_api_keys` and so do not appear in that grep.

| Var | Read at | Effect if unset |
|---|---|---|
| `FLASK_CONFIG` | `app/__init__.py:18` | defaults to `config.ProductionConfig` |
| `DATABASE_URL` | `config.py:21` | falls back to a **hardcoded production Postgres URL** |
| `SECRET_KEY` | `config.py:8` | literal default — and overwritten anyway at `app/__init__.py:28` |
| `API_KEY` / `api_key` / `X_API_KEY` / `API_KEYS` | `app/util/decorators.py:61-78` (`_env_api_keys`) | falls through to the `api_keys` table |
| `AUTH_API_BASE_URL`, `AUTH_SYSTEM_URL` | `decorators.py:37-43`, `app/util/appointments_helpers.py:25-27` | built-in `https://api.dental360grp.com/api` |
| `AUTH_VALIDATE_TOKEN_URL` | `decorators.py:46-58` | derived from the base, host-root `/validate_token` |
| `AUTH_VALIDATE_TOKEN_TIMEOUT` | `decorators.py:155` | 15s |
| `AUTH_SECRET_KEY`, `JWT_SECRET_KEY` | `decorators.py:28-34` (`_jwt_secret`) | falls back to the (literal) Flask `SECRET_KEY` |
| `AUTH_FORMS_TIMEOUT_GET`, `AUTH_FORMS_TIMEOUT_WRITE` | `appointments_helpers.py:30-31` | 30s / 45s |
| `V1_API_KEY`, `V1_SECRET_KEY` (+ `APPOINTMENT_V1_API_KEY`, `HMAC_SECRET`, `APPOINTMENT_HMAC_SECRET`) | `decorators.py:227-232` | v1 create returns "V1 auth is not configured" |
| `HMAC_MAX_SKEW_SECONDS` | `decorators.py:246`, `app/appointments_v1_routes.py:99` | 300s |
| `CONNECT_SYSTEM_URL` | `app/appointments_v1_routes.py:47` | built-in Connect host (also hardcoded at `appointment_routes.py:33`) |
| `OPENAI_API_KEY` | `app/appointment_routes.py:25-26`, module scope | **the app will not boot** — the constructor raises |
| `PRACTICE_DENTAL_FRONTEND_URL` | `app/treatment_plans_v2_routes.py:405` | patient share links cannot be built — see `be-treatment-plans` |
| `PATIENT_PORTAL_PRACTICE_NAME` / `_PHONE` | `treatment_plans_v2_routes.py:2360-2361` | practice card on the patient page is blank |
| `CHART_SCHEDULER_ENABLED` | `app/chart_session_scheduler.py:98` | defaults `"true"` |
| `WERKZEUG_RUN_MAIN` | `chart_session_scheduler.py:117` | set by the Werkzeug reloader only; never set here |
| `APPOINTMENT_DEV_PORT` | `run.py:17` | dev server binds **5002** |
| `S3_BUCKET`, `S3_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | `app/util/upload.py:10-13` | `boto3.client` still constructs; uploads 500 |
| `MICROSOFT_CLIENT_ID` / `_CLIENT_SECRET` / `_TENANT_ID` / `_EMAIL` | `app/dashboard_routes.py:22-25` | `/api/emails/read` cannot mint a Graph token — see `be-dashboard` |
| `MICROSOFT_SENDER_EMAIL` | `config.py:30` | `support@dental360grp.com` |
| `MAILGUN_API_KEY` / `_API_URL` / `_DOMAIN` | `app/appointment_routes.py:29-31` | mail sends fail silently |

`AUTH_SYSTEM_URL` at `app/dashboard_routes.py:20` is a **hardcoded literal**, not an env read.

All module-level reads happen at **import**, so an `.env` edit needs a process restart.

## 2. Hardcoded secrets already in the tree

Recorded so nobody adds to the list (CLAUDE.md §7.2). Do not reproduce the values.

- `app/__init__.py:28` — `SECRET_KEY` overwritten with a literal *after* `from_object`, so the
  env var is inert and every Flask session cookie / `itsdangerous` signature is forgeable.
  Highest-severity item in this slice; still unfixed.
- `config.py:8` — same literal as the `Config.SECRET_KEY` default.
- `app/__init__.py:11-14` — module-level `OpenAI(...)` with an inline `api_key` and a hardcoded
  IP `base_url`. Runs on import of the package.
- `app/__init__.py:23-25` and `config.py:21-23` — full production Postgres credentials as the
  `SQLALCHEMY_DATABASE_URI` fallback, in two places.
- `app/appointment_routes.py:28` — a literal OpenAI `ASSISTANT_ID`.
- `.env` is untracked and must stay so.

## 3. Pinned versions (`requirements.txt`)

The file is **UTF-16 LE with BOM** — `grep` reports it as binary. Read it with
`iconv -f UTF-16LE -t UTF-8 requirements.txt`.

```
Flask==3.1.0            Flask-SQLAlchemy==3.1.1   SQLAlchemy==2.0.36
Flask-Migrate==4.0.7    alembic==1.14.0           psycopg2(-binary)==2.9.10
Flask-APScheduler==1.13.1                         Flask-Login==0.6.3
flask-cors==5.0.1       Flask-JWT-Extended==4.7.1 PyJWT==2.10.1
gunicorn==23.0.0        requests==2.32.3          python-dotenv==1.1.0
boto3==1.37.36          openai==1.107.3
```

**No test runner is pinned**, but one is installed *inside the venv*: `env/` has pytest 9.1.1.
`env/Scripts/python -m pytest tests/` collects 300 tests across 9 files; the global 3.10
interpreter has no pytest, so plain `python -m pytest` still fails. `tests/` is plain
`unittest`, which pytest runs unchanged. Nothing pins it, so CI and a fresh clone have no runner.

## 4. Container

`Dockerfile` — `python:3.10-slim`, `pip install -r requirements.txt`, `EXPOSE 5000`, and at
`:30`:

```
gunicorn --workers 4 --threads 2 --timeout 120 --bind 0.0.0.0:5000 run:app
```

Four workers × one in-process `init_scheduler` = the chart auto-draft job fires four times per
interval in production. Survivable only because `auto_draft_inactive_sessions` takes
`with_for_update(skip_locked=True)` (`chart_session_scheduler.py:39`). Unresolved.

Port mismatch to know about: `run.py:17` binds **5002** locally (overridable with
`APPOINTMENT_DEV_PORT`; 5001 is left for `PreAuth_Flask`, which is not in this workspace), while
the container binds **5000**. CLAUDE.md §1 still says 5001.

## 5. `.github/workflows/cicd.yml`

Trigger: `push` to **`main` only** (`:6`). The working branches are `fahad` and
`feature/charting`, so this pipeline never runs on in-flight work. **No test step exists.**

`build` (`ubuntu-latest`): Checkout Source → Log in to Docker Hub → Build Docker Image →
Push Docker Image.

`deploy` (self-hosted runner `appointment-flask`): Check Disk Space Before Cleanup → Clean
Unused Docker Data → Pull Latest Docker Image → Stop and Remove Old Container → Run New Docker
Container (`:87`, the `docker run` at `:91`) → Wait for Application Startup → Verify Container
Status → Check Application Logs → Check Final Container and Disk Status.

The `docker run` (`:91-108`) passes `OPENAI_API_KEY`, `MICROSOFT_*`, `API_KEY`, `S3_*`,
`AWS_*`, `V1_API_KEY`, `V1_SECRET_KEY`, `HMAC_MAX_SKEW_SECONDS` and
`PRACTICE_DENTAL_FRONTEND_URL` — but **no `DATABASE_URL` and no `SECRET_KEY`**, so production
silently uses the hardcoded fallbacks in `config.py:21` and `app/__init__.py:28`.

## 6. Proving a blueprint is registered

The registration line in `app/__init__.py` is the step that gets forgotten, and nothing reports
it — the route just 404s. Tests will not catch it either: `tests/` builds a bare
`Flask(__name__)` and registers one blueprint by hand
(`tests/test_charting_sessions.py:20-29`); `create_app()` is exercised by no test.

```bash
cd 360_Flask_Appointment
python -c "from app import create_app; [print(r) for r in create_app().url_map.iter_rules()]"
```

Then `python run.py` (port 5002) and call the route with **both** `x-api-key` and a Bearer
token. A 401 means the header pair is wrong; a 404 means step 5 of the recipe was skipped.

## See also

`be-platform/SKILL.md` · `be-data-model` (Alembic chain) · `be-charting` (the scheduler
`create_app()` starts) · `be-dashboard` (the `MICROSOFT_*` consumer).
