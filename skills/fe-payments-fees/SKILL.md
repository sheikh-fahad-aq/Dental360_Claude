---
name: fe-payments-fees
description: Frontend payments and fee schedules — /payments (placeholder), /fee-schedules (mock) and the live Settings panels Terminal Readers, Fee Schedule Defaults, Plan Fee Schedule. Use when changing PMS_React/src/pages/Payments.jsx or FeeSchedules.jsx, src/api/stripeTerminal.js, clinicFeeSchedule.js, planLocationFeeSchedule.js, settings/payments/ or settings/fee-schedule/, or planFeeCsv.js; or when asked if a payments or fee screen is real. Not the account ledger — fe-ledger.
---

## Scope

Two unfinished nav pages (`/payments`, `/fee-schedules`), the Stripe Terminal hardware client, and the three
Settings panels holding the only real fee and reader data. Maturity splits down the middle and the unfinished
half looks complete — that boundary is the point of this skill. Money on an *account* is **`fe-ledger`**, the
live surface, whose estimates read plan coverage and contracted providers from Settings > Insurance & Claims;
`fe-settings` owns the rail and registration, behaviour *inside* the three panels is owned here; Chart Billing's
Payments sub-tab and the check-out payment step are placeholders in `fe-ledger` and `fe-scheduling`.

## Files

| path (under `PMS_React/`) | role |
|---|---|
| `src/pages/Payments.jsx` | **(entry — placeholder)** 366. Setup screen → fake 1400 ms "Connecting…" → board. `SETUP_KEY :20`, read/write `:40,:48`, phase `:334`, timer `:345-355`. KPIs and every tab count are literal zeros (`:172-173`); Print/Export/Date-range all call `notConnected :176`. |
| `src/components/payments/SelectPatientDrawer.jsx` | 240 — **the only working part of `/payments`.** `usePatientsList :59`, `PAGE_SIZE = 50`, portal + `OVERLAY_Z_INDEX.drawerBackdropGlobal :86`. Picking a patient only toasts (`Payments.jsx:183`). |
| `src/api/stripeTerminal.js` | 101 — **live**, `authApi`. 11 exports over `/stripe-terminal/{locations,devices}` + `/locations/:id/stripe-devices`. Local `unwrap :10`. **No `normalizeX`** — shape-guessing at each call site. |
| `src/components/settings/payments/TerminalReadersPanel.jsx` | 595 / 23 KB — **live**, settings `terminal-readers`. Gate `:296`, `loadData :295`, register `:348-378`, sync `:405`, toggle `:420`. Grep, do not read whole. |
| `src/pages/FeeSchedules.jsx` | **(entry — mock, in-memory)** 250. `useState([]) :67`; nothing is fetched, nothing persists. `handleSync :90` toasts "EHR sync is not connected yet." |
| `src/components/fee-schedules/NewFeeScheduleModal.jsx` | 441 / 17 KB — **mock**. Local form only; `handleSubmit` mints `id: fs_${Date.now()}` for `onCreate`. `TYPE_OPTIONS :8` = ucr / insurance_ppo / medicaid / cash_membership / custom. |
| `src/api/clinicFeeSchedule.js` · `planLocationFeeSchedule.js` | 120 / 93 — **live**, `preAuthApi`. `/clinic-fee-schedule` (standard + cash prices) and `/plan-location-fee-schedule` (in-network allowable by plan + location). Each has its own `unwrapList :16` and `normalizeClinicFee` / `normalizePlanLocationFee` at `:27`. |
| `src/components/settings/fee-schedule/FeeScheduleDefaultsPanel.jsx` · `PlanFeeSchedulePanel.jsx` | 786 / 31 KB and 1025 / 39 KB — **live**. Grep, never read whole. Gate `:279` / `:422`; `loadFees :300` / `:518`; bulk `:465`; CSV import `:696`; per-code lookup `:655`. |
| `src/utils/planFeeCsv.js` (owned) · `formatCurrency.js` (**fe-platform**, linked) | 169 — template download `:83`, `parsePlanFeeCsv :99`, header aliases `:8,:18,:25`; 32 — `formatCurrency :1` and the ledger's `formatLedgerMoney :22`. |

Touches (shared, not owned): `api/client.js` + `config.js` (`isAuthApiEnabled :75`, `isInsuranceApiEnabled :71`),
`api/procedureCodes.js`, `api/insurance.js`; `hooks/usePatientsList.js`, `useSettingsNavStatus.js:4,79-84`;
`config/routes.js:18,25`, `navigation.js:36,48`, `settingsNavigation.js:73-81,93`; `Settings.jsx:14,15,24,78,80,90`;
`AppRoutes.jsx:31,37,238,288`; `context/{Auth,Location,Toast}Context`; `utils/locationUtils.js` `getLocationUserMeta`;
`ui/{OverlayBackdrop,SearchableSelect,ConfirmDialog,SimpleLoader}`; `charts/DatePickerField.jsx`.

## Contract

Renders `ROUTES.payments` and `ROUTES.feeSchedules` — lazy `AppRoutes.jsx:31,37`, mounted `:238,:288`, sidebar
`navigation.js:48,36`. Owns three settings sections: `terminal-readers` and `fee-schedule-defaults` in
**Payments & Billing** (`settingsNavigation.js:79,80`), `plan-fee-schedule` in **Insurance & Claims** (`:93`) —
each dispatched by a ternary arm in `Settings.jsx:78,80,90`. Three further ids (`payments-setup`,
`bank-connection`, `payment-settings`) are commented out at `settingsNavigation.js:76-78` and are **not
routable**. API: `stripeTerminal.js` on `authApi`, the two fee modules on `preAuthApi` — both direct base URLs,
so the `/__appointment_api` and `/__chart_api` proxies are not involved. Tables: `references/wire-and-surfaces.md` §2-4.

## Invariants

1. **Never demo `/payments` or `/fee-schedules` as working** — README `:198`/`:197` label them
   `placeholder` and `mock (in-memory)`, `:377`/`:376` say why. Both look finished.
2. **Stripe never runs in the browser.** No `stripe`/`@stripe/*` dependency, no Stripe.js, and
   `VITE_STRIPE_PUBLISHABLE_KEY` (`.env.example:31`, README `:83-84`) is read by **zero** source files —
   grep-verified. Do not add one to "finish" payments; the card path is server-side, behind 360auth.
3. **`pms.payments.setupConnected` is cosmetic and has two readers.** `sessionStorage`, value `'1'`, written
   only by the fake connect. Keep it out of `localStorage`; no key name here may carry a patient id (§7.3).
4. **The fee-schedule panels refuse rather than silently mocking** — both `loadFees` set an error naming
   `VITE_APP_BASE_URL_PRE_AUTH` (`FeeScheduleDefaultsPanel.jsx:300-305`, `PlanFeeSchedulePanel.jsx:518-523`).
   The §5 silent-mock rule is suspended here on purpose, as in `fe-ledger`; `TerminalReadersPanel.jsx:296`
   returns silently instead. Convert neither to a mock, and never show a fee as real when the gate is off.
5. **`fetch` never appears here.** A new call is one export in the matching `src/api/` module, using that
   module's own `unwrap`, plus a `normalizeX` mapper.
6. **Money is `formatCurrency()` plus the `tabular-nums` class** — never a bare number, never a hardcoded
   hex, never `alert`. Feedback is `const { toast } = useToast()`, errors go through `getErrorMessage(err,
   fallback)`, dates are ISO `YYYY-MM-DD` (`NewFeeScheduleModal` `todayISO :36`; no date library exists here),
   and overlays are `createPortal` + `AnimatePresence` + `OverlayBackdrop` with a named `OVERLAY_Z_INDEX`
   key (`SelectPatientDrawer.jsx:86`), never a dynamic `z-[n]`.
7. **Route strings come from `ROUTES`**, and a new settings section is **three** edits: `settingsNavigation.js`,
   an import and a ternary arm in `Settings.jsx`. Miss the arm and it falls to `SettingsSectionPlaceholder`.
8. **Clinic and location scope comes from context, never a literal** — `getLocationUserMeta(user)` →
   `selectedLocation.clinic_id` (`FeeScheduleDefaultsPanel.jsx:272-277`, `TerminalReadersPanel.jsx:256`).
   Clinic fees need `clinic_id`; plan fees key on `location_id` + `plan_id`.
9. **Never log PHI (§7.1).** All ten owned files are `console.*`-clean, grep-verified — keep it that way.

## Working here

1. `wc -l`, then `grep -nE "^export |^function |^const [A-Z_]+ ="` + `sed -n`. `PlanFeeSchedulePanel`
   (39 KB), `FeeScheduleDefaultsPanel` (31 KB) and `TerminalReadersPanel` (23 KB) are never read whole.
2. **Making `/payments` real** → replace the hardcoded zeros (`Payments.jsx:172-173`) and each
   `notConnected` with a hook returning `{ items, loading, error, source, isApiEnabled, refetch }` guarded
   by a monotonic request-id ref; retire `SETUP_KEY` and fix `useSettingsNavStatus.js` in the same change.
3. **Making `/fee-schedules` real** → first decide whether it becomes a view over `clinicFeeSchedule.js` +
   `planLocationFeeSchedule.js` or a new backend resource. Do not add a third fee model.
4. **New terminal endpoint** → one export in `stripeTerminal.js` using the local `unwrap`, wired into
   `TerminalReadersPanel.jsx`; add a real `normalizeX` rather than copying the shape-guessing.
5. **New settings panel** → invariant 7's three edits, then load `/settings/<id>` and confirm it is not the
   placeholder. Finish with `npm run lint`; no test suite exists, so "verified" means you loaded the page
   and watched the request.

## Traps

- **`/fee-schedules` and Settings > Fee Schedule Defaults are unrelated code paths.** The nav page is
  `useState([])` (`FeeSchedules.jsx:67,92`); the real per-procedure fees live only in the two Settings panels.
  A schedule created on `/fee-schedules` survives neither the panel nor a reload.
- **Clicking "Get started" on `/payments` flips three Settings badges to "Connected"** —
  `useSettingsNavStatus.js:79-84` reads the same `pms.payments.setupConnected` flag and marks `payments-setup`,
  `payment-settings` and `bank-connection` connected. All three are commented out of `settingsNavigation.js`
  and not routable, so the badge asserts a connection that never existed.
- **`handleBulkSyncMissing` writes `standard_fee: 0`** for any procedure whose code carries no fee, and only for
  the first 50 of the at-most-200 loaded codes (`FeeScheduleDefaultsPanel.jsx:471-478`, `loadProcedures`
  `limit: 200` at `:343`). Zero-fee rows are real money rows on a live backend.
- **CSV import is one `POST` per row, sequential, plus a `listProcedureCodes` per unknown code**
  (`PlanFeeSchedulePanel.jsx:723-743`, `resolveProcedureId :655`). Partial success is the normal outcome — it
  toasts "Imported N; M skipped" and does **not** roll back.
- **Two byte-identical `formatCurrency` exports exist** — `utils/formatCurrency.js:1` and `appointmentDisplay.js:149`;
  both fee panels import the latter. `formatLedgerMoney` (`formatCurrency.js:22`) is a third, **non**-interchangeable contract.
- **Neither fee-schedule panel guards its async load** — no request-id ref, no `cancelled` flag
  (`FeeScheduleDefaultsPanel.jsx:300`, `PlanFeeSchedulePanel.jsx:518`) — so switching location or plan quickly
  can land a stale list; neither returns a `source`, and this slice has no `src/hooks/` hook of its own.
  **`SelectPatientDrawer` takes `isApiEnabled` but not `source`** (`:59`, though `usePatientsList.js:89` exposes
  it), so with `VITE_APP_BASE_URL_AUTH` unset it lists mock patients with nothing marking them (§5).
- **`registerTerminalReader` silently creates a Stripe Terminal location first** when none matches the selected
  practice location (`TerminalReadersPanel.jsx:352-359`), so registering against the wrong header location
  leaves a stray Stripe location behind. "Order reader" is a toast only (`:321`).
- **Ten API exports have no caller** (grep-verified): `getClinicFee`, `patchClinicFee`, `lookupClinicFee`,
  `getPlanLocationFee`, `patchPlanLocationFee`, `getTerminalLocation`, `toggleTerminalLocation`,
  `listStripeDevices`, `getStripeDevice`, `updateStripeDevice` — `lookupClinicFee` is the per-procedure price
  lookup an estimate flow would need, and it has no UI.

## See also

`references/wire-and-surfaces.md` (maturity table, every export with line and caller, panel internals, CSV
format, settings wiring, both readers of the setup flag) · `main-architecture` (hub, change log) · `fe-ledger`
(**the live money surface**; plan coverage + contracted providers drive its estimates) · `fe-settings` (rail,
registration, `SettingsSectionPlaceholder`) · `fe-insurance-claims` (`listInsurancePlans`, the plan ids Plan Fee
Schedule keys on) · `fe-scheduling` (check-out payment step, placeholder) · `PMS_React/README.md` → Environment
`:83-84`, Routes `:197-198`, Settings `:350-361`, Other pages `:376-377`.
