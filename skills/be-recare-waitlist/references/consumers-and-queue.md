# be-recare-waitlist reference — frontend consumers and queue mechanics

Loaded on demand. Every file named here lives in `PMS_React/` and is owned by `fe-scheduling`
or `fe-settings`, never by this skill.

## 1. Frontend consumers

All go through `appointmentApi`, base `/__appointment_api/api`, proxied in
`PMS_React/vite.config.js:51` and `vercel.json:5` — those two must change together.

| Client | Consumer | Notes |
|---|---|---|
| `src/api/waitlist.js` | `src/components/scheduling/SchedulingQueueDrawer.jsx` | list / pin / restore / remove / find-slots / offer |
| `src/api/waitlist.js` | `AppointmentDetailDrawer.jsx:1468-1508` | Actions → "Move to waitlist" |
| `src/api/appointments.js:1223` `listPatientRecare` | `AppointmentVisitWizard.jsx:1015` | the check-in Recall step |
| `src/api/appointments.js:1223` `listPatientRecare` | `src/config/exitWorkflowTasks.js:147` | `fetchRecareComplete`, drives the "schedule recare" exit task rendered by `ExitWorkflowChecklist.jsx` |
| `src/api/appointments.js:1240` `schedulePatientRecare` | — | exported, **no caller** |

`src/utils/appointmentWaitlist.js` builds the `POST /v2/waitlist` body from an appointment and
exposes the `validateWaitlistMoveContext` guard.

`src/components/settings/scheduling/AsapWaitlistPanel.jsx` is 72 lines of `useState` with **no
API calls at all**; `PMS_React/README.md:363` labels the `asap-waitlist` settings tab
mock/static. Maturity: backend routes `live`, settings panel `placeholder`.

## 2. Response envelopes differ between the two blueprints

- **Waitlist** returns `{success, data}` on success and `{success: false, error}` on failure.
- **Recare** returns bare objects, with `{error}` on failure.

`unwrap()` in `src/api/waitlist.js:14` encodes the waitlist shape. Harmonising one without the
other silently breaks the drawer.

## 3. Queue ordering

Computed in **Python, not SQL** — `_sort_key` at `waitlist_v2_routes.py:110`:

1. `is_pinned` descending (pinned entries first)
2. `PRIORITY_RANK[priority]` ascending; an unknown priority falls to rank **9**
3. `created_at` ascending
4. `id` ascending

`PRIORITIES`, `STATUSES`, `QUEUE_TYPES` and `PRIORITY_RANK` all live at
`waitlist_v2_routes.py:28-31`. Adding a priority value means editing `PRIORITIES` *and*
`PRIORITY_RANK`, or every new entry sorts last. Adding a SQL `order_by` will not win — the
Python sort runs after it.

## 4. `find-slots`

`POST /v2/waitlist/<id>/find-slots` (`:479`) is **read-only**: it proposes slots and books
nothing. It reaches the Auth service through `validate_provider` / `fetch_auth_service`, clamps
`days` to 1–31 (`:499-500`), and falls back to a 30-minute duration with a `warning` in the
response when the service record carries no duration (`:524-528`).

## 5. The two write paths for "recare is scheduled"

State that should have one owner has two:

1. `POST /v2/patients/<id>/recare/<patient_recare_id>/schedule` (`recare_v2_routes.py:178`) —
   the designed path, and **dead from the UI**.
2. `POST /v2/appointments/<id>/check-in/complete` with `linked_recare_id`
   (`app/appointment_checkin_routes.py:172-188`, owned by `be-visit-lifecycle`) — mutates
   `PatientRecare` directly and bypasses the route above.

Change one and you must change the other. See also invariant 7 in `SKILL.md`: recare `POST`
sets `is_scheduled = True` whenever `linked_appointment_id` is present
(`recare_v2_routes.py:164-165`) — a third place the same coupling is expressed.

## 6. The waitlist → appointment loop is not closed

`SchedulingQueueDrawer.jsx:817,895` put `waitlistId` on the appointment clipboard, but nothing
reads it back. No code anywhere sets `status='scheduled'` or `scheduled_appointment_id`; the
only status write the UI issues is `status:'waiting'` (`:798`). Entries therefore stay
`waiting` after the patient has actually been booked. Fixing this needs both repos.

## See also

`be-recare-waitlist/SKILL.md` · `be-appointments` (`find_available_slots`) ·
`be-visit-lifecycle` (the Recall step) · `fe-scheduling` (every file above).
