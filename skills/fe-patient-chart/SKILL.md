---
name: fe-patient-chart
description: Patient chart shell and non-clinical tabs — /patients/:patientId/*, the Patient<X>Page exports in PatientDetail.jsx, the patientSections.js registry, and the appts/audit/docs/family/journal/medical-hx/notes/tx-plans sections. Use when adding a chart tab, editing src/api/patients.js, patientApiService.js or PatientsContext, touching a usePatient* hook, or debugging /v2/patients, the audit-trail vs /history mismatch, or getClinicId(). Not charting, perio, insurance, billing, forms or labs.
---

## Scope

The chart shell at `/patients/:patientId/*` — a 17-entry section grid in a left sidebar over an
`<Outlet>` — plus the `/patients` list and the patient data layer (`PMS_React/src/api/patients.js`,
its mappers, the `usePatient*` hooks, `PatientsContext`). **Not owned, though they render inside this
shell:** `charting/` + perio (fe-charting, fe-perio), `insurance/` and `billing/` (fe-insurance-claims,
plus fe-ledger for the Ledger sub-tab), `forms/` (fe-forms), `labs/` (fe-labs), and `schedule`, which
only embeds scheduling. Maturity is **mixed** — read `references/sections.md` §1, not the screen.

## Files

| path (under `PMS_React/`) | role |
|---|---|
| `src/pages/PatientDetail.jsx` | **(entry)** 679 lines / 24KB. Default export = the shell; 17 named `Patient<X>Page` exports (`:261`-`:392`) are the route elements. `OverviewTab` is inline at `:175`. |
| `src/config/patientSections.js` | 178 lines. `PATIENT_SECTIONS` (the tab registry), `getPatientSectionById`, `getActivePatientSectionId`, `getPatientSectionTitle`. |
| `src/pages/PatientCharts.jsx` · `PatientDetail.legacy.jsx` | 804 / 887 lines, 31KB each — `grep`/`sed`, never read whole. The first is the patient list at `/patients` **and** `/`; the second is **dead**, imported nowhere in `src/`. Do not edit or copy from the legacy file. |
| `src/components/patient-detail/` shell | `PatientChartSidebar.jsx` 529 · `PatientAlertsPanel.jsx` 379 · `PatientSectionHeader.jsx` 122 · `PatientSectionPlaceholder.jsx` 18 · `PatientDetailSkeleton.jsx` 207 (dead, see Traps) · `shared/patientSectionUi.jsx` 88 · `shared/SimpleFormDialog.jsx` 119. |
| `src/components/patient-detail/<section>/` | Owned: `appts` 2 files · `audit` 2 · `comms` 1 · `contact` 1 · `docs` 4 · `family` 3 · `images` 1 · `journal` 2 · `medical-hx` 12 · `notes` 5 (TipTap) · `schedule` 1 · `tx-plans` 4 (`TxPlansSection`, two drawers, `txPlanFormat.js`; backed by `src/api/treatmentPlans.js` + `hooks/usePatientTreatmentPlans.js`). **Not owned, sitting in this tree:** `charting/` + `charting/perio/` (fe-charting / fe-perio), `insurance/` 9 + `billing/` 6 (fe-insurance-claims), `forms/` 4 (fe-forms), `labs/` 2 (fe-labs). Largest owned: `appts/AddAppointmentDrawer.jsx` 1334, `docs/DocsSection.jsx` 994. |
| `src/api/patients.js` | 327 lines. The only patient wire module; `authApi` + a local `unwrap()` at `:8`; re-exports the forms endpoints from `./forms` at `:306`. Hooks reach it via `src/services/patientApiService.js` (203). |
| `src/utils/patientMappers.js` · `patientTableQuery.js` · `src/context/PatientsContext.jsx` | 252 / 132 / 68. `mapApiPatientToView`; the pure list search/filter/sort; an in-memory patient list seeded from `src/data/patients.js` — no persistence, no network. |
| `src/hooks/usePatient*.js` · `useRelatedPeople.js` · `useRecentPatients.js` · `useFamilyNote.js` | **14** hooks owned here; return shapes in `references/sections.md` §2. Five `usePatient*` hooks are **not** owned: `usePatientAppointments` (fe-scheduling), `usePatientClaims` + `usePatientInsuranceData` (fe-insurance-claims), `usePatientLabCases` (fe-labs), `usePatientForms` (fe-forms). |
| `src/services/patientApiService.js` | 203. The layer the hooks and both pages call instead of `api/patients.js` directly (6 importers). |

Touches (shared, not owned, all under `src/`): `components/AppRoutes.jsx:39-77,315-340` (the
`lazyNamed` block) · `config/routes.js:28-33` · `components/charts/NewPatientDrawer.jsx` (edit
drawer) · `components/ui/Skeleton.jsx` · `lib/queryClient.js:20` (`patientKeys`).

## Contract

Routes: `/patients/:patientId` (index → `Navigate to="overview"`), 17 child segments, then catch-all
`:section` → `PatientSectionPlaceholderPage`; build URLs from `ROUTES.patient*`. API: `api/patients.js`
only, over `authApi` — collections nest under the patient (`GET/POST /v2/patients/:id/<plural>`), item
mutations do **not** (`PUT/DELETE /v2/patient-<plural>/:itemId`). Routes: `references/sections.md` §3.
**Per-section maturity and owning skill: `references/sections.md` §1** — one row per
`PATIENT_SECTIONS` entry, read off the tree, not copied from the README. Read it before calling any
tab real. Summary: `charting` `overview` `family` `insurance` `appts` `notes` `labs` `medical-hx`
`forms` `history` `schedule` are **live**; `billing` is claims-live + ledger-live; `docs` is **mock**
except lab cases; `journal` is **partial** (read-only, no write API); `tx-plans` is **partial** —
the list, create and "Generate from Chart" are now live against
`/v2/treatment-plans` (`be-treatment-plans`), but the full-screen builder, Present/Send and
the patient review page are not built yet; `images` and `comms` are **stubs**. Two corrections against `PMS_React/README.md:233-249`: Post-Op is **commented out**
(`patientSections.js:81-87`), so **17** render not 18; and its "ledger mock" is stale —
`billing/BillingSection.jsx:11` imports the real `ledger/LedgerWorkspace` (`README.md:17-19`, `:299`).

## Invariants

1. Never call `fetch`. Import from `src/api/patients.js`; never widen another module to `/v2/patients`.
2. Run every id through `parsePatientIdForApi()` and bail on `null` — chart ids may be placeholders.
3. Gating is env presence: `isPatientsApiEnabled()` means only "`VITE_APP_BASE_URL_AUTH` is
   non-empty". Unset it and the whole chart silently serves `src/data/patients.js` seeds.
4. `mapApiPatientToView` is the only place a raw patient payload may be read; `_api.raw` is for
   debugging, never logic. `view.dob` is a **display** string (`"Mar 5, 1988"`) — convert with
   `parseDobToISO()` before any wire write. ISO on the wire; there is no date library in this repo.
5. Hooks return `{ items, loading, error, source, isApiEnabled, refetch, ...mutators }` and guard
   async loads with a monotonic `generationRef`. Copy `src/hooks/usePatientAuditTrail.js` (86 lines).
6. Tab identity lives in `PATIENT_SECTIONS`. Never hardcode a section id or concatenate a chart URL.
7. Overlays: `createPortal` + `AnimatePresence` + `OverlayBackdrop` with `OVERLAY_Z_INDEX`
   (`PatientAlertsPanel.jsx` is the reference). Feedback is `const { toast } = useToast()` — never
   `alert`; `react-hot-toast` is not installed. Errors use `getErrorMessage(err, fallback)`.
8. Tailwind v4 utilities only, colors from `src/theme/theme.css` vars — never a hex literal. Reuse
   `shared/patientSectionUi.jsx` (`ApiErrorBanner`, `FormField`, `inputClass`…) over new controls.

## Working here

Adding a chart section takes **exactly four edits**:

1. Create `src/components/patient-detail/<section>/<X>Section.jsx` — default export taking
   `{ patient }`, plus `setHeaderSubtitle` if it drives the header subtitle.
2. Add a named `export function Patient<X>Page()` to `src/pages/PatientDetail.jsx`, reading context
   via the local `usePatientOutletContext()` (`:253`), which throws if `patient` is missing.
3. In `src/components/AppRoutes.jsx`, add `const Patient<X>Page = lazyNamed(() =>
   import('../pages/PatientDetail'), 'Patient<X>Page')` and `<Route path="<segment>"
   element={<Patient<X>Page />} />` inside the `/patients/:patientId` block — **above** the
   catch-all `<Route path=":section">`, or it renders the placeholder.
4. Add the entry to `PATIENT_SECTIONS` in `src/config/patientSections.js` with a `lucide-react`
   icon and `path: (id) => ROUTES.patientSection(id, '<segment>')`.

If the URL segment differs from the section id, also branch in `getActivePatientSectionId`
(`patientSections.js:158`) or the sidebar will not highlight. A new wire call is one exported
function in `src/api/patients.js` plus a `normalize*` in the section's `*Mappers.js`. Only
automated check: `npm run lint`. No test suite.

## Traps

- **`getClinicId()` (`src/api/patients.js:53`) defaults to clinic 1** when `VITE_CLINIC_ID` is unset
  or unparseable. Every other clinic-scoped module returns `null` and shows "No clinic selected"
  (`components/ledger/useLedgerClinicId.js:9`). This one guesses, and it is the one touching PHI —
  a misconfigured deploy reads another clinic's patients. Call sites: `patientApiService.js`,
  `usePatientAppointments.js:58`, `usePatientSidebarSummary.js:100`, `usePatientSearch.js:144`,
  `labs/`, `journal/`, `family/`, `tx-plans/`.
- **Audit trail has three names**: section id `audit-trail`, URL `/history`
  (`ROUTES.patientHistory`), API `GET /v2/patients/:id/audit-trail`. `getActivePatientSectionId`
  bridges them by hand (`patientSections.js:151`). Change one, change all four.
- **`notes/noteTemplates.js:119` `stripHtml` assigns to `innerHTML`** on a detached `<div>` to get
  plain text from stored note bodies (`NoteEditorDrawer.jsx:66`, `NotesSection.jsx:30`). No
  sanitizer exists in the repo; do not extend it. `journal/journalMappers.js:10` is a second copy.
- **Delete patient never reaches the network.** `PatientDetail.jsx:528` calls
  `PatientsContext.deletePatient` — an in-memory filter — then toasts "Patient deleted";
  `src/api/patients.js` exports no delete-patient function.
- `PatientsContext` state is seed data and dies on reload; `vite.config.js`'s
  `fullReloadOnContextHmr()` wipes it on any `src/context/` edit in dev too.
- `usePatientDetail` emits a fourth `source` value, **`'mock-fallback'`** (`:155`);
  `PatientDetail.jsx:611` keys its amber retry banner on exactly that string.
- Dead in this slice: `PatientDetailSkeleton.jsx` (reachable only from the legacy page; the live
  skeleton is `RouteFallback({ forPatientChart })` in `AppRoutes.jsx:91`) and `usePatientFamily.js`.

## See also

- `main-architecture` — hub, index, change log. Siblings that render inside this shell: `fe-charting` ·
  `fe-perio` · `fe-insurance-claims` · `fe-ledger` · `fe-labs` · `fe-forms` · `fe-scheduling`.
  `fe-platform` owns `AppRoutes.jsx`, `ROUTES`, `ui/Skeleton.jsx` and `lib/queryClient.js`;
  `fe-reports-worklists` owns `charts/NewPatientDrawer.jsx` and the `src/data/` seeds.
- `references/sections.md` — section inventory and stub evidence, hook catalogue, full
  `/v2/patients` route table, mapper gotchas, shell files, storage keys.
- `PMS_React/README.md:233-262`, `:441-490`, `:512-569`. `PROJECT_GUIDE.md` is stale — ignore it.
