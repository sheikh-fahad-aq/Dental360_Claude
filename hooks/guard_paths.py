"""PreToolUse hook: refuse writes that are always a mistake in this workspace.

Exit 2 blocks the call and feeds stderr back to the model, so each message here
is written to tell it what to do instead -- not merely that it was stopped.

Scope is deliberately narrow. A guard that fires on legitimate work gets
disabled, and then it guards nothing.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import read_event, rel_path, tool_paths  # noqa: E402

# These messages cite CLAUDE.md sections by "§", and the Windows console
# defaults to cp1252. Without this the model reads a mojibake'd citation.
try:
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover - Python < 3.7 or a wrapped stream
    pass


def check(rel):
    """Return a refusal message, or None to allow."""
    lower = rel.lower()
    parts = lower.split("/")
    base = parts[-1]

    # --- generated or vendored trees: editing these is never the real fix ---
    for seg in ("node_modules", "dist", "__pycache__", ".git"):
        if seg in parts:
            return (
                "Blocked: `{}` is inside `{}/`, which is generated or vendored. "
                "Edit the source that produces it instead.".format(rel, seg)
            )
    if parts[:2] == ["360_flask_appointment", "env"]:
        return (
            "Blocked: `{}` is inside the Python virtualenv. Change "
            "`360_Flask_Appointment/requirements.txt` instead.".format(rel)
        )

    # --- secrets (CLAUDE.md §7.2) ---
    if base == ".env" or base.startswith(".env."):
        if base in (".env.example", ".env.mocktest"):
            return None
        return (
            "Blocked: `{}` holds live credentials and is untracked by design "
            "(CLAUDE.md §7.2). If a new variable is needed, add it to "
            "`.env.example` with a placeholder and tell the user to fill in the "
            "real value themselves.".format(rel)
        )

    # --- applied migrations are immutable (CLAUDE.md §4.5) ---
    if "/migrations/versions/" in "/" + lower:
        return (
            "Blocked: `{}` is an Alembic revision that may already be applied. "
            "Editing it desynchronises every database that ran it "
            "(CLAUDE.md §4.5). Generate a NEW revision with `flask db migrate` "
            "instead. If this revision is genuinely unapplied everywhere, the "
            "user must confirm that before it is touched.".format(rel)
        )

    # --- lockfiles are tool output ---
    if base in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml"):
        return (
            "Blocked: `{}` is generated. Run the package manager (`npm install "
            "<pkg>`) and let it rewrite the lockfile.".format(rel)
        )

    # --- world-readable after deploy (CLAUDE.md §7.6) ---
    if parts[:2] == ["pms_react", "public"] and base.endswith(".md"):
        return (
            "Blocked: `PMS_React/public/` is copied verbatim into `dist/` and is "
            "fetchable by any unauthenticated visitor (CLAUDE.md §7.6). Internal "
            "documentation belongs in `.claude/docs/` or the backend repo, not "
            "here."
        )

    # --- the stale README trap ---
    if rel == "PMS_React/PROJECT_GUIDE.md":
        return (
            "Blocked: `PROJECT_GUIDE.md` is stale and actively misleading; "
            "`PMS_React/README.md` is the source of truth. Update the README, or "
            "ask the user whether to delete this file rather than reviving it."
        )

    return None


def main():
    event = read_event()
    for raw in tool_paths(event):
        rel = rel_path(raw)
        if not rel:
            continue
        msg = check(rel)
        if msg:
            sys.stderr.write(msg + "\n")
            sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
