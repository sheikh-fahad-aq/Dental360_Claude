---
name: be-lab-cases
description: Backend lab case management — lab orders, the per-clinic lab-case status catalog, status audit log, due dates and overdue logic, vendor (lab_id/lab_name) linkage, appointment/patient attachment. Use when changing app/lab_cases_v2_routes.py, adding or debugging a /api/v2/lab-cases, /api/v2/lab-case-statuses or /api/v2/locations/{id}/lab-cases endpoint, or touching LabCase / LabCaseStatus. The React board is fe-labs.
---

## Scope

Lab orders sent to an outside dental laboratory: crown/bridge/denture cases with a case
number, tooth, shade, material, a due date and a clinic-defined status. One flat Flask
module owns the whole lifecycle plus the per-clinic status catalog and its audit log.
**The lab vendor master is NOT here** — `lab_id`/`lab_name` are loose columns on
`lab_case` and the vendor list lives in the external Auth service (`/v2/labs`, reached via
`authApi`). Nor does this slice own the appointment route slip that embeds lab cases
(`appointments_v2_routes.py`). Maturity: **live**.

## Files

| Path | Role |
|---|---|
| `360_Flask_Appointment/app/lab_cases_v2_routes.py` | **(entry)** all 13 routes, serializers, filters. 35KB / 988 lines — `grep`/`sed -n`, do not read whole |

`LabCase` / `LabCaseStatus` / `LabCaseStatusLog` are `be-data-model`'s, at
`360_Flask_Appointment/app/models.py:282-366` — seek there, do not read the 52KB file.
Touches, not owned: `app/__init__.py:47,64` (import + `register_blueprint`, `be-platform`),
`app/util/decorators.py` (`require_api_and_bearer`), and `app/util/appointments_helpers.py`
(`auth_get:202`, `fetch_auth_patient:304`, `validate_provider:1572`, `slim_patient:3392`,
`slim_provider:3536`, `parse_date:87` — `be-appointments`). **Every `PMS_React` file below is
owned by `fe-labs`**, not by this skill; they are listed as the wire contract only.

## Contract

Backend — blueprint `lab_cases_v2_routes`; every path below is served under `/api`:

| Route | Line | Purpose |
|---|---|---|
| `GET /api/v2/lab-cases` | 428 | clinic-wide list, paginated, no patient enrichment |
| `GET /api/v2/locations/<location_id>/lab-cases` | 443 | location board, **with** Auth patient enrichment |
| `POST /api/v2/lab-cases` | 467 | create; may derive fields from `appointment_id` |
| `GET /api/v2/lab-cases/<lab_case_id>` | 563 | single case (`clinic_id` query param required) |
| `PUT /api/v2/lab-cases/<lab_case_id>` | 593 | partial update of any field |
| `DELETE /api/v2/lab-cases/<lab_case_id>` | 700 | **hard delete** |
| `PATCH /api/v2/lab-cases/<lab_case_id>/status` | 723 | status-only change + date auto-stamp |
| `GET /api/v2/lab-cases/<lab_case_id>/status-history` | 775 | audit log, oldest first |
| `GET /api/v2/lab-case-statuses` | 809 | clinic status catalog (`include_inactive=true` widens) |
| `POST /api/v2/lab-case-statuses` | 834 | create status |
| `PUT /api/v2/lab-case-statuses/<status_id>` | 877 | rename / recolor / reorder |
| `DELETE /api/v2/lab-case-statuses/<status_id>` | 930 | **soft** — sets `status='inactive'` |
| `GET /api/v2/lab-cases/options` | 955 | dropdowns: statuses, order_types, shades, materials, labs |

Frontend (all `fe-labs`): `PMS_React/src/api/labCases.js` (193 lines, via `appointmentApi`) maps
1:1 to those routes — `status-history` has no client function and is **currently unconsumed**.
Rendered by `/labs` (`src/pages/Labs.jsx`, 794 lines → `useClinicLabCases` →
`listLocationLabCases`) and the patient chart Labs section (`patient-detail/labs/LabsSection.jsx`
→ `usePatientLabCases` → `listLabCases`); `DocsSection.jsx:445` also reads that hook. Both hooks
sit in `src/hooks/`; the status pill and catalog drawer are in `src/components/labs/`. Vendor
dropdowns come from `src/api/labs.js` `listActiveLabsForDropdown` — the Auth API `/v2/labs`, a
**different backend**, not this one.

## Invariants

1. **Never add `@require_api_and_bearer` to a route here.** Auth is applied blueprint-wide by
   `before_request` at :76-78; every request needs `x-api-key` **and** a valid Bearer token.
2. **`clinic_id` is mandatory on every endpoint** — query param on GET/DELETE, body field
   on POST/PUT/PATCH. Every lookup filters by it; a case is never fetched by id alone.
3. **`status_id` and `status` are written as a pair** — `status` denormalizes
   `lab_case_status.status_name`. Only `_resolve_status` (:207) or the PATCH status route
   may set them; never assign one without the other.
4. **Every status change goes through `_add_status_log` (:178).** It no-ops when
   `status_id` is unchanged, so call it unconditionally — but it must be called.
5. **A `status_id` must belong to the same clinic and be active** — `_status_for_clinic`
   (:169) enforces both; pass `active_only=False` only for read-back serialization.
6. `due_date` is required on create (:512). Date sanity is `_validate_dates` (:241):
   `due_date >= sent_date`, `delivered_date >= received_date`.
7. `case_number` is unique per clinic, case-insensitively; create (:493) and update (:623)
   both return **409** on collision.
8. **`is_overdue` is computed, never stored** (`_serialize_lab_case`:160-165). The closed set
   `delivered / complete / completed / cancelled` is duplicated in the `overdue=true` list
   filter (:340) — change both together.
9. Auth enrichment is best-effort: a failed provider/patient fetch appends to the response
   `warnings[]` array and still returns 200. Never make it a hard error.
10. `per_page` is clamped to 100 (:369); order is `due_date ASC NULLS LAST, created_at DESC`
    (:374-375). Keep both list endpoints on `_paginate_lab_cases`.

## Working here

1. Inventory first: `grep -nE "@[a-z_0-9]+\.route\(" app/lab_cases_v2_routes.py`, then
   `sed -n 'START,ENDp'`. Never open the file whole.
2. New field → column in `models.py` (LabCase, :282) + `_serialize_lab_case` (:124) + create
   body (:517) + update loops (:606 ints / :634 strings / :642 dates).
3. New route → edit `lab_cases_v2_routes.py` only. **No registration change is needed** —
   the blueprint is already registered at `app/__init__.py:64`.
4. Schema change → hand-write an Alembic file in `migrations/versions/` (see Traps #1).
5. Frontend → add the call to `src/api/labCases.js`, then surface it via
   `useClinicLabCases.js` / `usePatientLabCases.js`; pages call the hooks, not the API module
   (except the three status-catalog writes imported directly by `Labs.jsx`).

## Traps

1. **No migration exists for any lab table.** All 20 files in `migrations/versions/` are
   charting revisions; the three lab tables are declared in `models.py` alone.
2. **Two different `_serialize_lab_case` functions** — `lab_cases_v2_routes.py:124` (full:
   `patient`, `provider`, `status_detail`, `is_overdue`) and `appointments_v2_routes.py:171` (thin,
   used only by the route slip at that file's :1445,1600). Editing one does not change the other.
3. **`updated_by` is required on PUT even for non-status edits** (:664) and on PATCH status
   (:730). Omitting it is a 400, not a silent skip.
4. **`_appointment_defaults` (:248) runs on POST only.** It back-fills
   clinic/location/patient/provider from the appointment and 400s on a conflicting value;
   PUT does not re-check, so `appointment_id` can be repointed at a mismatched appointment.
5. **A `status` string matching no active catalog row is accepted** — `_resolve_status`
   (:217-226) stores `status_id=None` plus the raw text. That row renders with no color and
   never matches a `status_id` filter.
6. `SHADES` (:34) is deliberately truncated: VITA 3D-Master and Chromascop are commented out
   at :42-55, so `GET /options` returns VITA Classical + bleach only.
7. Both frontend hooks fall back to `MOCK_LAB_CASES` when the appointment API is off or
   errors (`usePatientLabCases.js:16,79`, `useClinicLabCases.js:15`) and expose a `source`
   field — check it before believing a populated board.

## See also

- `main-architecture` — hub, index, change log
- `be-appointments` — owns `Appointment` and the route slip that embeds lab cases
- `be-data-model` — owns the `LabCase` / `LabCaseStatus` / `LabCaseStatusLog` columns
- `be-recare-waitlist` — sibling V2 flat module, same auth and pagination shape
- `fe-labs` — owns every `PMS_React` file named above (board, chart section, status catalog)
- `references/api-fields.md` — request bodies, query filters, response envelopes
