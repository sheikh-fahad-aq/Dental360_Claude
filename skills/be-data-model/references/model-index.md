# Model index — `360_Flask_Appointment/app/models.py`

38 `db.Model` classes, one flat module, 1150 lines. No model is declared anywhere else in
`app/` (verified: `grep -rn "db.Model" app/ --include=*.py` matches only `models.py`).

Line numbers are `class` statement lines and are true at time of writing. Re-check with:

```bash
grep -nE "^class .*db\.Model|^\s+__tablename__" 360_Flask_Appointment/app/models.py
```

Legend: **A** = table created/managed by an Alembic migration under `migrations/versions/`.
Everything unmarked pre-dates Alembic in this repo — its DDL lives only in the deployed
database, and `models.py` is the only written record of its shape.

---

## Platform / auth

| Line | Class | Table | Purpose |
|---|---|---|---|
| 6 | `APILog` | `api_logs` | Per-request access log written by `log_api_access` — system, endpoint, method, status, `accessed_at`. |
| 17 | `ApiKey` | `api_keys` | Legacy DB-backed `x-api-key` records. Only consulted after the `.env` key set misses (`app/util/decorators.py:78`). |

## Appointments — core

| Line | Class | Table | Purpose |
|---|---|---|---|
| 26 | `Appointment` | `appointment` (implicit) | **The central row.** Scheduling fields, three provider slots, lifecycle timestamps (`checked_in_at` … `no_show_at`), and the Dentrix-style tracker columns (`tracking_status`, `arrived_at`, `ready_at`, `seated_at`). No `__tablename__` — Flask-SQLAlchemy derives `appointment`. |
| 99 | `AppointmentFile` | `appointment_files` | Uploaded attachment metadata: name, title, path, type, size, uploader. |
| 114 | `AppointmentLog` | `appointment_logs` | Free-form per-appointment change log keyed by `appointment_id` + `user_id`. |
| 127 | `CallLog` | `call_logs` | Phone contact attempts against an appointment (`call_type`, `details`). |
| 140 | `AppointmentServiceProvider` | `appointment_service_providers` | Many-to-many join of appointment to provider id. |
| 148 | `PostalLocation` | `postal_locations` | Postal code to location routing table. |
| 161 | `AppointmentLocation` | `appointment_locations` | Location and room (operatory) assignment for an appointment. |
| 172 | `WebAppointment` | `web_appointments` | Public/web-form booking requests before they become an `Appointment`. |
| 191 | `EmailLog` | `email_logs` | Outbound email audit: recipient, subject, both bodies, provider response, `success`. |
| 205 | `WebAppointmentFormData` | `web_appointment_form_data` | Intake payload attached to a web booking (`form_type`, parent contact fields, `patient_dob`). **Contains PHI.** |
| 221 | `TimePatternTemplate` | `time_pattern_template` | Named appointment time patterns per location (`length_minutes`). PK is `time_pattern_id`. |
| 230 | `TimePatternBlock` | `time_pattern_block` | The per-offset symbol blocks that make up one pattern. PK is `time_pattern_block_id`. |
| 239 | `AppointmentNote` | `appointment_note` | Typed notes: `note_type` in staff / clinical / billing / handoff / post_op / general. PK is `appointment_note_id`. |
| 261 | `AppointmentMessageLog` | `appointment_message_log` | Staff message log per appointment. PK is `message_log_id`. |
| 271 | `PatientTextMessage` | `patient_text_message` | Inbound/outbound SMS to a patient (`direction`). PK is `text_message_id`. |
| 525 | `AppointmentProcedure` | `appointment_procedure` | Planned/completed procedures on an appointment. `chart_procedure_id` is the soft link across to `chart_procedures` — the only place the two domains meet. |

## Visit lifecycle (check-in / check-out / tracker)

| Line | Class | Table | Purpose |
|---|---|---|---|
| 392 | `AppointmentVisit` | `appointment_visits` | One row per visit holding the whole check-in and check-out state machine: step, per-step verified booleans, payment amounts/status/method, `linked_recare_id`, and three note bodies. |
| 447 | `AppointmentWorkflowLog` | `appointment_workflow_logs` | Append-only `old_status` to `new_status` transition history with `action` and actor. |
| 467 | `AppointmentTrackingStatus` | `appointment_tracking_status` | Clinic-scoped tracker status definitions (Arriving / Here / Ready / …). |
| 503 | `AppointmentTrackingStatusLog` | `appointment_tracking_status_log` | Dwell time an appointment spent in each tracker status. |

## Labs

| Line | Class | Table | Purpose |
|---|---|---|---|
| 282 | `LabCase` | `lab_case` | The lab case itself. PK is `lab_case_id`. `clinic_id`/`location_id` are **nullable** here, unlike the two tables below. |
| 327 | `LabCaseStatus` | `lab_case_status` | Clinic-configurable status names with `color` and `sort_order`; `status` is a native `status_enum` ('active','inactive'). |
| 352 | `LabCaseStatusLog` | `lab_case_status_log` | Docstring: "Immutable audit history for LabCase status changes." Never update or delete a row here. |

## Recare / waitlist

| Line | Class | Table | Purpose |
|---|---|---|---|
| 372 | `RecareType` | `recare_type` | Recall type lookup. `name` is globally `unique` and there is no `clinic_id`, so a new type is visible to every clinic. |
| 379 | `PatientRecare` | `patient_recare` | A patient's due/overdue recall of a given type. PK is `patient_recare_id`. |
| 757 | `AppointmentWaitlist` | `appointment_waitlist` | ASAP/waitlist queue. `priority` in urgent/flexible/any, `status` in waiting/contacted/accepted/cancelled/scheduled, `queue_type` in asap/waitlist. `scheduled_appointment_id` back-links once booked. |

## Charting **A**

| Line | Class | Table | Purpose |
|---|---|---|---|
| 551 | `Chart` | `charts` | One chart per patient/visit-type stream. `chart_number` is unique and drawn from the Postgres sequence `chart_number_seq`; the comment at :555 says the sequence is global across clinics and gaps are intentional. |
| 576 | `ChartSession` | `chart_sessions` | The editing session and the lock. `object_id` (unique string) is the id every child row stores. Carries the sign/lock JSON arrays (`locked_scopes`, `pending_signature_scopes`, `revision_requested_scopes`, `signatures`) and the contributor/added-id arrays. |
| 612 | `ChartSessionNotes` | `chart_session_notes` | Rendered visit note for a session (`template_id`, `visit_type`, `note_body`, draft/final `status`). See the table-name trap in `SKILL.md`. |
| 635 | `ChartTemplate` | `chart_templates` | Note template per `visit_type` (unique). PK is a `String(64)` id, not an integer. |
| 655 | `ChartAuditLog` | `chart_audit_logs` | Who did what to a chart: `chart_id`, `session_id`, `user_id`, `provider_id`, `action`, `details`. |
| 672 | `ChartCondition` | `chart_conditions` | The condition/finding catalog — SNODENT, SNOMED CT, ICD-10, `procedure_code`, `affected_area`, comment-required flags. Seeded and repeatedly reshaped **by data migrations**, not by any admin endpoint. |
| 700 | `ChartProcedure` | `chart_procedures` | A charted procedure. `type` in TP/Cn/EC/EO (check constraint), `status` is a native Enum, `surfaces` is JSON, `deleted_at` at :747 makes deletion **soft**. |
| 803 | `ChartSetting` | `chart_settings` | Practice-wide chart display policy — **one row per clinic**, enforced by `uq_chart_settings_clinic_id` (:858). Dentition mode, `show_perio_chart`, three recolourable procedure colours (check-constrained to a 7-char `#…` string). Deliberately not scoped by location; the docstring at :804 explains why. |

## Perio **A**

| Line | Class | Table | Purpose |
|---|---|---|---|
| 884 | `ChartPerioExam` | `chart_perio_exams` | Exam header only — the operator's chosen settings, plus a denormalized clinic/location/patient/provider snapshot copied off the locked session. Soft-deleted via `deleted_at` (:1000). The docstring at :885-916 is authoritative: `skip_conditions` and `bop_sup_delay` are **recorded but not enforced**. |
| 1015 | `ChartPerioMeasurement` | `chart_perio_measurements` | Two row shapes in one table, told apart by `site`: `site` NOT NULL is a probing site (MB/B/DB/ML/L/DL) carrying pd/gm/mgj plus flags; `site` NULL is the tooth's own row (present, implant, mobility, bone_loss, furcation, note). **CAL is never stored** — it is derived as pd + gm on read. Check constraints bound pd/mgj/bone_loss to 0–20, gm to -20–20, mobility to 0–3. |

---

## Migration chain

20 files under `360_Flask_Appointment/migrations/versions/`, a single linear chain — no
branches, no merge revisions.

```
20260723_charting (down_revision = None)
 -> 20260724_chart_session_ownership -> 20260728_session_contract
 -> 20260729_chart_audit_logs -> 20260730_chart_conditions
 -> 20260730_add_more_conditions -> 20260730_condition_affected_area
 -> 20260730_chart_procedures -> 20260731_chart_procedure_type
 -> 20260731_chart_procedure_status -> 20260731_chart_proc_delete
 -> 20260731_chart_templates -> 20260731_visit_type_names
 -> 20260804_condition_comments -> 20260804_condition_catalog
 -> 20260805_restore_catalog -> 20260806_surface_scope
 -> 20260806_auto_draft -> 20260812_chart_settings
 -> 20260813_chart_perio_exams          <- head
```

Regenerate with:

```bash
grep -n "^revision\|^down_revision" 360_Flask_Appointment/migrations/versions/*.py
```

The revision **id** often differs from the **filename**: `20260728_clinical_session_contract.py`
declares `revision = "20260728_session_contract"`, and `20260731_chart_procedure_deletion.py`
declares `revision = "20260731_chart_proc_delete"`. Always cite the id, never the filename,
when writing a `down_revision`.

### Tables the chain actually creates

`charts`, `chart_sessions`, `chart_notes`, `chart_templates`, `chart_audit_logs`,
`chart_conditions`, `chart_procedures`, `chart_settings`, `chart_perio_exams`,
`chart_perio_measurements`. Ten tables — the charting and perio domains only.

### Migrations that are data, not schema

- `20260730_chart_condition_options.py` — `op.bulk_insert` seeds the condition catalog.
- `20260804_condition_catalog_mapping.py` — 156 KB, a `CATALOG_ROWS` literal at :13 and an
  `op.bulk_insert` at :517. Never open this file without a line range.
- `20260805_restore_condition_catalog.py` — rewrites 31 catalog rows in place, deletes
  `id >= 32`, and resets the serial sequence.

### Postgres-only migrations

`20260723_charting.py` (guarded by `op.get_bind().dialect.name == "postgresql"`),
`20260804_condition_catalog_mapping.py`, `20260805_restore_condition_catalog.py`
(unguarded `pg_get_serial_sequence`), `20260813_chart_perio_exams.py`.
`config.DevelopmentConfig` is `sqlite:///flask_app.db`, and `migrations/env.py` does not
set `render_as_batch`, so `flask db upgrade` under `FLASK_CONFIG=config.DevelopmentConfig`
is not a supported path.

### Blueprint to model map

Verified with `grep -n "from app.models import\|from .models import" app/*.py`.

| Module | Models imported |
|---|---|
| `app/appointment_routes.py` (legacy) | `Appointment`, `AppointmentFile`, `CallLog`, `AppointmentServiceProvider`, `AppointmentLog`, `PostalLocation`, `AppointmentLocation`, `WebAppointment`, `EmailLog`, `WebAppointmentFormData` |
| `app/appointments_v2_routes.py` | `Appointment`, `AppointmentLocation`, `AppointmentNote`, `AppointmentProcedure`, `AppointmentServiceProvider`, `AppointmentTrackingStatus`, `AppointmentTrackingStatusLog`, `AppointmentVisit`, `AppointmentWorkflowLog`, `LabCase` |
| `app/appointment_tracking_routes.py` | `Appointment`, `AppointmentNote`, `AppointmentTrackingStatus`, `AppointmentTrackingStatusLog`, `AppointmentVisit` |
| `app/appointment_notes_routes.py` | `AppointmentNote` |
| `app/appointment_procedures_routes.py` | `AppointmentProcedure` |
| `app/appointment_checkin_routes.py` | `PatientRecare`, `RecareType` |
| `app/lab_cases_v2_routes.py` | `Appointment`, `LabCase`, `LabCaseStatus`, `LabCaseStatusLog` |
| `app/recare_v2_routes.py` | `Appointment`, `PatientRecare`, `RecareType` |
| `app/waitlist_v2_routes.py` | `AppointmentWaitlist` |
| `app/charting_routes.py` | `Chart`, `ChartAuditLog`, `ChartCondition`, `ChartProcedure`, `ChartSession`, `ChartSessionNotes`, `ChartTemplate` |
| `app/chart_settings_routes.py` | `ChartSetting` |
| `app/chart_perio_routes.py` | `Chart`, `ChartSession`, `ChartPerioExam`, `ChartPerioMeasurement` |
| `app/chart_session_scheduler.py` | `Chart`, `ChartAuditLog`, `ChartSession`, `ChartSessionNotes` |
| `app/dashboard_routes.py` | `AppointmentLocation`, `Appointment` |
| `app/routes.py` | `ApiKey` |

`app/appointment_checkout_routes.py` and `app/appointment_forms_routes.py` import no model
directly — they go through `app/util/appointments_helpers.py`.

## Domain → tables → blueprint → frontend module

Verified via `grep -n "from app.models import" app/*.py` and the `src/api/` module headers.
`appointmentApi` emits `/__appointment_api/api/…`, `chartApi` emits `/__chart_api/api/…`
(`PMS_React/src/api/config.js:15-16`). No frontend code ever names a table.

| Domain | Tables | Blueprint | Frontend module (client) |
|---|---|---|---|
| Appointments | `appointment` + 15 satellites | `appointments_v2_routes.py`, `appointment_routes.py` (legacy) | `src/api/appointments.js`, `appointmentLookups.js` (`appointmentApi`) |
| Visit lifecycle | `appointment_visits`, `appointment_workflow_logs`, `appointment_tracking_status{,_log}` | `appointment_checkin/checkout/tracking_routes.py` | `src/api/appointments.js` |
| Labs | `lab_case`, `lab_case_status`, `lab_case_status_log` | `lab_cases_v2_routes.py` | `src/api/labCases.js` |
| Recare / waitlist | `recare_type`, `patient_recare`, `appointment_waitlist` | `recare_v2_routes.py`, `waitlist_v2_routes.py` | `src/api/appointments.js`, `waitlist.js` |
| Charting | `charts`, `chart_sessions`, `chart_session_notes`, `chart_templates`, `chart_audit_logs`, `chart_conditions`, `chart_procedures`, `chart_settings` | `charting_routes.py`, `chart_settings_routes.py` | `src/api/charting.js`, `chartingCatalog.js`, `chartSettings.js` (`chartApi`) |
| Perio | `chart_perio_exams`, `chart_perio_measurements` | `chart_perio_routes.py` | `src/api/chartPerio.js` (`chartApi`) |
