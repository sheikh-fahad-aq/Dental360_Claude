---
name: fe-scheduling
description: Frontend scheduling — the /scheduling Day/Week calendar, SchedulingContext, appointment create/reschedule/drag-resize, detail drawer, check-in/check-out visit wizard, visit status board and tracker stages, exit-workflow gate, find open slots, block time, route slip, day-schedule print. Use when editing PMS_React/src/pages/Scheduling.jsx, src/components/scheduling/*, src/context/SchedulingContext.jsx, src/api/appointments.js, useAppointmentDrag or utils/visitStatusTracker.js.
---

## Scope

`/scheduling` — the largest **live** module in `PMS_React`: a fixed 24-hour canvas, one column
per operatory, plus every overlay hanging off an appointment card. Owns the calendar, the
appointment lifecycle UI, the visit tracker, and `src/api/waitlist.js` (only `SchedulingQueueDrawer` and `AppointmentDetailDrawer` import it). **Not owned:** the chart's own Appts/Schedule sections (fe-patient-chart), `src/components/settings/scheduling/` (fe-settings), Revenue Reports (fe-reports-worklists) — though `DailyHuddleView.jsx` **is** owned here despite being imported only by `src/pages/RevenueReports.jsx`. Maturity
(`PMS_React/README.md:209-231`): calendar, CRUD, drag/resize, drawer, status tracker,
check-in, find-open-slots, block time, route slip and print are **live**; the check-out payment
step, the seed fallback and Month/Year views are **placeholder/mock**.

## Files

Under `PMS_React/`. Sizes noted where they matter — `grep -nE "^export |^function "` + `sed -n`
those, never read them whole.

| path | role |
|---|---|
| `src/pages/Scheduling.jsx` | **(entry)** 85 lines. Sidebar + header + grid + `VisitStatusBoard`, then 8 portaled overlays mounted for route lifecycle only. `SchedulingQueryParams` consumes `?patientId=&date=&appointmentId=` then strips them. |
| `src/context/SchedulingContext.jsx` | **69 KB / 2050 lines.** All state. Line map in `references/state-and-api.md` §1 — do not read whole. |
| `src/api/appointments.js` | **63 KB / 1981 lines.** Every `/v2/appointments/*` call + the card/detail mappers. Routes in `references/` §2. |
| `src/api/{scheduleBlocks,scheduleGroups,rooms,providers,services,multiCodes,lookups,appointmentLookups}.js` | Master data via **`authApi`**, not `appointmentApi`. Routes in `references/` §3. |
| `src/components/scheduling/CalendarGrid.jsx` (60 KB) · `WeekCalendarGrid` · `CalendarHeader` · `ViewDropdown` · `ScheduleActionsMenu` · `SchedulingSidebar` · `PasteSlotGhost` · `AppointmentHoverCard` | The calendar surface. `CalendarGrid` is the Day grid and the only one with drag/resize. |
| `AppointmentDetailDrawer.jsx` (**119 KB — largest file in `src/`**) · `RescheduleAppointmentModal` · `VisitStatusTracker` · `AppointmentVisitWizard.jsx` (**104 KB**) · `CheckInFormsStep` | Card → drawer; check-in / check-out wizards. |
| `VisitStatusBoard.jsx` (**115 KB**) · `SchedulePeek` · `ExitWorkflowChecklist` · `ExitWorkflowIncompleteModal` | Six-stage board, day timeline, exit gate UI. |
| `NewAppointmentModal.jsx` (45 KB) · `AppointmentProcedureSearch` · `AppointmentMultiCodeSelect` · `SelectedProceduresWithQuantity` · `FindOpenSlotsDrawer.jsx` (**78 KB / 1729 lines** — `grep`/`sed -n`) + `find-open-slots/{DateRangePopover,MultiCheckboxSelect}.jsx` + `SendAppointmentNotificationModal.jsx` (456) + `appointmentNotificationTemplate.js` (71) | Create flow, availability search, and the plan-context confirm step. |
| `SchedulingQueueDrawer.jsx` (49 KB) · `BlockTimeModal.jsx` (32 KB) · `AppointmentSearchDrawer` · `AppointmentStatusesModal` · `RouteSlipHost` + `RouteSlipModal` · `DaySchedulePrintDocument` · `OperatoryUtilizationPanel` · `DailyHuddleView` | Secondary surfaces. `RouteSlipHost` mounts in `src/App.jsx`, not `Scheduling.jsx`. |
| `src/hooks/{useAppointmentDrag,useCreateAppointment,useExitWorkflowCompleteGate,useExitWorkflowRecareMap}.js` · `src/utils/appointment{Clipboard,Display,Move,Queries,Time,Waitlist}.js` · `visitStatusTracker.js` (26 KB) · `weekRange.js` · `src/config/{appointmentConfirmationStatuses,exitWorkflowSettings,exitWorkflowTasks}.js` | Logic layer. Tracker/exit-workflow model detailed in `references/` §4. |
| `src/utils/{findOpenSlotsDrawerStore,schedulingQueueDrawerStore}.js` | `useSyncExternalStore` singletons, deliberately outside the context so open/minimize does not re-render the calendar. |
| `src/data/scheduling.js` | Grid geometry (`HOUR_HEIGHT = 96`, 4 sub-slots/hour) **plus** the `PROVIDERS` and `APPOINTMENTS` mock seeds. 28 files import it. |

Touches (shared, not owned): `src/config/routes.js`, `src/components/AppRoutes.jsx:27,190`,
`src/App.jsx`, the `{Auth,Location,Patients,Providers,Rooms,Toast}` contexts,
`src/components/ui/OverlayBackdrop.jsx`, `src/api/client.js`.

## Contract

Renders at `ROUTES.scheduling` — lazy route at `AppRoutes.jsx:190` inside `<ProtectedRoute>`.
Deep link `?patientId=&date=&appointmentId=` is consumed once, then removed via
`setSearchParams(..., { replace: true })`. Calls `api/appointments` through `appointmentApi`
(always the same-origin `/__appointment_api/api` proxy); rooms, providers, services,
scheduleBlocks, scheduleGroups, multiCodes, lookups and waitlist go via `authApi`. Calendar data =
`GET /v2/appointments/calendar`; availability = `POST /v2/appointments/availability`
(`FindOpenSlotsDrawer` is its only caller); full tables in `references/` §2–§3. Everything
children consume comes from `useScheduling()` — the memo at `SchedulingContext.jsx:1796`.

## Invariants

1. **No `fetch`, ever.** Import from `src/api/`; zero direct `fetch` exists outside
   `src/api/client.js` — keep it at zero.
2. **`appointmentApi` paths stay relative** — that host refuses browser CORS. A new proxied
   prefix must be added to **both** `vite.config.js` and `vercel.json`.
3. **Mutate appointments only through the context** — `createAppointment`, `patchAppointment`,
   `moveAppointment`, `resizeAppointment`, `cancelAppointment`, `removeAppointment`,
   `setVisitStage`, `advanceVisitStage`. Never `setState` a card position in a component.
4. **Map at the edge** — `toScheduleAppointment` / `toAppointmentDetail`, and keep
   `preserveSchedulePlacement(mapped, existing)` on any detail merge or cards jump to Unassigned.
5. **Guard every async load with a monotonic request-id ref** and bail when stale, as the seven
   `*RequestIdRef`s in the context already do.
6. **`HH:mm` times, ISO `YYYY-MM-DD` dates, no date library** — use `appointmentTime.js` and
   `weekRange.js`; for "now" call `getSchedulingReferenceNow()`, never bare `new Date()`.
7. **Overlays:** `createPortal(..., document.body)` + `<AnimatePresence>` + `<OverlayBackdrop
   zIndex={OVERLAY_Z_INDEX.…}>` — all 10 overlay files here; Tailwind cannot scan `z-[n]`.
8. **`const { toast } = useToast()`** — zero `alert()` calls exist here. Errors via
   `getErrorMessage(err, fallback)`.
9. **No hex literals** — `src/theme/theme.css` vars, or the stage/provider color objects in
   `visitStatusTracker.js` / `data/scheduling.js`.
10. **Reference `ROUTES`, never the string `'/scheduling'`.**

## Working here

1. Read `PMS_React/README.md:209` and `references/state-and-api.md` before touching state.
2. New field on a calendar card: extend `toScheduleAppointment` (`api/appointments.js:287`)
   **and** `toAppointmentDetail` (`:490`) — the drawer re-fetches detail and would drop it.
3. New API call: add it to `src/api/appointments.js` with a mapper, add a loader in
   `SchedulingContext.jsx`, then expose it in the `value` memo at `:1796` (the usual bug).
4. New overlay: build under `src/components/scheduling/`, mount it in `Scheduling.jsx` (or
   `App.jsx` if it must outlive the route, like `RouteSlipHost`), and add open/close state to the
   context — or an external store if it must not re-render the grid.
5. Grid geometry changes go in `src/data/scheduling.js` only (`SUB_SLOT_HEIGHT` is derived);
   print and peek surfaces keep their own scales on purpose.
6. Verify with `npm run lint` (the only automated check — no tests exist) and by loading
   `/scheduling` under `npm run dev`.

## Traps

- **XSS, unfixed (CLAUDE.md §7.4 violation).** `VisitStatusBoard.jsx:1127` renders
  `previewForm.html_content` via `dangerouslySetInnerHTML` with **no sanitizer**; the string comes
  straight off `GET /v2/appointments/{id}/forms` (`listAppointmentForms`, at `:834,932,970`). No
  sanitizer exists in the repo and `vercel.json` has no CSP. Never copy this pattern.
- **Ungated `console.warn` in production** — `SchedulingContext.jsx:375` and
  `AppointmentVisitWizard.jsx:976` print server error text. Gate logging on `import.meta.env.DEV`.
- **Silent mock fallback.** With `VITE_APP_BASE_URL_APPOINTMENT` empty the context loads the
  `APPOINTMENTS` seed (`SchedulingContext.jsx:143,1443`) with **no banner and no `source` flag**,
  unlike the `use*` hooks — a full-looking calendar may be entirely fake.
- **`VITE_SCHEDULING_REFERENCE_NOW`** (`utils/appointmentQueries.js:38`) overrides "now" for all
  past/future logic and is **absent from `.env.example`**. `SCHEDULING_REFERENCE_NOW:47` is a
  deprecated frozen 2026-07-01 constant — call `getSchedulingReferenceNow()` instead.
- **Month and Year are dead options.** `VIEW_OPTIONS` lists them, but `Scheduling.jsx` only
  branches on `isWeekView`, so choosing either silently renders the Day grid. Printing is
  separately gated to Day at `CalendarHeader.jsx:220`.
- **Drag is DOM-coupled and Day-only.** `resolveDropTarget` (`utils/appointmentMove.js:48`) uses
  `elementFromPoint` + `closest('[data-operatory-column]')`, emitted at `CalendarGrid.jsx:790`;
  renaming it breaks drag with no error. `useAppointmentDrag` is imported by `CalendarGrid` only.
- **Check-out payment is a placeholder** — `AppointmentVisitWizard.jsx:601`
  `StripePaymentPlaceholder`, `:1800` `handlePlaceholderCharge` (600 ms `setTimeout` + toast, no
  charge). Check-in insurance falls back to `mapMockPatientInsuranceToView` (`:937,943`).
- **`useCreateAppointment` is not used by this page** — `NewAppointmentModal.jsx:655` calls the
  context's `createAppointment`; the hook serves only
  `patient-detail/appts/AddAppointmentDrawer.jsx`. Two create paths — change both.
- **`FindOpenSlotsDrawer` is ONE component with TWO behaviours, switched on
  `isPlanContext = Boolean(planSeed?.planId)`.** Opened from `CalendarHeader.jsx:209`
  (`findOpenSlotsDrawerStore.open()`, no seed) it is the front-desk slot finder it has always
  been: flat slot list, every filter, and a click on a time **books immediately**. Opened from
  `patient-detail/tx-plans/builder/TreatmentPlanBuilder.jsx:741` (`open({ planId, … })`) it
  switches to a weekday strip, a two-step confirm flow, and a hidden **Service** selector.
  Provider stays visible in both — a plan names who drew the work up, not who delivers it.
  Anything new here must be gated the same way, or /scheduling silently changes behaviour.
- **In plan context a click on a slot does NOT book.** `handleSlotChosen` sets `pendingSlot` and
  the confirm step renders in place of the search; only the footer's "Book this appointment"
  calls `handleBookSlot`. The slot row shows a `ChevronRight` rather than a `Check` for exactly
  that reason. On a 409 the confirm step is dropped before the re-search, or the operator retries
  the slot that just failed.
- **Never build a slot key by hand.** `slotKey(slot)` is the shared identity across the list, the
  in-flight spinner and the confirm step; three hand-written copies of the same template literal
  is how the spinner lands on the wrong row.
- **Day tabs are built from the ISO Y-M-D parts, never `new Date(iso)`.** A bare ISO date string
  parses as UTC, so west of Greenwich `new Date('2026-09-07')` is Sunday the 6th and the tab names
  a different weekday than the slots under it. `slotDayLabels` and `formatSlotDate` both do it the
  safe way — copy them.
- **The notify composer suspends the drawer's outside-click close.** It is portaled to
  `document.body`, so every click inside it is an outside click as far as the drawer is concerned
  and would close it mid-compose; the Escape/pointerdown effect is keyed on `[visible, notifyOpen]`
  for that reason. Any future portaled child of this drawer needs the same treatment.
- **`POST /v2/appointments/notify` sends a PROPOSAL, before the booking exists** — it takes the
  slot, not an appointment id (`notifyProposedAppointment`, `api/appointments.js:912`). It is
  never a gate: Book stays enabled whether or not the patient was notified, because a patient with
  no email on file still has to be bookable. `notifiedKey` stores WHICH slot was notified, not a
  boolean — a boolean survives the operator going back and picking a different time. SMS is
  refused server-side with a reason; the modal's SMS primary is permanently disabled to match.
- **The notify composer's Email body is the SHARED `ui/EmailTemplateEditor`**, the same TipTap
  editor `SendTreatmentPlanModal` uses — it moved out of `tx-plans/builder/` for this. Its banner,
  button label and variable list are props: this caller passes
  `appointmentNotificationTemplate.js`'s constants and **no `buttonLabel`**, because a proposed
  time carries no link and a previewed button the sent mail does not have would misdescribe it.
  Only the BODY travels; the banner, the details table, the procedure list and the closing
  "not confirmed until our office books it" are rendered by the server from the payload, so an
  operator who rewrites the template cannot drop the caveat. The SMS tab keeps a flat, read-only
  chip template — a text message has no markup and there is no editor there whose `[Bracketed]`
  tokens could be half-deleted into something the server will not substitute.
- **Open Chart carries the VISIT, in navigation state.** Both entry points —
  `AppointmentDetailDrawer.handleOpenChart` and `VisitStatusBoard.handleOpenChart` — send
  `{ chartVisitId: appt.id }` alongside the optional `seedPatient`, and the charting page opens its
  visit picker pre-selected on it (`fe-charting`). Change the two together: a board that lands the
  clinician on a blank chart while the drawer pre-selects reads as a bug in whichever one they used
  second. It rides in state, not the URL — an appointment id in a query string lands in access logs
  and Referer headers (§7.1) — and the drawer sends it **outside** the `patient ?` branch, so a
  chart reached with no patient record loaded still knows which visit it was opened for.
- **The chart's Visit rail checks out by COMING HERE.** `VisitPanelFooter.handleCheckOut`
  (fe-charting) closes the charting session, navigates to `${ROUTES.scheduling}?date=<visit date>`
  and calls `openAppointmentDetail(appointmentId)` — `Scheduling.jsx` is still the only mount of
  `AppointmentDetailDrawer` and `AppointmentVisitWizard`. Both were briefly mounted in the rail as
  well; they are not any more, so neither may be assumed to exist off this page.
- **`SchedulingQueryParams` accepts `?checkout=1` alongside `date`/`appointmentId`.** That is how
  the chart's Visit rail hands a check-out over — in the URL, not in context state, so the request
  survives an SPA navigation, a hard one, or a reload of the link. It runs AFTER
  `focusAppointment` so a plain selection cannot overwrite the intent, and it selects the
  appointment itself, so a link with no date still opens the drawer. All four params are stripped.
- **`AppointmentDetailDrawer` portals into a container IT OWNS**, appended and removed by its own
  effect, not straight into `document.body`. Unmounting the owner while an `AnimatePresence` exit
  is still running can leave the backdrop behind — `fixed inset-0 z-60` at `opacity: 0` and still
  `pointer-events: auto`, blanketing whatever page comes next. Owning the node makes the cleanup
  unconditional. It has **three** mount sites: `pages/Scheduling.jsx`, `patient-detail/appts/ApptsSection.jsx`
  and `patient-detail/schedule/ScheduleSection.jsx`.
- **`requestCheckOut(appointmentId)` is an INTENT the drawer consumes, not a command.** The
  chart's Visit rail sets it, navigates here, and `AppointmentDetailDrawer` picks it up once its
  appointment has loaded — starting a check-out means moving the tracker AND opening the wizard,
  and neither can act on an appointment nobody has read. The drawer clears it before deciding, so
  a refetch cannot start a second check-out; a visit that cannot be checked out (never checked in,
  already completed, API off) leaves the drawer open showing why rather than forcing a wizard the
  server would refuse.
- **`post_op_receipt` is a DONE-marker, not check-out step 3.** The server writes it on completion
  (`appointment_checkout_routes.py`); `normalizeCheckOutStep` maps it to `review_charges`, and
  `start_check_out` only preserves a step when the visit was already `in_progress`. Mapping it to
  `schedule` — and carrying it forward on the server — re-opened a finished check-out on its last
  screen, two steps past the charges the operator had come back to review. Resuming means resuming
  something still in progress.
- **Two legacy endpoint fallbacks** in `api/appointments.js` are intentional — `references/` §2.
- **Editing `src/context/` forces a full page reload** (`fullReloadOnContextHmr()`, `vite.config.js`).
- `PROJECT_GUIDE.md` is stale and misleading; `PMS_React/README.md` is the source of truth.

## See also

- `references/state-and-api.md` — context line map, route tables, tracker/exit-workflow model.
- `main-architecture` — hub, index and change log.
- Backend siblings: `be-appointments` (calendar, CRUD, availability), `be-visit-lifecycle` (check-in/check-out, tracking-status, the appointment-forms proxy behind `VisitStatusBoard`), `be-recare-waitlist` (Scheduling Queue drawer, ASAP).
- Frontend siblings: `fe-patient-chart` (the chart's own Appts/Schedule tabs), `fe-forms` (the `/f/` link store `CheckInFormsStep` writes into), `fe-reports-worklists` (`RevenueReports.jsx`, the only importer of `DailyHuddleView.jsx`), `fe-settings` (providers/services/operatories/schedule blocks), `fe-platform`.
