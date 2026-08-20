---
name: main-architecture
description: The Dental360 architecture hub and skill index — how the Flask API and the React SPA fit together, which feature skill owns which files, and the record of what has changed. Load this first whenever you do not already know which be-* or fe-* skill applies, when a change spans both repos, when adding a new feature area, or when asked about the system as a whole, the skill set, or the architecture change log.
---

# Dental360 architecture

Two applications, three git repos, one product. `CLAUDE.md` holds the rules that apply on
every turn; this skill holds the map. Load a feature skill from the index below before
reading source — the file maps and traps there will save you far more context than they cost.

## Topology

```
   PMS_React (SPA, :5173)
        │
        ├─ authApi ──────────► 360auth            identity, patients, providers, rooms,
        │                                          services, procedure codes, labs, forms,
        │                                          Stripe Terminal
        ├─ preAuthApi ───────► pre-auth API        insurance, eligibility, claims,
        │                                          fee schedules, payer portals
        ├─ appointmentApi ───► /__appointment_api/api ─┐
        └─ chartApi ─────────► /__chart_api/api ───────┴─► 360_Flask_Appointment (:5001)
                                (same-origin proxies — those hosts refuse browser CORS)
```

Only `360_Flask_Appointment` lives in this workspace. The other two backends are external;
the SPA is their only consumer here. Full detail: `references/topology.md`.
Which frontend module calls which backend blueprint: `references/api-contract-matrix.md`.

## Skill index

**Backend — `360_Flask_Appointment/`** (flat: one blueprint per module under `app/`)

| Skill | Owns |
|---|---|
| `be-appointments` | Appointment CRUD + calendar. V2 API, the legacy `/api/appointment/*` surface, and the shared helpers |
| `be-visit-lifecycle` | Arrival → departure: check-in, check-out, status tracking, visit notes, procedures, forms proxy (the route slip is `be-appointments`) |
| `be-charting` | Odontogram chart sessions, chart procedures, catalogs, clinic chart settings, the in-process session scheduler, and the test suite |
| `be-perio` | Periodontal exams — measurement grid, lifecycle, bulk entry |
| `be-lab-cases` | Lab case lifecycle, vendors, due dates |
| `be-recare-waitlist` | Recare/recall due tracking and the ASAP waitlist |
| `be-treatment-plans` | Phase-wise treatment plans: patient accept/decline, signature, share link, and the bridge from accepted work to a booked visit |
| `be-dashboard` | Aggregate statistics and reporting endpoints |
| `be-data-model` | `models.py` and Alembic migrations — the model index every other skill defers to |
| `be-platform` | `create_app()` wiring, config, auth decorators, uploads, Docker, CI |

**Frontend — `PMS_React/`**

| Skill | Owns |
|---|---|
| `fe-platform` | App shell, routing, `src/api/client.js` and the four clients, theme, shared UI, build config |
| `fe-auth` | Login, 2FA, session lifecycle, SSO handoff, browser storage |
| `fe-scheduling` | The calendar and everything on it — the largest live module |
| `fe-patient-chart` | The chart shell and its non-clinical sections |
| `fe-charting` | Odontogram, tooth chart, procedure charting, chart session ownership |
| `fe-perio` | The perio measurement grid UI |
| `fe-ledger` | The patient financial ledger — one implementation, two surfaces |
| `fe-insurance-claims` | Insurance, eligibility, claims, payer portals |
| `fe-labs` | Lab case board and the chart's lab section |
| `fe-forms` | Form library, schema renderer, the public `/f/:token` intake link |
| `fe-settings` | The settings shell and its wired panels |
| `fe-payments-fees` | Payments and fee schedules — mostly unfinished; check before demoing |
| `fe-reports-worklists` | Revenue reports, worklists, documents, and the mock-data index |

The authoritative file→skill mapping is `.claude/hooks/ownership.tsv`. It is machine-read
by the hooks and covers every file in both repos; if you are unsure who owns a path,
that file answers it.

## The change record

`CHANGELOG.md` in this directory is appended by `.claude/hooks/record_change.py` on every
edit — automatically, at no token cost. Never write to it by hand.

`.stale.json` tracks which skills now describe code that has changed since the skill was
last touched. That is a *signal*, not a verdict: most edits do not invalidate a skill.

**Your obligation:** when a change alters a feature's contract, invariants or file map,
update that feature's `SKILL.md` in the same turn. Run `/skill-sync` to see what the
current diff has put at risk.

## Adding a feature area

1. Write `.claude/skills/<be|fe>-<name>/SKILL.md` against `.claude/docs/SKILL_AUTHORING_SPEC.md`.
2. Add its glob(s) to `.claude/hooks/ownership.tsv` — **above** any general rule that would
   otherwise swallow them, since first match wins.
3. Add a row to the index above.
4. Re-run the coverage check in `/skill-sync` to confirm nothing became orphaned.

## Traps at the seam

- **The two repos deploy independently.** A frontend change that assumes a new backend
  field ships broken until the backend deploys. Land the backend first, and say so.
- **`PMS_React/README.md` is the frontend's source of truth** and is unusually accurate,
  including its `live`/`mock`/`partial`/`placeholder` labels. `PROJECT_GUIDE.md` in the same
  repo is stale and misleading — ignore it.
- **`README_V2_APPOINTMENTS.md`** is the backend's endpoint reference. Cite it; do not
  duplicate it into a skill.
- The appointment/chart proxy is declared in **three** blocks across two files:
  `server.proxy` and `preview.proxy` in `vite.config.js`, and `rewrites` in `vercel.json`.
  Changing one alone breaks dev, or `npm run preview`, or production — never all three at
  once, so the mistake survives review. (The README says "twice"; it is counting files.)

## See also

`.claude/docs/SKILL_AUTHORING_SPEC.md` · `references/topology.md` ·
`references/api-contract-matrix.md` · `CHANGELOG.md` · `CLAUDE.md` §2, §3
