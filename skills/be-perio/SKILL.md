---
name: be-perio
description: Backend periodontal charting — perio exams, probing depths, recession, BOP, suppuration, MGJ, furcation, mobility, the bulk measurements upsert, and the draft-final-void lifecycle with carry-forward. Use when changing chart_perio_routes.py or test_chart_perio_exams.py, adding or debugging a /api/v2/charts/perio-exam endpoint, working on ChartPerioExam or ChartPerioMeasurement, or chasing a perio 409/422. Not the odontogram.
---

## Scope

One `chart_perio_exams` header row plus N `chart_perio_measurements` child rows, from "New Perio
Exam" through bulk readings to finalize / reopen / void / soft-delete. No odontogram concepts —
sessions, procedures and the condition catalog belong to `charting_routes.py`. Perio never creates
or closes a chart session; it hangs off one, gates writes on it and touches its activity clock.
Maturity: **live** end to end (`PMS_React/README.md:278`).

## Files

| path | role |
|---|---|
| `360_Flask_Appointment/app/chart_perio_routes.py` | **(entry)** blueprint `chart_perio_routes`; 9 routes, validators, serializers, carry-forward. ~92KB / 1981 lines — `grep -nE "@chart_perio_routes\.route\("` + `sed -n`, never read whole. Lines 1-33 are the authoritative status/write matrix. |
| `360_Flask_Appointment/tests/test_chart_perio_exams.py` | 61 `unittest.TestCase` cases (1721 lines), sqlite + mocked Auth. Run with `unittest`, **not pytest** — pytest is not installed (see `be-charting` step 4). |

Touches, not owned. `be-data-model`'s: `app/models.py:884` `ChartPerioExam` / `:1015`
`ChartPerioMeasurement`, and `migrations/versions/20260813_chart_perio_exams.py`, which creates both tables (`down_revision = "20260812_chart_settings"`). `be-charting`'s: `app/charting_routes.py` (`OPEN_SESSION_STATUSES`, `_add_audit_log`, `_chart_code`, `_current_user_id`, `_positive_int`, `_timestamp`, `_touch_session`, `_utc_now`). `be-platform`'s: `app/__init__.py:52,69` and `app/util/decorators.py`.

## Contract

Backend — every route carries `@require_api_and_bearer` and mounts under `/api`:

| route | line | purpose |
|---|---|---|
| `POST /api/v2/charts/perio-exam` | `:642` | Start a draft exam on an open session. |
| `GET /api/v2/charts/perio-exam?patientId=&locationId=` | `:779` | Picker list, newest first; `measurementCount`, no `measurements`. |
| `GET /api/v2/charts/perio-exam/<exam_id>` | `:846` | One exam **with** every measurement + `previousFinalizedExamId/Date`. |
| `PATCH /api/v2/charts/perio-exam/<exam_id>` | `:957` | Edit the 7 `EXAM_EDITABLE_FIELDS:164`. Draft + open session only. |
| `POST /api/v2/charts/perio-exam/<exam_id>/measurements` | `:1172` | Bulk upsert, ≤256 rows (`MEASUREMENTS_MAX:138`). |
| `POST /api/v2/charts/perio-exam/<exam_id>/finalize` | `:1508` | draft→final; optional body `{carryForwardPrevious}`. |
| `POST /api/v2/charts/perio-exam/<exam_id>/reopen` | `:1643` | final→draft **and** void→draft; clears `finalized_at`. |
| `POST /api/v2/charts/perio-exam/<exam_id>/void` | `:1768` | final→void. Annuls; keeps rows and `finalized_at`. |
| `DELETE /api/v2/charts/perio-exam/<exam_id>` | `:1871` | Soft delete (`deleted_at`), draft or final. |

Which write each status allows, and nothing else (module docstring lines 17-23):
`draft` → measurements, PATCH, finalize, delete · `final` → reopen, void, delete · `void` → reopen
only (back to draft, un-voiding it); measurements, PATCH, finalize, void and delete all 409.

Frontend — `PMS_React/src/api/chartPerio.js` (1175 lines) is the only caller, one export per route
(`createPerioExam:632`, `fetchPerioExams:708`, `fetchPerioExam:740`, `updatePerioExam:872`,
`savePerioMeasurements:919`, `finalizePerioExam:986`, `reopenPerioExam:1051`, `voidPerioExam:1106`,
`deletePerioExam:1158`), riding `chartApi` through the same-origin proxy `/__chart_api`
(`PMS_React/vite.config.js:57,74` + `PMS_React/vercel.json:9`) so `BASE:72` becomes
`/api/v2/charts/perio-exam`. Used by `PMS_React/src/components/patient-detail/charting/`:
`PerioChartPanel.jsx` (list, PATCH, reopen, void) and `perio/PerioExamContext.jsx` (create, read,
save, finalize, delete). **No mock mode** — an unset base rejects with "Perio API is not configured."

## Invariants

1. **Two row shapes in one table, told apart by `site`.** Non-null = probing site (`MB B DB ML L DL`,
   `:88`) with `SITE_MEASUREMENT_FIELDS:176`; null = the per-tooth row with
   `TOOTH_MEASUREMENT_FIELDS:177`. Mixing them is 422 (`_measurement_values:1109`).
2. **`cal` is derived, never stored** (`_cal:384`, `pd + gm`); sending it is a 422. `gm` is signed —
   POSITIVE is recession. Flipping that sign inverts every CAL in the exam.
3. **The measurements endpoint is a full replace per row, not a patch** (`_apply_measurement:1084`):
   a field omitted from an item is written NULL/False, so re-sending a site un-flags what it omits.
4. **One exam per patient per UTC calendar day**, across locations and sessions, 409 backed by a
   partial unique index (`_exam_on_same_day:601`). Void and deleted exams free the day.
5. **`exam_date` is a DAY pinned to UTC midnight** (`_exam_date:307`), immutable after create,
   accepted up to `EXAM_DATE_FUTURE_TOLERANCE:304` (1 day) ahead. Do not tighten it — that rejects
   legitimate same-day exams east of Greenwich; the client is the strict side.
6. **`dateCreated` is `created_at` alone and never falls back to `exam_date`** (`_serialize_exam:423`);
   it drives the frontend created-today gate (`PerioChartPanel.jsx:184`) offering Edit/Delete vs Void.
7. **Session gate is `OPEN_SESSION_STATUSES = ("active","draft")`** (`charting_routes.py:48`), never
   `status == "active"`. `_open_session_for:516` passes `require_open=False` for three amendments
   only — finalize, reopen, delete of a *finalized* exam; on a closed session skip `_touch_session`
   and append `_session_closed_clause:510`.
8. **Every state change writes an audit row** via `_add_audit_log` (`perio_exam_started`/`_updated`/
   `perio_measurements_saved`/`_finalized`/`_reopened`/`_voided`/`_deleted`). A PATCH changing
   nothing is 200, unaudited, not version-bumped (`:1044`).
9. **Carry-forward fills gaps, never overwrites** (`_carry_forward_previous_readings:1431`): missing
   rows are copied whole, existing rows get only their NULL `CARRY_FORWARD_GAP_FILL_COLUMNS:1354`.
   `note` is never carried (`:1353`); flags never land on an existing row.
10. **Unknown keys are 422 everywhere** — body vs `EXAM_FIELDS:140`, PATCH vs
    `EXAM_READ_ONLY_FIELDS:173`, items vs `MEASUREMENT_FIELDS:185`; `reopen`/`void` bodies must be
    empty, `finalize` accepts only `carryForwardPrevious`.
11. **Bounds live in three places and move together:** `chart_perio_routes.py:119-138`, the
    `CheckConstraint`s at `models.py:1002-1012`/`:1099-1147`, `PERIO_BOUNDS` in `chartPerio.js:160`.
    Furcation is **0-4** and JSON, so those two validators are its only guard.
12. **Soft delete only.** `deleted_at` is set; measurement rows are never destroyed or cascaded, and
    `_live_exam:556` is the single definition of "live".

## Working here

1. Inventory first: `grep -nE "@chart_perio_routes\.route\(" app/chart_perio_routes.py`, then `sed -n` just that handler.
2. New exam field → `EXAM_FIELDS:140`, the editable/read-only split (`:164`), a validator,
   `_exam_setting_updates:867`, `_serialize_exam:423`, column + `CheckConstraint` in `models.py`,
   Alembic revision chained off `20260813_chart_perio_exams`.
3. New measurement field → `SITE_`/`TOOTH_MEASUREMENT_FIELDS:176-177`, `_measurement_values:1109`,
   `_apply_measurement:1084`, `_serialize_measurement:399`, carry-forward tuples (`:1322-1363`), model.
4. Mirror on the frontend or the save 422s: `chartPerio.js` `PERIO_SITE_FIELDS:139`,
   `PERIO_TOOTH_FIELDS:142`, `PERIO_BOUNDS:160`, `toPerioMeasurementBody:558`,
   `normalizePerioMeasurement:327`, and `charting/perio/perioExamDefaultsConstants.js`.
5. A new route needs no wiring (`app/__init__.py:69` already registers the blueprint). Extend
   `tests/test_chart_perio_exams.py`; run
   `cd 360_Flask_Appointment && ./env/Scripts/python -m unittest tests.test_chart_perio_exams`.

## Traps

- **`CLINIC_ID = 1` is hardcoded** (`:67`, mirrored in `charting_routes.py` and
  `chart_settings_routes.py`) — no tenancy, so any authenticated user reads and writes any
  practice's exams. All three constants move together when real tenancy lands.
- **`skipConditions` and `bopSupDelay` are recorded but NOT enforced** (`:106`) — validated, stored,
  audited, returned, and acted on nowhere; an extraction socket still asks for all six sites.
- **Void is no longer terminal, yet deleting a void exam still 409s** (`:1871`), and "reopen then
  delete" is no workaround — the reopened exam is a draft, and a draft delete needs an open session.
- **`_previous_finalized_exam:1366` ignores `location_id`** while the picker list filters by it, so
  the server names the carry-forward source on the single-exam read (`_previous_source_fields:1402`).
  Never let the client guess it.
- **Carry-forward 409s on a closed session while a plain finalize succeeds** (`:1572`) — it writes
  measurement rows, so it obeys the measurements gate, not the finalize gate.
- **A duplicate `(tooth, site)` inside one request is 400**, not last-write-wins (`:1220`).

## See also

- `references/measurement-payload.md` — field/bounds tables, carry-forward column split, error map.
- `main-architecture` (hub) · `be-charting` (the sessions perio hangs off, and the shared
  `_add_audit_log`/`_touch_session`) · `be-data-model` (columns, Alembic) · `fe-perio` (the grid UI).
