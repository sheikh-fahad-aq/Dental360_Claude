# Architecture change log

Appended automatically by `.claude/hooks/record_change.py` on every file edit. Do not
hand-edit and do not delete. One line per file per day, tagged with the skill that
documents it, so that keeping this record costs no model tokens.

Only changes to the two applications are recorded. Edits under `.claude/` are excluded --
this tree's own git history already covers them, and without that exclusion a session spent
writing skills would fill the log with itself.

Being listed here does **not** mean a skill is wrong. `/skill-sync` reads this alongside
`.stale.json` to work out what actually needs updating.

## 2026-08-18

Recording starts here, with the initial `.claude` tooling in place: `CLAUDE.md`, 22 feature
skills, 5 agents, 8 commands, 3 hooks and the ownership map. No application code was changed
in that work, which is why nothing is listed under this date yet.
- `PMS_React/src/api/ledger.js` — fe-ledger (Edit) [final]
