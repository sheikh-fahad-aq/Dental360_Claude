---
name: be-visit-lifecycle
description: Backend visit state machine — check-in/check-out wizards, the Arriving/Here/Ready/Chair/Checkout/Complete tracker board, tracking-status logs, no-show/complete, visit notes and procedures, and the Auth forms proxy. Use when changing appointment_checkin_routes.py, appointment_checkout_routes.py, appointment_tracking_routes.py or appointment_forms_routes.py, hitting /check-in, /check-out, /tracking-status or /forms, or debugging the exit-workflow gate. Not the route slip — be-appointments.
---

## Scope

Everything that happens to an appointment **between scheduling and the patient leaving**: the
check-in wizard, the front-desk tracker board, the check-out wizard, and the satellites those
wizards edit (procedures, notes, forms). Six flat blueprints, all at `/api`; create / reschedule /
cancel and the route slip belong to `be-appointments`. Three independent state axes live here and
must never be conflated — invariants 2, 3 and `references/state-machine.md` §1.

## Files

| Path (`360_Flask_Appointment/`) | Role |
|---|---|
| `app/appointment_tracking_routes.py` **(entry)** | Tracker-status master, board feed, PATCH move, status logs, no-show, complete. 37KB / 1012 lines — grep, do not read whole. |
| `app/appointment_checkin_routes.py` | Phase 4 check-in wizard: start / save step / complete. 317 lines. |
| `app/appointment_checkout_routes.py` | Phase 5 check-out wizard. 197 lines. |
| `app/appointment_procedures_routes.py`, `app/appointment_notes_routes.py` | Phase 2 / 3 per-appointment procedure and note CRUD. |
| `app/appointment_forms_routes.py` | Form Status Tracker. Owns **no table** — a proxy over the Auth forms API (invariant 7). |
| `Check_In_Flow.md`, `Check_Out_Flow.md` | ASCII step diagrams for the two wizards. Keep in sync with the step constants. |

Touches, not owned: `app/util/appointments_helpers.py` (where the real logic lives),
`app/util/decorators.py`, `app/models.py`, `app/__init__.py` (:41–46, :58–63), and the
never-registered 4-line re-export shim `app/appointment_status_routes.py`.

## Contract

| Route | Purpose | Line |
|---|---|---|
| `POST /v2/appointments/<id>/check-in/start` · `PUT …/check-in` · `POST …/check-in/complete` | Check-in wizard | checkin :51 / :105 / :240 |
| `POST /v2/appointments/<id>/check-out/start` · `PUT …/check-out` · `POST …/check-out/complete` | Check-out wizard | checkout :31 / :78 / :125 |
| `GET·POST /v2/appointment-tracking-statuses`, `PUT·DELETE …/<status_id>` | Clinic tracker-status master (DELETE deactivates); `…/seed` :360 is **disabled, always 400** | tracking :326 / :401 / :458 / :519 |
| `GET /v2/appointments/tracking` · `GET …/tracking-summary` | Board: `summary=true` counts · `tracking_status=<code>` bucket list · else `columns[]`; `-summary` is counts only | tracking :552 / :755 |
| `PATCH /v2/appointments/<id>/tracking-status` · `GET …/tracking-status-logs` | Move between buckets; per-status durations + history | tracking :796 / :889 |
| `POST /v2/appointments/<id>/no-show` · `POST …/complete` | Terminal lifecycle writes | tracking :925 / :963 |
| `GET·POST /v2/appointments/<id>/procedures` and `…/notes`, `PUT·DELETE` on each `/<row_id>` | Visit procedures; visit notes (`NOTE_TYPES`) | procedures :27/:57/:69/:109 · notes :29/:66/:84/:119 |
| `GET …/forms` · `POST …/forms/request-all` · `POST …/forms/<template_id>/request` · `PUT /v2/patient-forms/<id>` | Form Status Tracker + Auth proxy | forms :54 / :85 / :125 / :204 |

Every path is prefixed `/api`; lines point at the route decorator. Five tracking paths carry a
legacy alias on the same handler (`/v2/appointment-statuses[/…]`, `…/status-tracker`,
`…/tracker-status`, `…/status-logs`) — 19 route decorators over 11 handlers. Models
(`be-data-model`): `AppointmentVisit` :392, `AppointmentWorkflowLog` :447,
`AppointmentTrackingStatus` :467, `AppointmentTrackingStatusLog` :503.

Frontend, maturity **live** (`PMS_React/README.md:192`; the check-out payment step is a
non-interactive Stripe placeholder, :222). Sole caller `PMS_React/src/api/appointments.js`, over
`/__appointment_api/api`, rendered at `/scheduling` by `fe-scheduling`'s wizard, tracker strip and
status board. Per-surface line map: `references/state-machine.md` §7.

## Invariants

1. Each blueprint gates itself with a `before_request` hook wrapping `require_api_and_bearer`
   (checkin :24–31, checkout :21–28, tracking :149–156, notes :19–26, procedures :17–24, forms
   :20–27) — every route needs both `x-api-key` and a Bearer. Never decorate a single route.
2. Only four lifecycle writes are legal here: check-in complete → `checked_in` (checkin :277),
   check-out complete → `completed` (checkout :158), no-show → `no_show` (tracking :941), manual
   complete → `completed` (tracking :987). Nothing else assigns `appt.status`, none has a reverse,
   and each must call `create_workflow_log(...)` (helpers :2545) — the drawer's audit trail.
3. Tracker codes are **clinic data, not an enum**: go through `set_appointment_tracking_status`
   (helpers :2672), which validates against active `AppointmentTrackingStatus` rows for
   `appt.clinic_id`, raises `ValueError` otherwise, and closes the previous log row first so
   exactly one `AppointmentTrackingStatusLog` is ever open (:2731). Never assign
   `appt.tracking_status` or insert a log by hand. Board ordering (arriving → here → ready → chair
   → checkout → complete) is declared in the frontend; the backend takes any active code, any way.
4. Milestone timestamps are **set-once**: `apply_tracking_status` (helpers :2593–2605) stamps
   `arrived_at` / `ready_at` / `seated_at` / `checkout_started_at` only when null, and the wizard
   completions guard `checked_in_at` / `checked_out_at` / `completed_at` with `if not`. Both
   completes are idempotent — 200 "already completed" (checkin :250, checkout :135). Keep both.
5. `sync_system_status` is `False` at every call site here; the wizards set the lifecycle. Even
   when `True`, a tracker row mapping to `completed`/`complete` is refused (helpers :2749), so the
   board can never auto-complete a visit.
6. `appointment_forms_routes.py` persists nothing locally — templates from Auth
   `/locations/<id>/check-in-forms`, rows from `/patients/<id>/forms`; a template outside the
   location config is 400 `template_not_in_config` (forms :164). Do not add a table.
7. Step strings must be in `CHECK_IN_STEPS` (helpers :33) / `CHECK_OUT_STEPS` (:68); `copay` and
   `card_on_file` normalize onto `payment` (checkin :122, :197).
8. **Nothing gates check-out on the backend.** `POST /check-out/complete` succeeds even if
   check-in never ran and every step flag is false. The four exit tasks (recare, phone, email,
   payment) are a frontend soft gate only — `exitWorkflowTasks.js:8`.

## Working here

1. Pick the blueprint by concern (Files table); all six already mount at `/api`. A *new* blueprint
   must be imported **and** registered in `app/__init__.py:41–46` / `:58–63`.
2. Add the handler with no auth decorator (invariant 1); wrap the body in `try/except` with
   `db.session.rollback()` returning `{"error","details"}` — the frontend parses that shape.
3. Load the visit with `get_or_create_visit(appt)` (helpers :2559), never `AppointmentVisit(...)`;
   move buckets only via `set_appointment_tracking_status`; lifecycle only per invariant 2.
4. Put shared logic in `app/util/appointments_helpers.py` and add it to the module's explicit
   import list (e.g. checkin :8–18). Any `app/models.py` change needs an Alembic revision under
   `360_Flask_Appointment/migrations/versions/` — see `be-data-model`.
5. Wire `PMS_React/src/api/appointments.js`, then the wizard or board component; if wizard steps
   changed, update `Check_In_Flow.md` / `Check_Out_Flow.md`.

## Traps

- **Tracker seeding is off.** `DEFAULT_TRACKER_STATUSES = []` (tracking :146) and the seed route
  returns 400 unconditionally (:360). With no `appointment_tracking_status` rows for the clinic,
  `POST /check-in/complete` and `POST /check-out/start` raise inside
  `set_appointment_tracking_status` (codes `ready`/`checkout`) as a generic **500** — create the
  statuses first via `POST /api/v2/appointment-statuses`.
- The frontend sends `exit_task_skip_reason`/`_skip_note`/`_incomplete` on check-out complete,
  tracker PATCH and manual complete (`appointments.js` :1274–1284, :1855–1862, :1004–1010). The
  backend reads **none** (`grep -r exit_task` on the Flask repo → 0 hits).
- `POST /no-show` (:925) sets `appt.status` only — it neither moves the tracker nor closes open tracking logs, so a no-show can sit in the `chair` bucket with a log still open.
- Asymmetry: `check-out/start` sets tracker `checkout`, `check-in/start` touches no tracker — the
  board only advances at `check-in/complete` (→ `ready`). `_apply_system_status_side_effects`
  (tracking :226) and `_ensure_default_statuses` (:298) are **dead**: no call sites.
- Forms degrade unevenly — 200 with `forms_available:false` on `GET …/forms` when Auth is down
  (forms :74–76) vs **502** from the request endpoints (:114, :158); every response carries flat
  aliases *and* a `{success,data}` envelope, both load-bearing. `references/state-machine.md` §5.
- `Check_In_Flow.md` labels step 3 `copay`; the canonical set uses `payment` (helpers :33), and
  `start_check_in` returns the same stale list (checkin :90–98). **No backend tests cover this
  slice** — `360_Flask_Appointment/tests/` is charting only, and pytest is not installed.

## See also

- `main-architecture` (hub) · `be-appointments` (CRUD, calendar, availability, cancel, **route
  slip**; owns `appointments_helpers.py`) · `be-recare-waitlist` (the recare rows the Recall step
  links to) · `be-data-model` (`AppointmentVisit`, tracking-status tables) · `fe-scheduling`.
- `references/state-machine.md` — state tables, transition map, tracker internals, Auth forms call
  chain, the frontend exit-workflow gate, and the per-surface frontend line map (§7).
