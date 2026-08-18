---
name: dental360-claude-tooling
description: The .claude tooling for Dental360 is built around one always-loaded CLAUDE.md plus 23 on-demand feature skills, with hooks that record changes at zero token cost and keep commits out of the app repos.
metadata:
  type: project
---

Built 2026-08-18 at the user's request. The stated design goal was **low token use**, so it
is structured as:

- `.claude/CLAUDE.md` — the only always-loaded file (~185 lines). The workspace-root
  `CLAUDE.md` is a one-line `@.claude/CLAUDE.md` import, so the substance stays in the
  tracked `.claude` repo. Its `§` numbering deliberately matches the
  `CLAUDE.md §5 / §7.1 / §7.4 / §7.5 / §7.7` citations already present in `PMS_React/src`.
- `.claude/skills/` — `main-architecture` (hub and index) plus 9 `be-*` and 13 `fe-*`
  feature skills. These load only when their `description` matches, so unrelated features
  cost nothing. Budget: 120-line bodies, overflow into `references/`.
- `.claude/memory/` — **project memory lives here, not in `~/.claude/projects/`**
  (`CLAUDE.md` §9). `MEMORY.md` is imported by `CLAUDE.md` so the index loads every turn;
  the individual files are read only when relevant.
- `.claude/hooks/` — `record_change.py` (PostToolUse) appends every application-code edit
  to `skills/main-architecture/CHANGELOG.md` and flags the owning skill in `.stale.json`;
  `guard_paths.py` and `guard_commits.py` (PreToolUse) refuse dangerous writes and refuse
  `git add`/`git commit` inside the two app repos; `session_context.py` prints ~10 lines at
  session start.
- `.claude/hooks/ownership.tsv` — maps every path in both repos to its owning skill,
  first match wins. Verified to leave zero files unclaimed.

**Why:** the recurring theme is that a convention which only lives in prose gets forgotten
at the end of a long task, exactly when it matters. So each one is enforced by a hook
instead — and recording architecture changes that way means the transcript never carries
"now I will update the changelog". The bookkeeping is free; the model is left only with the
judgement call of whether a contract actually changed.

**How to apply:** run `python .claude/scripts/skill_status.py` for a health check (stale
skills, orphaned files, budget and frontmatter violations, broken path claims). Author or
edit skills against `.claude/docs/SKILL_AUTHORING_SPEC.md`. When adding a feature area, the
step that gets forgotten is adding its glob to `ownership.tsv` *above* the general rule that
would swallow it. See [[dental360-workspace-shape]] and [[pms-react-readme-is-truth]].
