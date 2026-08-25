# Serialization, money, provenance and PHI rules

Long-form backing for the shorter invariants in `be-treatment-plans/SKILL.md`. Line numbers
are in `360_Flask_Appointment/app/treatment_plans_v2_routes.py` unless stated otherwise.

## Money may be `NULL`, and `NULL` is not `0`

`office_fee_cents`, `insurance_estimate_cents`, `patient_estimate_cents` on
`TreatmentPlanItem` (`app/models.py:1487`) are all nullable, on purpose. `NULL` means "no
figure has been entered" and renders as "No Est."; `0` means the procedure is genuinely
free.

This is the direct contrast with `chart_procedures.ucr_fee_cents`, which is `NOT NULL
DEFAULT 0` — there, "unpriced" and "$0.00" are indistinguishable. See the comment block at
`app/models.py:1249`.

`_sum_optional` (`:628`) and `_totals` (`:636`) return `NULL` for a total the moment **any**
line is unpriced. Never sum the priced subset and present it as the plan total: a patient
signing a document that says "$1,200" when three of eight lines had no price is being shown
a number nobody stands behind.

## This service never computes an estimate

A figure in this API is only ever what a caller supplied. There is no insurance estimator
in `360_Flask_Appointment`. The estimator lives in `PreAuth_Flask`, which is **not in this
workspace** — do not add one here as a side effect.

`_cents_to_fee` (`:2665`) converts integer cents to the `Float` dollars
`AppointmentProcedure.fee` expects. That is a units conversion, not an estimate.

## `teeth` distinguishes `[]` from absent

`_plan_teeth(items)` (`:668`) returns the distinct tooth numbers a plan touches, ordered by
**first appearance** rather than sorted — a plan reads in the order it was built, and
"#8, #32" is how the clinician refers to it.

It is attached to every staff serialization, list (`:1090`) and detail alike, because the
LIST read carries neither phases nor items and the treatment-plan table had no other way to
say which teeth a plan covers without fetching every plan in full.

An **EMPTY** list means full-mouth work — a real clinical statement, since full-mouth items
carry no tooth number and are simply absent from the list rather than appearing as a blank
entry. A **MISSING** `teeth` key means the payload did not carry the field at all. Clients
must not conflate them: `normalizeTreatmentPlan` in
`PMS_React/src/api/treatmentPlans.js:289` keeps it `null` for exactly that reason.

`teeth` is staff-payload only, deliberately absent from `_serialize_plan_for_patient`
(`:2055`), which stays allow-listed.

## `scheduleCounts` is counted over accepted items only

`_schedule_counts` (`:694`). Only accepted work can be booked —
`schedule_treatment_plan_phase` refuses everything else — so a pending or declined line
sitting at "unscheduled" would be noise that makes a fully booked plan look half-finished.

## `origin` is authoring provenance; `response_source` is not

`treatment_plans.origin` is `"chart"` (built from charted findings — the charting builder,
or Generate from Chart) or `"manual"` (typed on the patient's Treatment Plans page). It is
what that page groups by.

An unknown value on create falls back to `"manual"` rather than 400ing: refusing to create
a plan over a provenance label would be the worse failure.

It is **staff-only** and deliberately absent from `_serialize_plan_for_patient()`.

Do not confuse it with `response_source`, which records how the PATIENT's answer arrived. A
plan is routinely chart-authored and phone-answered — the two fields are orthogonal.

Column added by `migrations/versions/20260821_treatment_plan_origin.py`; frontend constants
`PLAN_ORIGIN` / `PLAN_ORIGIN_LABEL` at `PMS_React/src/api/treatmentPlans.js:150-155`.

## Phase sequences are allocated, never caller-supplied

`_build_phase` (`:1376`) ignores the caller's `sequence` on every insert path.
`uq_treatment_plan_phases_plan_sequence` is unconditional.

`_next_phase_sequence` (`:1396`) counts **soft-deleted rows too**, because that unique
constraint does not exclude them. Reusing a sequence number freed by a soft delete raises
an `IntegrityError` at commit, far from the code that caused it.

`_next_item_sequence` (`:1600`) is the item-level equivalent.

## Revisions are write-once, and carry no signature

`_capture_revision` (`:882`) is called AFTER the mutation is applied and BEFORE the commit,
so the snapshot records the plan as it will actually read. The `db.session.flush()` at
`:904` is what makes that true — `_live_phases` / `_live_items` issue queries, and a
pending insert or a pending `deleted_at` would otherwise snapshot the state the caller was
trying to replace.

A version number is never reused. Not every mutation path bumps `plan.version` (the phase
routes never have), so when the current version already carries a revision the code moves
to the next one rather than collide with `uq_treatment_plan_revisions_plan_version` or —
far worse — rewrite a revision somebody has already been shown.

PHI: the snapshot is built with `include_signature=False` **and** `patientSignature` is
popped regardless (`:914`). `_serialize_revision` (`:931`) pops it again on read, as
defence in depth against a row written by an older build or restored from a dump. The
base64 signature lives once, on the plan; copying it into a row per edit multiplies where
it can leak (CLAUDE.md §7.1).

`REVISION_REASONS` (`:151`) is validated in `_capture_revision` — an unknown reason raises
`ValueError` rather than writing an uncategorised row.

## `TreatmentPlanEvent` carries no PHI

`_log_event` (`:529`). No signature bytes, no patient name, no recipient email address. The
`shared` event records the CHANNEL only (`:2306`). `treatment_plan_events.action` is free
text with **no** `CheckConstraint`, so a new verb needs no migration.

## Timezone asymmetry at the AppointmentProcedure boundary

Every datetime column on the treatment-plan tables is `DateTime(timezone=True)`.
`AppointmentProcedure.completed_at` is a **naive** `DateTime`. Write `tzinfo=None` when
crossing that boundary in `complete_appointment_planned_treatment` — `naive_now` at `:3084` — or SQLAlchemy
raises on comparison.

`_as_aware` (`:426`) and `_utc_now` (`:422`) are the helpers on this side; `_iso` (`:439`)
is the only thing that should ever produce a datetime string for the wire.

## `chart_procedure_id` on AppointmentProcedure is dead

`AppointmentProcedure` carries two columns that look interchangeable. The live link is
`treatment_plan_item_id`, written by `schedule_treatment_plan_phase`. Beside it,
`chart_procedure_id` is an `Integer` while the charting API hands out a `String(64)`
`object_id` — nothing populates it. Do not use it as a join key or "fix" it as a side
effect; it is recorded here so the next reader does not spend an hour on it.
