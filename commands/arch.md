---
description: Orient in the Dental360 architecture — load the hub skill and report current state
argument-hint: "[feature or file or question]"
allowed-tools: Bash, Read, Grep, Glob, Skill
---

Orient before working. Load the `main-architecture` skill — it carries the topology, the
full skill index, and the map from any file to the skill that documents it.

Then, if `$ARGUMENTS` names a feature, a file or a question:

1. Resolve it to an owning skill via `.claude/hooks/ownership.tsv` (first match wins):

```bash
cd "$CLAUDE_PROJECT_DIR" && grep -nE "$ARGUMENTS" .claude/hooks/ownership.tsv
```

2. Load that `be-*` / `fe-*` skill and answer from it. Read source only for what the skill
   does not cover — that is the point of the skill existing.

If `$ARGUMENTS` is empty, give a short orientation instead:

```bash
cd "$CLAUDE_PROJECT_DIR" && python .claude/scripts/skill_status.py --coverage
```

```bash
cd "$CLAUDE_PROJECT_DIR" && tail -30 .claude/skills/main-architecture/CHANGELOG.md
```

Report: which repos are dirty and on which branches, what the change log shows as recently
touched, and which skills are flagged stale. Keep it to a handful of lines — this is a
signpost, not a survey.

Two things worth stating whenever they are relevant, because they cause the most wasted
time here:

- **Most frontend API modules do not reach the Flask app in this workspace.** Only
  `appointmentApi` and `chartApi` do; `authApi` and `preAuthApi` target external services
  that are not checked out. See `references/api-contract-matrix.md` before hunting for a
  route.
- **Maturity labels are honest and several mock surfaces look finished.** Check the label
  in the owning skill or in `PMS_React/README.md` before treating a screen as working.
