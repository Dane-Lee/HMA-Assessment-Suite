# Handoff log

Shared channel between the two Claude sessions working this estate (personal computer / ATI work
computer). Neither session can see the other. **Read the top entry before starting. Add a new entry
before you finish.** Newest first.

Entry format: date · machine · what was done · what was decided and **why** · what the other
session must know.

---

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
