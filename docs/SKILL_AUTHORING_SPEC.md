# Skill authoring spec — Dental360

Binding contract for every file under `.claude/skills/`. Written for the agents that
author them and for anyone editing one later.

## 1. Why these exist

`CLAUDE.md` is loaded on **every** turn. Skills are loaded **only when triggered**.
So: anything that is not needed on every turn belongs in a skill, not in `CLAUDE.md`.
A skill that is too vague to trigger is dead weight; a skill that is too long burns
the budget it was meant to save.

## 2. Hard budgets

| File | Budget | Rule |
|---|---|---|
| `SKILL.md` body | **≤ 120 lines** | If it does not fit, push detail into `references/`. |
| `description` frontmatter | ≤ 500 chars | Must contain the trigger vocabulary (see §4). |
| `references/*.md` | ≤ 400 lines each | Loaded on demand, never automatically. |

Never paste source code that already exists in the repo. Cite `path/to/file.py:120`
instead — the reader can open it. A skill is a **map and a set of rules**, not a copy.

## 3. Required frontmatter

```yaml
---
name: <exact directory name, kebab-case>
description: <see §4>
---
```

`name` MUST equal the directory name. Nothing else is permitted in frontmatter.

## 4. The description is the trigger

Format, in one sentence then one clause:

> `<What this covers>. Use when <concrete task phrasings>, or when touching <file globs>.`

Include the words a person would actually type: feature nouns ("perio chart",
"waitlist", "route slip"), file names (`chart_perio_routes.py`), and route paths
(`/api/v2/appointments`). Descriptions that only restate the name do not trigger.

Bad:  `description: Charting skill for the backend.`
Good: `description: Backend odontogram charting — chart sessions, chart procedures, condition/procedure catalogs, and session locking. Use when changing charting_routes.py or chart_settings_routes.py, adding a /api/charting or /api/v2/charts endpoint, or debugging chart session ownership and sign/unlock flow.`

## 5. Required body sections, in this order

```markdown
## Scope
One paragraph. What this feature is and where its boundary sits.

## Files
A table: path | role. Owned files only — shared files go under "Touches".
Mark the entry point with **(entry)**. Give byte-size hints for files >40KB so the
reader knows to `grep`/`sed -n` rather than read whole.

## Contract
Backend: the routes it owns, as `METHOD /path — purpose`.
Frontend: the API modules it calls and the routes/components it renders.

## Invariants
Numbered, imperative rules that must not be broken. These are the highest-value
lines in the file. Each must be falsifiable — a reviewer can check it.

## Working here
The ordered steps to make a typical change. Include the file to edit AND the
registration/wiring file that is easy to forget.

## Traps
Known sharp edges, with `file:line` where possible. Say what is mock vs live.

## See also
Links to sibling skills and `references/`.
```

Omit a section only when it is genuinely empty. Never pad.

## 6. Accuracy rules

- **Verify before writing.** Every path, route, and line number must be checked
  against the working tree. A wrong path is worse than no skill.
- **Mark maturity.** `live` / `mock` / `partial` / `placeholder`. `PMS_React/README.md`
  is the source of truth for the frontend; believe its labels over the screen.
- **No invention.** If you cannot confirm a behaviour, write "unverified" or omit it.
- **Absolute-ish paths.** Always prefix repo-relative paths with the repo name:
  `360_Flask_Appointment/app/models.py`, `PMS_React/src/api/client.js`.

## 7. Cross-linking

Every skill ends with a `See also` pointing at `main-architecture` and its direct
siblings. `main-architecture` is the hub: it holds the index and the change log and
is the only skill mentioned by name in `CLAUDE.md`.

## 8. Naming

- Backend feature skills: `be-<feature>`
- Frontend feature skills: `fe-<feature>`
- The hub: `main-architecture`
