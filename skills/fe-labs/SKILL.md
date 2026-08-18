---
name: fe-labs
description: Frontend lab cases — the /labs board, the patient chart Labs section, the lab-case status catalog drawer and status pill, and Settings > Labs (lab vendor master). Use when changing PMS_React/src/pages/Labs.jsx, src/components/labs/**, patient-detail/labs/**, settings/labs/**, src/api/labCases.js, src/api/labs.js, src/hooks/useClinicLabCases.js or usePatientLabCases.js, or touching a lab order drawer, case number, shade, due date, overdue rule or lab status colour.
---

## Scope

Lab orders sent to an outside laboratory, on four surfaces: the `/labs` location board, the chart's
**Labs** section, the status-catalog drawer + status pill, and Settings > Labs. Maturity **live** —
README calls `/labs` "the most API-complete page outside the chart" (`PMS_React/README.md:195,247,371`).
**Two backends:** lab *cases* are `appointmentApi` `/v2/lab-cases` (`be-lab-cases`), lab *vendors*
`authApi` `/v2/labs` — separate service and gate. Docs and the chart shell belong to
`fe-patient-chart`, but lab cases are Docs' **only real content** (`README:249`).

## Files

| Path (under `PMS_React/`) | Role |
|---|---|
| `src/pages/Labs.jsx` | **(entry)** 794 lines. `/labs` board: All/Active tabs `:36`, filter popover, 25-row pager, status-catalog handlers `:303-333`, row → chart `:339`, mock note `:752`. |
| `src/api/labCases.js` | 193. 12 of the backend's 13 routes via `appointmentApi`. Local `unwrap:17`, `normalizeLabCasesList:34`. No mock branch — mocks live in the hooks. |
| `src/api/labs.js` | 99. Vendor master via `authApi` `/v2/labs`; `listActiveLabsForDropdown:53` fills every Lab dropdown. Own `unwrap:14`. **Different backend.** |
| `src/hooks/useClinicLabCases.js` | 371. Board state. `MOCK_LAB_CASES:15`, `DEFAULT_OPTIONS:42`, `resolveLabOptions:85`, location guard `:176-184`, `load:186`, `changeStatus:289`. |
| `src/hooks/usePatientLabCases.js` | 296. Patient state, same shape, `listLabCases` not the location board. `MOCK_LAB_CASES:16`, `resolveLabOptions:62`, catch fallback `:146-156`. |
| `src/components/patient-detail/labs/` | `LabsSection.jsx` 697 — chart table, filters, inline status pill, both drawers `:664,684`. `LabOrderDrawer.jsx` **33KB / 929 lines, grep, never read whole** — order form, re-reads via `getLabCase`, `updated_by`/`created_by` `:488,490`. |
| `src/components/labs/` | `LabCaseStatusesDrawer.jsx` 488 — controlled catalog CRUD (props `:272-282`), `PRESET_COLORS:25-34`. `LabStatusSelect.jsx` 192 — portal listbox pill, **live** (see Traps). `labStatusUtils.js` 60 — `getLabStatusId/Label/Color`, `normalizeStatusColor`, `colorToRgba`, `getContrastingTextColor`, `buildStatusPillStyle`; the only place a status colour is interpreted. |
| `src/components/settings/labs/` | `LabsPanel.jsx` 527 + `LabFormModal.jsx` 210. Vendor list and form. **live**, `authApi` only; refuses rather than mocking (`LabsPanel.jsx:120-124`). |

Touches (shared): `api/client.js` + `config.js`, `patients.js` `getClinicId`, `appointmentLookups.js`
`getProviders`, `services/patientApiService.js`, `utils/{locationUtils,patientMappers,formatName,
getErrorMessage,appointmentQueries}.js`; `config/routes.js:23`, `navigation.js:31`,
`patientSections.js:92-98`, `settingsNavigation.js:104`, `Settings.jsx:13,76-77`,
`AppRoutes.jsx:35,59,272,330`; `ui/OverlayBackdrop.jsx`; `docs/DocsSection.jsx:445,487-494,786` +
`docsFolders.js:46,170`; `tooth-chart-defaults/ProcedureColorsCard.jsx:60`.

## Contract

Renders `ROUTES.labs` (`AppRoutes.jsx:272`), the chart section `labs` → `ROUTES.patientSection(id,
'labs')` (`patientSections.js:92-98`, `AppRoutes.jsx:330`) and the `labs` Settings section
(`Settings.jsx:76`). Never write a literal `/labs`. `labCases.js` covers every route in
`be-lab-cases` **except** `GET /v2/lab-cases/<id>/status-history` — the audit log has no client
function and no UI. `listLocationLabCases` backs the board (Auth-enriched patient), `listLabCases`
the chart; `labs.js` adds `GET/POST/PUT/DELETE /v2/labs` + `PATCH /v2/labs/<id>/toggle`. Both hooks
return `{ cases, options, pagination, loading, error, source, isApiEnabled, refetch, addCase, editCase, changeStatus, removeCase }` — `cases`, **not** `items`. Params: `references/wire-and-components.md`.

## Invariants

1. **`clinic_id` on every lab-case call**, from `getClinicId()` — query param on GET/DELETE, body
   field on POST/PUT/PATCH. The hooks add it; direct callers must too.
2. **`updated_by` is mandatory on PUT and PATCH status** — a 400, not a silent skip. It is
   `getLocationUserMeta(user).userId`, 3rd arg of `changeStatus(id, statusId, updatedBy)`
   (`Labs.jsx:277`, `LabsSection.jsx:244`).
3. **Send `status_id`, never a free-text `status`** — the backend accepts an unmatched string and
   stores `status_id: null`: colourless, and invisible to any `status_id` filter.
4. **Status colour is server data, not theme** — read it only via `labStatusUtils.js`, apply it as an
   inline `style` (no Tailwind class can be built from a runtime hex). Those hexes and
   `PRESET_COLORS` are that data layer; all other colour is `gray-*` over `theme.css` vars (§6.4).
5. **A location must be selected for the board** — `useClinicLabCases:176-184` short-circuits with
   `Error('Select a location to view lab cases.')`; `listLocationLabCases` (`labCases.js:95`) throws.
6. **Dates are ISO `YYYY-MM-DD`** (`sent_date`/`due_date`/`received_date`/`delivered_date`), sliced
   with `String(v).slice(0,10)` (`LabOrderDrawer.jsx:399-400`); no date library exists here.
   `due_date` is required on create. **`is_overdue` is server-computed — never recompute it.**
7. **Dual-mode by env-var presence** (§5): `isLabCasesApiEnabled` *is* `isAppointmentApiEnabled`,
   `isLabsApiEnabled` *is* `isAuthApiEnabled`; new hook paths need a `!isApiEnabled` branch **and** an honest `source`.
8. **No `fetch` here.** `appointmentApi` always emits same-origin `/__appointment_api/api` (the host
   refuses CORS); that proxy is declared twice — `vite.config.js` and `vercel.json` — keep both.
9. **Never log a lab case, patient id or URL** (§7.1); gate diagnostics on `import.meta.env.DEV`, use
   `getErrorMessage(err, fallback)` + `const { toast } = useToast()`, never `alert`.
10. **Overlays** = `createPortal` + `AnimatePresence` + `OverlayBackdrop` with a named
    `OVERLAY_Z_INDEX` key (`LabCaseStatusesDrawer.jsx:365`, `LabOrderDrawer.jsx:800`, `LabFormModal.jsx:93`). One violation exists — Traps.

## Working here

1. Size first: `wc -l`, then `grep -nE "^export |^function |^const [A-Z_]+ ="` + `sed -n`.
   `LabOrderDrawer.jsx` must not be read whole.
2. New endpoint → one export in `labCases.js` (or `labs.js`) ending in that module's own `unwrap`,
   then surface it through a hook. Pages call hooks — the three status-catalog writes imported
   straight into `Labs.jsx:20-24` and `LabsSection.jsx:19-23` are the deliberate exception.
3. New field → `LabOrderDrawer.jsx` state + payload, both hooks' mock rows, the board column in
   `Labs.jsx`, the chart column in `LabsSection.jsx`, **and** `docsFolders.js:46` `labCaseToDoc` if
   it belongs in Docs. Backend counterpart: `be-lab-cases` "Working here" #2.
4. Change to either hook → apply it to **both**: near-duplicates, down to a copy of
   `resolveLabOptions` (`:85` / `:62`).
5. Verify on `/labs`, `/patients/:patientId/labs` **and** the Docs tab, then `npm run lint`. No test
   suite; "verified" means you watched the request.

## Traps

- **README's dead-code list is wrong here** (`README.md:547-548`). `LabStatusSelect.jsx` is **live** —
  imported by `Labs.jsx:15` and `LabsSection.jsx:36` (grep-verified); `LabCaseStatusesModal.jsx`
  **does not exist** — the file is `LabCaseStatusesDrawer.jsx`, also live (`Labs.jsx:16`,
  `LabsSection.jsx:37`). Nothing in this slice is dead.
- **`usePatientLabCases` invents lab cases on an API error**: the catch branch stamps the real
  patient's id onto `MOCK_LAB_CASES` ("D-360", Bridge, tooth 14, Zirconia, a named provider) and sets
  `source: 'mock-fallback'` (`:146-156`) — a **fourth** value outside `'api'|'mock'|'api-partial'`.
  `LabsSection.jsx:100-111` never destructures `source`, so those rows render as clinical fact under
  an `ApiErrorBanner` (`:305`). `useClinicLabCases` disagrees — its catch **clears** the list and
  sets `source: 'api'` (`:232-237`). Read `source` before believing a Labs table.
- **`DocsSection.jsx:488` gates lab docs on `labSource !== 'api'`** — correct, and why
  `mock-fallback` hides them there while the Labs tab still shows them.
- **`LabOrderDrawer.jsx:407,411` are ungated `console.log`s** (`"A"`, then `selectedLocation`) in a
  patient-scoped drawer — a §7.1 violation. Delete them; do not copy the pattern.
- **The board's Type filter is client-side over the current page only** (`Labs.jsx:185`) and then
  overwrites the server total with that count (`:192`); the hook's `statusId` / `orderType` server
  params (`useClinicLabCases.js:117-125`) are never passed by `Labs.jsx:149-156`.
- **Active/All is a substring test, not the backend's closed set** — `useClinicLabCases.js:204-209`
  drops statuses containing `deliver` or `cancel` (server set:
  `delivered/complete/completed/cancelled`), so a custom status "Cancel pickup" vanishes.
- **Neither hook uses a monotonic request-id ref** (no `useRef` at all) — both rely on the `load`
  callback identity, so a fast filter or pager change can land a stale response. Add the guard.
- **`LabStatusSelect.jsx:158` hardcodes `z-[90]`** instead of `OVERLAY_Z_INDEX.modalPanel`, and its
  portal has no `AnimatePresence` — the one overlay deviation in the slice (§6.6).
- **Settings > Labs deletes a vendor hard** (`LabsPanel.jsx:254`, `deleteLab(id, { hard: true })`);
  `lab_id`/`lab_name` are loose columns on `lab_case`, so cases keep a dangling name — prefer `toggleLab`.
- **The status-catalog writes have no mock branch**: with the appointment API off the board still
  renders sample rows, but Save in the Statuses drawer throws and only toasts.
- **`labs.js` exports no `normalizeX`** (§6.3) — `listActiveLabsForDropdown` maps to `{ id, name }`
  inline and returns `[]` when auth is off, so the Lab dropdown is silently empty.

## See also

- `references/wire-and-components.md` — endpoint↔function table, payload keys, hook return shape and
  every `source` value, component props, mock rows, README label map.
- `be-lab-cases` — the Flask counterpart (routes, `updated_by`, `case_number` 409, overdue set).
- `main-architecture` (hub) · `fe-patient-chart` (the chart shell and Docs; it owns `patient-detail/docs/`, this skill owns `patient-detail/labs/`) · `fe-settings` (the rail that routes the `labs` section) · `fe-scheduling` (`LocationContext`, route slip) · `fe-platform` (`client.js`, `OverlayBackdrop`) · `be-appointments` (route slip serializer).
