---
name: be-dashboard
description: Backend read-only reporting and aggregate stats — appointment counts AI vs web, by location and by status, plus a Flask-session dashboard gate and a Microsoft Graph inbox reader. Use when changing dashboard_routes.py, adding or debugging /api/appointments/stats, /stats/by_location, /stats/by_status, /api/appointments/web/stats/*, /api/dashboard/check or /api/emails/read, or when a stats number or filter= preset looks wrong.
---

## Scope

The read-only reporting corner of the appointment backend. Five aggregate endpoints count
rows in the `appointment` table (totals split AI vs web, grouped by location, grouped by
status), and two unrelated tenants share the same module: a Flask-`session` dashboard gate
(`/dashboard/check`) and a Microsoft Graph inbox reader (`/emails/read`). The module writes
nothing to the database — no `db.session.add` or `commit` appears in it. It does not own
appointment CRUD, the status vocabulary, or location records; it only counts what other
blueprints created. Nothing in `PMS_React` currently calls any of these seven routes.

## Files

| Path | Role |
|---|---|
| `360_Flask_Appointment/app/dashboard_routes.py` | **(entry)** 799 lines / ~33KB, 7 routes + 2 module helpers. Grep and `sed -n`; do not read whole. |

Touched, not owned: `app/models.py:26` — `Appointment`, the only table aggregated, whose
`created_at`/`status`/`type`/`location_id` are all **unindexed** (`be-data-model`). `be-platform`'s:
`config.py:26-30`, the `MICROSOFT_*` block on `ProductionConfig` that this module **never reads**
(see Traps); `app/__init__.py:53,71` (import + `register_blueprint`); `app/util/decorators.py`
(available but unused — Invariant 1). Plus `.env` (`MICROSOFT_CLIENT_ID`/`_SECRET`/`_TENANT_ID`).

## Contract

Backend — blueprint `dashboard_routes` (`:27`), all mounted at `url_prefix='/api'`:

- `POST /api/dashboard/check` — matches a client-supplied `profile.dashboards[]` entry named `auth`, writes Flask session keys. `:79`
- `GET  /api/appointments/stats` — one-shot `{total, total_ai, total_web}`. `:126`
- `GET  /api/appointments/stats/by_location` — `locations[]` with per-location total / ai / web, names resolved over HTTP. `:191`
- `GET  /api/appointments/stats/by_status` — `statuses[]`, grouped on `trim(lower(status))`, returned uppercased. `:308`
- `GET  /api/appointments/web/stats/by_status` — same, pre-filtered to `type='web'`. `:398`
- `GET  /api/appointments/web/stats/by_location` — `locations[]` with `total_web` only. `:490`
- `GET  /api/emails/read` — Microsoft Graph mailbox read; `?top&skip&filter&search&folder`. `:681`

Shared stats params: `start_date` + `end_date` (`YYYY-MM-DD`, honoured only together),
`filter` (`today|yesterday|last_7_days|this_week|this_month|last_month`), and `location_id`
(int) — accepted by `/stats`, `/stats/by_status`, `/web/stats/by_status` **only**; the two
`by_location` routes ignore it.

Frontend: **none**. `checkDashboardAccess()` at `PMS_React/src/api/auth.js:62` posts
`/dashboard/check` through `authApi` (`VITE_APP_BASE_URL_AUTH`) — a different host — so it
never reaches this blueprint. A future consumer must go through `appointmentApi` (base
`/__appointment_api/api`, proxied in `vite.config.js:51,68` and `vercel.json:5`).
Maturity: backend routes `live`; frontend coverage `none`; `/dashboard/check` effectively dead.

## Invariants

1. **These seven routes have no auth.** `grep -nE "^@" app/dashboard_routes.py` returns route
   decorators and nothing else. Every new route MUST carry `@require_api_and_bearer`
   (`app/util/decorators.py:206`); retrofitting the existing seven is the standing fix
   (CLAUDE.md §7.7 — authorization is server-side).
2. **Read-only.** No write may be added to this module. Aggregation never mutates.
3. **Every date filter is on `Appointment.created_at`, never `Appointment.date`** (`:164,
   :246, :362, :453, :540`). "today" means *booked* today, not *scheduled* today. Do not
   swap the column without renaming the endpoint.
4. **`start_date` and `end_date` are honoured only as a pair.** One alone applies no filter
   while the response still reports `"filter": "custom"`.
5. **Counts only — never PHI.** Do not add `patient_name`, `patient_id` or a request payload
   to a stats response or to the `print(f"...")` error lines (CLAUDE.md §7.1).
   `/emails/read` already returns full message bodies; do not widen what it exposes.
6. `MICROSOFT_*` are module-level `os.getenv` reads at `:22-25`, evaluated at **import**.
   An `.env` change needs a process restart, not just a reload.
7. A new blueprint is still two edits: the module, and `app/__init__.py` import +
   `register_blueprint(..., url_prefix='/api')` (CLAUDE.md §4.2).

## Working here

1. Locate the route: `grep -nE "@[a-z_0-9]+\.route\(" app/dashboard_routes.py`, then
   `sed -n` that range only.
2. The five stats routes each carry their **own copy** of the ~28-line date-preset ladder
   (`:137, :202, :320, :410, :501`). Changing the preset vocabulary means editing all five,
   or factoring the ladder into one helper in this module first.
3. Change the query, not the envelope — response keys are `total*` / `statuses` /
   `locations` and a new caller will key off them.
4. New route → add `@require_api_and_bearer`; the blueprint itself is already registered.
5. Verify: `cd 360_Flask_Appointment && python run.py`, then curl with `x-api-key`. There is
   **no test coverage** for this module — `tests/` is charting-only.

## Traps

- **Every stats endpoint is a sequential scan.** `Appointment` indexes only `tracking_status_id`
  and `tracking_status` (`models.py:87-90`); no migration adds one for the aggregated columns
  (`grep -rn create_index migrations/versions/` finds no appointment index). `by_status` also
  groups on `func.trim(func.lower(status))`, an expression no plain index serves. Add a
  `created_at` btree and a `lower(status)` expression index before adding another aggregate.
- **N+1 outbound HTTP per location.** `:283` and `:575` `asyncio.run()` a fan-out of
  `GET {AUTH_SYSTEM_URL}/clinic_locations/<id>` (`:268, :561`) — one request per distinct
  location, inside a synchronous Flask request, uncached. Failures are swallowed to
  `"Unknown"`, so a broken Auth host looks like missing data, not an error.
- **`total_ai` counts `status == 'ai'` but `total_web` counts `type == 'web'`** (`:172-173,
  :236-237`) — two different columns. `appointments_v2_routes.py:592` and
  `util/appointments_helpers.py:3300` match "ai" on status *or* type, so this undercounts.
- **`/appointments/web/stats/*` does not read `web_appointments`.** It filters
  `Appointment.type == 'web'` (`:445, :532`); `WebAppointment` (`models.py:172`) is a
  separate table this module never touches.
- **`config.py:26-30` is dead for this module** — `:22-25` read `os.getenv` directly and
  never consult `current_app.config`.
- **`MICROSOFT_EMAIL` is not an `.env` key.** `.env` defines `MICROSOFT_SENDER_EMAIL`; `:25`
  reads `MICROSOFT_EMAIL` and falls back to the hardcoded `it.support@dental360grp.com`, so
  that default is the mailbox actually read.
- **`/emails/read` returns raw HTML in `body`** (`:755`) plus a second N+1 Graph call for
  attachments (`:763`); `extract_main_content_from_html` (`:628`) is a regex tag-stripper, **not**
  a sanitizer — any renderer must obey CLAUDE.md §7.4.
- **`/dashboard/check` is unsafe and unused.** It is the only Flask-`session` writer in this
  blueprint (`:96-104`) and trusts a client-supplied `profile` body with no token check;
  `app/__init__.py:27` hardcodes a well-known placeholder `SECRET_KEY`, overriding `config.py`,
  so the cookie is forgeable. The SPA uses the Auth host's same-named route instead.
- Handlers return `str(e)` to the client (`:188,:305,:395,:487,:596,:799`) — DB errors leak.
- `datetime.utcnow()` throughout — presets are UTC days, not clinic-local days.
- `AppointmentLocation` is imported at `:4` and never used.

## See also

- `main-architecture` — hub index and change log.
- `be-appointments` — owns `Appointment` writes and the `status`/`type` vocabulary these counts
  depend on · `be-visit-lifecycle` — the tracking-status vocabulary · `be-data-model` —
  `Appointment`/`WebAppointment` and the missing indexes · `be-platform` —
  `require_api_and_bearer`, `config.py`, the `SECRET_KEY` trap.
- `references/aggregates-and-email.md` — per-route response shapes, the shared date-preset
  ladder, and the Graph `/emails/read` pipeline.
