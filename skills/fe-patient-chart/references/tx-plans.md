# fe-patient-chart — treatment plans

Companion to `.claude/skills/fe-patient-chart/SKILL.md`. Everything here was read off the working
tree. Paths are relative to `PMS_React/` unless prefixed with a repo name. Server side is
`be-treatment-plans` (`360_Flask_Appointment/app/treatment_plans_v2_routes.py`).

---

## 1. File map

`src/components/patient-detail/tx-plans/` — **7 files** plus `builder/`.

| file | lines | role |
|---|---|---|
| `TxPlansSection.jsx` | 439 | The `/patients/:id/tx-plans` tab. Owns `showArchived`, the archive / unarchive handlers, `getClinicId()` `:33`, the default-provider lookup via `useClinicChartSettings()` `:80`, and which of the three surfaces is mounted. |
| `ChartFindingsCard.jsx` | 139 | The summary the page opens on: charted treatment that has not reached a plan yet. Fed by `usePatientChartFindings`. |
| `TxPlansTable.jsx` | 310 | The paginated plan listing (status, progress, next step, row menu incl. Unarchive). |
| `GenerateFromChartDrawer.jsx` | 797 | "Generate from Chart". **Live** — `fetchChartProcedures` from `src/api/charting` `:16`; `findingFromChartProcedure` `:21` maps a normalized ChartProcedure to the drawer's finding shape. (It used to read `txPlanMockFindings.js`; that file no longer exists.) |
| `NewTreatmentPlanDrawer.jsx` | 311 | The create form. Only reached when no default provider is configured. |
| `txPlanFormat.js` | 249 | `formatCents` / `NO_ESTIMATE_LABEL` `:15`, `planStatusTone` `:62`, `planProgressLabel` `:73`, `formatPlanDate` `:112`, `chartProcedurePlanState` `:148`, `formatSite` `:178`, `planNextStep` `:226`. |
| `txPlanUi.jsx` | 247 | Shared display primitives for every plan surface (charting listing, builder document, patient preview). |

`tx-plans/builder/` — **17 files**.

| file | lines | role |
|---|---|---|
| `TreatmentPlanBuilder.jsx` | 1805 | The full-screen editor. `grep`/`sed -n`, never read whole. `handleSchedule` `:703`, `handlePresent` `:1034`, `handleSend` `:1076`, `handleSendSubmit` `:1081`, `handleCopyShareLink` `:1111`, the Mark-response gate `:370-382`. |
| `TreatmentPlanDocument.jsx` | 548 | The plan rendered as a document (phases, items, totals). |
| `TreatmentPlanPatientPreview.jsx` | 580 | What the patient sees, including `SignaturePad` `:124`. Mounted without app providers — nothing here may reach for `useToast` or `getClinicId()`. |
| `TreatmentPlanPresentation.jsx` | 168 | Chairside presentation mode: the clinician turns the screen to the patient. |
| `SendTreatmentPlanModal.jsx` | 513 | Staff compose modal (channel tabs, To row, subject, template body). Sibling of `forms/SendFormToPatientModal`. |
| `SendPredeterminationModal.jsx` | 205 | Addresses a predetermination claim to ONE coverage. |
| `emailTemplate.js` | 79 | `EMAIL_VARIABLES` `:24`, `SERVER_FILLED_VARIABLES` `:34`, `DEFAULT_SUBJECT` `:36`, `DEFAULT_BODY_HTML` `:39`, `EMAIL_BUTTON_LABEL`/`EMAIL_HEADER_TITLE` `:52-53`, `buildTreatmentPlanEmailHtml` `:55`, `isTemplateEdited` `:77`. This folder's half of the composer; the editor itself is shared. |
| `TreatmentPlanActionsMenu.jsx` | 189 | The "⋯" overflow menu. The action list starts at `:34`; `requiresSavedPlan` is the only disable reason (`:150-152`). |
| `ComparePlansModal.jsx` · `comparePlans.js` | 308 · 79 | Compare two plans. The pure matching rule lives in the `.js` so it can be reasoned about alone. |
| `treatmentPlanPdf.js` | 297 | Client-side jsPDF export. `COL` `:36`, `LABEL_GUTTER` `:39`, `ensureSpace` `:80`, `pdf.save(treatmentPlanPdfFilename(plan))` `:293`. |
| `treatmentPlanDraft.js` | 364 | The unsaved, in-memory plan the builder opens on, plus `planToDuplicatePayload`. |
| `RecommendedTreatmentRail.jsx` | 371 | Left rail: everything recommended on the chart and what is already in this document. |
| `RecordManualResponseModal.jsx` | 404 | The patient answered by phone / on a printout / in the chair. |
| `TreatmentPlanActivity.jsx` | 103 | The plan's append-only audit trail. |
| `TreatmentPlanVersionMenu.jsx` | 157 | "Current treatment plan" picker; a past version opens **read-only**. |
| `ProcedureLocationPopover.jsx` | 272 | Per-line editor for tooth / surfaces / material. |

Data layer: `src/api/treatmentPlans.js` (909, on `chartApi`), `src/hooks/usePatientTreatmentPlans.js`
(162), `src/hooks/usePatientChartFindings.js` (133). The charting tab's own listing —
`charting/treatment-listing/TreatmentListingPanel.jsx:134` — calls `listPatientTreatmentPlans({ patientId })`
directly and is owned by **fe-charting**.

---

## 2. Flows

**Opening the builder.** `TxPlansSection` mounts `TreatmentPlanBuilder` with `planId={builderPlanId}`
(`:399`), `seedFindings={draftSeed}` (`:403`) and `draftProviderId={draftProvider?.apiId}` (`:404`).
New Plan passes `planId={null}` — an unsaved draft, the same entry point charting uses — not a
create-then-open POST. The provider comes from Settings → Tooth Chart Defaults → Default Provider via
`useClinicChartSettings()` (`:80`); send `provider.apiId`, never `provider.id`, which is a String the
API rejects. With no default configured it falls back to `NewTreatmentPlanDrawer`, which asks for one.

**Scheduling the work.** The footer's Schedule opens the shared slot finder with a plan seed:
`findOpenSlotsDrawerStore.open({ planId, planTitle, patient, phases, procedures, acceptedCount,
onBooked })` (`handleSchedule` `:703`). That seed is also the drawer's MODE SWITCH — it reads
`Boolean(planSeed?.planId)` and, only then, groups the results into a horizontal weekday strip,
turns a slot click into a two-step confirm screen instead of an immediate booking, and hides its
Service selector. `patient` carries `{ id, name, email, phone }` because the confirm step composes
a "we are holding this time" email to that address; without the contacts the composer opens on an
empty To row for somebody who has one. In memory on the store only — never persisted, never
logged. `onBooked` refetches this plan, because booking is the one action that changes it from
outside the builder. Details in `fe-scheduling`.

**Presenting and sharing.** `handlePresent` (`:887`) marks the plan presented. `handleCopyShareLink`
(`:964`) mints a share token on click. `handleSend` (`:929`) only opens the modal; the actual
`sendTreatmentPlan` call in `handleSendSubmit` (`:934`) is what presents a draft and issues the token,
server-side, as part of delivering. Signing no longer revokes the token, and the link no longer
expires — a patient can come back to a plan they already signed and see why it is closed
(`treatmentPlans.js:844`, the `closed` field) instead of a dead link.

**The patient's page.** `/tp/:token` → `AppRoutes.jsx:177` → `src/pages/SharedTreatmentPlanPage.jsx`
(585). Stages are `verify` → loaded → submitted, or `unavailable` (`:264`). `verifySharedTreatmentPlan`
(`treatmentPlans.js:801`) POSTs the DOB and returns an `accessToken`; `fetchSharedTreatmentPlan`
(`:819`) sends it as an `X-Plan-Access` header. Decisions go back through
`submitSharedTreatmentPlanDecisions` (`:850`).

**Statuses.** `PLAN_STATUS` `treatmentPlans.js:49` and `PLAN_STATUS_LABEL` `:75` mirror
`ck_treatment_plans_status` in `360_Flask_Appointment/app/models.py:1386-1390`: `draft`, `presented`
(labelled "Proposed"), `partially_accepted`, `accepted`, `scheduled`, `declined`, `completed`, `void`.
`EDITABLE_PLAN_STATUSES` is `{draft, presented}` (`:96`) and must not be wider than the server's.

---

## 3. Traps, long form

Each of these is a one-line rule in `SKILL.md`. This is the evidence and the failure it came from.

### 3.1 Removing a plan is ARCHIVE, never void and never delete

The builder's "Archive / delete Treatment Plan" menu item used to call `voidTreatmentPlan`, so a plan
somebody tried to put away came back in the listing as a row reading "Void" — the exact bug archive
exists to fix. The client now exposes only `archiveTreatmentPlan` (`treatmentPlans.js:601`) and
`unarchiveTreatmentPlan` (`:609`); `voidTreatmentPlan` and `deleteTreatmentPlan` are **gone** from the
module, and `deletePlan` / `voidPlan` are gone from `usePatientTreatmentPlans`. Both server endpoints
still exist and are still tested in `be-treatment-plans` — do not re-add a client for either without a
screen that needs it. Archive 409s when the plan's work is already booked; surface that message rather
than a generic failure (`TxPlansSection.jsx:163-169`).

### 3.2 Archived plans are hidden server-side

`usePatientTreatmentPlans` and `TreatmentListingPanel` both stop showing them with no client-side
filter. The only way back is `includeArchived` → `?include_archived=true`
(`usePatientTreatmentPlans.js:27,87`), which the "Show archived" checkbox on `TxPlansSection`
(`:275,:307`) passes down. Delete that toggle and archive becomes one-way — and the archive
confirmation dialog's promise, "Turn on Show archived to find it again" (`TxPlansSection.jsx:429`),
becomes a lie. `isPlanEditable()` (`treatmentPlans.js:104`) and `planLockReason()` (`:118`) read
`plan.isArchived`, mirroring the server's `_archived_error`; without that the builder renders an
archived plan fully editable and the operator finds out one 409 at a time.

### 3.3 The plan list read is NOT location-scoped

`usePatientTreatmentPlans` sends only `clinic_id` and says so at `:73`; `TreatmentListingPanel:134`
sends nothing at all. Adding `location_id` back makes a plan the charting tab lists vanish from
`/tx-plans` with no error and no empty state saying why — a plan belongs to the patient, not to the
operatory it was drawn up in. `create` still stamps a `locationId` (`:116`), because the API requires one.

### 3.4 `/tp/:token` is public and must render standalone

`src/App.jsx` decides whether to wrap `AppRoutes` in `AppLayout`. It listed `/f/` (`:25`) but not
`/tp/`, so a patient opening their own treatment plan got the practice's internal sidebar — Scheduling,
Patients, Labs, Claims — wrapped around it. `AppRoutes.jsx:147` already drew the distinction correctly
for its Suspense fallback (`isPublicPlanLink`); the same test now exists at `App.jsx:35`. **Any new
public token route must be added in both places.**

### 3.5 The patient page opens on a DOB gate and never probes

`SharedTreatmentPlanPage` issues no request at all until the patient submits a date — an unverified GET
would answer "is this token real?" for anyone holding a guess, and could be polled to learn the moment
the patient signs. The access credential lives in component state (`:271`), never storage (§7.3), so a
refresh re-prompts on purpose. The DOB goes in the POST **body** (`treatmentPlans.js:803-805`): in a
query string it would land in access logs and Referer headers. Refusals are uniform on the server — a
wrong date and an unknown token answer identically — so there is nothing to branch on. The field asks
for **the patient's** date of birth, not "your" (`:121`): plans are routinely opened by a parent or a
spouse, and "your" invites them to spend the attempt budget on a value that could never match.

### 3.6 Opening a dialog must not write to the plan

`handleSend` used to call `presentTreatmentPlan` + `shareTreatmentPlan` before showing the compose form,
just to have a link ready. So merely clicking Send marked the plan Proposed, stamped `presented_at`,
opened a public review token and surfaced "Mark response" — before an address was typed, and even if
the operator cancelled or had no email on file. The record said the patient had been asked when nobody
had. `handleSend` is now `setSendOpen(true)` and nothing else (`:929`).

Related: **"Mark response" is gated on evidence the patient was actually asked** — `presentedAt`,
`isShared`, or decisions already recorded (`:345-355`) — not on status alone. The gate alone was not
enough: while opening the send dialog set those fields, no gate built on them could work. Fix the
write, not the reader. The already-answered clause still matters: without it a legacy plan carrying
decisions but no `presented_at` loses the button needed to amend them.

### 3.7 `scheduled` is a real status, and the sub-line still reports acceptance

It is in `ck_treatment_plans_status` (`app/models.py:1386-1390`) and in `PLAN_STATUS`
(`treatmentPlans.js:54`); the server's `_recalculate_plan_status` derives it, and both
`schedule_treatment_plan_phase` and `unschedule_treatment_plan_item` call that. The client only mirrors
it. Three consequences, all in the tree:

- `planProgressLabel` (`txPlanFormat.js:84-86`) keeps **acceptance** as the sub-line for a scheduled
  plan, because the practice is held to what the patient accepted; a booking is a logistical fact on
  top of that.
- `planNextStep` (`:246`) returns `""` for `scheduled`. Telling the front desk to "Schedule
  accepted care" for a plan they have already booked is how a visit gets booked twice.
- `planLockReason` (`treatmentPlans.js:130`) says "This treatment is booked onto a visit. Take it off
  the schedule to make changes."

`completed` deliberately does **not** read as scheduled: finished work is past, and a done plan reading
"Scheduled" sends the desk hunting an appointment that already happened.

### 3.8 The signature pad, and canvas sizing

`SignaturePad` (`TreatmentPlanPatientPreview.jsx:124`) wiped the canvas whenever
`signature === null && hasInk`. But `signature` is null for **two** different reasons — the parent
cleared it, and the parent has not been told yet — and the second is the normal state while somebody is
drawing, because the pad only publishes on `pointerup`. So the first stroke set `hasInk`, the effect saw
a null `signature`, and it cleared the canvas: measured as `stroke -> clearRect -> stroke -> clearRect`.
Ink never accumulated and `onSignatureChange` never fired, so Sign and submit stayed disabled forever.
It is keyed on `publishedRef` now (`:217,:239`), which tells the two cases apart. **Same class of bug as
`teeth` and the `plan.isArchived` chip: `null` and "not set yet" are not the same value.**

Separately, the same pad sized its bitmap in a single `requestAnimationFrame` that bailed silently on a
zero-size measurement — and StrictMode double-invokes the effect, so the cleanup cancelled the pending
frame. The bitmap stayed at the browser default 300x150 under a 686px box, putting every stroke past
~44% of the pad off-canvas. It is a `ResizeObserver` now (`:198`). `src/App.jsx:61` still has the same
rAF-then-setState pattern for its full-screen `AppLoader`: if that frame never runs (a hidden or
non-compositing tab), the white `fixed inset-0 z-50` overlay never lifts and swallows every pointer.

### 3.9 The PDF

- **Never print `$0.00` for a missing figure.** Money goes through `formatCents`, which gives "No Est."
  for `null` (`treatmentPlanPdf.js:10,205-211`).
- **The three money columns are right-aligned anchors, not left edges.** `COL` (`:36`) names the right
  edge of each column, so the label must be wrapped to `COL.fee - LABEL_GUTTER` (`:195`) — a gutter wide
  enough for the widest figure (`LABEL_GUTTER` is 70 `:39`; an earlier 16pt gutter printed
  `$12,480.00` straight through the procedure description on every wrapped line).
- **Reserve an item's height AFTER measuring its wrapped label** (`:198`). A constant reserve stranded a
  `code · #tooth` line at the top of the next page, above a DIFFERENT procedure — a consent problem on a
  signed document.
- **Redraw the column heads whenever `ensureSpace` reports a page break** (`:179,:198`).
- The filename deliberately excludes the patient's name (a downloads folder is often shared or
  screen-shared) and the signature IMAGE is deliberately not embedded (`:288`) — the signed name and
  date carry the same meaning without copying PHI into a file that gets emailed on.

Verified by parsing the generated content stream: 0 collisions, ink stops exactly on the 556pt text
edge, heads on every item page, 0 orphaned detail lines across 12–30 items.

### 3.10 The email composer edits a BODY, never the whole email

**`EmailTemplateEditor` lives in `src/components/ui/`, not here.** It moved out when the Add
Appointment drawer's notify composer needed the same editor with a different banner, no button and
its own tokens (`fe-scheduling`). Those three are props now — `headerTitle`, `buttonLabel`
(`null` = no button) and `variables` — and `SendTreatmentPlanModal` passes its own from
`emailTemplate.js`. Nothing plan-specific is left in the editor; add a second caller's constants as
props, never as an `if` inside it.

`EmailTemplateEditor` renders the chrome — banner, card, Review button — as fixed React markup and puts
only the message in TipTap (already a dependency; StarterKit v3 ships `link` and `undoRedo`, so
Bold / Italic / Link / Undo / Redo need no extra package). Nothing assigns `innerHTML` and nothing
arbitrary is parsed (`ui/EmailTemplateEditor.jsx:14`), which is the only way to have a WYSIWYG email in a
repo with no sanitiser (§7.4). `buildTreatmentPlanEmailHtml` (`emailTemplate.js:55`) composes the
outgoing string with **inline** styles and no classes — an email client strips stylesheets, which is
also why the hex values in that file are not a CLAUDE.md §6.4 violation. The template leaves the browser
with its `[Bracketed]` variables intact (`EMAIL_VARIABLES` `:24`); the server fills them, and
`[Form Link]` is server-only (`SERVER_FILLED_VARIABLES` `:34`).

### 3.11 The overflow menu

Every entry now does real work, and two of the reasons it used to give for disabling them were simply
wrong. Duplicate needs no new endpoint (`POST /v2/treatment-plans` takes phases and items inline —
`planToDuplicatePayload` in `treatmentPlanDraft.js`), and neither does Compare (two detail reads joined
on code + tooth — `comparePlans.js`, rendered by `ComparePlansModal.jsx`). Download PDF is client-side
jsPDF; `jspdf` was already a dependency and the prior art is `docs/docsFolders.js`.
**Pre-authorization was removed, not disabled** (`TreatmentPlanActionsMenu.jsx:20-28`) — it belongs to
the claims service, which this app does not talk to, so a permanently dead row only taught operators to
distrust the menu. `requiresSavedPlan` / `planSaved` (`:152`) is the one thing that still greys a row:
an unsaved draft has no id to fetch, duplicate or render.
