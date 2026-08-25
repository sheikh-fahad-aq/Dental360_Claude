# Topology, environment and request path

## Repos

| Path | Repo | Branch (at time of writing) | Notes |
|---|---|---|---|
| `360_Flask_Appointment/` | separate git repo | `fahad` | Flask API, the only backend checked out here |
| `PMS_React/` | separate git repo | `feature/charting` | the SPA |
| `.claude/` | separate git repo | `main` | this tooling; remote `Dental360_Claude.git` |

Three independent histories. A commit never spans two of them. Neither app repo tracks
`.claude/` — both `.gitignore` it.

## How a frontend request becomes a backend request

1. A component calls a domain module in `src/api/` — never `fetch` directly.
2. That module calls one of the four clients in `src/api/client.js`.
3. `buildHeaders` attaches `x-api-key` (always) and `Authorization: Bearer` (when a token
   exists), and sets `credentials: 'include'`.
4. `authApi` and `preAuthApi` emit an absolute URL from their env var.
   `appointmentApi` and `chartApi` emit a **same-origin path** and rely on a proxy.
5. The proxy forwards to the real host — declared in `vite.config.js` (`server.proxy` and
   `preview.proxy`) locally, and in `vercel.json` (`rewrites`) in production.
6. Flask receives it. Every blueprint is mounted at `url_prefix='/api'`, so a SPA path of
   `/__appointment_api/api/v2/appointments` arrives as `/api/v2/appointments`.

**The proxy is declared in three blocks across two files, and all three must change
together** — `server.proxy` (`PMS_React/vite.config.js:49`), `preview.proxy` (`:67`) and
`rewrites` (`PMS_React/vercel.json:3`). Editing only `vite.config.js` breaks production;
editing only `vercel.json` breaks local dev; forgetting `preview.proxy` breaks only
`npm run preview`. No failure shows up in the other environment, so this survives review
easily.

## Environment variables (frontend)

All are `VITE_`-prefixed and **baked into the bundle at build time** — readable by any
visitor. Never put a real secret behind one.

| Variable | Required | Purpose |
|---|---|---|
| `VITE_APP_BASE_URL_AUTH` | yes | 360auth — identity, patients, providers, rooms, services, procedure codes, labs, forms, Stripe Terminal |
| `VITE_APP_BASE_URL_APPOINTMENT` | yes | Appointments API — enables the target and sets the proxy destination; never appears in a browser request |
| `VITE_APP_BASE_URL_CHART` | yes | Charting API — same host as appointments today |
| `VITE_APP_BASE_URL_PRE_AUTH` | yes | Pre-auth / eligibility — insurance, benefits, claims, fee schedules, payer portals |
| `VITE_APP_X_API_Key` | yes | Sent as `x-api-key` on every request to all four backends |
| `VITE_CLINIC_ID` | yes | Clinic scope. Build-time constant — one build serves exactly one clinic |
| `VITE_PROVIDER_ROLE_ID` | no | Overrides the `role_id` used when creating a provider (default 2) |
| `VITE_SCHEDULING_REFERENCE_NOW` | no | Overrides "now" for appointment queries. **Read by the code but absent from `.env.example`** |
| `VITE_API_BASE_URL` | no | Legacy single-base fallback when a target-specific URL is unset |

`.env.example` also lists `VITE_STRIPE_PUBLISHABLE_KEY`, which **no source file reads** —
Stripe Terminal is driven entirely through 360auth and there is no Stripe.js integration.

**Feature gating is by presence, not by flag.** See `CLAUDE.md` §5. Unset a base URL and
that whole domain silently serves mock data.

## Environment (backend)

`config.py` selects a class via `FLASK_CONFIG` (default `config.ProductionConfig`).
`DATABASE_URL` drives the connection; `MICROSOFT_CLIENT_ID` / `MICROSOFT_CLIENT_SECRET` /
`MICROSOFT_TENANT_ID` / `MICROSOFT_SENDER_EMAIL` configure Graph email.

`create_app()` currently hardcodes fallbacks for several of these, including a database
URI, a `SECRET_KEY`, and an LLM client credential. These are recorded as traps in
`be-platform`. Do not add more, and do not reproduce their values into a skill, a commit
message, or a log line.

## Ports and processes

- Backend: `python run.py` → `:5002`, `debug=True`, **`use_reloader=False`**
  (`360_Flask_Appointment/run.py:17-19`). The port is `int(os.getenv("APPOINTMENT_DEV_PORT",
  "5002"))` — 5002 and not 5001 because `PreAuth_Flask` binds 5001 and the two services now
  have to run at the same time: PreAuth's ledger reads charted procedures from this host
  over HTTP. Set `APPOINTMENT_DEV_PORT` if 5002 collides on your machine.
  The reloader is disabled deliberately: `app/chart_session_scheduler.py` starts an
  in-process scheduler from `create_app()`, and a second process would run every job twice.
  The same constraint applies to any multi-worker WSGI deployment.
- Frontend: `npm run dev` → `:5173`. `PreAuth_React` defaults to the same port, so if both
  are running the second one silently takes 5174.

## What is not here

`360auth` and the pre-auth/eligibility API are external services. Their routes, models and
migrations are not in this workspace, and 22 of the 34 domain modules in
`PMS_React/src/api/` target them exclusively. See `api-contract-matrix.md`.
