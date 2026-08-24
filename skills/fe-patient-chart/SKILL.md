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
| `src/components/patient-detail/<section>/` | Owned: `appts` 2 files · `audit` 2 · `comms` 1 · `contact` 1 · `docs` 4 · `family` 3 · `images` 1 · `journal` 2 · `medical-hx` 12 · `notes` 5 (TipTap) · `schedule` 1 · `tx-plans` 7 + `builder/` 15 (adds `treatmentPlanPdf.js`, `comparePlans.js`, `ComparePlansModal.jsx`) (`TxPlansSection`, `ChartFindingsCard`, `TxPlansTable`, two drawers, `txPlanFormat.js`, `txPlanUi.jsx`; backed by `src/api/treatmentPlans.js` + `hooks/usePatientTreatmentPlans.js` + `hooks/usePatientChartFindings.js`). **Not owned, sitting in this tree:** `charting/` + `charting/perio/` (fe-charting / fe-perio), `insurance/` 9 + `billing/` 6 (fe-insurance-claims), `forms/` 4 (fe-forms), `labs/` 2 (fe-labs). Largest owned: `appts/AddAppointmentDrawer.jsx` 1334, `docs/DocsSection.jsx` 994. |
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
except lab cases; `journal` is **partial** (read-only, no write API); `tx-plans` is **live** —
the list, create, "Generate from Chart", the full-screen builder, Present, Send and the
public patient review page at `/tp/:token` (`pages/SharedTreatmentPlanPage.jsx`,
`AppRoutes.jsx:177`) all work against `/v2/treatment-plans` (`be-treatment-plans`), and the
page opens on a **Chart Findings** summary (`usePatientChartFindings`) over a paginated
`TxPlansTable`. (An earlier revision of this file claimed Present/Send and the review page
were unbuilt — they are `handlePresent` / `handleSend` in `TreatmentPlanBuilder.jsx` and the
route above.) `images` and `comms` are **stubs**. Two corrections against `PMS_React/README.md:233-249`: Post-Op is **commented out**
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
- **The plan list read is NOT location-scoped, and must not become so again.**
  `usePatientTreatmentPlans` sends only `clinic_id`; the charting tab's
  `TreatmentListingPanel` sends nothing at all. Adding `location_id` back makes a plan the
  charting tab lists vanish from `/tx-plans` with no error and no empty-state saying why —
  a plan belongs to the patient, not the operatory it was drawn up in. `create` still
  stamps a `locationId`, because the API requires one.
- **Every entry in the builder's "⋯" menu now does real work**, and two of the reasons it used
  to give for disabling them were simply wrong. Duplicate needs no new endpoint (`POST
  /v2/treatment-plans` takes phases and items inline — `planToDuplicatePayload` in
  `builder/treatmentPlanDraft.js`), and neither does Compare (two detail reads joined on
  code+tooth — `builder/comparePlans.js`, rendered by `ComparePlansModal.jsx`). Download PDF is
  client-side jsPDF (`builder/treatmentPlanPdf.js`); `jspdf` was already a dependency and the
  prior art is `docs/docsFolders.js`. **Pre-authorization was removed, not disabled** — it
  belongs to the claims service, which this app does not talk to, so a permanently dead row
  only taught operators to distrust the menu. `planSaved` is the one thing that still disables
  a row: an unsaved draft has no id to fetch, duplicate or render.
- **The PDF must never print `$0.00` for a missing figure.** It renders money through
  `formatCents`, which gives "No Est." for `null`. Its filename deliberately excludes the
  patient's name (a downloads folder is often shared or screen-shared) and the signature
  IMAGE is deliberately not embedded — the signed name and date carry the same meaning without
  copying PHI into a file that gets emailed on.
- **The PDF's three money columns are RIGHT-aligned anchors, not left edges.** `COL`
  in `builder/treatmentPlanPdf.js` names the right edge of each column, so the label must be
  wrapped to `COL.fee - LABEL_GUTTER` — a gutter wide enough for the widest figure. A 16pt
  gutter printed `$12,480.00` straight through the procedure description on every wrapped
  line. Two more rules there, both measured rather than guessed: reserve an item's height
  AFTER measuring its wrapped label (a constant reserve stranded a `code · #tooth` line at the
  top of the next page, above a DIFFERENT procedure — a consent problem on a signed document),
  and redraw the column heads whenever `ensureSpace` reports a page break. Verified by parsing
  the generated content stream: 0 collisions, ink stops exactly on the 556pt text edge, heads
  on every item page, 0 orphaned detail lines across 12–30 items.
- **The email composer edits a BODY, never the whole email.** `EmailTemplateEditor` renders
  the chrome — banner, card, Review button — as fixed React markup and puts only the message
  in TipTap (already a dependency; StarterKit v3 ships `link` and `undoRedo`, so Bold /
  Italic / Link / Undo / Redo need no extra package). Nothing assigns `innerHTML` and nothing
  arbitrary is parsed, which is the only way to have a WYSIWYG email in a repo with no
  sanitiser (§7.4). `buildTreatmentPlanEmailHtml` composes the outgoing string with INLINE
  styles and no classes — an email client strips stylesheets, which is also why the hex
  values in that file are not a §6.4 violation. The template leaves the browser with its
  `[Bracketed]` variables intact; the server fills them.
- **The signature pad erased itself, and `null` was the reason.** `SignaturePad` in
  `builder/TreatmentPlanPatientPreview.jsx` wiped the canvas whenever
  `signature === null && hasInk`. But `signature` is null for TWO different reasons — the
  parent cleared it, and the parent has not been told yet — and the second is the normal
  state while somebody is drawing, because the pad only publishes on `pointerup`. So the
  first stroke set `hasInk`, the effect saw a null `signature`, and it cleared the canvas:
  measured as `stroke -> clearRect -> stroke -> clearRect`. Ink never accumulated and
  `onSignatureChange` never fired, so Sign and submit stayed disabled forever. It is keyed
  on a `publishedRef` now, which tells the two cases apart. **This is the same class of bug
  as `teeth` and the `plan.isArchived` chip: `null` and "not set yet" are not the same
  value, and collapsing them is how this repo breaks.**
- **Canvas bitmaps need a ResizeObserver, not one `requestAnimationFrame`.** The same pad
  sized its bitmap in a single rAF that bailed silently on a zero-size measurement — and
  StrictMode double-invokes the effect, so the cleanup cancelled the pending frame. The
  bitmap stayed at the browser default 300x150 under a 686px box, putting every stroke past
  ~44% of the pad off-canvas. `App.jsx` has the SAME rAF-then-setState pattern for its
  full-screen `AppLoader`: if that frame never runs (a hidden or non-compositing tab), the
  white `fixed inset-0 z-50` overlay never lifts and swallows every pointer on the page.
- **`/tp/:token` is PUBLIC and must render standalone.** `App.jsx` decides whether to wrap
  `AppRoutes` in `AppLayout`, and it listed `/f/` but not `/tp/` — so a patient opening
  their own treatment plan got the practice's internal sidebar (Scheduling, Patients,
  Labs, Claims) wrapped around it. `AppRoutes.jsx` already drew the distinction correctly
  for its Suspense fallback (`isPublicPlanLink`); the same test now exists in both. Any new
  public token route must be added in BOTH places.
- **The patient page opens on a DOB gate and never probes.** `SharedTreatmentPlanPage`
  issues no request at all until the patient submits a date — an unverified GET would
  answer "is this token real?" for anyone holding a guess, and could be polled to learn the
  moment the patient signs. The access credential lives in component state, never storage
  (§7.3), so a refresh re-prompts on purpose. The DOB goes in the POST BODY: in a query
  string it would land in access logs and Referer headers. The field asks for THE PATIENT'S
  date of birth, not "your" — plans are routinely opened by a parent or a spouse, and
  "your" invites them to spend the attempt budget on a value that could never match.
- **OPENING A DIALOG MUST NOT WRITE TO THE PLAN.** `handleSend` used to call
  `presentTreatmentPlan` + `shareTreatmentPlan` before showing the compose form, just to have a
  link ready. So merely clicking Send marked the plan Proposed, stamped `presented_at`, opened a
  public review token and surfaced "Mark response" — before an address was typed, and even if the
  operator cancelled or had no email on file. The record said the patient had been asked when
  nobody had. `handleSend` is now `setSendOpen(true)` and nothing else: the server's
  `send_treatment_plan` presents a draft and issues the token as part of delivering, and Copy link
  on the SMS tab mints one on click. Only `handlePresent` and `handleCopyShareLink` may present or
  share, and both are explicit operator actions.
- **"Mark response" is gated on evidence the patient was actually asked** — `presentedAt`,
  `isShared`, or decisions already recorded — not on status alone. Note the gate alone was NOT
  enough: while opening the send dialog set those fields, no gate built on them could work. Fix
  the write, not the reader. The already-answered clause still matters: without it a legacy plan
  carrying decisions but no `presented_at` loses the button needed to amend them.
- **Removing a plan is ARCHIVE, never void and never delete.** The builder's
  "Archive / delete Treatment Plan" menu item used to call `voidTreatmentPlan`, so a plan
  somebody tried to put away came back in the listing as a row reading "Void" — that is the
  bug the archive feature exists to fix. The client now exposes only
  `archiveTreatmentPlan` / `unarchiveTreatmentPlan`; `voidTreatmentPlan` and
  `deleteTreatmentPlan` are gone from `src/api/treatmentPlans.js`, and `deletePlan` /
  `voidPlan` from `usePatientTreatmentPlans`. Both server endpoints still exist and are
  still tested in `be-treatment-plans` — do not re-add a client for either without a
  screen that needs it. Archive 409s when the plan's work is already booked; surface that
  message rather than a generic failure.
- **Archived plans are hidden server-side**, so `usePatientTreatmentPlans` and the charting
  tab's `TreatmentListingPanel` both stop showing them with no client-side filter. The only
  way back is `includeArchived` → `?include_archived=true`, which the "Show archived"
  checkbox on `TxPlansSection` passes down. Delete that toggle and archive becomes one-way.
  `isPlanEditable()` and `planLockReason()` read `plan.isArchived`, mirroring the server's
  `_archived_error`; without that the builder renders an archived plan fully editable and
  the operator finds out one 409 at a time.
- **New Plan on `/tx-plans` opens the same unsaved draft builder charting opens**
  (`TreatmentPlanBuilder` with `planId={null}` + `seedFindings` + `draftProviderId`), not a
  create-then-open POST. The provider comes from Settings → Tooth Chart Defaults →
  Default Provider via `useClinicChartSettings()`; send `provider.apiId`, never `provider.id`,
  which is a String the API rejects. With no default configured it falls back to
  `NewTreatmentPlanDrawer`, which asks for one.
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
