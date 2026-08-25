# API contract matrix

Which frontend module talks to which backend, derived from the `authApi` / `preAuthApi` /
`appointmentApi` / `chartApi` imports in `PMS_React/src/api/*.js`.

Regenerate the client column with:

```bash
cd PMS_React/src/api && for f in *.js; do echo "$f: $(grep -oE '\b(authApi|preAuthApi|appointmentApi|chartApi)\b' "$f" | sort -u | tr '\n' ' ')"; done
```

## The headline

**Only 10 of the 34 domain modules in `src/api/` reach the Flask app in this workspace.**
(35 files, minus `client.js`, which is transport rather than a domain module.)
Everything else targets `360auth` or the pre-auth/eligibility API, neither of which is
checked out here. When a frontend call fails, establish which backend it was aimed at
before opening `360_Flask_Appointment` — most of the time the answer is not in this repo.

## Modules that reach `360_Flask_Appointment`

| Frontend module | Client | Backend blueprint | Skills |
|---|---|---|---|
| `api/appointments.js` (~62KB) | `appointmentApi` | `appointments_v2_routes.py`, plus the check-in/check-out/tracking/notes/procedures modules | `fe-scheduling` ↔ `be-appointments`, `be-visit-lifecycle` |
| `api/appointmentLookups.js` | `appointmentApi` + `authApi` | `appointments_v2_routes.py` | `fe-scheduling` ↔ `be-appointments` |
| `api/labCases.js` | `appointmentApi` | `lab_cases_v2_routes.py` | `fe-labs` ↔ `be-lab-cases` |
| `api/waitlist.js` | `appointmentApi` | `waitlist_v2_routes.py` | `fe-scheduling` ↔ `be-recare-waitlist` |
| `api/documents.js` (~10KB) | `appointmentApi` | `patient_documents_routes.py` | `fe-patient-chart` ↔ *no backend skill* (see below) |
| `api/charting.js` (~48KB) | `chartApi` | `charting_routes.py` | `fe-charting` ↔ `be-charting` |
| `api/chartingCatalog.js` | `chartApi` | `charting_routes.py` | `fe-charting` ↔ `be-charting` |
| `api/chartPerio.js` (~58KB) | `chartApi` + `authApi` | `chart_perio_routes.py` | `fe-perio` ↔ `be-perio` |
| `api/chartSettings.js` | `chartApi` + `authApi` | `chart_settings_routes.py` | `fe-charting` ↔ `be-charting` |
| `api/treatmentPlans.js` (~34KB) | `chartApi` | `treatment_plans_v2_routes.py` | `fe-patient-chart` ↔ `be-treatment-plans` |

`api/treatmentPlans.js` rides **`chartApi`**, not `appointmentApi` — its header comment
(`PMS_React/src/api/treatmentPlans.js:5`) explains why. Both proxies reach the same Flask
app today, so a wrong client still works locally; do not take that as licence to mix them.

Both `appointmentApi` and `chartApi` ignore their configured base URL for the request path
and always emit a same-origin path (`/__appointment_api/api`, `/__chart_api/api`), because
those hosts refuse browser CORS. Setting the env var only *enables* the target and tells
the proxy where to forward.

## Modules that reach external backends

Not in this workspace — do not go looking for their routes in `360_Flask_Appointment`.

**`authApi` → 360auth (15):** `auth.js`, `patients.js`, `providers.js`, `rooms.js`,
`services.js`, `locations.js`, `lookups.js`, `multiCodes.js`, `procedureCodes.js`,
`scheduleBlocks.js`, `scheduleGroups.js`, `labs.js`, `forms.js`, `stripeTerminal.js`,
`clinicTeam.js`

**`preAuthApi` → pre-auth / eligibility (6):** `insurance.js`, `claims.js`, `era.js`,
`payerPortals.js`, `clinicFeeSchedule.js`, `planLocationFeeSchedule.js`

**Both:** `ledger.js` uses `authApi` *and* `preAuthApi` — the ledger is assembled from two
external backends and none of its routes live in this workspace.

**Neither:** `config.js` (base URLs and the `is*ApiEnabled()` gates) and
`requestDedupe.js` (the `withInflightDedupe` wrapper) make no calls of their own.

## Backend surfaces with no frontend consumer

Verified by grepping `PMS_React/src/api/` for each path.

- **`dashboard_routes.py` — `/appointments/stats`, `/appointments/stats/by_location`,
  `/appointments/stats/by_status`, `/appointments/web/stats/by_status`,
  `/appointments/web/stats/by_location`, `/emails/read`.** No SPA module references them.
  Treat this blueprint as serving something other than PMS_React (another client, or
  nothing) and confirm before assuming a change here is safe or is visible in the UI.
- **`/dashboard/check` is ambiguous.** `dashboard_routes.py` defines it, and
  `PMS_React/src/api/auth.js:63` calls `/dashboard/check` — but through **`authApi`**, so
  the SPA is hitting 360auth's version, not this one. Two implementations of the same path
  on two backends. Do not assume changing the Flask one affects the SPA. Unverified which
  is canonical.
- **`app/appointment_routes.py`** — the legacy `/api/appointment/*` surface, 29 routes.
  `PMS_React` targets `/api/v2/*`. Assume external or historical consumers and do not
  delete routes on the basis of SPA usage alone.
- **`app/appointment_status_routes.py`** — effectively empty (no routes defined).
- **`app/appointments_v1_routes.py`** — 2 routes, the HMAC-signed create surface. No SPA
  module reaches it.

## Backend surface with no owning skill

`app/patient_documents_routes.py` (11 routes, registered in `app/__init__.py:76`,
consumed by `api/documents.js`) is
matched only by the `360_Flask_Appointment/*` catch-all in `.claude/hooks/ownership.tsv`,
which routes it to `be-platform` — and no `be-*` skill actually describes it. Read the
module directly, and if you do substantial work there, give it a skill rather than
extending `be-platform`. The frontend half **is** covered, by `fe-patient-chart`.

## Recare

`recare_v2_routes.py` exists on the backend, and the strings `recare` / `recall` appear in
`api/appointments.js` rather than in a dedicated module — recare is reached through the
appointments surface on the frontend, not through a `recare.js`. Check
`api/appointments.js` before adding one.
