---
description: Review the current changes for PHI leakage and this codebase's known security traps
argument-hint: "[repo or path]"
allowed-tools: Bash, Read, Grep, Glob, Task
---

Review `$ARGUMENTS` (or the current diff in both repos, if empty) against `CLAUDE.md` §7.

Delegate to the `phi-security-reviewer` agent — it carries the full procedure and the list
of pre-existing findings, so it can tell new problems from old ones. Give it the diff scope.

Scope matters: review **what changed**, not the whole codebase. An audit of everything
produces a list nobody acts on.

```bash
cd "$CLAUDE_PROJECT_DIR" && for r in 360_Flask_Appointment PMS_React; do echo "=== $r ==="; git -C "$r" diff --stat; done
```

The seven checks, in short — the agent has the detail:

| | |
|---|---|
| §7.1 | No PHI in logs. Patient ids live in URLs, so a logged URL counts. Gate on `import.meta.env.DEV` |
| §7.2 | No secrets in source. `VITE_`-prefixed values are compiled into the bundle and readable by anyone |
| §7.3 | New browser storage keys: cleared on logout? Does the **key name** embed a patient id? |
| §7.4 | No `dangerouslySetInnerHTML` or `innerHTML` fed from the network — there is no sanitizer in this repo |
| §7.5 | Chart ownership stays in `sessionStorage`, deliberately non-durable |
| §7.6 | Nothing internal in `PMS_React/public/` — it ships to `dist/` and is world-readable |
| §7.7 | No client-side role gating. A hidden button is not a permission boundary |

Two live findings already exist and should not be re-reported as new, though they are worth
fixing if the work is nearby:

- `PMS_React/src/components/scheduling/VisitStatusBoard.jsx:1125` — backend-supplied
  patient-form HTML rendered through `dangerouslySetInnerHTML` with no sanitizer.
- `360_Flask_Appointment/app/__init__.py` — hardcoded `SECRET_KEY`, database URI fallback
  and an inline LLM credential.

Report findings ordered by severity, each with `file:line`, the concrete consequence, and
the fix — and always separate **introduced by this change** from **pre-existing**. Say
plainly when the change is clean. Never paste real PHI, tokens or credentials into the
report; describe them.
