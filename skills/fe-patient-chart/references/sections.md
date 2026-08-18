# fe-patient-chart — section inventory, hooks, wire routes

Companion to `.claude/skills/fe-patient-chart/SKILL.md`. Everything here was read off the
working tree. Paths are relative to `PMS_React/`.

---

## 1. Section → files → data source

One row per entry in `src/config/patientSections.js`. "Page export" is the named
`Patient<X>Page` in `src/pages/PatientDetail.jsx` that the router lazy-loads.

| id | URL segment | Page export | Component dir | Hook / data | Maturity |
|---|---|---|---|---|---|
| `charting` | `charting` | `PatientChartingPage` | `patient-detail/charting/` | `ChartingContext` | live — **fe-charting / fe-perio** |
| `overview` | `overview` | `PatientOverviewPage` | inline `OverviewTab` + `contact/ContactPanels.jsx` | `usePatientContact` | live |
| `family` | `family` | `PatientFamilyPage` | `family/` (3 files) | `useRelatedPeople`, `useFamilyNote` | live |
| `insurance` | `insurance` | `PatientInsurancePage` | `patient-detail/insurance/` | `usePatientInsuranceData` | live — **fe-insurance-claims** |
| `appts` | `appts` | `PatientApptsPage` | `appts/` (2 files) | `usePatientAppointments` | live |
| `billing` | `billing` | `PatientBillingPage` | `patient-detail/billing/` | `usePatientClaims` + `ledger/LedgerWorkspace` | claims live, ledger live — **fe-insurance-claims / fe-ledger** |
| `tx-plans` | `tx-plans` | `PatientTxPlansPage` | `tx-plans/` (4 files) | local `useState([])` + `txPlanMockFindings.js` | **mock** |
| `notes` | `notes` | `PatientNotesPage` | `notes/` (5 files) | `usePatientNotes` | live |
| `images` | `images` | `PatientImagesPage` | `images/ImagesSection.jsx` | none | **stub** |
| `labs` | `labs` | `PatientLabsPage` | `labs/` (2 files) | `usePatientLabCases` | live |
| `medical-hx` | `medical-hx` | `PatientMedicalHxPage` | `medical-hx/` (12 files) | `usePatientMedicalHx` | live |
| `forms` | `forms` | `PatientFormsPage` | `forms/` (4 files) | `usePatientForms`, `api/forms.js` | live |
| `docs` | `docs` | `PatientDocsPage` | `docs/` (4 files) | `usePatientLabCases`, `usePatientAppointments` | **mock** except lab cases |
| `journal` | `journal` | `PatientJournalPage` | `journal/` (2 files) | `usePatientAppointments` + `api/appointments.js` | **partial** — read-only |
| `comms` | `comms` | `PatientCommsPage` | `comms/CommsSection.jsx` | none | **stub** |
| `schedule` | `schedule` | `PatientSchedulePage` | `schedule/ScheduleSection.jsx` | `SchedulingContext` | live — **fe-scheduling** |
| `audit-trail` | **`history`** | `PatientHistoryPage` | `audit/` (2 files) | `usePatientAuditTrail` | live |

`post-op` is **commented out** in `src/config/patientSections.js:81-87`. The README module
heading calls the grid "18-entry"; only 17 entries render. Any unlisted `:section` segment
falls through the catch-all route to `PatientSectionPlaceholderPage`.

### Stub / mock evidence

- `comms/CommsSection.jsx:51-53` — `const conversations = []`, `emails = []`, `calls = []`.
  No API import anywhere in the file.
- `images/ImagesSection.jsx:42-52` — the file picker and both action buttons only `toast(...)`
  ("Imaging upload API is not available yet."). 105 lines total.
- `tx-plans/TxPlansSection.jsx:31` — `const [plans, setPlans] = useState([])`; nothing persists.
  `tx-plans/GenerateFromChartDrawer.jsx:17-18,223,245,272` reads `MOCK_CURRENT_VISIT_FINDINGS` /
  `ALL_MOCK_FINDINGS` from `txPlanMockFindings.js`. **It never touches the odontogram.**
- `docs/DocsSection.jsx:489` — the only real documents are `labCaseToDoc(...)` rows built from
  `usePatientLabCases`. `:980` toasts "Document upload API is not available yet."; Rotate,
  Share, Open-in-new-tab, Move all toast (`:296,:304,:333,:341,:752,:941`).
  `docs/docsFolders.js` is folder *structure*, not seed documents.
- `journal/JournalSection.jsx:345` — "Journal entry API is not available yet." Reads are real
  (`listPatientAppointments`); writes are not.

---

## 2. Hook catalog

All under `src/hooks/`. Every one returns the house shape
`{ …items, loading, error, source, isApiEnabled, refetch, …mutators }` unless noted.

| hook | lines | returns (beyond the house keys) | notes |
|---|---|---|---|
| `usePatientDetail.js` | 169 | `patient`, `enriching`, `setPatient` | **The only TanStack Query hook in the slice.** Key `patientKeys.detail(id)` from `src/lib/queryClient.js:22`. `source` can be `'api'`, `'mock'`, or **`'mock-fallback'`** — a fourth value the house convention does not list. Also exports `createPlaceholderPatient(patientId)`. |
| `usePatientContact.js` | 200 | `phones`, `preferences`, `addPhone`, `editPhone`, `removePhone`, `setPrimaryPhone`, `savePreferences` | |
| `usePatientMedicalHx.js` | 630 | `alerts`, `allergies`, `conditions`, `medications`, `vitals`, `socialHabits`, `questionnaireAnswers`, `dentalAnswers`, `premedAnswers`, `emergencyContact`, `additionalNotes` + 14 mutators | Loads ~8 resources in parallel; `:234` is the **only** place in the repo that emits `source: 'api-partial'`. |
| `usePatientNotes.js` | 107 | `notes` + mutators | |
| `useRelatedPeople.js` | 118 | `people`, `addPerson`, `editPerson`, `removePerson` | |
| `useFamilyNote.js` | 156 | `note`, `saving`, `saveNote`, `clearNote`; also exports `extractFamilyNoteText` | |
| `usePatientAppointments.js` | 95 | `appointments` | Calls `getClinicId()` at `:58`. |
| `usePatientAuditTrail.js` | 86 | `entries` | **API-only — never seeds mock rows** (`:26-30` returns empty when the API is off). Errors if the id is non-numeric. |
| `usePatientForms.js` | 141 | `forms` + mutators | |
| `usePatientLabCases.js` | 296 | `cases` + mutators | Shared with `docs/`. |
| `usePatientChartAlerts.js` | 252 | alert buckets for the sidebar | |
| `usePatientSidebarSummary.js` | 164 | sidebar counts/balance | `getClinicId()` at `:100`. |
| `usePatientsList.js` | 93 | `patients`, `total`, `meta` | 300 ms debounce (`SEARCH_DEBOUNCE_MS`). Powers both `/patients` and `/ledger`. |
| `usePatientSearch.js` | 187 | `results` | Debounced **phone** search; needs `MIN_PHONE_DIGITS`. |
| `usePatientQuickSearch.js` | 91 | `results` | Consumed by scheduling drawers, not by the chart. |
| `useRecentPatients.js` | 51 | `{ recent, trackPatient }` | **Off-shape.** `localStorage` key `practice-dental-recent-patients`, max 5, syncs across tabs via the `storage` event. |
| `usePatientFamily.js` | 2 | — | Deprecated re-export alias of `useRelatedPeople`. **Imported by nothing.** |
| `usePatientInsuranceData.js` / `usePatientClaims.js` | — | — | Owned by **fe-insurance-claims**. |

`src/services/patientApiService.js` (203 lines) sits between the hooks and `src/api/patients.js`:
`fetchPatientCore`, `enrichPatientSubresources`, `fetchPatientsPage`, `fetchPatientById`,
`createPatientFromForm`, `updatePatientFromForm`.

---

## 3. `src/api/patients.js` wire routes

All through `authApi`. `const V2 = '/v2/patients'` (`:6`). Local `unwrap()` at `:8` handles the
`{ success, data }` envelope and **preserves pagination meta** (`total`/`pages`/`has_next`/`page`)
by returning the whole object minus `success`/`error`/`detail` when those keys are present.

**Collections hang off the patient; item mutations do not.** Every sub-resource follows the
same split — `GET|POST /v2/patients/:patientId/<plural>` but `PUT|DELETE /v2/patient-<plural>/:itemId`.

| resource | collection | item |
|---|---|---|
| patients | `GET/POST /v2/patients`, `GET /v2/patients/search` | `GET/PUT /v2/patients/:id` |
| phones | `GET/POST …/:id/phones` | `PUT/DELETE /v2/patient-phones/:phoneId`, `PUT …/make-primary` |
| medical alerts | `GET/POST …/:id/medical-alerts` | `PUT/DELETE /v2/patient-medical-alerts/:alertId` |
| allergies | `GET/POST …/:id/allergies` | `PUT/DELETE /v2/patient-allergies/:allergyId` |
| conditions | `GET/POST …/:id/medical-conditions` | `PUT/DELETE /v2/patient-medical-conditions/:conditionId` |
| notes | `GET/POST …/:id/notes` | `PUT/DELETE /v2/patient-notes/:noteId` |
| medications | `GET/POST …/:id/medications` | `PUT/DELETE /v2/patient-medications/:medicationId` |
| related people | `GET/POST …/:id/related-people` | `PUT/DELETE /v2/patient-related-people/:personId` |
| vitals | `GET …/:id/vitals`, `GET …/:id/vitals/latest`, `POST …/:id/vitals` | `PUT/DELETE /v2/patient-vitals/:vitalId` |
| history answers | `GET/PUT …/:id/medical-history-answers` | `DELETE /v2/patient-medical-history-answers/:answerId` |
| preferences | `GET/PUT …/:id/preferences` | — |
| social history | `GET/PUT/DELETE …/:id/social-history` | — |
| family note | `GET/PUT/DELETE …/:id/family-note` (`hard` flag) | — |
| audit trail | `GET …/:id/audit-trail` (`from`, `to`, `user_id`, `action_type`, `tooth`) | — |

There is **no `deletePatient` export** — deleting a patient never leaves the browser.
Forms endpoints are re-exported from `./forms` at `src/api/patients.js:306-319`.

### Patient list / search routing

`src/services/patientApiService.js:134-150`:

- `search.trim().length < 2` → `GET /v2/patients?clinic_id=&page=&limit=`
- ≥ 2 chars and ≥ 7 digits after `replace(/\D/g,'')` → `GET /v2/patients/search?clinic_id=&phone=&limit=`
- otherwise → `GET /v2/patients/search?clinic_id=&q=&limit=`

When the API is on, `PatientCharts.jsx` passes `search: ''` into `applyPatientTableQuery` so the
server does the searching; filters and sort still run client-side over the current page only
(`src/pages/PatientCharts.jsx:259-268`).

---

## 4. Mappers

`src/utils/patientMappers.js` (252 lines) — `mapApiPatientToView(apiPatient, { phones, medicalAlerts })`
is the single normalizer. Consequences worth knowing:

- `view.dob` is a **display** string (`"Mar 5, 1988"`, via `isoToDisplayDob` `:24`), not ISO.
  `parseDobToISO(dob)` `:239` converts back for the wire; `parsePatientDob` in
  `src/utils/patientTableQuery.js:20` parses the same display format for sorting.
- `view.age` is computed locally from the ISO dob (`computeAgeFromISO` `:36`), never read from the API.
- `view.insurance.status` is hard-coded `'needed'` and `verified_date` `null` (`:33-38`) —
  the real state comes from `usePatientInsuranceData`, not from the patient record.
- `view._api.raw` keeps the untouched payload; `_placeholder` / `_seeded` mark synthetic shells.
- `parsePatientIdForApi(patientId)` `:234` → `Number.parseInt` or `null`. Every hook that hits the
  API must call it and bail on `null`.
- Write mappers: `formToCreatePatientBody(form, clinicId)` `:177`, `formToUpdatePatientBody(form)` `:206`,
  `alertNameToMedicalAlertBody(alertName)` `:224`.

`src/utils/patientTableQuery.js` (132 lines) — pure, no imports: `SORTABLE_COLUMNS`
(`dob`, `lastVisit`, `provider`, `status`), `matchesSearch`, `matchesFilters`, `comparePatients`,
`applyPatientTableQuery(rows, { search, filters, sort })`.

---

## 5. Shell files

| file | lines | role |
|---|---|---|
| `src/components/patient-detail/PatientChartSidebar.jsx` | 529 | Avatar, balance, status, the `PATIENT_SECTIONS` grid as `NavLink`s, alerts trigger. Uses `usePatientChartAlerts` + `usePatientSidebarSummary`. |
| `src/components/patient-detail/PatientAlertsPanel.jsx` | 379 | Portal overlay. `createPortal` + `AnimatePresence` + `OverlayBackdrop`, `OVERLAY_Z_INDEX`. |
| `src/components/patient-detail/PatientSectionHeader.jsx` | 122 | Title from `getPatientSectionTitle(sectionId)`; per-section action rows (`charting`, `insurance`, `billing`, `schedule`, `appts`, `overview`). Renders `charting/ChartingHeaderControls`. |
| `src/components/patient-detail/PatientSectionPlaceholder.jsx` | 18 | "coming soon" `EmptyState`. |
| `src/components/patient-detail/PatientDetailSkeleton.jsx` | 207 | Default export `PatientDetailPageSkeleton`, re-exported by `src/components/ui/Skeleton.jsx:4`. **Only consumer is `PatientDetail.legacy.jsx:833`, which is dead** — so this file is effectively dead too. The live loading state is the inline `RouteFallback({ forPatientChart })` in `src/components/AppRoutes.jsx:91`. |
| `src/components/patient-detail/shared/patientSectionUi.jsx` | 88 | `ApiErrorBanner`, `SectionToolbar`, `DetailField`, `StatusPill`, `FormField`, `inputClass` / `selectClass` / `labelClass` / `textareaClass`. |
| `src/components/patient-detail/shared/SimpleFormDialog.jsx` | 119 | Small modal used by journal, docs, billing, claims. |

## 6. Browser storage owned here

| key | store | written by |
|---|---|---|
| `practice-dental-recent-patients` | localStorage | `src/hooks/useRecentPatients.js:3` |
| `pd:patient-chart-panel-collapsed` | sessionStorage | `src/pages/PatientDetail.jsx:417,427` |
| `pd:medical-hx-reviewed:<patientId>` | localStorage | `src/components/patient-detail/medical-hx/MedicalHxSection.jsx:47` |

The medical-hx key embeds a patient id, so on a shared front-desk workstation the key list is
itself a record of which patients were opened (README "Browser storage").
