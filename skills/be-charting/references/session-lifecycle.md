# Chart session lifecycle — gate matrix, wire shapes, error map

Companion to `be-charting/SKILL.md`. All line numbers verified against
`360_Flask_Appointment/app/charting_routes.py` (1879 lines).

## 1. Status machine

`ChartSession.status` is one of `CHART_SESSION_STATUSES` (`:50`):
`active`, `draft`, `pending_countersign`, `pending_revision`, `auto-sign`, `signed`.
Only `active` and `draft` are *open* (`OPEN_SESSION_STATUSES`, `:48`).
`pending_countersign` / `pending_revision` are declared for the `?status=` list filter but
**no route writes them** — they exist in the enum only.

```
                    POST /chart-session  (:1206)
                              │  status=active, mode=clinical_session|edit_only
                              ▼
                  ┌───────► active ◄──────────────┐
                  │           │                   │
   POST /resume   │           │ POST /draft       │ POST /chart-templates
   (:1606)        │           │ (:1298)           │ (:909)  ← also forces draft
                  │           ▼                   │
                  └────────  draft  ──────────────┘
                              │
                              │ POST /autosign (:1383)   POST /signed (:1464)
                              ▼                           ▼   (requires status==active)
                          auto-sign                     signed
                        (ended_at set)                (ended_at + signature set)
```

Terminal states have no route back. There is **no unlock/reopen endpoint** — the frontend's
"Unlock chart" (`PMS_React/src/components/patient-detail/charting/UnlockChartModal.jsx`) resolves to `POST /resume`,
which only works while the session is still `active` or `draft`.

## 2. Per-route gate matrix

| route | mode gate | status gate | writes status |
|---|---|---|---|
| `POST /chart-session` `:1206` | payload `mode` in `("clinical_session","edit_only")` | — (409 if an open one exists) | `active` |
| `POST /chart-session/draft` `:1298` | clinical only (`:1333`) | open (`:1340`) | `draft` |
| `POST /chart-session/autosign` `:1383` | clinical only (`:1411`) | **`draft` only** (`:1418`) | `auto-sign` |
| `POST /chart-session/signed` `:1464` | clinical only (`:1522`) | **`active` only** (`:1529`) | `signed` |
| `POST /chart-session/resume` `:1606` | clinical only (`:1630`) | open (`:1637`) | `active` |
| `POST /chart-session/template` `:1012` | clinical only (`:1044`) | open (`:1046`) | unchanged |
| `POST /chart-templates` `:909` | clinical only (`:941`) | open (`:947`) | `draft` |
| `POST /chartprocedure` `:522` | any mode | **`active` only** (`:569`) | unchanged (touched) |
| `DELETE /chartprocedure` `:674` | any mode | **`active` only** (`:700`) | unchanged (touched) |
| `POST /chartprocedure/status` `:761` | any mode | **`active` only** (`:797`) | unchanged (touched) |
| `POST /chartprocedure/details` `:1745` | any mode | **none — any status** (`:1745` docstring) | unchanged (touched) |

Read routes (`GET /chart-session`, `/chart-session/active`, `/chart-session/templates`,
`/chartprocedure`, `/conditions`, `/chart-templates`) gate on nothing but auth.

**The sign/autosign asymmetry is the sharpest edge.** `/signed` demands `active`; `/autosign`
demands `draft`. Any autosave (`POST /draft`) flips the session to `draft`, so a client that
autosaved and then presses "Sign Note" gets
`409 "Only active clinical sessions can be signed"` until it calls `/resume` first.

## 3. Locking

Every mutating route re-reads its session with `.with_for_update()` inside the try block
before checking status, so two concurrent writers serialize on the row. `_open_session:305`
also takes `FOR UPDATE`, which is what makes the duplicate-session check in
`create_chart_session` race-free on Postgres.

**SQLite ignores `FOR UPDATE` and `skip_locked` entirely**, so the test suite proves the
status gates but proves nothing about the locking. Concurrency changes must be reasoned about
against Postgres, not against a green test run.

`_touch_session:249` / `_next_activity_time:233` bump `last_activity_at`, `lock_heartbeat` and
`updated_at` together, forcing strict monotonicity by adding 1µs when the clock has not moved.
`lock_heartbeat` is the *only* field the auto-draft scheduler reads — a route that mutates a
session without touching it makes that session look idle.

## 4. Audit log

`_add_audit_log:328` writes `ChartAuditLog(chart_id=<6-digit code>, session_id, user_id,
provider_id, action, details)`. Actions actually emitted:

`session_created`, `session_resumed`, `session_signed`, `session_auto_signed`,
`session_auto_drafted` (scheduler only, `user_id="system"`), `draft_saved` (manual saves only —
autosaves write no audit row, `:1364`), `chart_template_updated`, `chart_session_note_saved`,
`procedure_added` / `procedure_updated` / `procedure_deleted` / `procedure_status_updated` /
`procedure_details_updated` (the administrative-correction route; its `details` string names each
changed field `old -> new`, but for `comments` records only *that* it changed — the note body is
clinical free text, CLAUDE.md §7.1),
`condition_added` / `condition_updated` (the non-`TP` twins of the procedure actions).

`chart_id` on the audit row is the **zero-padded string** `_chart_code:268`, not `Chart.id`.

## 5. Wire shapes

Envelope for every route in both blueprints: `{"result": …, "status": <int>, "error": …}`,
and the HTTP status equals the `status` field (`_response:68`).

Timestamps are Firestore-style `{"_seconds": int, "_nanoseconds": int}` (`_timestamp:257`) —
not ISO strings. The session/procedure serializers also carry Firestore residue
(`collectionType`, `dataModelObjectType`, `objectID` with a capital D) that the frontend
normalizers depend on: `_serialize_session:402`, `_serialize_chart_procedure:456`,
`_serialize_chart_template:487`, `_serialize_chart_session_note:498`.

`objectID` prefixes: sessions `cs_`, templates `tpl_`, procedures `cp_`
(`_object_id:281`, `_template_object_id:289`, `_procedure_object_id:297` — each retries 5×
against a uniqueness probe, then raises).

`ChartProcedure` is serialized with **both** `sessionId` and `encounterId` set to the same
session object id (`:477`).

## 6. Chart procedures

- `type` ∈ `{TP, Cn, EC, EO}` (`CHART_PROCEDURE_TYPES:59`, mirrored by a DB CheckConstraint
  `ck_chart_procedures_type` on `models.py:755`-`:757`). `status` ∈ `{P, R, C, D}` (a Postgres enum
  `chart_procedure_status_enum`, `models.py:723`-`:729`).
- Default status is `P` for `TP`, `C` for everything else (`_chart_procedure_default_status:64`).
- `POST /chartprocedure` is an **upsert, not an insert**: it matches on
  `(session_id, type, cdt_code, tooth_number, condition_type)` *plus* whether the incoming
  surface list is empty, and merges surfaces into the existing row (`:581`-`:612`). Two calls
  for the same tooth+code do not create two rows — they widen one.
- Surfaces are normalized to `{M, O, D, B, L, I}` by `_normalize_surfaces:132`.
- Delete is a **soft delete** (`deleted_at`, `:734`) and is refused unless
  `type == "TP" and status == "P"` (`:722`). Completed or existing work can never be removed.
- `GET /chartprocedure` filters `deleted_at IS NULL` and ignores `locationId` beyond validating
  it (`:838`) — the response is every non-deleted procedure for the patient, all sessions.

## 7. Catalogs

- `GET /conditions` (`:876`) paginates `ChartCondition` with `page`/`limit`, `limit` capped at
  100 (400 above that). `clinic_id`/`location_id` are validated then **discarded** — the
  catalog is global.
- `GET /chart-templates` (`:902`) returns every `ChartTemplate` row, one per visit type.
- `POST /chart-templates` (`:909`) overwrites the **global** template body for a visit type
  while also drafting the caller's session note. It has no frontend caller.
- `POST /chart-session/template` (`:1012`) attaches an *additional* visit-type note to an open
  session and is 409 if that visit type already has one (`:1069`). This is how a session ends
  up with several notes, which `POST /signed` then signs together via its `templates[]` array.

## 8. Error map (charting_routes)

| status | when |
|---|---|
| 400 | malformed/missing field, bad `visitType`, `chartId`/`sessionId` sent to `POST /chart-session`, procedure/session mismatch |
| 401 | no user id resolvable from the bearer payload (`_current_user_id:150`) |
| 403 | bad api key / bearer (raised by the decorators, not this module) |
| 404 | session, chart, or procedure not found |
| 409 | duplicate open session, wrong mode, wrong status, missing draft note, undeletable procedure |
| 502 | Auth system unreachable or non-200 when validating patient/provider (`_external_lookup:195`) |

## 9. Migrations owned by this slice

Under `360_Flask_Appointment/migrations/versions/`: `20260723_charting.py` (base tables +
`chart_number_seq`), `20260724_chart_session_ownership.py`, `20260728_clinical_session_contract.py`,
`20260729_chart_audit_logs.py`, `20260730_chart_condition_options.py`,
`20260730_chart_procedures.py`, `20260730_add_more_conditions.py`,
`20260730_condition_affected_area.py`, `20260731_chart_procedure_{deletion,status,type}.py`,
`20260731_chart_templates.py`, `20260731_visit_type_names.py`,
`20260804_condition_{catalog_mapping,comments}.py`, `20260805_restore_condition_catalog.py`,
`20260806_chart_procedure_surface_scope.py`, `20260806_chart_session_auto_draft.py`,
`20260812_chart_settings.py`. `20260813_chart_perio_exams.py` belongs to `be-perio`.

The open-session partial unique index lives in `20260728_clinical_session_contract.py:111`
(clinical) and `20260724_chart_session_ownership.py:31` (edit-only, currently dead — see the
SKILL's Traps).

## 10. `src/api/charting.js` exports with no backend route

Seven exports in `PMS_React/src/api/charting.js` describe endpoints this blueprint does not
serve. With the chart API configured they 404; with `VITE_APP_BASE_URL_CHART` unset the module
falls back to **mock**, which is why they look like they work. Verified against the 17-route
`grep -nE "@charting_routes.route"` listing.

| export | line | claimed route |
|---|---|---|
| `updateChartSession` | `:570` | `PATCH /v2/charts/sessions/{id}` |
| `saveVisitNote` | `:599` | — |
| `addProcedure` | `:631` | — |
| `fetchChartCatalog` | `:1085` | — |
| `updateToothStatus` | `:1101` | — |
| `addToothEntry` | `:1128` | — |
| `removeToothEntry` | `:1145` | — |

Doc-comments in that file are proposed contract, not shipped contract. Before wiring one up,
add the Flask route first.
