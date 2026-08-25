# Removal verbs, the editing freeze, and derived status

Long-form backing for invariants 2–4 in `be-treatment-plans/SKILL.md`. Line numbers are in
`360_Flask_Appointment/app/treatment_plans_v2_routes.py` unless stated otherwise.

## Three removal verbs, and they are not interchangeable

| Verb | Column / value | What it means | Reversible |
|---|---|---|---|
| **archive** | `archived_at` (`app/models.py:1349`) | put away — leaves the listing, keeps status, decisions and signature | yes, `POST .../unarchive` `:1345` |
| **void** | `status = "void"` | the practice RETRACTED an offer the patient was shown; stays listed as the record of it | no |
| **delete** | `deleted_at` | erase a draft nobody ever saw; cascades onto every phase and item | no |

**Archive is the only one the SPA offers**, and the only one an operator means by "remove
this plan". `PMS_React/src/api/treatmentPlans.js` exports `archiveTreatmentPlan` (`:601`)
and `unarchiveTreatmentPlan` (`:609`); `voidTreatmentPlan` and `deleteTreatmentPlan` were
removed from that client. The backend routes still exist — `PUT` with `{"status":"void"}`
(`:1195`) and `DELETE /v2/treatment-plans/<planId>` (`:1268`) — they simply have no caller
in the SPA.

`DELETABLE_PLAN_STATUSES = {"draft"}` (`:98`). A presented plan gets the 409 "A presented
treatment plan cannot be deleted. Archive it instead." (`:1285`).

## `archived` is deliberately NOT a status

It is absent from `ck_treatment_plans_status` (`app/models.py:1387-1391`). Two reasons:

- `_recalculate_plan_status` (`:951`) rewrites `status` on every decision and would
  silently un-archive the plan;
- archiving must not destroy the record of what the plan HAD been.

Keep the two axes orthogonal. The listing composes them rather than letting them compete:
`?status=accepted` still cannot surface an archived plan, and `deleted_at` stays a separate
AND — deleted beats archived (`:1046-1055`).

The escape hatch is `?include_archived=true|1|yes` (`:1042`). An archive nobody can ever
see again is a delete wearing a kinder name, and unarchive needs some way to reach its
target.

Indexing: `ix_treatment_plans_patient_archived_at` on `(patient_id, archived_at)`
(`app/models.py:1397`) — the pre-existing `ix_treatment_plans_patient_status` cannot serve
the listing's `patient_id + archived_at` filter.

## `_scheduled_item_count` is load-bearing, not fussy

`:814`. Archive **409s** while any live item has `schedule_status != "unscheduled"` — i.e.
is scheduled or already completed.

An archived plan leaves `treatment_plan_item_index` (`GET
/v2/patients/<id>/treatment-plans/item-index`, `:2716`), so its chart findings revert to
"Not in Treatment Plan". That is correct for unbooked work and a **double-billing path**
for booked work: the `AppointmentProcedure` row survives on the visit, the operator sees
the finding as unplanned, re-plans it, and the same tooth and CDT code is billed twice.
Refusing to archive removes the contradiction instead of papering over it.

Relaxing that guard means changing the item-index contract in the same edit.

## The archive gate belongs to the ROUTE, not to a branch of it

`update_treatment_plan` (`:1198`) only calls `_content_edit_error` when the body carries a
CONTENT field (`title`, `narrative`, `providerId`, `providerName`, `preparedOn`). So a body
of exactly `{"status":"void"}` reached the void transition ungated and could void an
archived plan — which then came back from unarchive reading "Void", the exact conflation
the feature exists to undo. `_archived_error` (`:793`) is now called **unconditionally**,
straight after `_get_plan_or_404` (`:1204-1211`). Any new gate goes there too.

`delete_treatment_plan` calls `_archived_error` **before** the status check (`:1280`),
because archiving never writes status: an archived draft is still `"draft"` and would
otherwise sail through `DELETABLE_PLAN_STATUSES` and be erased beyond the reach of
unarchive (which resolves through `_get_plan_or_404`, which filters `deleted_at`).

Inside `_content_edit_error` (`:831`) the archive check sits **between** the signature
check and the status check (`:855`), so an archived DRAFT is told it is archived rather
than the misleading "can no longer be edited".

### Gated vs deliberately ungated

Gated on `_archived_error`: present, decisions, share, send, schedule, unschedule, DELETE,
and `_content_edit_error` (hence every content mutation).

Deliberately **un**gated: `GET/POST /v2/appointments/<id>/planned-treatment[/complete]`
(`:2987`, `:3041`) and `revoke_treatment_plan_share` (`:2316`). The first two are how
already-booked work reaches the chair and the bill; the third can only ever narrow access.

Archive also stamps `share_revoked_at` when a token exists (`:1335`), and
`_resolve_share_token` tests `archived_at` **in its own right** (`:2132`) — not via the
revocation, which is a separable side effect. Unarchive does **not** reissue the link:
revoking was a deliberate act of closing a public PHI surface.

`archive` / `unarchive` write `_log_event` verbs `"archived"` / `"unarchived"`.
`treatment_plan_events.action` is free text with no `CheckConstraint`, so a new verb needs
no migration. Neither route captures a revision — nothing about what was proposed changed.

## The patient's RESPONSE is the freeze, not the presentation

`EDITABLE_PLAN_STATUSES = {"draft", "presented"}` (`:93`). A presented plan nobody has
answered yet is still being negotiated, so phases and items stay editable. Editing closes
the moment any decision is recorded (`partially_accepted`, `accepted`, `declined`) or the
plan is signed.

One gate for the document (`_content_edit_error`, `:831`), one for a single accepted line
(`_item_edit_error`, `:863`). The latter is defence in depth and deliberately kept even
though it should be unreachable — it survives for the case where item acceptance and plan
status disagree.

Retraction is `void`, never delete, and **void must not carry content edits**: previously
`not wants_void` short-circuited the whole freeze, so a body carrying `status:"void"` could
also rewrite the title and narrative of a plan the patient had already signed.

The frontend mirror is `isPlanEditable()` in `PMS_React/src/api/treatmentPlans.js:104`
(with `planLockReason()` at `:118`). The two lists must agree or the builder shows
affordances that 409 on click.

## `scheduled` is DERIVED, never set by a caller

`_recalculate_plan_status` (`:951`, the derivation block at `:1004-1012`). A plan reads
`scheduled` when:

- there is at least one accepted item, AND
- `everything_decided` — `counts["pending"] == 0 and counts["deferred"] == 0`, AND
- every accepted item is `scheduled` or `completed`, AND
- at least one is `scheduled`.

Three rules that encodes:

1. Work that is entirely COMPLETED is past, not upcoming — the `any(... == "scheduled")`
   clause lets it fall through to the `completed` branch at `:1014`.
2. An undecided line keeps the plan out of `scheduled`, symmetrically with `completed`,
   because a booking does not settle a question the patient has not answered.
3. `schedule_treatment_plan_phase` (`:2909`) **and** `unschedule_treatment_plan_item`
   (`:2981`) both call the recalculation — neither did before, so a fully booked plan used
   to sit at "Accepted" until the next unrelated decision. Other callers: `:2031`
   (chairside decisions), `:2577` (patient decisions), `:3130` (completion at the chair).

It changes a LABEL, not the record: acceptance survives on every item, in
`acceptanceCounts`, in the events and in the signature. Deriving it here rather than in the
SPA is what stops the two listings (the tx-plans table and the charting tab's) from
disagreeing — they both just render `statusLabel`.

Vocabulary is widened in `migrations/versions/20260824_tp_scheduled.py`, which is the first
revision in this repo to use `op.batch_alter_table` (a SQLite CHECK cannot be altered in
place, and `migrations/env.py` sets no `render_as_batch`).

`deferred` blocks the terminal `completed` status on purpose. `completed` is terminal (the
early return at `:957`), so claiming it while a decision is outstanding would strand a
patient who later says yes.

## Booking ADOPTS rather than inserts

`schedule_treatment_plan_phase` (`:2781`). Booking a phase from Find Open Slots is TWO
writes, not one: the drawer seeds its procedure chips from the plan, sends them as
`procedureCodes`, and `create_appointment` materialises those into `AppointmentProcedure`
rows before this endpoint is called. Inserting again put the same tooth on the visit twice,
both priced — a billing defect.

`_adoptable_booking_rows` (`:2633`) builds a pool of rows on the visit that no plan item
owns yet (`treatment_plan_item_id IS NULL`) and that are not completed, ordered by id.
`_take_booking_row` (`:2602`) claims one, consuming it, in **two passes**:

1. exact `(code.upper(), tooth)` — a row that DOES name a tooth should only be claimed by
   the item for that tooth;
2. same code with a **blank** tooth — this is the pass that fires in practice, because
   `buildCreateAppointmentPayload` in `PMS_React/src/api/appointments.js` writes
   `tooth: null, surface: null, fee: null` for every row it builds from `procedureCodes`.

The tradeoff in pass two is deliberate: a genuinely separate tooth-less procedure with the
same code, added by someone else, can be claimed by the plan item instead. That costs one
merged row; not doing it costs every planned procedure being billed twice.

On both paths the plan's copy is authoritative — `procedure_code`, `description`, `tooth`,
`surface`, `fee`, `quantity` are all rewritten (`:2874-2881`), because the booking payload
carries no tooth, no surface and no fee.

Each candidate is consumed at most once, so two identical accepted lines cannot collapse
onto one booking row (which would leave the second unbilled while looking scheduled).

`cdt_code` is `String(64)` but `AppointmentProcedure.procedure_code` is `String(50)` —
truncated at `:2854`, as `description` does at `:2876`.

## Why `chart_procedures` is not the backing store

`POST /v2/charts/chartprocedure` is an UPSERT keyed on `(session_id, type, cdt_code,
tooth_number, condition_type)`, so two phases proposing the same code on the same tooth
would merge into one row. Every chart-procedure write requires the owning `ChartSession` to
still be `active`, and a signed session is terminal with no reopen route — while patient
acceptance happens days or weeks later. And `chart_procedure.status` P→{C,D,R} is a ONE-WAY
clinical axis, so a patient who declines in August could never accept in November.

Full rationale is the comment block above `TreatmentPlan` at
`360_Flask_Appointment/app/models.py:1249-1271`.

`chart_procedure_object_id` on a `TreatmentPlanItem` is **provenance only** — never
dereference it for display. The item snapshots its own copy of code, description, tooth,
surfaces and fee, so a signed plan cannot move when the chart moves.
