# Visit lifecycle — state tables, helper map, forms call chain

Companion to `be-visit-lifecycle/SKILL.md`. Everything below was read out of the working tree;
line numbers are `360_Flask_Appointment/` unless the path says otherwise.

## 1. The three state axes

| Axis | Column / field | Written by |
|---|---|---|
| Lifecycle | `Appointment.status` | check-in complete, check-out complete, `no-show`, manual `complete` (this slice); `PATCH /v2/appointments/<id>/status` and `cancel` (`be-appointments`) |
| Tracker bucket | `Appointment.tracking_status`, `tracking_status_id`, `tracking_status_changed_at` | `set_appointment_tracking_status` only |
| Wizard progress | `AppointmentVisit.check_in_status` / `check_in_step` / `check_out_status` / `check_out_step` | the two wizard blueprints |

`AppointmentVisit` (`app/models.py:392`) is created lazily by `get_or_create_visit`
(`app/util/appointments_helpers.py:2559`) — one row per appointment, keyed on `appointment_id`.

## 2. Step vocabularies

`CHECK_IN_STEPS` (`appointments_helpers.py:33`) —
`demographics, insurance, payment, forms, handoff, recall` plus legacy aliases `copay` and
`card_on_file`, both normalized onto `payment` at `appointment_checkin_routes.py:122` (and again
for `next_step`, :197). Note the `start_check_in` response still advertises the *old* list
(`demographics, insurance, copay, forms, handoff, recall`, checkin :90–98) — cosmetic only.

`CHECK_OUT_STEPS` (`appointments_helpers.py:68`) —
`visit_summary, insurance_estimate, payment, treatment, recall, post_op_receipt`.

`PAYMENT_METHODS` (:56) — `payment_link, sms, email, card, cash, check, terminal, other, none`.
`_normalize_payment_method` (checkin :34) lowercases, converts spaces and `/` to `_`, and folds
`payment_link_sms_email` / `sms_email` / `link` onto `payment_link`; anything else raises
`ValueError` → 400.

`NOTE_TYPES` (:77) — `staff, clinical, billing, handoff, post_op, general`. Default `staff`.

`AppointmentVisit.check_in_status` / `check_out_status` — `not_started → in_progress → completed`.

## 3. Lifecycle statuses

`ALLOWED_LIFECYCLE_STATUSES` (`appointments_helpers.py:2791`) is the full set the API accepts
(`scheduled, unconfirmed, confirmed, checked_in, completed, complete, cancelled,
cancelled_by_office, cancelledbyoffice, no_show, broken, left_message, unreachable, will_call,
late`) — but that constant is enforced by `apply_lifecycle_status` (:2814), which is used by
`be-appointments`, **not** by this slice. The four handlers here assign `appt.status` directly:

| Handler | Sets `status` | Also stamps |
|---|---|---|
| `complete_check_in` (checkin :240) | `checked_in` | `checked_in_at/by` if null; tracker → `ready` |
| `complete_check_out` (checkout :125) | `completed` | `checked_out_at/by`, `completed_at/by` if null; tracker → `complete` |
| `mark_no_show` (tracking :925) | `no_show` | `no_show_at`, `no_show_by` (unconditional) |
| `mark_completed` (tracking :963) | `completed` | `completed_at/by`, `checked_out_at/by` if null; tracker → `complete` |

## 4. Tracker board

Codes are **rows**, not an enum: `AppointmentTrackingStatus` (`models.py:467`), scoped by
`clinic_id`, with `code`, `status_name`, `color`, `sort_order`, `maps_to_system_status`,
`is_terminal`, `is_default`, `status ∈ {active, inactive}`.

The canonical six-stage order is declared **in the frontend** —
`PMS_React/src/utils/visitStatusTracker.js:16`, `VISIT_TRACKER_STAGES`:

| Stage | `mapsTo` |
|---|---|
| `arriving` | `scheduled` |
| `here` | `scheduled` |
| `ready` | `checked_in` |
| `chair` | `checked_in` |
| `checkout` | `checked_in` |
| `complete` | `completed` |

The backend enforces no ordering: `PATCH .../tracking-status` accepts any active code for the
clinic, forwards or backwards. `SUGGESTED_TRACKING_STATUS_CODES` (`appointments_helpers.py:47`)
lists the same six as a hint and is not validation.

### `set_appointment_tracking_status` (`appointments_helpers.py:2672`)

1. `resolve_tracking_status_row(clinic_id, code=, status_id=)` (:2630).
2. `require_master=True` (default) → unknown code raises `ValueError` listing the clinic's allowed
   codes (`list_tracking_status_codes`, :2650). An invalid `status_id` always raises.
3. Idempotent: same code + (same id or a prior `tracking_status_changed_at`) → returns
   `(False, row)` with no log write.
4. Otherwise `close_open_tracking_logs(appt.id, now)` (:2618) → `apply_tracking_status` (:2574)
   → insert a new `AppointmentTrackingStatusLog` (`models.py:503`).
5. `sync_system_status=True` copies `maps_to_system_status` onto `appt.status` **except** when it
   is `completed`/`complete` (:2749). Every caller in this slice passes `False`.

Set-once milestone stamps in `apply_tracking_status` (:2593–2605): `here → arrived_at`,
`ready → ready_at`, `chair → seated_at`, `checkout → checkout_started_at`. `complete` stamps
nothing — `completed_at` belongs to the lifecycle writes.

### Board feed shapes — `GET /api/v2/appointments/tracking` (tracking :552)

Requires `clinic_id` and `date`. Optional `location_id`, `provider_id(s)`, `operatory_id(s)`,
`patient`/`search`. Three mutually exclusive responses, checked in this order:

1. `summary=true` → `{date, total, tracker}` (counts only). Wins even if `tracking_status` is also
   sent (:585).
2. `tracking_status=<code>` → accordion cards for one bucket; an unknown code is a 400 listing the
   clinic's allowed codes.
3. neither → full `columns[]` board.

`GET /v2/appointments/tracking-summary` (:755) is response shape 1 plus an echoed `filters` block.

`_apply_day_tracker_filters` (:45) is shared by both so counts and lists agree. When `operatory_ids`
is supplied it also matches `operatory_id IS NULL` — deliberate, so legacy rows with no room still
appear in location-wide counts.

`is_arriving_eligible` (`appointments_helpers.py:2859`) restricts the Arriving bucket to
`ARRIVING_ALLOWED_STATUSES` (:2780) and excludes `ARRIVING_EXCLUDED_STATUSES` (:2769).

## 5. Forms proxy call chain

`app/appointment_forms_routes.py` stores nothing. Every request fans out to the Auth API through
`auth_get` / `auth_put` (`appointments_helpers.py:202` / `:345`), which forward the caller's own
`x-api-key` and `Authorization` (`auth_headers`, :80).

1. `fetch_location_check_in_forms_config(location_id, clinic_id)` (:840) → Auth
   `GET /locations/<id>/check-in-forms`. Returns `(config, available, warning, status)`.
   `available=False` means Auth was unreachable — **not** "no forms configured". No `location_id`
   on the appointment → empty config with `available=True`.
2. `fetch_auth_patient_forms(patient_id, appointment_id)` (:644) tries
   `/patients/<id>/forms` then `/v2/patients/<id>/forms`. HTTP 404 counts as *available, empty*.
3. `ensure_configured_patient_forms` (:969) creates missing `PatientForm` rows in Auth for
   configured templates (`request_auth_standard_forms` :730, `request_auth_single_form` :769).
4. `build_form_status_tracker` (:1138) assembles the ordered tracker payload:
   `items`/`forms`, `count`, `required`, `submitted`, `forms_available`, `delivery`,
   `config_template_ids`, `warning`, `auth_status`, `auth_error`, `auth_path`.
5. `update_auth_patient_form` (:806) backs `PUT /api/v2/patient-forms/<id>`.

`_tracker_response` (forms :34) emits `{success, data}` **and** spreads the same keys flat at the
top level for older frontend code, with `items` and `forms` always aliased to each other. Both
shapes are load-bearing.

Status codes are inconsistent by design: `GET .../forms` returns 200 with
`forms_available:false` + `warning` when Auth is down (forms :74–76); `request-all` returns 502
only when the warning text contains "unavailable" (:114); the single-form request returns 502 on
config failure (:158) and 400 `template_not_in_config` when the template is outside the location
config (:164).

Frontend note: `PMS_React/src/api/forms.js` talks to Auth **directly** for template management and
the preferred submit path `POST /v2/patient-forms/<id>/submit` (:216). Appointment and Status
Tracker screens are supposed to use the appointment proxy instead — see the header comment at
`src/api/forms.js:10`.

## 6. Frontend exit-workflow gate (no backend counterpart)

`PMS_React/src/config/exitWorkflowTasks.js:8` — `schedule_recare`, `collect_phone`,
`collect_email`, `collect_payment`. `isExitWorkflowStage` (:44) shows the checklist for stages
`checkout`, `complete`, `completed`. `useExitWorkflowCompleteGate.js` is a **soft** gate: with
`requireReasonForIncompleteTasks` off (default) the user just clicks "Complete anyway".

`collect_payment` is explicitly a proxy on the patient's account/family balance, not a visit
ledger — see the `TEMPORARY PROXY` comment at `exitWorkflowTasks.js:36`.

When the reason flag is on, the frontend attaches `exit_task_skip_reason`, `exit_task_skip_note`
and `exit_task_incomplete` to check-out complete, tracker PATCH and manual complete. **No backend
handler reads these fields** — verified by grepping `exit_task` across the Flask repo (0 hits).

## 7. Frontend callers (maturity **live**)

`PMS_React/README.md:192`; the check-out payment step is a non-interactive Stripe
placeholder (`:222`).

Sole caller is `PMS_React/src/api/appointments.js`, over `/__appointment_api/api`
(`src/api/config.js:15`):

| Surface | Lines in `appointments.js` |
|---|---|
| check-in | :1180–1192 |
| check-out | :1250–1262 |
| tracker (board, PATCH, logs) | :1778–1915 |
| no-show | :982 |
| manual complete | :991 |
| tracker-status master (CRUD) | :1306–1351 |
| visit procedures | :1016–1037 |
| visit notes | :1046–1065 |
| forms | :1126–1173 |

Rendered at `/scheduling` from `src/components/scheduling/`: `AppointmentVisitWizard.jsx`,
`VisitStatusTracker.jsx` (the drawer strip, mounted from `AppointmentDetailDrawer.jsx:2150`),
`VisitStatusBoard.jsx`, `CheckInFormsStep.jsx`, `ExitWorkflowChecklist.jsx`. Board stage order
lives in `src/utils/visitStatusTracker.js:16`; the exit gate is
`src/hooks/useExitWorkflowCompleteGate.js` + `src/config/exitWorkflowTasks.js` (§6 above).
Those files are owned by `fe-scheduling`, not by this skill.
