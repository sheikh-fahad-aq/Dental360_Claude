# Legacy route inventory + `appointments_helpers.py` group map

Companion to `be-appointments/SKILL.md`. Load only when you actually have to touch
`360_Flask_Appointment/app/appointment_routes.py` or need to find a helper.

---

## 1. Legacy `/api/appointment/*` — full inventory

File: `360_Flask_Appointment/app/appointment_routes.py` (4403 lines, 192KB — **never read whole**).
Blueprint `appointment_routes`, registered at `app/__init__.py:56` with `url_prefix='/api'`.

**None of these routes has an auth decorator.** `validate_api_key`, `validate_bearer_token`,
`log_api_access` and `allowed_file` are imported at :6 and then never used — each name appears
exactly once in the file, on that import line. Verify:
`grep -c 'validate_api_key' app/appointment_routes.py` → `1`.

**No route in this file is called by `PMS_React`.** Verified by grepping `PMS_React/src` for any
`/appointment/...` path string that is not `v2/appointments` — zero matches.

| Line | Method | Full path | Handler |
|---|---|---|---|
| 132 | POST | `/api/appointment/create` | `create_appointment` |
| 350 | POST | `/api/dentrix/appointment/create` | `dentrix_create_appointment` |
| 548 | GET | `/api/appointment/get/<appointment_id>` | `get_appointment_by_id` |
| 712 | GET | `/api/appointment/get/web/<appointment_id>` | `get_web_appointment_by_id` |
| 920 | POST | `/api/appointment/upload_file` | `upload_file` |
| 966 | GET | `/api/appointment/get_all/<location_id>` | `get_all_appointments` |
| 1135 | GET | `/api/appointment/get_next_week/<location_id>` | `get_next_week_appointments` |
| 1390 | GET | `/api/appointment/get_staff_web/<staff_id>` | `get_staff_web_appointments` |
| 1618 | GET | `/api/appointment/get_by_staff/<staff_id>` | `get_appointments_by_staff` |
| 1718 | POST | `/api/appointment/call-log` | `add_call_log` |
| 1755 | POST | `/api/appointment/call-log/update-status` | `update_call_log_and_status` |
| 1817 | POST | `/api/appointment/update_provider` | `update_or_create_provider` |
| 1887 | PUT | `/api/appointment/update-location` | `update_appointment_location` |
| 1940 | GET | `/api/appointment/provider/<appointment_id>` | `get_provider_by_appointment` |
| 1984 | PUT | `/api/appointment/update/<appointment_id>` | `update_appointment` |
| 2142 | POST | `/api/appointment/create/wp/<clinic_id>` | `create_appointment_from_webhook` (WordPress) |
| 2380 | POST | `/api/appointment/create/ortho` | `create_ortho_appointment` |
| 2960 | GET | `/api/appointment/get_all_web/<clinic_id>/<location_id>` | `get_all_web_appointments_by_location` |
| 3571 | GET | `/api/appointment/get_calendar/<location_id>` | `get_calendar_appointments_by_location` |
| 3740 | GET | `/api/available-appointments` | `get_available_appointments` — **mock**, see §1.1 |
| 3747 | GET | `/api/appointments/by_phone` | `get_appointments_by_phone` |
| 3798 | PUT | `/api/appointment/tool/update_status/<appointment_id>` | `update_appointment_status` |
| 3840 | GET | `/api/get_appointment_by_id_tool` | `get_appointment_by_id_tool` |
| 3908 | GET | `/api/appointment/get_all` | `get_all_appointments_anywhere` |
| 4112 | GET | `/api/appointments/upcoming_appointments` | `get_upcoming_appointments` |
| 4159 | POST, GET | `/api/appointment/update_status` | `update_appointment_status_vapi` |
| 4218 | GET | `/api/appointments/sms_appointments` | `get_sms_nextday_appointments` |
| 4264 | GET | `/api/patient/calllog/<appointment_id>` | `get_patient_calllog` |
| 4336 | GET | `/api/appointment/email-log/<appointment_id>` | `get_email_logs_by_appointment_id` |

29 routes. The path at :350 is written **without** a leading slash
(`"dentrix/appointment/create"`); Flask's blueprint setup joins prefix and rule as
`"/".join((prefix.rstrip("/"), rule.lstrip("/")))`, so it still mounts at
`/api/dentrix/appointment/create`. It works — do not "fix" it and silently change the path.

Handler names collide with V2 by design: `create_appointment` and `update_appointment` exist in
both modules. Endpoints are blueprint-scoped (`appointment_routes.create_appointment` vs
`appointments_v2_routes.create_appointment`), so there is no conflict — but `url_for` and
`grep -n "def create_appointment"` will both find two hits.

### 1.1 Known legacy sharp edges

- `GET /api/available-appointments` (:3740) returns the module-level literal `available_appointments`
  defined at :3732 — a hardcoded Monday–Friday time list. **Mock data, not a real query.**
- Module-level side effects at import time: `openai.OpenAI(...)` client and a hardcoded
  `ASSISTANT_ID` at :26–28, plus `CONNECT_SYSTEM_URL` / `AUTH_SYSTEM_URL` string constants
  at :33–35 (the Auth base is hardcoded here, unlike helpers which read env first).
- `log_appointment_action` (:44) writes `AppointmentLog` and truncates `change_description` /
  `log_type` to 255 chars. V2 uses `AppointmentWorkflowLog` via `create_workflow_log` instead —
  the two audit trails are **separate tables and do not merge**.
- Mixed `asyncio` / `aiohttp` / `requests` calling styles inside one module (`async_request` :111
  vs `sync_post` :121). Prefer the sync path if you must edit.
- Imports are duplicated throughout the header (`requests`, `asyncio`, `aiohttp`, `Blueprint`,
  `datetime` each imported two or three times across :1–40). Harmless, but do not treat the top
  of the file as a map of what the module actually uses.

---

## 2. `app/util/appointments_helpers.py` group map

3680 lines / 128KB. **Do not read whole** — jump with `sed -n 'START,ENDp'`. Groups below are the
top-level definition ranges as they appear in the file.

| Lines | Group | Anchors |
|---|---|---|
| 25–77 | Config constants | `AUTH_SYSTEM_URL` :25, `CHECK_IN_STEPS` :33, `CHECK_OUT_STEPS` :68, `NOTE_TYPES` :77, `PAYMENT_METHODS` :56 |
| 80–201 | Date/time parse, format, duration | `auth_headers` :80, `parse_date` :87, `parse_time` :97, `combine` :111, `end_datetime` :115, `fmt_date` :124, `fmt_time` :128, `duration_minutes_for_appointment` :143 |
| 202–359 | Auth HTTP client + PHI decode | `auth_get` :202, `plain_phi_text` :232, `normalize_auth_patient` :264, `fetch_auth_patient` :304, `auth_post` :330, `auth_put` :345 |
| 360–1378 | **Patient forms** (owned by the forms slice) | `extract_patient_forms_list` :372, `fetch_auth_patient_forms` :644, `fetch_location_check_in_forms_config` :840, `ensure_configured_patient_forms` :969, `build_form_status_tracker` :1138 |
| 1379–1597 | Patient resolve + entity validation | `patient_display_name` :1379, `normalize_v2_create_payload` :1428, `upsert_patient_via_auth` :1463, `resolve_patient_for_create` :1518, `validate_provider` :1572, `validate_operatory` :1585 |
| 1598–1650 | **Conflict detection** | `has_time_conflict` :1598 |
| 1651–2544 | **Availability engine** | `MAX_AVAILABILITY_DAYS` :1659, `operatory_hours_for_date` :1718, `fetch_location_rooms` :1772, `load_busy_appointments` :1814, `fetch_auth_schedule_blocks` :1895, `find_available_slots` :2041, `resolve_availability_targets` :2210, `resolve_availability_advanced` :2414 |
| 2545–2768 | Workflow log, visit, tracking writes | `create_workflow_log` :2545, `get_or_create_visit` :2559, `apply_tracking_status` :2574, `resolve_tracking_status_row` :2630, `set_appointment_tracking_status` :2672 |
| 2769–3272 | **Tracking board** (owned by the tracking slice) | `ALLOWED_LIFECYCLE_STATUSES` :2791, `apply_lifecycle_status` :2814, `build_tracking_summary` :2873, `serialize_status_tracker_list_card` :3094, `build_status_tracker_list_response` :3175 |
| 3273–3680 | Serializers | `build_status_summary` :3273, `serialize_appointment` :3330, `slim_patient` :3392, `build_appointment_insurance` :3422, `slim_provider` :3536, `slim_operatory` :3562, `serialize_procedure` :3584, `serialize_note` :3603, `serialize_visit` :3617, `serialize_workflow_log` :3663, `get_appointment_or_404` :3676 |

### 2.1 Helper gotchas

- **`age_from_dob` is defined twice**: :191 (`dob, on_date=None`) and :3514
  (`dob_value, on_date=None`). Python keeps the last one, so every importer gets :3514. The :191
  definition is dead. Do not add a third; do not assume the one you read at :191 is the live one.
- `auth_headers()` (:80) reads `request.headers` — helpers that call Auth are **request-scoped**
  and cannot run from a background job or the APScheduler tick without a request context.
- `auth_get` returns a `(body, status)` tuple and deliberately returns `None`-ish bodies on 404
  for callers that treat 404 as "missing" (:216–218). Check the status, not just the body.
- `has_time_conflict` filters `Appointment.status.notin_(["cancelled", "no_show", "completed"])`
  — a status spelled `complete` (also legal per `ALLOWED_LIFECYCLE_STATUSES` :2791) will **not**
  be excluded. Unverified whether any live row uses the short spelling.
- `ALLOWED_LIFECYCLE_STATUSES` contains near-duplicates on purpose (`completed`/`complete`,
  `cancelled_by_office`/`cancelledbyoffice`); `_normalize_lifecycle_status` (:2810) lowercases and
  maps spaces/hyphens to underscores before the check.
