---
name: fe-patient-chart
description: Patient chart shell and non-clinical tabs — /patients/:patientId/*, the Patient<X>Page exports in PatientDetail.jsx, the patientSections.js registry, the appts/audit/docs/family/journal/medical-hx/notes/post-op/tx-plans sections, and the public /tp/:token plan page. Use when adding a chart tab, editing src/api/patients.js or treatmentPlans.js, touching a usePatient* hook, or debugging /v2/patients, audit-trail vs /history, or getClinicId(). Not charting, perio, insurance, billing or labs.
---

## Scope

The chart shell at `/patients/:patientId/*` — an 18-entry section grid in a left sidebar over an `<Outlet>` —
plus the `/patients` list, the patient data layer (`PMS_React/src/api/patients.js`, its mappers, the
`usePatient*` hooks, `PatientsContext`), and treatment plans end to end including the public `/tp/:token` page.
**Not owned, though they render in this shell:** `charting/` + perio, `insurance/` + `billing/` (plus fe-ledger
for Ledger), `forms/`, `labs/`, `schedule`. Maturity is **mixed** — read `references/sections.md` §1, not the screen.

## Files

| path (under `PMS_React/`) | role |
|---|---|
| `src/pages/PatientDetail.jsx` | **(entry)** 693 lines / 25KB. Default export = the shell; **18** named `Patient<X>Page` exports (`:262`–`:393`) plus `PatientSectionPlaceholderPage` (`:395`) are the route elements. `OverviewTab` is inline at `:176`. |
| `src/config/patientSections.js` | 179 lines. `PATIENT_SECTIONS` (`:22`, 18 entries), `SECTION_BY_ID` `:151`, `getActivePatientSectionId` `:157`, `getPatientSectionTitle` `:170`. |
| `src/pages/PatientCharts.jsx` · `PatientDetail.legacy.jsx` | 804 / 887 lines, 31KB each — `grep`/`sed -n`, never read whole. The first is the patient list at `/patients` **and** `/`; the second is **dead**, imported nowhere in `src/`. Do not edit or copy from the legacy file. |
| `src/components/patient-detail/` shell | `PatientChartSidebar.jsx` 529 · `PatientAlertsPanel.jsx` 354 · `PatientSectionHeader.jsx` 122 · `PatientSectionPlaceholder.jsx` 18 · `PatientDetailSkeleton.jsx` 207 (dead, see Traps) · `shared/patientSectionUi.jsx` 88 · `shared/SimpleFormDialog.jsx` 119. |
| `src/components/patient-detail/<section>/` | Owned: `appts` 2 · `audit` 2 · `comms` 1 · `contact` 1 · `docs` 5 · `family` 3 · `images` 1 · `journal` 2 · `medical-hx` 12 · `notes` 5 (TipTap) · `post-op` 4 · `schedule` 1 · `tx-plans` **7 files + `builder/` 17** (map in `references/tx-plans.md` §1). **Not owned, in this tree:** `charting/` incl. `perio/` + `treatment-listing/`, `insurance/` 9 + `billing/` 3, `forms/` 5, `labs/` 2. Largest owned: `builder/TreatmentPlanBuilder.jsx` 1599, `docs/DocsSection.jsx` 1537, `appts/AddAppointmentDrawer.jsx` 1334. |
| `src/api/patients.js` | 328 lines. The only patient wire module; `authApi` + a local `unwrap()` `:8`; `getClinicId` `:53`; re-exports the forms endpoints from `./forms` `:306`-`:315`. Hooks reach it via `src/services/patientApiService.js` (203). |
| `src/api/treatmentPlans.js` · `src/api/documents.js` · `src/pages/SharedTreatmentPlanPage.jsx` | 909 / 280 / 585 lines. The first two are on **`chartApi`** and **`appointmentApi`**: `PLAN_STATUS` `:49`, `PLAN_STATUS_LABEL` `:75`, `isPlanEditable` `:104`, `planLockReason` `:118`, the `/shared/<token>` pair `:801`/`:819`. The third is the public two-factor plan page behind `/tp/:token`, rendered outside `AppLayout`. |
| `src/utils/patientMappers.js` · `patientTableQuery.js` · `src/context/PatientsContext.jsx` | 252 / 132 / 68. `mapApiPatientToView`; the pure list search/filter/sort; an in-memory patient list seeded from `src/data/patients.js` — no persistence, no network. |
| `src/hooks/usePatient*.js` · `useRelatedPeople.js` · `useRecentPatients.js` · `useFamilyNote.js` | **16** hooks owned here; shapes in `references/sections.md` §2. Four are **not** owned: `usePatientAppointments` (fe-scheduling), `usePatientInsuranceData` (fe-insurance-claims), `usePatientLabCases` (fe-labs), `usePatientForms` (fe-forms). |

Touches (shared, not owned, under `src/`): `components/AppRoutes.jsx:41-81,338-366` (the `lazyNamed` block
and the patient route block) and `:177` (`/tp/:token`) · `config/routes.js:34-39` · `src/App.jsx:35`
(`isPublicPlanLink`) · `components/charts/NewPatientDrawer.jsx` · `components/ui/Skeleton.jsx` ·
`lib/queryClient.js:20` (`patientKeys`).

## Contract

Routes: `/patients/:patientId` (index → `Navigate to="overview"`, `AppRoutes.jsx:346`), 18 child segments,
then catch-all `:section` → `PatientSectionPlaceholderPage`; build URLs from `ROUTES.patient*`. Plus the
public `/tp/:token`. API: `api/patients.js` over `authApi` — collections nest under the patient
(`GET/POST /v2/patients/:id/<plural>`), item mutations do **not** (`PUT/DELETE /v2/patient-<plural>/:itemId`);
route table in `references/sections.md` §3. Plans go to `/v2/treatment-plans` over `chartApi`
(`be-treatment-plans`); documents to `api/documents.js` over `appointmentApi`. **Per-section maturity and
owning skill: `references/sections.md` §1**, read off the tree — read it before calling any tab real. Only
`images`, `comms` and `post-op` are stubs and `journal` is read-only-partial; everything else is live.
`PMS_React/README.md:256,:259` is stale on two (`tx-plans` "mock", Post-Op `available: false`).

## Invariants

1. Never call `fetch`. Import from `src/api/patients.js`; never widen another module to `/v2/patients`.
2. Run every id through `parsePatientIdForApi()` and bail on `null` — chart ids may be placeholders.
3. Gating is env presence: `isPatientsApiEnabled()` means only "`VITE_APP_BASE_URL_AUTH` is non-empty".
   Unset it and the whole chart silently serves `src/data/patients.js` seeds.
4. `mapApiPatientToView` is the only place a raw patient payload may be read; `_api.raw` is for debugging,
   never logic. `view.dob` is a **display** string (`"Mar 5, 1988"`) — `parseDobToISO()` before any wire
   write. ISO on the wire; there is no date library in this repo.
5. Hooks return `{ items, loading, error, source, isApiEnabled, refetch, ...mutators }` and guard async loads
   with a monotonic `generationRef`; copy `usePatientAuditTrail.js` (86 lines). Clinical and financial hooks
   refuse to seed — `usePatientTreatmentPlans` / `usePatientChartFindings` return empty with
   `source: 'unavailable'` rather than invent a plan or a finding.
6. Tab identity lives in `PATIENT_SECTIONS`. Never hardcode a section id or concatenate a chart URL.
7. Overlays: `createPortal` + `AnimatePresence` + `OverlayBackdrop` with `OVERLAY_Z_INDEX`
   (`PatientAlertsPanel.jsx` is the reference). Feedback is `useToast()`, never `alert`; errors go through
   `getErrorMessage(err, fallback)`.
8. Tailwind v4 only, colors from `src/theme/theme.css` vars — never a hex literal; reuse
   `shared/patientSectionUi.jsx` over new controls. Sole exemption: `builder/emailTemplate.js`, which must
   inline styles because email clients strip stylesheets.

## Working here

Adding a chart section takes **exactly four edits**:

1. Create `src/components/patient-detail/<section>/<X>Section.jsx` — default export taking `{ patient }`,
   plus `setHeaderSubtitle` if it drives the header subtitle.
2. Add a named `export function Patient<X>Page()` to `src/pages/PatientDetail.jsx`, reading context via the
   local `usePatientOutletContext()` (`:254`), which throws if `patient` is missing.
3. In `src/components/AppRoutes.jsx`, add `const Patient<X>Page = lazyNamed(() => import('../pages/PatientDetail'),
   'Patient<X>Page')` and `<Route path="<segment>" …/>` inside the `/patients/:patientId` block, **above** the
   catch-all `<Route path=":section">` (`:365`) or it renders the placeholder.
4. Add the entry to `PATIENT_SECTIONS` in `src/config/patientSections.js` with a `lucide-react` icon and
   `path: (id) => ROUTES.patientSection(id, '<segment>')`.

If the URL segment differs from the section id, also branch in `getActivePatientSectionId`
(`patientSections.js:157`) or the sidebar will not highlight. A new wire call is one exported function in
`src/api/patients.js` plus a `normalize*` in the section's `*Mappers.js`. A new **public** token route is two
edits: the route in `AppRoutes.jsx` **and** the prefix test in `src/App.jsx:35`. Only check: `npm run lint`.

## Traps

- **`getClinicId()` (`src/api/patients.js:53`) defaults to clinic 1** when `VITE_CLINIC_ID` is unset or
  unparseable. Every other clinic-scoped module returns `null` instead (`ledger/useLedgerClinicId.js:19-28`,
  whose comment says "do not copy that here"). This one guesses, and it is the one touching PHI — a
  misconfigured deploy reads another clinic's patients. ~15 call sites incl. `patientApiService.js:135,175`,
  `usePatientSidebarSummary.js:100`, `usePatientSearch.js:144`, `TxPlansSection.jsx:33`.
- Treatment-plan hard rules. The evidence and the bug each came from are in **`references/tx-plans.md` §3** — read it before changing anything under `tx-plans/`.
  - Removing a plan is **archive** — `voidTreatmentPlan` / `deleteTreatmentPlan` are gone from `src/api/treatmentPlans.js`.
  - Archived plans are hidden server-side; the "Show archived" toggle (`includeArchived` → `?include_archived=true`) is the only way back, and `isPlanEditable` `:104` reads `plan.isArchived`.
  - The plan list read is **not** location-scoped and must not become so again.
  - `/tp/:token` is public and renders **standalone**; any new public route needs `App.jsx:35` as well as `AppRoutes.jsx`.
  - That page opens on a **DOB gate**: no request until a date is posted, DOB in the **body**, `X-Plan-Access` held in component state and never in storage (§7.3).
  - **Opening a dialog must not write to the plan** — `handleSend` is `setSendOpen(true)` and nothing else; only `handlePresent` / `handleCopyShareLink` present or share.
  - `scheduled` is a **real server status** (`treatmentPlans.js:54`, mirroring the widened `ck_treatment_plans_status`), not a client-derived label.
  - Signature pad: the clear is keyed on `publishedRef`, the bitmap is sized by a `ResizeObserver` — one `requestAnimationFrame` is not enough (`App.jsx:61` still has that shape).
  - PDF: `COL` `:36` names a column's **right edge** and `LABEL_GUTTER` is 70 `:39`; it prints "No Est.", never `$0.00`, and omits the patient name and the signature image.
  - `EmailTemplateEditor` edits a **body only**; `buildTreatmentPlanEmailHtml` inlines styles, leaves `[Bracketed]` variables for the server, and nothing assigns `innerHTML`.
- **Audit trail has three names**: section id `audit-trail`, URL `/history` (`ROUTES.patientHistory`), API `GET /v2/patients/:id/audit-trail`; `getActivePatientSectionId` bridges them at `patientSections.js:166`. Change one, change all.
- **`notes/noteTemplates.js:122` `stripHtml` assigns to `innerHTML`** on a detached `<div>` for stored note
  bodies (`NoteEditorDrawer.jsx:66`, `NotesSection.jsx:30`). No sanitizer exists here; do not extend it. Its
  old twin `journal/journalMappers.js:10` is a regex now and is **fixed** — copy that one.
- **Delete patient never reaches the network.** `PatientDetail.jsx:542` calls `PatientsContext.deletePatient`
  — an in-memory filter — then toasts "Patient deleted"; `src/api/patients.js` exports no delete function.
  That context is seed data and dies on reload; `fullReloadOnContextHmr()` wipes it on `src/context/` edits.
- `usePatientDetail` emits a fourth `source` value, **`'mock-fallback'`** (`:155`); `PatientDetail.jsx:626` keys its amber retry banner on exactly that string.
- Dead here: `usePatientFamily.js`, and `PatientDetailSkeleton.jsx` (only consumer is the dead
  `PatientDetail.legacy.jsx:833` via `ui/Skeleton.jsx:4`; the live skeleton is `AppRoutes.jsx:95`).

## See also

- `main-architecture` — hub, index, change log. Siblings rendering inside this shell: `fe-charting` ·
  `fe-perio` · `fe-insurance-claims` · `fe-ledger` · `fe-labs` · `fe-forms` · `fe-scheduling`.
  `be-treatment-plans` is the server side of `/v2/treatment-plans`. `fe-platform` owns `AppRoutes.jsx`,
  `App.jsx`, `ROUTES`, `ui/Skeleton.jsx`, `lib/queryClient.js`; `fe-reports-worklists` owns
  `charts/NewPatientDrawer.jsx` and `src/data/`.
- `references/sections.md` — section inventory and stub evidence, hook catalogue, `/v2/patients` route table,
  mapper gotchas, shell files, storage keys. `references/tx-plans.md` — tx-plans file map, the builder /
  send / share / archive flow, long-form traps.
- `PMS_React/README.md` `:236` Patient chart · `:444` structure · `:511` conventions · `:582` known gaps. `PROJECT_GUIDE.md` is stale — ignore it.
