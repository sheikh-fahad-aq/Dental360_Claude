# fe-labs — wire format and component inventory

Loaded on demand. Every line here was checked against the working tree; anything unconfirmed is
marked **unverified**. Repo-relative paths are under `PMS_React/`.

## 1. Endpoint ↔ client function

`src/api/labCases.js` — `appointmentApi`, base `/v2/lab-cases` (emitted as
`/__appointment_api/api/v2/lab-cases`). Backend routes and line numbers: `be-lab-cases`.

| Backend route | Function (line) | Notes |
|---|---|---|
| `GET /v2/lab-cases` | `listLabCases` :66 | clinic-wide / patient list; returns the normalized envelope |
| `GET /v2/locations/<id>/lab-cases` | `listLocationLabCases` :93 | **throws `Error('location_id is required')`** on a null id (:95) |
| `GET /v2/lab-cases/<id>` | `getLabCase` :107 | `{ clinicId }` → `?clinic_id=`; returns `data.lab_case ?? data` |
| `POST /v2/lab-cases` | `createLabCase` :115 | |
| `PUT /v2/lab-cases/<id>` | `updateLabCase` :121 | |
| `DELETE /v2/lab-cases/<id>` | `deleteLabCase` :127 | hard delete server-side |
| `PATCH /v2/lab-cases/<id>/status` | `updateLabCaseStatus` :134 | body `{ clinic_id, status_id, updated_by }` |
| `GET /v2/lab-cases/<id>/status-history` | **none** | audit log has no client function and no UI |
| `GET /v2/lab-case-statuses` | `listLabCaseStatuses` :140 | `includeInactive` → `include_inactive=true` |
| `POST /v2/lab-case-statuses` | `createLabCaseStatus` :157 | |
| `PUT /v2/lab-case-statuses/<id>` | `updateLabCaseStatusOption` :162 | rename / recolor / reorder |
| `DELETE /v2/lab-case-statuses/<id>` | `deactivateLabCaseStatus` :167 | soft — sets `status='inactive'` |
| `GET /v2/lab-cases/options` | `getLabCaseOptions` :177 | coerces to `{statuses, order_types, shades, materials, labs}`; tolerates a `SHADES` key |

`src/api/labs.js` — `authApi`, base `/v2/labs` (**the Auth service, not the appointment backend**):
`listLabs` :38, `listActiveLabsForDropdown` :53, `getLab` :71, `createLab` :77, `updateLab` :83,
`toggleLab` :89, `deleteLab` :94 (`{ hard: true }` → `?hard=true`).
`export { isAuthApiEnabled as isLabsApiEnabled }` at :10 — the gate is the *auth* base URL.

### Envelope handling

Each module has its own local `unwrap` (`labCases.js:17`, `labs.js:14`); both throw when
`success === false`, then return `data.data ?? data`. Array responses pass through untouched.
`normalizeLabCasesList` (`labCases.js:34`) is the only real mapper in the slice: it always yields
`{ lab_cases: [], pagination: { page, per_page, total, pages }, warnings: [] }`, synthesising a
single-page envelope when the server returns a bare array. `warnings[]` carries the backend's
best-effort Auth-enrichment failures; **nothing in the UI reads it today.**

## 2. Query params the hooks actually send

Board (`useClinicLabCases.js:190-197`) → `listLocationLabCases(locationId, …)`:
`clinic_id`, `page`, `per_page` (25 from `Labs.jsx:155`), `search` (trimmed, only when non-empty),
then `status_id` **or** `status` (mutually exclusive), then `order_type`.
`Labs.jsx:149-156` passes only `locationId, search, status, activeOnly, page, perPage` — so
`statusId` and `orderType` are dead params from the board's point of view.

Patient (`usePatientLabCases.js`) → `listLabCases({ clinic_id, patient_id, search?, status? })`.
`patient_id` comes from `parsePatientIdForApi(patientId)`; a non-numeric id forces the mock branch.

Never sent by either hook: `due_from`, `due_to`, `overdue`, `provider_id`. They exist server-side
and in the JSDoc (`labCases.js:55-65,74-92`) but have no UI.

## 3. Hook return shape and `source`

Both hooks return exactly:

```
{ cases, options, pagination, loading, error, source, isApiEnabled,
  refetch, addCase, editCase, changeStatus, removeCase }
```

Note `cases`, not the repo's usual `items`. `changeStatus(labCaseId, statusId, updatedBy)`;
`addCase(body)` / `editCase(labCaseId, body)` / `removeCase(labCaseId)`. Every mutator has a
mock branch that mutates local state and returns without a request.

`source` values, by hook:

| Hook | `'mock'` | `'api'` | `'mock-fallback'` |
|---|---|---|---|
| `useClinicLabCases` | `:170` — API off | `:180` no location · `:232` success · **`:237` catch** | never |
| `usePatientLabCases` | `:108` — API off or non-numeric id | `:144` success | **`:155` catch** |

`'mock-fallback'` is outside the workspace's documented `'api' | 'mock' | 'api-partial'` set
(CLAUDE.md §5). Only `DocsSection.jsx:488` tests it (via `labSource !== 'api'`); `LabsSection.jsx`
and `Labs.jsx` ignore `source` entirely and gate on `isApiEnabled` only.

## 4. Mock data

`useClinicLabCases.js:15` and `usePatientLabCases.js:16` each declare their own `MOCK_LAB_CASES`.
The patient copy is a single row that reads as a genuine order: `case_number 'D-360'`,
`order_type 'Bridge'`, `tooth '14'`, `shade 'A2'`, `material 'Zirconia'`, `lab_name 'Dental 360'`,
`provider { id: 1, name: 'Mohammed Parvez' }`, `status 'Ordered'`, `sent_date '2026-07-21'`,
`due_date '2026-08-04'`, `notes 'Special instructions'`. On the error path it is re-stamped with the
real `patient_id` (`:148`).

`DEFAULT_OPTIONS` (`:42` / `:40`) supplies three fallback statuses — Ordered `#3B82F6`,
Received `#22C55E`, Delivered `#6B7280` — plus order types, shades and materials. These fill the
dropdowns whenever `GET /options` returns empty, **including in live mode**, so a populated Shade
list is not evidence that the options endpoint answered.

## 5. Components

**`LabCaseStatusesDrawer`** (`components/labs/LabCaseStatusesDrawer.jsx:272-282`) — fully controlled:
`{ open, statuses, loading, error, onClose, onReload, onCreate, onUpdate, onDelete }`. It fetches
nothing; it copies `statuses` into local `drafts` on open (`:287-292`), locks `body` scroll and binds
Escape (`:294-300`). `PRESET_COLORS` (:25-34) are the eight swatch options. Handlers must re-throw so
the drawer can restore its row — `Labs.jsx:303-333` and `LabsSection.jsx` both do.

**`LabStatusSelect`** (`components/labs/LabStatusSelect.jsx:25`) — the inline status pill used in
both tables. Portals a `position: fixed` listbox measured against the trigger, styled with
`colorToRgba(selected.color, …)`. Hardcodes `z-[90]` at :158 rather than using
`OVERLAY_Z_INDEX.modalPanel` (same numeric value, `ui/OverlayBackdrop.jsx:16`).

**`LabOrderDrawer`** (`components/patient-detail/labs/LabOrderDrawer.jsx`, 929 lines) — the only lab
component that calls the API directly rather than through a hook: `getLabCase` :295 (re-read on
open), `fetchPatientCore` :336, `getProviders(clinicId, selectedLocation?.id)` :412. Modes
`create | view | edit`. Payload assembly at :488-490 sets `updated_by` on edit and `created_by` on
create from `getLocationUserMeta(user).userId`. Dates go out as `toDateISO(...)` /
`String(v).slice(0,10)`. `console.log("A")` :407 and `console.log(selectedLocation)` :411 are
unguarded — remove them.

**`LabsPanel`** (`components/settings/labs/LabsPanel.jsx`) — vendor master. Refuses with
`'API is not configured. Set VITE_APP_BASE_URL_AUTH.'` :123 and
`'No clinic selected. Choose a location or set VITE_CLINIC_ID.'` :129 rather than serving mock rows.
Loads `listLabs({ clinic_id, status: 'all', location_id?, q? })` :136. `handleHardDelete` :250 calls
`deleteLab(id, { hard: true })`; its failure toast recommends deactivating instead.

## 6. Docs section coupling

`patient-detail/docs/DocsSection.jsx:445` calls `usePatientLabCases(patient?.id)` and at :487-490
maps each case through `docsFolders.js:46` `labCaseToDoc(labCase, patient)` **only when
`labSource === 'api'`**. With no live cases it substitutes `createSampleLabRxDoc` (`:170`), and
:786 renders an explanatory empty state for the `lab-cases` folder. `labCaseToDoc` reads
`lab_case_id`, `lab_name`/`lab.name`, `order_type`, `tooth`, `sent_date`/`created_at`/`updated_at` —
add a field to the case and decide here whether it belongs in the doc title or description.

## 7. Maturity labels (from `PMS_React/README.md`)

| Surface | README line | Label |
|---|---|---|
| `/labs` board | :195, :371 | **live** — "the most API-complete page outside the chart" |
| Patient chart Labs section | :247 | **live** |
| Patient chart Docs section | :249 | **mock** — only lab cases are real content |
| Settings > Labs | :357 | **live** (listed under "Wired") |
| `LabStatusSelect.jsx`, `LabCaseStatusesModal.jsx` | :547-548 | listed as dead — **both claims are wrong**; see SKILL Traps |
