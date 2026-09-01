---
name: be-appointments
description: Backend appointment CRUD, availability search and the day/week calendar feed — V2 at /api/v2/appointments plus the frozen legacy /api/appointment/* surface. Use when changing appointments_v2_routes.py, appointment_routes.py or util/appointments_helpers.py, adding or debugging /calendar, /availability, /route-slip, /status or /cancel, or fixing a double-booking 409. Not check-in/check-out or the tracker board (be-visit-lifecycle), not stats (be-dashboard).
---

## Scope

Two appointment APIs live here and only one is current. **`/api/v2/appointments/*` in
`app/appointments_v2_routes.py` is where all new work goes** — it is what `PMS_React` actually
calls (a grep of `PMS_React/src` for any `/appointment/...` path that is not `v2/appointments`
returns nothing). **`app/appointment_routes.py` is legacy and effectively frozen**: 29 routes for
older non-PMS consumers (WordPress webhook, Dentrix import, VAPI/AI phone tools, SMS/email jobs),
with its own hand-rolled Auth calls, `asyncio`/`aiohttp` helpers and `AppointmentLog` writes that
V2 does not use. Do not add routes there, do not port V2 features into it, do not "fix" it unless
a named legacy consumer is broken. This slice owns CRUD, cancel, lifecycle status, availability
search, the calendar feed and the route slip; procedures, notes, check-in/out, the tracking board
and forms are separate blueprints that only share `appointments_helpers.py`.

## Files

| Path | Role |
|---|---|
| `360_Flask_Appointment/app/appointments_v2_routes.py` **(entry)** | V2 API. 74KB / 1841 lines — grep, do not read whole. |
| `360_Flask_Appointment/app/appointment_routes.py` | Legacy `/api/appointment/*`. 192KB / 4403 lines — never read whole. |
| `360_Flask_Appointment/app/util/appointments_helpers.py` | Shared helpers. 128KB / 3680 lines; group map in `references/`. |
| `360_Flask_Appointment/README_V2_APPOINTMENTS.md` | V2 request/response examples. Cite it; do not duplicate payloads. |

Touches (not owned): `app/models.py` (`Appointment` :26, `AppointmentVisit` :392,
`AppointmentWorkflowLog` :447, `AppointmentProcedure` :525), `app/util/decorators.py`, and
`app/__init__.py` (blueprint registration, :56–57).

## Contract

Backend — all under `url_prefix='/api'`; `Line` is in `appointments_v2_routes.py`.

| Route | Purpose | Line |
|---|---|---|
| `GET /api/v2/appointments/calendar` | Day (`date`) or range (`date_from`/`date_to`) feed: appointments, blocks, providers, operatories, statuses | 208 |
| `GET /api/v2/appointments/status-filters` | Status filter chips for the calendar header | 638 |
| `GET /api/v2/appointments` | Patient appointment list, paginated; `patient_id` + `clinic_id` required | 694 |
| `POST /api/v2/appointments/availability` | Find-open-slots search | 872 |
| `POST /api/v2/appointments` | Create — 3 patient payload modes (see README) | 1114 |
| `GET /api/v2/appointments/<id>` | Detail drawer payload | 1309 |
| `GET /api/v2/appointments/<id>/route-slip` | Printable route slip | 1379 |
| `PUT /api/v2/appointments/<id>` | Update / reschedule | 1624 |
| `PATCH /api/v2/appointments/<id>/status` | Lifecycle status change | 1764 |
| `POST /api/v2/appointments/<id>/cancel` | Cancel | 1812 |
| `POST /api/v2/appointments/notify` | Email a patient a **proposed** time — takes a slot, not an id | 1913 |

Legacy `/api/appointment/*` — 29 routes, inventory in `references/legacy-and-helpers.md`.
Frontend (maturity **live**, all files `fe-scheduling`'s): `PMS_React/src/api/appointments.js` is
the only caller (`const BASE = '/v2/appointments'`, :15) over the same-origin proxy
`/__appointment_api/api` (`src/api/config.js:15`). Consumers: `src/context/SchedulingContext.jsx`
(calendar + create), `src/hooks/usePatientAppointments.js`, and in `src/components/scheduling/` —
`CalendarGrid.jsx`, `NewAppointmentModal.jsx`, `RescheduleAppointmentModal.jsx`,
`AppointmentDetailDrawer.jsx`, `FindOpenSlotsDrawer.jsx`, `RouteSlipHost.jsx`. Rendered at
`/scheduling` (`src/components/AppRoutes.jsx:190`). `PATCH /<id>/status` has no caller in
`PMS_React/src`; other consumers unverified.

## Invariants

1. V2 auth is a blueprint-wide `before_request` gate, not a per-route decorator
   (`appointments_v2_routes.py:71–78` → `require_api_and_bearer`), so every V2 route needs **both**
   `x-api-key` and a valid `Authorization: Bearer`. Never decorate an individual V2 route; never
   add one expecting it to be public.
2. Legacy `appointment_routes.py` has **zero** auth decorators (`grep -c '@validate_api_key'` → 0).
   Adding auth there would break its existing consumers — another reason not to touch it.
3. Every status-affecting write reaches `create_workflow_log(...)` (`appointments_helpers.py:2545`)
   — directly for create/update/cancel (:1264, :1733, :1825), via `apply_lifecycle_status` for
   `PATCH /status`. That table is the drawer's audit trail.
4. Scheduling writes must run `has_time_conflict(...)` (`appointments_helpers.py:1598`) and return
   **409** with the conflict payload. It matches operatory **or** provider overlap and skips
   `cancelled` / `no_show` / `completed`. Updates must pass `exclude_appointment_id`.
5. Lifecycle strings must be in `ALLOWED_LIFECYCLE_STATUSES` (`appointments_helpers.py:2791`) and
   applied via `apply_lifecycle_status(...)` (:2814) — never assign `appt.status` directly.
6. Create writes `patient_id` and the legacy `customer_id` to the same value, and defaults
   `patient_phone` to `"N/A"` (both are `NOT NULL`). Keep that dual write.
7. Patients, providers, operatories, services and schedule blocks are **not** in this database.
   They come from the Auth API via `auth_get` / `auth_post` / `auth_put`
   (`appointments_helpers.py:202 / 330 / 345`), which forward the caller's own `x-api-key` and
   `Authorization` (`auth_headers()`, :80). Never query them locally.
8. Every V2 handler wraps its body in `try/except Exception` returning `{"error", "details"}`
   (write handlers `db.session.rollback()` first). The frontend depends on that shape.

## Working here

1. Check no sibling blueprint already serves the path:
   `grep -rn "v2/appointments" 360_Flask_Appointment/app/*.py`.
2. Add the handler in `appointments_v2_routes.py`; no decorator (invariant 1). A *new* blueprint
   must also be registered in `app/__init__.py` — the easy-to-forget step.
3. Put reusable logic in `app/util/appointments_helpers.py`, then add it to the explicit import
   list at `appointments_v2_routes.py:24–63`.
4. Serialize with the existing helpers — `serialize_appointment` (:3330), `slim_patient` (:3392),
   `slim_provider` (:3536), `slim_operatory` (:3562) — so payload shape stays stable.
5. Document it in `README_V2_APPOINTMENTS.md`, then wire `PMS_React/src/api/appointments.js`.

## Traps

- `README_V2_APPOINTMENTS.md` is **stale two ways**: it claims `validate_bearer_token` is
  "currently disabled / commented out" (false — the `before_request` gate enforces it), and its
  index omits `availability`, `status-filters`, `GET /v2/appointments`, `route-slip` and
  `PATCH /<id>/status`. Trust the source.
- `age_from_dob` is defined **twice** in `appointments_helpers.py` (:191 and :3514, different
  signatures). The second shadows the first; importers get the `dob_value` version.
- In `app/util/decorators.py`, `validate_user_role`, `validate_user_dashboard` and `log_api_access`
  reference `Role`/`Dashboard`, defined nowhere — `NameError` if used. Only
  `require_api_and_bearer` is safe.
- `app/appointment_status_routes.py` is a 4-line re-export shim of `appointment_tracking_routes`;
  `no-show` / `complete` live at `appointment_tracking_routes.py:925` and `:963`, not here.
- `GET /api/available-appointments` (`appointment_routes.py:3740`) returns a **hardcoded mock**
  dict defined at :3732. Not real availability — use `POST /v2/appointments/availability`.
- Calendar caps at `MAX_CALENDAR_APPOINTMENTS = 2000` (:68) and sets `truncated` (:332); ranges
  cap at `MAX_AVAILABILITY_DAYS = 31` (`appointments_helpers.py:1659`).
- Calendar provider/operatory filters union the legacy join tables `AppointmentServiceProvider`
  and `AppointmentLocation` (:272–303) — old rows have no `appointment_provider_id`/`operatory_id`,
  so keep both branches.
- **`/notify` is the one route here that neither reads nor writes the database.** It exists for
  the moment BEFORE a booking: the Add Appointment drawer's confirm step has a slot, not an
  appointment, and the coordinator wants the patient to see the time first. So it takes
  `patient_id` + `date` + `time` and no `appointment_id`, and every string it produces says the
  time is being *held* — the body closes with "not confirmed until our office books it". Never
  reword that into a confirmation, and never make it depend on an appointment existing: a patient
  who reads "confirmed" and finds nothing on the schedule is the failure the confirm step exists
  to prevent. Email only; SMS is refused with a reason (the Auth service's SMS path is
  form-specific). Delivery is `send_email` from `appointment_routes`, imported **lazily inside the
  handler** — a module-level import closes an import cycle at start-up. It is the only route in
  this file that touches `html` / `os`, both imported at :4–5.
- **`parse_date` / `parse_time` RAISE on a malformed value; they do not return `None`.** A bare
  `if not parse_date(...)` inside the file-wide `except Exception` answered **500** for what is
  the caller's typo. Wrap both in `except (TypeError, ValueError)` and return 400 — the
  availability route at :872 already does, and `/notify` now does too (:1949).
- Appointment test coverage is **one file**: `tests/test_appointment_notify.py` (11 tests) covers
  `/v2/appointments/notify` only. Everything else in this slice — calendar, availability, create,
  update, cancel — still has none.

## See also

- `main-architecture` — repo hub, skill index and change log. `fe-scheduling` — frontend caller.
- `references/legacy-and-helpers.md` — 29 legacy routes with line numbers + helper group map.
- `be-visit-lifecycle` — shares `appointments_helpers.py`: procedures, notes, check-in/out, the
  tracking-status board, the forms proxy · `be-recare-waitlist` (uses `find_available_slots`) ·
  `be-lab-cases` (the route slip embeds lab cases) · `be-data-model` (`Appointment` + 15
  satellites) · `be-platform` (blueprint registration, `require_api_and_bearer`).
