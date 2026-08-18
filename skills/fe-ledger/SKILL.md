---
name: fe-ledger
description: Frontend patient financial ledger — /ledger, /ledger/:patientId, /ledger/:patientId/portion and the chart's Billing > Ledger tab, all rendering one LedgerWorkspace. Use when changing PMS_React/src/components/ledger/**, src/pages/ledger/**, src/api/ledger.js or src/components/settings/ledger/**; touching a posting dialog, the aging summary strip, View menu, running balance, unapplied credits, patient portion, plan coverage or contracted providers; or when an estimate reads 0.00 / needs_review.
---

## Scope

Account resolution, the running-balance table, the aging + portion summary strip, the eight posting
dialogs, the Portion drill-down, and the two Settings panels feeding the estimate engine. **Maturity:
live** end to end against `PreAuth_Flask`'s `/api/ledger/*` (`PMS_React/README.md:307-347`); this SPA
is now its primary frontend. It owns money on an *account* — claims belong to `fe-insurance-claims`,
the chart shell to `fe-patient-chart`. `/ledger` has no design of its own: Patients, repointed.

## Files

| path (under `PMS_React/`) | role |
|---|---|
| `src/components/ledger/LedgerWorkspace.jsx` | **(entry)** 508 lines. The ONE ledger. Resolve `:107`, row load `:146`, reference data `:159`, `refresh` `:213`, `applyView` `:218`, 8 dialogs `:419-505`. |
| `src/api/ledger.js` | 268 lines. Every `/api/ledger/*` call + the code-kind colour map `:241`. No `normalizeX` — deliberate. |
| `src/pages/ledger/Ledger.jsx` | 599. `/ledger` list — Patients' table, hook and toolbar, minus Last Visit. |
| `src/pages/ledger/LedgerPatient.jsx` · `LedgerPortion.jsx` | 62 / 513. Page chrome only (workspace at `:53`); the Portion drill-down — Summary + Detailed tabs, sticky first/last columns, its own header builder `:44`. |
| `src/components/ledger/LedgerTable.jsx` · `LedgerBalanceSummary.jsx` | 401. Running balance, folding revision chains + xfer snapshots into render units (`:23`); the one-line equation strip (credits + 4 aging buckets = balance − insurance − write-off = patient portion). |
| `src/components/ledger/LedgerActionBar.jsx` · `LedgerViewMenu.jsx` · `LedgerPopover.jsx` · `LedgerLegendPopover.jsx` · `UnappliedCreditsPopover.jsx` · `AccountNoteDialog.jsx` | Posting actions; the View menu (every control is a server query param); anchored portal popovers; one account note shared by every member. |
| `src/components/ledger/ledgerUi.jsx` · `fields.jsx` · `ledgerDates.js` · `useLedgerClinicId.js` | **The house classes** (panels, head/body cells, `GRID_*`, `MONEY_CELL_CLASS`, 3 buttons, `LedgerAlert`, `LedgerCard`, `SectionLabel`, `TableMessageRow`, `LedgerStatusBadge`); 666-line form primitives (`MoneyInput`, `TabStrip:276`, `ComboBox:314`, `TagInput:464`); the whole date layer (no date library exists here); `user.clinic_id → selectedLocation.clinic_id → VITE_CLINIC_ID → null`. |
| `src/components/ledger/dialogs/` · `src/components/settings/ledger/` | 8 posting dialogs + `LedgerDialogShell.jsx`, `ApplyToChargesGrid.jsx`, `TransactionTabs.jsx`, `dialogHelpers.js` — `PatientWalkoutDialog.jsx` is **68KB / 1649 lines, grep, never read whole**; `PlanCoveragePanel.jsx` (528) and `ContractedProvidersPanel.jsx` (348), the estimate engine's inputs, live. |

Touches (shared, not owned): `src/api/client.js` + `config.js`; `src/utils/formatCurrency.js:22`
`formatLedgerMoney`; `src/config/routes.js:20-22`, `navigation.js:49`, `settingsNavigation.js:96-97`;
`src/pages/Settings.jsx:83,85`; `src/components/AppRoutes.jsx:32-34,246,256,264`;
`src/hooks/usePatientsList.js`; `src/pages/PatientCharts.styles.js` (`TableScroll`);
`src/theme/theme.css:67-83`; `src/index.css:75-82,137`; `patient-detail/billing/BillingSection.jsx:155`.

## Contract

Renders `ROUTES.ledger`, `ROUTES.ledgerPatient(id)`, `ROUTES.ledgerPortion(id)` and the chart's
Billing > Ledger tab; `/ledger/:patientId/portion` is registered **before** `/ledger/:patientId`
(`AppRoutes.jsx:256`) or the drill-down is unreachable. `LedgerWorkspace` props: `patientId`,
`variant` (`page` | `embedded`), `defaultViewMode`, `initialViewMode`, `onViewModeChange`,
`onAccountResolved` — the call sites differ only in chrome and default scope (page opens
**guarantor**, chart tab opens **patient**).

API: `src/api/ledger.js` only. `preAuthApi` for `/ledger/*` (money, claims, statements, coverage);
`authApi` for reference data. Both are direct base URLs — the `/__appointment_api` / `/__chart_api`
proxies are **not** involved. Routes, callers, dialogs: `references/routes-and-dialogs.md`.

## Invariants

1. **Exactly ONE ledger implementation** — `LedgerWorkspace.jsx`, rendered by `LedgerPatient.jsx:53`
   and `billing/BillingSection.jsx:155`. Check every change in **both**. Never fork a chart version.
2. **Money is an exact two-decimal string on the wire** (`"430.00"`). Display with
   `formatLedgerMoney`; never `parseFloat` a display value, never re-total a server figure. Where
   totalling is unavoidable (walkout) use `toCents`/`fromCents` (`dialogHelpers.js:14,24`).
3. **`src/api/ledger.js` has no `normalizeX` mapper, on purpose** — the repo-wide map-at-the-edge rule
   is suspended, because coercing those strings is the one change that breaks the ledger. The unwrap
   is `const body = (r) => r?.data` at `:31`. Do not add a normalizer.
4. **Every number is computed by the backend over the whole account** — the View menu is query
   params, so `applyView` re-fetches. Balance, aging and "since last 0" cannot be derived locally.
5. **Never send `clinic_id` on a money route** — PreAuth derives it from the account via 360auth.
   `useLedgerClinicId()` is for clinic-scoped *reference* lookups only and returns `null` rather than
   guessing; do not copy `getClinicId` from `src/api/patients.js`, which defaults to clinic 1.
6. **`client_request_id` is generated once per dialog opening** (`makeRequestId`
   `dialogHelpers.js:36`); regenerate it per save and a double-clicked Save is a second payment.
   **Delete reasons go in the body, never the query string** (`ledger.js:71`) — proxies log URLs.
7. **All chrome comes from `ledgerUi.jsx`** — import the constants, do not re-style. Neutrals
   `gray-*` (never `slate-*`), Tailwind's named sizes (never `text-[13px]`), `font-bold` only on a
   page `h1`. Page tables use `HEAD_/BODY_CELL_CLASS`, dialog grids `GRID_*` — the only density knob.
8. **Code-kind colour lives in three places that move together**: `--ledger-*`
   (`theme/theme.css:67-83`), `--color-ledger-*` in `@theme inline` (`index.css:75-82`), and
   `CODE_KIND_TEXT_CLASS` (`api/ledger.js:241`). Miss one and the class silently falls back.
9. **`fetchLedgerProviders` 404s on an empty provider list.** Callers catch and use `[]`
   (`LedgerWorkspace:180`) or the ledger will not open for a clinic with no providers. Do not
   generalise — `clinic_locations/get_all` returns `200 {"locations": []}`.
10. **After any successful post call `refresh()`** (re-resolve + re-fetch); never patch a posted row
    into local state. **The URL carries `?view=patient` and nothing else** — that is how the portion
    page returns to the view the operator left (`LedgerPatient.jsx:24,56`, `LedgerPortion.jsx:95,133`).

## Working here

1. `wc -l`, then `grep -nE "^export |^function |^const [A-Z_]+ ="` + `sed -n`;
   `PatientWalkoutDialog.jsx` and `fields.jsx` must not be read whole.
2. New API call → one export in `src/api/ledger.js`, in its section, ending `.then(body)`; never
   `fetch`, never add a mapper (invariant 3).
3. New dialog → build on `dialogs/LedgerDialogShell.jsx`, reuse `fields.jsx` + `ledgerUi.jsx`, seed a
   `client_request_id` on open, then register it in **both** `LedgerWorkspace`'s `dialog` switch and
   `LedgerActionBar.jsx`'s callbacks.
4. New column/row kind → `LedgerTable.jsx`, then `LedgerPortion.jsx:44`, which deliberately builds
   its own header cells. New View option → a control in `LedgerViewMenu.jsx` **and** the `params`
   object in `loadLedger` (`:133`); client-only options (`show_time`) stay out of `params`.
5. Verify in both surfaces — `/ledger/:patientId` and a chart's Billing > Ledger tab — then
   `npm run lint`. No test suite exists; "verified" means you watched the request.

## Traps

- **Unset `VITE_APP_BASE_URL_PRE_AUTH` and the ledger refuses rather than falling back to mock**
  (`LedgerWorkspace:273`, `Ledger.jsx:246` — a warning `LedgerAlert` naming the var). Unlike the rest
  of the app (§5) there is no mock ledger; `src/data/billingMock.js` kept only `MOCK_CLAIMS`.
- **The `/ledger` list gates on `isPatientsApiEnabled()`, not the ledger gate** (`Ledger.jsx:166`), so
  with auth configured and pre-auth not you get a full patient list whose rows open a refusal.
- **Estimates are `0.00` + `needs_review` until Settings > Insurance & Claims > Plan Coverage and
  Contracted Providers are filled in** — deliberate. In `ContractedProvidersPanel`, *absence of a row
  means not contracted*: assuming a contract writes off money the patient owes.
- **`LedgerPopover.jsx:22` uses a local `POPOVER_Z = 120`, not `OVERLAY_Z_INDEX`** (§6.6); only
  `LedgerDialogShell.jsx:17` uses the shared map. Do not raise one without checking the other.
- **The initial load is guarded by a `cancelled` closure flag** (`LedgerWorkspace:193-208`), not the
  repo's monotonic request-id ref — and `applyView` has no guard, so fast View changes can race.
  There is also **no `src/hooks/` hook here**, so no `{ items, loading, error, source }` envelope;
  state lives in the component, and only `/ledger` uses a hook (`usePatientsList`).
- **Twelve exports have no caller**, including the whole transaction lock/unlock pair — that backend
  surface has **no UI at all**. Full list in the reference; do not assume a screen exists.
- **Chart Billing's Pre-Auth and Payments sub-tabs are hardcoded empty states**, i.e. placeholder
  (`BillingLedgerPanel.jsx:4-8`). The README tree at `:424` still says `billing/ ledger/ (mock)`;
  that line is stale — the prose at `:299` is correct.
- **Editing never overwrites a row** — the backend snapshots, cancels and writes a new current
  version; `ViewTransactionDialog.jsx:271` renders that chain, and `show_history` /
  `include_transfers` are what make revisions and `code_kind: 'xfer'` rows visible at all.
  E-statements are not routed: `delivery` is `"print"` or `"print_and_mail"` only.

## See also

- `references/routes-and-dialogs.md` — every export with line number and caller, the dialog map,
  `ledgerUi`/`fields`/`dialogHelpers` inventories, View-menu params, settings panels, theme tokens.
- `main-architecture` — hub, index and change log. Siblings: `fe-insurance-claims` (the other half of
  Billing), `fe-patient-chart` (hosts the embedded workspace, and supplies the `usePatientsList` /
  `PatientCharts.jsx` design `/ledger` reuses), `fe-settings` (panel registration), `fe-payments-fees`
  (the other money surfaces — both placeholders), `fe-reports-worklists` (`charts/DatePickerField.jsx`, in every dialog here), `fe-platform`.
