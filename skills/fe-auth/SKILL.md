---
name: fe-auth
description: Frontend authentication, session and access control — /login, /login/otp, /login/forgot-password, /login/reset-password, AuthContext, ProtectedRoute, and the inbound ?token= SSO handoff. Use when changing PMS_React/src/context/AuthContext.jsx, src/api/auth.js, src/components/auth/** or the four login pages; touching pd:token:v1 / pd:auth:v1, POST /login, /verify_2fa, /auth_profile, /validate_token or /user_dashboards; or when demo mode signs you in with no backend.
---

## Scope

Password + TOTP sign-in, the JWT session, revalidation, logout, password reset, and both SSO
directions. **Maturity: live** against `360_flask-auth`, the only token issuer — this SPA consumes
(`README.md:130-153`). It owns *whether* you have a session, never *what you may do with it*: there
is **no client-side role gating in this app** (§7.7). Logout is here, so is the storage census.

## Files

| path (under `PMS_React/`) | role |
|---|---|
| `src/context/AuthContext.jsx` | **(entry)** 476 lines. The session machine: bootstrap `:213-273`, 5-min revalidate `:276-285`, `validateSession` `:182-211`, `completeSession` `:158-175`, `logout` `:141-145`, six mutators `:287-427`, `value` memo `:435-467`. |
| `src/api/auth.js` | 210. Eight exports on `authApi`; `unwrap` `:11`, `extractAccessToken` `:23`, `mapProfileToUser` `:135`, `PUBLIC = { includeBearer: false }` `:4`. |
| `src/components/auth/ProtectedRoute.jsx` | 43. Redirect gate `:38`, per-navigation revalidate `:33-36`, `SessionGate` spinner `:6-22`. |
| `src/components/auth/AuthShell.jsx` · `AuthHeroPanel.jsx` · `src/config/authSlides.js` | 41 / 138 / 47. Two-column card used by all four pages; autoplay hero carousel (6.5 s, honours `useReducedMotion`); three slides whose images live in `public/`. |
| `src/pages/LoginPage.jsx` · `OtpPage.jsx` | 310 / 223. Email + password (validation `:40-66`, submit `:68-87` → `ROUTES.otp`); six boxed digits with paste/arrow/backspace, auto-submit when full `:58-64`, QR enrolment block `:140-151`. |
| `src/pages/ForgotPasswordPage.jsx` · `ResetPasswordPage.jsx` | 130 / 228. Request a code; code + new password (≥8, confirmed) → `ROUTES.login` with a success message. |

Touches (shared, not owned): `src/api/client.js:14,24,73-85,107-112` (`TOKEN_KEY`, `setAuthToken`,
`handleUnauthorized`); `api/config.js:75-77`; `App.jsx:24,27,61-62`; `AppRoutes.jsx:79-82,165-168`;
`config/routes.js:3-6,40`; `layout/UserAccountMenu.jsx:30,109-114` (the only `logout()` caller);
outbound SSO = `layout/Sidebar.jsx:24-30,82-88,121-133` + `config/navigation.js:42`
(`externalApp: 'connect'`) + `utils/locationUtils.js:45-58` (`userId`).

## Contract

Everything goes through `src/api/auth.js` on `authApi` (base `VITE_APP_BASE_URL_AUTH`) — no proxy,
unlike `appointmentApi` / `chartApi`. `POST /login {email,password}` → `{temp_token, qr_code?}` ·
`POST /verify_2fa {token,temp_token}` → JWT · `GET /auth_profile` · `POST /forgot-password {email}` ·
`POST /verify-otp {otp,new_password}` · `GET <hostRoot>/validate_token` (**outside `/api`**) ·
`GET /user_dashboards/<userId>` · `POST /dashboard/check` (**dead**). First four send `PUBLIC`
(no bearer); payload shapes in `references/session-and-storage.md` §1.

Renders `ROUTES.login` / `.otp` / `.forgotPassword` / `.resetPassword` — lazy, registered **above**
the `ProtectedRoute` block (`AppRoutes.jsx:165-168`); `App.jsx:24` drops the sidebar shell for
`/login*`. `useAuth()` exposes `user`, `isAuthenticated`, `sessionValidating`, `pendingEmail`,
`pendingQrCode`, `isAuthApiEnabled`, six mutators, `validateSession`, `logout`, `clearPending` — and
throws outside the provider (`:474`).

## Invariants

1. **Exactly two auth keys**: `pd:token:v1` (written only by `setAuthToken`, `client.js:24`) and
   `pd:auth:v1` (`AuthContext:25`). Never write the token elsewhere; never add a third.
2. **`AuthProvider` sits directly inside `ToastProvider`, above every data provider**
   (`App.jsx:61-62`) — it needs `useToast` and nothing else. Do not reorder.
3. **`validate_token` is on the auth host root, not `/api`** — `getAuthHostRoot()` strips the trailing
   `/api` (`auth.js:7-9,81-86`); never call it as a bare relative path. **Pre-token calls must pass
   `PUBLIC`** (`:4`) — login, verify_2fa, forgot-password, verify-otp; a stale bearer gets rejected.
4. **Network/timeout never logs out; only an auth failure does** (`AuthContext:197-204`, 7 s abort
   `:26,98-106`). Keep that split — flaky wifi must not dump a clinician mid-chart.
5. **Every mutator resolves `{ ok, error }` and never throws** (`AuthContext:287-427`); pages render
   `result.error` inline. Do not wrap a call site in try/catch or a toast.
6. **Dual-mode by env presence** (§5): `isAuthApiEnabled()` is only "is `VITE_APP_BASE_URL_AUTH`
   non-empty" (`api/config.js:75-77`). Every new auth call needs an `if (!isAuthApiEnabled())` branch.
7. **`user.role` / `user_role` are display fields** (`auth.js:164-176`). Never hide a control as a
   permission boundary, never send a client-chosen role — enforce in the Flask route (§7.7).
8. **Never log a token, `temp_token`, email or a `?token=` URL** (§7.1) — `AuthContext.jsx` has no
   `console.*` today. **Never render an auth payload as markup** (§7.4): the one server blob here is
   the QR, kept as `<img src="data:image/png;base64,…">` (`OtpPage.jsx:146`).
9. **No `fetch` in this slice** — import from `src/api/auth.js`. `ROUTES` not literals, `useToast()`
   not `alert`, theme tokens (`primary`, `brand-100`, `ring`) not hexes.

## Working here

1. **New endpoint** → one export in `src/api/auth.js` reusing the local `unwrap` (`:11`), plus
   `PUBLIC` if it runs pre-token. Then a `{ok,error}` mutator in `AuthContext`, added to **both** the
   `value` object and its dependency array (`:435-467`) — the forgotten step.
2. **New auth page** → page in `src/pages/` wrapped in `AuthShell`; a `ROUTES` entry
   (`routes.js:3-6`); a `lazy()` import (`AppRoutes.jsx:79-82`); a `<Route>` above the
   `ProtectedRoute` block (`:165-168`). Off `/login`? extend `App.jsx:24` too, or it renders in the
   sidebar shell. **New hero slide** → `authSlides.js` + an image in `public/`, world-readable after
   deploy (§7.6), so nothing clinical or internal.
3. **Changing where sign-in lands** → five `ROUTES.scheduling` guards (`LoginPage:52`, `OtpPage:45,67`,
   `Forgot:17`, `Reset:40`); the chain hops are `LoginPage:83`, `Forgot:33`, `Reset:102`. All eight.
4. Verify by loading `/login` and watching `/login` → `/verify_2fa` → `/auth_profile`, then
   `npm run lint`. No test suite; "verified" means you watched the requests.

## Traps

- **The 401 auto-logout fires only for `/validate_token`** — `handleUnauthorized()` is gated on the
  request URL (`client.js:107-112`), so a 401 from `/auth_profile` or any data route leaves both keys
  in place and only surfaces an error; when it does fire it is `window.location.assign` (`:83`), a
  full reload. The README's flat "on 401 it clears both keys" holds only through that one path.
- **DEMO MODE.** Unset `VITE_APP_BASE_URL_AUTH` and any 4+ char password (`AuthContext:294`) and any
  6-digit code (`:324`) sign you in with a fake `demo.<btoa(email)>.<ts>` token (`:335`);
  `isAuthenticated` then ignores the token entirely (`:429-433`). The only tell is one footer line on
  the OTP page (`OtpPage.jsx:133-136`) — the login page gives none, and `/login/reset-password` is
  unreachable because Forgot stops at "Check your inbox" (`ForgotPasswordPage.jsx:32`).
- **The SSO fallback is an *unverified* base64 decode.** When `/auth_profile` fails after a `?token=`
  handoff, `completeSession` falls back to `decodeJwtPayload` (`AuthContext:29-38,163-168`) — no
  signature or expiry check. Display fields only; never derive anything from it.
- **Any `?token=` in the URL disables revalidation.** `validateSession` returns
  `{ok:true, skipped:true}` whenever `hasTokenInUrl()` (`AuthContext:73-79,184-185`) — a global check,
  not one scoped to the handoff — so the 5-minute timer and the per-navigation check both go quiet.
  Bootstrap strips the param with `history.replaceState` (`:222-227`). Relatedly, **a
  `{success:false}` body counts as unauthorized**: `isAuthFailureError` treats `error.status == null`
  as an auth failure (`:90-96`), so any envelope error from `unwrap` (`auth.js:14`) logs the user out.
- **Fourteen browser-storage keys are written; two are ever cleared** (§7.3) — `logout()` is only
  `persistUser(null)` + `setAuthToken(null)` (`:141-145`). The README says thirteen; it misses
  `pd:patient-chart-panel-collapsed` (`PatientDetail.jsx:417`). Survivors include
  `pms.visitStage.<appointmentId>`, `pms.checkInWizardSkipped.<appointmentId>`,
  `pd:medical-hx-reviewed:<patientId>` and `chart_owned_session_<patientId>` — ids **in the key name**,
  so on a shared front desk the key list is itself a record of which patients were opened. Never add
  another. Census: `references/session-and-storage.md` §2.
- **`pd:auth:v1` holds the whole `/auth_profile` payload** — `mapProfileToUser` keeps
  `profile: profile ?? null` (`auth.js:208`) — in clear, until logout. **Deep-link return is
  dropped**: `ProtectedRoute:39` sets `state={{ from: location.pathname }}` and nothing reads it
  (grep-verified), so every sign-in lands on `/scheduling`.
- **Three convention violations already here** — fix, do not copy: `AuthHeroPanel.jsx:92` hardcodes
  `to="/login"` instead of `ROUTES.login`; `AuthContext:60` uses its own `formatAuthError` rather than
  `getErrorMessage`; `authSlides.js` has literal `rgba()`. Dead export: `checkDashboardAccess:62`.

## See also

`references/session-and-storage.md` (endpoint table, storage census, session state machine,
demo-mode matrix, outbound SSO) · `main-architecture` (hub) · **`fe-platform`** (owns `api/client.js`,
`api/config.js`, `AppRoutes.jsx`, `App.jsx` — every file in Touches above) · `be-platform`
(`x-api-key`/Bearer on the Flask side; `360_flask-auth` itself is **not** checked out here) ·
`fe-charting` (`chart_owned_session_*`) · `fe-scheduling` (`pms.visitStage.*`) · `fe-patient-chart`
(`pd:medical-hx-reviewed:*`) · `fe-forms` (`/f/:token`) · `PMS_React/README.md` → "Authentication".
