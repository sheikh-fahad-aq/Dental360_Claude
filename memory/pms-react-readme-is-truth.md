---
name: pms-react-readme-is-truth
description: PMS_React/README.md is an unusually accurate architecture doc and the frontend's source of truth; PROJECT_GUIDE.md in the same repo is stale and misleading.
metadata:
  type: reference
---

`PMS_React/README.md` (~33KB) is the authoritative description of the frontend: the
four-backend topology, the env-var table, the auth flow, the route list, per-module and
per-chart-section maturity tables, the conventions, and a candid "Known gaps and traps"
section that names real security findings with `file:line`.

Its `live` / `mock` / `partial` / `placeholder` labels are honest and load-bearing —
**several mock surfaces look completely finished on screen**. Believe the label, not the UI.

`PMS_React/PROJECT_GUIDE.md` in the same repo is stale and actively misleading: it claims
the app is a prototype with no backend, and its folder tree omits `src/api` entirely.

**Why:** trusting the wrong one of these two files leads either to rebuilding something
that exists or to demoing fabricated clinical data as real.

**How to apply:** read the README section for the area before exploring source; it is
usually faster and more accurate than the code. Its content has been distilled into the
`fe-*` skills, so those are the cheaper entry point — see [[dental360-claude-tooling]].
