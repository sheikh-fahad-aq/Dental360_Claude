# Perio payload reference

Companion to `be-perio`. Everything here is checked against
`360_Flask_Appointment/app/chart_perio_routes.py` (1981 lines) and
`PMS_React/src/api/chartPerio.js` (1175 lines) at the line numbers shown.

## 1. Exam settings (`EXAM_FIELDS:140`)

| key | required on POST | default when absent | validator | editable by PATCH |
|---|---|---|---|---|
| `sessionId` | yes | — | non-empty string (`:657`) | no — re-pointing an exam would move readings between encounters |
| `providerId` | no | `session.provider_id` | `_positive_int` | yes (explicit `null` is refused — `provider_id` is NOT NULL) |
| `examDate` | no | today, UTC midnight | `_exam_date:307` | no — read-only in the Edit dialog |
| `toothNavigationScript` | **yes** | none; absent is a 400 | `_tooth_navigation_script:233` | yes |
| `mouthNavigationScript` | **yes** | none; absent is a 400 | `_mouth_navigation_script:247` | yes |
| `skipConditions` | no | `[]` | `_skip_conditions:261` | yes (`null` clears) |
| `bopSupDelay` | no | `0` | `_bounded_int` 0-16 | yes |
| `includePlaqueCalculus` | no | `false` | `_strict_bool:202` | yes |
| `skipHardPalateForMgj` | no | `true` | `_strict_bool` | yes |

`EXAM_EDITABLE_FIELDS:164` is those seven, in the dialog's field order — which is also the order the
audit row lists changes in. `EXAM_READ_ONLY_FIELDS:173` is the complement; sending one to PATCH is a
422 with a *different* message from an unknown key ("cannot be edited" vs "Unknown field(s)").

Navigation scripts: the five built-ins in `TOOTH_NAVIGATION_SCRIPTS:72`
(`pocket-depth`, `gingival-margin`, `pocket-depth-gingival-margin`, `mucogingival-junction`,
`pocket-depth-mucogingival-junction`), the six in `MOUTH_NAVIGATION_SCRIPTS:79` (`a`-`f`), plus any
id starting `custom-tooth-` / `custom-mouth-` (`:85-86`) up to 64 chars. Script *bodies* live
client-side; the exam records only which script was used. A typo in a built-in id ("pocket_depth")
is still a 400 — it is not silently accepted as a custom id.

`skipConditions` tokens (`PERIO_SKIP_CONDITIONS:106`): `crown`, `impacted-distal`, `impacted-mesial`,
`implant`, `implant-crown`, `missing`, `pontic`, `unerupted`. Duplicates are a 400, not de-duped.
**Recorded, never acted on** — see the trap in `SKILL.md`.

## 2. Measurement items (`MEASUREMENT_FIELDS:185`)

`POST .../measurements` takes `{"measurements": [ … ]}` — non-empty, ≤ `MEASUREMENTS_MAX:138` (256),
which is 32 teeth × 6 sites + 32 per-tooth rows = 224 plus headroom. Any other top-level key is 422.

Every item carries `toothNumber` (1-32). `site` decides the shape:

**Site row** — `site` in `MB B DB ML L DL` (`PERIO_SITES:88`), fields `SITE_MEASUREMENT_FIELDS:176`:

| field | type | bound | absent means |
|---|---|---|---|
| `pd` | int or null | 0-20 | not recorded (NULL) |
| `gm` | int or null | **-20-20, signed** | not recorded |
| `mgj` | int or null | 0-20 | not recorded |
| `bop` `sup` `plaque` `calculus` | strict bool | — | `false` |

**Per-tooth row** — `site: null`, fields `TOOTH_MEASUREMENT_FIELDS:177`:

| field | type | bound | absent means |
|---|---|---|---|
| `present` | strict bool | — | `true` |
| `implant` | strict bool | — | `false` |
| `mobility` | int or null | 0-3 | not recorded |
| `boneLoss` | int or null | 0-20 | not recorded |
| `furcation` | object or null | `{B\|L\|M\|D: 0-4}` | not recorded |
| `note` | string or null | ≤2000 chars (`NOTE_MAX_LENGTH:133`) | not recorded |

Rules the validators enforce (`_measurement_values:1109`):

- A per-tooth field on a site row, or a site field on a per-tooth row, is a **422** naming the
  misplaced field — not a silent drop.
- `cal` is the key clients try hardest to send; it is unknown and therefore 422. `_cal:384` computes
  `pd + gm` on every read and there is deliberately no column.
- `_strict_bool:202` accepts a real JSON boolean only — no `"true"`, no `1`.
- `_optional_bounded_int:225` keeps `null` distinct from `0`: an unprobed site and a 0 mm reading
  are different clinical facts.
- A repeated `(toothNumber, site)` inside one request is a **400** (`:1220`). Across requests the
  same key is an intentional overwrite, enforced by
  `uq_chart_perio_measurements_exam_tooth_site` plus the partial index
  `uq_chart_perio_measurements_exam_tooth_null_site` (`models.py:1099-1116`).
- Writes are a **full row replace** (`_apply_measurement:1084`), never a patch.

Read-back adds `cal`, `dateCreated`, `lastUpdated` (`_serialize_measurement:399`) and sorts by
`_measurement_sort_key:464` — the tooth's own row first (`site` NULL sorts to -1), then its sites in
`PERIO_SITES` order.

## 3. Carry-forward column split (`:1322-1363`)

`POST .../finalize` with `{"carryForwardPrevious": true}` copies from
`_previous_finalized_exam:1366` — the patient's most recent `status == 'final'`, non-deleted exam
strictly *earlier by `exam_date`* (row id breaks a same-day tie), **ignoring `location_id`**.

| tuple | columns | used when |
|---|---|---|
| `CARRY_FORWARD_NULLABLE_COLUMNS:1322` | `pd gm mgj mobility bone_loss furcation` | source set |
| `CARRY_FORWARD_FLAG_COLUMNS:1335` | `bop sup plaque calculus present implant` | whole-row copies only |
| `CARRY_FORWARD_EXCLUDED_COLUMNS:1353` | `note` | **never**, by either branch |
| `CARRY_FORWARD_GAP_FILL_COLUMNS:1354` | nullable − excluded | row already exists → fill only its NULLs |
| `CARRY_FORWARD_WHOLE_ROW_COLUMNS:1359` | (nullable + flags) − excluded | row absent → copy whole |

`note` is excluded because it is a dated narrative, not a reading: re-filing last visit's sentence
under today's signed exam manufactures a clinical assertion nobody made. Flags are never carried
onto an existing row because `False` cannot be told from "not recorded". `_carried_value:1496` deep-
copies `furcation` so two exams never share one dict.

Outcomes: no previous exam → finalize still **succeeds**, audit says nothing was carried
(`:1592-1596`). Closed session + carry-forward → **409** (`:1572`); a plain finalize on the same closed
session succeeds.

`GET /v2/charts/perio-exam/<id>` publishes the source the server *would* use as
`previousFinalizedExamId` / `previousFinalizedExamDate` (`_previous_source_fields:1402`). It is on
the single read, not the list, to avoid an N+1 on the perio tab's landing view.

## 4. Status / error map

Envelope is charting's `{result, status, error}` (`_response:190`); the HTTP status is mirrored into
the body.

| status | when |
|---|---|
| 400 | bad JSON body, missing `sessionId`/`examId`/`patientId`, any validator `ValueError`, empty or oversized `measurements`, duplicate `(tooth, site)` in one request |
| 401 | no `x-api-key` / no Bearer (`decorators.py`), or no resolvable `_current_user_id` |
| 403 | invalid API key or Bearer rejected by Auth |
| 404 | exam missing or soft-deleted (`_live_exam:556`), session missing, chart missing for session |
| 409 | session not open; second exam on the same patient-day; status refusal (finalized/void/already-void/draft-void); carry-forward on a closed session; measurement `IntegrityError` ("changed by someone else. Reload and try again.") |
| 422 | unknown key at any level; PATCH of a read-only field; non-empty `reopen`/`void` body; unknown key in a `finalize` body |

The duplicate-day 409 has one sentence shared by the pre-check and the `IntegrityError` race
(`_duplicate_exam_message:631`), so both read identically.

## 5. Audit rows

`_add_audit_log(session, chart, user_id, action, details)` — imported from `charting_routes.py`.
Every detail opens with `_exam_audit_subject:501` = `Perio exam <objectID> (exam date <YYYY-MM-DD>)`,
so a row is recognisable months later without a join.

| action | line | detail carries |
|---|---|---|
| `perio_exam_started` | `:753` | 0 rows, both script ids, `skipHardPalateForMgj` |
| `perio_exam_updated` | `:1072` | `field before -> after; …` in `EXAM_EDITABLE_FIELDS` order (plus derived `providerName`) |
| `perio_measurements_saved` | `:1291` | added / updated / submitted counts + total rows now |
| `perio_exam_finalized` | `:1631` | row count + carry-forward clause |
| `perio_exam_reopened` | `:1756` | source status; un-voiding is spelled out |
| `perio_exam_voided` | `:1859` | "a SIGNED exam was annulled", signed-at, rows retained |
| `perio_exam_deleted` | `:1966` | draft vs FINALIZED, rows retained, soft/recoverable |

Whenever the session is closed, `_session_closed_clause:510` is appended so the relaxed gate is
visible on the record rather than invisible.

## 6. Frontend mirror points

Change one of these and the counterpart must move in the same pair of commits (one per repo).

| backend | frontend |
|---|---|
| `EXAM_FIELDS:140` | `PERIO_EXAM_FIELDS` `chartPerio.js:80` |
| `EXAM_EDITABLE_FIELDS:164` | `PERIO_EXAM_EDITABLE_FIELDS:102` |
| `PERIO_EXAM_STATUSES:116` | `PERIO_EXAM_STATUSES:128` |
| `PERIO_SITES:88` | `PERIO_SITES:136` |
| `SITE_MEASUREMENT_FIELDS:176` | `PERIO_SITE_FIELDS:139` |
| `TOOTH_MEASUREMENT_FIELDS:177` | `PERIO_TOOTH_FIELDS:142` |
| `FURCATION_ENTRANCES:117` | `PERIO_FURCATION_ENTRANCES:145` |
| bounds `:119-138` | `PERIO_BOUNDS:160` (furcation **0-4**), `PERIO_NOTE_MAX_LENGTH:179` |
| `TOOTH_/MOUTH_NAVIGATION_SCRIPTS:72,79`, `PERIO_SKIP_CONDITIONS:106` | `perio/perioExamDefaultsConstants.js` |

Body assembly is `toPerioMeasurementBody:558` — it rebuilds each item key by key rather than
forwarding UI state, precisely because a stray `cal` 422s the whole batch. Reads go through
`normalizePerioExam:442` / `normalizePerioMeasurement:327`, which return `null` for junk instead of a
half-populated row and never turn a missing number into `0`.

## 7. Tests

`tests/test_chart_perio_exams.py` — 61 `unittest.TestCase` methods on sqlite with Auth mocked
(`_validate_bearer:76`). Notable clusters: same-day duplicate rules (`:224-282`), UTC-midnight
pinning and future tolerance (`:242-313`), bulk write and computed CAL (`:315-370`), the
void/reopen round trip (`:582-762`), delete of a void exam (`:763-791`, `:1474`), carry-forward gap
semantics (`:998-1343`), and the picker's field contract (`:1533`).

Run: `python -m pytest tests/test_chart_perio_exams.py` from `360_Flask_Appointment`.
