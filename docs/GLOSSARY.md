# Domain glossary

Dental-practice vocabulary as this codebase uses it. Load when a term in a ticket, a route
name or a column does not parse — guessing at these produces confidently wrong code.

## The visit

| Term | Meaning here |
|---|---|
| **Operatory** (op) | A treatment room/chair. The column axis of the scheduling calendar. `rooms` in the API. |
| **Provider** | Dentist or hygienist. Appointments are scheduled against a provider *and* an operatory; both can constrain availability. |
| **Check-in** | Patient arrives. Starts the visit state machine: forms, insurance verification, intake. |
| **Check-out** | Patient leaves. Charges posted, next visit scheduled, recare set. Gated by the exit workflow. |
| **Exit workflow** | The check-out checklist. `ExitWorkflowChecklist` gates completion; `useExitWorkflowCompleteGate` decides whether it may finish. |
| **Route slip** | The printed/on-screen summary that travels with the patient through the visit. |
| **Visit status** | Where the patient is right now — scheduled, confirmed, arrived, seated, in treatment, checked out. Distinct from appointment status. |
| **No-show** vs **cancellation** | No-show: did not arrive. Cancellation: told us in advance. Different endpoints, different reporting, different policy consequences. |
| **Huddle** | The morning meeting over the day's schedule. Backs `/revenue-reports/daily-huddle`. |

## Scheduling demand

| Term | Meaning here |
|---|---|
| **Recare** / **recall** | The standing hygiene interval (typically 6 months). Generates *future* demand: "this patient is due". |
| **Waitlist** / **ASAP list** | Patients wanting an earlier slot. Fills demand *now*, when a cancellation opens a gap. |
| **Block** | Reserved calendar time — lunch, admin, a provider's day off, or time held for a procedure type. |
| **Schedule group** | A named grouping of operatories/providers used as a calendar view. |
| **Open slot** | A gap that fits a given appointment length and provider. `FindOpenSlotsDrawer`. |

Recare and waitlist are easy to confuse and are separate backends
(`recare_v2_routes.py`, `waitlist_v2_routes.py`). Recare is *scheduled later*;
waitlist is *sooner if possible*.

## Charting

| Term | Meaning here |
|---|---|
| **Odontogram** | The tooth chart diagram. Per-tooth, per-surface graphical record. |
| **Surface** | A face of a tooth — mesial, distal, buccal/facial, lingual, occlusal/incisal. Restorations are recorded per surface, which is why a filling is `MOD` rather than just "tooth 14". |
| **Tooth numbering** | US **Universal** numbering: 1–32 permanent, A–T primary. Not FDI, not Palmer. |
| **Chart session** | An editing session over a patient's chart. Owned by one user, locked while open, signed to close. See `chartOwnership.js` and CLAUDE.md §7.5. |
| **Condition** vs **procedure** | Condition = what is observed (caries, fracture). Procedure = what is done (filling, crown). Separate catalogs, separate endpoints. |
| **Existing / planned / completed** | Procedure status. Drives colour on the odontogram and what appears on a treatment plan. |
| **Sign / unlock** | Signing finalises a chart note. Unlocking reopens a signed one — an audited action, not a normal edit. |

## Perio

| Term | Meaning here |
|---|---|
| **Perio(dontal) chart** | Gum-health measurements, recorded per tooth per site — typically 6 sites per tooth. Separate from the odontogram. |
| **Probing depth** (PD) | Pocket depth in mm. The core measurement. |
| **Recession** | Gum-line migration in mm. PD + recession = clinical attachment level. |
| **BOP** | Bleeding on probing. Boolean per site. |
| **Suppuration** (sup) | Pus at a site. Boolean per site. |
| **MGJ** | Mucogingival junction — the boundary measurement. |
| **Furcation** | Bone loss between the roots of a multi-rooted tooth. Graded. |
| **Mobility** | How much the tooth moves. Graded, per tooth (not per site). |

Per-**site** vs per-**tooth** is the indexing distinction that breaks perio code. Mobility
and furcation are not per-site; depths and BOP are.

## Money and insurance

| Term | Meaning here |
|---|---|
| **CDT code** | The ADA procedure code (`D2740` = porcelain crown). The unit of billing. "Procedure code" in this codebase. |
| **Fee schedule** | The price list. A clinic has one; each insurance plan may contract different amounts for the same code. |
| **Guarantor** | The person financially responsible — often a parent. The ledger is per *guarantor account*, not per patient. |
| **Ledger** | The running financial record: charges, payments, adjustments, insurance estimates. |
| **Portion** | The split between what insurance is expected to pay and what the patient owes. `/ledger/:patientId/portion`. |
| **Eligibility** | A real-time check that a patient's coverage is active and what it covers. |
| **Claim** | The billing request sent to the payer after treatment. |
| **Payer** | The insurance company. **Stedi** is the clearinghouse this system routes through. |
| **Pre-auth** | Getting the payer to approve a procedure before doing it. Names the backend that owns insurance. |
| **Unapplied credit** | Money received but not yet allocated to a specific charge. |

Insurance estimates read from **Plan Coverage** and **Contracted Providers** under
Settings > Insurance & Claims. Until those are populated every estimate is `0.00` and flagged
— a configuration gap, not a bug.

## Records

| Term | Meaning here |
|---|---|
| **PHI** | Protected Health Information. Anything identifying a patient plus anything about their care. Governs CLAUDE.md §7. |
| **Medical Hx** | Medical history — the questionnaire, allergies, medications, vitals, premedication. |
| **Premed** | Antibiotic premedication required before treatment for some patients. Clinically important; surfaced as an alert. |
| **Tx plan** | Treatment plan: proposed procedures, sequenced, with cost estimates. |
| **Lab case** | Work sent to an external dental laboratory (crown, denture). Has a vendor, a due date and a status the chair time depends on. |
| **Audit trail** | Who changed what, when. Section id `audit-trail`, URL `/history` — the ids do not match. |
