---
name: fe-charting
description: Frontend odontogram / tooth chart — findings, chart sessions (lock/unlock/resume/sign), and the charted-treatment listing (Recommended Treatment / Clinical History / Treatment Plans tabs). Use when editing PMS_React/src/components/patient-detail/charting/ (Odontogram.jsx, ToothChartContext.jsx, ChartingContext.jsx, treatment-listing/*) or src/api/charting.js, hitting /v2/charts endpoints, or debugging chart_owned_session_<patientId>, entryType vs procedureStatus. NOT perio — see fe-perio.
---

## Scope

The Charting tab (`/patients/:patientId/charting`) minus perio: the 32-tooth Universal/ADA odontogram, per-tooth status /
surfaces / findings, the chart-session lock machine (locked / active / in-use), sign & unlock, layers/filters, the Charting
Assistant note panel, and the **treatment listing** below the chart (Recommended Treatment / Clinical History / Treatment
Plans). README labels the section **live**. Boundary: `charting/perio/` **and** `charting/PerioChartPanel.jsx` (84 KB) are
**fe-perio** despite sitting here; `patient-detail/tx-plans/` (plan builder, `txPlanFormat.js`, `txPlanUi.jsx`) is
**fe-patient-chart** — the listing imports from it, does not own it; Tooth Chart Defaults are edited in `fe-settings`.

## Files

Paths under `PMS_React/`; `…/` = `src/components/patient-detail/charting/`, `…/tl/` = `+treatment-listing/`. 39 code files + 2 spec docs at the root, plus `treatment-listing/` (12) and `perio/`; `PerioChartPanel.jsx` and `perio/` are **fe-perio**.

| Path | Role |
|---|---|
| `…/ChartingSection.jsx` | **(entry)** sub-tabs + active panel + UnlockChartModal + Assistant; mounted by `src/pages/PatientDetail.jsx:308` |
| `…/ChartingContext.jsx` (31 KB) | session/lock state machine, provider pick, procedures load, saveDraft/signNote. Provider at `pages/PatientDetail.jsx:585` |
| `…/ChartingHeaderControls.jsx` | Locked↔Active header — rendered by `patient-detail/PatientSectionHeader.jsx:97`, not by ChartingSection |
| `…/ToothChartPanel.jsx` · `ToothChartContext.jsx` (47 KB) | the panel (chart + listing + plan-builder host); per-tooth records, selection, all chart mutations |
| `…/Odontogram.jsx` · `ToothGraphic.jsx` (45 KB) · `ToothNumberStrip.jsx` · `toothBuccalSvgs.js` | arch layout, per-tooth SVG + finding overlays, number rail, `import.meta.glob` of the tooth SVGs |
| `…/AddChartingPopover.jsx` (26 KB) · `ToothDetailSidebar.jsx` · `SurfaceContextMenu.jsx` · `ProcedureStatusMenu.jsx` | charting entry UI + status-transition menu |
| `…/tl/TreatmentListingPanel.jsx` (21 KB) | **the listing** — three tabs; owns the plan-list + item-index reads, filters, paging, search, CSV, bulk select |
| `…/tl/RecommendedTreatmentTable.jsx` · `ClinicalHistoryTable.jsx` · `TreatmentPlansTable.jsx` · `treatmentListingFilters.js` · `treatmentListingCsv.js` · `procedureJourney.js` | the three tab bodies (history read-only by design; plans table renders `plan.statusLabel`), `LISTING_TABS`/`applyFilters`, CSV columns + formula-injection guard, "Patient journey" wording |
| `…/tl/ChartEntryDetailPanel.jsx` (26 KB) · `ProcedureDetailsModal.jsx` (26 KB) · `TreatmentBulkActionBar.jsx` · `AddToTreatmentPlanModal.jsx` · `TreatmentListingMenu.jsx` | row slide-over, editable detail modal, portal bulk bar, add-to-draft-plan modal, "⋯" tab menu |
| `…/ChartingAssistant.jsx` (42 KB) · `SignNoteDialog.jsx` · `UnlockChartModal.jsx` · `ChartStatusFilters.jsx` · `LayersDropdown.jsx` · `ChartLegend.jsx` · `ChartMaximizeModal.jsx` · `ChartingSubTabs.jsx` | note panel, signature dialog, unlock/resume queue; filters/layers/legend/maximize/sub-tab chrome |
| `…/chartOwnership.js` · `chartingConstants.js` · `chartingCatalog.js` · `chartProcedureMappers.js` · `chartVisuals.js` · `chartFindingGraphics.js` (64 KB) · `chartingNoteTemplates.js` · `chartingMultiCodes.js` | sessionStorage `chart_owned_session_<patientId>` accessors (the ownership rule); constants, catalogs, mappers, SVG geometry, bundles — inventory in references §5 |
| `…/useChartingConditionCatalog.js` · `useChartingProcedureCatalog.js` · `useClinicChartSettings.js` | live pick-lists + practice defaults, each dual-mode |
| `…/ScreeningsPanel.jsx` · `CHARTING_API_FLOW.md` · `CHARTING_API_SPEC.md` | **placeholder** 14-line `EmptyState`; the backend contract — **cite, never duplicate** |
| `src/api/charting.js` (49 KB) · `chartingCatalog.js` · `chartSettings.js` · `src/context/ChartSettingsContext.jsx` · `src/assets/odontogram/teeth/` | the whole network contract + mocks (`grep -nE "^export "`, never read whole); `/v2/charts/conditions`; `/v2/chart-settings`; settings provider (`src/App.jsx:79`); the 64 live SVGs `tooth-1..32-{buccal,lingual}` |

## Contract

Renders at `ROUTES.patientCharting(patientId)` → `/patients/:patientId/charting` (`src/config/routes.js:38`), section id `charting`
in `src/config/patientSections.js:24`. Calls `src/api/charting.js` (22 exported async functions on `chartApi`, base `/v2/charts`;
4 are dead — Traps), `chartingCatalog.js`, `chartSettings.js`, and via `useChartingProcedureCatalog` `src/api/procedureCodes.js`
(`authApi`), whose response carries the multi-codes too. The listing additionally calls **`src/api/treatmentPlans.js`** (owned by
`fe-patient-chart`): `listPatientTreatmentPlans`, `fetchTreatmentPlanItemIndex`, `addTreatmentPlanItems`,
`isTreatmentPlansApiEnabled`. Endpoint tables in `references/wire-and-state.md` §1. Exposes `useCharting()` / `useToothChart()`; consumes `useChartSettingsOptional()` (`useClinicChartSettings.js:25,55`).

## Invariants

1. **`isReadOnly` is the only editing gate** — `status !== 'active'` (`ChartingContext.jsx:615`). Never gate on `isLocked`: an in-use chart is not locked (`ChartingSection.jsx:150`).
2. **Ownership lives in `sessionStorage`, never `localStorage`** (CLAUDE.md §7.5). The backend reports only that *a* session is open, not whose. Per-tab by design; always go through `chartOwnership.js`.
3. **Every session exit clears ownership** — `forgetOwnedSession` on sign, close, auto-sign-out; `rememberOwnedSession` on create and resume. A leak shows someone else's chart as editable.
4. **`entryType` ≠ `procedureStatus`.** `entryType` = `TP|Cn|EC|EO` (kind of entry); `procedureStatus` = `P|C|D|R`. Never map one onto the other. One-way and one-time: only `P` may move, and `C`/`D`/`R` are terminal.
5. **A multi-code is never charted as itself** — that writes one $0 ledger line for work nobody performed. A click charts its
   `members` through `addProcedures`, in one batch. Identify a bundle by `item_type === 'multi'`, never by category. There is
   no multi-codes request in the charting path: `GET /v2/procedure-codes` already returns them (references §1).
6. **The listing never fetches chart rows.** `ChartingContext` is the single fetcher and refetches after every chart write; the panel takes them as the `rows` prop (`ToothChartPanel.jsx:158-165`). A second copy goes stale on the next tooth charted.
7. **Plan membership is ENRICHMENT, never a gate.** Chart rows must render when the plan service is down: set `planApiAvailable=false` and *drop* the chips rather than badging every row "Not in Treatment Plan".
   `null` ≠ `undefined` here — `procedureJourney.js:32` reads `null` as "unavailable", `undefined` as "on no plan".
8. **Plan status is read, never re-derived.** `TreatmentPlansTable` renders `plan.statusLabel` with `planStatusToneId(plan.status)`
   (`tx-plans/txPlanFormat.js:58`), so a server-derived status such as `scheduled` needs no change here. Do not add a local status map.
9. **Only a DRAFT plan can be added to** (`AddToTreatmentPlanModal.jsx:5`) — the server answers 409 for anything else.
10. **Signer identity is server-side** (CLAUDE.md §7.7); `providerId`/`providerName` in the sign payload are convenience only.
11. **Never render `autoSaveDraft` or any server HTML as markup** (CLAUDE.md §7.4) — carry it as an opaque string. `ToothGraphic.jsx:961`
    is the only **live** `dangerouslySetInnerHTML` here and it paints bundled local SVG, never network data (`ToothBuccalGraphic.jsx:39` is dead).
12. **Never log a chart payload, URL or patient id** (CLAUDE.md §7.1) — all PHI. Catch blocks re-throw via
    `toChartSessionError`; surface text with `getErrorMessage(err, fallback)`.
13. **Dual-mode by env-var presence** (CLAUDE.md §5): `isChartApiEnabled()` is only "is `VITE_APP_BASE_URL_CHART` non-empty".
    Every new API function needs an `if (!isChartApiEnabled())` branch and a `normalizeX(raw)` mapper.
14. **`fetch()` never appears here.** `chartApi` always emits the same-origin `/__chart_api/api` prefix (the host refuses
    browser CORS); that proxy lives in **three** blocks — `server.proxy` + `preview.proxy` in `vite.config.js`, `rewrites` in
    `vercel.json` — which change together.
15. **Chart data loads once, in ChartingContext**: procedures, then `/active`, then the session list
    (`ChartingContext.jsx:199-241`). Do not add a second fetch in ToothChartProvider.
16. **No hardcoded hexes in components** (`chartVisuals.js` / `chartFindingGraphics.js` hexes are SVG paint — leave them);
    overlays are `createPortal` + `AnimatePresence` + `OverlayBackdrop` with a named `OVERLAY_Z_INDEX` key
    (`ChartMaximizeModal.jsx:36`, `UnlockChartModal.jsx:102`), never `z-[n]`; feedback is `useToast()`, never `alert`.
17. **Tooth numbers are integers 1-32**; primary/mixed is unsupported and fails loudly (Traps). ISO `YYYY-MM-DD` on the wire.

## Working here

1. Read the relevant part of `CHARTING_API_FLOW.md` / `CHARTING_API_SPEC.md` first — that is the backend's contract, and a
   payload change has to land there too.
2. **New endpoint** → function in `src/api/charting.js` (doc block, mock branch, `unwrapResult`, `normalizeX`), then document
   it in `CHARTING_API_SPEC.md`.
3. **New chart mutation** → `ToothChartContext.jsx` (optimistic update + server call + rollback), then `AddChartingPopover.jsx`
   / `ToothDetailSidebar.jsx`. Anything charting more than one row at once goes through `addProcedures` — looping
   `addProcedure` reads a `chartRef` that only catches up after a render, so its duplicate check misfires mid-batch.
4. **New listing column or filter** → the tab's table under `…/tl/`, **and** `treatmentListingCsv.js` (the tables are its spec:
   same columns, same order), **and** `treatmentListingFilters.js` for a new chip. A write inside the panel calls its own
   `load()` plus `onChartMutated`; a write in the plan builder signals back via `onChanged` → `setListingKey`
   (`ToothChartPanel.jsx:189`), remounting the panel. All three reads move together — references §7.
5. **New visual/finding** → glyph in `chartVisuals.js`, geometry in `chartFindingGraphics.js`, catalog row in
   `chartingCatalog.js`, **and** a `CHART_LAYERS` entry — the forgotten step.
6. **New sub-tab** → `CHARTING_SUB_TABS` (`chartingConstants.js:16`) **and** the `PANELS` map (`ChartingSection.jsx:14`).
   Hiding a tab only removes its button; the render-time `resolvedTab` guard (`ChartingSection.jsx:50`) stops the paint.
7. Gate anything editable on `charting.isReadOnly`. Verify with `npm run lint` — no test suite.

## Traps

- **Archived plans vanish from this listing with no explanation.** The backend hides `archived_at` plans from both reads by
  default (`360_Flask_Appointment/app/treatment_plans_v2_routes.py:1051` and `:2745`), and the panel calls
  `listPatientTreatmentPlans({ patientId })` with no `includeArchived` and has **no "Show archived" toggle** — so archiving a
  plan also strips the badge off its chart rows, which fall back to "Not in Treatment Plan". Not a bug in the item index.
  (Removing a plan is archive, not void and not delete — see `fe-patient-chart` / `be-treatment-plans`.)
- **Dead code, imported by nothing** (grep-verified): `ProcedureTable.jsx` and, through it only, `EditProcedureModal.jsx` — both
  superseded by `treatment-listing/` (`ToothChartPanel.jsx:155-157`); `ToothBuccalGraphic.jsx`; `TemplatesManagerModal.jsx`;
  `chartingMockData.js`; the 9 generic SVGs directly under `src/assets/odontogram/` (only `teeth/` is globbed —
  `toothBuccalSvgs.js` **is** live); and `charting.js:1085-1153` (`fetchChartCatalog`, `updateToothStatus`, `addToothEntry`,
  `removeToothEntry` — a proposed tooth-level contract; the live add path is `createChartProcedure`, keyed on `type`).
- **Only `chart-session*` and `chartprocedure*` are backend-verified** (`charting.js:37-54`); paths on bare `${BASE}/…`
  (`sessions/:id`, `sessions/:id/note`, `catalog`) may still move.
- **Note templates are half-local**: the Assistant merges `fetchChartTemplates()` rows onto the bundled set by `visitType`,
  keeping the bundled id so existing notes are not orphaned (`ChartingAssistant.jsx:269-297`). `ScreeningsPanel.jsx` is a
  placeholder — a tab, not a feature.
- **`primary` / `mixed` dentition is unsupported on purpose** — no artwork, integer 1-32 numbering. `resolveDentition()` always
  returns `rendered: 'adult'`; `Odontogram.jsx:323` renders the banner. Detail in references §6.
- Editing anything under `src/context/` forces a **full page reload** (`fullReloadOnContextHmr()` in `vite.config.js`) — a
  `ChartSettingsContext.jsx` tweak drops all in-memory chart state.

## See also

`references/wire-and-state.md` (endpoints, payload keys, lock machine, listing data flow, helper inventory, dentition,
CLAUDE.md citation sites) · `main-architecture` (hub) · **`be-charting`** (the Flask side of every `/v2/charts` route here) ·
**`be-treatment-plans`** (plan list, item index, archive semantics) · `fe-patient-chart` (`tx-plans/` builder,
`txPlanFormat.js`, and the `/patients/:patientId/*` shell) · `fe-perio` · `be-perio` · `fe-settings` (Tooth Chart Defaults) ·
`fe-platform` · in-repo `CHARTING_API_FLOW.md`, `CHARTING_API_SPEC.md`, `README.md`.
