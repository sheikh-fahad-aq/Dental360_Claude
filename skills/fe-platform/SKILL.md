---
name: fe-platform
description: PMS_React app shell and the plumbing every fe-* skill defers to — src/api/client.js and its four clients (authApi, preAuthApi, appointmentApi, chartApi), /__appointment_api + /__chart_api proxies, AppRoutes.jsx/App.jsx providers, layout/ + ui/ (OVERLAY_Z_INDEX), ROUTES, theme.css, vite.config.js, vercel.json. Use when adding a page or a public /tp/ or /f/ route, an env var or is*ApiEnabled gate, changing the proxy or a shared primitive, or debugging a 401, a blank route or a full reload on save.
---

## Scope

How the SPA boots, routes, authenticates its requests, paints its chrome and gets built — the layer under every
feature skill. **Maturity: live**; the only mock thing in it is `PatientsContext`, an in-memory seed sitting in the
live provider tree. It owns the four-backend topology, the one file allowed to call `fetch`, and the two public
standalone pages. Owned elsewhere, link never edit: `AuthContext.jsx` + `/login*` → **fe-auth**; `SchedulingContext` +
`RouteSlipHost` → **fe-scheduling**; `ChartSettingsContext` → **fe-charting**; `Settings.jsx` +
`settingsNavigation.js` → **fe-settings**; `patientSections.js` + `PatientDetail.jsx` → **fe-patient-chart**.
`PMS_React/README.md` is the truth; **`PROJECT_GUIDE.md` is stale — ignore it.**

## Files

| Path (under `PMS_React/`) | Role |
|---|---|
| `src/api/client.js` | **(entry for anything on the wire)** 215 lines. `buildHeaders` `:36`, `ApiError` `:63`, `handleUnauthorized` `:73`, `handleResponse` `:100`, `createApiClient` `:132`, the four clients `:200-209` |
| `src/api/config.js` · `requestDedupe.js` · `locations.js` | 85 / 27 / 40. Proxy bases `:15-16`, per-target resolution `:25-40`, `getApiKey` `:51`, the five `is*ApiEnabled()` gates `:55-85`; `withInflightDedupe(key, factory)` (only providers/rooms/services); `fetchLocationsForUser` branches staff vs clinic |
| `src/main.jsx` · `src/App.jsx` · `ErrorBoundary.jsx` · `AppLoader.jsx` · `CommandPalette.jsx` | 13 / 106 / 279 / 9 / 183. Root render + `installDevHmrRecovery()`; **ten** context providers (README's "9" is stale) + the `AppShell` standalone-vs-chrome branch `:22-46`; stale-chunk detect and 3 s auto-reload (`:4`,`:36`); boot spinner; ⌘/Ctrl-K patient search (`:35`) |
| `src/components/AppRoutes.jsx` | 372. EVERY route — all `lazy()`, all in `ProtectedRoute` except `/login*`, `/f/:token` `:175` and `/tp/:token` `:177`. `lazyNamed` `:12`, Suspense fallbacks `:95`/`:129`, route table `:170-367` |
| `src/components/layout/` | `AppLayout.jsx` (18 — sidebar + header + `.app-scroll`), `Sidebar.jsx` (12.7 KB — `'#'` guard `:82`, outbound SSO `:121`, `RecentPatientsList` commented out `:264`), `AppHeader.jsx` (mobile only), `PracticeSwitcher.jsx` (15 KB), `UserAccountMenu.jsx` (9 KB), `LogoIcon.jsx`, `SidebarTooltip.jsx` |
| `src/components/ui/` | 19 primitives. `OverlayBackdrop.jsx` carries `OVERLAY_Z_INDEX` `:8`; `SearchableSelect.jsx` is 17 KB — grep it. `EmailTemplateEditor.jsx` (227) is the TipTap email-body composer shared by the treatment-plan and appointment-notification send modals — banner, button label and variables are props, so keep it free of any one caller's constants. Prop table in references §5 |
| `src/lib/queryClient.js` · `src/config/` · `src/context/` (generic only) | 23 / — / —. Query defaults (staleTime 60 s, no refetch-on-focus, retry 1) + `patientKeys`; `routes.js` (`ROUTES` `:2`, `getPageTransitionKey` `:45`, `isNavItemActive` `:71`), `navigation.js` (4 sidebar groups), `loading.js` (`MOCK_LOAD_MS = 0`); `ToastContext.jsx` (`useToast()` `:175`), `SidebarContext.jsx`, `LocationContext.jsx`, `Providers/Services/RoomsContext.jsx`, `PatientsContext.jsx` (**mock seed**) |
| `src/theme/theme.css` · `src/index.css` · `tokens.js` | 172 / 953 / 50. `:root` tokens `:14`; the `@theme inline` bridge `:9-90` + `--breakpoint-sidebar` `:89`; the hand-synced JS hex mirror |
| `src/utils/` · `src/hooks/` · `src/constants/` | `getErrorMessage` · `formatName` · `formatCurrency` · `locationUtils` (32 importers) · `routePrefetch` · `searchDrawerStore` · `devHmrRecovery`; `useMediaQuery` · `useModalFocus`; `brand.js` · `phone.js` (E.164) |
| `vite.config.js` · `vercel.json` · `eslint.config.js` · `index.html` · `package.json` | 83 / 17 / 26 / 26 / 46 — the whole build and deploy surface |

## Contract

**Client API**: `get|delete(path, config)` · `post|put|patch(path, data, config)` ·
`request(method, path, config)`, `config = { params, data, headers, signal, includeBearer }`. Every call
resolves to `{ data, status, headers }`, rejects with `ApiError { message, status, data, url }`, and carries
`Accept` + `x-api-key` + `Bearer` (when a token exists) + `credentials: 'include'`.

**Four clients, two topologies.** `authApi` / `preAuthApi` hit their configured host directly.
`appointmentApi` / `chartApi` **always** emit `/__appointment_api/api` and `/__chart_api/api` (`config.js:28-39`)
because those hosts refuse browser CORS — their env var only *enables* the target and sets the proxy destination,
never appearing in a browser request. **Three envelope shapes** — `{ success, data }`, a bare array,
`{ items, total, page, limit }` — and 25 of the 35 `src/api/` modules unwrap their own. The public `/tp/:token` page
is the only unauthenticated caller: `chartApi` plus an `X-Plan-Access` header minted by a date-of-birth verify POST
(`api/treatmentPlans.js:801,822,864`), held in React state only and never in browser storage (§7.3). Env table, route
table, client contract with line numbers: the reference file.

## Invariants

1. **`fetch()` belongs in `src/api/client.js`** — a bare `fetch` in a component silently drops `x-api-key` and
   `Authorization`. Grep-verified exceptions, all inside `src/api/` and all binary downloads that need the raw
   `Response`: `claims.js:496` and `documents.js:240` re-build the headers by hand from `getAuthToken()` +
   `getApiKey()`; `documents.js:271` is a bare, header-less `fetch(signed)`. Never add one outside `src/api/`.
2. **The proxy is declared three times and all three must agree**: `vite.config.js:48-63` (`server`),
   `:66-81` (`preview`), `vercel.json:3-11` (`rewrites`).
3. **Gating is env-var presence, nothing else** (`CLAUDE.md` §5) — `is*ApiEnabled()` is literally "is this base URL non-empty"
   (`config.js:55-85`). A new target needs a `BASE_URL_BY_TARGET` entry, a gate, an `.env.example` line, and — if proxied — invariant 2.
4. **A 401 only logs you out on `/validate_token`** (`client.js:107-112`); every other 401 throws for the
   caller. Do not widen it — a flaky sub-resource must not evict a working session.
5. **Never hardcode a hex**: token in `theme/theme.css`, bridge in `index.css`'s `@theme inline`, then use the
   utility (Tailwind v4, **no `tailwind.config.js`**; a JS-side colour also needs `theme/tokens.js` by hand). **Never
   hardcode a route string** — `ROUTES`; nav from `config/navigation.js` / `settingsNavigation.js` / `patientSections.js`.
6. **Overlays**: `createPortal(…, document.body)` + `AnimatePresence` + `OverlayBackdrop` with a **named**
   `OVERLAY_Z_INDEX` key. Only 40/50/60/70/80/90 have static classes (`OverlayBackdrop.jsx:20-27`); anything
   else silently renders `z-40`, and Tailwind cannot scan a dynamic `z-[n]`.
7. **Feedback is `const { toast } = useToast()`** — never `alert`; `react-hot-toast` is **not installed**.
   `toast(msg)` is success, `toast(msg, { variant: 'error', description })` / `toastError(msg)` the red one
   (`ToastContext.jsx:135,163`). Error text via `getErrorMessage(err, fallback)`.
8. **Diagnostics stay behind `import.meta.env.DEV`** (`CLAUDE.md` §7.1): `client.js:125-127` and `:173-175` log request
   URLs carrying patient ids — the DEV gate is the only thing making them legal. Nothing `VITE_`-prefixed is a secret (§7.2).
9. **Hooks return `{ items, loading, error, source, isApiEnabled, refetch, ...mutators }`**, `source` = `'api' |
   'mock' | 'api-partial'`, guarded by a monotonic request-id ref; never render `mock` as clinical fact. **ISO
   `YYYY-MM-DD` on the wire — no date library here.** **React Compiler is on** (`vite.config.js:39`): manual memoization is noise.

## Working here

**Adding a page — four edits, and the third is the one people forget:**

1. Add the path (and any builder fn) to `ROUTES` in `src/config/routes.js`.
2. Add a `lazy()` import at the top of `src/components/AppRoutes.jsx` and a `<Route>` wrapped in
   `<ProtectedRoute>`. **Order matters** — a static segment must precede a `:param` sibling
   (`/ledger/:patientId/portion` before `/ledger/:patientId`, `AppRoutes.jsx:279-294`). A **public token route**
   is the exception: it also needs its prefix added to the standalone branch in **both** `App.jsx:24-35` and
   `AppRoutes.jsx:145-147`, or the patient gets the practice's sidebar wrapped around their own document.
3. Add a nav entry to `src/config/navigation.js`, or the page is URL-only — that is how `/revenue-reports`
   (and `/revenue-reports/:reportSlug`) ended up unreachable from the sidebar; `/forms` has one, `navigation.js:44`.
4. Add a `getPageTransitionKey` branch (`routes.js:45`) if it needs its own transition, and an
   `isNavItemActive` branch (`:71`) if its highlight rule is not "exact or `/`-prefixed".

**A backend call**: one export in the matching `src/api/<domain>.js` using that module's local `unwrap()`, exporting
a `normalizeX(raw)`, with an `if (!isXApiEnabled())` mock branch. Never `fetch`. **A shared primitive**:
`src/components/ui/`, `className` last; if it overlays anything add the layer to `OVERLAY_Z_INDEX` *and*
`Z_INDEX_CLASS`. Verify by loading the page and watching the request, then `npm run lint` — **no test suite, no CI**.

## Traps

- **NEVER BUILD A URL FROM A MIXED SOURCE — this repo has been bitten twice.** `BrowserRouter`
  wraps navigations in `startTransition` and every route in `AppRoutes.jsx` is `lazy()`, so
  `navigate()` moves `window.location` **synchronously** while `useLocation()` stays on the OLD
  value for the whole chunk fetch — hundreds of ms, not microseconds. Any effect that writes a URL
  inside that window and takes its pathname from React but its query from `window.location` (or
  calls `setSearchParams`, which resolves `"?…"` against the ROUTER's pathname) will
  `replaceState` the old pathname carrying the new query string, destroying the history entry the
  outbound navigation just made. The symptom is "the button did nothing".
  - `pages/PatientDetail.jsx` (the seed-state strip) — fixed: a `seedAppliedRef` latch plus a bail
    when the live URL no longer matches the rendered one. Both are load-bearing.
  - `pages/Scheduling.jsx` (`SchedulingQueryParams`' param strip) — fixed the same way. Its
    `openNewAppointment` dep rotates with the operatory list, i.e. **independently of the
    location**, which is what let it fire inside the stale window.
  - Rule: take every half of a URL from the same source, and bail if `window.location` has already
    moved on.
- **`AppLoader` must not lift on `requestAnimationFrame` alone** (`src/App.jsx`). A hidden or
  non-compositing tab never runs one, so the full-screen `fixed inset-0 z-50` overlay stayed up
  and swallowed every pointer while the app rendered normally underneath — "the button is dead",
  not "still loading". It now has a timeout floor alongside the frame. The same rAF dependency is
  why framer-motion exit animations never finish in a background tab, leaving `AnimatePresence`
  backdrops in the DOM at `opacity: 0` with `pointer-events: auto`.

- **Editing anything under `src/context/` forces a full page reload** — `fullReloadOnContextHmr()`,
  `vite.config.js:11-21`: Fast Refresh cannot patch hook exports, so in-memory state is lost by design.
- **`vercel.json` has no `headers` block** — production ships with **no CSP, HSTS, X-Frame-Options or
  Referrer-Policy**, `index.html:10-13` pulls Google Fonts at boot, and there is no Dockerfile and no CI.
- **There is no `path="*"` route** — an unknown URL renders the chrome over an empty content area, no 404 and no console error; a typo in a `ROUTES` value fails exactly this silently.
- **`/` renders `PatientCharts`; `src/components/Dashboard.jsx` is dead** — `<Dashboard />` is commented out at
  `AppRoutes.jsx:184`. Five more grep-verified dead files, the live hook inside a dead component
  (`useRecentPatients`), and the two README dead-list entries that are *wrong* are inventoried in references §8.
- **`theme.css:126-171` is a complete `.dark` palette nothing activates** — no code sets `class="dark"`. **`CommandPalette.jsx:90` uses `z-[95]`, outside `OVERLAY_Z_INDEX`** (its backdrop uses the map) and
  `ledger/LedgerPopover.jsx:22` has a local `POPOVER_Z = 120` — check both before raising a layer.
- **The proxy target strips a trailing `/api`** (`vite.config.js:26-34`) — `VITE_APP_BASE_URL_APPOINTMENT` must *include* `/api` for `/__appointment_api/api/...` to resolve. And `PatientsContext` is a live-tree mock.
- **Small doc lies, all verified** (line-level detail in references §9): `@emotion/styled` has one importer despite
  "no styled-components"; `index.html`'s `#app-loader` div is commented out so `App.jsx:59` is a no-op;
  `react-hooks/set-state-in-effect` is globally off; the `@ → src` alias is used by nothing; and
  `/revenue-reports/:reportSlug` (`AppRoutes.jsx:213-220`) is missing from the README's route table. The unsanitized
  HTML sinks (§7.4) sit just outside this slice — `dangerouslySetInnerHTML` at
  `scheduling/VisitStatusBoard.jsx:1065`, `innerHTML =` at `patient-detail/notes/noteTemplates.js:122`.

## See also

- `references/wiring-and-inventory.md` — env-var table, four-client contract, the complete route table with
  maturity, the provider tree, every `ui/` prop signature, the theme token map, the verified dead-code
  inventory, and the build/deploy surface.
- `main-architecture` — hub, index, change log. All twelve siblings defer here: `fe-auth` (AuthContext, `/login*`,
  SSO, browser storage), `fe-scheduling`, `fe-patient-chart` (the treatment-plan domain behind `/tp/`), `fe-charting`,
  `fe-perio`, `fe-ledger`, `fe-insurance-claims`, `fe-settings`, `fe-labs`, `fe-forms` (the `/f/` page),
  `fe-payments-fees`, `fe-reports-worklists`. `be-platform` is the Flask side of the two proxied hosts;
  `be-treatment-plans` owns the `/tp/` API. `PMS_React/README.md` → "The four backends", "Conventions",
  "Deployment", "Known gaps and traps".
