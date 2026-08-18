# fe-payments-fees — wire, exports and surface inventory

Overflow for `SKILL.md`. Paths under `PMS_React/`. Every line number verified against the
working tree; anything not verified is marked **unverified**.

---

## 1. Maturity table (believe this, not the screen)

| Surface | Where | Maturity | Evidence |
|---|---|---|---|
| `/payments` board | `src/pages/Payments.jsx` | **placeholder** | README `:198`, `:377`; zeros at `:172-173` |
| `/payments` patient picker | `src/components/payments/SelectPatientDrawer.jsx` | **live** (read-only) | real `usePatientsList` at `:59`; selecting only toasts (`Payments.jsx:183`) |
| `/fee-schedules` list | `src/pages/FeeSchedules.jsx` | **mock (in-memory)** | README `:197`, `:376`; `useState([])` at `:67` |
| New Fee Schedule modal | `src/components/fee-schedules/NewFeeScheduleModal.jsx` | **mock** | no API import; `id: fs_${Date.now()}` in `handleSubmit` |
| Settings > Terminal Readers | `src/components/settings/payments/TerminalReadersPanel.jsx` | **live** | README `:358`; real `authApi` calls |
| Settings > Fee Schedule Defaults | `src/components/settings/fee-schedule/FeeScheduleDefaultsPanel.jsx` | **live** | README `:357`; real `preAuthApi` calls |
| Settings > Plan Fee Schedule | `src/components/settings/fee-schedule/PlanFeeSchedulePanel.jsx` | **live** | README `:358`; real `preAuthApi` calls |
| Chart Billing > Payments sub-tab | `patient-detail/billing/` | **placeholder** (not owned here) | README `:305`; see `fe-ledger` |
| Check-out wizard payment step | `components/scheduling/` | **placeholder** (not owned here) | README `:222-223`; see `fe-scheduling` |

---

## 2. `src/api/stripeTerminal.js` — 101 lines, `authApi`

Gate: `isStripeTerminalApiEnabled` is a re-export of `isAuthApiEnabled` (`:4`), i.e. "is
`VITE_APP_BASE_URL_AUTH` non-empty". Local `unwrap` at `:10` — throws when
`success === false`, otherwise returns `data.data ?? data`. **No `normalizeX` mapper**, so
every function ends in a `?? data.devices ?? data.items ?? data.results ?? []`-style guess.

| Export | Line | Call | Caller |
|---|---|---|---|
| `createTerminalLocation` | 27 | `POST /stripe-terminal/locations` | `TerminalReadersPanel:353` |
| `listTerminalLocations` | 33 | `GET /stripe-terminal/locations` | `TerminalReadersPanel:302` (`loadData`) |
| `getTerminalLocation` | 40 | `GET /stripe-terminal/locations/:id` | **none** |
| `toggleTerminalLocation` | 46 | `PATCH /stripe-terminal/locations/:id/toggle` | **none** |
| `registerTerminalReader` | 56 | `POST /stripe-terminal/readers/register` | `TerminalReadersPanel:362` |
| `listStripeDevices` | 62 | `GET /stripe-terminal/devices` | **none** |
| `getStripeDevice` | 69 | `GET /stripe-terminal/devices/:id` | **none** |
| `syncStripeDeviceStatus` | 75 | `GET /stripe-terminal/devices/:id/status` | `TerminalReadersPanel:405` |
| `updateStripeDevice` | 80 | `PUT /stripe-terminal/devices/:id` | **none** |
| `toggleStripeDevice` | 86 | `PATCH /stripe-terminal/devices/:id/toggle` | `TerminalReadersPanel:420` |
| `listLocationStripeDevices` | 91 | `GET /locations/:id/stripe-devices` | `TerminalReadersPanel:303` |

`registerTerminalReader`'s doc block (`:51-55`) records the fields 360auth reads:
`clinic_id`, `location_id`, `stripe_terminal_location_id`, `registration_code`, `label`,
`device_type`, `user_id`.

**There is no Stripe.js.** `package.json` has no `stripe` / `@stripe/*` dependency
(grep-verified). `.env.example:31` carries a commented `VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...`
and **no file under `src/` reads it** (grep-verified). Card capture, payment intents and
reader `process_payment_intent` calls all live behind 360auth — this repo only registers and
lists hardware.

---

## 3. `src/api/clinicFeeSchedule.js` — 120 lines, `preAuthApi`, base `/clinic-fee-schedule`

Standard / cash prices per procedure, per clinic (optionally per location).
Gate `isClinicFeeScheduleApiEnabled :12` → `isInsuranceApiEnabled()` → `VITE_APP_BASE_URL_PRE_AUTH`.

`unwrapList :16` accepts six envelope shapes: bare array, `clinic_fee_schedules`, `fees`,
`items`, `data`, `results` — anything else yields `[]`, never an error. `normalizeClinicFee :27` emits camelCase:
`{ id, clinicId, locationId, procedureCodeId, procedureCode, procedureName, standardFee,
effectiveDate, terminationDate, isActive, isClinicWide, raw }`.
`isClinicWide` is derived — `locationId == null || locationId === ''`.

| Export | Line | Call | Caller |
|---|---|---|---|
| `listClinicFees` | 75 | `GET /clinic-fee-schedule` → `{ items, total, raw }` | `FeeScheduleDefaultsPanel:317` |
| `getClinicFee` | 88 | `GET /clinic-fee-schedule/:id` | **none** |
| `createClinicFee` | 95 | `POST /clinic-fee-schedule` | `FeeScheduleDefaultsPanel` |
| `bulkUpsertClinicFees` | 99 | `POST /clinic-fee-schedule/bulk` body `{ fees }` | `FeeScheduleDefaultsPanel:489` |
| `updateClinicFee` | 103 | `PUT /clinic-fee-schedule/:id` | `FeeScheduleDefaultsPanel` |
| `patchClinicFee` | 107 | `PATCH /clinic-fee-schedule/:id` | **none** |
| `deleteClinicFee` | 111 | `DELETE /clinic-fee-schedule/:id` | `FeeScheduleDefaultsPanel:504` |
| `lookupClinicFee` | 115 | `GET /clinic-fee-schedule/lookup` | **none** |

`lookupClinicFee` is the single-procedure price lookup an estimate or charge flow would want.
It has no UI. Do not assume a screen exists for it.

`listClinicFees` params sent by the panel (`FeeScheduleDefaultsPanel:318-321`):
`clinic_id`, `location_id?`, `is_active?`, `include_clinic_wide?`.

---

## 4. `src/api/planLocationFeeSchedule.js` — 93 lines, `preAuthApi`

Base `/plan-location-fee-schedule` — in-network allowables by plan + location + procedure.
Gate `isPlanLocationFeeScheduleApiEnabled :12` → the same `isInsuranceApiEnabled()`.

`unwrapList :16` (note the different key order from §3: `fees` before
`plan_location_fee_schedules`). `normalizePlanLocationFee :27` emits
`{ id, …, procedureCode, procedureName, planName, maxAllowableAmount, raw }`.

| Export | Line | Call | Caller |
|---|---|---|---|
| `listPlanLocationFees` | 58 | `GET` → `{ items, total, raw }` | `PlanFeeSchedulePanel:535` |
| `getPlanLocationFee` | 71 | `GET /:id` | **none** |
| `createPlanLocationFee` | 79 | `POST` (create **or** upsert by plan/location/procedure) | `PlanFeeSchedulePanel:639`, `:733` |
| `updatePlanLocationFee` | 83 | `PUT /:id` | `PlanFeeSchedulePanel` |
| `patchPlanLocationFee` | 87 | `PATCH /:id` | **none** |
| `deletePlanLocationFee` | 91 | `DELETE /:id` | `PlanFeeSchedulePanel:775` |

Panel list params: `location_id`, `plan_id?` (`PlanFeeSchedulePanel:536-537`). Plans come from
`src/api/insurance.js` `listInsurancePlans` (`PlanFeeSchedulePanel:446`) — see `fe-insurance-claims`.

---

## 5. `src/utils/planFeeCsv.js` — 169 lines

- `PLAN_FEE_CSV_TEMPLATE :78` — header `procedure_code,max_allowable_amount`, two sample rows.
- `downloadPlanFeeCsvTemplate :83` — Blob + `URL.createObjectURL` + a synthetic `<a download>`,
  revoked immediately. Filename `plan-fee-schedule-template.csv`. Called from
  `PlanFeeSchedulePanel:327`.
- `parsePlanFeeCsv :99` → `{ rows, errors }`. Strips a BOM, ignores blank lines, requires a
  header row plus at least one data row.
- Header aliases are three `Set`s: `CODE_HEADERS :8`, `ID_HEADERS :18`, `AMOUNT_HEADERS :25`,
  matched after `normalizeHeader :35` (lowercase, non-alphanumerics → `_`).
- `splitCsvLine :43` is a hand-rolled quote-aware splitter — no CSV library in this repo.
- `parseAmount :70` strips `$`, `,` and whitespace; rejects non-finite values and negatives
  (`:74`) by returning `null`, which the caller turns into a row error. `0` is accepted.
- Row shape: `{ procedureCode?, procedureCodeId?, maxAllowableAmount, line }`.

Errors are **collected, not thrown**: a file can yield some rows and some errors. The panel
aborts on any header-level error but proceeds past row-level ones.

---

## 6. `FeeScheduleDefaultsPanel.jsx` — 786 lines / 31 KB (grep, do not read whole)

| Concern | Line |
|---|---|
| gate `apiEnabled = isClinicFeeScheduleApiEnabled()` | 279 |
| clinic id resolution (`getLocationUserMeta(user)` → `selectedLocation.clinic_id`) | 272-277 |
| `loadFees` (refuses with a `VITE_APP_BASE_URL_PRE_AUTH` message when the gate is off) | 300 |
| `loadProcedures` — `listProcedureCodes({ page: 1, limit: 200 })` | 332, 343 |
| create / update submit | 437-455 |
| `handleBulkSyncMissing` — `.slice(0, 50)`, `standard_fee` defaults to `0` | 465, 473, 478 |
| delete | 504 |
| footer count with `tabular-nums` | 746 |

The row form is an inline modal component defined above the panel (its state starts at `:68`) —
`createPortal` + `AnimatePresence` + `OverlayBackdrop`, `DatePickerField` for the two dates.

## 7. `PlanFeeSchedulePanel.jsx` — 1025 lines / 39 KB (grep, do not read whole)

| Concern | Line |
|---|---|
| gate `isPlanLocationFeeScheduleApiEnabled() && isInsuranceApiEnabled()` | 422 |
| `loadPlans` (insurance plans) | 446 |
| `loadProcedures` | 485 |
| `loadFees` (refuses when the gate is off, or when no location is selected) | 518 |
| single save | 639 |
| `resolveProcedureId` — cache first, else a `listProcedureCodes({ q: code, limit: 20 })` per code | 655 |
| `handleCsvImport` | 696 |
| the sequential import loop | 723-743 |
| delete | 775 |
| CSV template button | 327 |

## 8. `TerminalReadersPanel.jsx` — 595 lines / 23 KB

| Concern | Line |
|---|---|
| `getClinicId(selectedLocation, allLocations)` helper | ~45-57 |
| `getStripeTerminalLocationId` (reads `stripe_terminal_location_id` / `stripe_location_id`) | ~66-70 |
| `normalizeLocationOptions` / `normalizeDevices` (local shape coercion, not `normalizeX`) | ~80, ~118 |
| location locked to `LocationContext`'s header selection | 266-274 |
| `matchedStripeTerminalLocationId` | 275 |
| `loadData` — silent return when the gate is off | 295, 296 |
| "Order reader" → toast only | 321 |
| register: creates the Terminal location if unmatched, then registers | 348-378 |
| sync status / toggle | 405, 420 |

---

## 9. Wiring checklist

| Thing | File · line |
|---|---|
| `ROUTES.payments = '/payments'` | `src/config/routes.js:18` |
| `ROUTES.feeSchedules = '/fee-schedules'` | `src/config/routes.js:25` |
| active-nav matchers | `routes.js:49,56,80-81,92-93` |
| sidebar entries | `src/config/navigation.js:36` (Fee Schedules), `:48` (Payments) |
| lazy imports | `src/components/AppRoutes.jsx:31,37` |
| route elements | `AppRoutes.jsx:238,288` |
| settings group `payments-billing` | `src/config/settingsNavigation.js:73-81` |
| `terminal-readers` · `fee-schedule-defaults` | `settingsNavigation.js:79,80` |
| `plan-fee-schedule` (in `insurance-claims`) | `settingsNavigation.js:93` |
| commented-out, **not routable**: `payments-setup`, `bank-connection`, `payment-settings` | `settingsNavigation.js:76-78` |
| panel dispatch ternary arms | `src/pages/Settings.jsx:78,80,90` |
| panel imports | `Settings.jsx:14,15,24` |
| nav status badges | `src/hooks/useSettingsNavStatus.js:4,30,33,34,42,79-84` |

## 10. `pms.payments.setupConnected` — both readers

1. `src/pages/Payments.jsx:20,40-53,334,345-355` — decides whether `/payments` paints the
   Setup screen, a 1400 ms fake "Connecting…", or the board. Written only by the fake connect.
2. `src/hooks/useSettingsNavStatus.js:4,79-84` — when the flag is `'1'`, the badges for
   `payments-setup`, `payment-settings` and `bank-connection` flip from "Needs setup" to
   **"Connected"**. All three of those sections are commented out of `settingsNavigation.js`
   and are not routable, so the badge is a claim about a connection that does not exist.

`sessionStorage`, not `localStorage`, and no patient or appointment id in the key name —
keep both properties (CLAUDE.md §7.3).

## 11. Money formatting — three functions, do not merge blindly

| Function | File · line | Used by |
|---|---|---|
| `formatCurrency` | `src/utils/formatCurrency.js:1` | billing/claims panels, `FamilySection` |
| `formatCurrency` (byte-identical duplicate) | `src/utils/appointmentDisplay.js:149` | **both** fee-schedule settings panels |
| `formatLedgerMoney` | `src/utils/formatCurrency.js:22` | the ledger only — different contract (string in, `--` for empty, no symbol option) |

Pair any of them with the `tabular-nums` class. `/payments` and `/fee-schedules` currently
print literal `"$0.00"` strings and import none of the three.
