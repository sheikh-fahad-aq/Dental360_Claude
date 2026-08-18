# be-platform reference — env vars, pinned versions, CI/CD

Loaded on demand. Everything here was read off the working tree; re-verify before quoting.

## 1. Environment variables actually read

Collected with
`grep -rhoE "os\.(environ\.get|getenv)\(\s*[\"'][A-Z_0-9]+[\"']" app/ config.py run.py`.
27 names, none of them optional-by-design unless noted.

| Var | Read at | Effect if unset |
|---|---|---|
| `FLASK_CONFIG` | `app/__init__.py:17` | defaults to `config.ProductionConfig` |
| `DATABASE_URL` | `config.py:21` | falls back to a **hardcoded production Postgres URL** |
| `SECRET_KEY` | `config.py:8` | literal default — and overwritten anyway at `app/__init__.py:27` |
| `API_KEY` / `api_key` / `X_API_KEY` / `API_KEYS` | `app/util/decorators.py:57` (`_env_api_keys`) | falls through to the `api_keys` table |
| `AUTH_API_BASE_URL`, `AUTH_VALIDATE_TOKEN_URL`, `AUTH_VALIDATE_TOKEN_TIMEOUT` | `decorators.py:33,42` | Bearer validation targets the built-in default host |
| `AUTH_SYSTEM_URL` | `app/util/appointments_helpers.py`, `app/dashboard_routes.py:20` | built-in `https://api.dental360grp.com/api` |
| `AUTH_SECRET_KEY`, `JWT_SECRET_KEY` | `decorators.py:24` (`_jwt_secret`) | local JWT decode path unusable |
| `AUTH_FORMS_TIMEOUT_GET`, `AUTH_FORMS_TIMEOUT_WRITE` | forms proxy helpers | built-in timeouts |
| `OPENAI_API_KEY` | `app/appointment_routes.py:27`, module scope | **the app will not boot** — the constructor raises |
| `CHART_SCHEDULER_ENABLED` | `app/chart_session_scheduler.py:98` | defaults `"true"` |
| `WERKZEUG_RUN_MAIN` | `chart_session_scheduler.py:117` | set by the Werkzeug reloader only; never set here |
| `S3_BUCKET`, `S3_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | `app/util/upload.py:10-13` | `boto3.client` still constructs; uploads 500 |
| `MICROSOFT_CLIENT_ID` / `_CLIENT_SECRET` / `_TENANT_ID` / `_EMAIL` / `_SENDER_EMAIL` | `app/dashboard_routes.py:22-25`, `config.py:27-30` | `/api/emails/read` cannot mint a Graph token — see `be-dashboard` |
| `MAILGUN_API_KEY` / `_API_URL` / `_DOMAIN` | legacy `appointment_routes.py` mail helpers | mail sends fail silently |

All module-level reads happen at **import**, so an `.env` edit needs a process restart.

## 2. Hardcoded secrets already in the tree

Recorded so nobody adds to the list (CLAUDE.md §7.2). Do not reproduce the values.

- `app/__init__.py:27` — `SECRET_KEY` overwritten with a literal *after* `from_object`, so the
  env var is inert and the Flask session cookie is forgeable.
- `config.py:8` — same literal as the `Config.SECRET_KEY` default.
- `app/__init__.py:11-14` — module-level `OpenAI(...)` with an inline `api_key` and a hardcoded
  IP `base_url`. Runs on import of the package.
- `app/__init__.py:21-24` and `config.py:21-23` — full production Postgres credentials as the
  `SQLALCHEMY_DATABASE_URI` fallback, in two places.
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

**No test runner is pinned and none is installed** — not in `env/` and not globally. `tests/`
is plain `unittest`; `python -m pytest` fails with `ModuleNotFoundError`, despite CLAUDE.md §1.

## 4. Container

`Dockerfile` — `python:3.10-slim`, `pip install -r requirements.txt`, `EXPOSE 5000`, and at
`:30`:

```
gunicorn --workers 4 --threads 2 --timeout 120 --bind 0.0.0.0:5000 run:app
```

Four workers × one in-process `init_scheduler` = the chart auto-draft job fires four times per
interval in production. Survivable only because `auto_draft_inactive_sessions` takes
`with_for_update(skip_locked=True)` (`chart_session_scheduler.py:39`). Unresolved.

Port mismatch to know about: `run.py:8` binds **5001** locally, the container binds **5000**.

## 5. `.github/workflows/cicd.yml`

Trigger: `push` to **`main` only** (`:6`). The working branches are `fahad` and
`feature/charting`, so this pipeline never runs on in-flight work. **No test step exists.**

`build` (`ubuntu-latest`): Checkout Source → Log in to Docker Hub → Build Docker Image →
Push Docker Image.

`deploy` (self-hosted runner `appointment-flask`): Check Disk Space Before Cleanup → Clean
Unused Docker Data → Pull Latest Docker Image → Stop and Remove Old Container → Run New Docker
Container (`:87`, the `docker run` at `:91`) → Wait for Application Startup → Verify Container
Status → Check Application Logs → Check Final Container and Disk Status.

The `docker run` passes **no `DATABASE_URL`**, so production silently uses the hardcoded
fallback in `config.py:21`.

## 6. Proving a blueprint is registered

The registration line in `app/__init__.py` is the step that gets forgotten, and nothing reports
it — the route just 404s. Tests will not catch it either: `tests/` builds a bare
`Flask(__name__)` and registers one blueprint by hand
(`tests/test_charting_sessions.py:22-30`); `create_app()` is exercised by no test.

```bash
cd 360_Flask_Appointment
python -c "from app import create_app; [print(r) for r in create_app().url_map.iter_rules()]"
```

Then `python run.py` (port 5001) and call the route with **both** `x-api-key` and a Bearer
token. A 401 means the header pair is wrong; a 404 means step 5 of the recipe was skipped.

## See also

`be-platform/SKILL.md` · `be-data-model` (Alembic chain) · `be-charting` (the scheduler
`create_app()` starts) · `be-dashboard` (the `MICROSOFT_*` consumer).
