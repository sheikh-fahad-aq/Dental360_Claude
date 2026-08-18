# fe-settings reference — sections, tabs and wiring

All counts verified against the working tree. Paths are relative to `PMS_React/`;
`…/` = `src/components/settings/`. Maturity labels follow `PMS_React/README.md`
conventions: **live** / **partial** / **mock** / **static** / **placeholder**.

---

## 1. The 23 registered sections

Source of truth: `src/config/settingsNavigation.js` (only uncommented `items` are routable) crossed
with the `activeSection === '<id>'` chain in `src/pages/Settings.jsx:64-95`.

**14 wired · 9 placeholder.**

### Group `payments-billing` — "Payments & Billing"

| id | label | panel | maturity |
|---|---|---|---|
| `terminal-readers` | Terminal Readers | `…/payments/TerminalReadersPanel.jsx` (595) | live — `src/api/stripeTerminal.js` |
| `fee-schedule-defaults` | Fee Schedule Defaults | `…/fee-schedule/FeeScheduleDefaultsPanel.jsx` (786) | live — `clinicFeeSchedule` + `procedureCodes` |

### Group `insurance-claims` — "Insurance & Claims"

| id | label | panel | maturity |
|---|---|---|---|
| `insurances-accepted` | Insurances Accepted | — | **placeholder** |
| `configure-rcm` | Configure RCM | — | **placeholder** |
| `era-enrollments` | ERA Enrollments | — | **placeholder** |
| `payer-setup` | Payers | `…/payers/PayerSetupPanel.jsx` | live, read-only (Stedi payers) — **fe-insurance-claims** |
| `payer-portals` | Payer Portals | `…/payers/PayerPortalsPanel.jsx` | live — **fe-insurance-claims** |
| `plan-fee-schedule` | Plan Fee Schedule | `…/fee-schedule/PlanFeeSchedulePanel.jsx` (1025) | live — `planLocationFeeSchedule` + `insurance` + `procedureCodes` |
| `plan-coverage` | Plan Coverage | `…/ledger/PlanCoveragePanel.jsx` (528) | live — **fe-ledger** (estimate engine input) |
| `contracted-providers` | Contracted Providers | `…/ledger/ContractedProvidersPanel.jsx` (348) | live — **fe-ledger** (estimate engine input) |

### Group `practice-operations` — "Practice Operations"

| id | label | panel | maturity |
|---|---|---|---|
| `labs` | Labs | `…/labs/LabsPanel.jsx` (527) + `LabFormModal.jsx` (210) | live — `src/api/labs.js` (`/v2/labs`), lab **vendors** |
| `procedure-codes` | Procedure Codes | `…/procedure-codes/ProcedureCodesPanel.jsx` (439) | live — `procedureCodes` + `lookups` |
| `multi-codes` | Multi-Codes | `…/multi-codes/MultiCodesPanel.jsx` (561) | live — `multiCodes` + `lookups` + `procedureCodes` |
| `scheduling` | Scheduling Configuration | `…/scheduling/SchedulingConfiguration.jsx` (129) | **partial** — see §2 |
| `scheduling-calendar` | Scheduling Calendar | `…/scheduling/schedulingCalendar/SchedulingCalendarSettingsPage.jsx` (477) | **mock** — zero API imports |
| `check-in-forms` | Check-In Forms | `…/check-in-forms/CheckInFormsPanel.jsx` (481) | live — `src/api/forms.js` |
| `tooth-chart-defaults` | Tooth Chart Defaults | `…/tooth-chart-defaults/ToothChartDefaultsPanel.jsx` (601) | live — `src/api/chartSettings.js` (`chartApi`) |
| `appointment-notes` | Appointment Notes | — | **placeholder** |
| `clinical-note-signing` | Clinical Note Signing | — | **placeholder** |
| `configure-agents` | Configure AI Agents | — | **placeholder** |
| `ai-kill-switch` | AI Kill Switch | — | **placeholder** |
| `online-booking` | Online Booking | — | **placeholder** |
| `printable-forms` | Printable Forms | — | **placeholder** |

### Orphan

| id | state |
|---|---|
| `operating-hours` | `…/operating-hours/OperatingHoursPanel.jsx` (537) + `operatingHoursConstants.js` (50) exist and are branched at `Settings.jsx:92`, but the nav item is commented at `settingsNavigation.js:107`. `isValidSettingsSectionId` therefore rejects the id and `/settings/operating-hours` redirects to the default section. Local `useState` only, no API module. |

---

## 2. Scheduling Configuration tabs

`SCHEDULING_TABS` (`…/scheduling/schedulingConstants.js:1`) crossed with `SchedulingTabContent`
(`…/scheduling/SchedulingConfiguration.jsx:43-55`). **9 active tabs**; `calendar-settings` is
commented out in *both* places (`schedulingConstants.js:2`, `SchedulingConfiguration.jsx:44`).

| tab id | panel | maturity |
|---|---|---|
| `providers` | `providers/ProvidersPanel.jsx` (760) + `ProviderFormModal.jsx` (663) + `ProviderViewModal.jsx` (310) | **live** — `src/api/providers.js`, `lookups.js` |
| `services` | `services/ServicesPanel.jsx` (456) + `ServiceFormModal.jsx` (452) | **live** — `src/api/services.js`, `lookups.js` |
| `operatories` | `operatories/OperatoriesPanel.jsx` (1089) + `OperatoryFormModal.jsx` (518) + `OperatoryAvailabilityModal.jsx` (269) | **live** — `src/api/rooms.js`, `providers.js` |
| `schedule-provider` | `scheduleGroups/ScheduleGroupsPanel.jsx` (521) + `ScheduleProviderWizardModal.jsx` (461) | **live** — `src/api/scheduleGroups.js` |
| `scheduling-rules` | `SchedulingRulesPanel.jsx` (538) + `scheduleBlocks/ScheduleBlockFormModal.jsx` (595) | **partial** — schedule blocks live via `src/api/scheduleBlocks.js`; the two `SettingCard` toggles (`:336`, `:352`) are local `useState(DEFAULT_PREFS)` (`:95`, `:117`) and persist nowhere |
| `provider-concurrency` | `ProviderConcurrencyPanel.jsx` (86) | **mock** — renders `MOCK_PROVIDER_CONCURRENCY_RULES` (`schedulingConstants.js:60`) |
| `service-frequency` | `ServiceFrequencyRules.jsx` (75) | **mock** — renders `MOCK_SERVICE_FREQUENCY_RULES` (`schedulingConstants.js:50`) |
| `attendance-policies` | `AttendancePoliciesPanel.jsx` (44) | **static** — hardcoded copy, no state |
| `asap-waitlist` | `AsapWaitlistPanel.jsx` (72) | **static** — one local toggle; the real queue is `be-recare-waitlist` |
| ~~`calendar-settings`~~ | (commented) | reachable only as the top-level `scheduling-calendar` section |

Tab state: `?tab=<id>` is authoritative; the last choice is cached in `localStorage`
`pd:settings:schedulingTab:v1` (`SCHEDULING_TAB_STORAGE_KEY`, `schedulingConstants.js:17`).
`DEFAULT_SCHEDULING_TAB = 'providers'`. The legacy id `schedule-groups` is accepted by
`isValidSchedulingTab` (`:19`) and rewritten to `schedule-provider` by `normalizeSchedulingTabId` (`:25`). An unknown-but-valid tab renders `SchedulingTabPlaceholder`
(`SchedulingConfiguration.jsx:30`).

---

## 3. Section → API module → base path

Every module lives in `src/api/` and defines its own `unwrap`/`assertSuccess`. Gate column is the
`is*ApiEnabled()` the module re-exports or calls — all of them reduce to "is this base URL non-empty".

| module | base path(s) | client | gate | used by |
|---|---|---|---|---|
| `procedureCodes.js` (219) | `/v2/procedure-codes` | `authApi` | `isAuthApiEnabled` | procedure-codes, fee-schedule ×2, multi-codes picker, charting catalog, scheduling drawers |
| `multiCodes.js` (387) | `/v2/multi-codes` | `authApi` | `isAuthApiEnabled` | multi-codes |
| `lookups.js` (310) | `/roles`, `/clinic_roles`, `/states`, `/service_categories` | `authApi` | `isAuthApiEnabled` | procedure-codes categories, provider/service form modals |
| `labs.js` (99) | `/v2/labs` | `authApi` | `isAuthApiEnabled` | labs (vendors) |
| `forms.js` (320) | `/form-templates`, `/patient-forms`, `/patients`, `/locations` | `authApi` | `isAuthApiEnabled` | check-in-forms |
| `providers.js` (367) | `/clinic_providers`, `/clinic_providers/filter` | `authApi` | `isAuthApiEnabled` | scheduling ▸ providers, operatories |
| `services.js` (231) | `/services` | `authApi` | `isAuthApiEnabled` | scheduling ▸ services |
| `rooms.js` (576) | `/get_room_id`, room CRUD | `authApi` | `isAuthApiEnabled` | scheduling ▸ operatories; also feeds `useSettingsNavStatus` via `RoomsContext` |
| `scheduleGroups.js` (523) | `/schedule_groups`, `/schedule_provider`, `/provider_schedules`, `/create_schedule_group` | `authApi` | `isAuthApiEnabled` | scheduling ▸ schedule-provider |
| `scheduleBlocks.js` (392) | `/schedule_blocks` | `authApi` | `isAuthApiEnabled` | scheduling ▸ scheduling-rules |
| `stripeTerminal.js` (101) | `/stripe-terminal/locations`, `/devices`, `/readers/register` | `authApi` | `isAuthApiEnabled` | terminal-readers |
| `chartSettings.js` (305) | `/v2/chart-settings` | **`chartApi`** | `isChartApiEnabled` (re-exported as `isChartSettingsApiEnabled` `:46`) | tooth-chart-defaults |
| `clinicFeeSchedule.js` (120) | `/clinic-fee-schedule` | **`preAuthApi`** | `isInsuranceApiEnabled` | fee-schedule-defaults |
| `planLocationFeeSchedule.js` (93) | `/plan-location-fee-schedule` | **`preAuthApi`** | `isInsuranceApiEnabled` | plan-fee-schedule |
| `insurance.js` (84) | insurance plans / carriers | **`preAuthApi`** | `isInsuranceApiEnabled` | plan-fee-schedule (also **fe-insurance-claims**) |

Notes:

- `procedureCodes.js` has **no internal mock branch**. `isProcedureCodesApiEnabled()` (`:25`) is
  exported for callers to check; `listProcedureCodes` (`:139`) throws `clinic_id is required` and
  otherwise always hits the network. The mock lives in the caller —
  `useChartingProcedureCatalog.js:86` falls back to a bundled `PROCEDURE_CATALOG` and is the only
  place in the repo that publishes a `source: 'api' | 'mock'` for this data.
- The list envelope is `{ success, page, limit, total, procedure_codes: [...] }` with defensive
  fallbacks through `body.data.procedure_codes`, `body.data`, and a bare array (`:162-171`).
- `normalizeProcedureCode` (`:76`) spreads `...raw` before its normalised keys, so unknown backend
  fields survive; do not rely on the shape being closed.
- No `settings/` panel touches `appointmentApi`, so the `/__appointment_api` proxy is irrelevant here.
  `chartApi` does emit the same-origin `/__chart_api/api` prefix — declared in both `vite.config.js`
  and `vercel.json`, which must stay in sync.

---

## 4. Commented-out inventory

`settingsNavigation.js` carries 25 commented item lines in addition to the 23 live ones.

**Five whole groups are commented out** (`:32-71` and `:122-128`): `general` (Manage Team, Roles &
Permissions, Security, Practice Info, Changelog, Notifications, Workflow Checklist), `integrations`
(PMS Integration, Credentials, Signature Devices, SOTA Imaging), `communications` (VoIP & Fax Setup,
VoIP Phone Setup, Communication Hours, Message Templates, CNAM Registration, Escalation Conditions),
`equipment` (Equipment), `reports` (RCM Overview Report).

**Individually commented items inside live groups:** `payments-setup`, `bank-connection`,
`payment-settings` (`:76-78`), `payer-contacts` (`:92`), `operating-hours` (`:107`),
`kiosk-check-in` (`:114`), `online-bill-pay` (`:119`).

`PMS_React/README.md:366-367` says "four whole nav groups (General, Communications, Equipment,
Reports)" — it omits Integrations.

---

## 5. Shell details

- `SettingsSidebar.jsx` (9 lines) is only an `<aside className="hidden … md:flex">` wrapper;
  everything is in `SettingsNavPanel.jsx` (330), which is rendered twice — once by the sidebar and
  once inside `SettingsMobileMenu.jsx` (100), a `createPortal` + `AnimatePresence` +
  `OverlayBackdrop(zIndex=OVERLAY_Z_INDEX.modalBackdrop)` drawer (`:57-95`).
- `SettingsNavPanel` state: `query` (label substring filter), `collapsedById` (per group),
  `activeGroupId` (IntersectionObserver scroll-spy over `data-nav-group-id`), `chipEdge` (horizontal
  fade on the jump-chip rail). Scroll container class comes from `settingsScrollClasses.js`
  (`SETTINGS_SCROLL_CLASSES`), used at `:295`.
- `SettingsHeader.jsx` (52) shows `BRAND_NAME` + the selected location (`useLocationContext`,
  "Loading…" while `initialising || locationsLoading || sessionValidating`) + the section label from
  `getSettingsSectionById`.
- `SettingsSectionPlaceholder.jsx` (18) renders the section label and the fixed sentence
  "This section will be available once API integration is complete."
- `Settings.jsx` collapses the global app sidebar on mount and restores the previous value on unmount
  (`useSidebar`, `:33-37`, `sidebarWasCollapsedRef`).

## 6. `useSettingsNavStatus` (dead output)

`src/hooks/useSettingsNavStatus.js` (92) exports `SETTINGS_NAV_STATUS_META` (`:8`, badge label +
Tailwind classes for `connected` / `needs_setup`) and `useSettingsNavStatus()` (`:73`), which merges
`BASE_STATUS_BY_ID` (30 ids, `:24-58`) with two live signals: `localStorage['pms.payments.setupConnected'] === '1'`
flips the three payments ids, and a loaded, error-free `useRooms()` sets `scheduling` from
`rooms.length > 0`.

Grep-verified: the only call site is `SettingsNavPanel.jsx:118`, written as a bare
`useSettingsNavStatus()` with no assignment, and `SETTINGS_NAV_STATUS_META` has **no importer at all**.
No badge is rendered anywhere in the settings tree. The hook still subscribes the nav panel to
`RoomsContext`, so removing it changes re-render behaviour — it is not free to delete blindly.
Its ids also cover sections that are commented out (`pms-integration`, `credentials`,
`signature-devices`, `sota-imaging`, `payments-setup`, `bank-connection`, `payment-settings`,
`payer-contacts`, `operating-hours`), which is a second reason not to treat it as a section registry.
