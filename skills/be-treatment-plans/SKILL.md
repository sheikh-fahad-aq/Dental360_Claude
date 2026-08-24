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
| `360_Flask_Appointment/tests/test_treatment_plans.py` | 97 tests — 16 are named regressions for reviewed defects |
| `360_Flask_Appointment/migrations/versions/20260821_treatment_plan_origin.py` | `treatment_plans.origin` |

**Touches:** `app/__init__.py` (import + `register_blueprint`), `app/models.py`
`AppointmentProcedure.treatment_plan_item_id` (the new link column — **not**
`chart_procedure_id` beside it, which is an `Integer` against the `String(64)` object_id the
charting API hands out and is populated by nothing).

## Contract

Envelope is `{success, data}` / `{success, error}`, matching `waitlist_v2_routes.py`.

```
GET    /v2/patients/<id>/treatment-plans              list (?status=, ?clinic_id=, ?location_id=)  :469
       ^ each plan carries totals, acceptanceCounts, phaseCount and `teeth` — NOT phases/items
       ^ archived plans are EXCLUDED unless ?include_archived=true
POST   /v2/treatment-plans                            create, phases+items optional inline          :530
GET    /v2/treatment-plans/<planId>                   detail incl. signature                        :605
PUT    /v2/treatment-plans/<planId>                   edit (pre-response) or status:"void"          :615
DELETE /v2/treatment-plans/<planId>                   soft-delete (draft only)                      :677
POST   .../archive  | .../unarchive                   hide from the listing | bring it back
POST   /v2/treatment-plans/<planId>/phases            add phase                                     :741
PUT    | DELETE   .../phases/<phaseId>                rename/reorder | remove                  :768 :815
POST   /v2/treatment-plans/<planId>/items             add one or many                               :925
PUT    | DELETE   .../items/<itemId>                  edit/re-phase | remove                  :988 :1056
POST   .../present                                    records a showing; idempotent, never 409s    :1184
POST   .../decisions                                  chairside accept/decline/defer + signature   :1211
POST   | DELETE   .../share                           issue | revoke the patient link        :1339 :1377
POST   .../shared/<token>/verify                       PUBLIC — prove the DOB, mint an access token
GET    /v2/treatment-plans/shared/<token>             PUBLIC — patient reads their plan            :1390
       ^ both public reads require the X-Plan-Access credential that /verify returns
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
2. **`teeth` distinguishes `[]` from absent.** `_plan_teeth()` puts the distinct teeth a
   plan touches on every serialization, list and detail alike, first-planned first, so the
   listing can name them without fetching each plan in full. An EMPTY list means full-mouth
   work — a real clinical statement. Clients must not render a missing `teeth` as
   full-mouth: `normalizeTreatmentPlan` in `PMS_React/src/api/treatmentPlans.js` keeps it
   `null` for exactly that reason. It is staff-payload only — deliberately absent from
   `_serialize_plan_for_patient`, which stays allow-listed.
3. **This service never computes an estimate.** A figure is only ever what a caller
   supplied. The estimator lives in `PreAuth_Flask`, which is not in this workspace.
4. **`scheduled` is DERIVED, never set by a caller.** `_recalculate_plan_status` moves a
   plan there when every ACCEPTED item is booked and nothing is still awaiting a decision
   — the same shape as `completed`, which has always been derived from item
   `schedule_status`. Three rules it encodes: work that is entirely COMPLETED is past, not
   upcoming, so it falls through to `completed`; an undecided line keeps the plan out of
   `scheduled`, symmetrically with `completed`, because a booking does not settle a question
   the patient has not answered; and `schedule_treatment_plan_phase` **and**
   `unschedule_treatment_plan_item` both call the recalculation — neither did before, so a
   fully booked plan used to sit at "Accepted" until the next unrelated decision.

   It changes a LABEL, not the record: acceptance survives on every item, in
   `acceptanceCounts`, in the events and in the signature. Doing it here rather than in the
   SPA is what stops the two listings (the tx-plans table and the charting tab's) from
   disagreeing — they both just render `statusLabel`.
5. **The patient's RESPONSE is the freeze, not the presentation.**
   `EDITABLE_PLAN_STATUSES = {"draft", "presented"}` — a presented plan nobody has
   answered yet is still being negotiated, so phases and items stay editable. Editing
   closes the moment any decision is recorded (`partially_accepted`, `accepted`,
   `declined`) or the plan is signed. One gate: `_content_edit_error(plan)` for the
   document, `_item_edit_error(item)` for a single accepted line. Retraction is `void`,
   never delete — `void` must not carry content edits, and `DELETABLE_PLAN_STATUSES`
   stays `{"draft"}` because erasing is not editing.
   The frontend mirror is `isPlanEditable()` in `PMS_React/src/api/treatmentPlans.js`;
   the two lists must agree or the builder shows affordances that 409 on click.
6. **THREE REMOVAL VERBS, and they are not interchangeable.**
   - `archived_at` — put away. Leaves the listing, keeps status, decisions and
     signature. Reversible via `POST .../unarchive`. **This is the only one the SPA
     offers**, and the only one an operator means by "remove this plan".
   - `status = "void"` — retracted. The practice withdraws an offer the patient was
     SHOWN, and the void plan stays listed as the record of that.
   - `deleted_at` — erased. Draft only (`DELETABLE_PLAN_STATUSES`), cascades onto every
     phase and item. Gated on `_archived_error` FIRST, because archiving never writes
     status: an archived draft is still `"draft"` and would otherwise sail through the
     guard and be erased beyond the reach of unarchive.

   `archived` is deliberately **not** a status and is absent from
   `ck_treatment_plans_status`. `_recalculate_plan_status` rewrites `status` on every
   decision and would silently un-archive the plan; and archiving must not destroy the
   record of what the plan HAD been. Keep them orthogonal.

   **`_scheduled_item_count` is load-bearing, not fussy.** Archive 409s while any live
   item is scheduled or completed. An archived plan leaves `treatment_plan_item_index`,
   so its chart findings revert to "Not in Treatment Plan" — correct for unbooked work,
   and a double-billing path for booked work, because the `AppointmentProcedure` survives
   on the visit while the operator is invited to re-plan and re-book the same tooth.
   Relaxing that guard means changing the item-index contract in the same edit.

   **The archive gate belongs to the ROUTE, not to a branch of it.** `update_treatment_plan`
   only calls `_content_edit_error` when the body carries a CONTENT field, so a body of
   exactly `{"status":"void"}` reached the void transition ungated and could void an
   archived plan — which then came back from unarchive reading "Void". `_archived_error`
   is now called unconditionally, straight after `_get_plan_or_404`. Any new gate goes
   there too.

   Archive also stamps `share_revoked_at`, and `_resolve_share_token` tests `archived_at`
   **in its own right** — not via the revocation, which is a separable side effect.
   Unarchive does not reissue the link. Gated surfaces: present, decisions, share, send,
   schedule, unschedule, DELETE and `_content_edit_error`. Deliberately **un**gated:
   `/v2/appointments/<id>/planned-treatment` (both routes) and `revoke_share` — the first
   two are how already-booked work reaches the chair and the bill, the third can only
   narrow access.
7. **`origin` is authoring provenance, `response_source` is not.**
   `treatment_plans.origin` is `"chart"` (built from charted findings — the
   charting builder or Generate from Chart) or `"manual"` (typed on the patient's
   Treatment Plans page), and it is what that page groups by. An unknown value on
   create falls back to `"manual"` rather than 400ing: refusing to create a plan
   over a provenance label would be the worse failure. It is **staff-only** and
   deliberately absent from `_serialize_plan_for_patient()`. Do not confuse it
   with `response_source`, which records how the PATIENT's answer arrived — a
   plan is routinely chart-authored and phone-answered.
8. **The patient signature is write-once.** Re-signing is refused, and
   `submit_shared_decisions` refuses a closed plan outright via `_plan_closed_state`.
   Signing NO LONGER revokes the share token: it used to, and a patient who signed and
   refreshed — or whose phone dropped the response — met "this link is no longer
   available" with no way to tell whether their signature had landed. Write-once is
   enforced by the plan's terminal state, which is the thing that cannot be undone.
9. **THE PATIENT LINK TAKES TWO FACTORS, and the second one is the real one.**
   The token says WHICH plan. It travels by email and leaks the way email leaks, so it
   is not permission to read a clinical document on its own. `POST
   .../shared/<token>/verify` compares a date of birth against a salted digest
   snapshotted onto the plan at share/send time (`share_dob_hash` / `share_dob_salt`)
   and mints a row in `treatment_plan_share_sessions`; both public reads then require
   that credential in `X-Plan-Access`, checked BEFORE any `plan.status` inspection so
   the 409s distinguishing a draft from a closed plan sit behind both factors.

   Five rules hold this together, and each was a real hole first:
   - **Never a signed/stateless grant.** `app/__init__.py` sets `SECRET_KEY` to the
     literal `"your_secret_key"` unconditionally, overriding `config.py`. It is
     committed, so anything signed with it is forgeable by anyone who has read the
     repo. Hence a random secret compared against a stored digest, which needs no key.
   - **`share_failed_attempts` is MONOTONIC.** Cleared only by a successful verify —
     never by a cooldown expiring. A counter a lockout resets is one an attacker
     sleeps through.
   - **Attempt limiting NEVER revokes the link.** An unauthenticated caller who can
     permanently destroy a patient's access to their own plan has a denial-of-service
     primitive, not a security control. Cooldowns escalate and cap; they do not kill.
   - **Malformed input costs nothing.** A date failing the shape check, an unknown
     token, and a failure to READ the expected DOB all refuse without touching the
     counter — otherwise anyone holding the token locks the patient out with junk.
   - **Fail CLOSED.** `_live_patient_dob` returns None for a non-200, a 502, `PHI::`
     ciphertext or an unparseable shape, and every caller reads None as refuse. The
     `if status == 200 ... else` template elsewhere in this file is right for a
     display name and would be a hole here.

   The counter is keyed on the PLAN, not the token: re-sending rotates the token, and a
   token-keyed counter would let the practice hand an attacker a fresh budget on
   request. Rotation also revokes every existing session.
10. **`/send` and `/share` must issue the SAME link.** Both stop the expiry, both snapshot
   the DOB, both revoke existing sessions on rotation, and both refuse with 409 when the
   date of birth is unreadable. `/send` was left behind once already: emailing a plan
   produced a token that died in 30 days while Copy link produced a permanent one — the
   same plan with two lifetimes depending on which button the coordinator pressed. Any
   future change to one belongs in the other.
11. **Email variables are substituted SERVER-SIDE, and escaped.** `_fill_email_variables`
   fills `[Form Link]`, `[Practice Name]` and `[Patient First Name]` in both the subject
   and the body. `[Form Link]` *cannot* be filled in the browser: `/send` rotates the share
   token as part of sending, so the review URL does not exist until the request is being
   handled. Everything except the URL goes through `html.escape` — these land inside an HTML
   email, and a practice name carrying `&` or a patient name carrying `<` would otherwise
   break the markup or inject into it. The URL is deliberately NOT escaped; escaping it
   would corrupt the href.
12. **The patient link does not expire, and a finished plan says so.**
   `share_token_expires_at` is NULL on issue (an explicit `expiresInDays` is still
   honoured and capped at 10 years). A patient returning to a plan they already
   answered gets `closed: {reason, at}` and an "already complete" screen rather than a
   dead link.
13. **Public routes are allow-listed, not deny-listed.** `_serialize_plan_for_patient()`
   names every field that may leave. Never build the public payload by serializing
   everything and popping keys — that fails open on the next field added.
14. **Phase sequences are allocated, never caller-supplied,** and are never reused —
   `_next_phase_sequence()` counts soft-deleted rows, because
   `uq_treatment_plan_phases_plan_sequence` does not exclude them.
15. **Only `accepted` + `unscheduled` items are booked**, and an item whose
   `AppointmentProcedure.is_completed` cannot be unscheduled — otherwise the same
   treatment lands on the bill twice.
16. **`TreatmentPlanEvent.note` carries no PHI** — no signature bytes, no patient name.
17. **`AppointmentProcedure.completed_at` is a naive `DateTime`.** Write `tzinfo=None`;
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
