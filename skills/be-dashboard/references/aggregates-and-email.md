# be-dashboard — response shapes, the date ladder, and the Graph email pipeline

All line numbers are `360_Flask_Appointment/app/dashboard_routes.py` unless prefixed.
Verified against the working tree; the file is 799 lines, CRLF.

---

## 1. The shared date-preset ladder

Five stats routes each contain a **private copy** of the same ~28-line block. Copies begin at
`:137`, `:202`, `:320`, `:410`, `:501`. Semantics are identical in all five.

Inputs: `start_date`, `end_date` (`YYYY-MM-DD`), `filter`.
Base clock: `now = datetime.utcnow()`.

| Condition | `start_date` | `end_date` (exclusive) |
|---|---|---|
| `start_date` **and** `end_date` both present | `strptime(start)` | `strptime(end) + 1 day` |
| `filter=today` | midnight UTC today | +1 day |
| `filter=yesterday` | midnight UTC yesterday | +1 day |
| `filter=last_7_days` | `now - 6 days` | `now + 1 day` |
| `filter=this_week` | `now - now.weekday()` days (Monday) | +7 days |
| `filter=this_month` | 1st of this month | `now + 1 day` |
| `filter=last_month` | 1st of last month | 1st of this month |
| anything else, or only one of the two dates | `None` → **no date filter** | — |

Consequences to know before touching it:

- The comparison column is always `Appointment.created_at`, never `Appointment.date`
  (`:164, :246, :362, :453, :540`). Presets describe **when the appointment row was
  created**, i.e. booking volume, not clinic-day volume.
- `last_7_days`, `this_week` and `this_month` keep the *time-of-day* component of `now`,
  so `start_date` is not midnight for those three. Only `today`, `yesterday`,
  `this_month` and `last_month` start at midnight.
- `this_week` is Monday-anchored and its `end_date` runs 7 days from that Monday — it
  therefore includes future-created rows for the rest of the week.
- Passing `start_date` alone yields no filter, yet the response still echoes
  `"filter": "custom"`. Passing `filter=` with an unknown value yields no filter and
  echoes the unknown value back.
- Timezone: the ladder is pure UTC. There is no clinic-timezone handling anywhere in the
  module. A US-clinic "today" straddles two UTC days.

---

## 2. Response shapes

### `GET /api/appointments/stats` — `:126`

Single-pass aggregate, no subquery (`:170-174`).

```
{ "status": "success",
  "filter": "<echoed>", "location_id": <int|null>,
  "start_date": "<echoed|null>", "end_date": "<echoed|null>",
  "total": int, "total_ai": int, "total_web": int }
```

`total_ai` = `count(lower(status) == 'ai')`; `total_web` = `count(lower(type) == 'web')`.
Different columns — see SKILL.md Traps.

### `GET /api/appointments/stats/by_location` — `:191`

`GROUP BY Appointment.location_id` (`:232-240`, group key `:239`). **No `location_id` query param is read.**
Empty result short-circuits to `{"status":"success","locations":[]}` (`:254-255`).

```
{ "status": "success", "filter", "start_date", "end_date",
  "locations": [ { "location_id": int|null,
                   "location_name": "<resolved|Unknown>",
                   "total_appointments": int, "total_ai": int, "total_web": int } ] }
```

Rows with `location_id = NULL` survive the grouping but are excluded from the name lookup
(`:258` filters falsy ids), so they render as `"Unknown"`.

### `GET /api/appointments/stats/by_status` — `:308`

`GROUP BY func.trim(func.lower(Appointment.status))` (`:352, :355`), then re-uppercased
for output (`:378`). Honours `location_id` (`:367`).

```
{ "status": "success", "filter", "start_date", "end_date", "location_id",
  "statuses": [ { "status": "SCHEDULED", "total": int } ] }
```

Because the grouping normalises case and whitespace, `" Scheduled"` and `"scheduled"`
collapse into one bucket. That is deliberate; do not "fix" it by grouping on the raw column.

### `GET /api/appointments/web/stats/by_status` — `:398`

Identical to the above plus `.filter(func.lower(Appointment.type) == "web")` (`:445`).
Adds `"appointment_type": "web"` to the envelope (`:478`).

### `GET /api/appointments/web/stats/by_location` — `:490`

`GROUP BY location_id` filtered to `type='web'` (`:532`, group key `:533`). Returns `total_web` only — no
`total_appointments`, no `total_ai`.

### `POST /api/dashboard/check` — `:79`

Body `{ "profile": { id, first_name, last_name, email, role: {name}, dashboards: [...] } }`.
Looks for `dashboards[].name == 'auth'` (`:92`). On match, writes nine Flask session keys
(`:96-104`) and returns `200 {"message": "Dashboard matched successfully"}`. No match →
`400`. Missing `profile` → `400`. No authentication of any kind.

### `GET /api/emails/read` — `:681`

```
{ "status": "success", "email_address", "folder", "total_emails", "top", "skip",
  "emails": [ { id, subject, from, from_name, to[], received_date_time, is_read,
                body_preview, has_attachments, body, body_content_type, main_content,
                attachments?[ {id,name,content_type,size} ] } ] }
```

Non-200 from Graph is forwarded verbatim, including `details: response.text` (`:791-795`),
with Graph's own status code as the HTTP status.

---

## 3. Location-name resolution (both `by_location` routes)

`:261-283` and `:554-575` define a nested `async def fetch_location_names()` and drive it
with `asyncio.run()` from the synchronous Flask handler.

- Target: `GET https://api.dental360grp.com/api/clinic_locations/<id>` — `AUTH_SYSTEM_URL`
  is a **module constant** at `:20`, not configurable by env.
- The caller's inbound `x-api-key` and `Authorization` headers are forwarded verbatim
  (`:263-264`, `:556-557`). Since the route itself requires neither, both are usually empty
  and every lookup fails.
- Any exception, and any non-200, resolves to `"Unknown"` (`:275-277`). Failures are silent.
- One request per distinct location id, no cache, no concurrency cap, no per-request
  timeout on the `aiohttp` session.

If you need this to be fast or correct, the right fix is a local lookup table or a cached
batch call, not more concurrency.

---

## 4. Microsoft Graph pipeline (`/emails/read`)

Configuration is read **at import time** from the process environment (`:22-25`), never from
`current_app.config`:

| Module constant | Env var | Fallback |
|---|---|---|
| `MICROSOFT_CLIENT_ID` | `MICROSOFT_CLIENT_ID` | `None` |
| `MICROSOFT_CLIENT_SECRET` | `MICROSOFT_CLIENT_SECRET` | `None` |
| `MICROSOFT_TENANT_ID` | `MICROSOFT_TENANT_ID` | `None` |
| `MICROSOFT_EMAIL` | `MICROSOFT_EMAIL` | `"it.support@dental360grp.com"` |

`360_Flask_Appointment/config.py:26-30` declares `MICROSOFT_CLIENT_ID`,
`MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT_ID` and `MICROSOFT_SENDER_EMAIL` on
`ProductionConfig`. Those attributes are **never read by this module**. Note also that the
repo `.env` defines `MICROSOFT_SENDER_EMAIL`, not `MICROSOFT_EMAIL` — so the mailbox read is
the hardcoded fallback above unless someone adds `MICROSOFT_EMAIL` to `.env` and restarts.

Flow:

1. `get_graph_token()` (`:601`) — client-credentials POST to
   `https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token`, scope
   `https://graph.microsoft.com/.default`, 30s timeout. Returns `None` on any failure, and
   the route turns that into `500 {"error": "Failed to get Microsoft Graph access token"}`.
   **No token cache** — a fresh token is minted on every request.
2. `GET {GRAPH_BASE_URL}/users/{email}/mailFolders/{folder}/messages` (`:702`) with
   `$top` (capped at 100), `$skip`, `$orderby=receivedDateTime desc`, and a fixed `$select`
   that includes `body` and `attachments`. Caller-supplied `filter` becomes `$filter` and
   `search` becomes `$search` **unescaped** (`:713-718`) — untrusted OData passthrough.
3. For each message with `hasAttachments`, a second Graph call to
   `/users/{email}/messages/{id}/attachments` (`:763`). N+1; errors swallowed to `[]`.
4. `extract_main_content_from_html()` (`:628`) produces `main_content`: a
   `re.sub(r"<[^>]+>", "", ...)` tag strip plus `html.unescape`, then truncation at the
   first reply/forward separator (`-----Original Message`, `________________`, `from: `,
   `sent: `, `subject: `, `get outlook for`). It is a **display heuristic, not a
   sanitizer** — the untouched original is still returned in `body`.

Security notes carried into the skill body: the route is unauthenticated, it returns full
message bodies of a shared support mailbox, and CLAUDE.md §7.4 forbids sinking that HTML in
`PMS_React` (no sanitizer exists there).

---

## 5. Indexing / performance detail

`Appointment` (`360_Flask_Appointment/app/models.py:26-95`) declares exactly two indexes:
`tracking_status_id` (`:87`) and `tracking_status` (`:88-90`). No `__tablename__` is set, so
the table is `appointment`.

`grep -rn create_index migrations/versions/` returns no appointment index. Therefore each of
the five stats routes is a full sequential scan plus a hash aggregate:

| Route | Scan predicate | Group key |
|---|---|---|
| `/appointments/stats` | `created_at` range, `location_id` | none (single row) |
| `/stats/by_location` | `created_at` range | `location_id` |
| `/stats/by_status` | `created_at` range, `location_id` | `trim(lower(status))` |
| `/web/stats/by_status` | `lower(type)='web'` + above | `trim(lower(status))` |
| `/web/stats/by_location` | `lower(type)='web'` + range | `location_id` |

`lower(type)` and `trim(lower(status))` are function calls on the column, so even if plain
btree indexes were added on `status` and `type` the planner could not use them. Any real fix
needs expression indexes:

```sql
CREATE INDEX ix_appointment_created_at   ON appointment (created_at);
CREATE INDEX ix_appointment_location_id  ON appointment (location_id);
CREATE INDEX ix_appointment_lower_status ON appointment (lower(btrim(status)));
CREATE INDEX ix_appointment_lower_type   ON appointment (lower(type));
```

Unverified: actual row counts and query timings in the deployed Postgres
(the `appointment_db` host in `config.py`) were not measured. The absence of indexes is verified
from the model and the migration tree; the resulting plan is inferred, not observed.
