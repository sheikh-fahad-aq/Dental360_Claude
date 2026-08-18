"""PreToolUse hook on Bash: keep commits out of the two application repos.

CLAUDE.md §8 says `360_Flask_Appointment` and `PMS_React` are committed by the
user, by hand, and that Claude's job is to hand over the message text instead.
That rule is easy to forget at the end of a long task, exactly when it matters,
so it is enforced here rather than left to prose.

Scope is deliberately tight: only `git add` and `git commit`, and only when the
target resolves inside one of the two app repos. Read-only git is untouched,
and `.claude/` is explicitly allowed -- it is tooling, not product.

Exit 2 blocks the call and sends stderr back to the model.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import WORKSPACE, read_event  # noqa: E402

try:
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

APP_REPOS = ("360_flask_appointment", "pms_react")

# `git add` / `git commit`, allowing the global flags that may precede the
# subcommand (e.g. `git -C foo -c user.name=x commit`).
WRITE_CMD = re.compile(r"\bgit\b(?:\s+-[^\s]+(?:\s+[^\s]+)?)*\s+(add|commit)\b")
DASH_C = re.compile(r"\bgit\b[^|;&]*?\s-C\s+(?:\"([^\"]+)\"|'([^']+)'|([^\s]+))")
CD_TO = re.compile(r"\bcd\s+(?:\"([^\"]+)\"|'([^']+)'|([^\s|;&]+))")


def first_group(match):
    return next((g for g in match.groups() if g), None) if match else None


def targets_app_repo(command, cwd):
    """Which app repo would this command commit into? None if not one."""
    # An explicit -C wins, then a `cd` earlier in the same command, then cwd.
    candidates = [first_group(DASH_C.search(command)),
                  first_group(CD_TO.search(command)),
                  cwd]
    for cand in candidates:
        if not cand:
            continue
        try:
            path = cand if os.path.isabs(cand) else os.path.join(cwd or WORKSPACE, cand)
            rel = os.path.relpath(os.path.abspath(path), os.path.abspath(WORKSPACE))
        except Exception:
            continue
        head = rel.replace(os.sep, "/").split("/")[0].lower()
        if head in APP_REPOS:
            return head
        if head in (".claude", "..", "."):
            # .claude is allowed; "." / ".." mean this candidate told us nothing
            # useful, so fall through to the next one.
            if head == ".claude":
                return None
            continue
    return None


def main():
    event = read_event()
    command = (event.get("tool_input") or {}).get("command") or ""
    if not command:
        sys.exit(0)

    match = WRITE_CMD.search(command)
    if not match:
        sys.exit(0)

    repo = targets_app_repo(command, event.get("cwd") or WORKSPACE)
    if not repo:
        sys.exit(0)

    proper = "360_Flask_Appointment" if repo == APP_REPOS[0] else "PMS_React"
    which = "backend" if repo == APP_REPOS[0] else "frontend"
    sys.stderr.write(
        "Blocked: `git {verb}` in `{proper}`.\n\n"
        "That repo is committed by the user, by hand (CLAUDE.md §8). Do not stage "
        "or commit it.\n\n"
        "Hand over the commit instead: the `git add` line with explicit paths, the "
        "message in a fenced block, and the `git commit` command left unrun for the "
        "user to paste. `/ship {which}` produces exactly that.\n\n"
        "This still applies when the work is finished and verified — producing the "
        "text is what finishing looks like here.\n".format(
            verb=match.group(1), proper=proper, which=which
        )
    )
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
