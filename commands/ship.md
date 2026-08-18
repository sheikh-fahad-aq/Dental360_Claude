---
description: Produce ready-to-paste commit messages for the current work, one per repo
argument-hint: "[backend | frontend | claude | all]"
allowed-tools: Bash, Read, Grep, Glob, Task
---

Prepare the current work for commit.

**You do not commit the application repos.** `360_Flask_Appointment` and `PMS_React` are
committed by the user, by hand (CLAUDE.md §8). Your output is the commit message text and
the staging command — not a commit. Do not run `git add` or `git commit` against either.

`.claude/` is the exception and may be committed directly.

## Survey

```bash
cd "$CLAUDE_PROJECT_DIR" && for r in 360_Flask_Appointment PMS_React .claude; do echo "=== $r ($(git -C $r rev-parse --abbrev-ref HEAD 2>/dev/null)) ==="; git -C "$r" status --short; done
```

`$ARGUMENTS` narrows the scope: `backend`, `frontend`, `claude`, or `all` / empty. Skip any
repo that is clean and say so — do not invent work to describe.

## Read the diff before writing anything

`git -C <repo> diff` and `git -C <repo> diff --cached`, in full. A message describing
changes you have not read is worse than no message.

While reading, check three things and report them **above** the message, not inside it:

1. **Secrets and PHI.** No `.env`, credential, token, patient id or payload in any hunk
   (CLAUDE.md §7.1, §7.2). If the diff touches auth, storage, logging or rendering, run the
   `phi-security-reviewer` agent before going further.
2. **Junk.** `node_modules/`, `dist/`, `__pycache__/`, `env/`, editor scratch. Propose a
   `.gitignore` line rather than quietly omitting it from the staging command.
3. **Stale skills.** `python .claude/scripts/skill_status.py --stale`. If the change alters
   a contract or invariant, the owning skill should be updated and staged alongside the
   code — flag it now, while it can still go in the same commit.

## Output, per repo

Give the staging command with **explicit paths**. Never `git add -A` or `git add .` — the
two app repos sit next to a `.claude` tree that must not be swept in.

```bash
git -C 360_Flask_Appointment add app/appointments_v2_routes.py app/models.py
```

Then the message in its own fenced block, ready to paste:

- Subject imperative, under 72 chars, no type prefix. Match the repo's existing style —
  check with `git -C <repo> log --oneline -10`; both currently use plain sentences.
- Body wrapped at 72, saying what changed and **why**.
- When the work spans both apps, name the counterpart, because the repos deploy
  independently and a reader of one history cannot find the other:

  ```
  Counterpart: PMS_React — <subject of the paired commit>
  ```

- End with:

  ```
  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
  ```

Then the commit command itself, unrun, so the user can paste it:

```bash
git -C 360_Flask_Appointment commit -F -
```

## Order

When both apps changed, present the **backend first** and say so explicitly. A frontend
commit that assumes a new backend field is broken until the backend deploys.

## Finally

State plainly what you did not cover and why. Do not push, and do not offer to.
