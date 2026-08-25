# The patient review link — two factors, parity, and the public surface

Long-form backing for invariants 5–7 in `be-treatment-plans/SKILL.md`. Everything here is
in `360_Flask_Appointment/app/treatment_plans_v2_routes.py` unless stated otherwise.

## Why two factors

The share token says **which plan**. It travels by email and leaks the way email leaks, so
on its own it is not permission to read a clinical document. `POST
/v2/treatment-plans/shared/<token>/verify` (`:2367`) is the second factor: the patient's
date of birth, compared against a salted digest snapshotted onto the plan at share/send
time.

Success mints a row in `treatment_plan_share_sessions` (`app/models.py:1401`, table name at
`:1415`) and returns a one-shot credential. Both remaining public reads require it in the
`X-Plan-Access` header, checked by `_verified_share_session` (`:353`) **before** any
`plan.status` inspection — so the 409s that distinguish a draft from a closed plan sit
behind both factors, not one.

## The five rules, each a real hole first

1. **Never a signed/stateless grant.** `app/__init__.py:28` sets
   `app.config['SECRET_KEY'] = 'your_secret_key'` unconditionally, overriding `config.py`.
   It is committed, so anything signed with it is forgeable by anyone who has read the
   repo. Hence a random secret (`secrets.token_urlsafe(32)`) compared against a stored
   sha256 digest — which needs no key at all. `_mint_share_session` `:330`,
   `_digest` `:213`.
2. **`share_failed_attempts` is MONOTONIC.** Cleared only by a successful verify
   (`:2456`), never by a cooldown expiring. A counter that a lockout resets is one an
   attacker sleeps through. Column: `app/models.py:1381`.
3. **Attempt limiting NEVER revokes the link.** An unauthenticated caller who can
   permanently destroy a patient's access to their own plan has a denial-of-service
   primitive, not a security control. `_dob_cooldown_minutes` (`:317`) escalates
   `5 * 2^(steps-1)` minutes past `SHARE_DOB_ATTEMPTS_PER_COOLDOWN = 5` (`:130`) and caps
   at `SHARE_DOB_MAX_COOLDOWN_MINUTES = 60` (`:131`). It never kills.
4. **Malformed input costs nothing.** The ordering inside `verify_shared_treatment_plan`
   is deliberate and not the obvious one: parse the submitted date, resolve the token,
   refuse while a cooldown runs, resolve the expected date — and only *then* increment and
   compare. A date failing the shape check, an unknown token, and a failure to READ the
   expected DOB all refuse without touching the counter. Otherwise anyone holding the
   token locks the patient out with junk.
5. **Fail CLOSED.** `_live_patient_dob` (`:283`) returns `None` for a non-200, a
   transport error surfaced as 502, `PHI::` ciphertext, or an unparseable shape, and every
   caller reads `None` as refuse. The `if status == 200 ... else` template elsewhere in
   this file is right for a display name and would be a hole here.

## Counter keyed on the plan, not the token

Re-sending rotates the token. A token-keyed counter would let the practice hand an
attacker a fresh guessing budget on request. Rotation also calls `_revoke_share_sessions`
(`:346`), and `_verified_share_session` compares `session.token_fingerprint` against the
current token's digest — so a credential minted against a rotated token is dead.

## Two date parsers, deliberately different

- `_parse_submitted_dob` (`:231`) — what the PATIENT typed. **Strict**: ISO
  `YYYY-MM-DD` only. Deliberately NOT `parse_dob` from `appointments_helpers`, which also
  accepts `%d-%m-%Y`, so `01-02-1987` and `01/02/1987` resolve to different dates there. A
  day/month ambiguity is not something to bake into a security comparison.
- `_coerce_stored_dob` (`:248`) — what the AUTH SERVICE holds. **Tolerant**: `date`,
  `datetime`, ISO prefix, and month-first `M/D/YYYY`. This end is not typed by an attacker
  and the upstream shape is not ours to dictate. `PHI::` ciphertext returns `None`.

## Session lifetimes

`SHARE_SESSION_TTL_MINUTES = 30` (`:134`) sliding, capped by
`SHARE_SESSION_MAX_HOURS = 4` (`:136`) absolute. `_verified_share_session` slides
`expires_at` on every successful read, clamped to `absolute_expires_at`.

## `/send` and `/share` must issue the SAME link

`share_treatment_plan` `:2140`, `send_treatment_plan` `:2203`. Both:

- stop the expiry — `share_token_expires_at = None`;
- call `_snapshot_share_dob` (`:299`) and **409** when it returns False, with the same
  "no usable date of birth on file" message;
- call `_revoke_share_sessions` on rotation.

`/send` was left behind once already: emailing a plan produced a token that died in
`SHARE_TOKEN_TTL_DAYS = 30` (`:109`, now unused on this path) while Copy link produced a
permanent one — the same plan with two lifetimes depending on which button the coordinator
pressed. See the comment at `:2263`. Any future change to one belongs in the other.

`expiresInDays` is still accepted on `/share` and capped at 3650 days (`:2169`), so a
caller that wants a bounded link can still have one. It is simply not the default.

`_snapshot_share_dob` runs where a Bearer token exists and a slow Auth call is acceptable,
so the unauthenticated verify path never makes an outbound request — which would otherwise
hand an attacker a way to hammer the Auth service through us.

## Email variables are substituted SERVER-SIDE, and escaped

`_fill_email_variables` (`:2329`) fills `[Form Link]`, `[Practice Name]` and
`[Patient First Name]` in **both** the subject and the body.

`[Form Link]` *cannot* be filled in the browser: `/send` rotates the share token as part of
sending, so the review URL does not exist until the request is being handled. The composer
therefore ships the template with the placeholder still in it.

Everything except the URL goes through `html.escape` (imported as `html_escaping`). These
land inside an HTML email body, and a practice name carrying `&` or a patient name carrying
`<` would otherwise break the markup or inject into it. The URL is deliberately **not**
escaped — it is built here from a urlsafe token and a configured base, and escaping it
would corrupt the `href`.

Channel is **email only**. SMS delivery lives in the external Auth service, which has no
treatment-plan endpoint, so an SMS request is refused with a message saying so rather than
accepted and silently dropped (`:2231`). `send_email` is imported lazily inside the route
because `app.appointment_routes` imports from `app` and a module-level import would close
the cycle at start-up.

## The link does not expire, and a finished plan says so

`_plan_closed_state` (`:386`) returns `{reason, at}` for `signed` / `completed` /
`declined`. A patient returning to a plan they already answered gets an "already complete"
screen rather than a dead link. It is only ever returned AFTER both factors are proved.

`submit_shared_decisions` (`:2538`) refuses a closed plan outright, keyed on the same
`_plan_closed_state` so the refusal and the screen agree by construction — a SIGNED plan
used to fall through to `_apply_signature` and come back as a bare 400 that told the
patient nothing.

**Signing NO LONGER revokes the share token.** It used to, and a patient who signed and
refreshed — or whose phone dropped the response — met "this link is no longer available"
with no way to tell whether their signature had landed. Write-once is enforced by the
plan's terminal state, which is the thing that cannot be undone.

## The public surface is allow-listed, not deny-listed

`_serialize_plan_for_patient` (`:2055`) names every field that may leave. Never build the
public payload by serializing everything and popping keys — a deny-list fails open on the
next field added. Nothing internal crosses: no clinic, location, patient, provider or
appointment id, no chart-procedure provenance, no signature, no `teeth`, no `origin`.

`PUBLIC_ENDPOINTS` (`:184`) is the set of three endpoint names that get
`validate_api_key` instead of the full `require_api_and_bearer` gate, via the
`before_request` hook at `:202`. A route absent from that set gets the full gate — which is
the safe default, but means a new public route 401s until it is added.

`_resolve_share_token` (`:2117`) returns the same vague 404 for unknown / too-short /
revoked / **archived** / expired / void. Do not make those distinguishable. `archived_at`
is tested there in its own right, not left to the revocation that `archive_treatment_plan`
also performs — those are separable.

The public endpoints require `x-api-key` but **no Bearer token**. That key is
`VITE_`-prefixed and baked into the SPA bundle (CLAUDE.md §7.2), so the DOB is the only
real secret in the chain.

## Frontend counterpart

`PMS_React/src/api/treatmentPlans.js` exports `verifySharedTreatmentPlan(token, {dateOfBirth})`
(`:801`), `fetchSharedTreatmentPlan(token, {accessToken})` (`:819`) and
`submitSharedTreatmentPlanDecisions` (`:850`). The page is
`PMS_React/src/pages/SharedTreatmentPlanPage.jsx`, rendered standalone at `/tp/:token` —
`App.jsx` excludes `/tp/` from `AppLayout` as it already did `/f/`. See `fe-platform`.
