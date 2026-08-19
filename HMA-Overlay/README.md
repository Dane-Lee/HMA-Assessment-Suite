# HMA Overlay

> Working name — a rename is on the list.

Admin-only tool that joins an individual's **Human Movement Assessment** against the
**physical demands of their job** (FTA/PDA) and the **task steps of their station** (JSA),
and reports which parts of that job put *that specific person* at risk, and why.

One file. Double-click `HMA Overlay.html` to open it in Edge or Chrome. No install, no
build step, no server, no internet.

> **Admin-facing only.** Nothing in this tool is shown to the employee. See
> [Scope and guardrails](#scope-and-guardrails) — this is intervention targeting, not a
> fitness-for-duty determination.

---

## The job library is part of the program

**11 jobs and 11 stations are built into the file.** They are not imported, not stored in
browser storage, and not lost when browser data is cleared. Open the file on any machine, in
any browser, and the library is simply there.

The jobs were parsed from the ATI FTA documents in
`Ergo Assessment Helper/source-data/FTA-examples-Somerset-editable/` — all 17 movements with
their frequency, task text, and notes, plus the material-handling chart. 170 real demands and
79 handling rows.

Edit anything on the **Jobs** and **Stations** screens, then click **Save into program**. That
downloads a fresh `HMA Overlay.html` with your changes baked into it — replace your copy and
the library travels with the file from then on, by USB, email, or shared drive.

> Local edits live in browser storage only until you Save into program. The Data screen tells
> you when you have unsaved edits, and can discard them or restore removed built-ins.

**A caveat on the seeded stations:** they were scaffolded from the FTA task text, *not* from
real JSAs. No hazard assessment was performed, so hazard types are empty. Treat the step names
as a starting point — edit them to match your actual JSA and add the hazard types. Steps
carrying **Strain** or **Awkward Positioning** pull the site's coaching language into reports.

**A caveat on the seeded jobs:** these are the **Somerset, KY** FTAs, labelled as such. They are
a working library and a set of realistic templates to copy — not your Navarre job list. The
Navarre `.doc` drafts are legacy binary files that yield nothing to text extraction, so those
jobs need entering by hand (**Jobs → New job**, or **Copy** an FTA and edit it).

## Getting employee records in

The only thing brought in per-use. In the HMA Tracker, click **→ Send to Overlay** on the
Records tab — that copies every record to your clipboard. Here, paste into the box on the
**Data** screen and click **Receive records**.

Records already present are updated in place, never duplicated, so re-sending is always safe.

> **Why the clipboard.** The two apps run on different origins — the Tracker is served by
> Vite/Vercel, this is a local file — and browsers block a direct handoff between them. If the
> two ever do share an origin (for example, if this file is dropped into the Tracker's Vite
> project), this app notices the Tracker's records automatically and offers a one-click pull
> with no copy/paste at all. That path is already built; it just needs the two served together.

---

## Using it

1. **Data** → paste the records from the Tracker.
2. **Employees** → pick a person.
3. Assign the **job** and, optionally, the **station**.
4. Read the ranked findings. **Print / Save PDF** for the file.
5. Optionally, **Link task steps** to correct the app's keyword guesses.

### Task-step linking

The app seeds the demand → task-step mapping two ways: keyword matching against the station's
task names, and checking whether the job's own task text names the step directly. Suggestions
show in orange; click to confirm or clear. Once you touch a row it becomes yours and
suggestions stop overriding it.

The mapping is stored **per job + station pair, not per employee** — do it once and every
employee on that station inherits it. It is baked in by **Save into program**.

---

## How the ranking works

Full detail, including the complete 17-demand crosswalk, is on the **Method** screen in the
app. In brief:

**Deficit** (per pattern, from the HMA) — pain `4`, score 0 `3`, 1 `2`, 2 `1`, 3 `0`.
A pattern's deficit is its **worst side**, because the job loads the worst side too.

> The Tracker's 15-point total uses `min(R,L)` summed across five patterns. That's the right
> number for triage, but it hides *which side* is limited — which is the whole question here.
> A 3/1 asymmetry and a 2/2 both contribute 1 to the total and mean very different things on
> a station that loads one side every cycle.

**Demand** (per demand, from the FTA) — Never `0` (excluded), Occasional `1`, Frequent `2`,
Constant `3`.

**Score** = `demand × coupling × deficit`, then escalated by:

| Modifier | Effect |
|---|---|
| Pain on the pattern | floor of 9 where exposure is real, 5 where it's incidental |
| Side-to-side asymmetry ≥ 1 | +1, names the weaker side; flags if the job calls the demand one-sided |
| Hypermobility + Frequent/Constant | +1 — risk mode inverts to control at end range under sustained load |
| OA flagged + lower-extremity pattern | +2 |
| Material handling ≥ 35 lb + trunk/lunge at Frequent+ | +1 |
| Sustained/static language in the job notes + deficit ≥ 2 | +0.5 |

Pain escalates **proportionally to exposure** (`frequency weight × coupling`). A flat floor made
*"Sitting — breaks and lunch"* rank as Priority alongside genuine findings on the same painful
pattern; scaling it keeps painful patterns escalated without letting incidental demands
outrank real ones.

**Bands** — Priority ≥ 8 · Elevated 4–7 · Monitor < 4. Monitor-band items collapse into a
compact list (usually a secondary-coupling echo of a finding already shown); nothing is discarded.

### The known gap

The HMA scores five patterns — Forward Lunge, Single Leg Dip, Shoulder Reach, Trunk Rotation,
Cervical Rotation. **None of them measure the hand or wrist.** So Simple Grasp, Firm Grasp,
Fine Manipulation, and Pinching have no capability data to join against.

When a job rates those Frequent or Constant, they're reported in a separate **"not measured by
HMA"** block rather than folded into the ranking — so the absence of a finding is never
mistaken for the absence of risk. The WISHA Hand & Wrist zone (Ergo Assessment Helper) and the
Strain Index (Task Analysis Scores) cover that ground on the job side.

---

## Scope and guardrails

This tool produces a document pairing a **named individual's physical limitations** with a
**specific job**. That is ADA-sensitive by nature, and the design reflects it:

- It is a **prioritization aid** — which correctives to weight, which coaching to reinforce,
  which station change to pursue first.
- It is **not** a fitness-for-duty determination, a work restriction, a placement or hiring
  input, or a medical opinion.
- Every output is framed as action on the *job and the program*, never as a judgment about
  the person.
- **Admin-facing only.** No employee-facing view exists and none should be added here — the
  employee-facing half of this ecosystem is HMA-Cadence, which deliberately receives only a
  finished exercise plan and never demand-match findings.
- A guardrail banner appears on screen and on every printed report.

### Data handling

- Runs **entirely in the browser**. No network calls, no cloud storage, no third-party
  services, and **no PHI to any AI platform**.
- The job library lives in the file. Employee records live in `localStorage` under
  `hmaOverlay.v1`, tied to the browser you use — pick Edge or Chrome and stick with it.
- The FTA source documents are read once at build time by `tools/parse-ftas.py` and never
  modified. They describe jobs, not people.
- Printed reports name an employee and describe their limitations. Handle them per ATI
  document procedures.

---

## Rebuilding the library from the FTAs

Only needed if the source FTA documents change. The app's **Save into program** button does the
same bake from the browser.

```bash
python tools/parse-ftas.py      # FTA .docx  -> tools/seed-library.json
python tools/make-stations.py   # scaffolds a station per job from the FTA task text
python tools/inject-seed.py     # bakes it into "HMA Overlay.html"
```

Two things the parser handles that are worth knowing about, because both were silently
corrupting the data:

- **`CERVICAL SPINEMOTION`** — the ATI template is missing a space in the detail rows of 8 of
  the 11 FTAs. Matching on the printed label dropped cervical demand entirely from those jobs,
  which would have made neck findings impossible on most of the library. Labels are now matched
  on letters only.
- **Grid vs. detail conflicts** — each FTA states frequency twice, and in 3 jobs the two
  disagree. Press Operator's summary grid says squatting *Never* while its detail row documents
  *"placing axle on the lowest rack, partial/sustained."* The parser keeps the **higher** demand
  (under-reporting is the wrong failure direction for a risk tool) and flags the conflict on
  that job's edit screen so the source document can be corrected.

## Testing

```bash
node test/engine-test.js
```

No dependencies — it pulls the `<script>` block straight out of `HMA Overlay.html`, stubs a
minimal DOM, and runs the real engine, so the test can't drift from the app. Covers the baked
library, seed/local-edit merging, record detection, the deficit model, every escalation
modifier, task-step linking, all nine screens, and a save-into-program round trip that re-parses
the regenerated file.

`demo-data/hma-records-DEMO.json` holds three **entirely fictional** employees for trying the
tool without real records — paste its contents into the Receive box.

| Employee | Demonstrates |
|---|---|
| Marcus Bell (7/15) | Pain override, side asymmetry, OA, and heavy handling stacking on one pattern |
| Dana Whitfield (12/15) | A clean scorer on a demanding job — the tool stays quiet rather than manufacturing findings |
| Ray Ortiz (7/15) | Broad but mild deficits: same total as Marcus, very different shape |

---

## Where it sits

```
HMA Grand Master/
├── HMA-Tracker-app/    assess movement → build corrective plan   (EIS authoring)
├── HMA-Cadence/        employee-facing compliance PWA            (employee)
└── HMA-Overlay/        person × job demand match                 (admin)  ← this
```

The Tracker gained one button — **→ Send to Overlay**, next to Export on the Records tab. It
reuses the Tracker's existing clipboard helper; nothing else in that app changed. It is a local
edit: rebuild/redeploy the Tracker if you want it on the Vercel copy too.

## Not built yet

- **WISHA overlay** — the 27 risk factors have a clean 4-zone → pattern mapping but aren't read
  yet. Would let a Hazard-level finding escalate the matching pattern directly.
- **TuMeke scores** — REBA / NIOSH LI / Strain Index as an intensity multiplier on the demand side.
- **Job-first roster view** — pick a station, see which assigned employees are mismatched.
- **Navarre jobs** — the built-in library is Somerset; Navarre needs entering by hand.
- **Real JSAs** — the seeded stations are FTA-derived scaffolds with no hazard types.
- **Crosswalk editing in the UI** — the coupling table is still code-level (`CROSSWALK`).
- **A better name.**
