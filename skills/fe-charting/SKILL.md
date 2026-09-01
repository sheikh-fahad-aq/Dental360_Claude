---

name: fe-charting

description: Frontend odontogram / tooth chart — findings, chart sessions (lock/unlock/resume/sign), and the charted-treatment listing (Recommended Treatment / Clinical History / Treatment Plans tabs). Use when editing PMS_React/src/components/patient-detail/charting/ (Odontogram.jsx, ToothChartContext.jsx, ChartingContext.jsx, treatment-listing/*) or src/api/charting.js, hitting /v2/charts endpoints, or debugging chart_owned_session_<patientId>, entryType vs procedureStatus. NOT perio — see fe-perio.

---



## Scope



The Charting tab (`/patients/:patientId/charting`) minus perio: the 32-tooth Universal/ADA odontogram, per-tooth status /

surfaces / findings, the VISIT the work is filed against (picker, panel, worklist, notes), layers/filters, and the Charting

Assistant note panel, and the **treatment listing** below the chart (Recommended Treatment / Clinical History / Treatment

Plans). README labels the section **live**. Boundary: `charting/perio/` **and** `charting/PerioChartPanel.jsx` (84 KB) are

**fe-perio** despite sitting here; `patient-detail/tx-plans/` (plan builder, `txPlanFormat.js`, `txPlanUi.jsx`) is

**fe-patient-chart** — the listing imports from it, does not own it; Tooth Chart Defaults are edited in `fe-settings`.



## Files



Paths under `PMS_React/`; `…/` = `src/components/patient-detail/charting/`, `…/tl/` = `+treatment-listing/`. 39 code files + 2 spec docs at the root, plus `treatment-listing/` (12) and `perio/`; `PerioChartPanel.jsx` and `perio/` are **fe-perio**.



| Path | Role |

|---|---|

| `…/ChartingSection.jsx` | **(entry)** sub-tabs + active panel + SelectVisitModal + VisitPanel; mounted by `src/pages/PatientDetail.jsx:308` |

| `…/ChartingContext.jsx` (31 KB) | session/lock state machine, provider pick, procedures load, saveDraft/signNote. Provider at `pages/PatientDetail.jsx:585` |

| `…/ChartingHeaderControls.jsx` | Locked↔Active header — rendered by `patient-detail/PatientSectionHeader.jsx:97`, not by ChartingSection |

| `…/ToothChartPanel.jsx` · `ToothChartContext.jsx` (47 KB) | the panel (chart + listing + plan-builder host); per-tooth records, selection, all chart mutations |

| `…/Odontogram.jsx` · `ToothGraphic.jsx` (45 KB) · `ToothNumberStrip.jsx` · `toothBuccalSvgs.js` | arch layout, per-tooth SVG + finding overlays, number rail, `import.meta.glob` of the tooth SVGs |

| `…/AddChartingPopover.jsx` (26 KB) · `ToothDetailSidebar.jsx` · `SurfaceContextMenu.jsx` · `ProcedureStatusMenu.jsx` | charting entry UI + status-transition menu |

| `…/tl/TreatmentListingPanel.jsx` (21 KB) | **the listing** — three tabs; owns the plan-list + item-index reads, filters, paging, search, CSV, bulk select |

| `…/tl/RecommendedTreatmentTable.jsx` · `ClinicalHistoryTable.jsx` · `TreatmentPlansTable.jsx` · `treatmentListingFilters.js` · `treatmentListingCsv.js` · `procedureJourney.js` | the three tab bodies (history read-only by design; plans table renders `plan.statusLabel`), `LISTING_TABS`/`applyFilters`, CSV columns + formula-injection guard, "Patient journey" wording |

| `…/tl/ChartEntryDetailPanel.jsx` (26 KB) · `ProcedureDetailsModal.jsx` (26 KB) · `TreatmentBulkActionBar.jsx` · `AddToTreatmentPlanModal.jsx` · `TreatmentListingMenu.jsx` | row slide-over, editable detail modal, portal bulk bar, add-to-draft-plan modal, "⋯" tab menu |

| `…/visit/ChartingVisitRail.jsx` · `VisitPanel.jsx` · `VisitPanelFooter.jsx` · `VisitPlanActions.jsx` | **the right-hand rail** — mounted by `pages/PatientDetail.jsx`, NOT by ChartingSection, so it spans the page height; collapses to a 44px strip. The footer's Check out **leaves this page**: it closes the charting session, navigates to /scheduling (with the visit's `?date=`) and opens the appointment popup there. The rail mounts NO check-out UI |

| `…/visit/SelectVisitModal.jsx` · `MoveToVisitModal.jsx` · `VisitPicker.jsx` | the two visit dialogs — start/change charting, and re-file one procedure. **`VisitPicker` is the shared list**; never copy it into a third dialog. SelectVisitModal preselects `pendingVisit ?? selectedVisit` — see the deep-link trap |

| `…/visit/VisitWorklistTab.jsx` · `VisitNotesTab.jsx` · `VisitInfoTab.jsx` · `useVisitList.js` · `useVisitNotes.js` · `useVisitPlannedTreatment.js` · `visitFormat.js` | the visit's worklist / notes / info, and the appointment, note and planned-treatment fetchers |

| `…/ChartStatusFilters.jsx` · `LayersDropdown.jsx` · `ChartLegend.jsx` · `ChartMaximizeModal.jsx` · `ChartingSubTabs.jsx` | filters/layers/legend/maximize/sub-tab chrome. **`ChartingAssistant.jsx`, `UnlockChartModal.jsx` and `SignNoteDialog.jsx` are DELETED** — the note moved into the Visit panel, and there is no unlock or sign-off step left |

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



1. **`isReadOnly` is the only editing gate** — `status !== 'active'`. It gates the tooth chart AND the perio chart from one flag, so starting charting unlocks both. `CHART_STATUS` has exactly two members now: `locked` (nobody has started charting on this screen) and `active`.

2. **THERE IS NO "IN USE" STATE.** Another user or tab holding a session does NOT make this chart read-only — that state was removed deliberately. Whoever starts charting gets their OWN session (the server keys one per provider per visit), so two clinicians can work one chart and each one's entries are attributed to them. Never reintroduce a lock keyed on someone else's session.

3. **Ownership lives in `sessionStorage`, never `localStorage`** (CLAUDE.md §7.5), and it is no longer a lock — it answers only "is this session mine to resume after a reload?". Always go through `chartOwnership.js`. **Resume must match the PROVIDER as well as the visit**: `create_chart_procedure` stamps rows with the *session's* provider, so resuming someone else's session files your work under their name.

4. **`entryType` ≠ `procedureStatus`.** `entryType` = `TP|Cn|EC|EO` (kind of entry); `procedureStatus` = `P|C|D|R`. Never map one onto the other. **No status is terminal**: the server accepts any `P|C|D|R` transition and audits each one, and the visit worklist offers every status on every row — a mis-click has to be correctable, and a row charted at an earlier visit still has to be markable done at this one. `updateChartProcedureStatus` takes an optional `sessionId` naming the session doing the changing; without it the server falls back to the row's ORIGINAL session and refuses once that one has closed, so always pass the open session. The odontogram's own one-way affordance (`allowedNextStatuses`) is a UI choice there, not a rule.

5. **A multi-code is never charted as itself** — that writes one $0 ledger line for work nobody performed. A click charts its

   `members` through `addProcedures`, in one batch. Identify a bundle by `item_type === 'multi'`, never by category. There is

   no multi-codes request in the charting path: `GET /v2/procedure-codes` already returns them (references §1).

6. **The listing never fetches chart rows.** `ChartingContext` is the single fetcher and refetches after every chart write; the panel takes them as the `rows` prop (`ToothChartPanel.jsx:158-165`). A second copy goes stale on the next tooth charted.

7. **Plan membership is ENRICHMENT, never a gate.** Chart rows must render when the plan service is down: set `planApiAvailable=false` and *drop* the chips rather than badging every row "Not in Treatment Plan".

   `null` ≠ `undefined` here — `procedureJourney.js:32` reads `null` as "unavailable", `undefined` as "on no plan".

8. **Plan status is read, never re-derived.** `TreatmentPlansTable` renders `plan.statusLabel` with `planStatusToneId(plan.status)`

   (`tx-plans/txPlanFormat.js:58`), so a server-derived status such as `scheduled` needs no change here. Do not add a local status map.

9. **A worklist row is COPIED onto a visit, never moved** — `/chartprocedure/attach` writes a new row carrying

   `sourceProcedureId`, because the recommendation stays in Recommended Treatment until the work is completed. **A

   status change is mirrored across every row sharing that link** (`_linked_procedures`, both directions:

   copy→source and source→copy, skipping soft-deleted rows) — otherwise the same treatment reads as done in

   one place and still owed in the other, and which place depended on where the clinician clicked. That

   provenance is the ONLY thing that stops one recommendation landing on a visit twice: two identical procedures on a

   tooth are legitimate, so the check cannot key on code and site. `/move` is the one call that accepts an

   `appointmentId` from a client; `/entered-in-error` soft-deletes with its own audit action (not a delete — the

   distinction is the record).

10. **`/chartprocedure/attach` IS IDEMPOTENT, so "200" does not mean "added".** It answers with
    the existing row when a copy is already on this visit, or when the source IS the visit's
    row. That is the common case, not the edge one: a recommendation stays listed under
    Recommended Treatment after it has been charted, so the row inviting the click is often
    already there. Compare the returned ids against `visitProcedures` before claiming
    anything was added — a false receipt sends the operator hunting for a line that was
    never going to appear. With NO visit open, `AddToVisitModal` asks for one and
    `beginCharting` opens it; that call RETURNS the session, because reading it back off
    context state would be the previous render's value.

11. **PLANNED and PERFORMED dates are separate facts.** `chartDate` is the planned date of
    service and keeps that meaning for the life of the row; `completedDate` is null until the
    procedure is completed and is cleared again on a revert — a row that is no longer
    complete has no date of service, and a claim bills on one. Never overload `chartDate`
    on completion: it would erase what was proposed.

12. **Completing asks; every other status is one click.** `CompleteProcedureModal` collects
    the office fee, the rendering provider and the performed date, and they go out WITH the
    status in one request (`updateChartProcedureStatus` takes them) — a details PATCH then a
    status POST writes two audit rows for one event and leaves a window where the row reads
    completed but unpriced, which is the state the ledger reads. **$0.00 is accepted and
    blank is refused**: `ucr_fee_cents` is NOT NULL DEFAULT 0, so a deliberate no-charge and
    an unpriced row are otherwise the same record. Fee/date/provider helpers live in
    `procedureFields.js` and are shared with `ProcedureDetailsModal` — never fork them.

13. **The listing shows ONE ROW PER INTENTION, deduped WITHIN A TAB.** `/attach` copies, so
    a proposal can be two `chart_procedures` rows (`sourceProcedureId`); both satisfy
    `isRecommendedRow`, so Recommended listed the same treatment twice. Status was hiding
    it — the duplicate only appears once a Completed copy is reverted to Planned. Dedupe
    **per tab**, never before the split: collapsing the pair globally empties Clinical
    History whenever the two have diverged (a completed copy against a still-planned
    source — exactly what a backend without status mirroring produces), which drops the
    record of work that was done. The original wins; an orphaned copy still shows.

14. **A booked plan line is CHARTED from the worklist, never faked.** `PlanStatusSelect` offers a status on a row

    that has no chart procedure behind it; picking one attaches (when the line carries a `chartProcedureId`) or

    creates a `TP` row on the open session FIRST, then sets the status. Never write a status onto something that

    is not a chart row — the create path is what stamps the session, provider and audit entry. The line then

    drops out of "Planned for this visit": `outstandingPlanned` matches on `sourceProcedureId` as well as `id`,

    and falls back to `code|toothNumber` for a line that had no chart row to attach.



15. **A visit session ends by a PERSON — Exit visit, or Check out.** The server's idle sweep skips any session

    with an `appointment_id` (`chart_session_scheduler.py`), because ten quiet minutes is what a radiograph or

    a conversation looks like from the server, and closing one left every later write answering 409

    mid-appointment. `useExitOnCheckOut` in `ChartingVisitRail.jsx` is the other half: it listens for

    `visitCompleted` from SchedulingContext (the wizard's SUCCESS path, not `closeVisitWizard`, which also

    fires on Cancel) so an abandoned visit is not left open forever. Charting with no visit still sweeps.



16. **Every chart write goes through `withLiveSession`.** A session can still be closed under you — another

    tab's Exit visit, a signed session — and the heartbeat only notices on its own tick, so a bare call could

    be refused with nowhere to go. It reopens the same visit once and retries. The refusal is recognised by

    `isSessionClosedError`, which matches the SIX wordings the API has used across routes and deploys and

    deliberately not 409 alone — a duplicate session, a non-draft plan and a bad status value are all 409 and

    must not be retried. Add a wording there, never a bare `err.status === 409` at a call site.



17. **Charting a booked plan line must also complete the PLAN item.** `chart_procedures` and

    `treatment_plan_items` are separate records: marking the procedure completed leaves the plan line

    `scheduleStatus: 'scheduled'` forever, so it stays badged "Scheduled" and the plan's

    completed/outstanding counts are wrong. `completeAppointmentPlannedTreatment` is the audited path (it

    also completes the linked appointment procedure) — call it, do not reproduce it.



18. **Only a DRAFT plan can be added to** (`AddToTreatmentPlanModal.jsx:5`) — the server answers 409 for anything else.

19. **Signer identity is server-side** (CLAUDE.md §7.7); `providerId`/`providerName` in the sign payload are convenience only.

20. **Never render `autoSaveDraft` or any server HTML as markup** (CLAUDE.md §7.4) — carry it as an opaque string. `ToothGraphic.jsx:961`

    is the only **live** `dangerouslySetInnerHTML` here and it paints bundled local SVG, never network data (`ToothBuccalGraphic.jsx:39` is dead).

21. **Never log a chart payload, URL or patient id** (CLAUDE.md §7.1) — all PHI. Catch blocks re-throw via

    `toChartSessionError`; surface text with `getErrorMessage(err, fallback)`.

22. **Dual-mode by env-var presence** (CLAUDE.md §5): `isChartApiEnabled()` is only "is `VITE_APP_BASE_URL_CHART` non-empty".

    Every new API function needs an `if (!isChartApiEnabled())` branch and a `normalizeX(raw)` mapper.

23. **`fetch()` never appears here.** `chartApi` always emits the same-origin `/__chart_api/api` prefix (the host refuses

    browser CORS); that proxy lives in **three** blocks — `server.proxy` + `preview.proxy` in `vite.config.js`, `rewrites` in

    `vercel.json` — which change together.

24. **Chart data loads once, in ChartingContext**: procedures, then `/active`, then the session list

    (`ChartingContext.jsx:199-241`). Do not add a second fetch in ToothChartProvider.

25. **No hardcoded hexes in components** (`chartVisuals.js` / `chartFindingGraphics.js` hexes are SVG paint — leave them);

    overlays are `createPortal` + `AnimatePresence` + `OverlayBackdrop` with a named `OVERLAY_Z_INDEX` key

    (`ChartMaximizeModal.jsx:36`, `visit/SelectVisitModal.jsx`), never `z-[n]`; feedback is `useToast()`, never `alert`.

26. **Tooth numbers are integers 1-32**; primary/mixed is unsupported and fails loudly (Traps). ISO `YYYY-MM-DD` on the wire.



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

- **Check out LEAVES the chart, and closes the charting session on its way out.**
  `VisitPanelFooter.handleCheckOut` awaits `exitCharting()`, navigates to
  `${ROUTES.scheduling}?date=<visit date>` and calls `openAppointmentDetail(appointmentId)`. The
  schedule is where a visit is finished; the drawer's own Check Out then moves the tracker to
  `checkout` and opens the wizard, which the rail's button never did — chart-side checkouts used
  to leave the visit board showing the patient still in the chair.
  - **The session close cannot move back to a listener on this page.** An appointment-linked
    session is exempt from the server's idle sweep and ends only because a person ended it
    (invariant 15). A `useExitOnCheckOut` hook used to sit in `ChartingVisitRail` and wait for the
    wizard's success — but the page it lived on is exactly what Check out now leaves, so it could
    never fire again. It is gone; the button is the closer. The draft note travels with
    `closeChartSession`, so nothing typed is lost, and coming back re-opens the visit through the
    picker.
  - **THE WHOLE REQUEST TRAVELS IN THE URL** — `/scheduling?date=&appointmentId=&checkout=1`.
    It began as in-memory context state set just before navigating, which only worked if the SPA
    navigation did, and the handler was reported three separate times as closing charting and
    going nowhere. A destination fully described by its URL survives every navigation mechanism,
    is reachable by hand, and is what makes the fallback below possible. `SchedulingQueryParams`
    consumes and strips all four.
  - **`navigate` GOES FIRST, and a hard fallback follows.** Closing the session is the
    destructive half; nothing is ordered in front of the route change, `exitCharting()` is fired
    last (unawaited, wrapped), and then — because `history.pushState` moves `window.location`
    SYNCHRONOUSLY — a one-line check falls back to `window.location.assign(target)` if the
    pathname did not move at all. It is a no-op on every healthy path. Deliberately not a
    timeout: a slow lazy chunk is a slow render, not a stalled history entry.
  - On arrival the drawer does the rest: `requestCheckOut` sets an intent on SchedulingContext,
    `AppointmentDetailDrawer` picks it up once it has actually READ the appointment, clears it,
    then moves the tracker to `checkout` and opens the wizard on Review charges. That logic stays
    in the drawer, which has the appointment. A visit that cannot be checked out leaves the drawer
    open showing why rather than forcing a wizard the server would refuse.
  - The rail mounts no check-out UI at all now. If any is ever mounted there again, it belongs
    OUTSIDE the `!visitPanelOpen` early return: inside it, collapsing the visit panel mid-checkout
    unmounted the wizard and threw the operator out of it. Bring the completion listener back with
    it.

- **`ChartingProvider` takes `initialVisitId` — deep-linking from Scheduling PRE-SELECTS a visit,
  it never opens one.** Scheduling's Open Chart (`AppointmentDetailDrawer` + `VisitStatusBoard`)
  puts `chartVisitId` in navigation state; `pages/PatientDetail.jsx` captures it **once, on the
  first render**, because its own seed effect wipes `state` to `{}` a beat later — and because a
  reload should forget it. The context resolves the appointment into **`pendingVisit`** and opens
  the picker on it. Four rules hold this together:
  - **`pendingVisit` is NOT `selectedVisit`.** The latter mirrors the open session and is cleared
    whenever there is none — including on every re-run of the mirror effect, which re-runs when
    `providers` load. A pre-selection parked there is wiped a beat later, by design. Two facts,
    two states; `SelectVisitModal` preselects `pendingVisit ?? selectedVisit`.
  - **It stops at pre-selecting.** Confirming creates a session, and `create_chart_procedure`
    stamps every row with that session's provider; the signed-in clinician is not resolvable to a
    provider row at all, so auto-starting would file clinical work under a name nobody read.
  - **It also preselects the VISIT'S provider** — a tier between the practice default and a real
    choice, and necessary rather than cosmetic: `VisitPicker` filters its list by
    `selectedProviderId` and would hide the very visit it was told to preselect, and
    `beginCharting` files under `selectedProviderId`, not under the visit's provider. It yields to
    an open session and to a manual pick (told apart from the auto-applied default by
    `defaultProviderAppliedForRef`).
  - **It waits for BOTH `sessionLoading` and `providersLoading` to settle, then runs once per id.**
    That ref is what stops a second picker opening over the clinician's work.
- **`resolveVisit` fetches and normalises; `loadVisit` is that plus `setSelectedVisit`.** Use the
  first to look at a visit you are only offering. Both go through `toAppointmentDetail` — storing
  the raw payload puts `provider: { id, name }` on the record and the visit header renders it as a
  React child, taking the page down on reload.



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

  keeping the bundled id so existing notes are not orphaned. `ScreeningsPanel.jsx` is a

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

