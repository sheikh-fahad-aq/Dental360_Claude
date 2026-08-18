# fe-ledger reference — every route, dialog and shared export

All paths relative to `PMS_React/`. Line numbers verified against the working tree.

## 1. `src/api/ledger.js` (268 lines) — every export

No `normalizeX` mapper exists in this module **on purpose** (header comment, lines 1-17):
money is an exact two-decimal string and coercing it is the one change that breaks the
ledger. The unwrap is `const body = (response) => response?.data` at `:31`.

Gate: `isLedgerApiEnabled()` `:23` → `isInsuranceApiEnabled()` → `VITE_APP_BASE_URL_PRE_AUTH`
non-empty. Reference lookups additionally need `VITE_APP_BASE_URL` (360auth), re-exported as
`isLedgerReferenceApiEnabled`.

### PreAuth_Flask — `preAuthApi`, prefix `/api` (client adds it), all paths below are `/ledger/*`

| export | line | METHOD path | callers |
|---|---|---|---|
| `resolveLedgerAccount` | 35 | GET `/accounts/resolve?patient_id=` | LedgerWorkspace:107, LedgerPortion:112 |
| `fetchLedgerAccount` | 38 | GET `/accounts/:id` | **no caller** |
| `fetchAccountNote` / `saveAccountNote` | 41/44 | GET / PUT `/accounts/:id/note` | AccountNoteDialog |
| `fetchLedgerTransactions` | 49 | GET `/accounts/:id/transactions` | LedgerWorkspace:146 — returns `{ rows, summary, view }` |
| `fetchLedgerSummary` | 52 | GET `/accounts/:id/summary` | **no caller** (summary rides on transactions) |
| `fetchOpenCharges` | 55 | GET `/accounts/:id/open-charges` | payment / both adjustment dialogs / walkout |
| `fetchTransaction` | 58 | GET `/transactions/:id` | ViewTransactionDialog |
| `applyUnappliedCredits` | 61 | POST `/accounts/:id/apply-credits` | LedgerWorkspace:227 |
| `procedureApi` | 78 | POST/PUT/DELETE `/procedure[/:id]` | EnterProcedureDialog, ViewTransactionDialog |
| `chargeAdjustmentApi` | 79 | POST/PUT/DELETE `/charge-adjustment[/:id]` | EnterChargeAdjustmentDialog, ViewTransactionDialog |
| `creditAdjustmentApi` | 80 | POST/PUT/DELETE `/credit-adjustment[/:id]` | EnterCreditAdjustmentDialog, ViewTransactionDialog |
| `paymentApi` | 81 | POST/PUT/DELETE `/payment[/:id]` | EnterPaymentDialog, ViewTransactionDialog |
| `voidProcedure` | 83 | POST `/procedure/:id/void` | ViewTransactionDialog:130 |
| `fetchClaimableProcedures` | 88 | GET `/accounts/:id/claimable-procedures` | CreateClaimDialog:44 |
| `fetchPatientCoverages` | 91 | GET `/accounts/:id/patient-insurance` | CreateClaimDialog:45 |
| `fetchAccountClaims` | 94 | GET `/accounts/:id/claims` | EnterInsurancePaymentDialog:107 |
| `fetchClaimGrid` | 97 | GET `/claims/:id/grid` | EnterInsurancePaymentDialog:129 |
| `createLedgerClaim` | 100 | POST `/claims` | CreateClaimDialog:99 |
| `postInsurancePayment` | 103 | POST `/insurance-payment` | EnterInsurancePaymentDialog:194 |
| `deleteInsurancePayment` | 106 | DELETE `/insurance-payment/:id` | **no caller** |
| `recalculateEstimates` | 111 | POST `/accounts/:id/recalculate-estimates` | **no caller** |
| `fetchChargeEstimates` / `overrideChargeEstimate` | 114/117 | GET / PUT `/charges/:id/estimates` | **no caller** |
| `fetchWalkoutSummary` | 124 | GET `/accounts/:id/walkout?patient_id=` | PatientWalkoutDialog:1488 |
| `createWalkoutClaims` | 129 | POST `/accounts/:id/walkout/claims` | PatientWalkoutDialog:256 |
| `sendWalkoutClaims` | 132 | POST `/accounts/:id/walkout/send-claims` | PatientWalkoutDialog:614 |
| `generateWalkoutStatement` | 138 | POST `/accounts/:id/statements` | PatientWalkoutDialog:1135 |
| `fetchAccountStatements` | 142 | GET `/accounts/:id/statements` | **no caller** (reprint list, unbuilt) |
| `fetchPatientPortion` | 149 | GET `/accounts/:id/portion?view=&patient_id=` | LedgerPortion:118 |
| `unlockTransaction` / `relockTransaction` | 156/159 | POST `/transactions/:id/unlock` / `/relock` | **no caller** |
| `fetchDenialCodes` | 164 | GET `/denial-codes` | EnterInsurancePaymentDialog:118 |
| `createDenialCode` | 167 | POST `/denial-codes` | **no caller** |
| `fetchContractedProviders` / `createContractedProvider` / `deleteContractedProvider` | 170/173/176 | GET / POST / DELETE `/contracted-providers[/:id]` | ContractedProvidersPanel |
| `fetchLedgerPlans` | 186 | GET `/plans` | both settings panels |
| `fetchPlanCoverage` / `savePlanCoverage` | 189/192 | GET / PUT `/plans/:id/coverage` | PlanCoveragePanel |
| `fetchTransactionTypes` | 197 | GET `/transaction-types` | LedgerWorkspace:162 |
| `fetchLedgerTags` | 200 | GET `/tags` | LedgerWorkspace:168 |
| `fetchXferReasons` | 203 | GET `/xfer-reasons` | LedgerWorkspace:174 |

`poster(path)` `:71` builds the four `{ create, update, remove }` triples. `remove(id, reason)`
puts the reason in the **body** (`{ data: { reason } }`), never the query string — staff free
text can name a patient and proxies log query strings.

### 360auth — `authApi`, read-only reference data

| export | line | path | callers |
|---|---|---|---|
| `searchLedgerPatients` | 208 | GET `/v2/patients/search` | **no caller** (`/ledger` uses `usePatientsList`) |
| `fetchLedgerPatient` | 211 | GET `/v2/patients/:id` | **no caller** |
| `fetchLedgerProviders` | 217 | GET `/clinic_providers/get_all/:clinicId` | LedgerWorkspace:180 |
| `fetchLedgerClinicLocations` | 220 | GET `/clinic_locations/get_all/:clinicId` | both settings panels |
| `searchLedgerProcedureCodes` | 223 | GET `/v2/procedure-codes` | EnterProcedureDialog:120, PlanCoveragePanel:111 |
| `providerLabel` | 227 | — | 27 call sites; tries `provider_name` → `display_name` → first+last → `Provider {id}` |

`fetchLedgerProviders` **404s on an empty provider list** — every caller must catch and use `[]`,
or the ledger will not open for a new clinic. Do not generalise: `clinic_locations/get_all`
answers `200 {"locations": []}`.

### Constants

`CODE_KIND_TEXT_CLASS` `:241` maps `procedure | patient_payment | insurance_payment |
charge_adjustment | credit_adjustment | insurance_claim | xfer` → `text-ledger-*`.
`DEFAULT_CODE_KIND_CLASS` `:254`, `codeKindClass()` `:256`, `LEDGER_LEGEND` `:259` (8 rows,
adds `A` = posted automatically and `*` = applied across visits, both `text-ledger-auto`).

## 2. The eight dialogs — `src/components/ledger/dialogs/`

Opened from `LedgerWorkspace`'s single `dialog` string state (`:419`-`:505`). Every one is
`<LedgerDialogShell>`-wrapped and calls `onSaved={refresh}`, which re-resolves the account and
re-fetches the rows — nothing is patched into local state.

| dialog key | file | lines | notes |
|---|---|---|---|
| `payment` | `EnterPaymentDialog.jsx` | 278 | FIFO apply grid, `client_request_id:158` |
| `insurance-payment` | `EnterInsurancePaymentDialog.jsx` | 507 | claim picker → `fetchClaimGrid`, denial codes, `needs_review` badge `:383` |
| `procedure` | `EnterProcedureDialog.jsx` | 429 | procedure-code ComboBox against 360auth |
| `create-claim` | `CreateClaimDialog.jsx` | 232 | claimable procedures × patient coverages |
| `charge` | `EnterChargeAdjustmentDialog.jsx` | 209 | types filtered `category === 'charge_adjustment'` |
| `credit` | `EnterCreditAdjustmentDialog.jsx` | 221 | plus xfer reasons |
| `walkout` | `PatientWalkoutDialog.jsx` | **1649 (68KB — grep, never read whole)** | 4 tabs, `TABS:69` = Create Claims / Send Claims / Payment / Statement |
| `transaction` | `ViewTransactionDialog.jsx` | 318 | view / edit / delete / void + revision history `:271` |
| `note` | `../AccountNoteDialog.jsx` | 65 | one note per account, shared by every member |

Shared inside `dialogs/`: `LedgerDialogShell.jsx` (portal + `OverlayBackdrop` +
`OVERLAY_Z_INDEX.modalBackdrop` at `:17`), `ApplyToChargesGrid.jsx`, `TransactionTabs.jsx`,
`dialogHelpers.js`.

`dialogHelpers.js` exports: `isMoneyInput:6` (the `/^\d*\.?\d{0,2}$/` mask), `toCents:14`,
`fromCents:24`, `makeRequestId:36`, `seedApplications:44` (FIFO pre-fill), `toApplicationPayload:61`,
`sumApplications:70`, `splitByKnown:81`, `memberOptions:93`.

`makeRequestId` is generated **once per dialog opening**, held in `useState('')`, and sent as
`client_request_id`. Only the five `_idempotent` routes honour it: `/ledger/procedure`, the two
adjustments, `/ledger/payment`, `/ledger/insurance-payment`. Editing a dialog to re-generate it
per save turns a double-click back into a second payment.

Walkout constants worth knowing: `MESSAGE_ELECTRONIC_LIMIT = 450`, `DUE_DATE_MIN_DAYS = 1`,
`DUE_DATE_MAX_DAYS = 180`, `MAX_DIAGNOSES_PER_CLAIM = 4` (fallback only — the server sends
`max_diagnoses` per group and that number wins). Statement `delivery` is `"print"` or
`"print_and_mail"`; e-statement renders disabled and the backend 400s it anyway.

## 3. Shared UI — `src/components/ledger/ledgerUi.jsx` (7.2KB)

Every class string is lifted from `src/pages/PatientCharts.jsx` and the settings panels. Do not
invent a second palette, radius or type scale.

Constants: `PANEL_CLASS`, `HEAD_CELL_CLASS`, `BODY_CELL_CLASS`, `GRID_HEAD_CELL_CLASS`,
`GRID_CELL_CLASS`, `MONEY_CELL_CLASS` (`text-right tabular-nums`), `TABLE_ROW_CLASS`, `LINK_CLASS`,
`BUTTON_SECONDARY_CLASS`, `BUTTON_PRIMARY_CLASS`, `BUTTON_ICON_CLASS`.
Components: `LedgerAlert` (`info | warning | error`), `SectionLabel`, `LedgerCard`,
`TableMessageRow`, `LedgerStatusBadge`.

Page tables use `HEAD_CELL_CLASS`/`BODY_CELL_CLASS`; dialog grids use the `GRID_*` pair. That is
the only density knob — tighter padding, same palette and type.

`src/components/ledger/fields.jsx` (666 lines) is the form-primitive set:
`Field:44`, `TextInput:65`, `MoneyInput:83`, `TextArea:104`, `SelectField:128`, `CheckboxField:166`,
`TriStateCheckbox:193`, `RadioField:213`, `SwitchField:238`, `TabStrip:276`, `ComboBox:314`,
`TagInput:464`.

`src/components/ledger/ledgerDates.js`: `parseDateOnly:23`, `toISODate:32`, `todayISO:38`,
`formatLedgerDate:56`, `formatLedgerDateTime:63`, `formatModifiedDate:76`, `addDaysISO:81`,
`diffDaysISO:92`. This is the whole date layer — there is no date library in the repo.

## 4. View menu parameters — `LedgerViewMenu.jsx`

Every control is a server query parameter; `onApply` calls `LedgerWorkspace.applyView`, which
re-fetches. Nothing is filtered in the browser.

- `sort_by`: `transaction_date` `:48` | `statement` `:55` (default `statement`)
- `view_mode`: `patient` `:69` | `guarantor` `:77`
- `range`: `all` `:125` | `since_zero` `:134` | `custom` `:142` (+ `from` / `to`, ISO `YYYY-MM-DD`)
- checkboxes: `show_history`, `include_deleted`, `include_transfers`, `show_time`

`show_time` is client-only (it is passed to `LedgerTable`, not to the API).
`include_transfers` is what makes `code_kind: 'xfer'` rows appear at all.
`lastZeroBalanceDate` shown in the menu comes from the response, `ledger.view.last_zero_balance_date`.

## 5. Settings panels — `src/components/settings/ledger/`

Both are **live**, both wired in `src/pages/Settings.jsx:83` / `:85` on section ids
`plan-coverage` / `contracted-providers`, listed in `src/config/settingsNavigation.js:96-97`.

**`PlanCoveragePanel.jsx` (528 lines)** — the estimate engine's inputs: allowed-fee schedule,
coverage table, deductibles/maximums, COB method. `DEDUCTIBLE_TYPES` = `preventive, basic, major,
ortho, none` — anything else means "no deductible for this category", never a silent default.
`COB_METHODS` = `'' (not recorded — no secondary estimate) | standard | non-duplication | carve-out`.
`BENEFIT_FIELDS` is the six-row deductible/maximum grid.

**`ContractedProvidersPanel.jsx` (348 lines)** — who may have an automatic contracted write-off
posted. **Absence of a row means not contracted**, deliberately: assuming a contract writes off
money the patient actually owes. A blank provider covers every provider at that location, which is
how practice-level contracts are usually signed.

Both use `useLedgerClinicId()` for `clinic_id` and refuse to guess when it is null.

## 6. Theme tokens

`src/theme/theme.css:67-83` defines `--ledger-procedure`, `--ledger-patient-payment`,
`--ledger-insurance-payment`, `--ledger-charge-adjustment`, `--ledger-credit-adjustment`,
`--ledger-insurance-claim`, `--ledger-xfer`, `--ledger-auto`, `--ledger-hatch-base`,
`--ledger-hatch-stripe`.

`src/index.css:75-82` bridges the first eight into Tailwind utilities via `@theme inline`
(`--color-ledger-*` → `text-ledger-*`). `src/index.css:137` defines `.ledger-estimate-fill`, the
hatched estimate row on the portion page, from the two hatch vars. There is no `tailwind.config.js`;
adding a code kind means adding the var, the `@theme inline` line, and the
`CODE_KIND_TEXT_CLASS` key — all three, or the class silently falls back.
