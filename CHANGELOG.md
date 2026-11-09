# Changelog

What changed in each MART version, newest first. The version is in
`mart/__init__.py`, shown in MART's sidebar and in the zip's
`BUILD-INFO.txt`. Format: one section per version, grouped into **Added**,
**Changed**, **Fixed**; the "What to try" list is for testing it on the
laptop.

## 0.9.30 — 08.11.2026 · M3 day 9 · the stewardship

### Added
- **A stewardship page per client** (Explorer → "Stewardship →"): what the
  client's renewals achieved over its **reporting period**, for the yearly
  stewardship meeting.
  - **Which policies are included** is said at the top: the renewals with
    a **renewal date in the period** (completed or still open); a renewal
    BM+ no longer exports still counts.
  - The period is the client's **reporting year**, starting on the 1st of
    its own month (Period… → "starts on the 1st of …"; calendar year until
    set), ‹ › for the year before / after, or one-off from / until dates.
  - A summary: renewals and how many completed, remarketed and insurers
    changed, proposals and insurers, plan design changes implemented / not,
    strategies, and the **savings per currency** (never added across).
  - Then by country, each renewal: strategy, insurer (→ the new one when it
    changed), proposals and the chosen one ★, BM+'s expected change, plan
    design changes (✓ implemented, ✗ not and why), savings, key learning.
  - **Print / PDF**: the page alone, without menus or buttons.
- **Savings per renewal**, in the renewal panel's Savings section (yours
  first, then BM+'s Savings sheet as "In BM+") and on the stewardship page:
  - **hard savings** = expiring premium − final premium;
  - **cost avoidance** = first quote − final premium (of the chosen proposal ★);
  - **unrealized savings** = final premium − the cheapest option the client
    didn't take.
  MART suggests them from your quotes and BM+'s expiring premium, each with
  what it was worked out from ("suggested by MART"); **Confirm…** keeps
  your figures ("✓ confirmed"), "Use MART's suggestion" goes back. Only
  amounts in the same currency are compared, never converted; BM+'s expiring
  premium is in the client's reporting currency, so hard savings are
  suggested when the final quote is in it. A suggestion above half of what
  it is measured against is flagged: the quotes may be for another cover.
- **A key learning per renewal**, one line, beside its savings.
- MART now keeps each client's **reporting currency**, from a single-client
  Renewal Tracker (the only export that names it).

### What to try
1. A renewal → Proposals: first and final quote of the chosen insurer ★, a
   quote from another → Savings & key learning: the three suggestions. Confirm…
2. Upload a single-client Renewal Tracker once, so MART knows the reporting
   currency (needed for hard savings).
3. Explorer → Stewardship → Period… → the client's reporting year → Print / PDF.

## 0.9.29 — 07.11.2026 · plan design changes, reshaped

Martin, 07.11.2026 (QUESTIONS D1b): "BM+ suggests" wasn't intuitive. What a
plan design change needs to say in the end: implemented or not, and if
not, why; and it often applies to several renewals at once.

### Changed
- **One change for several renewals.** A plan design change now applies to
  one or more renewals: all of a bundle's when added from the bundle (untick
  the ones it doesn't cover), the renewal itself when added from a renewal
  (tick others of its bundle). ✎ changes which renewals it applies to.
- **Open → implemented, or not implemented with why.** "Suggested",
  "agreed" and "dropped" are gone; "Outcome…" records implemented (it takes
  effect with the renewal) or not implemented, which asks why (client
  declined, insurer refused, deferred…).
- **BM+'s text once, one line per change.** The bundle page and the renewal
  panel show BM+'s plan design text once, as "In BM+": considered, the
  reason, and each change on its own line (split at line breaks and
  bullets), with **+ Track** and **×**. Tracking a line covers every renewal
  of the bundle whose BM+ text lists it; a tracked line shows ✓, a dismissed
  one can be offered again. The Strategy section no longer repeats BM+'s
  three plan design rows.
- **The bundle page has its own plan design block**, under the bundle's
  to-dos and notes; its header counts open / implemented / not implemented.
- **The edit bar's "Plan design…" adds ONE change** covering the ticked
  renewals (it used to add a copy to each).
- The client's overview lists each change once, with the renewals it
  applies to, filtered by outcome.

### Added
- **Premium effect (optional)** on a change: "-2.5 %" or "-25'000 EUR", as
  typed (no k or m).

### Kept
- Every change recorded before is kept (migration 18): suggested and
  agreed ones are open, implemented stay implemented, dropped ones are not
  implemented (no reason recorded). A BM+ suggestion taken over or
  dismissed before counts for every line of that BM+ text.

### What to try
1. A bundle where BM+ lists plan design changes → "In BM+" → **+ Track** on
   one line: it applies to every renewal of the bundle that lists it.
2. **+ Change** on the bundle → untick one renewal, premium effect "-2 %".
3. **Outcome…** → Not implemented → why. Then the client's Plan design
   changes page → Not implemented.

## 0.9.28 — 07.11.2026 · Explorer ⇄ Board, your clients on Home

### Added
- **Your clients on Home** (Martin, 07.11.2026): the first card on Home
  lists your clients, those needing attention first, each with what is
  waiting (updates passed, new entries, gone quiet, open to-dos) and two
  buttons, **Explorer** and **Board**. With more than 12 clients the rest
  fold behind "N more clients". It replaces the client cards that sat
  below Today.
- **Explorer | Board** switch (Martin, 07.11.2026): two joined buttons
  under the client's name in the explorer's side panel and beside the
  board's title; the page you are on is filled. It replaces the
  "Board →" link in the side panel.

### What to try
1. Home → Your clients → Board on a client; then Explorer on the board's
   switch, and Board again in the side panel.

## 0.9.27 — 07.11.2026 · type to find a country

### Added
- **Type to find** (Martin, 07.11.2026): a filter list of more than six
  names (countries, and regions where a client has that many) opens with a
  "Type to find…" box, the cursor already in it. Typing shows the names
  that contain it (case and accents ignored), within the ticked regions;
  Enter ticks the first one shown and empties the box for the next, so
  "bel ⏎ kor ⏎" ticks Belgium and Korea without scrolling.

### What to try
1. Explorer or board → All countries → type "bel", Enter, "kor", Enter.

## 0.9.26 — 07.11.2026 · several regions and countries

### Changed
- **Several regions and countries at once** (Martin, 07.11.2026): in the
  explorer's side panel and on the board, "All regions" and "All countries"
  open a list of tick boxes; tick as many as you like. A bundle shows when
  it is in one of the ticked regions and one of the ticked countries.
- **The filters follow each other:** ticking a region narrows the country
  list to that region's countries (this client's own regions). A country
  hidden that way is unticked, so nothing filters out of sight. "Untick all"
  in each list, "Clear filters" for everything.
- The two lists sit side by side in the side panel, so an open one never
  covers the other. The filters are still remembered per client in the
  tab, the single region or country of an older version too.
- One filter box (`partials/filters.html`) for the explorer and the board.

### What to try
1. A client's explorer → All regions → tick one: the country list shows only
   its countries. Tick a second region, then two countries.
2. Open a bundle: the filters stay. The board has the same filters.

## 0.9.25 — 07.11.2026 · an open Edit stands apart

### Changed
- **An open Edit sits on a light panel** (Martin, 07.11.2026): a to-do's or
  a note's Edit opens on a lightly shaded box with a thin border, so it is
  clear where this item's fields end and the next item starts. Everywhere
  the Edit menu is (topic board, renewal and bundle pages, To-dos page),
  light and dark.

### What to try
1. Client notes & to-dos → a to-do → Edit: its fields sit on a grey panel,
   the next to-do below it is clearly apart.

## 0.9.24 — 07.11.2026 · M3 day 8 · repeating to-dos

### Added
- **Repeating to-dos** (Martin, 05.11.2026, QUESTIONS M3b): "Repeat every
  [N] [days / weeks / months]" in every to-do's add form and Edit menu; for
  weeks, tick the weekdays (Mon … Sun). No working days, no holidays.
- **Ticking one done adds the next**, due one step after its due date (or
  after today when it has none): the same place (renewal, bundle, client
  topic), title, urgency, description and subtasks (unticked), and the same
  repeat. A monthly one on the 31st falls on the month's last day and comes
  back to the 31st. Ticked very late, the next one still lands after today.
- Unticking leaves the next one as it is, and ticking again never adds a
  second one. "— doesn't repeat —" in Edit stops it.
- A repeating to-do shows "↻ every month" (or "↻ every 2 weeks on Mon,
  Thu") beside its title.

### What to try
1. Client notes & to-dos → Partner tracker → + To-do "Release the partner
   tracker", due the last day of the month, repeat every 1 month → tick it:
   next month's is there.

## 0.9.23 — 07.11.2026 · M3 day 7 · client topics

### Added
- **Client topics** (Martin, 05.11.2026, PLANNING §5b): the client's own
  notes and to-dos (not those on a renewal or a bundle) in named, coloured
  topics. Client notes & to-dos (side panel) is now a **board**: a column
  per topic with its colour as a stripe, and in each column:
  - "+ To-do" / "+ Note" straight into that topic;
  - the open to-dos (urgent and overdue first), then the **pinned** notes
    (📌: key facts such as the partner-file recipients), then the newest
    notes (older ones fold away), and the done to-dos folded;
  - a footer such as "1 open · 1 urgent · next due 08.11 · 📌 1", so a
    column tells its story at a glance.
- **General** holds everything that isn't in a topic; every existing client
  note and to-do starts there. It can't be renamed or deleted.
- **+ Topic**: a name, one of eight colours, an optional country (its
  flag; only a label, renewal and bundle notes stay where they are) and a
  state: active, **on hold** (shown last, dimmed) or **done** (archived
  below the board, open it to change it back). ✎ on a column changes or
  deletes a topic; deleting moves its notes and to-dos to General.
- In a note's or to-do's **Edit**: **Topic → Move** puts it in another
  topic. 📌 on a note pins or unpins it.
- The **To-dos** page shows a client to-do's topic as a coloured chip.

### What to try
1. A client → Client notes & to-dos → + Topic "Partner tracker" (teal),
   "Implementation – Brazil" (amber, Brazil).
2. + Note in Partner tracker with the file's recipients → 📌 it.
3. Move an older client note from General into a topic (Edit → Topic).

## 0.9.22 — 07.11.2026 · QA: fixes from the code review

### Fixed
- **Edit renewals…: Enter in any field cleared your strategy** on every
  ticked renewal (it fired "Set the strategy" with its empty default). Enter
  now submits nothing; each action goes only through its own button, and
  "Go by BM+ (drop yours)" is an explicit choice in the strategy list.
- **BM+ moving a renewal date no longer strands your bundle data.** When
  every renewal of a bundle moves to the same new date, its board stage,
  expected update, name, notes and to-dos move with it. If the renewals
  split over several dates, or the new bundle already has something of
  yours, nothing moves and both bundles stay visible.
- **A client spelled differently in an export** ("Acme Group AG") no longer
  takes the renewals away from the client MART has them under; the upload
  message says how many stayed.
- **Your strategy now counts on the board**: with your "Incumbent with Rate
  Guarantee" the Proposals stage is not needed, so the card moves on to
  Update Policy (and "BM+'s stages are all done" can show).
- Board: moving a card back to a stage BM+ has since passed is kept, and so
  is a reason added to the stage a card is already in.
- Changing only the reason of your strategy no longer hides that BM+ has
  moved to another strategy since.
- Home: a bundle whose renewals are all marked completed is no longer
  listed as gone quiet, nor its BM+ date as passed (a date you set stays).
- To-dos of a client that is no longer yours are hidden (not deleted)
  instead of listed and impossible to tick or open.
- Amounts: "1.2m", "120k" or "1e5" are refused instead of saved as 1.2,
  120 or 15; write the number out ("EUR 120'000" and "120'000 CHF" work).
- Proposals: "lowest" only when two or more are priced in the same
  currency; the list is ordered by currency, then premium.
- An overview entry dated in the future (a typo like 2027 for 2026) no
  longer keeps a renewal "fresh" or "new".
- The renewal page, client notes, plan design changes and regions pages
  no longer build the bundle's cards they never show (0.59 s → 0.02 s on
  a 300-renewal bundle).
- A form's way back is checked by one rule (no other site, no control
  characters), and a redirect refuses control characters.

### What to try
1. Edit renewals… → tick two → Proposal / quote… → type an insurer → press
   Enter: nothing happens; "Add to the selected" adds it.
2. Set "Incumbent with Rate Guarantee" as your strategy on a renewal whose
   strategy task is done: its card moves to Update Policy.

## 0.9.21 — 07.11.2026 · QA fixes

### Fixed
- In a narrow (portrait) window, the bundle header's summary row
  (Strategy · Board · BM+ workflow · Proposals · Plan design · Completed)
  ran out of the window; it wraps now.
- The board's cards cut long country names ("Nether…"); they wrap now.
- **Settings → Save** answered with the page itself, so reloading it
  offered to send the form again; it now returns to the settings page
  with the same messages ("Settings saved.", "Database moved …").
- A test failed when it ran across midnight (it kept the previous day's
  date); MART itself was right.

### What to try
1. Make the window narrow and open a bundle: the summary row wraps.
2. Settings → Save, then reload the page: nothing is sent again.

## 0.9.20 — 07.11.2026 · one Clients page, a large card per client

### Changed
- **The Clients list and the Board's client picker are one page**
  (Martin, 06.11.2026): **Clients** shows a large card per client with
  **Board →** and **Explorer →**, and on it:
  - its renewals, bundles, countries (and the client's own regions) and
    the next renewal;
  - its **board in one row**: how many bundles sit in each of the seven
    columns (hover for what a column means; click for the board);
  - **Needs you**: passed / near expected updates, new overview entries,
    bundles gone quiet, open to-dos (the same counts as Home);
  - **Recorded by you**: renewals completed, strategies set (≠ BM+ on …),
    proposals received, bundles moved on the board;
  - **BM+ data**: how old the client's overview is, and renewals without
    a client-ready overview, with gaps or with none;
  - links to the client's notes & to-dos, plan design changes and regions.
- The main menu's **Board** entry is gone: a board opens from its client's
  card (or the explorer's side panel). `/board` still works: with one
  client it opens that client's board, otherwise the Clients page.

### What to try
1. Clients → read a card; Board → for a status call; Explorer → to work.

## 0.9.19 — 06.11.2026 · a leaner renewal page, BM+ to the fore

### Changed
- **The renewal page is leaner** (Martin, 06.11.2026: the MART cards took
  the room; he wants more of BM+). New order: header → to-dos and notes →
  BM+ stages → **renewal overview** → Strategy → Proposals → Renewal →
  Savings → the folded rest.
- **The header carries your actual state**: the strategy that counts (✎
  yours, else BM+'s) with "≠ BM+: …" when they differ and a ✎ to set or
  change it (your earlier changes are listed under its form); **✓ Mark
  completed** (green when BM+'s three stages are all done) or the
  completed badge; and the bundle's **Board** stage, which opens the same
  move form as on the board. The "Actual state" card is gone.
- The header also names the **expiring insurer** (with its networks, or
  "no network partner") and the **expiring premium** (BM+). The bundle line
  became the back link with a ⇄ beside it to move the renewal.
- **To-dos and notes** come first, as one slim line when there are none.
- **BM+ stages** in one slim row: state, due date and who; peer review and
  due-date moves on hover.
- **Renewal overview** right after the stages, the newest three entries
  open.
- **Strategy**: your strategy (✎, with why) above BM+'s Renewal Strategy
  sheet, and **plan design changes** inside it: BM+'s "considered /
  comments", its suggestion and your changes.
- **Proposals**: one section, yours first (to compare), BM+'s Proposals
  sheet below as "In BM+"; with none, one line.
- An empty Savings is one line too.
- Inside a BM+ section, what you wrote carries ✎ and a blue edge on its
  left, so MART and BM+ stay told apart without separate cards.

### What to try
1. Open a renewal: the overview is on the first screen.
2. ✎ beside the strategy pill → set yours; it shows in the header and at
   the top of Strategy.
3. "+ Change" in Strategy; "+ Proposal" in Proposals.

## 0.9.18 — 06.11.2026 · the renewal overview starts closed

### Changed
- In a bundle with only one renewal, the card's **Renewal overview** no
  longer starts open (Martin, 06.11.2026): like in every other bundle, it
  is closed when the page opens; click it to read it.

### What to try
1. Open a bundle with one renewal: its overview is closed.

## 0.9.17 — 06.11.2026 · why a card was moved, shown

### Added
- **The reason you gave when moving a card is shown** (Martin,
  06.11.2026: "where is this reason shown?"):
  - on the card, as a short line ("✎ quotes in, HR deciding"), while
    your stage applies;
  - behind the card's **✎**: click it for every move of that bundle on the
    board, newest first: when, to which column, where BM+ had it, and why.
    The ✎ stays (greyed) once BM+ caught up or the card follows BM+
    again, so the earlier moves can still be read;
  - in the bundle header: the same list under the Board stage's form (on
    the client page and in the board's pop-up).

### What to try
1. Drag a card to another column with a reason → the card shows it.
2. Click its ✎: your moves, with dates and reasons.

## 0.9.16 — 06.11.2026 · the column meanings behind an ⓘ

### Changed
- The board's column meanings are no longer always shown (Martin,
  06.11.2026): an ⓘ beside each column's name shows the line on hover or
  click, like the other ⓘ in MART. The window after a drag and the stage
  forms still show the meaning of the stage picked.

### What to try
1. Board → hover (or click) the ⓘ beside "Decision".

## 0.9.15 — 06.11.2026 · what each board column means

### Added
- **Each board column says what it means** (Martin, 06.11.2026: the
  guideline for the renewal pipeline), under its title, so you can see why
  a card is there and when to move it on:
  - **Not started**: the renewal has not been kicked off.
  - **Strategy**: the renewal has been kicked off; the strategy is pending.
  - **Proposals / Marketing**: the strategy is decided; terms and proposals
    for the renewal are being collected.
  - **Decision**: the final proposals from the insurer(s) are in; the
    client's decision is pending.
  - **Update Policy**: the renewal is confirmed with the client; the data
    in BM+ needs to be updated.
  - **Post-renewal review**: review all data, note key learnings, savings
    and plan design changes, and check that the policy documents are
    uploaded to BM+.
  - **Done**: all tasks have been completed.
- The same line shows when you move a card: in the window after dragging,
  and under the stage you pick (⇄ on a card, or the bundle header's Board
  stage).
- The column heads line up, so the cards of every column start level.

### What to try
1. Open a board: read the columns' lines.
2. ⇄ on a card → pick another stage: its line changes with it.

## 0.9.14 — 06.11.2026 · the board stage from the bundle itself

### Added
- **Move a bundle on the board from the bundle** (Martin, 06.11.2026): the
  "Board" stage in the bundle header (on the client page and in the
  board's pop-up) opens the same small form as ⇄ on the card: pick the
  stage, an optional reason, and into Done optionally mark its open
  renewals completed. Closing the pop-up shows the card in its new column.
  "Board" above it still leads to the board.

### What to try
1. Board → open a card → click its "Board" stage (e.g. "Not started ▾") →
   pick Decision → Move → click beside the pop-up.

## 0.9.13 — 06.11.2026 · a foldable menu, pop-overs kept in view

### Added
- **Fold the menu** (Martin, 06.11.2026): the button at the foot of the
  main menu folds it into a slim strip of icons (the names show on
  hover); › opens it again. Remembered in this browser.

### Fixed
- The board's ⇄ pop-over on the leftmost column was cut off at the
  board's left edge (it opened leftwards, out of the board's scroll area).
  Every pop-over in MART now opens where it has room: on its usual side,
  else the other, else shifted, so the board, a table or the menu never
  cut it off.

### What to try
1. Board → ⇄ on a card in "Not started": the pop-over opens to the right.
2. Fold the menu at its foot; open another page: it stays folded.

## 0.9.12 — 06.11.2026 · the board's cards open over it

### Added
- **A card opens its bundle over the board** (Martin, 06.11.2026). Click a
  card: the bundle page opens in a pop-up on top of the board, and works
  as on the client page: edit renewals, proposals, plan design, completed,
  the expected update, notes and to-dos, and its renewals (← back to the
  bundle stays in the pop-up).
- **A click outside** (or ×, or Esc) shrinks it back into its card. If you
  changed something in it, the board is refreshed first, so the card
  already shows it, in its new column if it moved.
- "Open the full page ↗" leaves the board for the page shown in the
  pop-up. Ctrl-click on a card still opens it in a new tab; dragging a card
  works as before.

### What to try
1. Board → click a card → mark a renewal's strategy or add a proposal in
   the pop-up → click beside it: the card shows the change.
2. In the pop-up, open a renewal, then go back to the bundle.

## 0.9.11 — 06.11.2026 · M3 day 6 · the board

### Added
- **The board**, one per client (**Board** in the main menu, "Board →" in
  the side panel and on the Clients list). Seven columns: **Not started ·
  Strategy · Proposals / Marketing · Decision · Update Policy ·
  Post-renewal review · Done**, a card per **bundle**.
- **Where a card starts**: at its **least advanced** renewal's stage (M3d),
  read from BM+'s three tasks: strategy at work → Strategy; strategy done →
  Proposals / Marketing (or Update Policy when the strategy needs no
  proposals); proposals done, policy update not started → Decision; policy
  update at work → Update Policy; all three done → Post-renewal review;
  every renewal marked completed by you → Done. A bundle at mixed stages
  says "2 of 3 at Proposals / Marketing" (hover: where the others are).
- **Drag a card** into another column to record its actual stage. A small
  window asks for an optional reason; Enter moves it, Esc puts it back.
  The ⇄ on each card does the same without dragging. Into **Done** you can
  also mark the bundle's open renewals completed today, in one go.
- **Your stage beside BM+'s**: a card you moved shows ✎ and "BM+: …" where
  BM+'s tasks put it. Once BM+ gets there (or further), the card follows
  BM+ again by itself ("✓ BM+ caught up"). A card you moved BACK stays
  there while BM+ stands still; if BM+ moves on, it says "≠ BM+ moved to …".
  Moving a card to the column BM+ has it in = follow BM+ again.
- **On each card**: flag, country, date (and your bundle name), the
  strategy pills (yours ✎), renewals, proposals received and from whom,
  completed count, BM+'s stage dots, ≠ (your strategy differs from BM+'s),
  the stale and broker-deadline badges.
- **Filters**: text, region (the client's own), country, from / until —
  the same as the explorer's and remembered with them; the column counts
  follow the filters.
- The bundle header in the explorer shows the bundle's **Board** stage.

### Changed
- The main menu's "Board" (greyed out since M1) now opens the board; with
  one client it goes straight to that client's board.

### What to try
1. Board → run through a client's bundles as on a status call.
2. Drag a bundle into **Decision** with a reason ("quotes in, HR to
   decide"); open the bundle: its header says Board ✎ Decision.
3. Drag a finished bundle into **Done** and tick "also mark … completed".
4. Filter the board by region and by date.

## 0.9.10 — 06.11.2026 · M3 day 5 · regions per client

### Added
- **Each client's own regions.** "Regions →" (beside "Plan design changes →"
  in the side panel) lists the client's countries with **BM+'s region**
  and the **region for this client**: prefilled from BM+ (per country the
  commonest value, cleaned: "EMEA, EMEA" → "EMEA"), changeable per country
  for this client only — e.g. "North America" and "LatAm" instead of
  BM+'s "US&C" and "LATAM". One "Save the regions" for all; an empty field
  (or BM+'s own name) goes back to BM+'s. Your regions are marked ✎.
- **Region filter** in the side panel, above the country filter: shows only
  the bundles of that region; remembered like the other filters.
- The bundle header names the bundle's region.

### What to try
1. Open a client → Regions → set "North America" for Canada and the United
   States → Save.
2. Pick "North America" in the side panel's region filter.

## 0.9.9 — 06.11.2026 · M3 day 4 · plan design changes

### Added
- **Plan design changes** on each renewal: a new section in the renewal
  panel (written in MART), after the proposals. **+ Change**: what changes
  ("deductible 500 → 1'000"), an optional detail, and where it stands —
  **suggested → agreed → implemented**, or **dropped** — since when.
  **State…** moves it on; the dates of the earlier states stay, so you can
  see when it was suggested and agreed. ✎ rewords it, × deletes it.
- **BM+'s suggestion**: when BM+'s Renewal Strategy sheet names types of
  plan design changes (or the Overview has plan design comments with
  changes considered), the section shows "BM+ suggests …" with **Take it
  over** (it becomes a suggested change of yours, marked "from BM+") or ×
  (not for this renewal; not offered again). BM+ itself is never changed.
- **Several renewals at once**: "Plan design…" in the bundle's edit bar
  adds the same change, in the same state, to every ticked renewal.
- **All of a client's changes**: "Plan design changes →" under the client
  notes in the side panel opens the overview: every change with its
  renewal, by renewal date, filtered by state (suggested / agreed /
  implemented / dropped), each linking to its renewal.
- The cards show "Plan design: 1 agreed · 1 implemented"; the bundle header
  counts them.

### What to try
1. On a renewal: + Change, then State… → agreed, later → implemented.
2. A renewal where BM+ lists plan design changes: Take it over.
3. Edit renewals… → Select all → Plan design… ; then the client's "Plan
   design changes →" overview.

## 0.9.8 — 06.11.2026 · act on several renewals at once

### Added
- **"Edit renewals…"** (it was "Move renewals…") opens the bundle's edit
  mode: tick renewals on the cards, or **Select all** for the whole bundle,
  and act on all of them at once:
  - **Strategy…**: your strategy (or "go by BM+") with a reason, for each
    ticked renewal;
  - **Proposal / quote…**: one insurer and variant, quote round, date,
    currency, rate change and note, with **a premium per renewal** (only the
    ticked ones are listed). Where that insurer and variant already has a
    proposal on a renewal, it becomes its next quote, so a bundle's
    negotiation can be followed in one go. All or nothing: a wrong premium
    changes none of them;
  - **Completed…**: a date and a note;
  - **Move…**: as before.
  The actions wait until something is ticked; afterwards the bundle stays
  in edit mode and says what was done ("Strategy set to Remarketing for 3
  renewals."). The insurer field suggests the country's network partners,
  as on a renewal. Plan design changes will join here (day 4).

### What to try
1. Open a bundle → "Edit renewals…" → Select all → Strategy… .
2. Tick two renewals → Proposal / quote… with a premium for each; later the
   final quote the same way.

## 0.9.7 — 06.11.2026 · a proposal holds its negotiation

From Martin's use of 0.9.5–0.9.6: every updated quote was its own row, so
some renewals had a long list.

### Changed
- **One proposal = one insurer and variant**, holding its **quotes**:
  first, revised…, final. A variant is the plan design (as expiring /
  changed) plus an optional **label** ("higher deductible", "with
  dental"), so the same insurer can have several proposals side by side.
- **"+ Quote"** on a proposal adds its next quote (the form offers
  "revised", then "final", with the last currency filled in). "+ Proposal"
  for an insurer and variant you already have adds the quote there.
- Each row shows the **latest quote** (premium, rate, note) and **how far it
  moved** since the first ("−5.6 % from 1'250'000"); **Negotiation: 3
  quotes** opens every quote in order, each with ✎ and ×. The comparison
  ("lowest") goes by each proposal's latest quote. ✎ on the row changes the
  proposal (insurer, plan design, label) and its latest quote.
- **Your existing proposals are merged** on start-up: the quotes you
  recorded for the same renewal, insurer and plan design become one
  proposal with those quotes (a chosen one stays chosen).
- Rates never break from their "%" across lines.

### What to try
1. Open a renewal where you recorded several quotes from one insurer: they
   are one row now; open "Negotiation".
2. "+ Quote" on a proposal for the next round; "+ Proposal" with a label
   for a second variant of the same insurer.

## 0.9.6 — 06.11.2026 · M3 day 3 · the Insurer Capability Database

### Added
- **A new tracker: the Insurer Capability Database** ("All Networks"). Drop
  it on Uploads like the other trackers. It is a **reference list for all
  clients**: the preview shows how it compares with the one MART has (new /
  changed / unchanged / no longer in the list), and loading it **replaces**
  it as a whole, so a newer version can be loaded at any time. Only the
  "Database" sheet is read; other sheets a version may carry are ignored.
  Like every export, the file itself is never kept and never in git.
- **Insurers** (new in the menu): pick a country to see its local partners
  of the international networks (AIA, Allianz, Generali, IGP, Insurope,
  MAXIS, Swiss Life, Zurich), each with its networks and "fully insured on
  5 of 7 lines · pooling on 3"; open one for each line of risk: fully
  insured, multinational pool, global insurance program, captive (with the
  quota shares) and the comments. Filter by network and line of risk. The
  same insurer written differently per network ("Manulife" / "Manulife
  Financial Corporation – Canadian Division") is shown once.
- **Choosing insurers for a remarketing**: the "+ Proposal" insurer field
  now suggests the country's network partners first, each with its
  networks, then the insurers this client already has in that country.
- **The networks behind an insurer**: each proposal shows the networks its
  insurer partners with in that country, and the section names the
  expiring insurer's networks ("Expiring insurer: Desjardins … MAXIS"),
  with a link to all network partners of the country.
- Home → Your data says which Insurer Capability Database is loaded.

### Changed
- Insurer names are matched within the country, ignoring case, accents,
  punctuation and legal / generic words ("Allianz" = "Allianz
  Lebensversicherungs-AG", "AXA" = "AXA Seguros S.A. de C.V.").
- Country names: Bonaire, Palestine and Sint Maarten (Dutch Part), as the
  database writes them, now get their flags.

### What to try
1. Upload `2025 Insurer Capability Database - All Networks.xlsx` on Uploads,
   check the preview, commit.
2. Open **Insurers**, pick a country you renew in, open a partner.
3. On a renewal in that country: "+ Proposal" → the insurer field suggests
   the network partners; the expiring insurer's networks show above.

## 0.9.5 — 06.11.2026 · M3 day 2 · proposals received

### Added
- **Proposals received**, recorded by you as the mails come in (M3f), to
  compare them. A new section in the renewal panel (written in MART), right
  after the actual state. **+ Proposal**: insurer (the client's insurers are
  suggested), first / revised / final quote, the date it arrived, the
  annual premium + currency, the rate change % the insurer quoted, plan
  design as expiring or changed, a note.
- **Side by side**: each insurer's latest quote counts (final before revised
  before first; earlier ones are greyed), sorted by premium, the lowest per
  currency marked **lowest**. Mark one as **★ chosen**. ✎ changes a
  proposal, × deletes it.
- Premiums and rates are taken as you type them: `1'250'000`,
  `1.180.000`, `1,210,000`, `1 195 000`, `+6,5`, `-3.5 %`.
- **On the cards**: "3 proposals: Allianz, AXA, Generali" and "★ AXA"; the
  **bundle header** counts them ("5 from 3 insurers").
- BM+'s own Proposals sheet stays below as **Proposals in BM+**, for
  reference; its expiring premium is shown as a hint next to yours.

### What to try
1. Record the quotes you have for one remarketing (first and final from the
   same insurer, too) and see them compared.
2. Mark the chosen one; check the card and the bundle header.

## 0.9.4 — 06.11.2026 · polish: the open dropdown lists

### Changed
- **The list a dropdown opens is no longer a square box.** It now has
  rounded corners, MART's colours (light and dark), a soft shadow, rounded
  rows, the chosen entry highlighted in blue, and an arrow that turns while
  it is open. This covers every dropdown: the side panel's country filter,
  your strategy, the to-do urgency / status / waiting-on, and the move bar.
  It needs Edge or Chrome from 2025 on; an older browser keeps its own list,
  which still works.
- The **date filters' calendar** (from / until) is drawn by the browser
  itself and can't be restyled; see QUESTIONS M3i.

### What to try
1. Open the country filter in a client's side panel, and ✎ on a
   renewal's strategy: the lists are rounded and match MART.

## 0.9.3 — 06.11.2026 · fix: dropdowns look like the rest of MART

### Fixed
- **The strategy dropdown was a slim grey rectangle** (the browser's own
  look). Every dropdown now has the same height, border, corners and
  colours as MART's text fields, including the urgency dropdown when you
  add a to-do; the smaller ones (side panel, move bar, to-do edit row) keep
  their size.

### What to try
1. Unpack 0.9.3 **while MART 0.9.2 is still open**: the page should ask
   you to start MART again (the check added in 0.9.2). Close MART, start it.
2. Open ✎ on a renewal's strategy, and "+ To-do": the dropdowns match the
   fields around them.

## 0.9.2 — 06.11.2026 · fix: a new version unpacked while MART runs

### Fixed
- **"Something went wrong" on the client pages after unpacking 0.9.1.**
  The new files were unpacked while MART 0.9.0 was still running. MART
  re-reads its pages on every request but its code only at start, so the
  new pages met the old code (`not enough values to unpack` in the error
  log). Nothing was wrong with the data. Now MART notices it: if a newer
  version is unpacked over the one running, every page says **"Start MART
  again"** (close the MART window, start `MART.bat`) instead of failing.
  This works from this version on, so this time close MART before
  unpacking 0.9.2.

### What to try
1. Close MART, unpack 0.9.2, start it: the client pages work again.
2. Next time, unpack a new version while MART is still open: the page
   asks you to start MART again.

## 0.9.1 — 06.11.2026 · M3 day 1 · your strategy looks like yours

From Martin's notes on 0.9.0.

### Changed
- **Your strategy no longer looks like BM+'s.** Wherever it shows (the
  card, the renewal panel, the bundle's strategy mix, the side panel's dots
  and the card's left edge) it is drawn **neutral, with a dashed border and
  a ✎**: "✎ Remarketing". BM+'s strategies keep their colours.
- **One dropdown, no free text.** Your strategy is picked from a single list:
  Remarketing · Incumbent without Rate Guarantee · Incumbent with Rate
  Guarantee · Non-expiring · **Canceled** (in place of "Unknown / New
  Policy") · TBC. The first entry, "go by BM+", drops yours.

### What to try
1. Set a strategy on a renewal and check it reads as yours at a glance, on
   the card and in the bundle header.
2. Open the ✎ again: the list, with "Canceled".

## 0.9.0 — 05.11.2026 · M3 day 1 · actual state

### Added
- **Your strategy beside BM+'s.** The renewal panel has a new section,
  **Actual state** (written in MART), right after the BM+ stages. Set your
  own strategy with ✎ (the BM+ strategies are offered, any text works) and
  an optional reason. MART remembers what BM+ said at that moment, so it can
  tell you:
  - **≠ BM+: …** BM+ hasn't caught up yet (still blank or the old value);
  - **≠ BM+ changed to …** BM+ moved to something else since, have a look;
  - **✓ BM+ caught up** once an upload brings BM+ in line; nothing to clean
    up by hand.
  Leave it empty to go by BM+'s strategy again. Nothing turns into a to-do.
- **Your strategy wins on the cards.** The renewal card's colour and
  strategy pill, the bundle's strategy mix and the side panel's dots go by
  your strategy where you set one; the card shows "≠ BM+: …" underneath.
- **Completed.** Mark a renewal completed (with a date and an optional
  note) in its panel, or **a whole bundle** at once from the bundle header
  ("Completed: 1 of 3 · ✓ Mark the rest completed"). MART suggests it when
  BM+'s three stages are all done, but only you mark it. Cards show
  "✓ completed DD.MM.YYYY", and a bundle whose renewals are all completed
  gets a green count in the side panel. × takes it back.
- Every change is kept (**Changes** in the section): what you set, when,
  why, and what BM+ said then.

### What to try
1. Open a renewal whose strategy BM+ doesn't have yet (blank / TBC), set
   yours with ✎ and a reason. See "≠ BM+" on the panel and on its card.
2. Mark a finished renewal completed; then mark the rest of its bundle
   completed from the bundle header.
3. After your next upload, check whether a "≠ BM+" became "✓ BM+ caught up".

## 0.8.5 — 05.11.2026 · M2 day 5 · hardening

### Changed
- **Faster pages on a big book.** Comparing each renewal's overview with
  its client-ready version, and finding its newest entry, is now done once
  per text and remembered: the texts only change with an upload. On a
  synthetic book of 30 clients and 4,500 renewals: Home 1.2 s → 0.4 s, the
  Clients list 0.7 s → 0.05 s, a client page 43 → 18 ms. The first page
  after an upload still does the work once.

### Checked (no change needed)
- Home, the client pages, To-dos and Clients on a 1,200-renewal book
  (15 clients): every page well under half a second.

### What to try
Use M2 for a full day and answer the M2 review questions in
`BUILD_PLAN_M2.md`.

## 0.8.4 — 05.11.2026 · fix: the expected-update ✎ box

### Fixed
- **Changing an expected update**: the box behind ✎ opened to the right of
  the button, which sits at the right end of the line, so it ran off the
  window. It now opens leftwards from the button (bundle view and renewal
  panel).

## 0.8.3 — 05.11.2026 · M2 day 4 · Home "Today"

### Added
- **Today** on Home: one list of what needs you, each line a link to the
  bundle, renewal or to-do:
  - **expected updates passed** (not confirmed), oldest first;
  - **to-dos due or urgent**: overdue, due today, and every urgent one
    (with whom they're waiting on);
  - **updates expected this week**;
  - **new overview entries since yesterday**;
  - **gone quiet**: bundles red for the stale limit with no expected
    update ahead (a bundle already listed for its passed date isn't listed
    again); renewals still to come first.
  Each list shows 10 and says how many more there are.
- **Your clients**: a card per client below, those needing you first:
  renewals in the export, the next renewal date, and counts of the above.

### Changed
- Home's former "Your renewals" and "To-dos" cards: the to-dos are in
  Today, the numbers are in the smaller **Your data** card at the bottom.

### What to try
Start the day from Home: does Today show what you need first, in the
right order? What is missing or in the way? (QUESTIONS G1.)

## 0.8.2 — 04.11.2026 · M2 day 3 · broker deadlines on bundles

### Added (QUESTIONS M2b, E4, K4)
- **Expected update** on every bundle: the date you expect an update on
  its renewals, who promised it, an optional note. Set it with
  **+ Expected update** in the bundle (or the renewal panel), change it
  with ✎, close it with **✓ Update arrived**, or drop it with ×.
- **From BM+**: without a date of yours, a bundle takes the earliest
  "Expected date to receive the final renewal terms" of its renewals,
  marked "from BM+". If you set your own, BM+'s date shows beside it
  ("BM+ says …") and never moves yours. A BM+ date no later than one you
  already closed isn't offered again.
- **While the date is ahead**, the bundle's renewals don't go amber or red
  (the stale clock is paused); the side panel shows ⏳ and the date.
  **Once it has passed** it turns red (⏰) until you confirm it.
- **A hint, never an automatic close**: when an overview entry dated on or
  after the day you set the date arrives, the line asks "did the update
  arrive?"; you confirm it yourself.
- **Earlier deadlines** (arrived, dropped, changed) stay in the bundle's
  history. A deadline stays with its bundle, like its notes; an emptied
  bundle with an open deadline stays visible.
- Database schema 8 (`deadlines`).

### What to try
Open a bundle whose renewals have a BM+ expected-terms date: see it
prefilled. Set your own date from a broker mail, watch the stale badge
pause, then click ✓ Update arrived.

## 0.8.1 — 04.11.2026 · M2 day 2 · richer to-dos

### Added (QUESTIONS M2a)
- **Urgency**: urgent / normal / low, chosen when adding a to-do or in
  Edit. Urgent ones carry a red "urgent" mark and come first everywhere
  (then by due date); low ones go to the end.
- **Status** while open: open, in progress, or **waiting**. Waiting asks
  on whom (broker, insurer, client, colleague, someone else), their name
  and since when (today if left empty): "waiting on broker Broker A since
  04.11.2026". Leaving "waiting" forgets who it was.
- **Description**: a longer text under the title (Edit).
- **Subtasks**: a checklist inside a to-do. Add and remove them in Edit,
  tick them off on the to-do itself; "☑ 1/2" shows the progress.
- Database schema 7 (to-do fields + subtasks); existing to-dos keep
  everything and start as open, normal.

### What to try
Add an urgent to-do on a renewal; in Edit set it to Waiting on your
broker and add two subtasks; tick one. See it on the To-dos page and Home.

## 0.8.0 — 04.11.2026 · M2 day 1 · overview freshness

### Added
- **How quiet each renewal's overview is**, from the date written on its
  newest entry, across the full and the client-ready overview: **amber**
  ("getting old") after 7 days, **red** ("stale") after 14.
  - On each renewal card, under the overview: "stale · 26 days".
  - In the side panel, per bundle: its quietest renewal, e.g. "26 d"
    (a small badge, so it isn't confused with the round "not client-ready"
    dot).
  - In the renewal panel, next to "Renewal overview".
- **New entries**: overview entries dated within the last 7 days carry a
  green "new" mark.
- **Settings → Time limits** has the three new limits (getting old, stale,
  new); stale is never earlier than getting old.

### Fixed
- Saving Time limits no longer fails when the form leaves a limit out; a
  limit not sent keeps its stored value (an emptied field is still refused).

### What to try
Open a client: spot the quiet bundles by their badge in the side panel,
then a renewal's "new" entries. Change the limits in Settings and look
again. (In the demo data most overviews are months old, so most is red.)

## 0.7.8 — 04.11.2026 · the client notes button stands out

### Changed (Martin's note on 0.7.7)
- **"Client notes & to-dos" no longer looks like a filter.** It has the
  blue rail of everything written in MART, a notebook icon, and a second
  line "about <client> as a whole"; it turns blue on hover and while open.
  Its counts of notes and open to-dos stay on the right.

### What to try
Open a client: the client notes button stands out above the filters.

## 0.7.7 — 04.11.2026 · "Everything BM+ exported" by section

### Changed (Martin's note on 0.7.6)
- **"Everything BM+ exported" is bundled under BM+'s own sections**
  (Policy Information (Expiring Policy Period), LOC Information, Premium
  Information, Multinational Network Information, Broking Remuneration,
  Renewal Information), each one expandable, in the export's order, with
  its number of fields. The headers no longer repeat the section name, and
  dates show as DD.MM.YYYY like everywhere else.

### What to try
Open a renewal, then "Everything BM+ exported", then one of its sections.

## 0.7.6 — 04.11.2026 · lines of coverage as a list

### Changed (Martin's note on 0.7.5)
- **Lines of coverage are a bulleted list** in the renewal panel, one line
  per bullet (two columns on a wide window), on their own row under the
  Renewal facts. BM+ joins them with commas; MART splits on commas,
  semicolons and line breaks but never inside brackets, so "Inpatient
  (Hospital and Surgical)" stays one line. The cards' Coverage (product
  groups) uses the same splitting.

### What to try
Open a renewal with several lines of coverage: one per bullet.

## 0.7.5 — 04.11.2026 · renewal panel: Renewal and Strategy stacked

### Changed (Martin's note on 0.7.4)
- **Renewal and Strategy are stacked** in the renewal panel instead of side
  by side: the strategy section holds much more. The Renewal section's
  short facts (insurer, period, kick-off, benefit owner, …) sit **two per
  row**, one per row in a narrow window.

### Fixed
- The renewal panel's link to its bundle's notes still carried the removed
  "group" setting in its address (harmless, now gone).

### What to try
Open a renewal: Renewal on top in two columns, Strategy below it.

## 0.7.4 — 04.11.2026 · moving renewals in an edit mode

### Changed (Martin's note on 0.7.3)
- **The tick boxes and the move bar only appear while moving.** A bundle
  shows its renewals plainly, with a **Move renewals…** button beside its
  name. That opens the edit mode: a tick box on each card, ticked cards
  outlined, and a bar that stays at the top while you scroll, with
  "N selected", **Select all** / **None**, the bundle to move to, and
  **Done** to leave without moving. **Move** only works once something is
  ticked; after moving you land on the target bundle, out of edit mode.
- Moving a single renewal from its own panel is unchanged.

### What to try
Open a bundle (no tick boxes), click **Move renewals…**, tick two, move
them into a new bundle; click **Done** in another bundle to leave without
moving.

## 0.7.3 — 04.11.2026 · renewal cards: name on top, policy number

### Changed (Martin's note on 0.7.2)
- **The policy name has the whole width of its card**, on top, with the
  tick box and the "⋯" links beside it; it was cut off in its narrow column.
- **The first field is the Entity, with the policy number below it** when
  BM+ has one. The Overview sheet has no policy number: it comes from the
  Renewal Strategy sheet (else Proposals, else Savings), as BM+ writes it
  ("(multiple)" included). The other fields are unchanged.

### What to try
Open a bundle with long policy names: the names are whole, and the policy
number sits under the entity.

## 0.7.2 — 04.11.2026 · date filters, one BM+ link, drag and drop

### Changed (Martin's notes on 0.7.1)
- **No more "By date / By country" toggle**: the country and date filters
  replace it. Bundles are listed by renewal month, each with its flag,
  country and date.
- **From / Until are dates with a calendar** instead of month dropdowns.
  The calendar opens on the client's own renewal dates, and the date shows
  the way Windows is set up (DD.MM.YYYY on a Swiss or German setup).
- **One BM+ link for the renewal.** The links to the individual tasks all
  opened the same page in BM+ (the renewal's workspace), so the "⋯" menu
  now offers the policy and one **Renewal in BM+** link, and the stage strip
  no longer repeats "Task in BM+" under each stage.

### Added
- **Drag and drop on the Uploads page**: drop one or several tracker files
  on the upload card and they go straight to the preview, as if chosen and
  sent. Only `.xlsx` files are taken (anything else is left out, and said
  so if nothing is left); a file dropped beside the card is ignored instead
  of the browser opening it. Choosing files still works.

### What to try
Open a client: no toggle; set From / Until with the calendar. Open a
renewal's "⋯": Policy and Renewal in BM+. Drag two trackers from Explorer
onto the upload card.

## 0.7.1 — 04.11.2026 · lighter pages, strategy colours, flags, filters

### Changed (Martin's notes on 0.7.0)
- **"Insurer Not Found" gives way to the Provider.** BM+ writes it when an
  insurer isn't in its list; the Provider column beside it then names who
  it is, and MART shows that (expiring, upcoming and in the proposals).
  Without a Provider, BM+'s words stay. Takes effect with the next upload.
- **To-dos and notes take less space**: **+ To-do** and **+ Note** buttons
  open the fields in a small box (the cursor is already in it); the lists
  only show when there is something in them.
- **The move bar's footnote is an ⓘ** that shows the hint on hover or tap.
- **Naming a bundle**: a ✎ pencil right beside the bundle's name replaces
  the "Name this bundle" button.

### Added
- **Strategy colours**: every strategy has its own colour, on the strategy
  pills (renewal cards, bundle header, renewal panel), as the left edge of
  each renewal card, and as small squares in the side panel showing which
  strategies a bundle holds (round dots stay status). Remarketing purple,
  Incumbent without RG blue, Incumbent with RG green, Non-expiring teal,
  Unknown / New Policy rose, TBC amber, none grey. Dark mode has its own
  shades.
- **Country flags** beside every country name: the bundle list (and its
  country headings), the bundle and renewal titles, To-dos and Home. They
  are images shipped with MART (the flag-icons set, MIT): Windows shows flag
  emoji as two letters. BM+'s long names ("Korea, Republic Of") are known;
  a name MART doesn't know shows without a flag.
- **Filters in the bundle list**: a country dropdown and **From / Until**
  month dropdowns (the months the client's renewals renew in), on top of the
  text filter. "4 of 35 bundles · Clear filters" says when one is on. They
  stay while you click through the client's bundles.

### Fixed
- **A client opened somewhere down the bundle list.** MART selected the
  next bundle to renew and scrolled the list to it, so every bundle renewing
  earlier (still in progress) sat above, out of sight. Opening a client now
  starts at the top of the list, with the top bundle selected, and without
  the filters used earlier. Clicking a bundle keeps the list where it was,
  and only the list ever scrolls to the selected bundle, never the page.

### Development
- **CI uses less than half the runner time**: Windows only (3.12 and
  3.14; the Linux job is dropped, MART runs on Windows), one run per change
  (pull requests and merges into `main`, not every branch push a second
  time), and a newer push to a PR cancels the run it replaces. It can also
  be started by hand from the Actions tab.

### What to try
Open a bundle: spot the strategies by colour; add a to-do with **+ To-do**;
hover the ⓘ; rename the bundle with ✎. Pick a country, then From / Until
months, click a few bundles (the filters stay), go back to Clients and open
the client again (top of the list, no filters). After the next upload,
check a renewal that showed "Insurer Not Found".

## 0.7.0 — 04.11.2026 · M1 day 7 · hardening

### Fixed
- **The database no longer grows with every upload.** The rows an upload
  was read into were kept after the commit although nothing needs them;
  they are now removed at commit, old ones are cleared (schema 6), and MART
  compacts the file at start when a quarter of it is free space. On the
  demo data: 7.5 MB → 1.1 MB, backups 405 KB → 73 KB.
- **What you write during the day is backed up**: every hour while MART
  runs (only when something changed; "Backups to keep" in Settings sets how
  many), besides the start and every upload.
- **A backup just before a database upgrade**, so an upgrade can always be
  undone with `MART.bat restore`.
- Two backups in the same second (an upload's and the hourly one) were
  ordered by their content hash, so MART could take the older one for the
  newest and write a duplicate; they are now ordered by when they were
  written.
- **A refused action explains itself and leads back**: "That didn't work",
  the reason, "Nothing was changed.", and a button back to the page you were
  on (the menu stays). Unexpected errors still name the log file.

### Checked (no change needed)
- A single-client upload only ever touches that client (test since 0.2.0).
- Renewals without BM+ ids ("Transitioned") are recognised by client,
  country, entity, policy and date, and marked "no BM+ id".

### What to try
Use MART for a full day of real work, then go through the **M1 review**
list in `BUILD_PLAN_M1.md`.

## 0.6.0 — 04.11.2026 · M1 day 6 · move renewals between bundles, history

### Added
- **Move renewals into your own bundles** (Martin, 04.11.2026: a policy BM+
  split into several renewals, product groups handled by different brokers,
  entities with their own policies). Bundles are still country + renewal
  date by default. On a bundle, tick one or several renewals and **Move the
  selected renewals to** an existing custom bundle of the same country, or
  to **a new bundle…** you name. On a renewal panel, **Move to another
  bundle** does the same for that one renewal. A custom bundle's renewals
  may have different dates (its header shows the range); **Rename** it from
  its header; "their own bundle (country + date)" moves renewals back. A
  bundle never mixes countries. An emptied custom bundle is kept and offered
  again. Placements are yours and survive every upload.
- **Name any bundle**: Rename / "Name this bundle" on the bundle header. A
  default bundle then reads "Poland · 01.01.2027 · *your name*"; clear the
  name to go back to country + date.
- **A bundle whose renewals all moved away stays** while it carries notes or
  open to-dos (0 renewals, "No renewals left in this bundle…"), so nothing
  you wrote is lost; without any, it simply goes.
- Custom bundles work like the others: notes and to-dos on them, on the To-dos
  page as "bundle “name”", counted on the Clients list.
- **History** on the renewal panel (folded, after the overview): every
  upload records what it changed: workflow status, strategy, insurer,
  upcoming insurer, renewal / kick-off / local meeting / client approval
  dates, expected rate change, benefit owner, local analyst, a new overview
  entry, and for its BM+ stage tasks status, due date, assignee, delegate,
  completion and peer-review approval; plus first seen / no longer in the
  export / back in the export. Each is dated by the export it came from
  ("Export of 10.11.2026"): BM+ does not say when something changed.

### What to try
1. In a bundle, tick two renewals and move them to a new bundle with a name;
   from another renewal's panel, move it into that bundle; rename it; move
   one back. Write a note on the custom bundle.
2. Upload a newer Renewal Tracker and Task Tracker, then open a renewal's
   **History**. (History starts with this version: earlier uploads were not
   recorded.)

## 0.5.1 — 04.11.2026 · client notes; notes from earlier renewals

### Added
- **Client notes and to-dos** (Martin, 04.11.2026): a space for things about
  the client as a whole. "Client notes & to-dos" at the top of the
  explorer's side panel opens it in the middle; the Clients list shows its
  counts next to the client. Client to-dos are on the To-dos page and Home
  like the others.
- **Notes from earlier renewals of the policy** on a renewal panel
  (Martin: "see legacy notes from past renewals"): folded under "Notes from
  earlier renewals of this policy", read-only, each with its renewal date
  and a link to that renewal. Cycles are matched by BM+'s stable policy id,
  so the history grows with every renewal MART keeps.

### What to try
Write a client note; open a renewal whose policy MART had last year (from
next year on, as MART keeps the renewals) to see last year's notes.

## 0.5.0 — 04.11.2026 · M1 day 5 · notes and to-dos

### Added
- **To-dos and notes on a renewal**: a "Your to-dos and notes" section on
  the renewal panel, right under the BM+ stages, marked *written in MART*
  (blue rail) so it is never mistaken for BM+ data. Add a to-do (title,
  optional due date) or a note in one line; tick a to-do off; edit or
  delete either under "Edit". The newest three notes show, older ones fold
  away; done to-dos fold away too.
- **To-dos and notes on a bundle** (all its renewals, like one mail
  covering several policies): the same section on the bundle view. A
  renewal's panel also shows its bundle's open to-dos and latest notes,
  with a link to the bundle.
- **Counts on the renewal cards** in a bundle: ☐ open to-dos, ✎ notes.
- **To-dos page** (new menu entry): every open to-do, overdue first, then by
  due date, undated last, each with its client, country, date and renewal
  (or "whole bundle") linking to it; done ones of the last 30 days below
  (or all of them).
- **Home**: a To-dos card with the open count, overdue, due in the next 7
  days, and the next five.
- Uploads never touch any of it: notes and to-dos stay on a renewal that
  changes or leaves the export.

### Fixed
- MART could not show a page with a timestamp on **Python 3.10** (it uses
  `datetime.UTC`, which only exists from 3.11). MART.bat accepts 3.10, so
  this now works there too.

### What to try
Work a real client for a while: add to-dos with due dates on a renewal and
on a bundle, write notes from a call, tick to-dos off on the To-dos page,
and look at Home. Tell me what is missing or in the way (more fields? a
note type? reminders?).

## 0.4.6 — 04.11.2026 · no Proposals stage for fixed-terms strategies

### Changed
- **Proposals reads "not needed"** when the renewal's upcoming strategy is
  *Incumbent with Rate Guarantee* or *Non-expiring* (Martin, 04.11.2026:
  those strategies have no Proposals stage in BM+). Before, it read "not in
  BM+ yet" as if something were missing. Shown on the stage strip and as a
  faint dotted stage dot. If BM+ does create a Proposals task anyway, MART
  shows that task.

### Fixed
- **The left menu stays put** while a page scrolls (Martin, 04.11.2026):
  it is as tall as the window, with the MART version at its bottom, instead
  of growing with the page and scrolling away.

### What to try
Open a renewal with *Incumbent with Rate Guarantee*: the Proposals stage
says "not needed". Scroll down a long renewal: the menu on the left stays.

## 0.4.5 — 04.11.2026 · renewal tasks only; every period type

### Changed
- **Only renewal tasks (Task Category "Renewal Workspace") are loaded**
  (Martin, 04.11.2026). Implementation and contract tasks are not, even
  when they name a policy; ones loaded before are removed at the next Task
  Tracker commit. The preview's column is now **Not loaded**.
- **The export's period works for every Date Type BM+ offers**: Renewal
  Date, Task Start Date, Task Due Date and Task Complete Date. "Not
  Specified" means no period.

## 0.4.4 — 04.11.2026 · tasks attach only to renewals MART has

### Changed
- **A task that belongs to no renewal in MART is not loaded** (Martin,
  04.11.2026: the renewals are the backbone, and the history grows from the
  renewals MART keeps). The preview shows them per client in a **No renewal**
  column, and the commit message counts them. Tasks loaded by 0.4.0–0.4.3
  that belong to no renewal are removed at the next Task Tracker commit for
  that client. Implementation tasks (Appointment, Upload Local Documents, …)
  carry no policy id in BM+, so they never attach.
- **Upload the Renewal Tracker first.** Uploaded together, Renewal Trackers
  now open before Task Trackers; a Task Tracker preview says so when a
  Renewal Tracker is still waiting.

### Fixed
- **A Task Tracker for a shorter period no longer reports older tasks as
  "no longer in the export".** BM+ records the export's period on General
  Information ("Date Type: Renewal Date, From … To …"); a task MART has
  whose renewal date lies outside it is not news.

### What to try
Upload a Renewal Tracker and a Task Tracker covering several years in one
go. The Renewal Tracker opens first; the Task Tracker preview shows how many
tasks have no renewal in MART. Then upload a Task Tracker for this year
only: nothing should read "no longer in the export".

## 0.4.3 — 04.11.2026 · a links menu on every renewal

### Changed
- **BM+'s renewal link is no longer offered:** the link the cross-client
  Renewal Tracker writes for the renewal doesn't open in BM+ (Martin,
  04.11.2026; the policy link does). MART keeps it, but doesn't show it.
- The renewal panel's main button is now **Policy in BM+**.

### Added
- A **"⋯" menu** on every renewal card in the bundle view and next to the
  renewal panel's title, with all the renewal's links: the policy in BM+ and
  each stage task in BM+. One open at a time; an outside click or Esc closes
  it. More kinds of links can join the same menu later.

### What to try
In a bundle, click "⋯" on a renewal card and open the policy and a task.
Tell me which task links work, and what other links you want in the menu.

## 0.4.2 — 04.11.2026 · straight to the preview, links to BM+

### Changed
- **Uploading several files opens the first preview straight away** (Martin,
  04.11.2026). It says how many files came and which could not be read;
  after you commit or discard it, MART opens the next one, as before.

### Added
- **Open in BM+** on the renewal panel, to make changes in BM+ directly.
  It is the link BM+ itself writes in the cross-client Renewal Tracker;
  MART keeps it when a single-client export (which has only bare ids)
  comes later. Without it, the button opens one of the renewal's tasks in
  BM+ and says so. Also a link to the expiring **policy** in BM+, and
  **Task in BM+** on each stage card. Links open in a new tab; MART never
  builds a link itself, it only uses `https://` links from the exports.

### What to try
1. Upload several files at once: you land on the first preview.
2. Open a renewal, click **Open in BM+**: it should open that renewal.
   Click **Task in BM+** on a stage. Tell me if any link lands on the wrong
   page.

## 0.4.1 — 04.11.2026 · trackers without some sheets

### Fixed
- **A Renewal Tracker created without some sheets no longer wipes them.**
  BM+ lets you leave out Renewal Strategy, Proposals or Savings. Before, an
  export without one of them showed every renewal as "changed" and, on
  commit, deleted what MART had from that sheet. Now a sheet that isn't in
  the export is not news: MART keeps what it has, compares only the sheets
  that are there, and the preview says so. A sheet that *is* there is the
  truth: a renewal with no rows in it really has none any more.
- The renewal panel marks a section kept from an earlier export: "from the
  export of 28.10.2026".

### What to try
Upload a full Renewal Tracker, then a slim one (e.g. without Proposals):
the preview says which sheets it lacks and shows no changes, and the
renewal panel still has the proposals, marked with the date of the export
they came from.

## 0.4.0 — 04.11.2026 · M1 day 4 · tasks and the renewal panel

### Added
- **Task Tracker upload**, both flavours, through the same preview →
  commit as the Renewal Tracker (MART recognises the tracker). Tasks are
  linked to *this* renewal cycle: the Task Tracker's `Policy ID` is the
  Renewal Tracker's per-cycle id; failing that, the stable policy id + the
  review date. Last year's tasks of the same policy never show as this
  year's. Like renewals, tasks are never deleted, only marked "no longer in
  the export".
- **Renewal panel**: click a renewal's name. Always in the same order: the
  glance (strategy, workflow, coverage) → the **BM+ stages** (Renewal
  Strategy → Proposals → Update Policy: status, due date, assignee,
  delegate, completed by, **peer review** approved / pending N days /
  rejected N times, due date moved N times) → the renewal facts and the
  **Renewal Strategy** sheet (incl. last renewal, claims, client-specific
  questions) side by side → **Proposals** (first and final quote per
  insurer) → **Savings** → the **renewal overview** → other BM+ tasks
  (implementation etc.) → the renewal feed and every field BM+ exported,
  folded away.
- **Stage dots** on every renewal card in the bundle view (one per stage,
  coloured by state, red ring = past due).
- **Several files in one upload** (e.g. all your single-client exports):
  each gets its own preview; after you commit or discard one, MART opens the
  next. One bad file doesn't stop the others.
- **"Overview as of"** per client: the report date of the last export that
  carried the overview (in practice the single-client export). Shown in the
  explorer's side panel and as a column on Clients, highlighted when out of
  date.
- **Settings → Time limits**: "Overview data out of date after" (7 days by
  default, 1–90). Stored with your data, so it is in the backups.

### Fixed / learned from the real exports
- Real cross-client Renewal Trackers have **no overview** either (0.3.0's
  note said they did): the overview comes from single-client exports.
- The two Task Tracker flavours name people differently (e-mail vs name),
  carry different columns and write dates as timestamps or dates; MART
  compares only the workflow facts both carry, so loading one flavour after
  the other shows "unchanged", and it keeps what the other flavour had for
  columns the current one lacks.
- BM+ task dates are real timestamps: MART now only rounds a time that is
  exactly on the hour or half hour (BM+'s midnight-UTC artefact), so a task
  completed at 14:32 keeps its own date.
- Implementation tasks (Appointment, Upload Local Documents, …) have UUID
  ids; they were skipped as "no id" before.

### What to try
1. Upload, in one go, the cross-client Renewal Tracker, a single-client
   Renewal Tracker and both Task Trackers. Walk through the previews.
2. Open a client: check "Overview as of" in the side panel and the stage
   dots on the cards.
3. Open a renewal you know well and compare the panel with BM+: stages,
   peer review, strategy, proposals, savings. Tell me what is missing, wrong
   or in the wrong place.
4. Settings → Time limits: set the limit to 1 day and watch the overview
   date turn orange on Clients.

## 0.3.0 — 04.11.2026 · M1 day 3 · client explorer

### Added
- **Clients** page: your clients with renewals, bundles, next renewal date,
  and how many renewals have no client-ready overview, gaps, or no overview.
- **Client explorer**: the client's bundles (same country + renewal date) in
  a side panel, grouped **by date** (month) or **by country**, with a filter
  (country, policy, entity, insurer). The selected bundle in the middle:
  renewal date and countdown, entities, insurers, the strategy and BM+
  workflow mix, and every renewal with coverage, insurer (→ upcoming
  insurer), strategy, workflow status and overview state. Opens on the next
  bundle to renew; the side panel keeps its scroll position.
- **Renewal overview** per renewal, like MAPT's renewals page: dated entries,
  newest first, with every line missing from the client-ready version
  marked, entries BM+ marked "(not client ready)" flagged, and older entries
  folded away.
- "Show / hide renewals no longer in the export".

### Fixed
- **Real cross-client exports carry the overview**: MART now takes a text
  stream from any export that fills it (the 0.2.0 rule, built on the demo
  files, would have ignored the overview of every cross-client upload).
- Overview entries only start at a line start: a date with a colon inside a
  sentence no longer splits an entry.
- Filters hide items reliably (`hidden` wins over layout rules).

### What to try
Open **Clients**, then one of your clients. Walk the bundles by date and by
country, filter for a country or an insurer, open a renewal's overview and
check the "not client-ready" marks against BM+.

## 0.2.0 — 04.11.2026 · M1 day 2 · Renewal Tracker upload

### Added
- **Uploads page**: upload a Renewal Tracker export (cross-client or
  single-client), see a **preview** per client (new / changed / unchanged /
  not in the file), then **commit** or **discard**. The .xlsx itself is not
  kept, only what MART reads from it.
- **My clients**: tick your clients in the preview; MART remembers, and
  ignores the others on every later upload. A single-client export is
  ticked automatically. Filter box and "All visible / None" for long lists.
- Renewals are **never deleted**: one missing from a later export is kept
  and marked "no longer in the export", and comes back if it reappears.
- All four data sheets are kept: Renewal Overview, Renewal Strategy,
  Proposals, Savings.
- Safety: notice for an identical file, a block (with override) for an
  export older than the one loaded, a backup after every commit, a plain
  reason for a wrong file.
- Home shows what is loaded.

### Fixed / learned from the real exports
- Same-named renewals without BM+ ids ("Transitioned") can be different
  policies: distinct rows are never merged, only exact duplicates.
- Dates are rounded to the nearest midnight (BM+ exports midnight UTC in
  local time; the evening before for the Americas).
- The two export flavours spell the same data differently (URL vs bare ids,
  a Client Name column, header spelling): compared by content, not spelling.
- The cross-client export carries no overview text (only the Renewal Feed):
  neither flavour can blank a text stream that only the other carries.
- Upload times shown in local time, not UTC.

### What to try
Upload the real cross-client Renewal Tracker, tick your clients, commit;
upload it again (all "unchanged"); upload a single-client export.

## 0.1.1 — 04.11.2026 · launcher and zip builder

### Fixed
- `MART.bat` finds Python wherever it is installed (py launcher, per-user
  and machine-wide folders, PATH) and skips the Microsoft Store placeholder.
  MART runs on Python 3.12 and 3.14.

### Added
- `make-zip.bat` (on the PC with the repo): pulls the latest version,
  builds the zip, tests it, shows it in Explorer.
- `BUILD-INFO.txt` in the zip: version, commit, build date.

## 0.1.0 — 03.11.2026 · M1 day 1 · skeleton

### Added
- `MART.bat`: start-up check, database, backup on start, server on
  127.0.0.1, browser opens.
- First-start **setup** and **Settings**: data folder (never a synced
  folder), backup folder, backups to keep, port.
- Backups: consistent snapshot, gzipped, deduplicated, newest N kept;
  `MART.bat backup` / `restore`.
- Runs with nothing installed: standard library, preinstalled `openpyxl`,
  Jinja2 + MarkupSafe shipped in `vendor/`.
