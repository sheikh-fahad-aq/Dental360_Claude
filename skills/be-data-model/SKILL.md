---
name: be-data-model
description: The Flask persistence layer — app/models.py (38 SQLAlchemy tables) and the Alembic chain under migrations/versions/. Owns no HTTP routes. Use when adding or altering a column or table, running flask db migrate / flask db upgrade, looking up which model backs a table (appointment, lab_case, chart_sessions, chart_procedures, chart_perio_measurements, chart_settings), scoping clinic_id, or debugging a down_revision error.
---

## Scope

Every table in `360_Flask_Appointment` is declared in one flat module, `app/models.py` —
no per-feature model packages, and no other file in `app/` declares a `db.Model`. Schema
changes land here and in `migrations/versions/`; this skill owns both and **no HTTP
routes**. Query construction, serialization and authorization stay in the owning
blueprint's skill.

## Files

| Path | Role |
|---|---|
| `360_Flask_Appointment/app/models.py` | **(entry)** All 38 models, 1150 lines / 52 KB. `grep`/`sed -n` it — never read whole. |
| `360_Flask_Appointment/migrations/versions/` | 20 revisions, one linear chain. `20260804_condition_catalog_mapping.py` is 156 KB — always use a line range. |
| `360_Flask_Appointment/migrations/env.py` | Stock Flask-Migrate env. Does **not** set `render_as_batch`. |
| `360_Flask_Appointment/migrations/alembic.ini`, `script.py.mako`, `README` | Alembic scaffolding; untouched from the Flask-Migrate template. |

Touches, not owned (all `be-platform`): `app/extensions.py` — defines `db`/`migrate`, import
`db` from here or from `app`; `config.py` — `ProductionConfig` = Postgres (the real target),
`DevelopmentConfig` = `sqlite:///flask_app.db`; `app/util/decorators.py` (319 lines), where
`validate_api_key` reads `ApiKey` and `log_api_access` writes `APILog`. Full per-model table,
revision chain and blueprint→model map: `references/model-index.md`.

## Contract

**No routes.** Six domains consume these tables — appointments, visit lifecycle, labs,
recare/waitlist, charting, perio. The domain → tables → blueprint → frontend-module map
(verified with `grep -n "from app.models import" app/*.py`) is the last table in
`references/model-index.md`; the per-module model import list is above it. No frontend code
ever names a table.

## Invariants

1. **`flask db migrate` then `flask db upgrade` — never `db.create_all()`.** There is no
   `create_all` call in `app/`, `tests/`, `migrations/`, `run.py` or `config.py`. Keep it so.
2. **`migrations/versions/` is append-only.** Once a revision has been applied anywhere,
   never edit its `upgrade()`, its `revision` id, or its `down_revision`. Fix a bad
   migration with a new revision on top.
3. **Edit `app/models.py` first, then `flask db migrate`.** `env.py` autogenerates off the
   live `db` metadata. Always read the generated file before upgrading — autogenerate
   drops server defaults and misses Enum changes.
4. **Cite the revision *id*, not the filename, in `down_revision`.** They differ:
   `20260728_clinical_session_contract.py` declares `revision = "20260728_session_contract"`.
5. **One head, one line.** Strictly linear from `20260723_charting` (`down_revision = None`)
   to `20260813_chart_perio_exams`. Two heads means you appended to a stale one.
6. **`clinic_id` is caller-supplied, not derived from the token** — routes read it from
   `request.args`/body (`app/appointments_v2_routes.py:216`, `app/lab_cases_v2_routes.py:432`),
   so the column is not a security boundary by itself. Every query over a clinic-scoped
   table needs an explicit `.filter(Model.clinic_id == clinic_id)`. 15 models declare one:
   `grep -n "clinic_id = db.Column" app/models.py`.
7. **`chart_settings` is one row per clinic**, enforced by `uq_chart_settings_clinic_id`
   (`models.py:858`). Upsert, never insert a second. No row is valid — it means defaults.
8. **The charting schema has no foreign keys, by design.** Children store the parent's
   opaque string (`ChartSession.object_id` into `session_id`, `ChartPerioExam.object_id`
   into `exam_id`) and the route enforces the link. Do not add a `db.ForeignKey` or an
   `ON DELETE CASCADE` to a `chart_*` table without changing that convention wholesale.
9. **Deletes on `chart_procedures` and `chart_perio_exams` are soft** — set `deleted_at`
   (`models.py:747`, `models.py:1000`). Every read path must filter it out.
10. **Never store a derived clinical value.** `ChartPerioMeasurement` has no CAL column on
    purpose (CAL = pd + gm, computed on read). Do not add one.
11. **Log tables are insert-only history, not state**: `lab_case_status_log` (documented
    immutable at `models.py:353`), `appointment_workflow_logs`,
    `appointment_tracking_status_log`, `chart_audit_logs`, `api_logs`.
12. **Never log a model instance or a row dict.** These tables hold PHI — `patient_name`,
    `patient_phone`, `web_appointment_form_data.patient_dob`, every note body. CLAUDE.md §7.1.

## Working here

1. Locate the model: `grep -nE "^class .*db\.Model|^\s+__tablename__" app/models.py`, then
   `sed -n 'START,ENDp'`. Do not open the file whole.
2. Edit the column in `app/models.py`. Put constraints in `__table_args__` in the model
   too, not only in the migration, or the next autogenerate will try to re-add them.
3. `cd 360_Flask_Appointment && flask db migrate -m "short reason"`.
4. **Read the generated file.** Add the `down_revision` if autogenerate guessed, drop
   spurious `op.drop_index`/`op.alter_column` noise, and backfill existing rows with an
   `op.execute` before flipping a column to `nullable=False` — that is the pattern used at
   `migrations/versions/20260728_clinical_session_contract.py:38-40`.
5. `flask db upgrade`. Confirm with `flask db current`.
6. If the new table needs an endpoint, that is the owning blueprint's skill plus the
   `register_blueprint` line in `app/__init__.py` (CLAUDE.md §4.2) — not this skill.
7. Run the suite with **`unittest`, not pytest** — pytest is installed nowhere in this
   workspace (`./env/Scripts/python -m unittest discover tests` from
   `360_Flask_Appointment`). Those seven files (all charting/perio) are the only automated
   coverage touching these models; nothing tests the appointment tables.

## Traps

- **Only 10 of 38 tables are Alembic-managed.** The chain starts at `20260723_charting`
  and creates the `charts`/`chart_*` tables only. Everything appointment-, lab-, recare-
  and waitlist-shaped pre-dates Alembic here: its DDL exists only in the deployed database.
  Altering one of those models still needs a hand-written migration — autogenerate has no
  baseline for them and will happily emit `op.create_table` for a table that already exists.
- **`chart_session_notes` is created by no migration.** `20260723_charting.py:72` creates
  `chart_notes`; `models.py:613` declares `__tablename__ = "chart_session_notes"` and no
  revision renames it. A database built purely from the chain will 500 on every note write.
- **`20260805_restore_condition_catalog.py:82` raises `NotImplementedError` in
  `downgrade()`.** `flask db downgrade` past that point is impossible by design — restore
  from a backup instead.
- **`flask db upgrade` does not work on the sqlite dev config.** Four revisions are
  Postgres-only and `env.py` sets no `render_as_batch`, so sqlite `ALTER` fails too.
  Develop against Postgres.
- **`Appointment` has no `__tablename__`** (`models.py:26`), so its table is the singular
  `appointment` while most siblings are plural. Raw SQL gets this wrong constantly.
- **`app/util/decorators.py` references undefined `Role` and `Dashboard`** at lines 220,
  248 and 288 — neither class exists in `models.py`. `validate_user_role`,
  `validate_user_dashboard` and `log_api_access` will raise `NameError` if ever applied.
  The live decorator is `require_api_and_bearer` (:206); use only that.
- **`recare_type.name` is globally unique with no `clinic_id`** (`models.py:376`) — adding
  a recall type for one clinic exposes it to all of them.
- **`chart_conditions` is maintained by data migrations, not an admin API.** Three
  revisions bulk-insert or rewrite its rows; a manual `UPDATE` will be clobbered by the
  next one.

## See also

- `main-architecture` — the index and change log.
- `be-appointments`, `be-visit-lifecycle`, `be-lab-cases`, `be-recare-waitlist`,
  `be-charting`, `be-perio`, `be-dashboard` — the blueprints that own the queries.
- `references/model-index.md` — all 38 models with purposes, the full revision chain, and
  the blueprint→model map.

## Per-patient tooth chart dentition

`patient_chart_dentition` (`app/models.py`, migration `78ab66d417c9_per_patient_tooth_chart_dentition`,
down_revision `20260827_chart_completed_date`) — one row per `(clinic_id, patient_id)` holding
`adult` | `primary` | `mixed`, CHECK-constrained, plus `updated_by`.

**A MISSING ROW IS THE NORMAL CASE** and means "no override, use the practice default"
(`chart_settings.default_dentition`, which may itself be `age-based`). Clearing an override
DELETES the row rather than writing a sentinel, so "no answer" has exactly one representation —
which is also why `age-based` is not a member of the CHECK.

Its own table rather than a column on `charts`, because `charts` is **not** a per-patient header:
`create_chart_session` writes a NEW `Chart` row per session, keyed by provider and visit type, so
a column there would record one clinician's answer for one visit. Same clinic-scoping caveat as
`chart_settings` — `CLINIC_ID` is hardcoded to 1 until real tenancy lands.

Note `chart_procedures.tooth_number` and `treatment_plan_items.tooth_number` are both
`String(20)` with no CHECK, which is why primary teeth (`"A"`-`"T"`) store with no schema change.
`chart_perio_measurements.tooth_number` is the exception: `SmallInteger` with
`ck_chart_perio_measurements_tooth_number` (1-32), so **perio is permanent-only at the database
level** and widening it is a migration, not a frontend change.
