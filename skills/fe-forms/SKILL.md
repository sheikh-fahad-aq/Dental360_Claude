---
name: fe-forms
description: Frontend patient forms and intake — the /forms library, the public /f/:token intake link, the chart Forms tab, Settings > Check-In Forms, and FormSchemaRenderer. Use when changing PMS_React/src/pages/Forms.jsx or PatientFormLinkPage.jsx, src/components/forms/**, patient-detail/forms/**, settings/check-in-forms/**, src/api/forms.js or usePatientForms.js; hitting /form-templates, /patients/{id}/forms or /locations/{id}/check-in-forms; or debugging form_schema or pms_patient_form_links_v1.
---

## Scope

Four surfaces render a form template and one configures it: the practice library `/forms`
(**partial**, README:194), the chart **Forms** tab (**live**, README:248), Settings > **Check-In
Forms** (**live**, 1 of the 12 wired sections, README:357), and the public `/f/:token` intake page
(**mock — localStorage only, no backend, no auth**, README:181). `FormSchemaRenderer` is the single
renderer all four share. Boundary: `scheduling/CheckInFormsStep.jsx` and `VisitStatusBoard.jsx`
*create* the `/f/` links and preview appointment forms — **fe-scheduling** owns them; this skill owns
the store and the modal they import. `src/utils/patientForm.js` is here by name only (Traps).

## Files

| path (under `PMS_React/`) | role |
|---|---|
| `src/components/forms/FormSchemaRenderer.jsx` | **(entry)** 492 lines — the one renderer and the schema contract: `fieldKey:16`, `collectSchemaFields:20`, `isFieldValueFilled:39`, `getMissingRequiredFields:49`, `FieldControl:103` (12 types), default export `:325`. |
| `src/api/forms.js` | 320. Every Auth forms call. Local `unwrap:24` (throws on `success:false`, else peels `.data`); three normalizers `:41,:51,:247`; `isFormsApiEnabled` is a bare **re-export of `isAuthApiEnabled`** `:17`. |
| `src/pages/Forms.jsx` | 717. `/forms` — **partial**. Tabs `:28`, five row actions `:33` of which only Preview is wired (`:388`); the rest toast "coming soon" `:392`. |
| `src/pages/PatientFormLinkPage.jsx` | 259. Public `/f/:token` — **mock**. DOB gate `:79`; submit `:109` writes localStorage and nothing else. |
| `src/components/forms/FormPreviewDrawer.jsx` · `SendFormToPatientModal.jsx` | Read-only preview, lazy `getFormTemplate:45`; the SMS/email composer — **UI only**, `onSend` is a parent callback and the file imports no API (`:130`). |
| `src/components/patient-detail/forms/` | `FormsSection.jsx` (600) the chart tab — schema resolution `:142`, hook `:183`, fill-in renderer `:544`, three overlays `:574,:585,:592`; `SendFormDrawer.jsx` template picker; `UploadPaperFormModal.jsx` **stub** (`FormsSection:355` toasts "Queued N files", uploads nothing); `formTemplates.js` two display helpers. |
| `src/components/settings/check-in-forms/CheckInFormsPanel.jsx` | 481. Per-location required templates, full-replace save `:232`. Category is a **client-side substring heuristic** on `code` `:28`; the Scope select is permanently `disabled` `:62`. |
| `src/hooks/usePatientForms.js` · `src/utils/patientFormLinkStore.js` | 141 — the chart tab's list plus `requestAll`/`requestOne`/`editForm`/`markSubmitted`, each re-`load()`ing; 73 — `localStorage['pms_patient_form_links_v1']` `:6`, which **is** the `/f/` backend (`createFormLinkToken:27`, `buildPatientFormUrl:70`). |
| `src/data/demoPatientFormSchema.js` · `practiceForms.js` (**both `fe-reports-worklists`' seed index — read here, edit there**) · `src/utils/patientForm.js` | 102-line fallback schema (4 sections) used when a row has no `form_schema`; 3 lines, only `FORMS_PAGE_SIZE_OPTIONS`; 268 lines that are **owned here by glob but are not intake** — add/edit-patient demographics (Traps). |

Touches (shared, not owned): `api/client.js` + `config.js`; `config/routes.js:15,17,41,48`,
`patientSections.js:107`, `settingsNavigation.js:110`, `pages/Settings.jsx:74`,
`AppRoutes.jsx:141,169,230`, `App.jsx:25`; `getResourceId`, `parsePatientIdForApi`,
`getLocationUserMeta`; `ui/OverlayBackdrop.jsx`, `EmptyState`, `Skeleton`.

## Contract

Routes: `ROUTES.forms` = `/forms` (`AppRoutes.jsx:230`, protected); `ROUTES.patientFormLink(t)` =
`/f/:token` (`AppRoutes.jsx:169`) renders **outside `AppLayout`** — no sidebar, no `ProtectedRoute`,
because `App.jsx:25` and `AppRoutes.jsx:141` branch on `/f/`. Chart tab `forms`, settings
`check-in-forms`.

API is `src/api/forms.js` on **`authApi` only** (`VITE_APP_BASE_URL_AUTH`, already ends `/api`;
neither same-origin proxy is involved): `/form-templates` (list · by id · by code),
`/patients/{id}/forms` (+ `request-standard`, `{templateId}/request`), `PUT /patient-forms/{id}`,
`POST /v2/patient-forms/{id}/submit`, `GET|PUT /locations/{id}/check-in-forms`. Appointment-scoped
forms are a **different module** — `listAppointmentForms` (`src/api/appointments.js:1126`, `appointmentApi`, `GET /v2/appointments/{id}/forms`): that payload is where `html_content` enters.

Schema: `{ title?, sections: [{ key|id, title?, fields: [{ key|name|id, label, type, required?,
placeholder?, options?, content? }] }] }`; types `text email phone date textarea radio select
checkbox multi_checkbox file signature static_text`, unknown → `text` (`:303`). Values are one flat `{ [fieldKey]: value }` map sent as `submitted_data`.

## Invariants

1. **`/f/:token` is unauthenticated and has no backend** — everything comes from
   `pms_patient_form_links_v1` in the *sending* browser (`patientFormLinkStore.js:6`). Never put a
   patient id, appointment id or token in that payload.
2. **Never render `html_content`, or any server field, as markup** (§7.4). The renderer deliberately
   ignores it (`FormSchemaRenderer.jsx:323`) and drives off `form_schema`. The sink at
   `scheduling/VisitStatusBoard.jsx:1127` is a bug to fix, not a pattern to copy — no sanitizer here.
3. **`fetch()` never appears here** (§6.1) — every call goes through `src/api/forms.js` on `authApi`.
4. **Gating is env-var presence** (§5): `isFormsApiEnabled` *is* `isAuthApiEnabled`. Unset
   `VITE_APP_BASE_URL_AUTH` and forms **refuse rather than mock** — error + empty list at
   `usePatientForms.js:30`, `Forms.jsx:316`, `CheckInFormsPanel.jsx:130`.
5. **`usePatientForms`'s `source` is outside the repo enum** — `'api' | 'disabled' | 'invalid-id' |
   'error'` (`:33,:53,:58`), never `'mock'`. A status, not the §5 mock flag.
6. **`PUT /locations/{id}/check-in-forms` is a full replace** of the ordered `template_ids`
   (`CheckInFormsPanel.jsx:232`). Send the complete set; a partial array silently unassigns forms.
7. **Do not "simplify" `submitPatientForm`** (`api/forms.js:207-241`): it tries
   `/v2/patient-forms/{id}/submit`, then `/patient-forms/{id}/submit`, then `PUT` with
   `status:'submitted'`, and **falls through only on 404/405** — every other status rethrows.
8. **A field's key is `key || name || id || field_<index>`** (`fieldKey:16`) — a keyless field is
   addressed **positionally**, so reordering a section renames its answer. Always set a `key`.
9. **Never log a form payload, token, patient id or `/f/` URL** (§7.1) — intake answers are PHI and
   this slice has no `console.*` today. Failures use `getErrorMessage(err, fallback)` + `useToast()`.
10. **Overlays = `createPortal` + `AnimatePresence` + `OverlayBackdrop` + an `OVERLAY_Z_INDEX` key**
    (§6.6; `SendFormToPatientModal.jsx:169`, `SendFormDrawer.jsx:96`). `ROUTES` not literals, no hex
    colours, ISO `YYYY-MM-DD` on the wire, **no date library**, never `alert`.

## Working here

1. Size first: `wc -l`, then `grep -nE "^export |^function |^const [A-Z]"` + `sed -n`; `Forms.jsx`
   (717) and `FormsSection.jsx` (600) are not read whole.
2. **New endpoint** → one export in `src/api/forms.js`, `unwrap(response.data)`, its own
   `normalizeX`; then a mutator in `usePatientForms.js` that awaits `load()`.
3. **New field type** → a branch in `FieldControl` (`FormSchemaRenderer.jsx:103`) **and** a case in
   `isFieldValueFilled:39`; miss the second and a required field of that type can never be filled.
4. **New page or section** → a `ROUTES` entry, `AppRoutes.jsx`, and the matching config
   (`patientSections.js` / `settingsNavigation.js` + the `Settings.jsx` branch). `/forms` itself has
   **no `navigation.js` entry** (Traps).
5. Verify by loading the surface and watching the request, then `npm run lint`. No test suite.

## Traps

- **`src/utils/patientForm.js` has nothing to do with intake forms** — it is the add/edit-patient
  demographics mapper (`EMPTY_PATIENT_FORM:30`, `patientToFormValues:147`) used by
  `charts/NewPatientDrawer.jsx:6` and `PatientDetail.jsx:28`.
- **`pms_patient_form_links_v1` is never cleared** (§7.3, README:160) and after a submit it holds
  `submittedData` — name, DOB, address, insurance answers — in plain `localStorage` on a shared
  front-desk workstation. Only `pd:token:v1` and `pd:auth:v1` are cleared on logout or 401.
- **The `/f/` DOB gate is theatre.** With no `patientDob` stored it accepts **any** valid date
  (`PatientFormLinkPage.jsx:92-94`) and `attemptsLeft` is React state (`:65`), so a reload restores
  all three tries. The record also lives in the *staff* browser: on the patient's own phone the
  lookup returns `null`, falls back to `DEMO_PATIENT_FORM_SCHEMA` (`:69`), and saves to that device.
- **The `file` field uploads nothing** — `FormSchemaRenderer.jsx:243-262` keeps `file.name`, drops
  the `File`; the demo "Insurance Card" captures a string. **`signature` is a plain text input**
  (`:284`) — a typed name, no canvas, no attestation.
- **`/forms` is unreachable from the sidebar** — absent from `config/navigation.js` and the command
  palette; the only in-app links are the two in `CheckInFormsPanel.jsx:299,373`. Its "Patient Responses" tab is a hardcoded `EmptyState` (`Forms.jsx:489-496`); no responses API exists.
- **Three convention breaks:** `Forms.jsx:165` uses `z-[200]`, outside `OVERLAY_Z_INDEX` (max 90);
  `PatientFormLinkPage.jsx:131,140` hardcode `bg-[#eef2f7]`, the slice's only raw hexes (§6.4); no
  load uses the monotonic request-id ref (`FormPreviewDrawer:42`/`SendFormDrawer:52` use `cancelled`,
  `usePatientForms` and `Forms.jsx` nothing).
- **`SendFormToPatientModal` sends no message** — it composes SMS/email and calls `onSend`; delivery
  is unwired end to end, and the chart tab toasts "Forms marked sent. SMS delivery is not connected
  yet." whenever the server returns `delivery.sent === false` (`FormsSection.jsx:222`).

## See also

- `references/schema-and-wire.md` — exports with callers, field-type and props tables, endpoint
  payloads, template-shape resolution, the link-store record, and the mock/live matrix.
- `main-architecture` (hub) · `fe-scheduling` (owns `CheckInFormsStep.jsx` and `VisitStatusBoard.jsx` —
  they create `/f/` links and hold the HTML sink) · `fe-patient-chart` (owns the chart shell the Forms
  tab mounts in, and `PatientDetail.jsx`, a caller of `utils/patientForm.js`) · `fe-settings` (the rail
  that routes `check-in-forms`) · `fe-reports-worklists` (the `src/data/` seed index) · `fe-platform` ·
  `be-visit-lifecycle` (`appointment_forms_routes.py`). `PMS_React/README.md` is the maturity truth.
