---
name: fe-settings
description: Frontend Settings — /settings/:sectionId, its config-driven side rail, and its own panels: Scheduling Configuration (providers, services, operatories, schedule blocks), Procedure Codes, Multi-Codes, Tooth Chart Defaults. Use when adding a settings section, editing PMS_React/src/pages/Settings.jsx, settingsNavigation.js, useSettingsNavStatus.js or procedureCodes.js, or when a section routes but renders SettingsSectionPlaceholder. Not the Labs, Check-In Forms, Fee Schedule, Payer or Ledger panels.
---

## Scope

`/settings/:sectionId` — a two-pane shell (config-driven side rail + exactly one panel) and the panels it
renders. **23 sections are registered and routable; 14 render a real panel, 9 fall through to
`SettingsSectionPlaceholder`** — counted from the tree, not the README (Traps). A section can route and
still be a placeholder; that is the defining failure mode here (Invariant 1). **Boundary — six `settings/`
subfolders belong to their feature skill; here you own only the nav entry and the `Settings.jsx` branch that
mounts them:** `payers/`→fe-insurance-claims · `ledger/`→fe-ledger · `labs/`→fe-labs ·
`check-in-forms/`→fe-forms · `payments/`+`fee-schedule/`→fe-payments-fees. `/scheduling` is **fe-scheduling**; Scheduling **Configuration** is here.

## Files

Under `PMS_React/`; `…/` = `src/components/settings/`. Bare numbers are line counts.

| path | role |
|---|---|
| `src/pages/Settings.jsx` | **(entry)** 103. 15 **static** panel imports `:12-26`; the `activeSection === '<id>'` chain `:64-95`; placeholder fallback `:97`. Collapses the app sidebar on mount, restores on unmount `:34-37`. |
| `src/config/settingsNavigation.js` | 141. `DEFAULT_SETTINGS_SECTION_ID = 'scheduling'` `:29`; `SETTINGS_NAV` `:31` — 3 live groups (Payments & Billing, Insurance & Claims, Practice Operations) plus **5 commented-out groups** and 25 commented items; `SECTION_BY_ID` / `getSettingsSectionById` / `isValidSettingsSectionId` `:131-141`. |
| `…/SettingsHeader.jsx` · `SettingsSidebar.jsx` · `SettingsNavPanel.jsx` · `SettingsMobileMenu.jsx` · `SettingsSectionPlaceholder.jsx` · `settingsScrollClasses.js` | 52 / 9 / 330 / 100 / 18 / 3. Location + section crumb; a `md:`-only 9-line wrapper; the nav panel (search, collapsible groups, jump chips, IntersectionObserver spy, `NavLink` to `ROUTES.settingsSection(id)` `:116`); a portal drawer for mobile; the "available once API integration is complete" card. |
| `src/hooks/useSettingsNavStatus.js` | 92. `connected` / `needs_setup` per section id + `SETTINGS_NAV_STATUS_META`; overrides `scheduling` from `useRooms()`. **Called for effect only** (`SettingsNavPanel.jsx:118`) — nothing renders a badge. |
| `…/scheduling/SchedulingConfiguration.jsx` · `SchedulingTabs.jsx` · `schedulingConstants.js` | 129 / 60 / 72. Second-level tab page, **9 active tabs** (`calendar-settings` commented at `schedulingConstants.js:2` *and* `SchedulingConfiguration.jsx:44`). Tab lives in `?tab=` and `localStorage` `pd:settings:schedulingTab:v1`; `schedule-groups` normalises to `schedule-provider`; unknown tab → `SchedulingTabPlaceholder` `:30`. |
| `…/scheduling/providers/` · `services/` · `operatories/` · `scheduleGroups/` · `scheduleBlocks/` | **live.** `ProvidersPanel` 760 + `ProviderFormModal` 663 + `ProviderViewModal`; `ServicesPanel` 456 + `ServiceFormModal`; `OperatoriesPanel` **1089 — grep, never read whole** + `OperatoryFormModal` 518 + `OperatoryAvailabilityModal`; `ScheduleGroupsPanel` 521 + `ScheduleProviderWizardModal` 461; `ScheduleBlockFormModal` 595 (owned by `SchedulingRulesPanel`, not a tab). |
| `…/scheduling/SchedulingRulesPanel.jsx` · `ProviderConcurrencyPanel.jsx` · `ServiceFrequencyRules.jsx` · `AttendancePoliciesPanel.jsx` · `AsapWaitlistPanel.jsx` | 538 **partial** — schedule blocks live via `src/api/scheduleBlocks.js`, but the two toggles at `:336-366` are `useState(DEFAULT_PREFS)` `:95,117` and persist nowhere. 86 / 75 / 44 / 72 **mock or static** — the first two render `MOCK_*` arrays (`schedulingConstants.js:50,60`), the last two are hardcoded copy with a local toggle. |
| `…/scheduling/schedulingCalendar/` | `SchedulingCalendarSettingsPage.jsx` 477 + `SearchRangesDrawer.jsx` 226 + constants 109 — **mock**: one `useState` `:193`, zero API imports, persists nothing. `SchedulingCalendar.jsx` is a 2-line re-export barrel with **zero importers** (dead). |
| `…/procedure-codes/` · `multi-codes/` **owned**; `check-in-forms/` `labs/` `payments/` `fee-schedule/` **linked** | **live.** Owned: `ProcedureCodesPanel` 439 · `ProcedureCodeFormModal` 361 · `ManageCategoriesDrawer` 432 · `CategorySelect` 385; `MultiCodesPanel` 561 · `MultiCodeFormModal` 789 · `ProcedureRowPicker` 247. Linked (edit via the owning skill): `CheckInFormsPanel` 481 → fe-forms; `LabsPanel` 527 + `LabFormModal` 210, lab **vendors** not lab cases → fe-labs; `TerminalReadersPanel` 595, `FeeScheduleDefaultsPanel` 786, `PlanFeeSchedulePanel` 1025 → fe-payments-fees. |
| `…/tooth-chart-defaults/` · `…/operating-hours/` | **live**: `ToothChartDefaultsPanel` 601 + `ProcedureColorsCard` 426 over `src/api/chartSettings.js` (`chartApi`); `CHART_SETTINGS_API_SPEC.md` (994) is the backend contract — cite it, never duplicate. **Unreachable**: `OperatingHoursPanel` 537 — branch at `Settings.jsx:92`, nav item commented at `settingsNavigation.js:107`; local `useState`, no API. |
| `src/api/procedureCodes.js` | 219. `/v2/procedure-codes` on `authApi`. `isProcedureCodesApiEnabled` `:25`, `normalizeProcedureCode` `:76`, paged `listProcedureCodes` `:139`, get/create/update/delete `:188-219`. **No mock branch inside the module** (Invariant 5). |

Touches (shared, not owned): `routes.js:26-27,57`; `AppRoutes.jsx:5,38,295-311`; contexts `Sidebar`,
`Location`, `Auth`, `Rooms`, `Providers`, `ChartSettings`, `Toast`; `utils/locationUtils.js`
`getLocationUserMeta`; `ui/OverlayBackdrop.jsx`; the 15 `src/api/` modules listed in the reference §3.

## Contract

Renders at `ROUTES.settingsSection(sectionId)` → `/settings/:sectionId`. Bare `/settings` redirects to the
default section (`AppRoutes.jsx:295-305`) and an unknown `:sectionId` redirects too (`Settings.jsx:53`), so
a bad id never reaches a panel. Nested state is query-string, not path: Scheduling Configuration uses
`?tab=<id>` (`SchedulingConfiguration.jsx:62-92`). Every panel calls a `src/api/` domain module
(section→module→base-path table in the reference §3); all settings traffic rides `authApi`
(`VITE_APP_BASE_URL_AUTH`) except Tooth Chart Defaults (`chartApi`, `VITE_APP_BASE_URL_CHART`) and the
fee-schedule / payer panels (`preAuthApi`, `VITE_APP_BASE_URL_PRE_AUTH`). `/__appointment_api` is unused here.

## Invariants

1. **A section is two edits, and the second is the forgotten one.** An item in a group's `items` in
   `settingsNavigation.js` makes it *routable*; an `activeSection === '<id>'` branch in
   `Settings.jsx:64-95` makes it *render*. With only the first you get the placeholder — silently, no
   error, no warning; that is how all 9 current placeholders arose. Do both in the same commit.
2. **`settingsNavigation.js` is the single registry.** Never hand-write `/settings/foo` — use
   `ROUTES.settingsSection(id)`; never key a panel off `useParams()` — read validated `activeSection`.
3. **One panel per section, mounted directly.** No nested `<Routes>` under Settings; sub-navigation is
   a query param (`?tab=`) so a deep link survives reload and Back works.
4. **Clinic id is resolved, never assumed** — `getLocationUserMeta(user).clinicId ??
   selectedLocation?.clinic_id ?? VITE_CLINIC_ID ?? null` (22 sites, e.g. `ProcedureCodesPanel.jsx:71`).
   When `null`, set "No clinic selected. Choose a location or set `VITE_CLINIC_ID`." and fetch nothing.
   **Never** copy `getClinicId()` from `src/api/patients.js` — it defaults to clinic 1.
5. **Gating is env-var presence, checked in the panel** (§5). `isProcedureCodesApiEnabled()` is literally
   `isAuthApiEnabled()`, and `procedureCodes.js` has **no `if (!enabled)` mock branch** — a caller that
   skips the gate hits the network unconditionally. Keep the `normalizeX` mapper at the module edge.
   **`fetch()` never appears here**; each module has its own `unwrap`/`assertSuccess` because three
   envelope shapes exist (`procedureCodes.js:29,41`).
6. **Every modal and drawer uses `createPortal` + `AnimatePresence` + `OverlayBackdrop` with an
   `OVERLAY_Z_INDEX` key** — all 12 here comply, incl. `SettingsMobileMenu.jsx:57-62`; never a dynamic
   `z-[n]`. Feedback is `useToast()`, errors via `getErrorMessage(err, fallback)`; no `alert()` exists
   under `settings/` and none may be added.
7. **Never log a payload, id or URL from a settings call** (§7.1). **Authorization is server-side** (§7.7):
   hiding a section is not a permission boundary, and nothing here gates on role. ISO `YYYY-MM-DD` on the
   wire — hours, blocks and availability windows are hand-formatted; there is no date library in this repo.

## Working here

1. **New section** → (a) `{ id, label, icon }` in the right group in `settingsNavigation.js`; (b) a branch
   in `Settings.jsx:64-95` plus its import at `:12-26`. A `BASE_STATUS_BY_ID` entry is optional and inert.
2. **New Scheduling Configuration tab** → an entry in `SCHEDULING_TABS` (`schedulingConstants.js:1`)
   **and** a line in `SchedulingTabContent` (`SchedulingConfiguration.jsx:43-55`). Same two-edit trap:
   tab only ⇒ `SchedulingTabPlaceholder`.
3. **New API call** → one export in the matching `src/api/` module with its `normalizeX` mapper, then
   gate the panel on that module's `is*ApiEnabled()`.
4. Size before you open — `wc -l`, then `grep -nE "^export |^function |^const [A-Z_]+ ="` + `sed -n`;
   `OperatoriesPanel.jsx` (1089), `PlanFeeSchedulePanel.jsx` (1025), `MultiCodeFormModal.jsx` (789). Verify
   by loading `/settings/<id>` and watching the request, then `npm run lint` — no test suite. Panels are
   **statically** imported, so a broken import anywhere blanks the whole Settings route.

## Traps

- **Tooth Chart Defaults → Default Dentition is a DEFAULT, not the answer.** All four options
  (`age-based` · `adult` · `primary` · `mixed`) now render — `SUPPORTED_DENTITIONS` in
  `toothChartDefaultsConstants.js` holds all of them since the A-T artwork landed. A clinician can
  override it for one patient from the chart's own ⋯ menu, and that choice is stored against the
  patient (`/v2/charts/patient-dentition`) and outranks this screen. `age-based` resolves from the
  patient's date of birth, and holds at adult when none is recorded.
- `UNSUPPORTED_DENTITION_NOTE` and the odontogram's red banner still exist and nothing shipped
  triggers them: they are the gate the next numbering scheme (FDI, supernumeraries) passes before
  it can be offered here, because a setting that is silently ignored is indistinguishable from one
  that works.


- **`PMS_React/README.md:353-354` is stale on the counts.** It says "32 registered sections; 12 render a
  real panel"; the tree says **23 registered, 14 wired, 9 placeholder** — `multi-codes` and
  `tooth-chart-defaults` were wired after that paragraph. It also says four groups are commented out when
  there are **five** (Integrations omitted) and calls Scheduling a "10-tab page" when 9 are active.
  Re-count before quoting a number; the maturity *labels* still hold.
- **The 9 placeholders** — `insurances-accepted`, `configure-rcm`, `era-enrollments`, `appointment-notes`,
  `clinical-note-signing`, `configure-agents`, `ai-kill-switch`, `online-booking`, `printable-forms`.
- **`operating-hours` is an orphan** — the 537-line panel is branched (`Settings.jsx:92`) but its nav item
  is commented (`settingsNavigation.js:107`), so the id fails validation and the URL redirects to
  `/settings/scheduling`. Uncommenting one line ships a panel that stores nothing.
- **`scheduling-calendar` (section) and `calendar-settings` (tab) are the same mock page** — the tab is
  commented out in both places, the section renders `SchedulingCalendarSettingsPage` directly
  (`Settings.jsx:66-69`). Controls, a drawer, a Save affordance, and it **persists nothing**: the
  highest-risk demo surface here. `SchedulingCalendar.jsx` beside it is a dead barrel (zero importers).
- **`useSettingsNavStatus()`'s return value is discarded** (`SettingsNavPanel.jsx:118`, no assignment) and
  `SETTINGS_NAV_STATUS_META` has no importer — the Connected / Needs setup badges are recomputed every
  render and never painted. Not a status source.
- **Pre-existing style violations, do not copy them:** 12 hardcoded `#e7ebef` card borders in the
  scheduling panels and `#3f3f46` nav text (`SettingsNavPanel.jsx:24-41,78`) break §6.4.
- **No panel here uses a `src/hooks/` data hook** — no `{ items, loading, error, source }` envelope and **no
  `source` flag anywhere in `settings/`**; state is local `useState`, and loads are guarded (where at all)
  by a `cancelled` closure rather than a monotonic request-id ref, so location switching can race.
- **`SchedulingRulesPanel`'s two preference toggles look saved and are not** (`:336-366`) — only the
  schedule-block list below is live. **`Labs` is the vendor catalog** (`/v2/labs`), not the lab-case board.

## See also

- `references/sections-and-panels.md` — the 23-section table (id · label · group · panel · maturity), the 9 scheduling tabs, the section→API-module→base-path map, the commented-out inventory.
- `main-architecture` — hub, index, change log. Siblings owning a subfolder here: `fe-insurance-claims`
  (`payers/`), `fe-ledger` (`ledger/`), `fe-labs` (`labs/`), `fe-forms` (`check-in-forms/`),
  `fe-payments-fees` (`payments/`, `fee-schedule/`). Also `fe-scheduling` (consumes providers / services /
  operatories / schedule blocks), `fe-charting` (Tooth Chart Defaults via `ChartSettingsContext`),
  `fe-platform` (`ROUTES`, `AppRoutes`, `OverlayBackdrop`), `be-lab-cases`, `be-recare-waitlist`.
- In-repo: `PMS_React/README.md` → "Settings" and "Adding a settings section" (`:491-495`);
  `…/tooth-chart-defaults/CHART_SETTINGS_API_SPEC.md`. `PROJECT_GUIDE.md` is stale — ignore it.
