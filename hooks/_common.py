"""Shared helpers for the Dental360 Claude hooks.

Deliberately stdlib-only and dependency-free: hooks run on every matching tool
call, so import cost is latency the user pays for. Nothing here may raise --
a crashing hook is far more disruptive than a missed changelog line.
"""

import fnmatch
import json
import os
import sys

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
CLAUDE_DIR = os.path.dirname(HOOKS_DIR)
WORKSPACE = os.path.dirname(CLAUDE_DIR)

SKILLS_DIR = os.path.join(CLAUDE_DIR, "skills")
ARCH_DIR = os.path.join(SKILLS_DIR, "main-architecture")
CHANGELOG = os.path.join(ARCH_DIR, "CHANGELOG.md")
STALE_FILE = os.path.join(ARCH_DIR, ".stale.json")
OWNERSHIP = os.path.join(HOOKS_DIR, "ownership.tsv")


def read_event():
    """Parse the hook payload from stdin. Returns {} rather than dying."""
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def rel_path(path):
    """Workspace-relative POSIX path, or None if the path is outside it.

    Windows hands us backslashes and inconsistent drive-letter case, so
    normalise both before comparing.
    """
    if not path:
        return None
    try:
        abs_path = os.path.abspath(path)
        root = os.path.abspath(WORKSPACE)
        if os.name == "nt":
            if not abs_path.lower().startswith(root.lower()):
                return None
        elif not abs_path.startswith(root):
            return None
        return os.path.relpath(abs_path, root).replace(os.sep, "/")
    except Exception:
        return None


_RULES_CACHE = None


def ownership_rules():
    """[(glob, skill)] in file order. First match wins, so order is load-bearing."""
    global _RULES_CACHE
    if _RULES_CACHE is not None:
        return _RULES_CACHE
    rules = []
    try:
        with open(OWNERSHIP, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if "\t" not in line:
                    continue
                pattern, skill = line.split("\t", 1)
                rules.append((pattern.strip(), skill.strip()))
    except Exception:
        rules = []
    _RULES_CACHE = rules
    return rules


def owning_skill(rel):
    """Which skill documents this file? None when nothing claims it."""
    if not rel:
        return None
    for pattern, skill in ownership_rules():
        if fnmatch.fnmatch(rel, pattern):
            return skill
        # A directory glob like "a/b/*" should also claim "a/b/c/d.js".
        if pattern.endswith("/*") and rel.startswith(pattern[:-1]):
            return skill
    return None


def load_stale():
    try:
        with open(STALE_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_stale(data):
    try:
        os.makedirs(ARCH_DIR, exist_ok=True)
        tmp = STALE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
        os.replace(tmp, STALE_FILE)
    except Exception:
        pass


def tool_paths(event):
    """Every file path a tool call touches, across the editing tool shapes."""
    ti = event.get("tool_input") or {}
    out = []
    for key in ("file_path", "notebook_path", "path"):
        val = ti.get(key)
        if isinstance(val, str) and val:
            out.append(val)
    edits = ti.get("edits")
    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict):
                val = edit.get("file_path")
                if isinstance(val, str) and val:
                    out.append(val)
    seen, uniq = set(), []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq
