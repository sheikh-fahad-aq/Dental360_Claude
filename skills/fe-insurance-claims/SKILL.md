---
name: fe-insurance-claims
description: Frontend insurance, eligibility, Stedi payers, payer portals and claims (preAuthApi). Use when changing the patient Insurance or Billing chart tab, the six-tab claim detail drawer, AddInsuranceDialog, EligibilityBreakdown, PayerPortalsPanel or PayerSetupPanel; touching PMS_React/src/api/{insurance,claims,payerPortals}.js, src/hooks/useClaim*.js, src/utils/payerUtils.js or claimMappers.js; or debugging carrier_id / stedi_payers, verify eligibility, claim send/void/replace.
---

## Scope

Insurance, eligibility, Stedi payers, payer-portal credentials and dental claims — the whole `preAuthApi`
surface: two patient-chart tabs (`/patients/:id/insurance`, `/patients/:id/billing`) and two settings panels
(`/settings/payer-setup`, `/settings/payer-portals`). **Insurance and claims are live**, not mock. Boundary:
the Billing tab's *Ledger* sub-tab renders `LedgerWorkspace` and belongs to `fe-ledger` — this skill owns only
the strip hosting it. Plan fee schedules (`settings/fee-schedule/`) read `listInsurancePlans`, not owned here.

## Files

Paths under `PMS_React/`; `pd/` = `src/components/patient-detail/`.

| Path | Role |
|---|---|
| `pd/insurance/InsuranceSection.jsx` | **(entry)** Insurance tab — plan cards, toolbar, Verify |
| `pd/insurance/AddInsuranceDialog.jsx` | add/edit coverage; the two-call create sequence |
| `pd/insurance/BenefitSummary.jsx`, `UpdateBenefitSummaryDialog.jsx` | plan-benefit card + its `PUT` form |
| `pd/insurance/EligibilityBreakdown.jsx` | renders the latest eligibility record |
| `pd/insurance/PayerSelect.jsx`, `CarrierSelect.jsx` | bespoke combos (not `SearchableSelect`) |
| `pd/insurance/insuranceFormConstants.js`, `planBenefitConstants.js` | form shape, validation, `buildPlanName`, `unwrapPlanBenefit` |
| `pd/billing/BillingSection.jsx` | **(entry)** Billing tab — owns all of its state |
| `pd/billing/BillingLedgerPanel.jsx` | 4-tab strip; slots `ledgerContent` + `claimsPanel` |
| `pd/billing/BillingClaimsPanel.jsx`, `BillingClaimsSummaryCards.jsx` | claims table + four stat cards |
| `pd/billing/BillingStatementNote.jsx` | local-only note (see Traps) |
| `pd/billing/claims/ClaimDetailDrawer.jsx` | **(entry)** the six-tab claim drawer |
| `pd/billing/claims/Claim{General,Info,Procedures,Diagnoses,Attachments,StatusNotes}Tab.jsx` | one file per tab |
| `pd/billing/claims/CreateClaimsDialog.jsx`, `ClaimFormFields.jsx`, `claimFormConstants.js` | bulk-create; shared inputs; `CLAIM_DETAIL_TABS` |
| `src/components/settings/payers/PayerPortalsPanel.jsx` | **(entry)** portals + logins. **48 KB / 1152 lines — `grep`/`sed -n`, never read whole** |
| `src/components/settings/payers/PayerSetupPanel.jsx` | **(entry)** Stedi payer browser, read-only |
| `src/api/insurance.js`, `claims.js`, `payerPortals.js` | the only `preAuthApi` callers |
| `src/hooks/usePatientInsuranceData.js`, `usePatientClaims.js` | Insurance-tab plans; claim lists/stats/send |
| `src/hooks/useClaimDetail.js`, `useClaimLookups.js` | one claim + 13 mutators; module-cached lookups |
| `src/utils/insuranceMappers.js`, `claimMappers.js`, `claimDetailMappers.js`, `eligibilityMappers.js`, `payerUtils.js` | edge mapping |

**Touches** (not owned): `src/pages/{PatientDetail,Settings}.jsx`, `src/config/{routes,patientSections,settingsNavigation}.js`,
`src/components/ledger/LedgerWorkspace.jsx`, `src/components/scheduling/AppointmentVisitWizard.jsx`,
`src/hooks/usePatientSidebarSummary.js`, `src/components/settings/fee-schedule/PlanFeeSchedulePanel.jsx`.

## Contract

Every route goes through `preAuthApi` → `VITE_APP_BASE_URL_PRE_AUTH` (`api.eligibility.dental360grp.com/api`),
sent **direct**: this host allows browser CORS, so unlike `appointmentApi`/`chartApi` there is no `/__*_api`
proxy and nothing to keep in sync between `vite.config.js` and `vercel.json`. Groups: `/insurance/plan*`
(+ `…/plan-benefit`, `…/verify`) · `/patient-insurance*` · `/insurance/eligibility` · `/payers/stedi` ·
`/insurance_company*` + `/insurance_login*` · `/claims/*` + `/claim-status`. **Full tables with
wired-vs-unwired status: `references/api-surface.md`.** Rendered at `ROUTES.patientInsurance(id)` /
`ROUTES.patientSection(id, 'billing')` (`src/config/routes.js:31,29`), registered in
`src/config/patientSections.js:44,58`, mounted by `PatientInsurancePage`/`PatientBillingPage`
(`src/pages/PatientDetail.jsx:281,382`). Settings ids `payer-setup`/`payer-portals` —
`src/config/settingsNavigation.js:90-91`, branched at `src/pages/Settings.jsx:86-89`.

## Invariants

1. A plan's `carrier_id` is a **`stedi_payers.id`**, produced only by `resolvePlanCarrierId(payer)`
   (`src/utils/payerUtils.js:105`) — never a payer-portal / `insurance_company` id, never a carrier row.
2. Creating coverage is **two calls, in order**: `POST /insurance/plan`, then `POST /patient-insurance`
   carrying the returned `plan_id`. Never one.
3. The Carrier field renders only for the Vyne payer, only in create mode (`AddInsuranceDialog.jsx:102`).
4. Only `src/api/{insurance,claims,payerPortals}.js` may touch `preAuthApi`; no `fetch` outside `src/api/client.js`.
5. Patient ids on this wire must be numeric — `parsePatientIdForApi(...)`; `null` means bail with a message.
6. Gating is env-var presence, not a flag: `isClaimsApiEnabled()` and `isPayerPortalsApiEnabled()` are aliases
   of `isInsuranceApiEnabled()` (`src/api/config.js:71`). One unset var silently mocks this entire slice.
7. Hooks return `{ …, loading, error, source, isApiEnabled, refetch, …mutators }`, `source` ∈ `'api' | 'mock'`;
   mutators resolve `{ ok: true }` / `{ ok: false, error }` and never throw at the component.
8. ISO `YYYY-MM-DD` on the wire; no date library — use `todayIsoDate()` (`claimFormConstants.js:70`) + `DatePickerField`.
9. `useToast()` for feedback, `getErrorMessage(err, fallback)` for errors, `createPortal` + `AnimatePresence`
   + `OverlayBackdrop` + `OVERLAY_Z_INDEX` for overlays, CSS vars from `src/theme/theme.css` — no hex literals.
10. Claim status is matched by **name string, not id** (`claimMappers.js:3-21`); a new backend status name must join the right `Set` or it stops being counted anywhere.

## Working here

**New claims endpoint** — `src/api/claims.js` → a mapper in `claimDetailMappers.js`/`claimMappers.js` → a
mutator in `useClaimDetail.js` ending in `await load()` (11 of 13 do; replace/delete do not) → the tab. New
drawer tab? add it to `CLAIM_DETAIL_TABS` (`claimFormConstants.js:1`); the drawer maps that array at
`ClaimDetailDrawer.jsx:339`.

**New insurance field** — `insuranceFormConstants.js` (`EMPTY_INSURANCE_FORM`, `formFromInsuranceView`,
`validateInsuranceForm`) → the payload at `AddInsuranceDialog.jsx:256-273` → **and mirror it at
`src/components/scheduling/AppointmentVisitWizard.jsx:1296-1312`**, a second copy of the same two-call
sequence importing the same constants. Easiest thing here to forget.

**New payer-portal route** — `src/api/payerPortals.js` only; run the response through the local `unwrapArray`
(line 15) and a `normalizeX`; do not add a fourth unwrapper. **Verify with `cd PMS_React && npm run lint`** —
there is no test suite.

## Traps

- **SECURITY — `PMS_React/public/` ships three internal backend API documents:** `INSURANCE_ROUTES_API.md`
  (715 lines), `STEDI_PAYERS_AND_PORTALS_API.md` (503), `insurance_api_frontend.md` (437) — 1,655 total. Vite
  copies `public/` verbatim into `dist/`, so **any unauthenticated visitor can fetch them from the deployed
  site**. They belong in `docs/` or the backend repo. Never add another.
- **Portal credentials are plaintext**: `normalizePortalLogin` carries `password` from the response into
  component state and `PayerPortalsPanel` shows it behind a toggle. Never log, toast, or URL-encode it.
- **`use_sandbox: true` is hardcoded** (`InsuranceSection.jsx:312`) — every "Verify eligibility" hits the
  Stedi sandbox. Real eligibility needs a config path first.
- **Sent claims are looked up by surname, not id**: `usePatientClaims.js:71-86` calls `listSentClaims({ patient:
  nameQuery })` then post-filters, keeping rows whose `patientId` is null. Cross-patient bleed is possible.
- **Only `usePatientClaims` guards with a request-id ref** (`:34`). `usePatientInsuranceData`, `useClaimDetail`
  and `useClaimLookups` have none and can land a stale response; add the ref if you touch their load paths.
- **Billing sub-tabs `Pre-Auth` and `Payments` are hardcoded empty states** (`BillingLedgerPanel.jsx:11-20`) —
  `placeholder`. `Ledger` is live but is `fe-ledger`'s `LedgerWorkspace` (`BillingSection.jsx:155`).
- **The statement note never persists** (`BillingSection.jsx:18`, `:134` — `onSave` is `setStatementNote`,
  local state, no API). `placeholder`.
- **Insurance silently fabricates a plan** from `patient.insurance` via `mapMockPatientInsuranceToView`
  (`insuranceMappers.js:95`), flagged `isMock: true` and short-circuited by `EligibilityBreakdown`. Mock plans
  look real — check `source`.
- **`parsePatientIdForApi` is defined twice, identically** (`insuranceMappers.js:128`, `patientMappers.js:234`);
  files here import from both. Do not fix one alone.
- **Several api exports are unwired** (no caller outside `src/api/`): `/claims/unresolved`, `/claims/outstanding`,
  the four sub-resource `GET`s, follow-up, `DELETE /patient-insurance`, `DELETE /insurance/plan`.
- `useClaimLookups` caches into a **module-level** variable — it never invalidates within a session.
- `mapEligibilityToBreakdown` is a generic key-flattener with no schema; renamed backend fields relocate
  silently instead of erroring.

## See also

- `main-architecture` — hub: index, conventions, change log
- `fe-ledger` — `LedgerWorkspace` + the Billing > Ledger sub-tab; its Create Claim dialog does **not** use `src/api/claims.js`
- Other siblings: `fe-patient-chart` (the `/patients/:patientId/*` shell both tabs mount in) · `fe-settings` (the rail routing `payer-setup` / `payer-portals`) · `fe-payments-fees` (`settings/fee-schedule/` reads `listInsurancePlans`) · `fe-scheduling` (the second copy of the two-call coverage sequence, `AppointmentVisitWizard.jsx`) · `fe-platform` (`client.js`, `ROUTES`)
- `references/api-surface.md` — full route tables, wired/unwired status, mapper inventory
