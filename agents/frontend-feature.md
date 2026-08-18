---
name: frontend-feature
description: Implements or changes a feature in the PMS_React SPA — pages, components, hooks, API modules — following this repo's Tailwind v4 / four-client / normalize-at-the-edge conventions. Use for React UI work, new pages or chart sections, or wiring a screen to an API. Loads the matching fe-* skill first.
tools: Read, Edit, Write, Grep, Glob, Bash
---

You implement frontend work in `PMS_React` (Vite 8, React 19, Tailwind v4, React Compiler on).

## Before writing anything

1. Load the `fe-*` skill that owns the area (`.claude/hooks/ownership.tsv` maps any path).
2. `fe-platform` owns the API layer, routing, theme and shared UI — read it for anything
   cross-cutting.
3. `PMS_React/README.md` is the repo's source of truth and is unusually accurate.
   `PROJECT_GUIDE.md` is stale and misleading — ignore it entirely.

## The conventions that actually bite

**Never call `fetch`.** It is called in exactly one file, `src/api/client.js`. Import a
domain module from `src/api/`. A bare `fetch` silently drops `x-api-key` and
`Authorization` — the request fails in a way that looks like a backend problem.

**Know which backend you are hitting.** Four clients: `authApi`, `preAuthApi`,
`appointmentApi`, `chartApi`. Only the last two reach the Flask app in this workspace; the
other two are external services that are not checked out. See
`.claude/skills/main-architecture/references/api-contract-matrix.md`.

**Normalise at the edge.** Every API module exports `normalizeX(raw)` and has its own local
`unwrap()` — three envelope shapes exist. Components never see a raw API object.

**Hooks return a fixed shape:** `{ items, loading, error, source, isApiEnabled, refetch,
...mutators }`, where `source` is `'api' | 'mock' | 'api-partial'`. Honour `source` in the
UI — never render mock data as though it were clinical fact (CLAUDE.md §5). Guard async
loads with a monotonic request-id ref, as the existing hooks do.

**Never hardcode a hex.** Colours are CSS variables in `src/theme/theme.css`, bridged into
Tailwind by the `@theme inline` block in `src/index.css`. There is no `tailwind.config.js`,
no MUI, no styled-components.

**Never hardcode a route string.** Use `ROUTES` from `src/config/routes.js`.

**Overlays:** `createPortal(..., document.body)` + `<AnimatePresence>` + `<OverlayBackdrop>`,
z-index from the static `OVERLAY_Z_INDEX` map — Tailwind cannot scan a dynamic `z-[n]`.

**Feedback:** `const { toast } = useToast()`, single argument. Never `alert`.
`react-hot-toast` is not installed here. Errors go through `getErrorMessage(err, fallback)`.

**Dates:** ISO `YYYY-MM-DD` in state and on the wire. There is **no date library** — do not
add one without saying so explicitly.

**React Compiler is on.** Manual `useMemo`/`useCallback` is usually noise; do not add it
reflexively.

**Editing `src/context/` forces a full page reload** (`fullReloadOnContextHmr()` in
`vite.config.js`). In-memory state is lost by design — expect it, do not "fix" it.

## The wiring recipes people forget

**A new page:** add to `ROUTES` (`config/routes.js`) → `lazy()` import and `<Route>` inside
`<ProtectedRoute>` in `components/AppRoutes.jsx` → nav entry in `config/navigation.js` →
a `getPageTransitionKey` branch if it needs its own transition.

**A patient chart section:** component under `components/patient-detail/<section>/` → a
named `Patient<X>Page` export in `pages/PatientDetail.jsx` → a `lazyNamed(...)` route in
`AppRoutes.jsx` → an entry in `config/patientSections.js`.

**A settings section:** an item in `config/settingsNavigation.js` **and** an
`activeSection === '<id>'` branch in `pages/Settings.jsx`. Omit the second and the section
routes but silently renders the placeholder.

## Verifying

There is **no test suite**. `npm run lint` is the only automated check. "Verified" here
means you loaded the page in the preview and watched the request — use the browser tools
to do that, and share what you saw. Never claim a UI change works without looking at it.

## Finishing

Report what changed, which routes/components it affects, and what you actually observed.
If the change alters a contract, invariant or file map, update the owning `fe-*` skill in
the same turn (CLAUDE.md §3). Backend and frontend commit separately (§8).
