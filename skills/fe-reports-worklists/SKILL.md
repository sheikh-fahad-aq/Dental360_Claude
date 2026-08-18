---
name: fe-reports-worklists
description: The thin pages — /revenue-reports (Daily Huddle shell), /lists/:worklistId (11 placeholder worklists), /documents — plus the shared widgets in src/components/charts/ (DatePickerField, MultiDatePicker, FilterPopover, NewPatientDrawer) and the index of every mock seed in src/data/. Use when editing RevenueReports.jsx, Lists.jsx, Documents.jsx, src/components/lists/*, listsWorklists.js, a hand-rolled date picker, useMockLoad.js or scripts/qa-*.mjs, or when answering "is this screen real?".
---

## Scope

What is left after the live modules: the `/revenue-reports` shell, the Lists worklists, Documents,
four shared widgets in `src/components/charts/`, and `src/data/`. **Nothing on those three pages
should be demoed as working.** Huddle tiles are the string `$0.00` and twelve of its thirteen slugs
render "Coming soon — UI shell only until revenue APIs are available"
(`DailyHuddleView.jsx:108,410`); all 11 worklists are chrome over an `EmptyState` and a literal
"0 shown" (`WorklistPanel.jsx:198`); Documents is `const documents = []` with every row action
toasting (`Documents.jsx:441,444`). README: `/lists/:worklistId` **placeholder**, `/documents`
**chrome only** (`README.md:193,196,374-375`); `/revenue-reports` **is absent from the README** —
it postdates it, so this skill is its only record. Widgets and seeds are the opposite: unglamorous,
load-bearing. `DailyHuddleView.jsx` sits in `components/scheduling/`, mapped by **`fe-scheduling`**
— owned here are the route contract, slug config and seed.

## Files

| path (under `PMS_React/`) | role |
|---|---|
| `src/pages/RevenueReports.jsx` | **(entry)** 10 lines, whole file — a `<div>` around `<DailyHuddleView />`. Does **not** read `:reportSlug`. |
| `src/components/scheduling/DailyHuddleView.jsx` · `src/data/dailyHuddleSeed.js` | 639 / 88. The view is **linked, not owned** (`fe-scheduling`): slug resolve `:233`, invalid-slug redirect `:268`, "Coming soon" branch `:405-417`, `MetricCard` `:84`. The seed is labels only — `HUDDLE_NAV` (13 slugs, 4 groups) `:3`, `HUDDLE_REPORT_SLUGS` `:37`, `isHuddleReportSlug` `:41`, day tabs `:53`, tiles `:59`, follow-up tabs `:82`. |
| `src/pages/Lists.jsx` · `src/config/listsWorklists.js` | **(entry)** 94 / 325. Page = two `<Navigate>` guards `:19-25`, and `key={worklist.id}` on the panel `:88` is what resets tab state. Config = the 11 worklists (tabs, filters, optional `columns`, actions, empty state), `DEFAULT_LIST_WORKLIST_ID` `:20`, `getListWorklistById` `:319`, `isValidListWorklistId` `:323`. |
| `src/components/lists/WorklistPanel.jsx` · `ListsSidebar.jsx` | 8.6 / 3 KB. Header, tabs, filters, table chrome, footer — no rows. Only `due-date-settings` is enabled (`:102`); the rest are `disabled title="Coming soon"`. Sidebar counts hardcode `0` (`:36`). |
| `src/components/lists/CreateWorklistModal.jsx` (28 KB) · `RecallDueDateSettingsModal.jsx` | Filter builder with a convincing preview — `usePatients()` `:423`, client filter `:454`, discarded on Create, which only toasts "saved locally" `:471`. The recall modal is the only Lists control that persists: 6 lists `:12` → `localStorage['pms.recallDueDateOffsets']` `:9,137`, which nothing reads back. |
| `src/pages/Documents.jsx` (664) | **(entry)** Tabs, debounced search, sort/page-size/row menus, empty state. `documents = []` `:441`; the five `DOC_ACTIONS` `:39` all toast `:444`. |
| `src/components/charts/DatePickerField.jsx` (23 KB / 606) · `MultiDatePicker.jsx` · `FilterPopover.jsx` · `NewPatientDrawer.jsx` (27 KB) | 606 / 272 / 334 / 691. `DatePickerField` is **the repo's date input — 22 importers**, live in ledger dialogs, claims, insurance, labs, settings, scheduling; hand-rolled `parseISO` `:30` / `toISO` `:37`, portal `:603`. The other three have one importer each except the drawer (`PatientCharts.jsx`, `PatientDetail.jsx`, + dead `PatientDetail.legacy.jsx`). |
| `src/hooks/useMockLoad.js` · `scripts/qa-data-integrity.mjs` · `qa-e2e-flow.mjs` | 38 / 2.5 KB / 7 KB. The hook is **effectively dead** (sole importer `PatientDetail.legacy.jsx:51`; delays are `0` — `config/loading.js:2,5`). Scripts are **not in `package.json`** and read only mock seeds. |

| **`src/data/` — the mock index** (the answer to "is that number real?"; three of these mix live static config with seed rows) | maturity | who reads it |
|---|---|---|
| `appointmentsSeed.js` (224) · `scheduling.js` (316, **owned by `fe-scheduling`**, indexed here only) | **mock** `APPOINTMENTS` `:47`; **mixed, mostly live** — grid geometry `:9-19` plus a re-export of that seed at `:77`, so `scheduling.js` is *not* a mock file | `SchedulingContext.jsx:143,1443` reads the seed **only when `!isAppointmentsApiEnabled()`**; the constants have 28 importers (see `fe-scheduling`) |
| `patients.js` (221) | **mixed** — `patients[]` `:3` mock; `PAGE_SIZE_OPTIONS:211`/`TABLE_COLUMNS:213` live; `TOTAL_PATIENTS = 19470` `:1` fabricated, **no consumer** | `PatientsContext.jsx:7`, `ui/Skeleton.jsx:1`, `ledger/Ledger.jsx:15` |
| `filters.js` (46) · `practiceForms.js` (3) | **live static config** — filter catalog + counters; page sizes | `charts/FilterPopover.jsx`, `ledger/Ledger.jsx`; `pages/Forms.jsx` |
| `patientSubresources.js` (170) · `billingMock.js` (11) · `practices.js` (28) · `demoPatientFormSchema.js` (102) | **mock** — notes/related people/meds/vitals/phones/prefs + helpers; `MOCK_CLAIMS = []`; 3 practices; the demo intake schema | 14 importers, mostly `fe-patient-chart` hooks that start `source: 'mock'`; `hooks/usePatientClaims.js`; `utils/locationUtils.js:1,221`; check-in / `VisitStatusBoard` / `/f/:token` (see `fe-forms`) |

Touches: `config/routes.js:11-14,24,36,44,67-73`; `AppRoutes.jsx:198-212,214-228,280-286`;
`config/navigation.js:30,34`; `routePrefetch.js:6,24`; `SchedulingContext.jsx:90,95,228-252`;
`CalendarHeader.jsx:167,205`; `ui/OverlayBackdrop.jsx`; `config/loading.js`.

## Contract

Renders `ROUTES.revenueReports` / `revenueReport(slug)`, `ROUTES.lists` / `listsWorklist(id)` and
`ROUTES.documents`, each `lazy()` + `ProtectedRoute` in `AppRoutes.jsx`. **No owned file imports
from `src/api/` — grep-verified;** the only network data here arrives via `ProvidersContext`,
`LocationContext` and `SchedulingContext`. `/revenue-reports` has **no sidebar entry** — its sole
entry is the Daily Huddle button in the calendar header (`CalendarHeader.jsx:205` → `openHuddle`),
and `isNavItemActive` deliberately lights up *Scheduling* there (`routes.js:67-73`). Huddle
open/closed **is the URL**: `huddleOpen = isRevenueReportsRoute` (`:95`), Escape → `/scheduling`.

## Invariants

1. **Never present a number from these three pages as real.** Tiles are the literal `$0.00`
   (`DailyHuddleView.jsx:108,538`), every count a literal `0`, `documents` is `[]`. Wiring a real
   value in means deleting the hardcoded one in the same edit.
2. **A new worklist is one edit** — append to `LIST_WORKLISTS` (`listsWorklists.js:42`); sidebar,
   guard and panel derive from it, so add no route and no nav entry. And **`getListWorklistById`
   never returns undefined** (`:320` falls back to `[0]`) — validate with `isValidListWorklistId`
   first (`Lists.jsx:23`), or a typo silently shows Hygiene recall.
3. **Slugs live in `dailyHuddleSeed.js`; the default lives in `routes.js:36`** — duplicated as a
   literal in `revenueReport = (slug = 'daily-huddle')` (`routes.js:12`). Change both.
4. **There is no date library in this repo.** `DatePickerField`/`MultiDatePicker` hand-roll
   `parseISO`/`toISO` on `YYYY-MM-DD`; never add dayjs/date-fns/luxon, fix the widget — which is
   **live UI with 22 importers**, so open a ledger dialog and a settings panel before finishing.
5. **Overlays are `createPortal` + `AnimatePresence` + `OverlayBackdrop` with a named
   `OVERLAY_Z_INDEX` key** (`CreateWorklistModal.jsx:481`, `RecallDueDateSettingsModal.jsx:151`,
   `NewPatientDrawer.jsx:343`); feedback is `useToast()`, never `alert`; colours are theme tokens,
   never a hex; routes from `ROUTES`, nav from `config/navigation.js`.
6. **Do not add a patient-scoped `localStorage` key** (CLAUDE.md §7.3) — `pms.recallDueDateOffsets`
   is safe because it names no patient. Never log a row from `CreateWorklistModal`'s preview
   (§7.1): seed today, PHI the day `PatientsContext` is repointed.
7. **A page here that goes live grows a hook** returning `{ items, loading, error, source,
   isApiEnabled, refetch }` with a monotonic request-id guard, plus `normalizeX(raw)` in a new
   `src/api/` module. `source` must reach the UI — mock may never read as clinical fact (§5).

## Working here

1. `wc -l` first. Only `RevenueReports.jsx` (10) and `Lists.jsx` (94) are read-whole; `Documents`,
   `NewPatientDrawer`, `DatePickerField`, `CreateWorklistModal` want
   `grep -nE "^export |^function |^const [A-Z]"` then `sed -n`.
2. **Worklist change** → `listsWorklists.js` only; a *behaviour* also means unlocking a button in
   `WorklistPanel.jsx:102` (`enabled` is currently `isDueDateSettings`) and branching in
   `handleSecondaryAction` `:85`. **New huddle report** → one `HUDDLE_NAV` item; routable at once,
   rendering "Coming soon" until a panel lands at `DailyHuddleView.jsx:405`.
3. **New page** → the four README steps: `ROUTES`, `lazy()` + `<Route>` in `AppRoutes.jsx`, a
   `config/navigation.js` entry, a `getPageTransitionKey` branch. Skipping the nav entry is why
   `/revenue-reports` is reachable only from the calendar. **Touching a widget** →
   `grep -rn "charts/<Name>"` first; its blast radius is entirely outside this skill.
4. `npm run lint`. The QA scripts are not part of it — run those by hand after editing a seed.

## Traps

- **`RevenueReports.jsx` ignores `:reportSlug`** — validation, redirect and `document.title` all
  live in `DailyHuddleView.jsx:233-270`, so editing the shell to "fix routing" does nothing. **All
  13 slugs render one component**; twelve hit the `activeNav !== 'daily-huddle'` branch (`:405`).
- **`CreateWorklistModal` is the most convincing fake here** — a working filter builder over
  real-looking rows, all discarded on Create (`:471`). Those rows are `src/data/patients.js` via
  `PatientsContext.jsx:7`, **not** the patients API.
- **`DatePickerField` uses a local `POPOVER_Z = 100` (`:8`), above `OVERLAY_Z_INDEX.modalPanel`
  (90)** — deliberate, so the calendar clears a dialog; `MultiDatePicker` renders **inline, no
  portal**, and clips inside an `overflow-hidden` parent (same shape as `LedgerPopover.jsx:22`).
  Separately, `CreateWorklistModal:432` and `RecallDueDateSettingsModal:107` set
  `document.body.style.overflow` by hand rather than leaving it to `OverlayBackdrop`.
- **The QA scripts parse seeds as text, never import them** (`qa-data-integrity.mjs:12-37,48`), so a
  rename breaks them silently and they exit `0` even with orphaned `patient_id` refs (`:66`);
  `qa-e2e-flow.mjs:13` inline-copies `appointmentQueries.js` and can pass while the real module is
  broken (`README.md:565-566`).
- **`useMockLoad.js` and `pages/PatientDetail.legacy.jsx` (31 KB) are dead** — grep-verified, no
  importer, absent from the README's dead list. **`DailyHuddleView` hardcodes `blue-*`** (10×)
  rather than brand tokens — not a hex, so no rule catches it.

## See also

- `references/inventory.md` — the 11 worklist configs, 13 huddle slugs, widget prop signatures and
  importer lists, QA script detail, and the full seed→importer map.
- `main-architecture` — hub, index, change log. Siblings: `fe-scheduling` (owns
  `DailyHuddleView.jsx`'s folder, `data/scheduling.js`, the appointment seed's consumer),
  `fe-patient-chart` (`patientSubresources.js`, `NewPatientDrawer` call sites, `PatientsContext`),
  `fe-ledger` / `fe-insurance-claims` (`DatePickerField` call sites), `fe-forms`
  (`demoPatientFormSchema.js`), `fe-platform` (`AppRoutes`, `ROUTES`, `OverlayBackdrop`).
- `PMS_React/README.md:193,196,374-375,562-566`. `PROJECT_GUIDE.md` is stale; ignore it.
