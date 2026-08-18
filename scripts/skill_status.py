"""Report the health of the Dental360 skill set. Read-only; changes nothing.

    python .claude/scripts/skill_status.py            # full report
    python .claude/scripts/skill_status.py --stale    # only what a diff put at risk
    python .claude/scripts/skill_status.py --coverage # only orphan/collision check

Exists so `/skill-sync` can get the mechanical facts in one shell call instead of
a dozen model turns. Everything here is a fact a script can establish; the
judgement calls are left to the caller.
"""

import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "hooks"))

from _common import (  # noqa: E402
    SKILLS_DIR,
    WORKSPACE,
    load_stale,
    owning_skill,
    rel_path,
)

REPOS = ("360_Flask_Appointment", "PMS_React")
SCAN = {
    "360_Flask_Appointment": ("app", "tests", "migrations"),
    "PMS_React": ("src",),
}
SKIP_DIRS = {"__pycache__", "node_modules", ".git", "dist", "env", "uploads"}
PATH_RE = re.compile(r"(?:360_Flask_Appointment|PMS_React)/[A-Za-z0-9_.@/-]+")


def skills():
    if not os.path.isdir(SKILLS_DIR):
        return []
    out = []
    for name in sorted(os.listdir(SKILLS_DIR)):
        if os.path.isfile(os.path.join(SKILLS_DIR, name, "SKILL.md")):
            out.append(name)
    return out


def frontmatter(path):
    """Return (name, description, body_line_count)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except Exception:
        return None, None, 0
    name = desc = None
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            head = text[3:end]
            body = text[end + 4:]
            for line in head.splitlines():
                if line.startswith("name:"):
                    name = line[5:].strip()
                elif line.startswith("description:"):
                    desc = line[12:].strip()
    return name, desc, len(body.strip().splitlines())


def git_changed(repo):
    path = os.path.join(WORKSPACE, repo)
    if not os.path.isdir(os.path.join(path, ".git")):
        return []
    files = set()
    for args in (("diff", "--name-only"), ("diff", "--name-only", "--cached"),
                 ("ls-files", "--others", "--exclude-standard")):
        try:
            res = subprocess.run(("git",) + args, cwd=path, capture_output=True,
                                 text=True, timeout=10)
            if res.returncode == 0:
                files.update(ln.strip() for ln in res.stdout.splitlines() if ln.strip())
        except Exception:
            pass
    return sorted("{}/{}".format(repo, f) for f in files)


def report_coverage():
    print("== Coverage ==")
    orphans, by_skill = [], {}
    known = set(skills())
    for repo, subs in SCAN.items():
        for sub in subs:
            base = os.path.join(WORKSPACE, repo, sub)
            if not os.path.isdir(base):
                continue
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fn in filenames:
                    if fn.endswith((".pyc", ".pyo")):
                        continue
                    rel = rel_path(os.path.join(dirpath, fn))
                    owner = owning_skill(rel)
                    if owner is None:
                        orphans.append(rel)
                    else:
                        by_skill[owner] = by_skill.get(owner, 0) + 1

    for name in sorted(by_skill):
        missing = "" if name in known else "   <-- NO SKILL.md"
        print("  {:<24} {:>4} files{}".format(name, by_skill[name], missing))

    unclaimed = [s for s in known if s not in by_skill and s != "main-architecture"]
    if unclaimed:
        print("\n  Skills claiming no files (check ownership.tsv): " + ", ".join(unclaimed))
    print("\n  Orphaned files: {}".format(len(orphans)))
    for o in orphans[:25]:
        print("    " + o)
    if len(orphans) > 25:
        print("    ... {} more".format(len(orphans) - 25))
    return len(orphans)


def report_health():
    print("\n== Skill files ==")
    seen_desc = {}
    for name in skills():
        path = os.path.join(SKILLS_DIR, name, "SKILL.md")
        fm_name, desc, lines = frontmatter(path)
        flags = []
        if fm_name != name:
            flags.append("name!=dir({})".format(fm_name))
        if not desc:
            flags.append("no-description")
        elif len(desc) > 500:
            flags.append("desc>{}".format(len(desc)))
        if lines > 120:
            flags.append("body={}>120".format(lines))
        # crude near-duplicate description check
        if desc:
            key = tuple(sorted(set(re.findall(r"[a-z]{5,}", desc.lower()))))[:14]
            if key in seen_desc:
                flags.append("desc~{}".format(seen_desc[key]))
            else:
                seen_desc[key] = name
        print("  {:<24} {:>4} lines  {}".format(name, lines, " ".join(flags) or "ok"))


def report_broken_paths():
    print("\n== Broken path claims ==")
    total = 0
    for name in skills():
        skill_dir = os.path.join(SKILLS_DIR, name)
        bad = []
        for root, _dirs, files in os.walk(skill_dir):
            for fn in files:
                if not fn.endswith(".md"):
                    continue
                fp = os.path.join(root, fn)
                try:
                    with open(fp, "r", encoding="utf-8") as fh:
                        text = fh.read()
                except Exception:
                    continue
                for m in sorted(set(PATH_RE.findall(text))):
                    cand = m.rstrip(".,);:`*")
                    # Skip globs, placeholders, and prose elisions like
                    # "PMS_React/.../charting/X.jsx" -- none are path claims.
                    if any(ch in cand for ch in "*<>") or "..." in cand:
                        continue
                    if not os.path.exists(os.path.join(WORKSPACE, cand)):
                        bad.append("{}: {}".format(fn, cand))
        if bad:
            total += len(bad)
            print("  {}".format(name))
            for b in bad[:12]:
                print("    " + b)
            if len(bad) > 12:
                print("    ... {} more".format(len(bad) - 12))
    if not total:
        print("  none")
    return total


def report_stale():
    print("== At risk from the current diff ==")
    hits = {}
    for repo in REPOS:
        for rel in git_changed(repo):
            owner = owning_skill(rel)
            if owner:
                hits.setdefault(owner, []).append(rel)
    recorded = load_stale()
    for name in sorted(recorded):
        hits.setdefault(name, [])
        hits[name] = sorted(set(hits[name]) | set(recorded[name].get("files", [])))
    if not hits:
        print("  nothing — working trees are clean and no edits were recorded")
        return
    for name in sorted(hits):
        print("  {} ({} files)".format(name, len(hits[name])))
        for f in hits[name][:10]:
            print("    " + f)
        if len(hits[name]) > 10:
            print("    ... {} more".format(len(hits[name]) - 10))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stale", action="store_true")
    ap.add_argument("--coverage", action="store_true")
    args = ap.parse_args()

    if args.stale:
        report_stale()
        return
    if args.coverage:
        report_coverage()
        return

    report_stale()
    print()
    report_coverage()
    report_health()
    report_broken_paths()


if __name__ == "__main__":
    main()
