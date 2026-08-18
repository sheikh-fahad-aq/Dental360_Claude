# `.claude/` — Dental360 agent tooling

Configuration for Claude Code across the Dental360 workspace. Tracked as its own git repo;
neither app repo includes it (both `.gitignore` `.claude`).

```
.claude/
├── CLAUDE.md            the always-loaded rules; /CLAUDE.md at the workspace root imports it
├── settings.json        permissions + hook registration
├── launch.json          dev servers for the browser preview
├── agents/              specialist subagents
├── commands/            slash commands
├── hooks/               event scripts + the file→skill ownership map
├── scripts/             CLI helpers (not hooks)
├── skills/              main-architecture + one skill per feature
└── docs/                authoring spec, glossary
```

## Setup after a fresh clone

The workspace root (`D:\Dental360`) is **not** a git repo — it just contains the three that
are. So one file cannot be tracked by anything: the root `CLAUDE.md` that Claude Code
actually loads. Recreate it after cloning:

```bash
printf '@.claude/CLAUDE.md\n' > ../CLAUDE.md
```

That one line imports `.claude/CLAUDE.md`, which is tracked here. Keeping the substance on
this side means the always-loaded rules are version-controlled and reviewable; the
untracked file is a pointer with nothing to lose.

## The idea

`CLAUDE.md` is loaded on **every turn**, so it holds only what is always true — roughly 150
lines of rules. Everything else lives in a skill, and skills load **only when triggered by
their description**. Working on the perio grid pulls in `fe-perio` and `be-perio`; it does
not pull in the ledger, the settings shell or the claims mappers.

That is the whole token strategy: one small always-on file, twenty-two precise on-demand
ones, and a hub (`main-architecture`) that indexes them so nothing has to be searched for.

## Skills

Named `be-*` (Flask) and `fe-*` (React), plus the `main-architecture` hub. Each carries a
file map, the API contract, numbered invariants, the wiring steps that are easy to forget,
and the known traps with `file:line`.

Write and edit them against `docs/SKILL_AUTHORING_SPEC.md` — it is binding, and the
`skill-curator` agent enforces it.

## Hooks

| Event | Script | What it does |
|---|---|---|
| `PreToolUse` on edits | `guard_paths.py` | Refuses writes to `.env`, applied Alembic revisions, lockfiles, `node_modules/`, `dist/`, and `PMS_React/public/`. Each refusal explains the alternative. |
| `PostToolUse` on edits | `record_change.py` | Appends the file to `skills/main-architecture/CHANGELOG.md` and marks the owning skill in `.stale.json`. |
| `SessionStart` | `session_context.py` | Prints ~10 lines: each repo's branch, dirty state, and any stale skills. |

`record_change.py` is why keeping the architecture record current costs **zero model
tokens** — the transcript never carries "now I will update the changelog". The model owes
the record only a judgement call: did this change alter a contract? `/skill-sync` surfaces
that.

`hooks/ownership.tsv` maps every path in both repos to its owning skill. **First match
wins**, so specific globs must sit above general ones. It currently leaves zero files
unclaimed; `python scripts/skill_status.py --coverage` verifies that.

All three hooks are stdlib-only and exit 0 on any internal error — a broken hook must never
block work.

## Commands

| | |
|---|---|
| `/arch` | Orient: load the hub, resolve a file or feature to its skill |
| `/skill-sync` | Which skills the current diff invalidated — then fix them |
| `/api-contract` | Verify a frontend call and its Flask route agree |
| `/be-endpoint` | Add a Flask endpoint to convention |
| `/fe-page` | Add a page, chart section, or settings section to convention |
| `/mock-check` | What is real vs mock, so nothing fake gets demoed |
| `/phi-check` | Review changes against the §7 security invariants |
| `/ship` | Consolidated per-repo commits |

## Agents

`backend-feature` · `frontend-feature` · `api-contract-auditor` · `phi-security-reviewer` ·
`skill-curator`

## Maintaining this

When a feature area is added, four steps — all listed in the `main-architecture` skill under
"Adding a feature area". The one that gets forgotten is adding the glob to `ownership.tsv`
*above* the general rule that would otherwise swallow it.

Health check:

```bash
python .claude/scripts/skill_status.py
```

Reports stale skills, orphaned or double-claimed files, frontmatter and budget violations,
and every path claim in a skill that no longer resolves.

## Portability note

Hook commands invoke `python "$CLAUDE_PROJECT_DIR/.claude/hooks/<name>.py"`. This workspace
runs Windows with Git Bash and Python 3.10 on `PATH`. If hooks silently do nothing, check
that `python` resolves and that `$CLAUDE_PROJECT_DIR` expands in your shell; the scripts
themselves resolve every other path from `__file__`, so only the invocation is
environment-dependent.
