# fe-scheduling — SchedulingContext map, API surface, tracker model

Companion to `fe-scheduling/SKILL.md`. Everything here was read out of the working tree.
Line numbers drift — re-`grep` before trusting one.

---

## 1. Navigating `PMS_React/src/context/SchedulingContext.jsx` (2050 lines)

One provider, one giant function body (`SchedulingProvider` at `:86`), one `useMemo` value
object at `:1796`, `useScheduling()` at `:2046`. Do **not** read it whole. Use:

```bash
grep -nE "^  const [a-zA-Z]+ = (useCallback|useMemo)" src/context/SchedulingContext.jsx
grep -nE "^  const \[[a-zA-Z]+" src/context/SchedulingContext.jsx      # state
sed -n 'START,ENDp' src/context/SchedulingContext.jsx
```

### Layout by line range

| lines | what lives there |
|---|---|
| `1–83` | imports. Pulls from `data/scheduling`, `utils/visitStatusTracker`, `api/appointments`, `api/rooms`, `api/scheduleGroups`, `api/scheduleBlocks`, `utils/appointmentQueries`, `utils/appointmentClipboard`, `utils/appointmentMove`, `utils/weekRange` and 5 sibling contexts (`Auth`, `Location`, `Patients`, `Providers`, `Rooms`). |
| `86–140` | request-id refs (`dayAppointmentsRequestIdRef`, `daySchedulesRequestIdRef`, `dayScheduleBlocksRequestIdRef`, `statusFiltersRequestIdRef`, `statusTrackerRequestIdRef`, `trackingSummaryRequestIdRef`, `trackerListRequestIdRef`) + the appointments/date/view/filter state. |
| `141–300` | UI-shell state (sidebar, fit-to-screen, four accordion collapse flags), modal/drawer state, tracker state, route-slip state. |
| `302–520` | tracker loaders: `ensureTrackerStatuses:302`, `reloadTrackingSummary:338`, `reloadStatusTracker:383`, `reloadTrackerList:437`. |
| `521–744` | visit-stage mutators: `setVisitStage:521` (the longest single callback), `advanceVisitStage:721`, `focusAppointment:733`. |
| `745–1055` | appointment CRUD: `openNewAppointment:745`, `addAppointment:786`, `createAppointment:799`, `removeAppointment:884`, `cancelAppointment:890`, `moveAppointment:925`, `resizeAppointment:991`. |
| `1056–1200` | filter toggles (`toggleProvider`, `toggleOperatory`, `toggleStatus` — the last takes `{ exclusive }`), `reloadStatusFilters:1142`. |
| `1200–1250` | date navigation. `goToPrevDay:1206` / `goToNextDay:1215` step ±7 in Week mode. `isWeekView` derived at `:1246`. |
| `1340–1420` | `clearScheduleFilters:1340`, `selectAllProviders:1347`, `filteredAppointments:1357`. |
| `1422–1584` | `reloadDayAppointments` — the main loader. Day *or* week range, `merge`, `silent`. |
| `1585–1795` | `visibleColumns:1585`, `reloadDaySchedules:1625`, `reloadDayScheduleBlocks:1673`, `blocksByRoomId:1724`, `schedulesByRoomId:1754`. |
| `1796–2044` | the `value` memo — the exported API, ~110 keys. Read this to learn what consumers may use. |

### The mock fallback branch

`reloadDayAppointments` at `:1440` short-circuits when `!appointmentsApiEnabled`, and at
`:1443` calls `setAppointments(APPOINTMENTS)` — the seed re-exported by
`src/data/scheduling.js:77` from `src/data/appointmentsSeed.js`. Initial state at `:143` does
the same: `isAppointmentsApiEnabled() ? [] : APPOINTMENTS.map(withStoredVisitStage)`.
There is **no banner and no `source` field** on this context — unlike the `use*` hooks, the
scheduling context does not tell you whether you are looking at API or seed data.

### Persisted keys

| key | written by |
|---|---|
| `pd:schedule:fitToScreen` | `SchedulingContext.jsx:177,186` |
| `pms.visitStage.<appointmentId>` | `utils/visitStatusTracker.js:86,131` |
| `pms.checkInWizardSkipped.<appointmentId>` | `utils/visitStatusTracker.js:87,143` |

---

## 2. `src/api/appointments.js` (1918 lines, 63 KB) — routes

`const BASE = '/v2/appointments'` (`:15`). Client is `appointmentApi`, so every path is
emitted as `/__appointment_api/api/v2/appointments/...` regardless of
`VITE_APP_BASE_URL_APPOINTMENT`. Local `unwrap()` at `:184` handles bare arrays,
`{ success, data }` (throws when `success === false`) and `{ appointments: [] }`.

| method + path | export | line |
|---|---|---|
| `GET /v2/appointments` | `listPatientAppointments` | `:574` |
| `GET /v2/appointments/calendar` | `fetchAppointmentsCalendar` | `:645` |
| `POST /v2/appointments/availability` | `searchAppointmentAvailability` | `:865` |
| `POST /v2/appointments` | `createAppointment` | `:895` |
| `GET /v2/appointments/{id}` | `fetchAppointmentDetail` | `:929` |
| `PUT /v2/appointments/{id}` | `updateAppointment` | `:936` |
| `POST /v2/appointments/{id}/cancel` | `cancelAppointmentApi` | `:973` |
| `POST /v2/appointments/{id}/no-show` | `markAppointmentNoShow` | `:982` |
| `POST /v2/appointments/{id}/complete` | `completeAppointmentManual` | `:991` |
| `GET·POST /v2/appointments/{id}/procedures`, `PUT·DELETE .../{procedureId}` | `listAppointmentProcedures:1016`, `createAppointmentProcedure:1024`, `updateAppointmentProcedure:1029`, `deleteAppointmentProcedure:1037` | |
| `GET·POST /v2/appointments/{id}/notes`, `PUT·DELETE .../{noteId}` | `listAppointmentNotes:1046` … `deleteAppointmentNote:1065` | |
| `GET /v2/appointments/{id}/forms` | `listAppointmentForms` | `:1126` |
| `POST` request-forms (all / one) | `requestAllAppointmentForms:1136`, `requestAppointmentForm:1154` | |
| `PUT /v2/patient-forms/{patientFormId}` | `updateAppointmentPatientForm` | `:1173` |
| `POST .../check-in/start`, `PUT .../check-in`, `POST .../check-in/complete` | `startCheckIn:1180`, `updateCheckIn:1187`, `completeCheckIn:1192` | |
| `POST .../check-out/start`, `PUT .../check-out`, `POST .../check-out/complete` | `startCheckOut:1250`, `updateCheckOut:1257`, `completeCheckOut:1262` | |
| recare list / schedule | `listPatientRecare:1223`, `schedulePatientRecare:1240` | |
| tracking-status CRUD | `listAppointmentStatuses:1306`, `createAppointmentStatus:1329`, `updateAppointmentStatus:1339`, `deleteAppointmentStatus:1351` | |
| `GET /v2/appointments/status-filters` | `fetchStatusFilters` | `:1379` |
| `GET /v2/appointments/status-tracker` | `fetchStatusTracker` | `:1778` |
| tracking summary | `fetchTrackingSummary` | `:1815` |
| `PATCH /v2/appointments/{id}/tracking-status` | `patchTrackerStatus` | `:1848` |
| `GET /v2/appointments/{id}/route-slip` | `fetchRouteSlip` | `:1907` |
| `GET /v2/appointments/{id}/status-logs` | `fetchAppointmentStatusLogs` | `:1915` |

### Two legacy-fallback pairs — do not "clean these up"

- `TRACKING_STATUSES_BASE = '/v2/appointment-tracking-statuses'` (`:1289`) with
  `TRACKING_STATUSES_LEGACY = '/v2/appointment-statuses'` (`:1290`). Every status CRUD call
  tries the first and retries the second.
- `patchTrackerStatus` (`:1848`) PATCHes `.../tracking-status`, and on **404 or 405 only**
  retries `.../tracker-status` (`:1896`). Any other status re-throws.

### Mappers exported here (use them, never hand-roll)

`toScheduleAppointment(raw, opts):287` — raw calendar row → calendar card.
`toAppointmentDetail(payload, opts):490` — detail GET → drawer model.
`preserveSchedulePlacement(mapped, existing):33` — detail GET may return null
operatory/provider; this keeps the card where the calendar already put it instead of
dropping it into `UNASSIGNED_OPERATORY_ID` (`:18`, the string `'__unassigned__'`).
`buildCreateAppointmentPayload(input):768`, `buildUpdateSchedulePayload({…}):943`,
`mapApiStatusToUiStatuses(status, checkInStatus):259`,
`normalizeStatusFiltersResponse:1403`, `normalizeStatusSummaryToFilters:1502`,
`appointmentMatchesStatusFilters:1730`, `normalizeAppointmentFormsResponse:1076`,
`mapAppointmentInsurance:113`, `asAppointmentNotesText:89`.

Wizard step arrays live here too: `CHECK_IN_STEPS:155`
(`demographics · insurance · payment · forms · handoff · recall`),
`CHECK_IN_STEPS_LEGACY:165` (deprecated, has `copay`/`card_on_file`),
`CHECK_OUT_STEPS:175` (`visit_summary · insurance_estimate · payment · treatment · recall …`),
`NOTE_TYPES:152`.

---

## 3. Sibling API modules

All of these use **`authApi`** (not `appointmentApi`), i.e. `VITE_APP_BASE_URL_AUTH`.

| module | routes |
|---|---|
| `src/api/rooms.js` | `GET /locations/{id}/rooms:223`, `GET /rooms/{id}:234`, `POST /locations/{id}/rooms:246`, `PUT /rooms/{id}:258`, `DELETE /rooms/{id}:269`, `GET /get_room_id:281`. Also `getRoomHoursForDate:466`, `findScheduleRoom:573`. |
| `src/api/providers.js` | `GET /clinic_providers/get_all/{clinicId}:82`, `GET /clinic_providers/{id}:153`, `POST /clinic_providers:158`, `PUT :164`, `PATCH .../toggle:170`, `DELETE :176`, `GET /clinic_providers/filter:181`. The cached list fetch is wrapped in `withInflightDedupe` (`:139`); `findScheduleProvider:364`. |
| `src/api/services.js` | `GET /services/get_all/{clinicId}:80`, `GET /services/{id}:91`, `POST /services:101`, `PUT /services/{id}:113`. |
| `src/api/scheduleBlocks.js` | `GET /schedule_blocks:153`, `GET /schedule_blocks/{id}:164`, `POST :175`, `PUT :241`, `DELETE :252`. Block types: `block·lunch·meeting·holiday·closed·maintenance·custom`. |
| `src/api/scheduleGroups.js` | `POST /create_schedule_group:409`, `POST /schedule_provider:451`, `GET /schedule_groups:469`, `GET /schedule_groups/filter:493`, `GET /provider_schedules:521`. Provider working hours per room/date. |
| `src/api/multiCodes.js` | `/v2/multi-codes` — list `:283`, detail `:322`, `GET /{id}/preview:334` (fees are **not** on the multi-code; preview sums `procedure_code_fees` per location), `POST :342`, `PUT :349`, `PATCH /toggle:360`, `DELETE :382`. |
| `src/api/lookups.js` | `GET /roles:65`, `GET /clinic_roles:73`, service-category CRUD `:209/:247/:269`. |
| `src/api/appointmentLookups.js` | No routes of its own — wraps `lookups`/`providers`/`rooms`. `getAvailableSlots:108` computes slots **client-side** from `getRoomHoursForDate`; it is not the backend availability call and is used only by patient-chart drawers, not by Find Open Slots. |

---

## 4. Visit tracker & exit workflow

`src/utils/visitStatusTracker.js` (25 KB) is the model.

- `VISIT_TRACKER_STAGES:16` — six stages, ids `arriving · here · ready · chair · checkout ·
  complete`, each with `label`, `color`, `boardBg`, `boardBorder` and a `mapsTo` legacy
  status. `VISIT_TRACKER_STAGE_IDS:73`, `DEFAULT_TRACKER_STATUS_SEED:76`.
- Derivation: `extractTrackerCode(appt):196` → `deriveVisitStage(appt):222` →
  `withStoredVisitStage(appt):321` (overlays localStorage). `canShowVisitTracker:264`,
  `isAppointmentCheckedIn:282`, `isReadyOrLaterStage:165`,
  `showsSkippedCheckInIndicator:180`.
- Normalizers for the board: `normalizeTrackerListAppointment(raw, bucketCode):391`,
  `normalizeStatusTrackerResponse:549`, `normalizeTrackingSummary:703`,
  `defaultTrackerActions:350`.

`src/config/exitWorkflowTasks.js`

- `EXIT_WORKFLOW_TASK_IDS:8` = `schedule_recare · collect_phone · collect_email ·
  collect_payment`; `EXIT_WORKFLOW_TASKS:15` adds `label` and `async`.
- `evaluateExitWorkflowTasks(appt, { recareComplete }):166`,
  `getIncompleteExitTasks:193`, `isExitWorkflowStage:44`, `fetchRecareComplete:147`,
  `isPaymentProxyComplete:88`.

`src/config/exitWorkflowSettings.js` — `EXIT_WORKFLOW_SETTINGS:7`,
`isExitWorkflowRequireReasonEnabled:11`, `EXIT_TASK_SKIP_REASON_OPTIONS:16`,
`buildExitTaskSkipPayload:27`. The skip payload fields (`exit_task_skip_reason`,
`exit_task_skip_note`, `exit_task_incomplete`) are accepted by both
`patchTrackerStatus` and `completeCheckOut`.

Gate wiring: `src/hooks/useExitWorkflowCompleteGate.js:20` owns the gate and renders
`ExitWorkflowIncompleteModal`; `src/hooks/useExitWorkflowRecareMap.js:10` batch-resolves the
async recare task for a list of patient ids.

---

## 5. Grid geometry — `src/data/scheduling.js`

```
HOUR_HEIGHT 96 · SUB_SLOTS_PER_HOUR 4 · SUB_SLOT_HEIGHT 24
TIME_COLUMN_WIDTH 80 · COLUMN_MIN_WIDTH 250 · HEADER_HEIGHT 58
GRID_HOURS 24 · GRID_HEIGHT 2304 · START_HOUR 0 · END_HOUR 24
BUSINESS_START 9 · BUSINESS_END 16
VIEW_OPTIONS ['Day','Week','Month','Year']
```

`PROVIDERS` and the re-exported `APPOINTMENTS` in the same file are **mock seeds**.
Print/peek surfaces use their own scale: `PRINT_HOUR_HEIGHT = 40`
(`DaySchedulePrintDocument.jsx:16`), `PEEK_HOUR_HEIGHT = 44` (`SchedulePeek.jsx:31`).

---

## 6. Drag mechanics

`src/hooks/useAppointmentDrag.js` — pointer events, `DRAG_THRESHOLD_PX = 5:10`,
`AUTO_SCROLL_EDGE_PX = 56:11`, `AUTO_SCROLL_STEP_PX = 14:12`. Imported by
**`CalendarGrid.jsx` only** — week view has no drag.

Drop resolution is DOM hit-testing, not React state:
`resolveDropTarget(clientX, clientY, durationMin)` at `utils/appointmentMove.js:48` calls
`document.elementFromPoint(...)` (`:49`) and `closest('[data-operatory-column]')` (`:50`),
reading the column id off the attribute (`:53`). The attribute is emitted at
`CalendarGrid.jsx:790`. Rename it and drag silently stops working — nothing type-checks it.

Collision + snapping: `canPlaceAppointment:26`, `rangesOverlap:11`,
`snapMinutesFromOffset:15`, `snapDurationMinutes:63`.
