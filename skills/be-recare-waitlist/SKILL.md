---
name: be-recare-waitlist
description: Backend recare/recall due tracking and the ASAP waitlist queue — recare types, patient recare items, waitlist entries, priority ranking, soft-cancel and find-slots. Use when changing recare_v2_routes.py or waitlist_v2_routes.py, adding a /api/v2/recare-types, /api/v2/patients/<id>/recare or /api/v2/waitlist endpoint, debugging the Scheduling Queue drawer, "move to waitlist", ASAP priority order, or the check-in Recall step. Proposes slots but never books: appointment writes are be-appointments.
---

## Scope

Two small sibling blueprints that both feed scheduling demand from opposite ends.
**Recare** (`recare_v2_routes.py`) tracks *future* demand: a patient owes a hygiene/perio
recall on a due date, and the row flips to `is_scheduled` once an appointment is linked.
**Waitlist** (`waitlist_v2_routes.py`) absorbs *unmet* demand: patients queued for an
earlier or ASAP slot, ranked so staff can fill a cancellation. Neither module creates or
mutates appointments — recare only *links* an existing appointment id, waitlist only
*proposes* slots. Booking belongs to `appointments_v2_routes.py`; availability math to
`app/util/appointments_helpers.py`.

## Files

| Path | Role |
|---|---|
| `360_Flask_Appointment/app/recare_v2_routes.py` | **(entry)** 235 lines, 5 routes. Recare types + patient recare items. Read whole. |
| `360_Flask_Appointment/app/waitlist_v2_routes.py` | **(entry)** 617 lines / ~24KB, 6 routes. ASAP/waitlist queue. Read whole or by section. |

Models, owned by `be-data-model`, none with FKs: `RecareType` (`app/models.py:372`),
`PatientRecare` (`:379` — patient_id, recare_type_id, due_date, linked_appointment_id,
location_id, is_scheduled) and `AppointmentWaitlist` (`:757` — clinic/location/patient, priority,
status, queue_type, is_pinned, scheduled_appointment_id).

Touched, not owned: `app/util/appointments_helpers.py` (`serialize_recare:3650`,
`find_available_slots`, `resolve_availability_*`, `slim_patient/provider` — `be-appointments`),
`app/util/decorators.py` and `app/__init__.py:48-49,65-66` (`be-platform`),
`app/appointment_checkin_routes.py:168-190` (`be-visit-lifecycle`). `src/api/waitlist.js` and
`src/utils/appointmentWaitlist.js` are **`fe-scheduling`'s**, not this skill's.

## Contract

Backend — all mounted at `url_prefix='/api'`:

- `GET  /api/v2/recare-types` — list all types, name asc. `recare_v2_routes.py:33`
- `POST /api/v2/recare-types` — create; case-insensitive dedupe returns 200 not 201. `:50`
- `GET  /api/v2/patients/<patient_id>/recare` — `?location_id=&actionable=true`; returns `recare[]` + `actionable_count`. `:85`
- `POST /api/v2/patients/<patient_id>/recare` — accepts `recare_type_id` *or* `recare_type_name` (auto-creates the type). `:125`
- `POST /api/v2/patients/<patient_id>/recare/<patient_recare_id>/schedule` — links an appointment, sets `is_scheduled`. `:178`
- `GET  /api/v2/waitlist` — `clinic_id` + `location_id` required; filters `status|priority|queue_type|search|pinned|include_cancelled`; returns `{items, total, counts, filters}`. `waitlist_v2_routes.py:138`
- `POST /api/v2/waitlist` — add entry. `:231`
- `GET  /api/v2/waitlist/<id>?clinic_id=` — single entry. `:336`
- `PUT|PATCH /api/v2/waitlist/<id>` — partial update; `clinic_id` required in body. `:357`
- `DELETE /api/v2/waitlist/<id>?clinic_id=[&soft=false]` — soft-cancel by default. `:440`
- `POST /api/v2/waitlist/<id>/find-slots` — proposes open slots; **read-only**, books nothing. `:479`

Frontend, all via `appointmentApi` over `/__appointment_api/api`: `src/api/waitlist.js` feeds
`SchedulingQueueDrawer.jsx` and the detail drawer's "Move to waitlist"; `listPatientRecare` in
`src/api/appointments.js:1223` feeds the check-in Recall step and the exit-workflow recare task.
Maturity: backend routes `live`; the `asap-waitlist` settings panel is a `placeholder` with no
API calls (`PMS_React/README.md:363`). Full consumer table: `references/consumers-and-queue.md` §1.

## Invariants

1. Auth is enforced by a blueprint-wide `before_request` gate wrapping `require_api_and_bearer`
   (`recare_v2_routes.py:16-23`, `waitlist_v2_routes.py:34-41`) — every request needs
   `x-api-key` **and** `Authorization: Bearer`. Never add a per-route auth decorator here; it
   would double-validate against the Auth service.
2. Every waitlist route is tenant-scoped: the query must filter on `clinic_id` (and
   `location_id` for list). A new waitlist route without a `clinic_id` filter is a bug.
3. Enum values live in `waitlist_v2_routes.py:28-31` (`PRIORITIES`, `STATUSES`, `QUEUE_TYPES`,
   `PRIORITY_RANK`), validated on write. Adding one means editing that constant *and*
   `PRIORITY_RANK`, or the entry sorts to rank 9.
4. Queue order is computed in Python, not SQL: `_sort_key` at `:110` = pinned first, then
   priority rank, then `created_at`, then id (`references/consumers-and-queue.md` §3). Do not
   add an `order_by` and assume it wins.
5. `serialize_recare` (`appointments_helpers.py:3650`) and `_serialize_entry`
   (`waitlist_v2_routes.py:73`) are the only response shapes. Add a field there, not inline.
6. Recare and waitlist never write to `Appointment` — they store an appointment id
   (`linked_appointment_id` / `scheduled_appointment_id`) and nothing else.
7. Recare `POST` sets `is_scheduled = True` whenever `linked_appointment_id` is present
   (`recare_v2_routes.py:164-165`); keep that coupling if you add another write path.
8. Waitlist responses are `{success, data|error}`; recare responses are bare objects with
   `{error}`. Do not "harmonise" one without updating `unwrap()` in `src/api/waitlist.js:14`.
   Both shapes: `references/consumers-and-queue.md` §2.

## Working here

1. Inventory first: `grep -nE "@[a-z_0-9]+\.route\(" app/waitlist_v2_routes.py`.
2. Edit the route in the single flat module — there is no package per feature.
3. New blueprint only: import it in `app/__init__.py:48-49` and register with
   `url_prefix='/api'` at `:65-66`. Existing routes need no registration change.
4. Model change → edit `app/models.py`, then add an Alembic revision under
   `360_Flask_Appointment/migrations/versions/` (see Traps #1).
5. Frontend: add the call to `src/api/waitlist.js` or the Recare block at
   `src/api/appointments.js:1217`, then wire the component (`fe-scheduling`).

## Traps

1. **No migration exists for these tables.** All 20 revisions in `migrations/versions/` are
   charting revisions; `appointment_waitlist`, `patient_recare` and `recare_type` were never
   created by Alembic, so on a fresh DB the table itself may be missing. Do not assume
   autogenerate produces a clean diff.
2. **The waitlist → appointment loop is not closed.** Entries stay `waiting` after the patient is
   booked; nothing writes `scheduled_appointment_id`. `references/consumers-and-queue.md` §6.
3. **`schedule` route is dead from the UI**, and there are two write paths for one state change
   — the check-in wizard mutates `PatientRecare` directly via `linked_recare_id`
   (`appointment_checkin_routes.py:172-188`). Change both: §5 of the reference.
4. `POST /v2/recare-types` and `POST /v2/patients/<id>/recare` have **no frontend caller**;
   recare rows are seeded elsewhere (unverified — no seeding code found in this repo).
5. `DELETE` defaults to soft-cancel (`soft` is false only when `?soft=false` literally appears,
   `:449`). Cancelled rows stay in the table, and reappear with `?include_cancelled=true`.
6. `GET /v2/patients/<id>/recare?location_id=` also returns rows with `location_id IS NULL`
   (`recare_v2_routes.py:94-100`) — deliberate, so clinic-wide recare is never hidden.
7. `find-slots` reaches the Auth service via `validate_provider`/`fetch_auth_service`, clamps
   `days` to 1–31 (`:499-500`), and silently falls back to 30 minutes with a warning when the
   service record has no duration (`:524-528`).
8. Waitlist patient/provider names are denormalised columns backfilled from Auth at create
   time (`_patient_name_from_auth:65`) and go stale; the serializer prefers a live payload.

## See also

- `main-architecture` — hub, index and change log.
- `be-appointments` — owns booking, availability helpers and `find_available_slots`.
- `be-visit-lifecycle` — owns the Recall step that writes `PatientRecare` directly.
- `be-data-model` — owns `recare_type`, `patient_recare`, `appointment_waitlist`.
- `be-lab-cases` — sibling V2 flat module with the same auth and pagination shape.
- `fe-scheduling` — owns `src/api/waitlist.js`, `SchedulingQueueDrawer.jsx` and the recare calls
  in `src/api/appointments.js`.
- `references/consumers-and-queue.md` — consumer table, envelope shapes, `_sort_key`,
  `find-slots`, and the two unclosed loops.
