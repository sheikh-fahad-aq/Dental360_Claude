---
name: dental360-workspace-shape
description: The Dental360 workspace is three independent git repos, not a monorepo — commits never span them, and most frontend API calls target backends that are not checked out.
metadata:
  type: project
---

`D:\Dental360` looks like a monorepo but is a container for **three independent git
repositories**: `360_Flask_Appointment` (branch `fahad`), `PMS_React` (branch
`feature/charting`), and `.claude` (branch `main`, remote `Dental360_Claude.git`). No
git repo exists at the container level.

Two consequences that are easy to get wrong:

1. **A commit never spans two repos.** Backend and frontend changes for one feature ship as
   separate commits, and they deploy independently — land the backend first.
2. **The SPA talks to four backends and only one is checked out here.** Just 8 of its 31
   `src/api/*.js` modules reach `360_Flask_Appointment` (via the `appointmentApi` and
   `chartApi` clients). The other 23 target `360auth` and a pre-auth/eligibility API, which
   are external services with no source in this workspace. Reading Flask routes to debug an
   `authApi` or `preAuthApi` call wastes time and actively misleads.

**Why:** both mistakes look reasonable from the directory layout, and neither produces an
error that points at the real cause.

**How to apply:** check which client an API module imports before looking for a route, and
use `/ship` rather than staging across directories. See
[[dental360-claude-tooling]] for where this is written down.
