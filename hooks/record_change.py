"""PostToolUse hook: record every file edit against the architecture skill.

This is the mechanism behind CLAUDE.md §3. It exists so that keeping the
architecture record current costs *zero* model tokens: the transcript never has
to carry "now I will append to the changelog". The model only owes the record a
judgement call -- whether a feature's contract actually changed -- and
`/skill-sync` surfaces that from the .stale.json this hook maintains.

Writes two things:
  skills/main-architecture/CHANGELOG.md  -- append-only, one line per file/day
  skills/main-architecture/.stale.json   -- which skills now describe changed code

Always exits 0. A failure here must never interrupt the user's work.
"""

import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import (  # noqa: E402
    ARCH_DIR,
    CHANGELOG,
    load_stale,
    owning_skill,
    read_event,
    rel_path,
    save_stale,
    tool_paths,
)

# Churn that says nothing about product architecture. Recording it would bury
# the signal. `.claude/` is excluded wholesale: this log exists to track changes
# to the two applications, and the tooling's own git history already records
# edits to skills, hooks and commands. Without this, a session spent authoring
# skills fills the log with itself.
IGNORE_FRAGMENTS = (
    "/node_modules/",
    "/dist/",
    "/__pycache__/",
    "/.git/",
    "/env/",
    "/uploads/",
)


def ignored(rel):
    if rel == "CLAUDE.md" or rel.startswith(".claude/"):
        return True
    probe = "/" + rel
    return any(frag in probe for frag in IGNORE_FRAGMENTS)


def main():
    event = read_event()
    if (event.get("tool_response") or {}).get("success") is False:
        return

    today = datetime.date.today().isoformat()
    tool = event.get("tool_name") or "Edit"
    session = (event.get("session_id") or "")[:8]

    new_lines = []
    stale = load_stale()
    touched_any = False

    for raw in tool_paths(event):
        rel = rel_path(raw)
        if not rel or ignored(rel):
            continue
        skill = owning_skill(rel) or "unclaimed"
        new_lines.append("- `{}` — {} ({}) [{}]".format(rel, skill, tool, session))
        if skill not in ("unclaimed", "main-architecture"):
            entry = stale.setdefault(skill, {"since": today, "files": []})
            if rel not in entry["files"]:
                entry["files"].append(rel)
            entry["last"] = today
        touched_any = True

    if not touched_any:
        return

    try:
        os.makedirs(ARCH_DIR, exist_ok=True)
        header = "## {}\n".format(today)
        existing = ""
        if os.path.exists(CHANGELOG):
            with open(CHANGELOG, "r", encoding="utf-8") as fh:
                existing = fh.read()
        else:
            existing = (
                "# Architecture change log\n\n"
                "Appended automatically by `.claude/hooks/record_change.py` on every file\n"
                "edit. Do not hand-edit; do not delete. One line per file per tool call,\n"
                "tagged with the skill that documents it.\n\n"
            )

        # De-duplicate within the day so a file edited ten times gets one line.
        day_start = existing.find(header)
        if day_start == -1:
            existing = existing.rstrip("\n") + "\n\n" + header
            day_block = ""
            day_end = len(existing)
        else:
            day_end = existing.find("\n## ", day_start + len(header))
            day_end = len(existing) if day_end == -1 else day_end
            day_block = existing[day_start + len(header):day_end]

        additions = [ln for ln in new_lines if ln not in day_block]
        if not additions:
            save_stale(stale)
            return

        block = day_block.rstrip("\n")
        block = (block + "\n" if block else "") + "\n".join(additions) + "\n"
        updated = existing[:day_start + len(header)] + block + existing[day_end:] \
            if day_start != -1 else existing + block

        tmp = CHANGELOG + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(updated)
        os.replace(tmp, CHANGELOG)
    except Exception:
        pass

    save_stale(stale)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
