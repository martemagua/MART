# MART — Renewal lifecycle & project management (planning draft)

> Status: **planning only, nothing built.** This is a picture of what is
> possible plus open questions. Everything here can still change.
> **MART is a new, standalone app.** MAPT NEO is *reference only*: its
> knowledge of the BM+ trackers, its patterns and the lessons it learned the
> hard way inform MART, but nothing is shared at runtime (no shared database,
> no shared code dependency, no data migrated). Where this plan says "as in
> MAPT", read "the same idea, rebuilt in MART".

---

## 1. What MART is (and how it differs from MAPT NEO)

| | MAPT NEO | MART |
|---|---|---|
| Main question | "What does the book look like?" | "What do I have to do, by when, and is it on track?" |
| Main unit | Policy / coverage / period | The **renewal case**: one policy's renewal cycle, treated as a small project |
| Time horizon | Snapshot of the current trackers | The **whole lifecycle**, from the first signal before the renewal to the post-renewal review, **kept after BM+ forgets it** |
| Work features | Bolted on over time (Follow-ups, chasers, to-dos, meetings, audits are separate things) | Built around one model: case → phase → work items → reminders |

MAPT NEO already has many project-management pieces (the Follow-ups queue,
the chaser ladder, the contact log, the to-do Kanban). They were added to an
analytics app, though, and each one keys itself to the renewal in its own way.
MART puts the **renewal case** at the centre and hangs everything else off it.

---

## 1b. What Martin wants to be able to do (round 2 input)

MART = **Martin's Awesome Renewal Tool**.

1. **Orient myself on opening it.** A summary of my clients with their notes
   and to-dos. My **local AI agent connects over MCP**, reads the database and
   helps organise my day.
2. **Client → renewals, bundled.** Selecting a client shows all of their
   renewals **bundled by country + renewal date**. Selecting a bundle shows
   its individual renewals.
3. **Kanban with colleagues: show the *real* state.** BM+ often lags reality.
   For example, the strategy is already agreed, but the broker hasn't
   submitted it in BM+ yet. I need to be able to record the actual state and
   **point out the discrepancy**.
4. **Overview freshness + broker deadlines.** See which policies have **new**
   renewal overview comments and which are **stale**. When a broker gives an
   expected date for an update, I can record it as a **deadline**.
5. **Notes and to-dos on renewals.**

### What this settles

- Q25 (MCP/AI agent): **yes**, from day one, and as part of the daily routine.
- Q8 (unit): the natural grouping is the **bundle = client × country ×
  renewal date**. It can be derived automatically from the trackers; no manual
  grouping is needed.
- Q10 (who wins): **neither overwrites the other.** BM+ state and actual state
  are kept side by side, and the *difference* is a first-class thing to see
  and act on.

---

## 1c. The screens

### Home — "where am I?"
One card per client, ranked by what needs attention:

- renewals in flight and the next renewal date
- 🟢 new overview comments since I last looked · 🟠 stale overviews
- broker deadlines passed or due this week
- open discrepancies (actual state ≠ BM+)
- open to-dos (count + the next few) and the latest note

Above the cards is a **"Today"** strip: deadlines due, to-dos due, overdue
broker promises. The AI agent's day plan (written over MCP) can appear here
as a note or a set of to-dos it created.

### Client page — renewals by bundle
```
Mercedes-Benz Group AG
├─ Poland · 01.01.2027            3 renewals   strategy: Remarketing (actual) ≠ BM+ blank ⚠
│    ├─ Life           Allianz    overview 3d ago 🟢
│    ├─ Medical        PZU        overview 41d ago 🟠   broker promise: 15.11 ⏰
│    └─ Disability     Allianz    …
├─ Spain · 01.01.2027             2 renewals
└─ Brazil · 01.03.2027            1 renewal
```

- A bundle row rolls up its renewals: the worst freshness, the soonest
  deadline, the stage mix, and discrepancies.
- Clicking a bundle opens its renewals. Clicking a renewal opens the
  **renewal drawer** (BM+ facts, the actual-state panel, the overview
  timeline, notes, to-dos and deadlines).
- Notes, to-dos and deadlines can be attached at **bundle** level (they apply
  to all renewals in it, like one email covering several policies) or at
  **renewal** level.

### Kanban — the shared picture when working with colleagues
- Columns = stages. **The card sits in the column of its *actual* state.**
  If BM+ shows something different, the card carries a badge such as
  "BM+: Strategy — not started".
- Dragging a card records an actual-state change, with an optional one-line
  reason ("agreed with HR on call 28.10").
- The cards could be bundles or individual renewals (see Q-B2).
- Filters: client, country, owner, "only discrepancies", "only stale".

### Overview freshness
- **New** = an overview entry whose own date (its `DD MMM YYYY:` header)
  is within the last N days (Martin, 04.11.2026, QUESTIONS E2: no "seen"
  marks; the date written on the entry is what counts).
- **Stale** = no overview entry for a while, in two steps: amber after 7
  days, red after 14 (QUESTIONS E1), both under Settings → Time limits,
  next to the age of the overview *data* itself (from 0.4.0, 7 days). All
  entries count, client-ready or not (E3).
- **An expected date defers the clock** (Martin, 04.11.2026): when a broker
  says "terms expected late November", nagging weekly until then makes no
  sense. A renewal with a broker deadline in the future is not stale; the
  clock starts again on that date (M2, with broker deadlines).
- MAPT already parses dated `DD MMM YYYY:` entries out of the overview and
  stores `latest_overview_date`. This can be reused directly.

### Broker deadlines ("they said they'd update by …")
- A **deadline** = (**bundle**, who promised, what, expected date, source
  note): when Martin expects updates on those renewals. Separate from
  to-dos, which are his own tasks (Martin, 04.11.2026).
- **Confirmed by Martin**, never closed automatically (QUESTIONS E4); MART
  points out a new overview entry dated on or after the promise.
- **Prefilled** from the Renewal Strategy sheet's "Expected date to receive
  the final renewal terms" when BM+ has it (K4).
- **Overdue** → it appears on Home/Today, and a chase can be started
  (chaser ladder, with a ready-to-send draft as in MAPT).

---

## 1d. "Actual state" vs BM+: the discrepancy model

This is the most distinctive feature, so it gets its own design.

- **Per renewal, per field**, MART can hold *my* value next to BM+'s value.
  Candidate fields: stage (Strategy / Proposals / Update Policy / done),
  upcoming strategy, workflow status, plan design changes yes/no, new insurer,
  expected effective date.
- Each assertion stores: value, who and when, an optional reason/evidence
  note, and **the BM+ value at the time it was made**.
- Every view computes three states:
  - **in sync**: BM+ = actual (or no actual recorded, so BM+ is shown)
  - **BM+ behind**: actual is ahead → "broker to submit in BM+". This is
    itself a follow-up item, possibly a deadline or a chase
  - **conflict**: BM+ moved to something *different* from what I asserted →
    needs my look
- **Self-healing**: when an ingest brings BM+ in line with my value, the
  discrepancy closes and is logged ("BM+ caught up on 04.11"). Nothing has to
  be cleaned up by hand.
- This generalises MAPT's `renewal_strategies` pattern (an answer stored
  *beside* the tracker, BM+ wins once it has one). In MART the actual state
  wins *on the board*, and BM+ wins as the record. Both are shown.

---

## 2. What we learned from the MAPT trackers

### 2.1 The four BM+ exports

| Tracker | Grain | What it gives MART | Watch-outs |
|---|---|---|---|
| **Task Tracker** (`Task Summary`) | one BM+ task | the three BM+ stages per renewal (**Renewal Strategy → Proposals → Update Policy**), status, assignee, escalation manager, due date, times escalated | full SNAPSHOT per client: tasks that vanish are deleted. Two export flavours (cross-client / client-specific). BM+ keeps a finished cycle's tasks unless they are marked Completed, so they have to be scoped to the cycle by `Policy Renewal/Review Date` |
| **Renewal Tracker** (`Renewal Overview`) | one in-progress renewal | workflow status, upcoming strategy, year of last remarketing, plan-design changes + comments, target/actual loss ratio, claims comments, multinational network (MNW) expiring vs upcoming, **dated overview text** (all + client-ready) | **completed renewals are dropped on every ingest.** MAPT does not read the `Renewal Strategy`, `Proposals` and `Savings` sheets yet, and those are exactly what a post-renewal review needs |
| **Benefit Tracker** (BD / PCD / CD sheets) | policy, coverage, period, plan design | the **result** of a renewal: new period, dates, premium, headcount, insurer, design, Rate Guarantee End, Total Savings at Last Renewal, Prior Renewal Strategy, benchmarking | this is the "did BM+ get updated?" source. Only the current period is in each file, so history builds up across uploads |
| **Insurer Capability DB** | network × country × line | network partner checks | global snapshot |

### 2.2 The glue (reuse as-is)

- **Expiring policy unique id**: the one id that stays the same across
  cycles (`Benefit Unique ID` = `Expiring Policy Unique ID` = `Policy Unique ID`).
- **Cycle**: a renewal is (expiring id, renewal/review date), or BM+'s
  `Renewal Unique ID`. MAPT had to derive the cycle after the fact
  (`CURRENT_CYCLE_SQL`). In MART the cycle is a first-class object.
- **(scope, ref)**: the convention for notes, links and to-dos. It works and
  is worth copying.
- NULL means "to be confirmed", not zero. Trust BM+ task status rather than
  recomputing it. Count deadlines in **working days**.

### 2.3 What has to be corrected or rethought for MART

1. **History must outlive BM+.** The Renewal Tracker drops completed
   renewals and the Task Tracker deletes vanished tasks. A post-renewal phase
   is impossible if the case disappears at the moment it completes. MART
   owns the case, and BM+ data only *updates* it.
2. **Record changes, not only state.** Each ingest should record what
   *changed*: "Proposals went In Progress → Completed, first seen 12.03".
   Without that there is no timeline, no cycle time and no "what moved since
   my last meeting". Note: BM+ does not export *when* something happened.
   MART only knows when it **first saw** it, so accuracy depends on how often
   you upload.
3. **BM+'s three stages are too coarse to manage by.** They are a reporting
   skeleton. The real work (claims data request, broker brief, quotes,
   client sign-off, BM+ update, audit, savings write-up) sits inside them.
   MART needs **its own phases** and maps BM+'s stages onto them.
4. **Plan backwards from the renewal date.** The deadline never moves, so
   every step's due date should be computed from it (T-120, T-90, …, in
   working days). The case's health is then *planned vs actual*, and you
   are warned before the deadline is at risk, not after.
5. **Bundles are real.** One mail covers several policies, and one client and
   country often renews together. MAPT's contact log had to add `n_refs` for
   this. MART should allow cases to be grouped and moved together.
6. **One reminder engine**, not chasers + to-do reminders + attention badges
   as three separate mechanisms.

---

## 3. What matters in a project-management tool, applied to renewals

| PM concept | Renewal translation |
|---|---|
| Project | **Renewal case** (one policy × one cycle), optionally in a **bundle** (client/country) |
| Project template / playbook | **Renewal playbook**: phases + checklist items + relative deadlines. Variants by strategy (incumbent / remarketing / rate guarantee / non-expiring), possibly by product group or country |
| Milestones | Phase gates: strategy agreed, terms received, client decision, BM+ updated, review passed |
| Tasks | BM+ tasks (mirrored, read-only) **+** playbook items **+** your ad-hoc to-dos, all on the same case |
| Status | Phase (where it is) **+** health/RAG (on track?) **+** **ball in court** (us / broker / insurer / client / COE). Much of a renewal is waiting on someone, so "waiting on whom, since when" is the key field |
| Deadlines | Absolute (renewal date) and relative (T-minus working days) |
| Reminders | Due-date alarms, chaser ladder rungs, snooze, "remind me if no answer in N WD" |
| Dependencies / blockers | "Can't request quotes until claims data is in". Light, at checklist level only |
| Board (Kanban) | Columns = phases, cards = cases, swimlanes = client / renewal month / owner |
| Calendar / timeline | Renewal dates + back-scheduled milestones, exported to Outlook (.ics, as MAPT already does) |
| My Day / inbox | Today's due + overdue + replies to read + chasers due, in one list |
| Activity log | Append-only timeline per case: BM+ changes, your actions, contacts, notes |
| Definition of done | Post-renewal review checklist (data audit + knowledge captured) |
| Reporting | Cases per phase, overdue, cycle time per phase, savings achieved, audit pass rate |

---

## 4. A proposed renewal lifecycle (to be corrected by you)

```mermaid
flowchart LR
    U[Upcoming<br/>T-180..T-120] --> K[Kick-off & data<br/>claims, census, LR]
    K --> S[Strategy<br/>BM+ 'Renewal Strategy']
    S --> M[Marketing / Proposals<br/>BM+ 'Proposals'<br/>chasers live here]
    M --> D[Decision & sign-off]
    D --> I[Implementation<br/>BM+ 'Update Policy']
    I --> R[Post-renewal review<br/>data audit + knowledge]
    R --> C[Closed]
```

Each phase has:

- **entry/exit criteria**, either *automatic* from tracker data (for example,
  "Strategy" can exit when BM+ has an Upcoming Renewal Strategy or the
  Renewal Strategy task is Completed) or *manual* checklist ticks;
- **playbook items**, each with a relative due date;
- an **expected duration**, which gives the health (RAG) colour.

How BM+ and MART interact: BM+ statuses move the case *forward
automatically* where a rule says so. You can always move it manually. What
happens when the two disagree is open question Q10.

### 4.1 Post-renewal review: the part MAPT doesn't do

MAPT's audit checks the *quality of one Benefit Tracker file*. A post-renewal
review is different. It checks a **before → after delta for one case**:
did the new cycle land in BM+ correctly? Candidate checks, all derivable from
data MAPT already ingests:

| Check | Source |
|---|---|
| New period exists; start = old end + 1 day; end/next renewal date set | Benefit Tracker BD/PCD |
| Premium and headcount **updated**, not just copied from last year (identical value = suspicious) | PCD period vs previous period |
| Insurer matches the decision (remarketing win means a new carrier) | BD insurer vs strategy/outcome |
| Prior Renewal Strategy = what was actually decided | BD `Prior Renewal Strategy` vs case |
| Year of Last Remarketing updated if remarketed | BD / Renewal Tracker |
| Rate Guarantee End Date set if renewed with a rate guarantee | BD |
| **Total Savings at Last Renewal** filled (23% fill rate in the sample!) | BD |
| Plan design changes = Yes → coverage design actually differs between periods, and the changes are described | Renewal Tracker + CD sheets diff |
| Loss ratio / claims period refreshed | PCD claims block |
| MNW upcoming = implemented after renewal | Renewal Tracker → PCD |
| Client-ready overview has a final entry | Renewal Tracker overview |
| BM+ tasks all Completed | Task Tracker |

Then the **knowledge capture** items: record the savings (amount, basis,
type), record the plan design changes (what, from → to, effective date),
lessons learned. Whether these feed a MART knowledge register, a report or something else
is open question Q16.

Findings can be **waived** ("accepted, not applicable"), so they don't nag
forever. The MAPT audit plan already identified waivers as an open point.

---

## 5. Kanban board — first sketch

- **Columns** = lifecycle phases (§4). The Closed column prunes itself after N days.
- **Cards** = renewal cases (or a bundle card that expands). The card shows
  client · country · product group · renewal date countdown · strategy pill
  · ball-in-court · next action + its due date · RAG dot · BM+ stage strip
  (3 mini dots) · chaser badge.
- **Swimlanes** (switchable): none / client / renewal month / owner / strategy.
- **Filters**: same live-filter pattern as MAPT (client, country, product
  group, strategy, owner, health, "only waiting on others").
- **Drag** = move phase. Phase gates can warn ("2 exit items open") but should
  not block.
- **Drawer** on click: a timeline, the checklist per phase, chasers and
  contacts, notes. Same layout as MAPT's renewal drawer, so it is familiar.
- Other views on the same data: **list**, **calendar/timeline**
  (back-scheduled milestones), **My Day**.

---

## 6. Sketch of the data model

```
clients, policies              mirror of BM+ (reused ingestion, read-only)
renewal_cases                  id, expiring_policy_id, cycle_key (renewal_unique_id | review date),
                               client, country, product_group, renewal_date, strategy,
                               phase, health, ball_in_court, owner, bundle_id,
                               opened_at, closed_at          ← MART-owned, never dropped
bundles                        client × country × renewal date (derived; overridable?)
actual_state                   case_id, field, value, bm_value_at_assertion, reason,
                               asserted_by (user|AI), asserted_at, resolved_at, resolution
deadlines                      (scope, ref) bundle|case, promised_by, what, expected_date,
                               source, fulfilled_at, fulfilled_by (overview entry|manual)
seen_marks                     per case: last time I acknowledged its overview (→ "new")
playbooks (config YAML)        phases, items, relative due offsets (WD), gate rules, variants
work_items                     case_id, phase, title, source (bm+|playbook|manual|review),
                               due_date, status, assignee, waiting_on, depends_on
reminders                      target (scope, ref), remind_at, rule, snoozed_until, done
chasers / contact events       as in MAPT (ladder + who-reached-out/who-answered)
case_events                    append-only timeline: observed BM+ changes + user actions
review_checks                  case_id, check_id, result, value_before/after, waived_by/why
knowledge                      savings records, plan design change records, lessons
notes                          (scope, ref) comments, as in MAPT
```

The playbook and the review checks live in YAML, like MAPT's specs and audit
rules: one place, editable without touching code.

---

## 7. Relationship to MAPT NEO (decided)

**MART is built new, as its own app**, with its own repo, database,
ingestion, notes, to-dos, chasers, board and AI plugin. MAPT NEO is
reference only:

- **Reused as knowledge:** how the BM+ trackers are shaped (sheets, header
  rows, column names, the two Task Tracker flavours, the id system), the
  cross-tracker glue, NULL = TBC, working-day clocks, and the gotchas listed
  in §2.3 and in MAPT's CLAUDE.md.
- **Reused as patterns (rebuilt, not imported):** spec-driven ingestion (column
  names in YAML), stage → preview → commit uploads, the `(scope, ref)`
  convention, live filters, the MCP server's design rules.
- **Not carried over:** MAPT's database, its user data (notes, to-dos,
  chasers, meetings), and its analytics/exploration features, unless you
  ask for one specifically.
- MART's own ingestion fixes what MAPT can't do for a project tool: it
  keeps completed renewals, records changes between uploads, and treats the
  renewal cycle as a first-class object.

### Runtime and delivery (decided 03.11.2026)

The work laptop has **Python 3.12** (`C:\Program Files\Python312`) with only a
few preinstalled packages: `openpyxl`, `et_xmlfile`, `pandas`, `numpy`,
`python-dateutil`, `pywin32`, `six`, `tzdata`. pip points at the company's
internal package server, which needs credentials Martin doesn't have
(requested from IT as an optional extra, never required). No Node or Deno.

So MART is built to need **nothing installed**:

| Part | Built with |
|---|---|
| Database | `sqlite3` (standard library) |
| Web server | standard-library HTTP server + a small MART router, on `127.0.0.1` only |
| Pages | server-rendered HTML; a templating library only if clearly worth it, and then pure-Python, copied into `vendor/` (licence kept) |
| Excel in/out | `openpyxl` (preinstalled) |
| Browser side | HTMX, SortableJS (drag-and-drop), a chart library: plain JS files shipped in the folder, no build step |
| MCP connector | MART's own small JSON-RPC-over-stdio implementation (standard library), no MCP SDK |
| Outlook (optional, later) | `pywin32`, only if company rules allow it |

**Rules that follow:**
- Every dependency is either in the standard library, preinstalled on the
  laptop, or pure Python shipped inside MART. **No compiled packages.**
- The startup script checks this on launch and says clearly what is missing,
  instead of crashing.
- **Delivery = one zip**: unzip into a local folder, double-click
  `MART.bat`, open `http://127.0.0.1:<port>`. Updates = unzip the new
  version over the app folder.
- **Data lives outside the app folder** (its own data directory), backed up
  automatically to OneDrive or a company network folder. The live database
  never runs from a synced folder.
- MART **generates its AI plugin** with this machine's paths (see §7b).

---

## 7b. The AI plugin (MCP server + skills + templates)

MART ships with an **AI plugin**: one installable package that lets the local
AI agent *use* MART, not just query it. It has three parts:

```
mart-plugin/
├─ .claude-plugin/plugin.json      name, version, description
├─ .mcp.json                       registers the MART MCP server (stdio, the venv's python)
├─ skills/
│  ├─ mart-navigation/SKILL.md     data model, which tool answers which question, gotchas
│  ├─ mart-daily-plan/SKILL.md     the morning routine: read Today → propose a day plan
│  └─ mart-capture/SKILL.md        turn emails / meeting notes / broker replies into
│                                  notes, to-dos, deadlines, actual-state suggestions
├─ commands/                       slash shortcuts: /mart-today, /mart-client <name>,
│                                  /mart-stale, /mart-discrepancies
└─ templates/                      fixed shapes the agent fills (see below)
```

(The layout above is the Claude plugin format. If the agent is something
else, see QUESTIONS H1. The MCP server itself works with any MCP-capable
agent.)

### 0. The target app (what we know, 03.11.2026)

Martin's agent is a **company-built desktop app**, with a choice of OpenAI
and Anthropic models (mostly Sonnet 4.6 / 5). It uses the standard
skill / plugin format:

- **Connectors** = local MCP servers started by the app: `Name`, `Command`,
  `Arguments` (comma-separated), optional `Env Secrets`, and a `Mode`
  (both / plan / build). So MART's MCP server runs as a local stdio process.
- **Skills**: a `SKILL.md` plus `assets/`, `references/` and `scripts/`
  subfolders. Built-in skills run Python and JS scripts (the `docx` skill
  ships `scripts/blocks/*.py` using `python-docx`). Trigger is a slash
  command and/or automatic. Imported as `.zip`, `.skill` or `.md`.
- **Plugins** bundle skills, agents, hooks and connectors, and install as a
  `.plugin` or `.zip`.

Consequences:
- MART ships as **one `.zip` plugin**: connector registration + skills +
  templates in `assets/`.
- Word and Excel output can **reuse the app's built-in docx/xlsx skills**
  (MART supplies the data and template). MART only builds a file itself where
  the layout is fixed and must have a single implementation (e.g. the
  partner tracker).
- Skills must work on both OpenAI and Anthropic models: few tools, plain
  names, explicit steps. All write safety (AI stamp, source, undo feed)
  lives in MART, not in the model.
- Connector `Mode`: **both** (confirmed). Plan = the agent proposes, Build =
  it acts. MART refuses writes in Plan mode.

**What the app's `skill-builder` skill shows (v1.0.3):**
- The agent works in a **sandboxed workspace**: `workspace_bash`, `deno run`
  for TS scripts, and Python = **Pyodide** (WebAssembly, in the app, not
  the laptop's Python). No network inside the sandbox.
  → **Skill scripts cannot reach MART's database.** All MART data goes
  through the MCP connector, which the app starts as a real local process.
- Skill contract: folder name = frontmatter `name`
  (`^[a-z0-9][a-z0-9_-]{0,63}$`) + a `description` saying *when* to use it
  (optional: `icon`, `auto-detectable`). `references/*.md`, `scripts/`
  (Deno/TS or Python), `assets/` (UTF-8 text only). **5 MB per skill.**
  Script output goes to `$WORKSPACE_OUTPUT_DIR`.
- Skills can call other skills' scripts via `$SKILLS_DIR` (e.g. built-in
  `docx`, `marsh-xlsx`), and use `markitdown` / `render-doc`.
- Skills can be created by the agent itself (draft → `workspace_skill_save`)
  or imported as `.zip` / `.skill` / `.md`.
- Body conventions: a "Pick a mode" table, which reference to read for which
  task, "Hard rules" at the end; keep SKILL.md short (about 80 lines), detail
  in `references/`.

**Runtime on the laptop (03.11.2026):** `C:\Program Files\Python312\python.exe`
(Python 3.12) is installed; the `WindowsApps\python.exe` entry is only the
Store alias. **No Node, no Deno.** → MART's server and connector run on
Python 3.12, in MART's own virtual environment (no admin needed).

**Plugin format (from the app's plugin development guide):** the same shape
as Claude Code plugins.

```
mart/
├── .claude-plugin/plugin.json   # REQUIRED: {"name": "mart", "version", "description"}
├── skills/<skill>/SKILL.md      # + references/, scripts/, assets/
├── agents/<agent>.md            # subagents (frontmatter: name, description, model, tools)
├── commands/<command>.md        # slash commands
├── hooks/hooks.json             # optional (only if useful)
└── .mcp.json                    # the connector
```

- `.mcp.json`: `{"mcpServers": {"<name>": {"command", "args", "env",
  "working_dir", "init_timeout_secs", "call_timeout_secs", "mode": "both"}}}`.
- Installed from a **folder** (fastest while developing) or a **`.plugin` /
  `.zip`** archive; scope personal (global) or per project. An org
  marketplace exists for distribution later.
- **Namespacing:** skills become `mart:<skill>`; the connector becomes
  `mart__<server>`; its tools are seen as `mcp_mart__<server>_<tool>`, so
  server and tool names stay short.
- Skill frontmatter also accepts `icon`, `allowed-tools`, `model` (pin a
  model), `max-iterations`, `triggers`; a skill body over about 5000 tokens
  draws a warning (detail goes in `references/`).
- The app's diagnostics lint expects each skill to have a **"## What I Need
  From You"** (or "## Required Inputs") section.
- Paths in the manifest start with `./` and never contain `..`.

Consequence: the connector's `command` must point at **this machine's**
MART Python and server script. MART therefore **generates its own plugin**
(a `build_plugin` tool writes `.mcp.json` with the real paths and
`MART_DB_PATH`, then zips the folder), so nobody types paths by hand.

### 1. MCP server (`tools/mcp_server.py`, registered as `MART`)

| Kind | Tools (first sketch) |
|---|---|
| Orient | `today()` · `list_clients()` · `client_overview(client)` |
| Drill down | `bundle(client, country, date)` · `renewal(id)` · `overview_timeline(id)` |
| Signals | `new_overviews(since)` · `stale_overviews()` · `deadlines(due\|overdue)` · `discrepancies()` |
| Your data | `notes(scope, ref)` · `todos(filter)` · `contact_log(id)` |
| Writes (user data only) | `add_note` · `create_todo` · `set_deadline` · `fulfil_deadline` · `mark_seen` · `log_contact` · `suggest_actual_state` (you confirm in MART) |
| Escape hatch | `describe_schema` · `query` (read-only connection) |

Lessons carried over from MAPT's server:
- Tool and server names must match `^[a-zA-Z0-9_-]{1,128}$`. One bad
  character makes strict runtimes reject *every* tool.
- Return **compact rows**. Long text (overview histories) comes from its own
  tool, or the output limit is exceeded.
- **Purpose-built tools before SQL.** The skill says so explicitly, so
  answers match what the web app shows.
- **Never write tracker (BM+) data.** Everything the agent writes is
  stamped `created_by='AI'` and shown as such.
- A tool that writes a **file** requires an explicit `path`, with no default
  folder. The agent asks the user where it should go.
- A `mcp_selftest --config` tool prints the exact registration for this
  machine, so nobody types paths from memory.

### 2. Skills
Written for the agent: when to use which tool, the data model in a few
paragraphs (case → bundle → renewal; BM+ state vs actual state; NULL = TBC;
working days), and step-by-step routines (morning plan, capture, meeting
prep). The skill text is kept in the repo next to the code, so a tool change
and its description change in the same commit.

### 3. Templates
Fixed shapes the agent fills, so output looks the same every time. Two
families; which ones are wanted is QUESTIONS H2:

| Out of MART (reports) | Into MART (extraction) |
|---|---|
| Daily brief | Broker email → deadline + note ("update by Fri 15.11") |
| Client status (per bundle) | Meeting notes → to-dos + actual-state suggestions + notes |
| Discrepancy list for brokers/COE ("please submit in BM+") | Broker reply → contact log entry (answered / acknowledged only) |
| Meeting prep / agenda | Pasted BM+ overview text → what changed |
| Post-renewal review summary | |
| Chase email draft | |

Each template = a markdown file with the required inputs (which tools to
call), the output skeleton, and rules (e.g. a client-facing output never
includes `!`-internal notes or internal overview entries).

---

## 7c. Knowledge base (decided 03.11.2026)

Savings must still be **recorded in BM+**. MART holds the **central
knowledge**: what was saved, what changed in the plan design, what was
learned, what a client prefers. There is no existing format to match.

**v1: start simple, grow from use.** Martin can't yet say what he will
look things up by, so no detailed schema up front.

- **Entry** = one short fact: `type` (savings · plan design change · lesson
  · client fact), short text, BM+ figures where they exist (amount, %,
  currency, BM+ savings category and driver), free tags, and links to the
  renewal cycle → policy, client, country, insurer, product group.
- **Sources:** each upload creates or refreshes savings entries from the
  Renewal Tracker's **Savings** and **Proposals** sheets. Martin adds or edits
  entries by hand (his AI agent can too, over MCP). MART does **not**
  calculate savings itself.
- **Provenance:** every entry is marked *from BM+* or *by you* (or *AI*). An
  upload refreshes only BM+-sourced entries and never overwrites what was
  typed in MART.
- **Internal only:** read by Martin alone. Never included in client-facing
  output, so it can stay terse.
- **Where it shows:** a Knowledge section in each renewal's panel, a
  per-client view, search across everything, and year-over-year history per
  policy.
- **Post-renewal review** has two separate checks: *BM+ Savings section
  filled?* and *knowledge recorded in MART?*
- Fields get added later from real use (e.g. structured plan-design fields
  once a pattern shows).

---

## 8. Possible build order (once the questions are answered)

Re-ordered after round 2, so that the things Martin described come first:

1. **Backbone**: reused ingestion → `renewal_cases` + derived bundles +
   change events, with overview entries parsed (freshness comes for free)
2. **Client page** (renewals by country × date) + **renewal drawer** with
   notes and to-dos
3. **Home** (client cards + Today) and the **AI plugin v1**: MCP server (reads + user-data writes) + the navigation skill
4. **Broker deadlines** + overview new/stale + seen-marks
5. **Actual state + discrepancies** + the **Kanban board**
6. Reminders / chasers / Outlook .ics
7. Playbook YAML + back-scheduled work items + health
8. Post-renewal review checks + waivers, then knowledge capture (savings /
   plan design) + reporting

---

## 9. Questions & clarifications

All open questions now live in **`QUESTIONS.md`** (grouped A–J, with space for
the answers, and the most important ones starred).
