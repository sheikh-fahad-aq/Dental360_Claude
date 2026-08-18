---
description: Stage and commit the current work as consolidated, per-repo commits
argument-hint: "[backend | frontend | claude | all] [\"message\"]"
allowed-tools: Bash, Read, Grep, Glob
---

Commit the current work. **One repo per commit** — `360_Flask_Appointment`, `PMS_React` and
`.claude` have three independent histories and a commit never spans them (CLAUDE.md §8).

## Survey before staging

```bash
cd "$CLAUDE_PROJECT_DIR" && for r in 360_Flask_Appointment PMS_React .claude; do echo "=== $r ($(git -C $r rev-parse --abbrev-ref HEAD 2>/dev/null)) ==="; git -C "$r" status --short; done
```

`$ARGUMENTS` selects the scope: `backend`, `frontend`, `claude`, or `all` / empty for every
repo that has changes. A quoted string is the subject line to use.

If a repo is clean, say so and skip it — do not create an empty commit.

## Before you stage anything

1. **Read the diff.** `git -C <repo> diff` — all of it. Never stage what you have not read.
2. **Check for secrets and PHI.** No `.env`, no credential, no patient data, no token in
   any hunk (CLAUDE.md §7.1, §7.2). If the diff touches auth, storage, logging or
   rendering, run the `phi-security-reviewer` agent first.
3. **Check for junk.** `node_modules/`, `dist/`, `__pycache__/`, `env/`, `.claude/skills/
   main-architecture/.stale.json`, editor scratch files. If any is untracked-and-unwanted,
   propose a `.gitignore` line rather than just skipping it.
4. **Check the skills are current.** `python .claude/scripts/skill_status.py --stale`.
   If a change alters a contract or invariant, the owning skill should be updated in the
   *same* commit as the code — not a follow-up. Say so if you are deliberately deferring.

## Staging

Stage explicit paths. Never `git add -A` or `git add .` — both sweep up files nobody
reviewed, and the app repos sit alongside a `.claude` tree that must not be mixed in.

## Message

Subject: imperative, under 72 chars, no type prefix — match the existing style, which is
plain sentences (`git -C <repo> log --oneline -10` to confirm).

Body: what changed and **why**, wrapped at 72. Then, when the work spans both apps, name
the counterpart explicitly, because the two repos deploy independently and a reader of one
history has no way to find the other:

```
Counterpart: PMS_React — <subject of the paired commit>
```

End every commit message with:

```
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

## Order

When both apps changed, **commit the backend first** and say so. A frontend commit that
assumes a new backend field is broken until the backend deploys.

## Do not push

Committing is local. Never `git push` — the user does that. Report each commit's repo,
branch and short SHA when you are done, and state plainly anything you left uncommitted.
