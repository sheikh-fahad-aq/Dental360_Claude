# Dental360 — workspace guide

Two applications, one product. This file is loaded on every turn, so it stays short:
the detail lives in skills, which load only when relevant.

| Repo | What | Stack |
|---|---|---|
| `360_Flask_Appointment/` | Appointments + charting API | Flask, SQLAlchemy, Alembic, Py 3.10 |
| `PMS_React/` | Clinical + front-desk SPA | Vite 8, React 19, Tailwind v4 |

They are **separate git repos** on separate branches (`fahad` / `feature/charting`).
Never commit across them in one commit. `.claude/` is a third repo, tracked separately.

---

## §1 Running things

```bash
cd 360_Flask_Appointment && python run.py
```

```bash
cd PMS_React && npm run dev
```

Backend on :5001 (single process — see §4.4), frontend on :5173.

Backend tests: `python -m pytest tests/` from `360_Flask_Appointment` — the **only**
automated test coverage in the workspace. The frontend has none; `npm run lint` is its
only check. "Verified" on the frontend means you loaded the page and watched the request.

## §2 Finding your way

**Do not explore blind.** Every feature has a skill carrying its file map, contract,
invariants and traps. Load the one that matches before reading source. The index lives in
the **`main-architecture`** skill — start there when you do not know which skill applies.

Backend skills are `be-*`, frontend skills are `fe-*`.

## §3 Recording changes

`main-architecture` is the durable record of how this system fits together. A hook appends
every file edit to its `CHANGELOG.md` automatically — you never do that by hand.

What you **do** owe it: when a change alters a feature's contract, invariants or file map,
update that feature's `SKILL.md` in the same turn. A skill that lies is worse than one
that is absent. `/skill-sync` reports which skills your current diff has invalidated.

## §4 Backend rules

1. **The app is flat.** Every blueprint is one large module directly under `app/`. Do not
   reorganise into packages as a side effect of a feature change.
2. **A new blueprint is two edits** — the module, and its import plus `register_blueprint`
   in `app/__init__.py`. Forgetting the second is the classic failure here: the route
   404s and nothing anywhere reports an error.
3. **Everything mounts at `url_prefix='/api'`.** New work targets the `/api/v2/*` surface.
   `app/appointment_routes.py` is legacy — read it, do not extend it.
4. **The scheduler is in-process.** `app/chart_session_scheduler.py` starts from
   `create_app()`, which is why `run.py` passes `use_reloader=False`. Anything that forks
   or runs multiple workers will run those jobs more than once.
5. **Migrations are append-only.** `flask db migrate`, then `flask db upgrade`. Never edit
   a file under `migrations/versions/` that has already been applied anywhere.
6. Auth and permission decorators live in `app/util/decorators.py`. Use them; do not
   hand-roll a check inside a route.

## §5 Dual-mode data

Both apps degrade to mock data instead of failing, and **this is driven by the presence of
config, not by a feature flag**. On the frontend, `isPatientsApiEnabled()` is literally
"is `VITE_APP_BASE_URL_AUTH` non-empty". Unset a base URL and that entire domain silently
serves mock data — no error, no banner, no visual difference.

What this obliges you to do:

- Every data hook returns `source: 'api' | 'mock' | 'api-partial'`. Honour it. Never render
  mock data in a way that reads as real clinical information.
- When something "works" but the data looks invented, check the env var before you debug
  the code. This is the most confusing failure mode in the workspace.
- A surface labelled `mock` in a skill or in `PMS_React/README.md` **is mock**, however
  finished it looks. Believe the label, not the screen.

## §6 Frontend rules

1. **`fetch` is called in exactly one file** — `src/api/client.js`. Import a domain module
   from `src/api/`. A bare `fetch` silently drops `x-api-key` and `Authorization`.
2. **Four backends, four clients:** `authApi`, `preAuthApi`, `appointmentApi`, `chartApi`.
   The appointment and chart hosts refuse browser CORS, so those two clients always emit
   same-origin paths (`/__appointment_api/api`, `/__chart_api/api`). That proxy is declared
   in **three** places — `server.proxy` and `preview.proxy` in `vite.config.js`, and
   `rewrites` in `vercel.json` — and all three must change together. (`PMS_React/README.md`
   says "twice", counting files rather than blocks.)
3. **Normalise at the edge.** Every API module exports `normalizeX(raw)`; components never
   see a raw API object. Each module has its own `unwrap()` — three envelope shapes exist.
4. **Never hardcode a hex.** Colours are CSS vars in `src/theme/theme.css`, bridged by the
   `@theme inline` block in `src/index.css`. Tailwind v4, no `tailwind.config.js`, no MUI.
5. **Never hardcode a route string.** Use `ROUTES` from `src/config/routes.js`. Navigation
   is config-driven: `config/navigation.js`, `settingsNavigation.js`, `patientSections.js`.
6. Overlays: `createPortal` + `AnimatePresence` + `OverlayBackdrop`, z-index from the
   static `OVERLAY_Z_INDEX` map — Tailwind cannot scan a dynamic `z-[n]`.
7. Feedback is `const { toast } = useToast()`. Never `alert`. `react-hot-toast` is **not**
   installed here. Errors go through `getErrorMessage(err, fallback)`.
8. ISO `YYYY-MM-DD` on the wire. **There is no date library in this repo** — do not add one
   silently.
9. React Compiler is on. Manual `useMemo`/`useCallback` is usually noise.
10. Editing anything under `src/context/` triggers a **full page reload**, by design
    (`fullReloadOnContextHmr()` in `vite.config.js`). In-memory state is lost.

## §7 Security and PHI

This system holds protected health information. These are not style preferences.

**§7.1 Never log PHI.** No patient id, name, DOB, appointment id or request payload in
`console.*`, in a server log line, or in an error message that reaches a browser. Patient
ids appear in URLs, so never log a URL from a patient-scoped call either. Gate every
diagnostic on `import.meta.env.DEV`.

**§7.2 Never commit a secret.** `.env` files stay untracked. Anything `VITE_`-prefixed is
**baked into the bundle and readable by any visitor** — it is not a place for a secret.
Pre-existing violations are recorded in `be-platform`; do not add to them.

**§7.3 Browser storage is not private.** Thirteen keys are written and only `pd:token:v1`
and `pd:auth:v1` are cleared on logout or 401. Several embed a patient or appointment id
**in the key name**, so on a shared front-desk workstation the key list is itself a record
of which patients were opened. Do not add another patient-scoped key name.

**§7.4 Never sink untrusted HTML.** No `dangerouslySetInnerHTML`, and no assignment to
`innerHTML`, for anything that came from the network. Server-supplied HTML rendered into
the DOM is a token-and-PHI theft vector, and **there is no sanitizer in this repo** —
DOMPurify is present only as a transitive dependency of jspdf and is never imported. Parse
the payload and render the fields you need. Existing violations are recorded as traps in
`fe-scheduling` and `fe-patient-chart`; fix them rather than copying them.

**§7.5 Chart ownership is per-tab and deliberately non-durable.** It lives in
`sessionStorage` (`chart_owned_session_<patientId>`), not `localStorage`, so a closed
browser never leaves a chart looking "owned" by someone who has gone home. Do not move it
to `localStorage` for convenience. See `fe-charting`.

**§7.6 `PMS_React/public/` is world-readable after deploy.** Vite copies it verbatim into
`dist/`. It currently holds three internal backend API documents. Never put anything there
that is not meant for an anonymous visitor.

**§7.7 Authorization is server-side.** There is **no client-side role gating** in the SPA.
Never treat a hidden button as a permission boundary, and never trust a role value the
client sent. Enforce it in the Flask route with a decorator from `app/util/decorators.py`.

## §8 Committing

**Never run `git commit` in `360_Flask_Appointment/` or `PMS_React/`.** Do not `git add`
in them either. Those two repos are committed by the user, by hand.

What you owe instead is the **commit message text**, ready to paste — one message per repo,
in a fenced block, plus the exact `git add` paths you would have staged. Then stop. `/ship`
produces this.

This holds even when the work is finished, verified and obviously correct, and even when
the user asked you to "ship" or "finish" it. Producing the text *is* finishing it. Only an
explicit, specific instruction to run the commit yourself overrides this.

`.claude/` is the exception: it is tooling, not product, and you may commit it directly.

Still true when you write the message:

- One repo per commit — the three histories are independent and a commit never spans them.
- Backend and frontend are **separate** messages even for one feature; name the counterpart
  in each body.
- Backend lands first when both changed; the two deploy independently.
- Never stage `.env`, `node_modules/`, `dist/`, `__pycache__/` or `env/`.
- Never `git push` anything, including `.claude/`.

## §9 Memory

**Project memory lives in `.claude/memory/`, not in the per-user memory directory under
`~/.claude/projects/`.** This overrides the default memory location. Anything worth
remembering about Dental360 is written here, so it is versioned with the tooling, reviewable
in a diff, and travels with the repo to every machine and teammate.

- `.claude/memory/MEMORY.md` is the index — one line per memory, loaded every turn.
- Each memory is its own file next to it, read only when the index says it is relevant.
- Same format as before: `name` / `description` / `metadata.type` frontmatter, then the
  fact. `[[wiki-links]]` between memories still resolve, by file name.
- Before adding one, check whether an existing file already covers it and update that
  instead. Do not record what the repo already states — a skill, `CLAUDE.md`, or git
  history is the better home for anything derivable from the code.

@.claude/memory/MEMORY.md
