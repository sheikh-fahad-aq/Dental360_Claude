---
description: Report what is real and what is mock, so nothing fake gets demoed as working
argument-hint: "[module or route or page]"
allowed-tools: Bash, Read, Grep, Glob
---

Establish whether `$ARGUMENTS` (or the whole app, if empty) is backed by a real API or by
mock data. This exists because **several mock surfaces in this app look completely
finished**, and the failure mode is someone demoing fabricated clinical data.

## How the app decides

Gating is by **presence of an environment variable, not by a feature flag** (CLAUDE.md §5).
`isPatientsApiEnabled()` is literally "is `VITE_APP_BASE_URL_AUTH` non-empty". Unset a base
URL and that entire domain silently serves mock data — no error, no banner, no visual tell.

So there are two separate questions, and both matter:

1. **Is the code wired to an API at all?** — a property of the source.
2. **Is that API enabled in this environment?** — a property of `.env`.

## Check the code

```bash
cd "$CLAUDE_PROJECT_DIR/PMS_React" && grep -rn "source: *'mock'\|source: *'api-partial'\|isApiEnabled\|MOCK\|mockData\|Seed" src --include=*.js --include=*.jsx -l | sort
```

The owning `fe-*` skill states the maturity label for its surfaces, and
`PMS_React/README.md` carries the authoritative per-module and per-chart-section tables.
**Believe the labels, not the screen.** Known-mock or placeholder areas at the time the
skills were written include tx-plans, documents, payments, fee schedules, the worklists,
and most settings sections — confirm against the skill rather than quoting this list.

`src/data/` is the mock seed directory; `fe-reports-worklists` indexes it.

## Check the environment

```bash
cd "$CLAUDE_PROJECT_DIR/PMS_React" && for v in VITE_APP_BASE_URL_AUTH VITE_APP_BASE_URL_APPOINTMENT VITE_APP_BASE_URL_CHART VITE_APP_BASE_URL_PRE_AUTH VITE_CLINIC_ID; do printf '%-34s %s\n' "$v" "$(grep -q "^$v=.\+" .env 2>/dev/null && echo set || echo 'UNSET -> that domain falls back to mock')"; done
```

Do not print the values — the API key is in the same file.

Two specific traps worth naming when they apply:

- With `VITE_APP_BASE_URL_AUTH` unset the **whole auth layer becomes demo mode**: any 4+
  character password and any 6-digit code sign you in.
- `getClinicId()` in `src/api/patients.js` **defaults to clinic 1** when `VITE_CLINIC_ID` is
  unset, rather than showing "No clinic selected" like every other clinic-scoped call. It is
  the one module that guesses, and it is the one touching PHI.

## Report

A short table: surface → `live` / `mock` / `partial` / `placeholder` → what makes it so
(no API module, an unset env var, a hardcoded seed). Then one line naming anything that
would mislead a viewer if demoed right now.
