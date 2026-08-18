# Lab cases V2 — field reference

Companion to `be-lab-cases`. Everything here is read off
`360_Flask_Appointment/app/lab_cases_v2_routes.py` and `app/models.py:282-366`.
All paths are served under `/api` (`app/__init__.py:64`).

## Tables

### `lab_case` (`models.py:282`)

PK `lab_case_id`. Nullable unless noted.

| Column | Type | Notes |
|---|---|---|
| `clinic_id` | int, indexed | nullable in the model, but **required by every route** |
| `location_id` | int, indexed | path-fixed on the location board |
| `appointment_id` | int, indexed | plain int, no FK constraint |
| `patient_id` | int, indexed | **NOT NULL** |
| `provider_id` | int, indexed | validated against Auth on create/provider change |
| `lab_id` | int, indexed | id in the Auth `/v2/labs` vendor master; no FK here |
| `lab_name` | str(150) | free text snapshot of the vendor name |
| `case_number` | str(100), indexed | unique per clinic (enforced in code, not in DB) |
| `order_type` | str(100) | free text; `ORDER_TYPES` (:24) is only a dropdown hint |
| `tooth` / `shade` / `material` | str(50/50/100) | free text |
| `status_id` | int, indexed | → `lab_case_status.id`, no FK constraint |
| `status` | str(50), default `"Ordered"` | denormalized `status_name` |
| `sent_date` / `due_date` / `received_date` / `delivered_date` | date | |
| `notes` | text | |
| `created_by` / `updated_by` | int | user ids, no FK |
| `created_at` / `updated_at` | datetime NOT NULL | `updated_at` has `onupdate` |

### `lab_case_status` (`models.py:327`)

PK `id`. `clinic_id` NOT NULL, `status_name` str(100) NOT NULL, `color` str(50),
`sort_order` int NOT NULL default 0, `status` enum `active|inactive` NOT NULL default
`active`, `user_id` int NOT NULL, `created_at` datetime NOT NULL.
`status_name` is unique per clinic, case-insensitively — enforced in code at :844 (create)
and :894 (update), returning 409.

### `lab_case_status_log` (`models.py:352`)

Append-only. PK `id`; `lab_case_id`, `clinic_id`, `new_status_id`, `new_status_name`,
`changed_by_user_id`, `changed_at` are NOT NULL; `old_status_id` / `old_status_name` are
nullable (first transition). Written only by `_add_status_log` (:178) and never updated or
deleted by any route — deleting a lab case does **not** cascade to its logs.

## List query parameters

Shared by `GET /v2/lab-cases` and `GET /v2/locations/<id>/lab-cases`, applied in
`_apply_lab_case_list_filters` (:303).

| Param | Match |
|---|---|
| `clinic_id` | **required**, positive int |
| `location_id` | exact int — ignored on the location board (path wins) |
| `patient_id`, `appointment_id`, `provider_id`, `lab_id`, `status_id` | exact int |
| `status`, `order_type` | exact, case-insensitive (`lower(col) == lower(value)`) |
| `due_from`, `due_to` | `YYYY-MM-DD`, inclusive range on `due_date` |
| `overdue` | literal string `"true"` only; `due_date < today` and status not closed |
| `search` | ILIKE `%term%` over `case_number`, `lab_name`, `order_type`; if the term is all digits it also matches `patient_id` or `provider_id` exactly |
| `page` | default 1, floored at 1 |
| `per_page` | default 25, clamped to 1..100 |

Ordering is fixed: `due_date ASC NULLS LAST, created_at DESC` (:374-375).

## Request bodies

### `POST /v2/lab-cases` (:467)

Required: `clinic_id`, `patient_id`, `provider_id`, `created_by`, `case_number`,
`order_type`, `due_date`, and **`lab_id` or `lab_name`**.
Optional: `location_id`, `appointment_id`, `tooth`, `shade`, `material`, `notes`,
`sent_date`, `received_date`, `delivered_date`, `status_id` **or** `status`.

`appointment_id` triggers `_appointment_defaults` (:248): the appointment is loaded (404 if
missing) and `clinic_id`, `location_id`, `patient_id` (falling back to
`Appointment.customer_id`), `provider_id` (`appointment_provider_id`) are back-filled when
absent. A supplied value that disagrees with the appointment is a 400.

Status resolution (`_resolve_status`, :207), in order: explicit `status_id` (must be active
and same-clinic, else `ValueError` → 400); else a `status` name matched case-insensitively
against active rows (**no match still succeeds** — `status_id=None`, raw string stored);
else the existing value on update; else the clinic's active row named `Ordered`, else the
literal `"Ordered"` with `status_id=None`.

Errors: 400 missing/invalid, 404 appointment not found, 409 duplicate `case_number`,
500 wrapped.

### `PUT /v2/lab-cases/<id>` (:593)

`clinic_id` and `updated_by` are required on **every** call. All other fields are optional
and applied only when the key is present. `patient_id` and `provider_id`, if present, may
not be null. Dates absent from the body keep their stored value before `_validate_dates`
runs, so a partial date update is still validated against the whole set.

### `PATCH /v2/lab-cases/<id>/status` (:723)

Body: `clinic_id`, `updated_by`, `status_id` — all required. Side effect: when the resolved
`status_name` lower-cases to `received` or `delivered` and the matching date column is
empty, it is stamped with today's UTC date (:751-756). No other route does this.

### Status catalog

`POST /v2/lab-case-statuses` (:834) requires `clinic_id`, `user_id`, `status_name`;
accepts `color`, `sort_order`, `status`. `PUT /v2/lab-case-statuses/<id>` (:877) requires
`clinic_id` and patches only the keys present. `DELETE` (:930) takes `clinic_id` as a query
param and flips `status` to `inactive` — rows already referenced by a lab case keep
rendering, because `_status_for_clinic(..., active_only=False)` is used for read-back.

## Response envelopes

- List: `{ "lab_cases": [...], "pagination": {page, per_page, total, pages}, "warnings": [] }`
- Single / create / update / status: `{ "lab_case": {...}, "warnings": [] }` (create and
  update also carry `"message"`)
- History: `{ "lab_case_id": n, "status_history": [...] }` ordered `changed_at ASC, id ASC`
- Statuses: `{ "statuses": [...] }`
- Options (:955): `{ "statuses", "order_types", "shades", "materials", "labs" }` where
  `labs` is `DISTINCT (lab_id, lab_name)` **drawn from existing lab cases in that clinic** —
  it is not the vendor master, so a vendor with no cases yet never appears
- Errors: `{ "error": "...", "details": "..." }` from `_error` (:81)

Serialized case fields beyond the columns: `patient` (`slim_patient`), `provider`
(`slim_provider`), `status_detail` (the full status row or `null`), `is_overdue` (computed).
`warnings[]` carries per-id Auth-fetch failures such as
`"Provider 12 could not be loaded from Auth service"`.
