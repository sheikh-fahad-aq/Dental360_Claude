---
description: Verify a frontend call and its backend route actually agree
argument-hint: "<endpoint path, api module, or feature>"
allowed-tools: Bash, Read, Grep, Glob, Task
---

Audit the seam between `PMS_React` and `360_Flask_Appointment` for `$ARGUMENTS`.

Delegate to the `api-contract-auditor` agent — it has the full procedure. Give it the
target and any symptom the user described (a 404, an empty list, a shape mismatch).

Two things to establish yourself first, because they resolve most questions immediately
and cost one shell call each:

**Which backend is this even?**

```bash
cd "$CLAUDE_PROJECT_DIR/PMS_React/src/api" && grep -oE "\b(authApi|preAuthApi|appointmentApi|chartApi)\b" *.js | sort -u | grep -i "$ARGUMENTS"
```

`authApi` and `preAuthApi` point at external services that are **not checked out here** —
23 of the 31 frontend API modules do. If the target is one of those, say so and stop:
reading Flask routes will actively mislead.

**Is the blueprint registered?**

```bash
cd "$CLAUDE_PROJECT_DIR/360_Flask_Appointment" && grep -n "register_blueprint" app/__init__.py
```

An unregistered blueprint 404s with no error logged anywhere. It is the most common cause
of a mystery 404 in this codebase, and it is a two-line check.

Remember the path translation: the SPA emits `/__appointment_api/api/v2/...`, the proxy
strips the prefix, and every blueprint mounts at `url_prefix='/api'` — so the Flask route
decorator reads `'/v2/...'`. Search for the path *fragment*, never the whole SPA string.

Report the verdict — agree, disagree, or cannot verify — then each discrepancy with
`file:line` on both sides. Do not print payloads or patient ids (CLAUDE.md §7.1).
