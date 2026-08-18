---
description: Check which feature skills the current changes have invalidated, and update them
argument-hint: "[skill-name | --check | --rebuild-map]"
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, Task
---

Keep the skill set truthful. A skill that describes code as it used to be is worse than no
skill, because it is trusted.

## Gather the facts first

```bash
cd "$CLAUDE_PROJECT_DIR" && python .claude/scripts/skill_status.py
```

That reports, in one call: which skills the current diff puts at risk, whether any file is
orphaned or claimed by a skill that does not exist, which `SKILL.md` files break the
frontmatter or 120-line budget, and every path claim that no longer resolves.

Argument handling for `$ARGUMENTS`:

- **empty** — act on everything the report flags.
- **a skill name** — restrict to that skill; still run the full report for context.
- **`--check`** — report only. Change nothing, and say clearly what you would have changed.
- **`--rebuild-map`** — the ownership map is wrong: reconcile `.claude/hooks/ownership.tsv`
  against the real tree, then re-run with `--coverage` until orphans are zero.

## Then decide, per skill

Being listed as "at risk" is a signal, not a verdict. Most edits do not invalidate a skill.
Update one only when the change alters something it *asserts*: a route, a file in its map,
a stated invariant, a documented trap that is now fixed, a maturity label, or a wiring
recipe. Pure logic changes behind a stable contract need nothing.

Read `.claude/docs/SKILL_AUTHORING_SPEC.md` before editing — the section order, the
frontmatter shape and the 120-line budget are binding. Push overflow into that skill's
`references/`; never delete information to fit.

For anything beyond a couple of skills, delegate to the `skill-curator` agent — one per
skill, in parallel.

## Verify, then clear

Re-run `python .claude/scripts/skill_status.py` and confirm broken path claims are gone and
no budget or frontmatter flag remains. Re-read every `file:line` citation you touched and
correct the number: line numbers drift constantly, and a wrong one discredits the file.

Then remove the skills you actually handled from
`.claude/skills/main-architecture/.stale.json`, leaving any you did not.

## Report

Say which skills you updated and what changed in each, which you checked and deliberately
left alone and why, and anything you could not verify. Do not invent an edit to look busy —
"three skills flagged, none needed changing" is a good outcome, stated plainly.
