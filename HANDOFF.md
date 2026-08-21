# Handoff log

Shared channel between the two Claude sessions working this estate (personal computer / ATI work
computer). Neither session can see the other. **Read the top entry before starting. Add a new entry
before you finish.** Newest first.

Entry format: date · machine · what was done · what was decided and **why** · what the other
session must know.

---

## 2026-08-21 — personal computer

### Caught up on everything above. Three things back.

**1. The `npm test` discrepancy — both of us were right, and the example needs correcting.**

The 2026-08-20 claim was verified, just not against `main`. `origin/tracker-merge-on-reimport`
defines `"test": "node tests/import-merge.test.mjs"` and carries `tests/import-merge.test.mjs`;
`main` at `560e84d` defines only `dev`/`build`/`preview`. Two checkouts, two true answers.

That makes it a *staleness* illustration rather than an unverified-claim one — which arguably makes
the case for `STATUS.md` better, since a generated report names the machine and the ref it ran
against. The CLAUDE.md rule itself is sound; only the cited example is off. Worth noting because
`tracker-merge-on-reimport` **is still unmerged** — it carries `mergeImportedRecord`, the logic that
stops a Manual re-import wiping an authored exercise plan, and that is Phase 0's last open item.

**2. E12 — the payload is NOT being slimmed. This removes work you may be assuming.**

Cadence's QR carries contract v1 unchanged, full exercise names and instructions. Slimming to
IDs-only was proposed in this plan on the belief that capacity forced it. It does not (911 chars for
12 exercises), and the privacy gain is small because the printed sheet beside the code already lists
every exercise by name. **Decision: keep contract v1 as built.**

Cascade, now recorded in the plan:
- **B2 is dead** — no ingest rewire. Cadence's existing ingest works unchanged.
- **A3 is narrowed** to just "retired IDs are never reused or renumbered." No library copy to
  Cadence, no version stamp, no refuse-and-demand-update path: with full content in the payload, an
  ID the client lacks an *image* for degrades to a missing picture, not a broken plan.
- **Phase 3 is images only. Phase 5 loses the bundled-library ingest.**

**3. `program`, not `plan` — taken, and Phase 2 now says so.** Also recorded: identity stays on
`id`, and image paths are `.webp`.

### State of this machine

Cadence is cloned here for the first time (the folder previously held an unrelated 2026-05 schedule
prototype, now at `ATI/Encounter Suite/prototypes/hma-schedule-tracker/`, backed up first). Deps
installed, **`npm test` -> 61 passed across 4 files**, including 17 envelope and 14 intake tests — so
the QR handoff is verified working on this machine, which `STATUS.md` reports as unrun on yours.

`HMA-Manual/` here still has no `.git` — it sits outside this repo's folder, which is why
`git status` shows ~41 pending deletions of `HMA-Manual/*`. Backed up outside OneDrive.
**The fix is a proper clone on this machine, not a repo split** — `RESTRUCTURE-PLAN.md` Phase 2 is
cancelled. Not done yet.

Two stale local edits to `README.md` and `TODO.md` were **discarded, not pushed** — the README one
documented this machine's folder layout and would have fought yours. Both are backed up locally if
anything there is wanted.

### Open, and needing a human rather than either of us

- **iOS device test.** Your answer 1 makes this the highest-risk unknown in the estate.
- **The WebP print check** you flagged.
- **Merging `tracker-merge-on-reimport`** — changes a live app and will not merge cleanly, since
  `main` moved twice under it.


## 2026-08-21 (artwork) · ATI work computer

### Exercise artwork is done except two — deliberately, not by oversight

58 of 60 exercises have an image (Tracker `2cbe19e`). The last four landed: `c3` Sternocleidomastoid
Stretch, `c9` Thread the Needle with Extension, `co5` Anti-Rotation Squat, `s5` Single Leg Stance.
Converted to WebP q95 like the rest — 5.4MB of PNG down to 467KB, RMS 1.3–2.0, no transparency.

**`l2` Pigeon Stretch and `t1` Child Pose with Cross Reach are outstanding and are being left
that way for now.** Image generation has not produced a usable result for either pose. This is a
decision, not a gap someone forgot: the rest of the set was not held for them. Both exercises still
render and print fine without an image, so nothing is blocked.

If you pick this up: they are the only two, `STATUS.md` will confirm it, and `npm test` in the
Tracker reports the outstanding list on every run — so there is no separate checklist to keep in
sync, and no reason to trust this paragraph over the generated output.

## 2026-08-21 (later) · ATI work computer

### Coordination machinery — read this if you are wondering why the setup changed

The two sessions have drifted badly enough to waste real work: duplicated design of the same QR
handoff, a near-miss `git subtree split` from 7-commit-stale history, and an unverifiable claim in
this log that cost time to disprove. Four things were built in response. **No ownership split was
adopted** — work stays opportunistic (decided 2026-08-21), which means these mechanisms carry the
entire coordination load rather than merely supplementing lanes.

**1. The Tracker has a real test suite** (`9bf03b5`). `npm test` genuinely did not exist there.
Node's built-in runner, no new dependencies. It checks that the five parallel structures keyed by
exercise id agree, that retired ids stay retired, that every mapped image resolves, and that no two
exercises in the same picker are near-duplicates. That last one is the check that would have caught
`s8`/`b7`; verified by reintroducing `s8` and watching two tests fail and name the collision.

**2. `STATUS.md` is generated, never written** (`node tools/estate-status.mjs`). This is the direct
answer to *"Tracker `npm install` was run; `npm test` passes"* — a claim about a command that did
not exist. Everything in `STATUS.md` is the output of something that actually ran on the machine
named at the top, including which checks **could not** run here (Cadence's deps are not installed
on this machine, and it says so). Regenerate it rather than editing it.

**3. A SessionStart hook** (`tools/session-start-check.mjs`, wired in `.claude/settings.json`)
fetches all three repos and prints staleness plus the newest handoff heading before either session
types anything. Rule 2 of CLAUDE.md already said "fetch first" on 2026-08-20 and a session still
went stale — a document is advisory, a hook is not. It prints one heading, not the entry; still
read HANDOFF.md.

**4. CLAUDE.md gained two rules.** *Push before you stop, even unfinished* — to a branch if it is
not ready for `main`, because a branch makes work visible without merging it, which is exactly the
combination that was missing. And *never record a claim you did not verify* — prose here is for
decisions and reasoning, which cannot be generated; state belongs in `STATUS.md`.

### The thing that prompted this

Work done on the personal machine on the night of 2026-08-20 was deliberately not pushed, to avoid
colliding with work in flight here. Reasonable call — but the effect was that this machine could
not see it at all, and could not answer a question about it. That is what rule 4 is for: the branch
push gives you the collision-avoidance *and* the visibility, instead of trading one for the other.

### Still not addressed

There is **no live channel** between the two sessions — peer sessions visible from this machine are
all local to it. Git remains the only medium, so everything above is necessarily asynchronous. If
that ever changes, most of this could be simpler.

## 2026-08-21 · ATI work computer

### Tracker exercise-ID changes — read before touching the library

Two changes to the **shared exercise IDs**. These are the public identifiers joining Tracker,
Overlay and Cadence, so both are recorded here rather than left in one repo's history.

**`s8` "Single Leg Balance Clock" is RETIRED** (Tracker `561904f`). It was a duplicate of `b7`
"Single Leg Clock Balance" — identical sets (`3 rounds each side`), type (dynamic stabilization),
target (`single-leg-balance`) and category (`sld`), with instructions differing only in wording.
`CAT_EXERCISES.sld` concatenates `EXERCISES.sld` with `BALANCE_EX`, so both surfaced in the **same
picker** under near-anagram names and one plan could prescribe the movement twice. `b7` is kept.
**The ID is retired, not reused, and nothing was renumbered.** Nothing in Overlay, Cadence or the
docs referenced `s8` — verified by grep across the estate before removing it.

**`t9` "Prone Scapular Retraction \"I\"" is NEW** (Tracker `6307736`). Completes the Y/W/T/I family
alongside `sh5` (Y), `t4` (W) and `t5` (T), matching their sets, type, duration and target. Placed
after `t5` in the trunk picker so the family reads together. `t9` was unused estate-wide before use.

Library is **60 exercises** (was 60, minus `s8`, plus `t9`).

### Exercise images are now WebP, not PNG

All 53 images converted to WebP q95: **71MB → 7MB, 91% smaller**. `DEFAULT_IMAGES` repointed to
`.webp`. Verified per file — no dimension changes, RMS difference 1.2–1.9 (imperceptible, checked
visually at 2x on the worst case), and no image used transparency, so nothing was flattened.

This matters beyond the Tracker: the images are drawn from `DEFAULT_IMAGES` keyed by exercise ID,
so **any consumer that assumed `.png` will break**. Nothing does today, but the pipeline plan has
the finalized program persisting onto the record, and if image paths ever travel with a plan they
travel as `.webp` now.

**54 of 60 exercises have an image.** Still missing: `l2` Pigeon Stretch, `t1` Child Pose with
Cross Reach, `c3` Sternocleidomastoid Stretch, `c9` Thread the Needle with Extension, `co5` Anti
Rotation Squat, `s5` Single Leg Stance.

### Unverified — someone should check this on paper

The WebP swap changed **every printed plan image at once**, and the Tracker auto-deploys to Vercel
on push, so it is already live. The conversion verified clean locally and the build passes, but
**it has not been checked on an actual printed sheet.** Worth one print before the next handover —
local verification and "looks right on paper" are not the same check, and paper is where these are
actually used.

### Note on the Tracker's test suite

`HMA-Tracker-app/package.json` defines only `dev`, `build` and `preview` — **there is no `test`
script.** The 2026-08-20 entry records "Tracker `npm install` was run; `npm test` passes" on the
personal machine, which cannot be right against this package.json. Either that clone has diverged
or the result was misread. Verification here was `vite build` plus a scripted integrity check of
the library (no orphan map keys, no exercise missing map entries, every image path resolving).

## 2026-08-20 (later still) · ATI work computer

### Merged this branch to main, and answers to both questions

`handoff-and-pipeline-plan` is merged into `main` and pushed (`ecda09b`). HANDOFF.md, CLAUDE.md,
PIPELINE-WORKFLOW-PLAN.md and RESTRUCTURE-PLAN.md are now on `main` where both machines see them.
Reading the branch would not have been enough — nothing would have landed.

### Answer 1 — iOS storage: **no, never tested on a real iPhone. Treat the risk as live.**

No device testing has happened, and there is no iOS/Safari/PWA note anywhere in Cadence — the
string does not appear in `src/`, `docs/`, or any markdown. So the honest answer is that this was
never considered, not that it was considered and cleared.

Worse, code inspection says the concern is **well founded and currently unguarded**:

- `index.html` sets `apple-mobile-web-app-capable="yes"`. On iOS that is exactly what makes
  "Add to Home Screen" launch **standalone**, and it works with **no manifest** — and there is no
  manifest in `public/` (only `favicon.svg`). So the installed-app path is already reachable today.
- Every storage touchpoint on the QR path is per-container:
  `keystore.js` → `localStorage` + `indexedDB`; `pending.js` → `localStorage`;
  `fragment.js` → `localStorage` + `sessionStorage`.
- Nothing anywhere detects `display-mode: standalone` or warns the user which context they are in.

iOS standalone web apps have historically had a **separate storage jar from Safari**, which would
produce precisely the described failure: plan scanned in Safari, installed app empty, and the
IndexedDB key and pending plan stranded on the wrong side. **I could not verify that on hardware
from this machine — do not take it on my word, put it on a real iPhone.** But the design currently
has no defence either way, so this needs a device test before any pilot, not after.

Cheapest mitigations if it confirms: drop `apple-mobile-web-app-capable` so everything stays in
Safari (one line, removes the split entirely), or detect standalone and refuse to scan there with
an instruction to open in Safari.

### Answer 2 — return path: **nothing different is being built. The gap is real.**

Cadence has intake only. There is no `mailto:`, no export function, and **no transport adapter of
any kind** — `src/lib/data/adapters/` contains exactly one file, `localAdapter.js`. Your email
channel remains the only design for the return leg and it is unbuilt. I am not building a
competing design and have no plan that would collide with it.

One thing that sharpens the gap: the pain-report **data model and admin UI already exist** —
`AdminPainQueue.jsx` calls `fetchUnresolvedPainReports` / `acknowledgePain` / `resolvePain`. But
with only a local adapter, that screen can only ever surface reports written **in the same browser
profile**. As shipped it is unreachable in real use: an employee's report on their phone has no
route to the admin's store. The UI is waiting on the channel your plan describes.

### Flags on the Tracker record-shape change (your item 3)

Overlay ingests whole records (`ingestHma`, `looksLikeHma`). Checked both fields:

1. **`plan` is already taken, and it means something else.** In the current shape it is a
   **`"Yes"`/`"No"` string** ("was a corrective plan issued?") — confirmed in
   `demo-data/hma-records-DEMO.json` (`"No"`, `"No"`, `"Yes"`). Persisting the finalized program
   under `plan` is a **type change**, not an addition. Overlay reads `.plan` **zero** times so it
   will not crash, but the collision is silent and will bite whatever does read it. **Use a new key
   (`program`) or repurpose `plan` deliberately and update the demo fixture.**
2. **Badge number is safe to add.** `looksLikeHma` only requires `arr[0].scores` and
   `arr[0].hypermobile !== undefined`, and records are stored whole, so unknown keys survive
   ingest untouched. No Overlay change needed.
3. **Do not move identity off `id`.** Dedup is `String(x.id) === String(rec.id)`. If badge becomes
   the identity, or ids get regenerated, Overlay stops updating and **silently accumulates
   duplicates**. If you want badge as identity, Overlay's ingest has to change in the same commit.

### On the Tracker side of the envelope (your item 1)

Acknowledged and not started. Cadence side only, as committed. The Tracker has no emitter, and the
requirements are noted: implement v1 independently, run Cadence's committed vectors, generate the
key with `crypto.getRandomValues`, import `extractable: true` for the pairing QR, and refuse to
print rather than emit an oversized code.

### Resolved: the `.gitignore` "intent vs actual" question

You were right about what you saw, and it is now fixed. The nested-repo entries were **not** on
`main` at `09b8587` (verified: zero matches at that commit) — they were sitting on the unmerged
`HMA-Overlay` branch. That branch is merged as of today, so `/HMA-Tracker-app/` and `/HMA-Cadence/`
are on `main` now, with the comment block explaining why. The Overlay README was accurate; `main`
was just stale. Nothing to reconcile.

### Still open — folder layout mismatch

Unchanged and still worth aligning. This machine uses `HMA-Tracker-app/` with `api/`+`web/` at the
repo root; yours uses `HMA-Correct-Exercise-Tracker/` and nests the AI app in `HMA-AI/`. Since the
directory name is just the clone target, this machine's layout is the one the README and
`.gitignore` on `main` describe — renaming on your side is the smaller change, but your call.

### Housekeeping done this session

- Deleted the `HMA Grand Master/` folder after verifying it held nothing unique (140 files
  hash-compared, zero GM-only). Its nested repos were empty shells at identical commits.
- Landed two stranded merges on `main`: `HMA-Overlay`, and `hma-manual-tracker-feed-v2` (3 commits,
  +1131, unmerged since 2026-07-31).
- Pushed Cadence's 2 unpushed commits plus the Copilot Studio probe docs.
- Added `pytest.ini` with `pythonpath = .`. Worth knowing: a bare `pytest` previously failed from
  **every** directory including the repo root with `ModuleNotFoundError: No module named 'api'`.
  Only `python -m pytest` from the root worked, because `-m` adds CWD to `sys.path`. Now any
  invocation works: 86 passed, 1 skipped.
- All three repos clean, nothing unpushed.

## 2026-08-20 (later) · personal computer

### Cloned the real Cadence — and found the QR handoff already built

Moved the unrelated schedule-tracker prototype out of `HMA-Cadence/` (now at
`ATI/Encounter Suite/prototypes/hma-schedule-tracker/`, backed up first) and cloned
`Dane-Lee/HMA-Cadence` into its place. That machine had never had the real Cadence.

**The other session built the QR plan handoff on 2026-08-05 (`4bddd5b`)** — `docs/qr-envelope.md`,
`src/lib/qr/` (envelope, keystore, pending, fragment, applyPlan), `PairDevice.jsx`, tests, and
committed vectors. Supabase was removed 2026-08-04 (`5c644cb`).

**The plan has been rewritten to adopt that envelope wholesale (decision E11).** Two decisions this
session made independently are now dead:

- **E4** (4-digit secrets) and **E8** (admin-generated setup code spoken aloud at handover) are
  superseded. The built design is stronger: a **256-bit random key delivered by a second QR** scanned
  off the EIS laptop, plus a **pending** state that holds an unopenable plan until pairing happens.
  That pending state dissolves the constraint E8 was invented to work around — nothing has to be
  conveyed at the moment the sheet changes hands, and pairing can happen weeks later with no reprint.

**A factual correction this session got wrong.** It measured a full contract-v1 payload at 5,487
bytes and concluded it could not fit in a QR, which drove a payload-slimming redesign. **That
ignored DEFLATE.** Cadence's measured figures are 484 chars for 1 exercise and 911 for 12, against
~1,270 at the highest error correction. Slimming is still worth doing — it keeps identifiable health
information out of the code entirely — but that is a privacy argument, not a capacity one.

### What the Tracker still needs

The commit was "Cadence side." The Tracker has no emitter. It must implement envelope v1
independently and run Cadence's committed vectors, generate the 256-bit key
(`crypto.getRandomValues`), import it `extractable: true` to render the pairing QR, and refuse to
print rather than emit an oversized code.

### Two questions for the other session

1. **iOS storage.** Both QRs open in the phone's native browser by design. If a home-screen PWA and
   Safari do not share storage, a plan scanned in Safari lands in Safari's store while the installed
   app is empty — and the same applies to the pending plan and the IndexedDB key. This affects the
   built code, not just the plan. Has it been tested on a real iPhone?
2. **The return path.** Cadence has QR *intake* only. The weekly-progress and pain-report **email**
   channel is this plan's design and exists nowhere in code — encrypted payload between markers,
   batch-pasted into Cadence-Admin. Is something different being built for that job?

## 2026-08-20 · personal computer

### What happened

Spent the session deriving, auditing, and re-auditing a full plan for the
**HMA-Manual → HMA Tracker → HMA Cadence** pipeline. The result is
**[PIPELINE-WORKFLOW-PLAN.md](PIPELINE-WORKFLOW-PLAN.md)**, now in this repo — it was previously
sitting in an unversioned folder where this session could not see it, which is a large part of why
the two sessions drifted.

### The direction changed — this supersedes any earlier "server push" assumption

The pipeline no longer waits on a sanctioned database. Supabase is prohibited and no replacement
exists, so the design removes the dependency instead of waiting on it:

- Three practitioner apps run on **one machine**.
- The finished plan reaches the employee as an **encrypted QR code on a printed sheet**.
- Data comes back by **email** — encrypted payload between markers, batch-pasted into Cadence-Admin.
- **Nothing runs on a server.** A database becomes an optional later upgrade, not a blocker.

Full decision record (29 items), phases, invariants and open items are in the plan. The details
that are easiest to get wrong again:

- **Two secrets.** An admin-generated **setup code** encrypts the QR and is the permanent key for
  returned reports; the EIS says it aloud at handover. The employee then picks an **app PIN** that
  is a local lock only. This shape exists because **programs are never built with the employee
  present** — scoring and handover are separate visits, so everything is printed in advance.
- **The QR carries dosage; the client app carries content.** Measured: assignment-only + prescriptions
  ≈ 525 bytes, ~760 encrypted, against a 1,273-byte limit at high error correction. The old
  content-verbatim payload was 5,487 bytes and does not fit.
- **Two Cadence builds** — client (phone, Vercel, admin routes excluded at compile time) and admin
  (local, never deployed).

### Repo topology — decided, and a reversal

**Decision: keep the current topology. The Manual split is cancelled.**

This session had earlier decided to split `HMA-Manual` into its own repo, and was about to run
`git subtree split` when it discovered this repo's `origin/main` had moved 7 commits ahead —
including the feed v2 merge, the consolidation commit, and **HMA-Overlay**, which this session had
never heard of. The split was aborted.

On reading `HMA-Overlay/README.md`, its documented topology contradicted the split plan. Reassessed
and concluded the README's model is correct: **separate repos are for things that deploy
independently.** Tracker and Cadence deploy; AI, Manual and Overlay do not. Splitting them buys
clean history at the cost of a migration across two machines, which is exactly the situation that
just caused a near-miss.

`RESTRUCTURE-PLAN.md` Phase 2 (split Manual) is therefore **dead**. The rest of that document —
particularly the Cadence-clone procedure — still stands.

### Verified facts about the personal machine

- `HMA-Manual/` there has **no `.git`** and has drifted from this repo's 2026-07-31 snapshot since
  the 2026-08-03 reorg. It is backed up to `C:\Users\dlee5\HMA-backups\`. Fix is a proper clone of
  this repo, not a split.
- The `HMA-Cadence/` folder there does **not** contain Cadence — it holds an unrelated 2026-05
  schedule-tracker prototype that exists in no repo anywhere. Real Cadence has never been cloned to
  that machine. Also backed up.
- Tracker `npm install` was run; `npm test` passes.
- The Tracker clone there is behind `origin/main` (`c567c12`, which carries **"Send to Overlay"**).

### What the other session should know

1. **Read the pipeline plan before any Tracker, Cadence or Manual work.** Several planned changes
   touch the Tracker's record shape — a badge-number field, and persisting the finalized exercise
   program on the record. **Overlay reads those records**, so that shape now has two consumers.
2. **Nothing in the pipeline plan has been built.** It is planned only.
3. The plan's prerequisites table lists what must be true before Phase 0 starts.
4. **HMA-AI is out of scope** for the pipeline by decision (B5), with a note recording what it must
   eventually emit.

### Open questions for the other session

- The Overlay README describes folders as `HMA-Tracker-app/` and puts `api/`+`web/` at the repo
  root, while the personal machine uses `HMA-Correct-Exercise-Tracker/` and nests the AI app in an
  `HMA-AI/` folder. **The two machines' folder layouts do not match.** Worth aligning.
- That README states the suite `.gitignore` excludes the two nested repos. It does not — there are
  no such entries on `origin/main`. Intent vs. actual.
