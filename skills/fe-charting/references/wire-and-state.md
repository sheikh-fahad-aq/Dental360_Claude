# fe-charting — wire contract, state machine, helper inventory

Detail overflow from `fe-charting/SKILL.md`. The authoritative narrative lives in the repo:
`PMS_React/src/components/patient-detail/charting/CHARTING_API_FLOW.md` (261 lines, user flow +
backend guide) and `CHARTING_API_SPEC.md` (338 lines, data dictionary + per-endpoint shapes).
Read those before changing a payload. This file is the index into them.

## 1. Endpoints actually called (all via `chartApi`, base `/v2/charts`)

`PMS_React/src/api/charting.js` — 49 KB. `grep -nE "^export " ` it; never read whole.

| Function (line) | Call |
|---|---|
| `createChartSession` (278) | `POST /v2/charts/chart-session` |
| `fetchActiveChartSession` (354) | `GET  /v2/charts/chart-session/active` |
| `fetchChartSessions` (375) | `GET  /v2/charts/chart-session` |
| `resumeChartSession` (429) | `POST /v2/charts/chart-session/resume` |
| `signChartSession` (497) | `POST /v2/charts/chart-session/signed` |
| `autoSignChartSession` (526) | `POST /v2/charts/chart-session/autosign` |
| `saveChartSessionDraft` (541) | `POST /v2/charts/chart-session/draft` |
| `updateChartSession` (570) | `PATCH /v2/charts/sessions/:id` |
| `saveVisitNote` (599) | `PUT  /v2/charts/sessions/:id/note` |
| `addProcedure` (631) | `POST /v2/charts/sessions/:id/procedures` |
| `createChartProcedure` (757) | `POST /v2/charts/chartprocedure` |
| `fetchChartProcedures` (908) | `GET  /v2/charts/chartprocedure` |
| `deleteChartProcedure` (939) | `DELETE /v2/charts/chartprocedure` (body `{sessionId, objectId}`) |
| `updateChartProcedureStatus` (984) | `POST /v2/charts/chartprocedure/status` |
| `updateChartProcedureDetails` (1035) | `POST /v2/charts/chartprocedure/details` — fee/provider/date/comments, partial by KEY PRESENCE; the ONLY chart-procedure write with **no active-session gate**, and it rejects `cdtCode`/`type`/`toothNumber`/ids/`status` with 400 |
| `fetchPatientDentition` / `savePatientDentition` | `GET`/`PUT /v2/charts/patient-dentition` — the per-patient tooth set. `dentition: null` is "no override", not an error; PUTting null CLEARS it (the server deletes the row). The READ never throws — a failure reads as no override, which falls back to the practice default; the WRITE does, because a clinician pressed a button |
| `fetchChartTemplates` (826) | `GET  /v2/charts/chart-templates` |
| `fetchChartSessionTemplates` (864) | `GET  /v2/charts/chart-session/templates` (plural — different path) |
| `applyChartSessionTemplate` (886) | `POST /v2/charts/chart-session/template` (singular) |

Only `chart-session*` and `chartprocedure*` are marked VERIFIED against the live backend
(`charting.js:37-54`). Everything on bare `${BASE}/…` is a proposed contract.

**Exported but called by nothing** (proposed tooth-level contract, `charting.js:1085-1153`):
`fetchChartCatalog`, `updateToothStatus`, `addToothEntry`, `removeToothEntry`. The banner comment at
`charting.js:1057-1067` says so explicitly. The live add path is `createChartProcedure`,
discriminated by `type` (`TP | Cn | EC | EO`).

Sibling modules: `PMS_React/src/api/chartingCatalog.js` → `GET /v2/charts/conditions`
(`listChartingCatalog`, own `isChartingCatalogApiEnabled()`), and
`PMS_React/src/api/chartSettings.js` → `GET/PUT /v2/chart-settings` (gated by
`isChartApiEnabled`, re-exported as `isChartSettingsApiEnabled`).

**Not on `chartApi`** — the Procedures tab's pick-list rides the AUTH backend:
`src/api/procedureCodes.js` → `GET /v2/procedure-codes`, gated by `isAuthApiEnabled`.

**That one call also carries the bundles.** The response has `multi_codes` as its own array
beside `procedure_codes`, each bundle already holding the member procedures it stands for:

```json
{ "procedure_codes": [ { "code": "D2161", "item_type": "procedure", … } ],
  "multi_codes":     [ { "code": "DEVADCOEPV", "name": "Adult COE PVT", "item_type": "multi",
                         "procedure_count": 2, "procedure_codes_csv": "D0012, DEV000",
                         "procedures": [ { "procedure_code": "D0012",
                                           "procedure_name": "Gum Builder", "fee": 0, … } ] } ],
  "multi_codes_total": 2 }
```

So charting makes **no** multi-codes request: `listProcedureCodes` returns `multiCodes` (run
through `normalizeMultiCode`, reused from `src/api/multiCodes.js`) next to `items`, and
`useChartingProcedureCatalog` returns them as `multiCodes` for the picker's section. The same
response fills the section and supplies what gets charted, so the list cannot promise one
procedure and chart another. `previewMultiCode` / `listMultiCodes` still exist for
Settings › Multi-Codes; charting calls neither.

Three traps live in that shape:

1. **Bundles are not paged with the codes.** `total` / `total_pages` describe `procedure_codes`
   alone and the same bundles repeat on **every** page, so the paging loop gathers them into a
   `Map` by id — appending would yield one copy per page.
2. **Category does not identify a bundle.** The live ones are filed under Orthodontics (15) and
   Diagnostic (6), *not* "Multi-codes" (18). `isMultiCodeRow` tests `item_type === 'multi'`
   first and only falls back to the category when the field is absent — otherwise every
   ordinary Orthodontics code would be swallowed as a bundle.
3. **A member fee of 0 is a real answer** (several codes here are genuinely 0), so the catalog
   price book is consulted only when the bundle gave no number at all — it exists for the thin
   `procedure_codes_csv`-only response, where names and fees are backfilled by code.

Archived bundles (`is_active === false`) are dropped client-side. With the auth API off there
is no mock bundle catalog and none is invented — the section simply does not appear.

## 2. `createChartProcedure` payload (charting.js:757-801)

Wire keys differ from UI keys: `code → cdtCode`, `label → description`, `fee → ucrFeeCents`
(cents, rounded), `note → comments`, `toothNumber` is a **string**. `surfaces` is sent as
abbreviations (`surfacesToAbbr`, charting.js:679) and is **omitted entirely** when the provider
picked none — do not fabricate `["M","D","B","L","O"]` for a whole-tooth procedure.

## 3. The lock state machine

`ChartingContext.jsx:94` holds `status ∈ CHART_STATUS` (`chartingConstants.js:137`).

```
             no active session ─────────────────────────────► locked
 active session && ownsSession(patientId, id) ─────────────► active
 active session && !ownsSession ───────────────────────────► in-use
 active.status !== 'active' (draft/pending_*) ─────────────► locked   (parked, resumable)
```

Derived at `ChartingContext.jsx:609-619`: `isLocked`, `isInUse`, `isReadOnly = status !== active`,
`pendingSession`, `isEditOnly = session.mode === 'edit-only'`.

Transitions write ownership: `rememberOwnedSession` at create (378) and resume (491);
`forgetOwnedSession` at auto-sign-out (430), close (528), and sign (571).

Page-load order is deliberate (`ChartingContext.jsx:199-241`): procedures **first** so the
odontogram can paint, then `/active`, then the full session list for the Unlock modal's
Resume / Auto Sign Out queue. Every step is non-fatal — a failure leaves the chart locked
rather than blocking the page. Guarded by a `cancelled` flag, not a request-id ref.

## 4. `entryType` vs `procedureStatus`

- `entryType` — *what kind of entry*: `TP` treatment-planned, `Cn` condition/finding,
  `EC`/`EO` existing restoration. Helpers: `normEntryType`, `isExistingType`, `isConditionType`
  (`chartProcedureMappers.js:39-54`).
- `procedureStatus` — *clinical state*: `P` planned, `C` completed, `D` declined, `R` referred
  (`CHART_PROCEDURE_STATUS`, charting.js:957).
- One-way, one-time: only `P` may move, and `C`/`D`/`R` are terminal. Mirrored client-side by
  `allowedNextStatuses` (`chartProcedureMappers.js:95`) so the menu never offers a rejected
  transition; enforced server-side.
- A row with a `sourceId` (a procedure paired to a finding) and a `kind === 'status'` row never
  offer a transition.

## 5. Helper module inventory

| File | Lines | What it holds |
|---|---|---|
| `chartingConstants.js` | 232 | `UPPER_TEETH`/`LOWER_TEETH`, `CHART_STATUS`, `CHART_SESSION_MODE`, `CHART_VISIT_TYPES`, sub-tab registry, `getQuadrantPosition`/`getToothType`/`getBitingSurface`/`getChartableSurfaces`, `toChartDateKey` |
| `chartingCatalog.js` | 406 | `TOOTH_SURFACES`, `TOOTH_STATUSES`, `TOOTH_CONDITIONS`, `EXISTING_RESTORATIONS`, `PROCEDURE_CATALOG`, `PROCEDURE_STATUS_META`, `CHART_LAYERS`, `formatChartSite` |
| `chartProcedureMappers.js` | 273 | wire rows → per-tooth chart: `buildChartFromProcedures`, `allowedNextStatuses`, `isTreatmentRow`, `isProcedureRowDeletable` |
| `chartVisuals.js` | 481 | CDT classification (`parseCdtCode`, `classifyCdtCode`, `isFixtureCode`, `classifyCondition`, `describeChartEntry`), `SURFACE_PAINT`/`TOOTH_OVERLAY`/`TOOTH_GLYPH`/`VISUAL_COLOR` |
| `chartFindingGraphics.js` | 1377 | pure SVG geometry for findings (caries dots, fracture polylines, root position). Biggest file in the slice; `grep` it |
| `chartingNoteTemplates.js` | 425 | bundled note templates, `cloneTemplate`, `makeBlankTemplate` |
| `chartOwnership.js` | 73 | the four sessionStorage accessors + `ownedSessionKey` |
| `chartingMultiCodes.js` | 125 | pure helpers, no hooks/network: `MULTI_CODE_CATEGORY_ID` (18), `isMultiCodeRow`, `buildPriceBook`, `toChartingMultiCode(raw, priceBook)` → bundle + `members` (chart-ready) + `memberCount`. Fetched by `useChartingProcedureCatalog`, which returns `multiCodes` |

## 6. Dentition

Three tooth sets render. `resolveDentition(defaultDentition, { dobISO, override })` in
`useClinicChartSettings.js` is the only place the question is answered; `useChartDentition.js`
is the hook that feeds it (its own file so `useClinicChartSettings` and `ChartingContext` do not
import each other — ChartingContext already imports the former for the default provider).

| Set | Upper, screen left → right | Lower, screen left → right |
|---|---|---|
| `adult` | 1 … 16 | 32 … 17 |
| `primary` | A … J | T … K |
| `mixed` | 1,2,3, A … J, 14,15,16 | 32,31,30, T … K, 19,18,17 |

Precedence: the patient's stored dentition (`/v2/charts/patient-dentition`) → the practice
setting when it names a set outright → the age rule. The age rule is under 6 primary, 6-12
mixed, 13+ adult, from `ChartingProvider`'s `patientDob` (ISO; `patient.dob` is a locale string
and `patient.age` is 0 for an unrecorded date, so `patientMappers.js` gained `dobISO`). **No date
of birth holds at adult** — the placeholder patient paints for the first frames of every
navigation and reports `age: 0`.

`supported` and the `DentitionUnsupportedBanner` survive with nothing shipped triggering them:
they are the gate a future numbering scheme (FDI, supernumeraries, retained deciduous) passes
through before it can be offered in Settings.

**Perio is untouched and must stay that way.** `chart_perio_measurements.tooth_number` is a
`SmallInteger` with a DB CHECK of 1-32, `perioGridModel.js` slices `PERMANENT_UPPER_TEETH` by
index to mean "the patient's right half", and the midline-mirror predicate is `n >= 9 && n <= 24`.
A letter reaching any of it produces reading keys like `"NaN:MB"`, a grid whose every cell is
disabled, and a save that throws before it sends — with no error surfaced anywhere.

## 7. The treatment listing's three reads

`…/treatment-listing/TreatmentListingPanel.jsx` renders under the odontogram (`ToothChartPanel.jsx:158`)
and joins three sources that must stay in step:

| Source | Owner | Note |
|---|---|---|
| chart procedures (`rows` prop) | `ChartingContext` | the single fetcher; refetches after every chart write. The panel never fetches these. |
| `listPatientTreatmentPlans({ patientId })` | the panel's own `load()` | no `includeArchived`, so **archived plans are absent**; there is no "Show archived" toggle here |
| `fetchTreatmentPlanItemIndex(patientId)` | the panel's own `load()` | `Map` chartProcedureId → plan item; the backend also excludes archived plans from it |

Both plan reads run in one `Promise.all` guarded by a request-id ref; on failure the panel sets
`planApiAvailable = false`, keeps the chart rows, and drops the chips. Writes: row/bulk chart writes call
`load()` + `onChartMutated`; the plan builder calls `onChanged`, which bumps `listingKey`
(`ToothChartPanel.jsx:189`) and remounts the panel so all three reads restart.

Tabs (`treatmentListingFilters.js:17`): `recommended` (`entryType === 'TP'` and status not `C`/`D`),
`history` (`Cn`/`EC`/`EO`, or `TP` with `C`/`D`/`R`), `plans`. Badge text comes from
`chartProcedurePlanState()` (`tx-plans/txPlanFormat.js:148`) — scheduling beats acceptance beats
presentation; `undefined` → "Not in Treatment Plan". Plan-row status text is `plan.statusLabel` from the
server (`api/treatmentPlans.js:75,300`), never re-derived here.

## 8. `CLAUDE.md` citation sites in this slice

Eleven, all still resolving to sections the workspace `CLAUDE.md` carries (the README calls them dangling —
that is stale): `src/api/charting.js:31` (§5), `:158` (§7.4), `:308` (§7.1), `:495` (§7.7), `:807` (§7.4),
`:1032` (§6.8); `chartOwnership.js:14` (§7.5); `useChartingConditionCatalog.js:29` (§5);
`useChartingProcedureCatalog.js:14,117` (§5); `ChartingAssistant.jsx:286` (§7.4).

Separately, `PMS_React/PROJECT_GUIDE.md` is **stale and actively misleading** (stamped July 2026);
`PMS_React/README.md` is the source of truth for this slice — the README says so itself at `README.md:453`
and `:586`.
