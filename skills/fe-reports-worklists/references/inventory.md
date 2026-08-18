# fe-reports-worklists — inventory

Overflow detail for `SKILL.md`. All paths relative to `PMS_React/`. Verified against the working
tree; anything unconfirmed is marked **unverified**.

---

## 1. Revenue Reports — the 13 slugs

`src/data/dailyHuddleSeed.js:3` `HUDDLE_NAV`, four groups. `HUDDLE_REPORT_SLUGS:37` flattens them;
`isHuddleReportSlug:41` is the router guard; `getHuddleReportLabel:45` feeds `document.title`
(`DailyHuddleView.jsx:240-245`, format `"<label> · Revenue Reports"`).

| group | slugs |
|---|---|
| Financial | `daily-huddle` (**the only one with a body**), `daily-reconciliation`, `rcm-activity`, `production-collections`, `collections-summary`, `adjustments`, `aging` |
| Clinical | `case-acceptance`, `hygiene-metrics` |
| Operations | `patient-flow`, `scheduling-efficiency`, `provider-scorecard` |
| Settings | `goals` |

The other twelve render the centred "Coming soon — UI shell only until revenue APIs are available"
block plus a *Back to Daily Huddle* button (`DailyHuddleView.jsx:405-417`).

**The Daily Huddle body itself** (`:420+`): a location `SearchableSelect` and a provider
`SearchableSelect` (real options — `LocationContext` / `ProvidersContext`), three day tabs
(`HUDDLE_DAY_TABS:53` — Yesterday / Today / Monday, local state only), four `MetricCard`s
(`HUDDLE_METRICS:59`, each printing the literal `$0.00` at `:108`), a schedule list/grid toggle, a
group-by-provider toggle, five follow-up tabs (`HUDDLE_FOLLOW_UP_TABS:82`), a "No insights yet"
strip `:527`, and an export menu (`HuddleExportMenu:124`). `data-no-print="true"` marks the chrome
at `:284,338,440`. None of the filters is wired to anything that produces a number.

**Route plumbing.** `routes.js:11-12` (`revenueReports`, `revenueReport(slug)`), `:36`
(`DEFAULT_REVENUE_REPORT_SLUG`), `:44` (shares the `'scheduling'` transition key), `:67-73`
(`isNavItemActive` lights up Scheduling). `AppRoutes.jsx:198-212`: `/revenue-reports` redirects to
`ROUTES.revenueReport()`, `/revenue-reports/:reportSlug` renders `<RevenueReports />`.
`SchedulingContext.jsx:90` derives `isRevenueReportsRoute`, `:95` `huddleOpen`, `:228-252`
`openHuddle` / `closeHuddle` / `toggleHuddle` / `setHuddleOpen` — all four are `navigate()` calls,
there is no boolean state. `CalendarHeader.jsx:167` prefetches the chunk on idle via
`routePrefetch.js:6,24`; `:205` is the click. Escape inside the view calls `closeHuddle`
(`DailyHuddleView.jsx:248-256`).

---

## 2. The 11 worklists (`src/config/listsWorklists.js`)

Every entry is `{ id, label, navIcon, title, description, tabs[], filters[], empty{}, columns?,
primaryAction?, secondaryActions? }`. **All tab `count` values are literal `0`.** Only two entries
carry `columns` (so only those two render table chrome — `WorklistPanel.jsx:76,183`); only two
carry a `primaryAction`, and it is `disabled title="Coming soon"` (`:122-134`).

| id | line | tabs | columns? | primary action | secondary |
|---|---|---|---|---|---|
| `hygiene-recall` (**default**, `:20`) | 44 | active / disabled / all | yes (6) | Add recall | Due date settings, Print |
| `broken-appointments` | 80 | all-fallout / no-shows / late-cancels | — | — | Print |
| `unscheduled-treatment` | 103 | all / accepted / partially-accepted / active | — | — | Print |
| `reactivation` | 127 | all / ready / needs-contact | — | — | Print |
| `new-patients` | 149 | all / unscheduled / scheduled | yes (7) | — | Print |
| `post-op-follow-up` | 172 | all / pending / failed / awaiting-ack | — | — | Print |
| `approved-pre-auths` | 196 | all / approved / partially-approved | — | — | Print |
| `referred-patients` | 218 | all / unscheduled / scheduled / other-open | — | — | Print |
| `referrals-in` | 243 | all / new / needs-work / ready / scheduled | — | New referral | Print |
| `benefit-max` | 269 | all / stale / high-remaining / ready | — | — | Print |
| `asap-waitlist` | 293 | active / booked / all | — | Add waitlist patient | Print |

Note `asap-waitlist` here is **UI only** and unrelated to the real waitlist API described in
`be-recare-waitlist` / the Scheduling Queue drawer — do not conflate them.

**Panel behaviour** (`WorklistPanel.jsx`): filter controls are `<select>` elements with exactly one
`<option>`, their own label (`:19-29`) — they cannot filter. Tabs are local state with a
`resolvedTabId` fallback (`:82`). The footer is a hardcoded `0 shown` plus two permanently
`disabled` pagination buttons (`:197-217`). `RecallDueDateSettingsModal` mounts only when a
`due-date-settings` secondary action exists (`:219`), i.e. Hygiene recall only.

**Recall due-date modal** (`RecallDueDateSettingsModal.jsx`): six lists at `:12` — `bitewings`,
`fmx-pano`, `prophy-perio`, `exam`, `child-prophy`, `fluoride`; `DEFAULT_OFFSET = 1` (`:21`);
reads at `:23-32`, writes at `:137` to `localStorage['pms.recallDueDateOffsets']` as
`{ [listId]: integerDays }`; toasts "Recall due date settings saved" `:141`. **No other file in
the repo reads that key** (grep-verified) — the offsets affect nothing.

**Create-worklist modal** (`CreateWorklistModal.jsx`): `FILTER_CATALOG:25`, `AGE_RANGE_OPTIONS:63`,
`STATUS_OPTIONS:72`, `INSURANCE_STATUS_OPTIONS:78`; `matchesFilter:396` runs client-side over
`usePatients()` (`:423`), preview capped at 8 rows (`:459`); `canCreate` needs a name and ≥1 filter
(`:460`); `handleCreate:469` only toasts. Two nested portals (`FilterPicker:160`,
`ValuePicker:288`) sit at `OVERLAY_Z_INDEX.modalPanel + 10` — an arithmetic z-index, not a map key.

---

## 3. Documents (`src/pages/Documents.jsx`)

`TABS:24` (All Documents / Review Queue) · `SORT_OPTIONS:29` (5) · `PAGE_SIZE_OPTIONS:37`
(25/50/100) · `DOC_ACTIONS:39` (View, Rename, Move to folder, Download, Delete). Sub-components:
`SortBySelect:50`, `DocumentRowActions:189`, `RowsPerPageSelect:336`. Search is debounced 250 ms
(`:412-415`). `emptyCopy:417` varies by tab and by whether a search is active. `documents = []`
(`:441`) with the comment "No documents API yet — keep list empty (no static / lab stand-in rows)";
`handleDocAction:443` and `comingSoon:437` both toast. The header docstring says "UI shell only
until a documents API is available".

---

## 4. Shared widgets — `src/components/charts/`

| component | props |
|---|---|
| `DatePickerField` `:82` | `value, onChange, placeholder='MM/DD/YYYY', minYear=1920, maxYear=+2, className, displayFormat='mdy', size='md', disabled, ariaLabel, minDate, maxDate` |
| `MultiDatePicker` `:56` | `value=[], onChange, disabled, minYear=-1, maxYear=+2, className, ariaLabel` |
| `FilterPopover` `:44` | `filters, onFiltersChange, onClearAll, showClear=false` |
| `NewPatientDrawer` `:201` | `open, onClose, onSubmit, mode='create'\|'edit', initialValues` |

`DatePickerField` internals: `parseISO:30`, `toISO:37`, `formatDisplay:42`, `isSameDay:63`, day /
month / year views, `POPOVER_GAP = 4` and `POPOVER_Z = 100` at `:7-8`, portal to `document.body`
at `:603`. `minDate`/`maxDate` gate **day cells only** — the month and year views stay navigable
by design (comment at `:94-96`). `MultiDatePicker` has its own `parseISO:22` / `toISO:29` /
`formatChip:34` and renders **inline, no portal**.

**`DatePickerField` importers (22)** — ledger dialogs (`EnterCharge/CreditAdjustment`,
`EnterPayment`, `EnterInsurancePayment`, `EnterProcedure`, `PatientWalkout`, `ViewTransaction`),
`LedgerViewMenu`, `ContractedProvidersPanel`, `FeeScheduleDefaultsPanel`, `OperatingHoursPanel`,
`ScheduleBlockFormModal`, `NewFeeScheduleModal`, claims (`ClaimGeneralTab`, `CreateClaimsDialog`),
`AddInsuranceDialog`, `AddAppointmentDrawer`, `AuditTrailSection`, `JournalSection`,
`LabOrderDrawer`, `AppointmentDetailDrawer`, `RescheduleAppointmentModal`, `NewPatientDrawer`.

`MultiDatePicker` → `settings/scheduling/scheduleGroups/ScheduleProviderWizardModal.jsx:8` only.
`FilterPopover` → `pages/PatientCharts.jsx:33` only (reads `src/data/filters.js`).
`NewPatientDrawer` → `PatientCharts.jsx:34`, `PatientDetail.jsx:21`, and the dead
`PatientDetail.legacy.jsx:29`; it validates through `utils/patientForm.js` (`EMPTY_PATIENT_FORM`,
`validatePatientForm`) and never calls an API itself — the caller's `onSubmit` does.

---

## 5. `src/data/` — full seed → importer map

| file | importers |
|---|---|
| `appointmentsSeed.js` | none directly; re-exported by `scheduling.js:77`, consumed as `APPOINTMENTS` in `context/SchedulingContext.jsx:13,143,1443` |
| `scheduling.js` | 28 files — `charts/MultiDatePicker`, `charts/DatePickerField`, `patient-detail/appts/{ApptsSection,AddAppointmentDrawer}`, `patient-detail/journal/journalMappers`, 16 under `components/scheduling/`, `context/SchedulingContext`, `hooks/{useAppointmentDrag,usePatientSidebarSummary}`, `utils/{appointmentMove,appointmentQueries,patientForm,patientMappers}` |
| `patients.js` | `context/PatientsContext.jsx:2,7` (`patients`), `components/ui/Skeleton.jsx:1` (`TABLE_COLUMNS`), `pages/ledger/Ledger.jsx:15` (`PAGE_SIZE_OPTIONS`). `TOTAL_PATIENTS` (`:1`) has **no importer** |
| `patientSubresources.js` | `patient-detail/{contact/ContactPanels,family/FamilySection,family/AddFamilyMemberModal,forms/FormsSection,medical-hx/MedicalHxSection,notes/NotesSection,PatientAlertsPanel,audit/auditMappers}`, `hooks/{usePatientContact,usePatientNotes,useRelatedPeople,usePatientChartAlerts,usePatientForms,usePatientMedicalHx}` |
| `filters.js` | `charts/FilterPopover.jsx`, `pages/ledger/Ledger.jsx` |
| `billingMock.js` | `hooks/usePatientClaims.js` |
| `practices.js` | `utils/locationUtils.js:1,221` |
| `practiceForms.js` | `pages/Forms.jsx` |
| `demoPatientFormSchema.js` | `scheduling/CheckInFormsStep.jsx`, `scheduling/VisitStatusBoard.jsx`, `pages/PatientFormLinkPage.jsx` |
| `dailyHuddleSeed.js` | `scheduling/DailyHuddleView.jsx` |

---

## 6. QA scripts (`PMS_React/scripts/`, not in `package.json`)

`npm run` cannot reach them — `package.json:6-11` has only `dev`, `build`, `lint`, `preview`. Run
`node scripts/qa-data-integrity.mjs` / `node scripts/qa-e2e-flow.mjs` by hand.
`eslint.config.js` globs only `**/*.{js,jsx}`, so neither file is linted and neither gets Node
globals (`PMS_React/README.md:563-564`).

**`qa-data-integrity.mjs`** (66 lines) — `readFileSync` on `src/data/patients.js` and
`src/data/appointmentsSeed.js` (`:48-49`), then **regex text extraction**: `extractPatientIds:12`
(`/id:\s*'(\d+)'/g`), `extractAppointments:27` (splits on `\n  {\n`), `extractAppointmentDate:20`,
`checkStalePatientFields:39` (flags `lastVisit`, `last_visit`, `next_appointment_id`, `history[]`).
Reports orphaned `patient_id` refs but **exits `0` for them** — only stale fields or a missing date
fail the run (`:66`). Reformatting either seed can break the parse without any error.

**`qa-e2e-flow.mjs`** (227 lines) — `:13` "Inline appointment query logic (mirrors
`src/utils/appointmentQueries.js`)", then re-implements `getSchedulingReferenceNow:14`,
`toDateISO:23`, `parseAppointmentDate:27`, `getAppointmentDateTime:34`,
`filterValidAppointments:41`, `getAppointmentsForPatient:51`, `getNextAppointmentForPatient:57`,
`getPastAppointmentsForPatient:69`, `getLastVisitForPatient:79`, plus `createTestPatient:84`.
Because the logic is copied, the script can pass while the real module is broken. Exits non-zero
only if a check fails (`:227`).

---

## 7. Dead code confirmed here

- `src/hooks/useMockLoad.js` — `useMockLoad:7`, `useMockTabLoad:23`. Sole importer is
  `src/pages/PatientDetail.legacy.jsx:51`, which has **no importer at all** (grep-verified). Both
  delays are `0` (`src/config/loading.js:2,5`), and `MOCK_FETCH_MS:8` is marked `@deprecated`.
- `src/pages/PatientDetail.legacy.jsx` — 31,933 bytes, no importer. Absent from the README's
  dead-code list at `PMS_React/README.md:544-552`.
- `src/data/patients.js:1` `TOTAL_PATIENTS = 19470` — a fabricated headline figure with no reader.
  Do not resurrect it into a UI.
