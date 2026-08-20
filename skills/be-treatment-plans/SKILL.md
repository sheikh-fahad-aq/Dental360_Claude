---
name: be-treatment-plans
description: Backend treatment plans — phase-wise proposed treatment, per-item patient accept/decline/defer, the signature, the tokenised patient review link, and the bridge that turns accepted work into appointment procedures and then completed treatment. Use when changing app/treatment_plans_v2_routes.py, adding or debugging a /api/v2/treatment-plans, /v2/patients/{id}/treatment-plans or /v2/appointments/{id}/planned-treatment endpoint, touching TreatmentPlan / TreatmentPlanPhase / TreatmentPlanItem / TreatmentPlanEvent, or chasing a plan status, share-token or scheduling 409.
---

## Scope

A treatment plan is a **clinical and financial document**, not a view over the chart. It
snapshots proposed procedures into phases, is presented to the patient, records a per-item
accept / decline / defer plus one signature, and then hands accepted work to the schedule
as `AppointmentProcedure` rows that get completed at the visit. It does **not** own the
odontogram (`be-charting`), the appointment itself (`be-appointments`), or check-out
(`be-visit-lifecycle`). It computes no insurance estimate — there is no estimator in this
backend. Maturity: **live** (backend); the React builder is partial — see `fe-patient-chart`.

## Files

| Path | Role |
|---|---|
| `360_Flask_Appointment/app/treatment_plans_v2_routes.py` | **(entry)** the whole blueprint — 23 routes, ~1890 lines. `grep`/`sed -n`, do not read whole. |
| `360_Flask_Appointment/app/models.py:1273-1500` | `TreatmentPlan` (:1273), `TreatmentPlanPhase` (:1335), `TreatmentPlanItem` (:1375), `TreatmentPlanEvent` (:1456) |
| `360_Flask_Appointment/migrations/versions/20260819_treatment_plans.py` | the 4 tables + `appointment_procedure.treatment_plan_item_id` |
| `360_Flask_Appointment/tests/test_treatment_plans.py` | 68 tests, ~1410 lines — 16 are named regressions for reviewed defects |

**Touches:** `app/__init__.py` (import + `register_blueprint`), `app/models.py`
`AppointmentProcedure.treatment_plan_item_id` (the new link column — **not**
`chart_procedure_id` beside it, which is an `Integer` against the `String(64)` object_id the
charting API hands out and is populated by nothing).

## Contract

Envelope is `{success, data}` / `{success, error}`, matching `waitlist_v2_routes.py`.

```
GET    /v2/patients/<id>/treatment-plans              list (?status=, ?clinic_id=, ?location_id=)  :469
POST   /v2/treatment-plans                            create, phases+items optional inline          :530
GET    /v2/treatment-plans/<planId>                   detail incl. signature                        :605
PUT    /v2/treatment-plans/<planId>                   edit (draft only) or status:"void"            :615
DELETE /v2/treatment-plans/<planId>                   soft-delete (draft only)                      :677
POST   /v2/treatment-plans/<planId>/phases            add phase                                     :741
PUT    | DELETE   .../phases/<phaseId>                rename/reorder | remove                  :768 :815
POST   /v2/treatment-plans/<planId>/items             add one or many                               :925
PUT    | DELETE   .../items/<itemId>                  edit/re-phase | remove                  :988 :1056
POST   .../present                                    draft -> presented, freezes the document     :1184
POST   .../decisions                                  chairside accept/decline/defer + signature   :1211
POST   | DELETE   .../share                           issue | revoke the patient link        :1339 :1377
GET    /v2/treatment-plans/shared/<token>             PUBLIC — patient reads their plan            :1390
POST   /v2/treatment-plans/shared/<token>/decisions   PUBLIC — patient submits + signs             :1421
GET    /v2/patients/<id>/treatment-plans/schedulable  accepted-but-unbooked worklist               :1474
POST   .../phases/<phaseId>/schedule                  book accepted items onto an appointment      :1518
POST   .../items/<itemId>/unschedule                  take one back off                            :1638
GET    /v2/appointments/<id>/planned-treatment        what this visit is planned to do             :1689
POST   /v2/appointments/<id>/planned-treatment/complete   mark done at the chair                   :1744
GET    /v2/treatment-plans/<planId>/events            the Activity tab                             :1848
```

## Invariants

1. **Money may be `NULL` and `NULL` is not `0`.** `office_fee_cents`,
   `insurance_estimate_cents`, `patient_estimate_cents` are nullable. `NULL` = "no figure"
   (renders "No Est."); `0` = genuinely free. `_totals()` returns `NULL` for a total the
   moment **any** line is unpriced — never sum the priced subset.
2. **This service never computes an estimate.** A figure is only ever what a caller
   supplied. The estimator lives in `PreAuth_Flask`, which is not in this workspace.
3. **A presented plan is frozen.** Only `status == 'draft'` may be edited (models, phases,
   items). Retraction is `void`, never delete — and `void` must not carry content edits.
4. **The patient signature is write-once.** Re-signing is refused, and signing spends the
   share token (`share_revoked_at`). The link is emailed and forwarded; one link, one
   signature.
5. **Public routes are allow-listed, not deny-listed.** `_serialize_plan_for_patient()`
   names every field that may leave. Never build the public payload by serializing
   everything and popping keys — that fails open on the next field added.
6. **Phase sequences are allocated, never caller-supplied,** and are never reused —
   `_next_phase_sequence()` counts soft-deleted rows, because
   `uq_treatment_plan_phases_plan_sequence` does not exclude them.
7. **Only `accepted` + `unscheduled` items are booked**, and an item whose
   `AppointmentProcedure.is_completed` cannot be unscheduled — otherwise the same
   treatment lands on the bill twice.
8. **`TreatmentPlanEvent.note` carries no PHI** — no signature bytes, no patient name.
9. **`AppointmentProcedure.completed_at` is a naive `DateTime`.** Write `tzinfo=None`;
   every other column here is `DateTime(timezone=True)`.

## Working here

1. Load this skill, then `be-data-model` for a schema change and `be-appointments` if the
   change crosses into scheduling.
2. Edit `app/treatment_plans_v2_routes.py`. It is one flat module by design (CLAUDE.md §4.1).
3. A new column needs the model in `app/models.py` **and** an Alembic revision. The
   `migrations/versions/` guard hook will refuse the write — the user must confirm.
4. A new public route must be added to `PUBLIC_ENDPOINTS` **and** given an allow-listed
   serializer. A route absent from that set gets the full `require_api_and_bearer` gate.
5. Add tests to `tests/test_treatment_plans.py`; run
   `env/Scripts/python.exe -m unittest tests.test_treatment_plans`.
6. Frontend counterpart is `PMS_React/src/api/treatmentPlans.js` — a new response field
   needs a line in its normalizer or components never see it.

## Traps

- **`chart_procedures` is NOT the backing store, deliberately.** `POST /v2/charts/chartprocedure`
  is an upsert keyed on `(session_id, type, cdt_code, tooth_number, condition_type)`, so two
  phases proposing the same code on the same tooth would merge; every chart-procedure write
  needs an `active` ChartSession and a signed session is terminal with no reopen route; and
  its `status` P→{C,D,R} is one-way, so a patient who declines could never later accept.
  See the comment block above `TreatmentPlan` in `models.py:1249`.
- `chart_procedure_object_id` on an item is **provenance only** — never dereferenced for
  display. The item snapshots its own copy so a signed plan cannot move.
- The public endpoints require `x-api-key` but **no Bearer token**. That key is
  `VITE_`-prefixed and baked into the SPA bundle (CLAUDE.md §7.2), so the share token is the
  only real secret. Treat it accordingly: opaque, expiring, spent on use.
- `_resolve_share_token` returns the same vague 404 for unknown / expired / revoked / void.
  Do not make those distinguishable — the difference only helps somebody probing tokens.
- A `deferred` item blocks the terminal `completed` status on purpose. `completed` is
  terminal (early return in `_recalculate_plan_status`), so claiming it while a decision is
  outstanding would strand a patient who later says yes.
- `cdt_code` is `String(64)` but `AppointmentProcedure.procedure_code` is `String(50)` —
  truncate at the boundary (`:1586`), as `description` already does.

## See also

`main-architecture` · `be-charting` (where recommended treatment comes from) ·
`be-appointments` and `be-visit-lifecycle` (where accepted treatment goes) ·
`be-data-model` · `fe-patient-chart` (the Tx Plans UI)
