---
description: Add or change a Flask endpoint following this repo's conventions
argument-hint: "<METHOD /api/v2/path — what it does>"
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, Task
---

Implement `$ARGUMENTS` in `360_Flask_Appointment`.

Load the owning `be-*` skill first (`.claude/hooks/ownership.tsv` maps any path to one), and
`be-data-model` if this touches the schema. For anything beyond a small change, delegate to
the `backend-feature` agent.

## The checklist that matters here

1. **Pick the right module.** The app is flat — one blueprint per file under `app/`. Put the
   route in the module that owns the domain. Do not create a new module for a route that
   belongs in an existing one, and do not reorganise into packages along the way.

2. **Declare the path without the `/api` prefix.** Every blueprint mounts at
   `url_prefix='/api'`, so `@bp.route('/v2/appointments')` serves `/api/v2/appointments`.
   Target the `/api/v2/*` surface; `app/appointment_routes.py` is legacy — read it, do not
   extend it.

3. **If the blueprint is new, register it.** Import *and* `register_blueprint` in
   `app/__init__.py`. Skipping this yields a 404 with nothing logged anywhere — the classic
   time sink in this repo.

4. **Guard it.** Use a decorator from `app/util/decorators.py`. Never hand-roll an auth
   check in the route body, and never trust a role or clinic id the client sent
   (CLAUDE.md §7.7).

5. **Match the existing envelope.** Look at the neighbouring routes in the same module and
   return the same shape — the frontend's `unwrap()` is written against it. Three shapes
   exist across the codebase; consistency within a module is what matters.

6. **Do not log PHI.** No patient id, payload or patient-scoped URL in a log line or in an
   error message that reaches the client (CLAUDE.md §7.1).

7. **Schema changes:** edit `app/models.py`, then `flask db migrate -m "..."`, then review
   the generated revision before `flask db upgrade`. Alembic routinely misreads type changes
   and server defaults. Never edit an applied revision — a hook blocks it (§4.5).

## Verify

```bash
cd "$CLAUDE_PROJECT_DIR/360_Flask_Appointment" && python -m py_compile app/*.py && python -m pytest tests/ -q
```

The suite only covers charting, perio and chart sessions. If your change is elsewhere, say
plainly that no test covers it rather than implying it was verified.

## Then

Check whether the SPA actually consumes this
(`.claude/skills/main-architecture/references/api-contract-matrix.md`) — several backend
surfaces have no frontend consumer, so "it works" may not be observable in the UI.

Update the owning skill's Contract section with the new route, and commit backend-only
(CLAUDE.md §8) — `/ship backend`.
