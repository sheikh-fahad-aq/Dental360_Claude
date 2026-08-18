# fe-perio — the measurement model in detail

Companion to `fe-perio/SKILL.md`. Everything here is verified against the working tree.
Paths are relative to `PMS_React/src/`; `perio/` = `components/patient-detail/charting/perio/`.

---

## 1. Two row shapes, one discriminator

The exam holds a flat list of measurement rows. `site` decides which shape a row is —
`api/chartPerio.js:327` (`normalizePerioMeasurement`) is where that fork lives.

| | `site: null` — per TOOTH | `site: 'MB' … 'DL'` — per SITE |
|---|---|---|
| Constant | `PERIO_TOOTH_FIELDS` (`chartPerio.js:142`) | `PERIO_SITE_FIELDS` (`chartPerio.js:139`) |
| Fields | `present`, `implant`, `mobility`, `boneLoss`, `furcation`, `note` | `pd`, `gm`, `mgj`, `bop`, `sup`, `plaque`, `calculus` |
| Rows per mouth | 32 | 32 × 6 = 192 |
| Store key | `` `${tooth}:tooth` `` | `` `${tooth}:MB` `` |

A full mouth is 224 rows — under the server's `MEASUREMENTS_MAX = 256`
(`chartPerio.js:186`), which is why `savePerioMeasurements` chunking never fires in practice.

Sending a field from the wrong list is a 422. `normalizePerioMeasurement` returns `null` for a
row whose `toothNumber` is outside 1–32 (a row that cannot be placed cannot be shown) and
uppercases/validates `site` against `PERIO_SITES`.

**Defaults that matter.** `present` defaults to **true** on every per-tooth row, so a row
existing proves nothing. `perioMeasurementsHaveRecordedValues` (`chartPerio.js:400`) is the
"has anybody typed into this exam" test the Finish dialog uses to decide whether to offer
carry-forward; it treats only an explicit `present === false` as a finding, and tests sites with
`!= null && !== false` so a **PD of 0 counts as a reading**.

### `cal` is derived

`perioCal(pd, gm) = pd + gm`, `null` unless both exist (`chartPerio.js:312`). The server sends
`cal` and it is **recomputed anyway**, so the grid shows the same number after a keystroke as
after a reload. `cal` is absent from `PERIO_SITE_FIELDS`, is never sent, and the CAL cell
(`PerioComputedCell`, `perio/PerioSiteInput.jsx:168`) is read-only.

### Bounds

`PERIO_BOUNDS` (`api/chartPerio.js:160`) is the wire authority:

| field | range | note |
|---|---|---|
| `toothNumber` | 1–32 | Universal/ADA |
| `pd`, `mgj` | 0–20 mm | |
| `gm` | −20–20 mm | **signed** — negative = margin coronal to the CEJ, positive = recession |
| `mobility` | 0–3 | |
| `boneLoss` | 0–20 | but the UI scale is 4 bands — see §5 |
| `furcation` | 0–4 | five grades; no server CheckConstraint behind it |
| `bopSupDelay` | 0–16 | teeth, not seconds |
| `note` | ≤ 2000 chars | `PERIO_NOTE_MAX_LENGTH` |

Mirrors live in `perio/perioExamDefaultsConstants.js`: `PERIO_MEASURE_BOUNDS` (:1261),
`PERIO_GRADE_BOUNDS` (:1438), `PERIO_FIELD_BOUNDS` (:1455). A mirror that is **tighter** than the
wire is silent data loss on read-modify-write, because the server already holds the wider value
and a UI with no option for it rewrites the reading. Move the wire bound first.

---

## 2. Sites, faces, and the mesial/distal flip

Six sites, three per face (`chartPerio.js:136`, ordered as the server sorts them):

```
buccal / facial : MB  B  DB
lingual / palatal: ML  L  DL
```

`PERIO_SITE_FACE` (`perio/perioGridModel.js:75`) maps code → `'buccal' | 'lingual'`.
Two spellings coexist: lowercase UI ids in `perioExamDefaultsConstants.js` (`PERIO_SITES` at
:1022, objects with `id`/`code`) and the uppercase wire codes in `perioGridModel.js` /
`api/chartPerio.js`. `toSiteCode()` (`perioGridModel.js:60`) is the **only** crossing —
a stray `toUpperCase()` at a call site produces store keys nothing reads (`3:mb` vs `3:MB`).

**Screen order.** Mesial always points at the midline. `isMirroredTooth(n)` is teeth **9–24**
(`perioExamDefaultsConstants.js:1072`); unmirrored teeth read D·B·M left-to-right, mirrored read
M·B·D. `perioSiteOrderFor(toothNumber, face)` (`perioGridModel.js:98`) owns the flip; nothing
re-derives it. `siteHeaderLetter` / `perioSiteLetterTriple` build the header from the same answer.

**Furcation entrances** (`FURCATION_ENTRANCES`, `perioExamDefaultsConstants.js:1205`) exist only
on molars 1-3/14-16 (maxillary), 17-19/30-32 (mandibular) and premolars 5 and 12. Teeth with
none are **absent from the map**, so `FURCATION_ENTRANCES[n]` is falsy — use
`hasFurcationEntrances(n)` / `furcationEntrancesFor(n, face)`. Grades are per entrance
(`{ B: 0, M: 2, D: 1 }`), and `readFurcation` (`chartPerio.js:296`) drops out-of-range entries
and returns `null` when nothing was graded.

**Sextants** (`PERIO_SEXTANTS`, `perioGridModel.js:512`) exist for the BOP/Sup all-teeth modal:
upper-right, upper-anterior, upper-left, lower-left, lower-anterior, lower-right; the two
anterior sextants carry **two groups** each so the letter triples read correctly either side of
the midline. `perioSextantForTooth(n)` picks the opening tab.

---

## 3. What the grid draws

`perioVisibleRows(measures, { includePlaqueCalculus })` (`perioGridModel.js:136`) returns the
rows for the exam's tooth script, top to bottom, each with a `kind`:

| kind | rendered as | rows |
|---|---|---|
| `site` | editable number, one per site | PD, GM, MGJ |
| `computed` | read-only, one per site | CAL |
| `flag` | toggle, one per site | BOP, Sup, Plaque, Calculus |
| `tooth` | one control per tooth column | Furc, BLoss, Mob |
| `graph` | the pocket-depth plot band | — |

Conditional rows: **CAL only when both `pd` and `gm` are measured**; the **graph band only when
`pd` is measured**; **Plaque/Calculus only when the exam set `includePlaqueCalculus`**. An
unknown measure id contributes nothing rather than throwing, so a custom script cannot take the
panel down.

`PerioChartGrid.jsx` is a **single `overflow-x-auto` scroller** with sticky label rails; per-row
scrollers would let the buccal and lingual rows for one tooth sit at different offsets.
SimpleBar is deliberately not used. There is **no `role="grid"`** — the layout puts a midline
divider between cells, so every cell instead carries a full sentence as its accessible name
(built in `perio/perioGridLabels.js`, e.g. "Tooth 3 buccal mesial probing depth") and arrow
movement is implemented by hand. Cells use a native `title`, never the house `Tooltip` —
200 tooltip instances is 200 portals on a surface being typed into.

---

## 4. Keyboard and keypad entry

**Three surfaces, one writer.** Grid cell, keypad key and the ▲/▼ steppers all end in the
context's mutations (`setSite`, `toggleFlag`, `setToothField`, `setFurcation`), which validate
bounds, refuse `cal` by name and toast every refusal.

**Grid keys** (`PerioChartGrid.jsx:206`, one delegated handler on the container):

- `Enter` / `Shift+Enter` — next / previous cell in DOM order.
- `ArrowUp` / `ArrowDown` — same tooth **and** same site in the target row where one exists,
  falling back to the same tooth, so stepping from a 3-cell site row into a 1-cell per-tooth row
  does not jump columns.
- `ArrowLeft` / `ArrowRight` are **deliberately not intercepted** — they move the caret inside a
  numeric input, and stealing them makes a mistyped "12" uncorrectable without the mouse.

**Typed values** hold a local draft (`PerioSiteInput`, regex `/^-?\d{0,2}$/`) because `gm` is
signed and the intermediate string `"-"` must not commit. An empty field commits `null`, which
genuinely un-records the reading. Advance is by `shouldAdvanceImmediately(rawText, field, bounds)`
(`perioGridModel.js:400`): advance once the value provably cannot grow — `value >= limit`, or
`value * 10 > limit`, where `limit` is `|min|` for a negative and `max` otherwise. A field with
no bound never auto-advances. **No timers** are involved.

**Keypad** (`perio/PerioEntryPanel.jsx`) has two pages — `units` (0-9) and `teens` (10-19),
`PERIO_KEYPAD_PAGES` at `perioExamDefaultsConstants.js:1540`. Every key is a **whole value**, so
12 mm is one press and `commitAdvance(…, { whole: true })` steps immediately. `perioKeypadPagesFor`
hides the teens page for a 0-3/0-4 grade field (every key would be dead). Keypad buttons cancel
the mousedown that would blur the focused cell — the operator has a probe in the other hand.
Nothing advances off a per-TOOTH target; a tooth column has no next site.

**Focus route.** `perioVisitOrder(passes)` (`perioGridModel.js:202`) is one stop per SITE;
`perioFieldVisitOrder(passes, toothScript)` (:326) expands each site stop over the script's
measures **in the script's declared order** (not the grid's paint order), giving one stop per
CELL. The context publishes both: `moveFocus`/`visitOrder` and
`moveFieldFocus`/`advanceField`/`retreatField`/`commitAdvance`/`fieldVisitOrder`.

---

## 5. Grades and pick-lists

All in `perio/perioExamDefaultsConstants.js`, all option lists over `PERIO_BOUNDS`:

- `MOBILITY_GRADES` (:1307) — 0 None, I <1 mm horizontal, II >1 mm horizontal, III horizontal +
  vertical/depressible.
- `FURCATION_GRADES` (:1342) — **labels are verbatim, never paraphrase**: 0 None ·
  1 "Probe root indentation" · 2 "Penetrates into furcation" · 3 "Through furcation - soft
  tissue" · 4 "Furcation open, void of soft tissue". The 3-vs-4 split decides treatability.
  `0` is a real recorded answer ("probed, not involved"); blank means nobody looked.
- `BONE_LOSS_GRADES` (:1373) — four bands: None / Mild / Moderate / Severe. **The wire still
  allows 0-20** (`BONE_LOSS_WIRE_MAX`, :1384). A value of 4-20 read back from an older build has
  no option in the list; render it as its bare numeral (`perioGradeOption` returns `null`, which
  is the signal). **Never clamp it into 0-3.**
- `PERIO_GRADE_SCALES` (:1391) maps `field` → scale so the grid looks options up by the string it
  already holds.

---

## 6. Navigation scripts and passes

Two per-exam choices, both fixed at creation and both editable afterwards via PATCH.

**Tooth navigation script** — which measurements are prompted at each site, in what order.
`TOOTH_NAVIGATION_SCRIPTS` (:62): `pocket-depth` (`pd`), `gingival-margin` (`gm`),
`pocket-depth-gingival-margin` (`pd`,`gm`), `mucogingival-junction` (`mgj`),
`pocket-depth-mucogingival-junction` (`pd`,`mgj`).

> `gm` and `mgj` are **not** synonyms. `gm` is the gingival margin read against the CEJ (signed;
> combines with PD to give CAL, which stages periodontitis). `mgj` is the mucogingival junction,
> a separate landmark giving keratinized-tissue width. Merging the two scripts destroys either
> CAL or KT width.

**Mouth navigation script** — the route round the arches. `MOUTH_NAVIGATION_SCRIPTS` (:186),
six built-ins `a`–`f`, each a list of `{ order, pass, scope, direction }` over
`upper-facial | upper-lingual | lower-facial | lower-lingual`, `arch | right | left`,
`ltr | rtl`.

`resolvePasses(mouthScript, toothScript, customs, options)` (:515) is the algorithm: it drops a
pass the tooth script cannot read on that surface (`readableSurfacesFor`, `MEASURE_PASS_CAPABILITY`)
— e.g. `skipHardPalateForMgj: true` removes the upper-lingual pass from an MGJ-only exam, because
there is no mucogingival junction on the palate. `MouthNavigationDiagram` renders
`resolvePasses(...)`, never `script.passes`, which is why the pictures change when the tooth
script changes.

Custom scripts: `resolveToothScripts` / `resolveMouthScripts` merge the practice's lists with the
built-ins; `createCustomToothScriptDraft` / `createCustomMouthScriptDraft` ship `id: null`
because only a server can mint a stable id, and **there is no persistence for them** — they live
in `PerioChartPanel`'s `customScripts` state for the session. The editor dialogs in
`perio/PerioScriptEditors.jsx` have **no caller**; existing custom scripts still resolve and
render, they just cannot be created any more.

---

## 7. Exam lifecycle and the save/finalize boundary

```
                    createPerioExam
                          │
                          ▼
   cancelExam ◄────── [ draft ] ──finalize──► [ final ] ──void──► [ void ]
   (soft delete)          ▲                      │                   │
                          └────── reopen ────────┴─── reopen ────────┘
```

`PERIO_EXAM_STATUSES = ['draft', 'final', 'void']` (`chartPerio.js:128`).

- **draft** — the ONLY status that accepts measurement writes.
- **final** — signed; measurements 409. Delete is allowed (and offered) only when the row was
  created today.
- **void** — annulled but retained; appears in the picker marked void. Measurements, finalize, a
  second void **and delete** are all 409. `reopen` is the one write it accepts and takes it back
  to `draft`. **Void is reversible** — code that assumes it is terminal is out of date.

`normalizePerioExam` (`chartPerio.js:442`) **never defaults to `'draft'`**: an unrecognised status
passes through verbatim so every `=== 'draft'` test fails closed. `measurements` is `null` when
the response carried none (the LIST endpoint) and an **array** when it did (detail / bulk save) —
including `[]` for a started-but-unprobed exam. A state engine must not blank a full grid because
a list refresh came back without rows.

### Autosave flush (`perio/PerioExamContext.jsx`)

- Debounce 800 ms, max wait 5000 ms, at most 4 send-turns per flight (:113-126).
- `pendingRef` is a Set of **keys**; a failed flush re-queues keys, not values, so the next flush
  re-reads the rows as they are then.
- `inFlightRef` is the single-flight mutex; `flush()` awaits a running flight.
- A failed flush **toasts and parks the readings** — it never drops them. A perio flush losing
  rows is invisible, unlike a ledger row.
- `adoptExamEnvelope` (:358) merges only version/status/timestamps/count, and only when
  `saved.examId === current.examId`. The measurement rows in the bulk-save response are
  **deliberately discarded**: they are a snapshot from before whatever the operator typed while
  the request was in flight.
- `loadExam` flushes first and **abandons the load** if the flush fails, rather than overwriting
  readings the operator believes are recorded.

### Finalize

`finalize()` = flush → `POST …/finalize` → adopt. `PerioChartPanel.handleFinish` awaits `flush()`
itself and stops on `{ ok: false }` **before opening the dialog**, so the operator is never asked
an irreversible carry-forward question that is then refused.

`carryForwardPrevious` must be a **real boolean** (`chartPerio.js:990`) — the server's
`_strict_bool` 400s a coerced value. It is only offered when
`perioMeasurementsHaveRecordedValues()` is false, and because it **writes readings server-side**
the panel reloads afterwards.

### The four round-trip actions

Edit settings, carry-forward finalize, reopen and void all change the server's copy in a way the
context cannot derive, so each ends in `loadExam()`. `committedChange` in `PerioChartPanel` holds
the change the server already accepted so a retry retries the **reload**, not the mutation
(which would 409). Editing settings needs no such guard: a no-op PATCH is a 200.

### Manage menu gate

`wasCreatedToday(dateCreated)` (`PerioChartPanel.jsx:184`) — the operator's **local** calendar day,
computed in one place, re-armed by a timeout aimed one second past midnight. It is `dateCreated`,
not `examDate`: the rule is "you can still fix what you just entered", a fact about the
keystrokes, so a paper chart backdated to last month but keyed in this afternoon is still
correctable. An unreadable timestamp fails to "not today" — the Void branch, which annuls rather
than destroys.

Refusal sentences are exported from `PerioExamContext.jsx:157-164`
(`PERIO_START_EXAM_REASON`, `PERIO_LOCKED_DRAFT_REASON`, `PERIO_FINALIZED_REASON`,
`PERIO_VOIDED_REASON`, `PERIO_UNKNOWN_STATUS_REASON`) so the banner, the keypad hint and the
toasts say the same thing. **They name real menu items** — remove Reopen from the menu and two of
these strings become lies.

---

## 8. Context surface

`PerioExamProvider` is mounted by `PerioChartPanel` with `key={patientId}`, so no reading can
survive into another patient's chart. Props: `locked` (from `charting.isReadOnly`), `sessionId`,
`patientId`, `providerId`, `providerName`, `customToothScripts`, `customMouthScripts`.

Three hooks:

- `usePerioExam()` — the full value (throws outside the provider).
- `usePerioExamActions()` — the mutation half only, so a cell keeps its handlers across a
  keystroke. `setSite`, `toggleFlag`, `focusCell` are built from refs and **never change identity**
  for the life of the provider; putting them in the same object as `measurements` made them look
  new to all ~200 memoised cells.
- `usePerioExamOptional()` — returns `null` outside the provider, for shared toolbars.

The value carries: `exam`, `examId`, `status`, `patientId`, `sessionId`, `canEdit`,
`readOnlyReason`, `loading`, `error`, `saving`, `saveError`, `hasUnsavedChanges`, `measurements`
(a `Map`), `getSite`, `getTooth`, `focusedCell`, `focusCell`, `moveFocus`, `visitOrder`,
`visitIndex`, `fieldVisitOrder`, `fieldVisitIndex`, `moveFieldFocus`, `advanceField`,
`commitAdvance`, `retreatField`, `createExam`, `loadExam`, `setSite`, `toggleFlag`,
`setToothField`, `setFurcation`, `finalize`, `cancelExam`, `flush`, `toothScript`, `mouthScript`,
`toothScripts`, `mouthScripts`, `setToothNavigationScript`, `visibleRows`, `passes`,
`siteOrderFor`.

**Two-layer edit gate**: `canEdit` (`:301`) answers "disable this control" at render time;
`canEditRef` answers "may this mutation run" at event time. Both are required.

This slice does **not** follow the repo's `{ items, loading, error, source, isApiEnabled, refetch }`
hook shape — perio has no mock source, so there is no `source` to report. It also uses
`toPerioError` (`chartPerio.js:238`) rather than `getErrorMessage`, and an `AbortController` +
exam-id comparison rather than a monotonic request-id ref. Match the local pattern.

---

## 9. Known-honest gaps and dead code

| Thing | State |
|---|---|
| `skipConditions` (8 ids, `perioExamDefaultsConstants.js:798`) | `partial` — collected, validated, sent, stored, read back. **Nothing skips anything.** The route walks every tooth. Gap documented at :781, including that the model has one direction-less `impacted` status so `impacted-distal`/`impacted-mesial` cannot both be honoured. |
| `bopSupDelay` (0-16 teeth) | `partial` — stored and read back; nothing sequences entry by it. BOP/Sup are available alongside depths at every setting. Gap at :826. |
| `PerioScriptEditors.jsx` (51KB) | Dead — `CustomToothScriptDialog` / `CustomMouthScriptDialog` have no importer anywhere in `src`. |
| `isValidPerioNavigation` (:920), `isValidPerioExamOptions` (:946) | Dead — written for a settings load path that does not exist. |
| Docblock at `perioExamDefaultsConstants.js:10` | **Stale** — says the Start Perio Exam dialog "DOES NOT EXIST YET". `NewPerioExamDialog.jsx` is that dialog and is wired. |
| `/settings/tooth-chart-defaults` | Configures **nothing** perio. It stores default provider, default dentition and procedure colours only. Boundary argued in `components/settings/tooth-chart-defaults/CHART_SETTINGS_API_SPEC.md` §1.1, cited from `perioExamDefaultsConstants.js:21`. |
