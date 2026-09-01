---
name: be-treatment-plans
description: Backend treatment plans — phases, per-item accept/decline/defer, the signature, archive, the two-factor (share token + date of birth) patient review link, and booking accepted work onto a visit. Use when changing app/treatment_plans_v2_routes.py, adding a /api/v2/treatment-plans, /v2/patients/{id}/treatment-plans or /v2/appointments/{id}/planned-treatment endpoint, touching TreatmentPlan / TreatmentPlanItem / TreatmentPlanShareSession, or chasing a plan status, share-token or scheduling 409.
---

## Scope

A treatment plan is a **clinical and financial document**, not a view over the chart. It
snapshots proposed procedures into phases, presents them to the patient, records a per-item
accept / decline / defer plus one signature, and hands accepted work to the schedule as
`AppointmentProcedure` rows completed at the visit. It does **not** own the odontogram
(`be-charting`), the appointment (`be-appointments`) or check-out (`be-visit-lifecycle`), and
computes no estimate. **Live**; the React builder is partial (`fe-patient-chart`).

## Files

| Path | Role |
|---|---|
| `360_Flask_Appointment/app/treatment_plans_v2_routes.py` | **(entry)** the whole blueprint — 30 routes, 3255 lines (~130KB). `grep`/`sed -n`, do not read whole. |
| `360_Flask_Appointment/app/models.py:1249-1681` | rationale comment (`:1249`), `TreatmentPlan` (`:1273`), `TreatmentPlanShareSession` (`:1401`), `TreatmentPlanPhase` (`:1447`), `TreatmentPlanItem` (`:1487`), `TreatmentPlanEvent` (`:1579`), `TreatmentPlanRevision` (`:1616`) |
| `360_Flask_Appointment/tests/test_treatment_plans.py` | 141 tests, the only coverage for this feature |
| `360_Flask_Appointment/migrations/versions/` | `20260819_treatment_plans.py` (4 tables + `appointment_procedure.treatment_plan_item_id`), then `20260820_tp_revisions.py`, `20260820_treatment_plan_item_material.py`, `20260820_treatment_plan_response.py`, `20260821_treatment_plan_origin.py`, `20260822_treatment_plan_archived.py` (archive columns + `ix_treatment_plans_patient_archived_at`), `20260824_tp_share_verify.py` (DOB hash/salt, attempt counter, `treatment_plan_share_sessions`), `20260824_tp_scheduled.py` (`ck_treatment_plans_status` widened with `scheduled`; first `op.batch_alter_table` in this repo) |

**Touches:** `app/__init__.py:55` (import) + `:75` (`register_blueprint`, `url_prefix='/api'`);
`AppointmentProcedure.treatment_plan_item_id`, **not** the dead `chart_procedure_id` beside it.

## Contract

Envelope `{success, data}` / `{success, error}`; line = the `@…route` decorator; `.../` is
`/v2/treatment-plans/<planId>/`. The listing returns totals, acceptedTotals, acceptanceCounts,
scheduleCounts, phaseCount and teeth but NOT phases/items, and hides archived plans unless
`?include_archived=true`.

```
GET  /v2/patients/<id>/treatment-plans  list; ?status= ?clinic_id= ?location_id=  :1028
POST /v2/treatment-plans  create; phases+items optional inline                    :1103
GET|PUT|DELETE /v2/treatment-plans/<planId>  read | edit/void | delete draft
                                                                :1185 :1195 :1268
POST .../archive | .../unarchive  leave the listing | come back        :1299 :1345
POST .../reopen                   new version: unsign, clear answers
POST .../phases   PUT | DELETE .../phases/<phaseId>      :1411   :1439 :1490
POST .../items    PUT | DELETE .../items/<itemId>        :1613   :1677 :1763
POST .../present (idempotent, never 409s) | .../decisions (chairside) :1940 :1991
POST .../share | .../send | DELETE .../share  issue|email|revoke :2140 :2203 :2316
POST /v2/treatment-plans/shared/<token>/verify  PUBLIC — prove DOB, mint    :2367
GET|POST /v2/treatment-plans/shared/<token>[/decisions]  X-Plan-Access :2471 :2535
GET  /v2/patients/<id>/treatment-plans/schedulable | .../item-index :2672 :2716
POST .../phases/<phaseId>/schedule | .../items/<itemId>/unschedule  :2781 :2924
GET|POST /v2/appointments/<id>/planned-treatment[/complete]         :2987 :3041
GET  .../events | .../revisions | .../revisions/<revisionId>  :3146 :3196 :3229
```

## Invariants

1. **Removing a plan is ARCHIVE; archive/void/delete are not interchangeable.** `archived_at`
   hides it reversibly; `status="void"` retracts an offer the patient was SHOWN and stays
   listed; `deleted_at` erases a draft only. Archive is the only one the SPA offers, and
   `archived` is deliberately **not** a status. `_archived_error` (`:793`) goes at the TOP of
   a route, never in a branch; archive 409s while `_scheduled_item_count` (`:814`) is non-zero.
2. **`scheduled` is DERIVED, never set by a caller.** `_recalculate_plan_status` (`:951`,
   block `:1004`) sets it when every accepted item is booked and nothing awaits a decision.
   A LABEL only; `schedule_treatment_plan_phase` and `unschedule_treatment_plan_item` call it.
3. **THE CALENDAR IS THE FREEZE, not the patient's response.** `EDITABLE_PLAN_STATUSES =
   {"draft","presented","partially_accepted","accepted"}`, `DELETABLE_PLAN_STATUSES =
   {"draft"}`. A plan the patient accepted but nobody has booked is still being arranged;
   freezing at "accepted" only forced coordinators to abandon the document and rebuild it,
   losing the plan the patient agreed to. What cannot move is work the calendar owns, and
   that is enforced **per line**: `_item_edit_error` refuses `schedule_status !=
   "unscheduled"`, NOT `acceptance == "accepted"`. It is load-bearing now, not defence in
   depth — the only thing between an edit and an orphaned `AppointmentProcedure`.
   `delete_treatment_plan_phase` bypasses it entirely and carries its own booked guard for
   the same reason. The content routes call `_recalculate_plan_status` so a line added
   after acceptance drops the plan off "accepted" instead of claiming the patient agreed to
   it. Mirrored by `isPlanEditable()` / `isPlanItemEditable()` in
   `PMS_React/src/api/treatmentPlans.js`.
4. **A SIGNATURE IS STILL AN ABSOLUTE BAR at `_content_edit_error`; `/reopen` is the way
   through.** It detaches the signature, clears every acceptance and the manual response,
   then lets `_recalculate_plan_status` land the plan on `presented`. It must **never** set
   `status="draft"`: that reads as "nobody has ever seen this" and is a trap —
   `_recalculate_plan_status` returns early on draft, so the plan could never climb back
   and completing treatment at the chair would leave it reading Draft forever. Nothing is
   copied and nothing is lost: `_capture_revision` already ran on the signing request, so
   the signed text is a frozen revision in the version picker — that IS the "previous
   version". Refuses once anything is booked. Modelled on `reopen_chart_perio_exam`: a
   distinct transition, never a widened gate. `response_source` / `response_note` are NOT
   NULL, so clear them to `""`.
   **Booked lines are SKIPPED, not refused.** Rejecting the whole request whenever anything
   was on the calendar made a `scheduled` plan permanently unrevisable — book phase 1 and
   phase 2 could not be touched. A booked line keeps its acceptance (an appointment backs it)
   and stays protected by `_item_edit_error`; the rest reopen and the roll-up drops off
   `scheduled` on its own. With NOTHING unbooked it refuses even when a signature could be
   detached: doing so would strip the attestation and leave the plan equally uneditable — a
   destructive no-op. **`completed` is refused outright** and the message names Duplicate:
   every accepted line has been performed, with appointment procedures marked done and
   charges posted, so clearing the acceptance would say nobody agreed to delivered work.
   **Refused outright on `scheduled` and `completed`.** `scheduled` is derived and means EVERY
   accepted line is booked with nothing undecided, so a reopen would find no reopenable line,
   change no acceptance, leave the status where it was — and destroy the signature on the way
   past. A strictly destructive no-op. This does NOT conflict with the skip-booked-lines rule:
   the case that one protects (phase 1 booked, phase 2 open) leaves the plan on `accepted`,
   because not every accepted line is booked yet, and that plan still reopens. The client
   mirrors it — `canReopen` tests `!isSettledPlan` BEFORE the signature clause, which is an OR
   and otherwise let a scheduled-and-signed plan offer a button the server refuses.
5. **THE PATIENT LINK TAKES TWO FACTORS, and the second is the real one.** `POST
   .../shared/<token>/verify` (`:2367`) proves the reader by date of birth against a per-plan
   salted digest and mints the `X-Plan-Access` credential both public reads check BEFORE any
   status inspection. Never a signed grant (`app/__init__.py:28` commits a literal
   `SECRET_KEY`); `share_failed_attempts` is monotonic; limiting never revokes the link; junk
   input never spends the counter; `_live_patient_dob` (`:283`) fails CLOSED.
6. **`/send` and `/share` must issue the SAME link.** Both stop the expiry, both call
   `_snapshot_share_dob` (`:299`) and 409 when the DOB is unreadable, both
   `_revoke_share_sessions` on rotation. Signing no longer revokes the token.
7. **Email variables are substituted SERVER-SIDE, and escaped.** `_fill_email_variables`
   (`:2329`) fills `[Form Link]`/`[Practice Name]`/`[Patient First Name]`; the browser cannot
   fill `[Form Link]`, as `/send` rotates the token. All but the URL go through `html.escape`.
8. **Public routes are allow-listed, not deny-listed** — `_serialize_plan_for_patient()`
   (`:2055`) names every field that may leave. `PUBLIC_ENDPOINTS` at `:184`.
9. **`NULL` money is not `0`** (no figure vs free): `_totals` (`:636`) returns `NULL` if **any**
   line is unpriced. **`teeth` distinguishes `[]` from absent** (`_plan_teeth` `:668`), EMPTY
   meaning full-mouth. Staff-only, as is `origin` (provenance, NOT `response_source`).
10. **Phase sequences are allocated, never caller-supplied,** and never reused —
   `_next_phase_sequence` (`:1396`) counts soft-deleted rows.
11. **Only `accepted` + `unscheduled` items are booked**, a completed one cannot be unscheduled,
   and scheduling **adopts** a matching booking row instead of inserting a duplicate (`:2633`).
12. **Events and revision snapshots carry no PHI** — no signature bytes, name or email.
   `AppointmentProcedure.completed_at` is naive (`:3084`); all else is `timezone=True`.

## Working here

1. Load `be-data-model` too for a schema change, `be-appointments` if it crosses into
   scheduling. Edit `app/treatment_plans_v2_routes.py` — flat by design (CLAUDE.md §4.1).
2. A new column needs the model in `app/models.py` **and** an Alembic revision; the
   `migrations/versions/` guard hook refuses the write until the user confirms.
3. A new public route needs three things: an entry in `PUBLIC_ENDPOINTS` (`:184`), an
   allow-listed serializer, and a `_verified_share_session` (`:353`) check before any
   `plan.status` read. Absent from that set it gets `require_api_and_bearer` instead.
4. Any new mutating route calls `_archived_error` right after `_get_plan_or_404` (`:560`),
   unless it is an exemption listed in `references/removal-and-status.md`.
5. `env/Scripts/python.exe -m pytest tests/test_treatment_plans.py`. A new response field
   also needs a line in the normalizer in `PMS_React/src/api/treatmentPlans.js`.

## Traps

- **`chart_procedures` is NOT the backing store, deliberately** — upsert key, `active`-session
  requirement, one-way status axis; `chart_procedure_object_id` on an item is provenance
  only. See `references/removal-and-status.md` and `app/models.py:1249`.
- The public endpoints require `x-api-key` but **no Bearer token**, and that key is
  `VITE_`-prefixed and baked into the SPA bundle (CLAUDE.md §7.2) — the DOB is the only real
  secret in the chain.
- `_resolve_share_token` (`:2117`) returns the same vague 404 for unknown / revoked /
  archived / expired / void. Do not make those distinguishable.
- A `deferred` item blocks the terminal `completed` status on purpose (`:990`), which returns
  early at `:957` — claiming it with a decision outstanding strands a patient who says yes later.
- `cdt_code` is `String(64)` but `AppointmentProcedure.procedure_code` is `String(50)`;
  truncate at the boundary (`:2854`), as `description` does at `:2876`.
- `SHARE_TOKEN_TTL_DAYS = 30` (`:109`) exists but no longer governs `/share` or `/send`.

## See also

Long form: invariants 1-3 and 10 in `references/removal-and-status.md`; 4-6 in
`references/share-link.md`; 8 and 11 in `references/data-rules.md`. Siblings:
`main-architecture` · `be-charting` · `be-appointments` · `be-visit-lifecycle` ·
`be-data-model` · `fe-patient-chart` · `fe-platform` (the `/tp/:token` page).
