# fe-charting — wire contract, state machine, helper inventory

Detail overflow from `fe-charting/SKILL.md`. The authoritative narrative lives in the repo:
`PMS_React/src/components/patient-detail/charting/CHARTING_API_FLOW.md` (261 lines, user flow +
backend guide) and `CHARTING_API_SPEC.md` (338 lines, data dictionary + per-endpoint shapes).
Read those before changing a payload. This file is the index into them.

## 1. Endpoints actually called (all via `chartApi`, base `/v2/charts`)

`PMS_React/src/api/charting.js` — 45 KB. `grep -nE "^export " ` it; never read whole.

| Function (line) | Call |
|---|---|
| `createChartSession` (273) | `POST /v2/charts/chart-session` |
| `fetchActiveChartSession` (349) | `GET  /v2/charts/chart-session/active` |
| `fetchChartSessions` (370) | `GET  /v2/charts/chart-session` |
| `resumeChartSession` (424) | `POST /v2/charts/chart-session/resume` |
| `signChartSession` (492) | `POST /v2/charts/chart-session/signed` |
| `autoSignChartSession` (521) | `POST /v2/charts/chart-session/autosign` |
| `saveChartSessionDraft` (536) | `POST /v2/charts/chart-session/draft` |
| `updateChartSession` (565) | `PATCH /v2/charts/sessions/:id` |
| `saveVisitNote` (594) | `PUT  /v2/charts/sessions/:id/note` |
| `addProcedure` (626) | `POST /v2/charts/sessions/:id/procedures` |
| `createChartProcedure` (752) | `POST /v2/charts/chartprocedure` |
| `fetchChartProcedures` (903) | `GET  /v2/charts/chartprocedure` |
| `deleteChartProcedure` (934) | `DELETE /v2/charts/chartprocedure` (body `{sessionId, objectId}`) |
| `updateChartProcedureStatus` (979) | `POST /v2/charts/chartprocedure/status` |
| `fetchChartTemplates` (821) | `GET  /v2/charts/chart-templates` |
| `fetchChartSessionTemplates` (859) | `GET  /v2/charts/chart-session/templates` (plural — different path) |
| `applyChartSessionTemplate` (881) | `POST /v2/charts/chart-session/template` (singular) |

Only `chart-session*` and `chartprocedure*` are marked VERIFIED against the live backend
(`charting.js:37-53`). Everything on bare `${BASE}/…` is a proposed contract.

**Exported but called by nothing** (proposed tooth-level contract, `charting.js:1020-1088`):
`fetchChartCatalog`, `updateToothStatus`, `addToothEntry`, `removeToothEntry`. The comment at
`charting.js:995-1000` says so explicitly. The live add path is `createChartProcedure`,
discriminated by `type` (`TP | Cn | EC | EO`).

Sibling modules: `PMS_React/src/api/chartingCatalog.js` → `GET /v2/charts/conditions`
(`listChartingCatalog`, own `isChartingCatalogApiEnabled()`), and
`PMS_React/src/api/chartSettings.js` → `GET/PUT /v2/chart-settings` (gated by
`isChartApiEnabled`, re-exported as `isChartSettingsApiEnabled`).

## 2. `createChartProcedure` payload (charting.js:752-795)

Wire keys differ from UI keys: `code → cdtCode`, `label → description`, `fee → ucrFeeCents`
(cents, rounded), `note → comments`, `toothNumber` is a **string**. `surfaces` is sent as
abbreviations (`surfacesToAbbr`, charting.js:674) and is **omitted entirely** when the provider
picked none — do not fabricate `["M","D","B","L","O"]` for a whole-tooth procedure.

## 3. The lock state machine

`ChartingContext.jsx:91` holds `status ∈ CHART_STATUS` (`chartingConstants.js:137`).

```
             no active session ─────────────────────────────► locked
 active session && ownsSession(patientId, id) ─────────────► active
 active session && !ownsSession ───────────────────────────► in-use
 active.status !== 'active' (draft/pending_*) ─────────────► locked   (parked, resumable)
```

Derived at `ChartingContext.jsx:579-587`: `isLocked`, `isInUse`, `isReadOnly = status !== active`,
`pendingSession`, `isEditOnly = session.mode === 'edit-only'`.

Transitions write ownership: `rememberOwnedSession` at create (353) and resume (466);
`forgetOwnedSession` at auto-sign-out (405), close (503), and sign (546).

Page-load order is deliberate (`ChartingContext.jsx:171-215`): procedures **first** so the
odontogram can paint, then `/active`, then the full session list for the Unlock modal's
Resume / Auto Sign Out queue. Every step is non-fatal — a failure leaves the chart locked
rather than blocking the page. Guarded by a `cancelled` flag, not a request-id ref.

## 4. `entryType` vs `procedureStatus`

- `entryType` — *what kind of entry*: `TP` treatment-planned, `Cn` condition/finding,
  `EC`/`EO` existing restoration. Helpers: `normEntryType`, `isExistingType`, `isConditionType`
  (`chartProcedureMappers.js:39-54`).
- `procedureStatus` — *clinical state*: `P` planned, `C` completed, `D` declined, `R` referred
  (`CHART_PROCEDURE_STATUS`, charting.js:952).
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

## 6. Dentition

`useClinicChartSettings.js:100-172`. `resolveDentition()` always returns `rendered: 'adult'`.
`primary` and `mixed` are deliberately unsupported — no A-T/51-85 artwork, integer 1-32
numbering everywhere, and 1-32 bounds in `ToothChartContext` / `EditProcedureModal`. The failure
is loud on purpose: `useChartDentition()` logs one dev warning per setting and `Odontogram.jsx:323`
renders `DentitionUnsupportedBanner` (`data-testid="dentition-unsupported-banner"`). Do not
"fix" this by silently rendering adult teeth for a child.
