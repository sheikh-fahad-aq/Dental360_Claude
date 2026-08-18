# fe-platform reference — wiring, env, inventory

Overflow for `fe-platform/SKILL.md`. Every line below was checked against the working tree.
Paths are relative to `PMS_React/`.

---

## 1. Environment variables

All are `VITE_`-prefixed and **baked into the bundle at build time** — readable by any visitor.
Never put a secret behind one (workspace `CLAUDE.md` §7.2). Read in `src/api/config.js` unless noted.

| Variable | Req | Read at | Purpose / effect when unset |
|---|---|---|---|
| `VITE_APP_BASE_URL_AUTH` | yes | `config.js:26` | 360auth host. Unset ⇒ `isPatientsApiEnabled()`/`isAuthApiEnabled()` false ⇒ patients, providers, rooms, services, procedure codes, labs, forms all serve mock, **and login becomes demo mode** |
| `VITE_APP_BASE_URL_APPOINTMENT` | yes | `config.js:28-33` | *Enables* the appointment target and sets the **proxy destination in `vite.config.js:26-29`**. Never appears in a browser request — `getApiBaseUrl` returns `/__appointment_api/api` |
| `VITE_APP_BASE_URL_CHART` | yes | `config.js:34-39` | Same deal for `/__chart_api/api`; proxy target at `vite.config.js:31-34`. Same host as appointments today |
| `VITE_APP_BASE_URL_PRE_AUTH` | yes | `config.js:27` | Insurance / eligibility / claims / **ledger**. Ledger refuses rather than mocking |
| `VITE_APP_X_API_Key` | yes | `config.js:51` | Sent as `x-api-key` on **every** request to all four backends (`client.js:48-51`). Note the mixed-case name |
| `VITE_CLINIC_ID` | yes | `src/api/patients.js` etc. | Clinic scope. Build-time constant — one build serves one clinic |
| `VITE_PROVIDER_ROLE_ID` | no | `src/api/lookups.js:14` | `role_id` used when creating a provider (default `'2'`) |
| `VITE_SCHEDULING_REFERENCE_NOW` | no | `src/utils/appointmentQueries.js:38` | Freezes "now" for appointment queries. **Absent from `.env.example`** |
| `VITE_API_BASE_URL` | no | `config.js:43` | Legacy single-base fallback used by `getApiBaseUrl` when a target-specific URL is unset |
| `VITE_STRIPE_PUBLISHABLE_KEY` | — | **nothing** | Listed in `.env.example` only. No source file reads it |

`.env.example` and `.env.mocktest` both exist at the repo root; `.env` is untracked.

**Gate helpers** (`config.js:55-85`) — all are "is this base URL non-empty", nothing more:
`isApiTargetEnabled(target)` · `isPatientsApiEnabled()` · `isAuthApiEnabled()` (same as patients)
· `isInsuranceApiEnabled()` · `isAppointmentApiEnabled()` · `isChartApiEnabled()`.
`src/api/locations.js:14` re-exports `isAuthApiEnabled as isLocationsApiEnabled`.

---

## 2. The four clients

`src/api/client.js` — the only file in the repo that calls `fetch()` (grep-verified: zero hits
elsewhere in `src/`).

| Export | Line | Base |
|---|---|---|
| `authApi` | `:194` | `VITE_APP_BASE_URL_AUTH`, direct |
| `preAuthApi` | `:197` | `VITE_APP_BASE_URL_PRE_AUTH`, direct |
| `appointmentApi` | `:200` | **always** `/__appointment_api/api` |
| `chartApi` | `:203` | **always** `/__chart_api/api` |
| `api` (default) | `:206` | `@deprecated` alias of `authApi` — do not use in new code |
| `ApiError`, `createApiClient`, `getAuthToken`, `setAuthToken`, `TOKEN_KEY` | `:209`, `:24`, `:14` | `TOKEN_KEY = 'pd:token:v1'` |

Method shapes (`client.js:182-190`):

```
get(path, config)            delete(path, config)
post|put|patch(path, data, config)
request(method, path, config)      getBaseUrl()
config = { params, data, headers, signal, includeBearer }
resolves  { data, status, headers }        throws ApiError { message, status, data, url }
```

Request pipeline (`client.js:132-180`): path joined to base (an absolute `http…` path bypasses the
base) → `new URL(joined, window.location.origin)` so relative proxy bases work → `params` appended,
skipping `undefined`/`null`/`''` → body `JSON.stringify`d unless `FormData` → `buildHeaders`
(`:36`) sets `Accept`, `Content-Type` (not for FormData), `x-api-key`, `Authorization: Bearer` →
`fetch` with `credentials: 'include'` → `handleResponse` (`:100`).

**401 handling is narrow** (`client.js:107-112`): `handleUnauthorized()` — clear `pd:token:v1` and
`pd:auth:v1`, hard-navigate to `ROUTES.login` — fires **only when the URL contains
`/validate_token`**. A 401 from any other endpoint just throws an `ApiError`.

Diagnostics, both `import.meta.env.DEV`-gated: `client.js:119-121` logs status + URL + body on any
failure; `client.js:167-169` logs every URL containing `appointments`. Both print URLs that carry
patient ids — the DEV gate is what keeps them compliant with `CLAUDE.md` §7.1.

### Envelope shapes

22 of the 31 modules under `src/api/` define their own local `unwrap()`. Three shapes exist:

1. `{ success, data }` — throw on `success === false`, else return `data ?? responseData`
   (`locations.js:4-12`, `patients.js:9`, `auth.js:12`)
2. bare array — returned as-is (`providers.js:15`, `labs.js:16`, `forms.js:26`, `labCases.js:19`)
3. `{ items, total, page, limit }` — paged list

`src/api/ledger.js` deliberately has none (see `fe-ledger` invariant 3).

`src/api/requestDedupe.js` — `withInflightDedupe(key, factory)` shares an in-flight promise so
concurrent identical requests hit the network once. Used by `providers.js`, `rooms.js`,
`services.js` only.

`src/api/locations.js` — 40 lines, the platform's own domain module: `fetchUserLocation(userId)`,
`fetchLocationsForUser({ userId, userRole, clinicId })` (staff hit
`/clinic_team/staff/locations/:id`, everyone else `/clinic_locations/get_all/:clinicId`),
`setUserLocation({ userId, locationId })`.

---

## 3. Routes

Registered in `src/components/AppRoutes.jsx:164-342`. Maturity from `PMS_React/README.md`.

### Public (no `ProtectedRoute`, no sidebar/header — `App.jsx:24-25` branches on pathname)

| Path | Element | Line |
|---|---|---|
| `/login` `/login/forgot-password` `/login/reset-password` `/login/otp` | Login / ForgotPassword / ResetPassword / Otp | `:165-168` |
| `/f/:token` | `PatientFormLinkPage` — **localStorage only, no backend** | `:169` |

### Protected

| Path | Element | Line | State |
|---|---|---|---|
| `/` | `PatientCharts` — `{/* <Dashboard /> */}` commented out beside it | `:171-179` | live |
| `/patients` | `PatientCharts` | `:180-187` | live |
| `/charts` | `<Navigate to="/patients" replace>` (not wrapped in `ProtectedRoute`) | `:188` | — |
| `/scheduling` | `Scheduling` | `:189-196` | live |
| `/revenue-reports` | redirect → `ROUTES.revenueReport()` = `/revenue-reports/daily-huddle` | `:197-204` | **absent from the README route table** |
| `/revenue-reports/:reportSlug` | `RevenueReports` → `DailyHuddleView` (639 lines, scheduling) | `:205-212` | see `fe-scheduling` |
| `/lists` → `/lists/:worklistId` | redirect, then `Lists` | `:213-228` | placeholder |
| `/forms` | `Forms` | `:229-236` | partial |
| `/payments` | `Payments` | `:237-244` | placeholder |
| `/ledger` | `Ledger` | `:245-252` | live |
| `/ledger/:patientId/portion` | `LedgerPortion` — **registered before** the next row | `:253-262` | live |
| `/ledger/:patientId` | `LedgerPatient` | `:263-270` | live |
| `/labs` | `Labs` | `:271-278` | live |
| `/documents` | `Documents` | `:279-286` | chrome only |
| `/fee-schedules` | `FeeSchedules` | `:287-294` | mock (in-memory) |
| `/settings` → `/settings/:sectionId` | redirect to `DEFAULT_SETTINGS_SECTION_ID`, then `Settings` | `:295-313` | 32 sections, 12 wired |
| `/patients/:patientId` + 17 children | `PatientDetail` with `<Outlet>` | `:314-341` | mixed |

Chart children (`:322-340`): index → `overview`; then `overview insurance charting history notes
family appts labs tx-plans schedule medical-hx forms images docs journal comms billing`, and a
`:section` catch-all rendering `PatientSectionPlaceholderPage`.

**There is no top-level `path="*"` route.** An unknown URL like `/nope` matches nothing: the app
chrome renders and the content area is blank, with no 404 screen and no console error.

`src/config/routes.js` also exports `DEFAULT_REVENUE_REPORT_SLUG = 'daily-huddle'` (`:36`),
`getPageTransitionKey(pathname)` (`:39`) and `isNavItemActive(navPath, pathname)` (`:62`).

### Lazy loading

Every route element is `lazy()`. Named exports out of `pages/PatientDetail.jsx` go through
`lazyNamed(importer, exportName)` (`AppRoutes.jsx:12-24`), which throws a readable
"Try a full page refresh" error instead of rendering an `undefined` HMR stub.
`Suspense` fallback picks between `AuthFallback` (`:125`) and `RouteFallback` (`:91`), the latter
switching to a chart-shaped skeleton when the path matches `/^\/patients\/[^/]+/` (`:142`).

`src/utils/routePrefetch.js`: `importRevenueReports` (shared with the `lazy()` call so one chunk is
emitted), `onIdle(fn, timeout)`, `prefetchRevenueReports()`. Called from
`scheduling/CalendarHeader.jsx`.

---

## 4. Provider tree — `src/App.jsx`

Outermost first. `App.jsx` line numbers in brackets.

```
ErrorBoundary [58]
└ QueryClientProvider [59]        src/lib/queryClient.js — staleTime 60s, gcTime 5m,
  └ BrowserRouter [60]              refetchOnWindowFocus false, retry 1; patientKeys factory
    └ ToastProvider [61]          → fe-platform
      └ AuthProvider [62]         → fe-auth
        └ ChartSettingsProvider [69]  → fe-charting (above LocationProvider on purpose:
          └ LocationProvider [70]        clinic-scoped, fetched once per session)
            └ SidebarProvider [71]    → fe-platform
              └ PatientsProvider [72]     seeded from src/data/patients — MOCK
                └ ProvidersProvider [73]
                  └ ServicesProvider [74]
                    └ RoomsProvider [75]
                      └ SchedulingProvider [76]  → fe-scheduling (69 KB)
                        ├ AppShell [77]
                        └ RouteSlipHost [78]
```

Ten context providers. The README's "9 nested providers" predates `ChartSettingsProvider`.

| Context | Size | Hook | Exposes |
|---|---|---|---|
| `ToastContext.jsx` | 6.8 KB | `useToast()` `:175` | `{ toast, toastError }`. `toast(message, { variant, description })` `:135`; id is `variant:text:detail` so repeats dedupe and restart their timer; success 3200 ms, error 5200 ms |
| `SidebarContext.jsx` | 2.0 KB | `useSidebar()` `:70` | `collapsed`, `mobileOpen`, toggles |
| `LocationContext.jsx` | 6.4 KB | `useLocationContext()` `:224` | `selectedLocation`, `setSelectedLocation`, `selectLocation`, `locations` (filtered), `allLocations`, `initialising`, `locationsLoading`, `sessionValidating`, `isApiEnabled`. Caches to `pd:selectedLocation:v1`; keeps the cached value if the API fails (`:121`) |
| `PatientsContext.jsx` | 2.0 KB | `usePatients()` `:64` | **mock** — in-memory array seeded from `src/data/patients` |
| `ProvidersContext.jsx` · `ServicesContext.jsx` · `RoomsContext.jsx` | 3.2 / 2.8 / 2.2 KB | `useProviders()` `useServices()` `useRooms()` | live lists behind `withInflightDedupe` |

`AuthContext.jsx` (14 KB) and `SchedulingContext.jsx` (69 KB) are **not** owned here.

---

## 5. Shared UI primitives — `src/components/ui/`

| File | Size | Default export signature |
|---|---|---|
| `OverlayBackdrop.jsx` | 1.5 KB | `({ onClick, position='fixed', zIndex=OVERLAY_Z_INDEX.drawerBackdropGlobal, className })`. Also `OVERLAY_Z_INDEX` `:8`, `OVERLAY_BACKDROP_CLASS` `:4`, `OVERLAY_BACKDROP_TRANSITION` `:6`, `getOverlayBackdropClassName()` `:29` |
| `Skeleton.jsx` | 8.8 KB | none — named only: `SkeletonBlock`, `PatientOverviewTabSkeleton`, `PatientInsuranceTabSkeleton`, `PatientHistoryTabSkeleton`, `PatientChartingTabSkeleton`, `PatientSubresourceSkeleton`, `PatientMobileListSkeleton`, `PatientTableSkeleton`, and a re-export of `PatientDetailPageSkeleton` `:4` |
| `SearchableSelect.jsx` | 17 KB | `({ id, value, onChange, options, loading, disabled, error, ariaLabel, required, placeholder, searchPlaceholder, … })` — grep, do not read whole |
| `ConfirmDialog.jsx` | 4.7 KB | `({ open, title, description, confirmLabel='Delete', cancelLabel='Cancel', onConfirm, onCancel, destructive=true, confirmDisabled, cancelDisabled })` — uses `useModalFocus` |
| `Tooltip.jsx` | 7.6 KB | `({ content, side='top', className, portal=true, children })` |
| `EmptyState.jsx` | 2.8 KB | `({ icon: Icon, title, description, action, variant='default', className })` |
| `PhoneInput.jsx` | 3.7 KB | `({ id, name, value, onChange, onValueChange, disabled, required, placeholder, autoComplete='tel-national', … })` — pairs with `src/constants/phone.js` |
| `Checkbox.jsx` | 1.9 KB | `({ checked, indeterminate, onCheckedChange, disabled, id, className, 'aria-label', 'aria-labelledby' })` |
| `LoadingSpinner.jsx` | 744 B | `({ label='Loading', className, size='sm', showLabel=true })` — used by `AppLoader.jsx` |
| `SimpleLoader.jsx` | 736 B | `({ label='Loading...', className, minHeightClassName='min-h-[320px]' })` — 11 call sites, the panel-level loader |
| `CopyButton.jsx` | 1.4 KB | `({ value, label='Copy chart number', className })` — **transitively dead**, only importer is `pages/PatientDetail.legacy.jsx` |
| `Breadcrumbs.jsx` | 1.4 KB | `({ items, className })` — **dead** |

`OVERLAY_Z_INDEX` (`OverlayBackdrop.jsx:8-17`):
`sidebarBackdrop 40 · sidebarDrawer 50 · drawerBackdrop 40 · drawerPanel 50 ·
drawerBackdropGlobal 60 · drawerPanelGlobal 70 · modalBackdrop 80 · modalPanel 90`.
Only these six values have static classes (`:20-27`); any other number silently falls back to
`z-40`.

---

## 6. Theming

- `src/theme/theme.css` (172 lines) — `:root` at `:14`. Sections: brand scale `:15` (`--brand-50`
  … `--brand-950`, primary `#273c75`), semantic colors `:28`, ledger code kinds `:60`, surfaces
  `:85` (incl. `--sidebar*`), typography `:98` (`--font-sans` Inter), radii `:102`, layout `:108`
  (`--sidebar-width: 15rem`, `--sidebar-width-icon: 54.4px`, `--sidebar-drawer-width`), scrollbars
  `:113`, shadows `:119`.
- `src/index.css` (946 lines) — `@import 'tailwindcss'` `:1`, `@import './theme/theme.css'` `:2`,
  `@theme inline { … }` `:9-90` bridging every var to a Tailwind utility. `blue-*` is remapped onto
  the brand scale so legacy utilities theme too. `--breakpoint-sidebar: 67.5rem` `:89` is what makes
  the `sidebar:` variant work (`AppHeader.jsx:12` `sidebar:hidden`).
- `src/theme/tokens.js` (50 lines) — JS mirror for canvas/SVG contexts: `brand`, `theme`,
  `getCssVar(name, fallback)`, `getPrimaryColor()`. Imported by `api/rooms.js`, `api/providers.js`,
  `data/scheduling.js`. **Keep hex values in sync with `theme.css` by hand — nothing enforces it.**
- `src/theme/index.js` — one-line barrel re-exporting `tokens`. **Dead**, zero importers.
- `.dark { … }` at `theme.css:126-171` is complete but **nothing ever sets `class="dark"`** — dark
  mode is aspirational.
- Other named blocks in `index.css`: `.app-scroll` `:402` (the scroll container in `AppLayout`),
  `.ledger-estimate-fill` `:137`, reduced-motion `:587`, `.app-loader*` `:621-658` (paired with the
  **commented-out** `#app-loader` div in `index.html:17-22`), two `@media print` blocks `:664`,
  `:709`.

---

## 7. Utilities, hooks, constants owned here

| Path | Exports |
|---|---|
| `src/utils/getErrorMessage.js` (150) | `getErrorMessage(error, fallback)` `:125`, `getAppointmentConflictDetails(error)` `:62` |
| `src/utils/formatName.js` (138) | `toTitleCaseWord` `toTitleCaseName` `formatNameParts` `formatName` `getNameInitials` `formatSearchPatientName` — 20 importers |
| `src/utils/formatCurrency.js` (32) | `formatCurrency(amount)` `:1`, `formatLedgerMoney(value, { withSymbol, blankOnEmpty })` `:22` |
| `src/utils/locationUtils.js` (225) | `readStoredLocation` `writeStoredLocation` `clearStoredLocation` `getLocationUserMeta` `canFetchLocations` `formatLocationDisplayName` `isExcludedLocation` `sanitizeLocations` `formatLocationRecord` `formatLocationsList` `filterLocationsForPath` `getMockLocations` — 31 importers |
| `src/utils/routePrefetch.js` (26) | `importRevenueReports` `onIdle` `prefetchRevenueReports` |
| `src/utils/searchDrawerStore.js` (37) | `searchDrawerStore` — a `useSyncExternalStore` store, deliberately outside React context so opening the drawer does not re-render the calendar |
| `src/utils/devHmrRecovery.js` (56) | `installDevHmrRecovery()` — DEV-only; reloads on `vite:preloadError` and when `#root` stays empty for 1.2 s, throttled to once per 2.5 s via `sessionStorage['pd-hmr-reload-at']`. Called once from `main.jsx:7` |
| `src/hooks/useMediaQuery.js` (28) | `useMediaQuery(query)`, `useIsMobile(breakpoint=768)` |
| `src/hooks/useModalFocus.js` (118) | default `useModalFocus({ open, dialogRef, onEscape })`, `isTopmostModal(node)` `:49` |
| `src/constants/brand.js` | `BRAND_NAME = 'Dental Practice'`, `COMPANY_NAME` |
| `src/constants/phone.js` | `PHONE_COUNTRY_CODE` `PHONE_COUNTRY_DIAL` `PHONE_NATIONAL_LENGTH` `PHONE_INPUT_PLACEHOLDER` `digitsOnly` `toNationalPhoneDigits` `formatNationalPhoneDisplay` `toPhoneE164` `isCompletePhone` `phoneValidationError` `normalizePhoneInput` |
| `src/constants/usStates.js` | `US_STATES` — **dead**, zero importers |
| `src/config/loading.js` | `MOCK_LOAD_MS = 0`, `MOCK_TAB_LOAD_MS = 0`, `MOCK_FETCH_MS` (deprecated alias). Artificial delays are off |

---

## 8. Dead code — grep-verified in this working tree

Zero importers anywhere under `src/`:

- `src/components/Dashboard.jsx` (9 lines, renders "This is dashboard") — `/` renders
  `PatientCharts`; the `<Dashboard />` call is commented out at `AppRoutes.jsx:176`
- `src/components/ui/Breadcrumbs.jsx`
- `src/constants/usStates.js`
- `src/theme/index.js` (barrel)
- **`src/pages/PatientDetail.legacy.jsx`** — not in the README's dead list. It is the only importer
  of `src/components/ui/CopyButton.jsx`, so that primitive is dead too
- `src/components/layout/RecentPatientsList.jsx` — file is live code but its only mount is
  **commented out** at `Sidebar.jsx:264`, so the sidebar's recent-patients strip never paints.
  `src/hooks/useRecentPatients.js` is **not** dead: `pages/PatientDetail.jsx:40,408` imports it and
  calls `trackPatient`, so the `practice-dental-recent-patients` localStorage key is still written —
  it just has no reader in the shell. Do not delete the hook with the component.

Also outside this skill's slice, grep-verified in this tree:
`settings/scheduling/schedulingCalendar/SchedulingCalendar.jsx` (2-line re-export barrel, no
importer), `charting/ToothBuccalGraphic.jsx`, `charting/TemplatesManagerModal.jsx`,
`charting/chartingMockData.js`, `perio/PerioScriptEditors.jsx`, `hooks/usePatientFamily.js`,
`hooks/useMockLoad.js`, `src/Untitled.base`, `src/assets/hero.png` (the live hero images are
`public/auth-hero*.jpg` via `config/authSlides.js:4`), and the 9 generic tooth SVGs directly under
`src/assets/odontogram/` (only `teeth/` is globbed).

**Two entries on the README's dead list are wrong — do not act on them.**
`components/labs/LabStatusSelect.jsx` is **live** (`pages/Labs.jsx:15`,
`patient-detail/labs/LabsSection.jsx:36`), and `components/labs/LabCaseStatusesModal.jsx`
**does not exist** — the real file is `LabCaseStatusesDrawer.jsx`, also live. See `fe-labs`.

---

## 9. Build, deploy, tooling

`vite.config.js` (83 lines): plugins `react()`, `babel({ presets: [reactCompilerPreset()] })` `:39`,
`tailwindcss()`, `fullReloadOnContextHmr()` `:11-21`. Alias `@ → src` `:44-46` (**nothing uses it**;
every import in `src/` is relative). `server.proxy` `:48-63` and `preview.proxy` `:66-81` are
byte-identical copies — change both.

Proxy target derivation `:26-34`: the env value has a trailing `/api` stripped, defaulting to
`https://api.appointment.dental360grp.com`. So `VITE_APP_BASE_URL_APPOINTMENT` must include `/api`
for the browser path `/__appointment_api/api/...` to land correctly.

`vercel.json` (17 lines) is the entire production config: rewrite `/__appointment_api/:path*` `:4-7`
and `/__chart_api/:path*` `:8-11`, both to `https://api.appointment.dental360grp.com/:path*`, then
`/(.*) → /index.html` `:12-15`. **No `headers` block** — no CSP, HSTS, X-Frame-Options or
Referrer-Policy in production. No Dockerfile, no CI workflow.

`eslint.config.js` (26 lines): flat config, globs `**/*.{js,jsx}` only (so `scripts/qa-*.mjs` get no
rules and no Node globals), ignores `dist`. `react-hooks/set-state-in-effect` is **globally off**
`:22`; `react-refresh/only-export-components` is a warn.

`index.html` (26 lines): title "Practice Dental", `theme-color` `#142866`, a **Google Fonts
stylesheet link** `:10-13` (an external network dependency at boot), and the `#app-loader` div
commented out `:17-22` — which makes `App.jsx:49`'s `getElementById('app-loader')?.remove()` a
permanent no-op.

`package.json`: name `practice-dental`, scripts `dev build lint preview`. No `engines` field, so
nothing enforces Vite 8's Node 20.19+/22.12+ requirement. Notable deps: `@tanstack/react-query`,
`framer-motion`, `react-router-dom` 7, `lucide-react`, `@tiptap/*`, `jspdf`, `simplebar-react`
(one importer: `charting/Odontogram.jsx`), and `@emotion/styled` — used by exactly one file,
`src/pages/PatientCharts.styles.js:3` (`TableScroll`), despite the README's "no
styled-components".

The app has three names: package `practice-dental`, `BRAND_NAME` "Dental Practice", document title
"Practice Dental".
