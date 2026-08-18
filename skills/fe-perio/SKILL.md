---
name: fe-perio
description: Periodontal charting UI — the Perio Chart sub-tab: the ~200-cell measurement grid (PD, GM, CAL, MGJ, BOP, Sup, plaque/calculus, mobility, bone loss, furcation), the keypad entry panel, navigation scripts, and the draft/final/void exam lifecycle. Use when changing PerioChartPanel.jsx, anything under charting/perio/, or src/api/chartPerio.js, or when debugging /v2/charts/perio-exam start, autosave flush, finalize, reopen, void, or the Manage menu date gate. Not the odontogram — fe-charting.
---

## Scope

The Perio Chart sub-tab of the patient chart — `ChartingSection.jsx:16` maps panel id `perio` to
`PerioChartPanel`. **Maturity: live end to end** against `/v2/charts/perio-exam` (start, edit
settings, bulk readings, finalize, reopen, void, soft delete), with two `partial` gaps inside it
(see Traps). There is **no mock path**: perio re-exports the chart gate (`export
{ isChartApiEnabled as isPerioApiEnabled }`, `chartPerio.js:66`), so with the chart base URL unset
every call throws "Perio API is not configured." rather than serving mock rows. This slice owns the
exam and its measurements; the odontogram, chart session and lock belong to `fe-charting`.

## Files

Under `PMS_React/`; `…/` = `src/components/patient-detail/charting/perio/`. Sized files: `grep -nE "^export "` then `sed -n`, never read whole.

| Path | Role |
|---|---|
| `src/components/patient-detail/charting/PerioChartPanel.jsx` **(entry)** | 84KB. Composition + exam LIST/pick; `PerioExamHeader` (:298), `wasCreatedToday` (:184), `PerioChartPanelInner` (:452), export (:1539) |
| `src/api/chartPerio.js` | 60KB. The only perio wire module: constants, normalizers, 9 calls |
| `…/PerioExamContext.jsx` | 61KB. `PerioExamProvider`, `usePerioExam` / `usePerioExamActions` / `usePerioExamOptional`; reading store, autosave flush, focus route |
| `…/PerioChartGrid.jsx` | The one `overflow-x-auto` scroller + row stack; arrow/Enter movement (:206) |
| `…/PerioGridRow.jsx`, `…/PerioSiteInput.jsx`, `…/PerioDepthGraph.jsx` | One row; the four cell shapes (input, `PerioComputedCell`, `PerioFlagCell`, `PerioToothCell`); the depth plot band |
| `…/PerioEntryPanel.jsx`, `…/PerioBopSupAllTeethModal.jsx` | 55KB / 45KB. Docked flags + measurements + two-page keypad; the sextant-tabbed BOP/Sup all-teeth modal with its own draft |
| `…/PerioChartToolbar.jsx`, `…/PerioExamManageMenu.jsx` | 45KB. Zoom, script switch, mode strips, `PERIO_DEFAULT_ZOOM` (:212); the Manage dropdown (Edit · Delete · Void · Reopen · Print) |
| `…/NewPerioExamDialog.jsx`, `…/FinishPerioExamDialog.jsx` | 49KB. One shell, two modes + `EditPerioExamDialog` (:953); Finish plus the carry-forward-previous choice |
| `…/PerioNavigationFields.jsx`, `…/MouthNavigationDiagram.jsx` | Script pickers; arch route diagram + `describeScript` |
| `…/PerioScriptEditors.jsx`, `…/PerioPrintView.jsx` | 51KB custom-script dialogs, **no caller in `src`** (dead); print surface with `printPerioExam()` (:96) |
| `…/perioExamDefaultsConstants.js` | 93KB. Pure data: scripts, passes, bound mirrors, grades, keypad pages, sites |
| `…/perioGridModel.js` | 32KB. Store key, site order, visible rows, visit orders, sextants, `shouldAdvanceImmediately` |
| `…/perioGridLabels.js`, `…/perioExamDate.js` | Accessible cell names; `formatExamDate`, `summarizePerioExam`, `examOptionLabel(s)` |

## Contract

Every call is `chartApi` (same-origin `/__chart_api/api`) + `BASE = '/v2/charts/perio-exam'`.

| `chartPerio.js` export | Wire |
|---|---|
| `createPerioExam` | `POST /v2/charts/perio-exam` — body rebuilt from `PERIO_EXAM_FIELDS` |
| `fetchPerioExams` / `fetchPerioExam` | `GET …?patientId=&locationId=` (rows carry `measurementCount`, `measurements: null`) · `GET …/{examId}` (detail; `measurements` is an array, maybe `[]`) |
| `updatePerioExam` | `PATCH …/{examId}` — only the 7 `PERIO_EXAM_EDITABLE_FIELDS` |
| `savePerioMeasurements` | `POST …/{examId}/measurements` — `{ measurements: [...] }`, chunked at 256 |
| `finalizePerioExam` | `POST …/{examId}/finalize` — `{ carryForwardPrevious: true }` only when true |
| `reopenPerioExam` | `POST …/{examId}/reopen` — `final → draft` **and `void → draft`** |
| `voidPerioExam` / `deletePerioExam` | `POST …/{examId}/void` · `DELETE …/{examId}` (soft; 409 on a void exam) |

Renders no route of its own — it is a panel inside the chart route (`fe-patient-chart` owns that shell). Also exports `perioCal`, `normalizePerioExam`, `normalizePerioMeasurement`, `perioMeasurementsHaveRecordedValues` and the constants `PERIO_SITES`, `PERIO_SITE_FIELDS`, `PERIO_TOOTH_FIELDS`, `PERIO_BOUNDS`, `PERIO_EXAM_STATUSES`, `PERIO_FURCATION_ENTRANCES`, `PERIO_NOTE_MAX_LENGTH`.

## Invariants

1. **`site` is the whole type discriminator.** `site: null` = per-TOOTH row (`present`, `implant`,
   `mobility`, `boneLoss`, `furcation`, `note`); a `PERIO_SITES` code (`MB B DB ML L DL`) = per-SITE
   row (`pd gm mgj bop sup plaque calculus`). A field from the wrong list is a 422.
2. **Store key is `perioMeasurementKey(tooth, site)` → `` `${n}:${site ?? 'tooth'}` ``**
   (`perioGridModel.js:110`). Never hand-build it; case matters (`3:MB`, not `3:mb`).
3. **`cal` is derived, never stored or sent** — `perioCal(pd, gm) = pd + gm`, `null` unless both
   exist (`chartPerio.js:312`). The CAL cell is read-only and the context refuses writes to it.
4. **`PERIO_BOUNDS` (`chartPerio.js:160`) is the wire authority**; `PERIO_MEASURE_BOUNDS` /
   `PERIO_FIELD_BOUNDS` / `PERIO_GRADE_BOUNDS` in `perioExamDefaultsConstants.js` mirror it. Move a
   bound there first and fix the mirrors in the same change — a tighter mirror silently rewrites
   readings on read-modify-write. Furcation is **0–4** (five grades); `gm` is signed (−20..20).
5. **`draft` is the only writable status.** `canEdit = !locked && exam?.status === 'draft'`
   (`PerioExamContext.jsx:301`); render gating reads `canEdit`, event-time mutations read
   `canEditRef`. `normalizePerioExam` must never default an unknown status to `'draft'`.
6. **Finish flushes first and the flush may refuse** — `handleFinish` awaits `flush()` and stops on
   `{ ok: false }` **before the dialog opens**; a finalized exam accepts no later write.
7. **The Manage menu gates on `dateCreated` being today, not `examDate`** — computed once in
   `wasCreatedToday` (`PerioChartPanel.jsx:184`), passed down as the `createdToday` boolean. Created
   today → Edit/Delete; older → Void; void → Reopen. Delete never appears on a void exam.
8. **Four panel actions must end in `loadExam()`**: edit settings, carry-forward finalize, reopen,
   void. Plain finish is the exception and stays on the context's `finalize()`.
9. **`PerioBopSupAllTeethModal` is Save/Cancel, not write-through** (`PerioBopSupAllTeethModal.jsx:65`):
   one press can change 192 sites, so it snapshots a `baseline`, mutates a `draft` and diffs on Save. Never "simplify" it into per-click writes.
10. **The keypad must not take focus** — every key cancels the blurring mousedown, and every key is
    a whole value (12 mm is one press on the teens page), final by construction.
11. House rules: no `fetch` outside `src/api/client.js`; `const { toast, toastError } = useToast()`;
    no hex literals (theme CSS vars); ISO `YYYY-MM-DD`, no date library.

## Working here

1. **New measurement field** — add to `PERIO_SITE_FIELDS`/`PERIO_TOOTH_FIELDS` + `PERIO_BOUNDS` in
   `src/api/chartPerio.js`; extend `normalizePerioMeasurement`/`toPerioMeasurementBody`; add a row
   in `perioVisibleRows` (`perioGridModel.js:136`), a cell in `PerioSiteInput.jsx`, a label in
   `perioGridLabels.js`, the bound mirror. Backend lands first — see `be-perio`.
2. **New exam setting** — add to `PERIO_EXAM_FIELDS` and, only if the server allows editing it,
   `PERIO_EXAM_EDITABLE_FIELDS`; extend `createPerioExam`/`toPerioExamSettingsBody`; add the control
   to `PerioNavigationFields.jsx` or `NewPerioExamDialog.jsx`; extend `DEFAULT_PERIO_EXAM_OPTIONS`.
3. **State transition** — `chartPerio.js`, then the context action, then the item in
   `PerioExamManageMenu.jsx`, then the refusal sentence in `PerioExamContext.jsx:157-164` (those strings name real menu items by design; removing an item means editing the sentence).
4. **Entry route** — `resolvePasses` (`perioExamDefaultsConstants.js:515`) plus `perioVisitOrder` /
   `perioFieldVisitOrder` in `perioGridModel.js`; grid and keypad both walk it.
5. Verify with `npm run lint` — the only automated check in this repo.

## Traps

- **Stale docblock.** `perioExamDefaultsConstants.js:10` says the Start Perio Exam dialog "DOES NOT
  EXIST YET" — `NewPerioExamDialog.jsx` is that dialog and is wired. Its validators
  `isValidPerioNavigation` (:920) / `isValidPerioExamOptions` (:946) genuinely have no callers.
- **`skipConditions` and `bopSupDelay` are `partial`** — collected, validated, stored, read back and
  consumed by nothing (HONEST GAPs at `perioExamDefaultsConstants.js:781`, `:826`); the route still
  walks every tooth and BOP/Sup stay available at any delay.
- **`PerioScriptEditors.jsx` (51KB) is dead** — its two dialogs have no importer; the Add/Edit/Delete
  cluster was removed from `PerioNavigationFields` (:103). Saved custom scripts still resolve.
- **`gm` ≠ `mgj`** — gingival margin (signed, feeds CAL) vs mucogingival junction (a landmark feeding keratinized-tissue width). Merging them destroys one of the two.
- **Mesial/distal flip** — `isMirroredTooth(n)` is teeth 9–24; screen order is D·B·M unmirrored,
  M·B·D mirrored. Only `perioSiteOrderFor` decides it; never re-derive at a call site.
- **Bulk-save responses ignore their measurement rows on purpose** (`adoptExamEnvelope`,
  `PerioExamContext.jsx:358`), merging the envelope only when `saved.examId` matches the loaded exam
  — otherwise a late response could flip `canEdit` true over a finished record.
- Autosave: 800 ms debounce, 5 s max wait, 4 flush turns (`PerioExamContext.jsx:113-126`); a failed
  flush re-queues **keys, not values**. The panel guards its async load with an `AbortController` +
  exam-id compare, **not** the repo's usual monotonic request-id ref — match the local pattern.
- `perioExamDefaultsConstants.js:21` cites `PMS_React/src/components/settings/tooth-chart-defaults/
  CHART_SETTINGS_API_SPEC.md` §1.1: `/settings/tooth-chart-defaults` configures nothing perio.

## See also

- `main-architecture` — the hub, index and change log.
- `be-perio` — `360_Flask_Appointment/app/chart_perio_routes.py`, the server side of every route above.
- `fe-charting` — the odontogram, chart sessions and the `isReadOnly` lock this panel obeys.
  `fe-patient-chart` — the `/patients/:patientId/*` shell the Charting tab lives in.
- `references/perio-model.md` — grid model, indexing, navigation passes, keyboard flow, statuses.
