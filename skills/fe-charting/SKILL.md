---
name: fe-charting
description: Frontend odontogram / tooth chart — surfaces, findings, chart sessions (lock/unlock/resume/sign), procedure ledger, Charting Assistant note panel. Use when editing PMS_React/src/components/patient-detail/charting/ (Odontogram.jsx, ToothChartContext.jsx, ChartingContext.jsx, UnlockChartModal.jsx) or src/api/charting.js, hitting /v2/charts endpoints, or debugging chart_owned_session_<patientId>, entryType vs procedureStatus, /patients/:patientId/charting. NOT perio — see fe-perio.
---

## Scope

The Charting tab (`/patients/:patientId/charting`) minus perio: the 32-tooth Universal/ADA odontogram,
per-tooth status/surfaces/findings, the procedure ledger, the chart-session lock machine
(locked / active / in-use), the sign & unlock flow, layers/filters, and the Charting Assistant note
panel. README labels the section **live** — sessions and chart procedures are real endpoints.
Boundary: `charting/perio/` **and** `charting/PerioChartPanel.jsx` (84 KB) are **fe-perio** despite
sitting here; practice-wide defaults are edited in `components/settings/tooth-chart-defaults/`, read here.

## Files

Paths under `PMS_React/`; `…/` = `src/components/patient-detail/charting/` — 38 code files + 2 spec docs + `perio/`, of which `PerioChartPanel.jsx` and all of `perio/` are **fe-perio**, leaving 37 owned here.

| Path | Role |
|---|---|
| `…/ChartingSection.jsx` | **(entry)** sub-tabs + active panel + UnlockChartModal + Assistant; mounted by `src/pages/PatientDetail.jsx:307` |
| `…/ChartingContext.jsx` (29 KB) | session/lock state machine, provider pick, procedures load, saveDraft/signNote. Provider at `pages/PatientDetail.jsx:573` |
| `…/ChartingHeaderControls.jsx` | Locked↔Active header — rendered by `patient-detail/PatientSectionHeader.jsx:97`, not by ChartingSection |
| `…/ToothChartPanel.jsx` · `ToothChartContext.jsx` (45 KB) | the tooth-chart panel; per-tooth records, selection, all chart mutations |
| `…/Odontogram.jsx` · `ToothGraphic.jsx` (45 KB) · `ToothNumberStrip.jsx` · `toothBuccalSvgs.js` | arch layout, per-tooth SVG + finding overlays, number rail, `import.meta.glob` of the tooth SVGs |
| `…/AddChartingPopover.jsx` (22 KB) · `ToothDetailSidebar.jsx` · `SurfaceContextMenu.jsx` | charting entry UI |
| `…/ProcedureTable.jsx` · `ProcedureStatusMenu.jsx` · `EditProcedureModal.jsx` · `ChartStatusFilters.jsx` · `LayersDropdown.jsx` · `ChartLegend.jsx` · `ChartMaximizeModal.jsx` · `ChartingSubTabs.jsx` | ledger + row actions; filters/layers/legend/maximize/sub-tab chrome |
| `…/ChartingAssistant.jsx` (42 KB) · `SignNoteDialog.jsx` · `UnlockChartModal.jsx` | note panel, signature dialog, unlock/resume queue |
| `…/chartOwnership.js` | sessionStorage `chart_owned_session_<patientId>` accessors — the ownership rule |
| `…/chartingConstants.js` · `chartingCatalog.js` · `chartProcedureMappers.js` · `chartVisuals.js` · `chartFindingGraphics.js` (64 KB) · `chartingNoteTemplates.js` | constants, catalogs, mappers, SVG geometry — inventory in references |
| `…/useChartingConditionCatalog.js` · `useChartingProcedureCatalog.js` · `useClinicChartSettings.js` | live pick-lists + practice defaults, each dual-mode |
| `…/ScreeningsPanel.jsx` · `CHARTING_API_FLOW.md` · `CHARTING_API_SPEC.md` | **placeholder** 14-line `EmptyState`; the backend contract — **cite, never duplicate** |
| `src/api/charting.js` (45 KB) | the whole network contract + mocks. `grep -nE "^export "`, never read whole |
| `src/api/chartingCatalog.js` · `chartSettings.js` · `src/context/ChartSettingsContext.jsx` | `/v2/charts/conditions`, `/v2/chart-settings`, practice settings provider (`src/App.jsx:69`) |
| `src/assets/odontogram/teeth/` | the 64 live SVGs (`tooth-1..32-{buccal,lingual}`) |

## Contract

Renders at `ROUTES.patientCharting(patientId)` → `/patients/:patientId/charting`
(`src/config/routes.js:32`), section id `charting` in `src/config/patientSections.js:23`. Calls
`src/api/charting.js` (17 functions on `chartApi`, base `/v2/charts`), `chartingCatalog.js`,
`chartSettings.js`, and via `useChartingProcedureCatalog` `src/api/procedureCodes.js` — endpoint
table in `references/wire-and-state.md` §1. Exposes `useCharting()` / `useToothChart()`; consumes
`useChartSettingsOptional()`.

## Invariants

1. **`isReadOnly` is the only editing gate** — `status !== 'active'` (`ChartingContext.jsx:583`).
   Never gate on `isLocked`: an in-use chart is not locked (`ChartingSection.jsx:150`).
2. **Ownership lives in `sessionStorage`, never `localStorage`** (CLAUDE.md §7.5). The backend
   reports only that *a* session is open, not whose; `chart_owned_session_<patientId>` is how a
   tab knows it owns one. Per-tab by design. Always go through `chartOwnership.js`.
3. **Every session exit clears ownership** — `forgetOwnedSession` on sign, close, auto-sign-out;
   `rememberOwnedSession` on create and resume. A leak shows someone else's chart as editable.
4. **`entryType` ≠ `procedureStatus`.** `entryType` = `TP|Cn|EC|EO` (kind of entry);
   `procedureStatus` = `P|C|D|R`. Never map one onto the other. Transitions are one-way and
   one-time: only `P` may move, and `C`/`D`/`R` are terminal.
5. **Signer identity is server-side** (CLAUDE.md §7.7). `providerId`/`providerName` in the sign
   payload are convenience only; there is no client-side role gating anywhere in this app.
6. **Never render `autoSaveDraft` or any server HTML as markup** (CLAUDE.md §7.4) — carry it as an
   opaque string. `ToothGraphic.jsx:961` is the sole `dangerouslySetInnerHTML` and it renders
   bundled local SVG, never network data.
7. **Never log a chart payload, URL or patient id** (CLAUDE.md §7.1) — all PHI. Catch blocks
   re-throw via `toChartSessionError`; surface text with `getErrorMessage(err, fallback)`.
8. **Dual-mode by env-var presence** (CLAUDE.md §5): `isChartApiEnabled()` is only "is `VITE_APP_BASE_URL_CHART` non-empty" — unset it and charting silently serves mocks.
   Every new API function needs an `if (!isChartApiEnabled())` branch and a `normalizeX(raw)` mapper.
9. **`fetch()` never appears here.** Import from `src/api/`; `chartApi` always emits the
   same-origin `/__chart_api/api` prefix (the host refuses browser CORS) and the proxy is declared
   twice — `vite.config.js` and `vercel.json` — keep both in sync.
10. **Chart data loads once, in ChartingContext**: procedures, then `/active`, then the session
    list (`ChartingContext.jsx:171-215`). Do not add a second fetch in ToothChartProvider.
11. **No hardcoded hexes in components** — Tailwind utilities over `src/theme/theme.css` vars. The
    hexes in `chartVisuals.js` / `chartFindingGraphics.js` are SVG paint constants; leave them there.
12. **Overlays** = `createPortal` + `AnimatePresence` + `OverlayBackdrop` with a named
    `OVERLAY_Z_INDEX` key (`ChartMaximizeModal.jsx:36`, `UnlockChartModal.jsx:100`), never `z-[n]`.
    Feedback is `const { toast } = useToast()` — never `alert`.
13. **Tooth numbers are integers 1-32**; primary/mixed is unsupported and fails loudly (Traps).
    ISO `YYYY-MM-DD` on the wire; there is no date library in this repo.

## Working here

1. Read the relevant part of `CHARTING_API_FLOW.md` / `CHARTING_API_SPEC.md` first — that is the
   backend's contract, and a payload change has to land there too.
2. **New endpoint** → function in `src/api/charting.js` (doc block, mock branch, `unwrapResult`,
   `normalizeX`), then document it in `CHARTING_API_SPEC.md`.
3. **New chart mutation** → `ToothChartContext.jsx` (optimistic update + server call + rollback),
   then `AddChartingPopover.jsx` / `ToothDetailSidebar.jsx`, then `ProcedureTable.jsx` for its row.
4. **New visual/finding** → glyph in `chartVisuals.js`, geometry in `chartFindingGraphics.js`,
   catalog row in `chartingCatalog.js`, **and** a `CHART_LAYERS` entry — the forgotten step.
5. **New sub-tab** → `CHARTING_SUB_TABS` (`chartingConstants.js:16`) **and** the `PANELS` map
   (`ChartingSection.jsx:14`). Hiding a tab only removes its button; the render-time `resolvedTab`
   guard (`ChartingSection.jsx:50`) is what stops a hidden panel painting.
6. Gate anything editable on `charting.isReadOnly`. Verify with `npm run lint` — no test suite.

## Traps

- **Dead code, imported by nothing** (grep-verified): `ToothBuccalGraphic.jsx`, `TemplatesManagerModal.jsx`
  (*not* in the README's dead list — no importer exists), `chartingMockData.js` (only the FLOW doc names it),
  and the 9 generic SVGs directly under `src/assets/odontogram/` (only `teeth/` is globbed) — `toothBuccalSvgs.js` **is** live.
- **Dead exports in `src/api/charting.js:1020-1088`**: `fetchChartCatalog`, `updateToothStatus`,
  `addToothEntry`, `removeToothEntry` — proposed contract, never called. The live add path is
  `createChartProcedure`, discriminated by `type`.
- **Only `chart-session*` and `chartprocedure*` are backend-verified** (`charting.js:37-53`);
  paths on bare `${BASE}/…` (`sessions/:id`, `sessions/:id/note`, `catalog`) may still move.
- **Note templates are half-local**: `TemplatesManagerModal.jsx` imports no API; the Assistant
  merges `fetchChartTemplates()` rows onto the bundled set by `visitType`
  (`ChartingAssistant.jsx:271-290`). `ScreeningsPanel.jsx` is a placeholder — tab, no feature.
- **`primary` / `mixed` dentition is unsupported on purpose** — no artwork, integer 1-32 numbering,
  1-32 bounds in `ToothChartContext`/`EditProcedureModal`. `resolveDentition()` always returns
  `rendered: 'adult'`; `Odontogram.jsx:323` shows the banner. Half-implementing it would put adult
  tooth numbers on a child's record.
- **Nine sites cite `CLAUDE.md §5/§7.1/§7.4/§7.5/§7.7`** (`charting.js:31,153,303,490,802`;
  `chartOwnership.js:14`; both catalog hooks; `ChartingAssistant.jsx:286`). The README calls them
  dangling — now stale: workspace `CLAUDE.md` carries all five, restated above. `PROJECT_GUIDE.md`
  is stale and misleading; `PMS_React/README.md` is the source of truth.
- Editing anything under `src/context/` forces a **full page reload** (`fullReloadOnContextHmr()`
  in `vite.config.js`) — a `ChartSettingsContext.jsx` tweak drops all in-memory chart state.

## See also

`references/wire-and-state.md` (endpoint table, payload key mapping, lock state machine, helper
inventory, dentition) · `main-architecture` (hub) · **`be-charting`** (the Flask side of every
`/v2/charts` route here) · `fe-perio` (`charting/perio/` + `PerioChartPanel.jsx`) · `be-perio` ·
`fe-patient-chart` (the `/patients/:patientId/*` shell) · `fe-settings` (Tooth Chart Defaults) ·
`fe-platform` · in-repo `CHARTING_API_FLOW.md`, `CHARTING_API_SPEC.md`, `README.md` → "Clinical charting".
