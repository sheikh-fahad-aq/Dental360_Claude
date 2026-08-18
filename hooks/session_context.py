"""SessionStart hook: a compact orientation line, injected once per session.

Everything printed here is charged to every subsequent turn's context, so this
is kept to roughly ten lines. It answers only the questions that are expensive
to rediscover and cheap to state: which branch each repo is on, whether either
tree is dirty, and which skills are known to be out of date.

The skill index itself is NOT printed -- that is the main-architecture skill's
job, and it should load on demand rather than on every session.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import WORKSPACE, load_stale  # noqa: E402

REPOS = ("360_Flask_Appointment", "PMS_React", ".claude")


def git(repo_path, *args):
    try:
        out = subprocess.run(
            ("git",) + args,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def main():
    lines = []
    for name in REPOS:
        path = os.path.join(WORKSPACE, name)
        if not os.path.isdir(os.path.join(path, ".git")):
            continue
        branch = git(path, "rev-parse", "--abbrev-ref", "HEAD") or "?"
        dirty = git(path, "status", "--porcelain")
        count = len([ln for ln in dirty.splitlines() if ln.strip()])
        state = "{} uncommitted".format(count) if count else "clean"
        lines.append("  {:<24} {:<18} {}".format(name, branch, state))

    stale = load_stale()
    if stale:
        names = sorted(stale.keys())
        shown = ", ".join(names[:6]) + (" +%d more" % (len(names) - 6) if len(names) > 6 else "")
        lines.append("")
        lines.append("  Skills describing changed code (run /skill-sync): " + shown)

    if not lines:
        return

    print("Dental360 workspace")
    print("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
