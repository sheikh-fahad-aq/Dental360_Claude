# fe-forms — schema, wire and inventory

Overflow for `fe-forms/SKILL.md`. Every path is relative to `PMS_React/`. Line numbers verified
against the working tree; anything not confirmed is marked **unverified**.

---

## 1. Maturity matrix

| Surface | Route / id | Maturity | Evidence |
|---|---|---|---|
| Practice form library | `/forms` | **partial** | README:194. Templates are real (`listFormTemplates`); Responses tab is an `EmptyState`; 4 of 5 row actions toast "coming soon" (`Forms.jsx:392`) |
| Patient chart Forms tab | `/patients/:id/forms` | **live** | README:248. `usePatientForms` → real Auth endpoints; request, edit and submit all hit the server |
| Settings > Check-In Forms | `/settings/check-in-forms` | **live** | README:357 lists it among the 12 wired sections; `GET|PUT /locations/{id}/check-in-forms` |
| Public intake link | `/f/:token` | **mock** | README:181 "localStorage only, no backend". `PatientFormLinkPage.jsx` imports no API module |
| Upload paper form | modal in chart tab | **stub** | `FormsSection.jsx:355` toasts "Queued N files for digitizing"; `UploadPaperFormModal.jsx` imports no API |
| Send form SMS/email | `SendFormToPatientModal` | **UI only** | No API import; `onSend` is a parent callback. Server reports `delivery.sent === false` and the chart toasts "SMS delivery is not connected yet" (`FormsSection.jsx:222`) |

---

## 2. `src/api/forms.js` — exports, callers

Client: `authApi` (`VITE_APP_BASE_URL_AUTH`, base already ends `/api`). Envelope handling is the
module-local `unwrap` at `:24` — it throws when `success === false`, otherwise returns `.data` if
present, else the body as-is. Arrays pass through untouched.

| Export | Line | Wire | Callers |
|---|---|---|---|
| `isFormsApiEnabled` | `:17` | — (re-export of `isAuthApiEnabled`) | `Forms.jsx:23`, `SendFormDrawer.jsx:6`, `CheckInFormsPanel.jsx:12`, `usePatientForms.js:3` |
| `normalizeFormTemplatesResponse` | `:41` | accepts array \| `{templates}` \| `{items}` \| `{results}` → array | internal |
| `normalizePatientFormsResponse` | `:51` | → `{ patient_id, appointment_id, count, required, submitted, forms[], delivery }` | internal |
| `listFormTemplates` | `:96` | `GET /form-templates?clinic_id=` | `Forms.jsx`, `SendFormDrawer.jsx`, `CheckInFormsPanel.jsx` |
| `getFormTemplate` | `:106` | `GET /form-templates/{id}` | `FormPreviewDrawer.jsx:45`, `FormsSection.jsx:17` |
| `getFormTemplateByCode` | `:116` | `GET /form-templates/code/{code}?clinic_id=` | `FormsSection.jsx:17` |
| `listPatientForms` | `:130` | `GET /patients/{id}/forms?appointment_id=` | `usePatientForms.js` |
| `requestStandardPatientForms` | `:142` | `POST /patients/{id}/forms/request-standard` | `usePatientForms.requestAll` |
| `requestPatientForm` | `:168` | `POST /patients/{id}/forms/{templateId}/request` | `usePatientForms.requestOne` |
| `updatePatientForm` | `:198` | `PUT /patient-forms/{id}` | `usePatientForms.editForm`, and the last resort inside `submitPatientForm` |
| `submitPatientForm` | `:207` | `POST /v2/patient-forms/{id}/submit` → fallback chain | `usePatientForms.markSubmitted` |
| `normalizeLocationCheckInFormsResponse` | `:247` | → `{ location_id, clinic_id, template_ids[], templates[], updated_at, updated_by }` | internal |
| `getLocationCheckInForms` | `:291` | `GET /locations/{id}/check-in-forms?clinic_id=` | `CheckInFormsPanel.jsx:160` |
| `updateLocationCheckInForms` | `:305` | `PUT /locations/{id}/check-in-forms` | `CheckInFormsPanel.jsx:232` |

### Request bodies

- **request-standard / request one** — `{ clinic_id, location_id, appointment_id, user_id,
  delivery_method }`, `delivery_method` defaults to `'sms'` (`usePatientForms.js:69,90`).
- **submit** — `{ submitted_data, user_id? }`. Path order: `/v2/patient-forms/{id}/submit`, then
  `/patient-forms/{id}/submit`, then `PUT /patient-forms/{id}` with
  `{ status: 'submitted', submitted_data, user_id? }`. The loop advances **only** on HTTP 404/405
  (`:229`); any other status rethrows immediately.
- **check-in forms PUT** — `{ clinic_id, template_ids: [ordered ids], user_id }`. Full replace.

### Adjacent module, not this one

`listAppointmentForms` (`src/api/appointments.js:1126`) calls `GET /v2/appointments/{id}/forms` on
`appointmentApi` (same-origin `/__appointment_api/api`), normalised by
`normalizeAppointmentFormsResponse` (`:1076`) into
`{ appointment_id, forms_available, count, required, submitted, forms[] }`. Rows in that payload can
carry `html_content`, which is what `scheduling/VisitStatusBoard.jsx:1065,1127` renders through
`dangerouslySetInnerHTML` with no sanitizer (CLAUDE.md §7.4). Siblings there:
`requestAllAppointmentForms:1136`, `requestAppointmentForm:1154`,
`updateAppointmentPatientForm:1173`.

---

## 3. The `form_schema` contract

```
{
  title?:       string      // heading; overridden by the `title` prop
  subtitle?:    string      // falls back to `description`
  description?: string
  sections: [
    {
      key?: string, id?: string,      // React key; `section_<index>` if absent
      title?: string,
      description?: string,
      fields: [ … ]
    }
  ]
}
```

Field object: `{ key?, name?, id?, label?, type?, required?, placeholder?, options?, content? }`.

- **Identity** — `fieldKey(field, index)` (`FormSchemaRenderer.jsx:16`) resolves
  `key || name || id || \`field_${index}\``. The index is the field's position **within its
  section**, so two keyless fields in different sections collide on `field_0`. Always author `key`.
- **Values** — one flat object `{ [fieldKey]: value }`, seeded from `initialValues` and reset
  whenever the `formSchema` identity changes (`:348`). This is what is sent as `submitted_data`.
- **`collectSchemaFields`** (`:20`) flattens sections, skips `static_text`, and stamps
  `_sectionTitle` / `_sectionIndex` on each field.
- **`getMissingRequiredFields`** (`:49`) drives both the "Required fields remaining" list and the
  Submit button's disabled state (only when `requireAllRequired`).

### Field types

| `type` | Control | Stored value | Notes |
|---|---|---|---|
| `text` (default) | `<input type=text>` | string | Any unrecognised type lands here (`:303`) |
| `email` · `date` | native input of that type | string | dates are ISO `YYYY-MM-DD` |
| `phone` | `<input type=tel>` | string | `htmlType` remap at `:304` |
| `textarea` | `<textarea>` | string | `:119` |
| `radio` | `OptionRow` list | string | `:135`; options at `:106` |
| `select` | `<select>` | string | `:164` |
| `checkbox` | single box | boolean | `:190`; filled = `Boolean(value)` |
| `multi_checkbox` | box list | **array of strings** | `:208`; filled = non-empty array |
| `file` | drop-zone `<input type=file>` | **`file.name` string** | `:243`. The `File` object is discarded — nothing is uploaded |
| `signature` | plain `<input type=text>` | typed name string | `:284`. No canvas, no attestation |
| `static_text` | paragraph from `content \|\| label` | none | `:111`. Excluded from `collectSchemaFields` and always "filled" |

`options` entries may be a scalar or `{ value \| id, label \| name }` — resolved identically at
`:144`, `:177` and `:218`.

### `FormSchemaRenderer` props (`:325`)

`formSchema` · `title` · `subtitle` · `initialValues` · `readOnly` · `submitting` · `submitLabel` ·
`onSubmit(values)` · `className` · `variant` (`'default' | 'patient'`) · `showHeader` ·
`showRequiredRemaining` · `requireAllRequired` · `onValuesChange(values)`.

`variant='patient'` switches to taller inputs and a full-width blue submit button; the **only**
call site is `PatientFormLinkPage.jsx:227` (with `showRequiredRemaining` + `requireAllRequired`). A missing or non-object `formSchema` renders
"Preview unavailable" (`:363`); an empty `sections` array renders "This form has no fields yet."

Callers: `FormPreviewDrawer.jsx:131` (readOnly), `FormsSection.jsx:544` (fill-in),
`CheckInFormsStep.jsx:607` (fe-scheduling), `PatientFormLinkPage.jsx:223`.

---

## 4. Template shape is not normalised into a model

There is no `normalizeFormTemplate`. Consumers cope with several shapes:

- **Title** — `name || title || label || code` in four separate helpers:
  `Forms.jsx:291 templateTitle`, `formTemplates.js:14 templateDisplayName`,
  `FormsSection.jsx:128 formDisplayName`, `CheckInFormsPanel.jsx:24 templateTitle`.
- **Template id on a patient-form row** — `resolveTemplateId` (`FormsSection.jsx:132`) tries
  `form_template_id`, `template_id`, `formTemplateId`, `templateId`.
- **Schema** — `loadFormSchemaForItem` (`FormsSection.jsx:142`): the row's own `form_schema`, else
  `getFormTemplate(id)` (`form_schema ?? schema`), else `getFormTemplateByCode(code)`. May still
  return `null`, which surfaces as a load error in the fill-in drawer.
- **Row id** — `getResourceId(item, 'form_id', 'id')` (`usePatientForms.js:139`).
- **Category** — invented client-side by substring match on `code` / `form_type`
  (`CheckInFormsPanel.jsx:28`): `Consent` (hipaa/consent/waiver/release), `Insurance`,
  `Patient Intake` (registration/intake/new_patient), else `Standard` if `is_standard`, else
  `Custom`. The server sends no category field.

---

## 5. `usePatientForms` (`src/hooks/usePatientForms.js`)

Signature `usePatientForms(patientId, { appointmentId } = {})`. Returns:

```
{ forms, meta: { count, required, submitted }, loading, error, source,
  isApiEnabled, refetch, requestAll, requestOne, editForm, markSubmitted, getFormId }
```

- `source` is `'api'` (`:53`), `'disabled'` / `'invalid-id'` (`:33`), `'error'` (`:58`). **Never
  `'mock'`** — this domain has no mock fallback, unlike most of the app (CLAUDE.md §5).
- `patientId` goes through `parsePatientIdForApi`; a non-numeric id short-circuits to
  `source: 'invalid-id'` with an `Error('Invalid patient id.')`.
- Every mutator awaits `load()` afterwards, so the list is always server truth. There is **no
  optimistic update** and **no request-id guard** — `load` is a `useCallback` re-run by `useEffect`,
  so a fast patient switch can resolve out of order.

---

## 6. The `/f/:token` link store

`src/utils/patientFormLinkStore.js` — one `localStorage` key, `pms_patient_form_links_v1` (`:6`),
holding `{ [token]: record }`. Never cleared: logout and 401 remove only `pd:token:v1` and
`pd:auth:v1` (README:154-160).

Record fields observed in the writers (`scheduling/CheckInFormsStep.jsx`,
`scheduling/VisitStatusBoard.jsx`) and readers (`PatientFormLinkPage.jsx`):
`token`, `createdAt`, `updatedAt`, `formSchema`, `formTitle`, `formSubtitle` / `formDescription`,
`practiceName`, `patientDob`, `expiresAt`, `status`, `submittedAt`, `submittedData`.

API: `createFormLinkToken()` `:27` (16 hex chars from `crypto.randomUUID`, or a `Date.now()`
fallback), `savePatientFormLink` `:38`, `getPatientFormLink` `:49`, `updatePatientFormLink` `:55`,
`buildPatientFormPath` `:66`, `buildPatientFormUrl` `:70`.

### Why the page is not real intake

1. **Same-origin storage only.** The record is written in the staff browser. A patient on another
   device gets `getPatientFormLink → null` and falls through to `DEMO_PATIENT_FORM_SCHEMA`
   (`PatientFormLinkPage.jsx:69`).
2. **The DOB gate is client-side and optional.** `:92-94` — if the record has no `patientDob`, any
   syntactically valid `MM-DD-YYYY` is accepted.
3. **The attempt counter is component state.** `MAX_ATTEMPTS = 3` at `:11`, `attemptsLeft` at `:65`;
   a page reload restores all three tries.
4. **Submit writes locally.** `:109-123` calls `updatePatientFormLink(token, { status:'submitted',
   submittedAt, submittedData })`. No network call anywhere in the file.
5. **After submit the answers persist** — full intake PHI in `localStorage` on the workstation that
   sent the link.

Wiring: `App.jsx:25` and `AppRoutes.jsx:141` both test `pathname.startsWith('/f/')` to render the
page outside `AppLayout`; the route itself is `AppRoutes.jsx:169`, with no `ProtectedRoute` wrapper.
`getPageTransitionKey` maps the prefix to `'patient-form-link'` (`config/routes.js:41`).

---

## 7. Known deviations from repo convention

| Rule | Deviation | Where |
|---|---|---|
| §6.4 no hardcoded hex | `bg-[#eef2f7]` twice | `PatientFormLinkPage.jsx:131,140` |
| §6.6 `OVERLAY_Z_INDEX` | `z-[200]` on the row-action portal; the map maxes at 90 | `Forms.jsx:165` |
| §5 `source` enum | `'disabled' \| 'invalid-id' \| 'error'` instead of `'mock' \| 'api-partial'` | `usePatientForms.js:33,58` |
| §5 mock fallback | Forms refuse instead of degrading to mock | `usePatientForms.js:30`, `Forms.jsx:316`, `CheckInFormsPanel.jsx:130` |
| monotonic request-id ref | `cancelled` closure flag, or no guard at all | `FormPreviewDrawer.jsx:42`, `SendFormDrawer.jsx:52`; none in `usePatientForms` / `Forms.jsx` |
| navigation is config-driven | `/forms` has no `config/navigation.js` entry and no command-palette entry; reachable only from `CheckInFormsPanel.jsx:299,373` | — |

Conforming, for reference: no `fetch()` and no `console.*` anywhere in the slice; every overlay uses
`createPortal` + `AnimatePresence` + `OverlayBackdrop` with a named `OVERLAY_Z_INDEX` key except the
`Forms.jsx` row menu; all feedback goes through `useToast()` and `getErrorMessage`.
