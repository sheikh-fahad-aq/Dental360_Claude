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
| `src/api/appointments.js` | **63 KB / 1918 lines.** Every `/v2/appointments/*` call + the card/detail mappers. Routes in `references/` §2. |
| `src/api/{scheduleBlocks,scheduleGroups,rooms,providers,services,multiCodes,lookups,appointmentLookups}.js` | Master data via **`authApi`**, not `appointmentApi`. Routes in `references/` §3. |
| `src/components/scheduling/CalendarGrid.jsx` (60 KB) · `WeekCalendarGrid` · `CalendarHeader` · `ViewDropdown` · `ScheduleActionsMenu` · `SchedulingSidebar` · `PasteSlotGhost` · `AppointmentHoverCard` | The calendar surface. `CalendarGrid` is the Day grid and the only one with drag/resize. |
| `AppointmentDetailDrawer.jsx` (**119 KB — largest file in `src/`**) · `RescheduleAppointmentModal` · `VisitStatusTracker` · `AppointmentVisitWizard.jsx` (**104 KB**) · `CheckInFormsStep` | Card → drawer; check-in / check-out wizards. |
| `VisitStatusBoard.jsx` (**115 KB**) · `SchedulePeek` · `ExitWorkflowChecklist` · `ExitWorkflowIncompleteModal` | Six-stage board, day timeline, exit gate UI. |
| `NewAppointmentModal.jsx` (45 KB) · `AppointmentProcedureSearch` · `AppointmentMultiCodeSelect` · `SelectedProceduresWithQuantity` · `FindOpenSlotsDrawer.jsx` (40 KB) + `find-open-slots/{DateRangePopover,MultiCheckboxSelect}.jsx` | Create flow and availability search. |
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
- **Two legacy endpoint fallbacks** in `api/appointments.js` are intentional — `references/` §2.
- **Editing `src/context/` forces a full page reload** (`fullReloadOnContextHmr()`, `vite.config.js`).
- `PROJECT_GUIDE.md` is stale and misleading; `PMS_React/README.md` is the source of truth.

## See also

- `references/state-and-api.md` — context line map, route tables, tracker/exit-workflow model.
- `main-architecture` — hub, index and change log.
- Backend siblings: `be-appointments` (calendar, CRUD, availability), `be-visit-lifecycle` (check-in/check-out, tracking-status, the appointment-forms proxy behind `VisitStatusBoard`), `be-recare-waitlist` (Scheduling Queue drawer, ASAP).
- Frontend siblings: `fe-patient-chart` (the chart's own Appts/Schedule tabs), `fe-forms` (the `/f/` link store `CheckInFormsStep` writes into), `fe-reports-worklists` (`RevenueReports.jsx`, the only importer of `DailyHuddleView.jsx`), `fe-settings` (providers/services/operatories/schedule blocks), `fe-platform`.
