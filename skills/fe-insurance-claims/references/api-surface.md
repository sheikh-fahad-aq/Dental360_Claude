# fe-insurance-claims — pre-auth API surface

Every route below is emitted by `preAuthApi` (base `VITE_APP_BASE_URL_PRE_AUTH`,
`api.eligibility.dental360grp.com/api`). **No proxy** — unlike the appointment and chart
clients, this host allows browser CORS, so the configured URL really is the request URL.
Nothing here appears in `vite.config.js` or `vercel.json`.

`wired` = some component/hook calls it. `unwired` = exported and reachable but no caller
outside `src/api/` (verified by grep). Unwired exports are not dead — they are the obvious
extension points — but do not assume a screen exists for them.

---

## `PMS_React/src/api/insurance.js` (84 lines)

| Function | Route | State |
|---|---|---|
| `listInsurancePlans` | `GET /insurance/plan` | wired — `settings/fee-schedule/PlanFeeSchedulePanel.jsx` |
| `getInsurancePlan` | `GET /insurance/plan/:planId` | wired — `usePatientInsuranceData`, `AppointmentVisitWizard` |
| `createInsurancePlan` | `POST /insurance/plan` | wired — `AddInsuranceDialog`, `AppointmentVisitWizard` |
| `updateInsurancePlan` | `PATCH /insurance/plan/:planId` | wired |
| `deleteInsurancePlan` | `DELETE /insurance/plan/:planId` | **unwired** |
| `verifyInsurancePlan` | `POST /insurance/plan/:planId/verify` | wired — the "Verify" toolbar button |
| `getPlanBenefit` | `GET /insurance/plan/:planId/plan-benefit` | wired — `BenefitSummary` |
| `updatePlanBenefit` | `PUT /insurance/plan/:planId/plan-benefit` | wired — `UpdateBenefitSummaryDialog` |
| `patchPlanBenefit` | `PATCH /insurance/plan/:planId/plan-benefit` | **unwired** |
| `listInsuranceEligibility` | `GET /insurance/eligibility` | wired — `EligibilityBreakdown` |
| `getInsuranceEligibility` | `GET /insurance/eligibility/:id` | **unwired** |
| `listPatientInsurance` | `GET /patient-insurance` | wired — `usePatientInsuranceData`, `usePatientSidebarSummary` |
| `getPatientInsurance` | `GET /patient-insurance/:id` | **unwired** |
| `createPatientInsurance` | `POST /patient-insurance` | wired |
| `updatePatientInsurance` | `PATCH /patient-insurance/:id` | wired |
| `deletePatientInsurance` | `DELETE /patient-insurance/:id` | **unwired** — the Insurance panel has no delete |
| `listPayers` | `GET /payers/stedi` | wired — `AddInsuranceDialog`, `AppointmentVisitWizard`, `PayerSetupPanel` (`PayerSelect` only renders the list it is handed) |
| `listInsuranceCarriers` | `GET /insurance_company_carriers?insurance_company_id=` | wired — `AddInsuranceDialog` (feeds `CarrierSelect`) |
| `isInsuranceApiEnabled` | — | re-export of `api/config.js:71` |

The module returns `response.data` raw. It defines **no local `unwrap()`** — unwrapping is
pushed into `src/utils/insuranceMappers.js`, `eligibilityMappers.js`, `payerUtils.js` and
`insurance/planBenefitConstants.js` (`unwrapPlanBenefit`).

### The verify payload

`InsuranceSection.jsx:310`:

```
verifyInsurancePlan(planId, {
  update_plan: true,
  use_sandbox: true,          // hardcoded — line 312
  patient_id, location_id,
  patient_insurance_id,
})
```

It fires and returns immediately; the panel bumps a local `eligibilityRefreshKey` so
`EligibilityBreakdown` re-runs `GET /insurance/eligibility`. There is no polling and no
completion signal — a fast click-through can show the *previous* eligibility record.

---

## `PMS_React/src/api/claims.js` (128 lines)

### Lookups (cached module-globally by `useClaimLookups`)

| Function | Route | State |
|---|---|---|
| `listPlaceOfServiceOptions` | `GET /claims/place-of-service-options` | wired |
| `listClaimTypeRanks` | `GET /claims/claim-type-ranks` | wired |
| `listAccidentTypes` | `GET /claims/accident-types` | wired |
| `listClaimStatuses` | `GET /claim-status` | wired (note: **not** under `/claims`) |

### Lists

| Function | Route | State |
|---|---|---|
| `listUnsentClaims` | `GET /claims/unsent` | wired — `usePatientClaims` |
| `listSentClaims` | `GET /claims/sent` | wired — `usePatientClaims` |
| `listUnresolvedClaims` | `GET /claims/unresolved` | **unwired** |
| `listOutstandingClaims` | `GET /claims/outstanding` | **unwired** |

Both are unwrapped by `mapClaimsListResponse` → `{ count, claims }` from a
`{ claims: [...], count }` envelope. **They are not queried the same way**
(`usePatientClaims.js:71-86`):

```
listUnsentClaims({ patient_id: numericId })   // real id filter
listSentClaims({ patient: nameQuery })        // a NAME string
```

`nameQuery` is `patientName.split(',')[0].trim()` — the surname half of `"Last, First"`.
The sent list is then filtered client-side to rows whose `patientId` matches, *keeping rows
where `patientId` is null*. So the Sent sub-tab is a name search with a permissive
post-filter: two patients sharing a surname can pull each other's claims into the request,
and a sent claim whose row omits `patient_id` shows on every patient with that surname.
Do not copy this pattern; if `/claims/sent` grows a `patient_id` param, switch to it.

### Claim lifecycle

| Function | Route | State |
|---|---|---|
| `getClaim` | `GET /claims/:id` | wired — `useClaimDetail` |
| `createClaim` | `POST /claims` | wired — `usePatientClaims.createNewClaim` |
| `bulkCreateClaims` | `POST /claims/bulk-create` | wired — `CreateClaimsDialog` |
| `updateClaim` | `PUT /claims/:id` | wired — General + Claim Info tabs save together |
| `deleteClaim` | `DELETE /claims/:id` | wired |
| `sendClaims` | `POST /claims/send` | wired — from the list *and* the drawer |
| `voidClaim` | `POST /claims/:id/void` | wired |
| `replaceClaim` | `POST /claims/:id/replace` | wired — returns the replacement id |
| `resubmitClaim` | `POST /claims/:id/resubmit` | wired |
| `refreshClaimStatus` | `POST /claims/:id/refresh-status` | wired — Status/Notes tab |

### Sub-resources

| Function | Route | State |
|---|---|---|
| `addClaimProcedures` / `removeClaimProcedures` | `POST` / `DELETE /claims/:id/procedures` | wired |
| `updateClaimDiagnoses` | `PUT /claims/:id/diagnoses` | wired |
| `addClaimAttachment` / `removeClaimAttachments` | `POST` / `DELETE /claims/:id/attachments` | wired |
| `addClaimNote` | `POST /claims/:id/notes` | wired |
| `listClaimProcedures` / `listClaimDiagnoses` / `listClaimAttachments` / `listClaimNotes` | the matching `GET`s | **all four unwired** |
| `getClaimFollowUp` / `updateClaimFollowUp` | `GET` / `PUT /claims/:id/follow-up` | **unwired** |

**Why the four `list*` GETs are unwired:** `GET /claims/:id` already returns
`claim_procedures`, `claim_diagnoses`, `claim_attachments`, `claim_notes` and
`claim_follow_up` inline. `mapClaimDetailResponse` (`src/utils/claimDetailMappers.js:40`)
reads all of them off that one payload, and 11 of `useClaimDetail`'s 13 mutators end with
`await load()` — a full re-`GET`. So the six drawer tabs never issue a sub-resource read.
The two exceptions are `replaceClaimAction` (`useClaimDetail.js:104`) and
`deleteClaimAction` (`:136`): the claim they were pointed at is gone, so the *parent*
reacts instead — `BillingSection.jsx:122-130` clears `detailClaimId` on delete, and on
replace refetches the list then re-points the drawer at the new claim id.

The `DELETE`s that carry a body use the client's `config.data`:
`removeClaimProcedures(id, body)` → `api.delete(path, { data: body })`.

---

## `PMS_React/src/api/payerPortals.js` (169 lines)

The only owned api module that follows the README's shape fully: a local `unwrapArray`
(line 15) plus three exported mappers — `normalizePortal`, `normalizePortalLogin`,
`normalizePortalCarrier`. List functions return `{ items, raw }`; getters return one
normalized object; writers return `response.data` raw.

| Function | Route |
|---|---|
| `listInsuranceCompanies` | `GET /insurance_company` |
| `getInsuranceCompany` | `GET /insurance_company/:id` |
| `createInsuranceCompany` | `POST /insurance_company` |
| `updateInsuranceCompany` | `PUT /insurance_company/:id` |
| `deleteInsuranceCompany` | `DELETE /insurance_company/:id` |
| `listPortalCarriers` | `GET /insurance_company_carriers?insurance_company_id=` |
| `listInsuranceLogins` | `GET /insurance_login` |
| `listInsuranceLoginsForPortal` | `GET /insurance_login_all/:insuranceCompanyId` |
| `getInsuranceLoginById` | `GET /insurance_login_by_id/:loginId` |
| `getPreferredInsuranceLogin` | `GET /insurance_login/:insuranceCompanyId` |
| `createInsuranceLogin` | `POST /insurance_login` |
| `updateInsuranceLogin` | `PUT /insurance_login/:id` |
| `deleteInsuranceLogin` | `DELETE /insurance_login/:id` |

`unwrapArray(data, keys)` tries, in order: `data` itself if it is an array, each named key
(`payers`, `insurance_companies`, `companies`, `carriers`, `logins`), then `data.data`.
That fallback chain is why three envelope shapes coexist without breaking this module —
if you add a route here, feed its response through `unwrapArray` with the right key rather
than writing a fourth unwrapper.

**Credentials are handled in plaintext.** `normalizePortalLogin` carries a `password`
field straight from the response into component state
(`src/api/payerPortals.js` `normalizePortalLogin`), and `PayerPortalsPanel.jsx` renders it
behind a show/hide toggle. Nothing is encrypted or redacted client-side. Treat that panel
as a PHI-adjacent surface: no logging, no toasting the value, no putting it in a URL.

---

## Mapper inventory

| File | Lines | Key exports |
|---|---|---|
| `src/utils/insuranceMappers.js` | 131 | `mapPatientInsuranceToView(patientInsurance, planDetail)`, `mapMockPatientInsuranceToView(patient)`, `parsePatientIdForApi` |
| `src/utils/claimMappers.js` | 139 | `mapClaimListItem`, `mapClaimsListResponse`, `computeClaimStats`, `filterClaimsBySubTab`, `filterClaimsBySearch`, `categorizeClaim`, `claimStatusBadgeClass`, `attentionBadgeClass`, `displayClaimStatus` |
| `src/utils/claimDetailMappers.js` | 176 | `mapClaimDetailResponse`, `detailToGeneralForm`, `detailToInfoForm`, `generalFormToUpdatePayload`, `infoFormToUpdatePayload`, `buildBulkCreatePayload` |
| `src/utils/eligibilityMappers.js` | 282 | `unwrapEligibilityList`, `pickLatestEligibility`, `mapEligibilityToBreakdown`, `splitPatientName`, `formatEligibilityDate`, `formatEligibilitySourceLabel` |
| `src/utils/payerUtils.js` | 131 | `normalizePayers`, `normalizeCarriers`, `filterPayers`, `filterCarriers`, `resolvePlanCarrierId`, `isVynePayer`, `findPayerById`, `findPayerByCarrierId`, `findPayerByDisplayName`, `formatPayerLabel` |

### Claim status buckets (`claimMappers.js:3-21`)

Three module-level `Set`s drive `categorizeClaim` and the summary cards:

- `ADJUDICATED_STATUSES` — Accepted, Paid, Settled, Pending, Resubmitted,
  Additional Information Requested, Zero Payment
- `DENIED_STATUSES` — Reject, Rejected, Rejected by Payer, Rejected by eServices,
  Unprocessible Claim
- `SENT_STATUSES` — Sent, Queued

These are **string sets, not ids**. A new backend status name silently falls into none of
the buckets and stops being counted. If you add one, add it here as well as to whatever
badge branch in `claimStatusBadgeClass`.

### `mapEligibilityToBreakdown` is a generic flattener

`eligibilityMappers.js` has no schema for the Stedi 271 response. It walks the payload with
`flattenObject` (depth-limited), humanizes snake_case keys into labels, and groups rows via
`sectionFromKeys` keyword matchers. Adding a field to the backend response makes it appear
in the UI with an auto-generated label and no code change. Conversely, a *renamed* field
does not error — it just lands in a different section or none.

---

## Backend documents

The authoritative request/response shapes live in three markdown files that are currently
misfiled in `PMS_React/public/` (see the security trap in `SKILL.md`):

- `INSURANCE_ROUTES_API.md` — 715 lines — plans, plan benefits, eligibility, patient-insurance
- `STEDI_PAYERS_AND_PORTALS_API.md` — 503 lines — `/payers/stedi`, `/insurance_company*`,
  `/insurance_login*`
- `insurance_api_frontend.md` — 437 lines — the frontend-facing summary

Read them for payload detail; do **not** treat their location as sanctioned.
