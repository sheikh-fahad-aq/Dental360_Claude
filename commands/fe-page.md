---
description: Add a page, patient chart section, or settings section to the SPA
argument-hint: "<page|section|settings> <name> — what it shows"
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, Task
---

Add the surface described by `$ARGUMENTS` to `PMS_React`.

Load `fe-platform` (routing, API layer, shared UI) plus the skill owning the feature area.
For a substantial screen, delegate to the `frontend-feature` agent.

These are multi-file wiring recipes, and **every one of them fails silently if you miss a
step** — no error, just a page that does not route or renders a placeholder.

## A top-level page — 4 edits

1. `src/config/routes.js` — add the path to `ROUTES`. Never use a literal route string
   anywhere else.
2. `src/components/AppRoutes.jsx` — a `lazy()` import and a `<Route>` wrapped in
   `<ProtectedRoute>`.
3. `src/config/navigation.js` — the sidebar entry.
4. `src/config/routes.js` — a `getPageTransitionKey` branch, if it needs its own transition.

## A patient chart section — 4 edits

1. The component under `src/components/patient-detail/<section>/`.
2. A named `Patient<X>Page` export in `src/pages/PatientDetail.jsx`.
3. A `lazyNamed(...)` route in `src/components/AppRoutes.jsx`.
4. An entry in `src/config/patientSections.js`.

Note the existing `audit-trail` id → `/history` URL mismatch before assuming id and path
must match.

## A settings section — 2 edits

1. An item in the right group's `items` in `src/config/settingsNavigation.js`.
2. An `activeSection === '<id>'` branch in `src/pages/Settings.jsx`.

**Without the second, the section routes and silently renders the placeholder.** Roughly 20
of the 32 sections are in exactly that state, so it looks normal and nobody notices.

## Building the screen itself

- Data comes from a module in `src/api/` — never a bare `fetch` (it drops `x-api-key` and
  `Authorization`). New endpoint? Add it to the domain module with a `normalizeX(raw)` and a
  local `unwrap()` matching the envelope the backend returns.
- A new hook returns `{ items, loading, error, source, isApiEnabled, refetch, ...mutators }`
  and guards async loads with a monotonic request-id ref. Honour `source` — never render
  mock data as clinical fact (CLAUDE.md §5).
- Colours are CSS variables, never hex. Tailwind v4 utilities only.
- Overlays: `createPortal` + `AnimatePresence` + `OverlayBackdrop`, z-index from the static
  `OVERLAY_Z_INDEX` map.
- Feedback via `useToast()`; errors via `getErrorMessage(err, fallback)`.
- React Compiler is on — skip manual memoization.

## Verify

There is no test suite. `npm run lint`, then load the page in the preview and watch the
request. Report what you actually saw — never claim a UI change works without looking.

Then update the owning `fe-*` skill (new files, new route, changed recipe) and commit
frontend-only — `/ship frontend`.
