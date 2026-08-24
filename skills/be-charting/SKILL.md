---
name: be-charting
description: Backend odontogram charting — chart sessions, chart procedures (TP/Cn/EC/EO), the condition and chart-template catalogs, per-clinic tooth-chart settings, and the in-process auto-draft scheduler. Use when changing charting_routes.py, chart_settings_routes.py or chart_session_scheduler.py, adding a /api/v2/charts/* or /api/v2/chart-settings endpoint, running tests/test_charting_*.py, or debugging session locking or autosign. Not perio — be-perio.
---

## Scope

The odontogram side of clinical charting: a `Chart` header, the `ChartSession` that owns edits to
it, the `ChartProcedure` rows it writes, notes/templates (`ChartSessionNotes` + `ChartTemplate`),
the condition catalog, tooth-chart settings, and the in-process job that drafts abandoned sessions.
**Perio is not here** — `chart_perio_routes.py` is `be-perio`; it hangs off a session this slice
created, never opening or closing one. Maturity **live** (`PMS_React/README.md:239`, `:269`).

## Files

| path | role |
|---|---|
| `360_Flask_Appointment/app/charting_routes.py` | **(entry)** blueprint `charting_routes`; 17 routes, validators, serializers, audit log. ~65KB / 1879 lines — `grep -nE "@charting_routes.route"` then `sed -n`, never read whole. Constants `:26`-`:62` are the authoritative enums. |
| `360_Flask_Appointment/app/chart_settings_routes.py` | blueprint `chart_settings_routes`; GET/PUT `/v2/chart-settings`. 241 lines, read whole — its comments are the tenancy record. |
| `360_Flask_Appointment/app/chart_session_scheduler.py` | 139 lines. Flask-APScheduler job `chart_session_auto_draft`. Wiring for all three lives in `be-platform`'s `__init__.py` at `:50,67` · `:51,68` · `:74` (`init_scheduler(app)`) — the easy thing to forget. |
| `360_Flask_Appointment/tests/` | `test_charting_sessions.py` (1117), `test_chart_procedures.py` (736), `test_chart_session_notes.py` (311), `test_conditions_catalog.py` (231), `test_chart_session_scheduler.py` (151), `test_charting_rules.py` (88). |

Touches, not owned: `app/models.py:551-880` (the eight `Chart*` models) and the revisions that
create them — both `be-data-model`'s, since `ownership.tsv` gives it every file under
`migrations/`; enumerated in `references/session-lifecycle.md` §9. `app/__init__.py` is
`be-platform`'s.

## Contract

All 19 routes carry `@require_api_and_bearer` (`app/util/decorators.py:206`) — `x-api-key` plus a
Bearer validated by a live HTTP call to Auth — and mount at `/api`. Under `/api/v2/charts`:

- `POST /chart-session` `:1206` open one, 409 + the existing session if any is open ·
  `/draft` `:1298` save the note, session → `draft` · `/resume` `:1606` `draft` → `active`
- `POST /chart-session/signed` `:1464` sign + close, **requires `active`** · `/autosign` `:1383`
  close unsigned, **requires `draft`** · `/template` `:1012` attach another visit-type note
- `GET /chart-session` `:1159` list by location+patient (`?status=`) · `/active` `:1124` the one
  active session · `/templates` `:1103` this session's notes
- `POST /chartprocedure` `:522` add one entry, **upsert/merge not insert** · `DELETE` `:674`
  soft-delete, planned `TP` only · `POST /chartprocedure/status` `:761` `P`/`R`/`C`/`D`
- `POST /chartprocedure/details` `:1745` edit the **administrative** fields only —
  `ucrFeeCents`, `providerId`+`providerName`, `chartDate`, `comments`, each applied only if its
  key is present; 400 on any identity field (`cdtCode`, `type`, `toothNumber`, `patientId`,
  `sessionId`, `clinicId`, `locationId`, `status`, `objectId`). **The one write that is NOT
  session-gated** — see Invariant 2
- `GET /chartprocedure` `:836` non-deleted entries for a patient · `/conditions` `:876`
  paginated catalog (`limit` ≤ 100) · `/chart-templates` `:902` all templates, and
  `POST /chart-templates` `:909`, which overwrites a **global** template body
- `chart_settings_routes.py`: `GET /api/v2/chart-settings` `:176` (the clinic row, or shipped
  defaults at 200) · `PUT` `:182` **full replace**, 422 unknown key, 400 partial body

Frontend: `PMS_React/src/api/{charting,chartingCatalog,chartSettings}.js` via `chartApi`, always
same-origin `/__chart_api/api` (`vite.config.js:57` + `vercel.json:9`, which change together).
Rendered by `src/components/patient-detail/charting/` (`ChartingContext.jsx`, `Odontogram.jsx`,
`ToothChartContext.jsx`, `ProcedureTable.jsx`, `SignNoteDialog.jsx`, `UnlockChartModal.jsx`) and
`settings/tooth-chart-defaults/ToothChartDefaultsPanel.jsx`.

## Invariants

1. Every route in both blueprints uses `@require_api_and_bearer` — never hand-roll auth, never
   add a route without it. Re-read the session with `.with_for_update()` **before** checking it,
   then mode, then status; every mutating route does, and one that does not is a race.
2. `active` is the only status accepting chart-procedure writes; `active`+`draft` the only ones
   accepting note writes. **One deliberate exception:** `POST /chartprocedure/details` accepts
   any session status, because fee/provider/date/note are administrative facts a practice must
   be able to correct on a signed encounter. It buys that with a mandatory
   `procedure_details_updated` audit row, and it cannot touch a clinical field. `signed`/`auto-sign` are terminal — no route reopens them. `POST
   /signed` requires `active`, `POST /autosign` requires `draft`; do not widen either.
3. Any route mutating a session must call `_touch_session:249` (else the scheduler auto-drafts
   it away under the clinician) and log via `_add_audit_log:328`. No silent edits.
4. One open (`active`|`draft`) clinical session per `(location_id, patient_id, provider_id,
   visit_type)` — `_open_session:305` **and** the partial index `uq_chart_sessions_open_clinical_owner_visit`. Change both or neither.
5. Never hard-delete a chart procedure: set `deleted_at`, bump `version`, and only when
   `type == "TP" and status == "P"`. `type` (`TP`/`Cn`/`EC`/`EO`) and `status` (`P`/`R`/`C`/`D`)
   are different axes — never map one onto the other.
6. Responses are `{"result","status","error"}` with HTTP code == `status`, timestamps are
   `{"_seconds","_nanoseconds"}`, and `chart_id` on `ChartProcedure`/`ChartAuditLog` is the
   zero-padded string from `_chart_code:268`, not `Chart.id`. The frontend parses exactly this.
7. `charting_routes.CLINIC_ID` and `chart_settings_routes.CLINIC_ID` are both `1`; they move
   together when real tenancy lands.

## Working here

1. `grep -nE "@charting_routes.route" app/charting_routes.py`, then `sed -n 'START,ENDp'`.
2. Adding a route: append to the existing module — the backend is flat, no new package. A new
   *blueprint* also needs an import + `register_blueprint` in `app/__init__.py`.
3. Adding a column: `app/models.py`, then `flask db migrate` + `flask db upgrade`; migrations are
   append-only. If it changes who may hold a session open, move the partial unique index in
   `migrations/versions/20260728_clinical_session_contract.py:111` with it.
4. Run the tests — the only automated coverage in the monorepo, and plain `unittest`, **not
   pytest** (pytest is not installed in `env/`, despite `CLAUDE.md` §1): ``` cd
   360_Flask_Appointment && ./env/Scripts/python -m unittest tests.test_charting_rules \
   tests.test_charting_sessions tests.test_chart_procedures tests.test_chart_session_notes \
   tests.test_chart_session_scheduler tests.test_conditions_catalog   # 83 tests, ~2.3s ``` Sqlite
   in-memory, `auth_get` and the bearer `requests.get` mocked. Each file builds its own bare
   `Flask` app with only the tables it needs — a new model must join that file's `setUpClass`.
5. Wire-shape changes: update `PMS_React/src/api/charting.js` (or `chartSettings.js`) in the
   same change; separate commits per repo, each naming the counterpart.

## Traps

- **The scheduler auto-closes** `active` sessions of mode `clinical_session`/`edit_only` whose
  `lock_heartbeat` is over 60 min old (`INACTIVITY_TIMEOUT:13`): `status = "draft"`,
  `auto_drafted = True`, note drafted, `session_auto_drafted` logged as `user_id = "system"`. It
  never signs. Off via `CHART_SCHEDULER_ENABLED=false`; skipped under `TESTING` and `flask db`.
- **It silently never starts under `FLASK_CONFIG=config.DevelopmentConfig`** — `init_scheduler:117`
  skips when `app.debug` and `WERKZEUG_RUN_MAIN != "true"`, but `run.py:8` passes
  `use_reloader=False`, so that var is never set (verified both ways). Conversely `Dockerfile:30`
  runs `gunicorn --workers 4`, so production runs **four** schedulers — safe only because
  `auto_draft_inactive_sessions` takes `with_for_update(skip_locked=True)` (`:39`). Keep that lock.
- **The edit-only uniqueness index is dead**: `20260724_chart_session_ownership.py:33` filters
  `mode = 'edit-only'` but the code writes `edit_only` (`charting_routes.py:49`) and no later
  migration fixes it — duplicate open edit-only sessions are blocked by `_open_session` alone.
- **`chart_settings_routes.py` has no tenancy** and its header comment says so: any authenticated
  user of any practice full-replaces clinic 1's row through the PUT — a cross-tenant *write*
  reachable from a settings screen. Resolve the clinic from `g.user.clinic_id`.
- **`POST /chart-templates` mutates the shared template for a visit type**, not the caller's copy, and no frontend calls it. An admin tool, not a save button.
- **Seven `src/api/charting.js` exports are proposed contract with no backend route** —
  `updateChartSession` (`PATCH /v2/charts/sessions/{id}`), `saveVisitNote`, `addProcedure`,
  `fetchChartCatalog`, `updateToothStatus`, `addToothEntry`, `removeToothEntry`: 404 when the
  chart API is on, **mock** when off. Doc-comments are not contract.
- **SQLite ignores `FOR UPDATE`/`skip_locked`**, so a green test run proves nothing about
  concurrency; `_next_chart_number:272`'s `MAX+1` fallback is likewise test-only. Session creation
  makes two live Auth calls (`_validate_external_references:212`, 502 when Auth is down) — mock `app.charting_routes.auth_get` in tests.

## See also

- `references/session-lifecycle.md` — status machine, per-route gate matrix, audit actions,
  serializer fields, procedure upsert rules, error map, full migration list.
- `main-architecture` (hub) · `be-perio` (`chart_perio_routes.py`, hangs off these sessions) ·
  `be-data-model` (`charts`/`chart_*` columns, the Alembic chain) · `be-platform` (registration,
  `require_api_and_bearer`, the gunicorn worker count that multiplies the scheduler) ·
  `fe-charting` (odontogram, per-tab `sessionStorage` lock) · `fe-settings` (Tooth Chart Defaults).
