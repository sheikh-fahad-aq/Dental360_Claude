# fe-auth reference — wire, storage, session lifecycle

Loaded on demand. Every line below was checked against the working tree; anything unconfirmed is
marked **unverified**. Paths are relative to `PMS_React/`.

---

## §1 Endpoint table

All eight live in `src/api/auth.js` and go out on `authApi` (base `VITE_APP_BASE_URL_AUTH`, i.e. a
direct cross-origin call — the `/__appointment_api` / `/__chart_api` proxies are not involved).
`PUBLIC = { includeBearer: false }` is defined at `auth.js:4`.

| export | line | method + path | bearer | request | response used |
|---|---|---|---|---|---|
| `loginWithPassword` | `:43` | `POST /login` | no | `{ email, password }` | `temp_token` \| `tempToken`; `qr_code` \| `qrCode` |
| `verifyLoginOtp` | `:48` | `POST /verify_2fa` | no | `{ token, temp_token }` | spread + `accessToken` from `extractAccessToken` |
| `fetchAuthProfile` | `:57` | `GET /auth_profile` | yes | — | whole profile → `mapProfileToUser` |
| `checkDashboardAccess` | `:62` | `POST /dashboard/check` | yes | `{ profile }` | **dead — no caller anywhere in `src/`** |
| `requestForgotPassword` | `:67` | `POST /forgot-password` | no | `{ email }` | ignored (success only) |
| `resetPasswordWithOtp` | `:72` | `POST /verify-otp` | no | `{ otp, new_password }` | ignored (success only) |
| `validateAuthToken` | `:81` | `GET <hostRoot>/validate_token` | yes | `{ signal }` | ignored; throw = invalid |
| `fetchUserDashboards` | `:93` | `GET /user_dashboards/<userId>` | yes | — | `{ user_id, dashboards[] }` |

Plus two non-network exports: `openUserDashboardApp` (`:113`, see §5) and `mapProfileToUser`
(`:135`, see §6). `isAuthApiEnabled` is re-exported from `src/api/config.js` at `:41`.

**`getAuthHostRoot()` (`:7-9`)** takes `getApiBaseUrl(API_TARGETS.auth)` and strips a trailing
`/api`, because `validate_token` is mounted on the host root rather than under the `/api` prefix.
If the base URL is empty it falls back to the relative `'/validate_token'` (`:83`).

**`unwrap` (`:11-21`)** is this module's own envelope reader — one of the three shapes in the repo.
It only unwraps when the body has a `success` key: `success: false` throws an `ApiError` built from
`error` \| `detail` with **no HTTP status**, which is exactly the case §3 treats as unauthorized.

**`extractAccessToken` (`:23-39`)** accepts `token`, `access_token` or `accessToken`, and as a last
resort parses a `redirect_to` / `redirectTo` URL and lifts its `token` query param. That is the same
shape as the inbound SSO handoff.

### Token attachment

`src/api/client.js:36-61` (`buildHeaders`) puts `x-api-key` on every request and
`Authorization: Bearer <pd:token:v1>` on every request that did not pass `includeBearer: false`.
Every request also carries `credentials: 'include'` (`:176`). A bare `fetch` bypasses all of it.

---

## §2 Browser storage census

**Fourteen keys are written across `src/`; two are ever removed.** `PMS_React/README.md:156-163`
lists thirteen — it omits `pd:patient-chart-panel-collapsed`. A fifteenth, `pd-hmr-reload-at`, is
written only under `import.meta.env.DEV` and is not counted.

| key | store | declared at | cleared on logout/401 |
|---|---|---|---|
| `pd:token:v1` | local | `api/client.js:14` (`TOKEN_KEY`) | **yes** — `setAuthToken(null)` |
| `pd:auth:v1` | local | `context/AuthContext.jsx:25` (`AUTH_KEY`) | **yes** — `persistUser(null)`; also `client.js:76` |
| `practice-dental-recent-patients` | local | `hooks/useRecentPatients.js:3` | no |
| `pd:medical-hx-reviewed:<patientId>` | local | `patient-detail/medical-hx/MedicalHxSection.jsx:46` | no — **patient id in key name** |
| `pms_patient_form_links_v1` | local | `utils/patientFormLinkStore.js:6` | no |
| `pms.visitStage.<appointmentId>` | local | `utils/visitStatusTracker.js:86` | no — **appointment id in key name** |
| `pms.checkInWizardSkipped.<appointmentId>` | local | `utils/visitStatusTracker.js:87` | no — **appointment id in key name** |
| `pms.recallDueDateOffsets` | local | `components/lists/RecallDueDateSettingsModal.jsx:9` | no |
| `pd:selectedLocation:v1` | local | `utils/locationUtils.js:3` | no |
| `pd:settings:schedulingTab:v1` | local | `components/settings/scheduling/schedulingConstants.js:17` | no |
| `pd:schedule:fitToScreen` | local | `context/SchedulingContext.jsx:177,186` (literal) | no |
| `pms.payments.setupConnected` | **session** on write | `pages/Payments.jsx:20` | no |
| `chart_owned_session_<patientId>` | **session** | `patient-detail/charting/chartOwnership.js:22` | no — **patient id in key name**; per-tab by design (§7.5) |
| `pd:patient-chart-panel-collapsed` | **session** | `pages/PatientDetail.jsx:417,427` (literal) | no — *missing from the README list* |
| `pd-hmr-reload-at` | session | `utils/devHmrRecovery.js:11` | n/a — DEV only |

### Two findings worth knowing

- **`pms.payments.setupConnected` is written to `sessionStorage` and read from `localStorage`.**
  `pages/Payments.jsx:42,50` uses `sessionStorage`; `hooks/useSettingsNavStatus.js:62` uses
  `localStorage`. The settings-nav "Connected" badge can therefore never light up from the Payments
  screen. Owned by `fe-settings` / the Payments surface, recorded here because the census found it.
- **`logout()` is three calls** — `persistUser(null)`, `clearPendingLogin()`, `setAuthToken(null)`
  (`AuthContext:141-145`). It does not iterate storage. `client.js:73-85` (`handleUnauthorized`)
  removes exactly the same two keys and then `window.location.assign(ROUTES.login)`.

### `pd:auth:v1` contents

Whatever `mapProfileToUser` returns (§6) — including `profile: profile ?? null`, the **raw
`/auth_profile` body**. Serialized with `JSON.stringify` at `AuthContext:124`. On read
(`:40-50`) a stored blob without an `email` is discarded.

---

## §3 Session lifecycle

Constants: `VALIDATE_TOKEN_TIMEOUT_MS = 7000`, `VALIDATE_INTERVAL_MS = 5 * 60 * 1000`
(`AuthContext:26-27`).

```
                                 ┌── ?token= in query (any route) ──┐
  page load                      │  strip via history.replaceState  │
      │                          │  completeSession(urlToken)       │
      ▼                          └──────────────┬───────────────────┘
  bootstrapSession :218 ─── token + storedUser ─┤
      │                                         ▼
      │                            callValidateToken()  ── auth failure ──▶ expireSession
      │                                         │                            (toast once,
      │                                         ├── ok ──▶ /auth_profile         logout)
      │                                         │           ├─ ok   ▶ persistUser
      │                                         │           └─ fail ▶ keep stored user
      └── neither ──▶ sessionValidating = false
```

- **Bootstrap** `:213-273`, guarded by a `cancelled` closure flag (not the repo's monotonic
  request-id ref) and skipped entirely when `!isAuthApiEnabled()` (`:214`).
- **Periodic revalidation** `:276-285` — `setInterval(validateSession, 5 min)`, only while `user`
  and a stored token both exist.
- **Per-navigation revalidation** — `ProtectedRoute.jsx:33-36`, effect keyed on `location.pathname`;
  skipped while `sessionValidating`. In-flight overlap is suppressed by `validateInFlightRef`
  (`AuthContext:118,190`).
- **`validateSession` outcomes** (`:182-211`): `{ok:true}`; `{ok:true, skipped:true}` when
  `!isAuthApiEnabled()` or `hasTokenInUrl()`; `{ok:false, reason:'missing_token'|'network'|
  'unauthorized'|'unexpected'}`.
- **What counts as an auth failure** — `isAuthFailureError` (`:90-96`): an `ApiError` with status
  401/403, **or with `status == null`** (the `unwrap` envelope throw from §1).
- **What does not** — `isNetworkOrTimeoutError` (`:81-88`): `AbortError`, any `TypeError`, or a
  message matching `/Failed to fetch|NetworkError|network/i`. These keep the session.
- **`expireSession`** `:147-156` toasts once per session (`expiryToastShownRef`, reset only in
  `completeSession` `:161`) then logs out.
- **`completeSession`** `:158-175`: `setAuthToken` → `fetchAuthProfile()`, and on **any** throw
  falls back to `decodeJwtPayload(accessToken)` (`:29-38`) — `atob` on segment 1, base64url
  normalised, **no signature or expiry verification**. Then `mapProfileToUser` + `persistUser`.
- **`isAuthenticated`** `:429-433`: with the API enabled, `user && readStoredToken()`; with it
  disabled, just `user`.

---

## §4 Demo mode (`VITE_APP_BASE_URL_AUTH` unset)

`isAuthApiEnabled()` → `isApiTargetEnabled(API_TARGETS.auth)` → `Boolean(getApiBaseUrl(auth))`
(`api/config.js:55-77`), which also honours the legacy `VITE_API_BASE_URL` fallback (`:43,48`).

| step | demo behaviour | line |
|---|---|---|
| `requestLogin` | 650 ms sleep; rejects only if `password.length < 4`; sets `pendingEmail`, no `temp_token` | `:292-300` |
| `verifyOtp` | 700 ms sleep; any `/^\d{6}$/` passes; mints `demo.${btoa(pendingEmail)}.${Date.now()}` into `pd:token:v1` | `:328-338` |
| `resendOtp` | 500 ms sleep, always `{ok:true}` | `:363-366` |
| `requestPasswordReset` | 700 ms sleep, always `{ok:true, email}` | `:395-398` |
| `resetPassword` | 700 ms sleep, always `{ok:true}` (still enforces 6-digit + ≥8 chars locally) | `:416-419` |
| bootstrap / revalidate | both early-return; no `/validate_token` ever fires | `:214,183` |
| `isAuthenticated` | true from `user` alone — the fake token is never checked | `:429-433` |

On-screen tells: **one**, the OTP page footer (`OtpPage.jsx:133-136`). `LoginPage` does not even
read `isAuthApiEnabled`. `/login/reset-password` is unreachable because
`ForgotPasswordPage.jsx:32` only navigates there when the API is enabled — and reaching the URL
directly bounces to `/login/forgot-password`, since it requires `location.state.email`
(`ResetPasswordPage.jsx:14,43-45`).

---

## §5 Outbound SSO

1. `config/navigation.js:42` — the Communication nav item carries `path: '#'` and
   `externalApp: 'connect'`.
2. `layout/Sidebar.jsx:82-88` — `NavItem`'s click handler `preventDefault()`s any item with
   `externalApp` and calls `onExternalApp(item.externalApp)` behind an `openingRef` re-entry guard.
3. `layout/Sidebar.jsx:121-133` — `handleExternalApp` resolves `userId` from
   `getLocationUserMeta(user)` (`utils/locationUtils.js:45-58`), toasts if absent, then calls
   `openUserDashboardApp({ userId, appName, token: getStoredAccessToken() })`. The token is read
   straight from `localStorage[TOKEN_KEY]` at `Sidebar.jsx:24-30`.
4. `api/auth.js:113-133` — fetches `/user_dashboards/<userId>`, matches a dashboard by
   case-insensitive trimmed `name`, throws if none, then appends `?token=` (or `&token=`) to
   `dashboard_url` and calls `window.open(url, '_blank', 'noopener,noreferrer')`.

The token therefore travels in a query string to a third-party origin. That is the existing
contract with the legacy AppMenu redirect; do not widen it, and do not log the resulting URL.

---

## §6 `mapProfileToUser` and the page surface

`auth.js:135-210`. It reads through `raw.user_profile ?? raw.profile ?? raw.user ?? raw` and emits:
`email`, `name` (first+last, else `name`/`full_name`, else the email local part, else
`'Clinician'`), `first_name`, `last_name`, `role`, `id`, `clinic_id`, `user_role`, `dashboard`,
`dashboard_id`, `profile`. Every field has three-to-six fallback paths — the auth backend's shape is
not stable, so read through this mapper, never off a raw response.

`role` is unwrapped from an object via `name ?? label ?? id` (`:173-176`). It is a **display**
field: §7.7 forbids gating on it.

### Page behaviour worth not re-deriving

| page | notable |
|---|---|
| `LoginPage.jsx` | `:30` renders `location.state.message` (set by the reset flow); `:51-53` bounces an authenticated user to `/scheduling`; `:83` navigates to `ROUTES.otp` with `state.email`. Written in a double-quote/semicolon style unlike the rest of `src/`. |
| `OtpPage.jsx` | `OTP_LENGTH = 6`; auto-submit guarded by `autoSubmittedRef` so a rejected code does not loop (`:58-64`); paste distributes across boxes (`:114-121`); `pendingQrCode` renders the enrolment QR (`:140-151`); no `email` → `Navigate` to `/login` (`:70-72`). |
| `ForgotPasswordPage.jsx` | Success copy is deliberately non-committal ("If an account exists for …", `:48`) — do not make it confirm whether the address is registered. |
| `ResetPasswordPage.jsx` | Confirm-match check at `:90`; submit disabled until code + both fields are filled (`:213`); 6-digit and ≥8-char rules live in `AuthContext:409-414`. On success navigates to `/login` with a message (`:102-105`). |
| `AuthShell.jsx` | Props `children`, `title`, `subtitle`, `footer`, `headerExtra`. Hero column is `lg:` only. |
| `AuthHeroPanel.jsx` | Autoplay 6500 ms, paused by `paused` state and by `useReducedMotion` (`:39-46`). `:92` hardcodes `to="/login"` — should be `ROUTES.login`. |
| `ProtectedRoute.jsx` | `SessionGate` shows a spinner while `sessionValidating` (`:9-19`); unauthenticated → `Navigate to={ROUTES.login} state={{ from: location.pathname }}`, and **nothing reads `from`**. |
