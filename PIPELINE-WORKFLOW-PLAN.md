# HMA Pipeline — HMA-Manual → HMA Tracker → Cadence

**Rewritten:** 2026-08-17 · **Amended:** 2026-08-20 (second audit; E1–E10) · Supersedes the 2026-08-14 draft
**Status:** direction decided, nothing built beyond hop 1

---

## 1. What changed and why

The 2026-08-14 draft assumed the plan would eventually reach the employee over a network — a
Supabase Edge Function originally, then some ATI-sanctioned replacement. Supabase is prohibited and
no sanctioned backend exists, so that plan was permanently blocked on a dependency outside the
project's control.

**The new direction removes the dependency instead of waiting on it.** The three practitioner apps
run on one machine. The employee's phone gets its plan from a QR code and sends data back by email.
Nothing runs on a server, no database holds PHI, and there is no approval gate between here and a
working pipeline.

A database is no longer a blocker. If one is ever sanctioned it becomes an optional upgrade behind
Cadence's existing adapter interface — it is not on the critical path for anything below.

Companion doc: `RESTRUCTURE-PLAN.md` (repo topology; its Phase 1 is this doc's Phase 0).

---

## 2. Architecture

```
   ┌──────────────── ONE PRACTITIONER MACHINE (BitLocker) ─────────────────┐
   │                                                                       │
   │   HMA-Manual            HMA Tracker              Cadence-ADMIN        │
   │   (FastAPI+SQLite)      (offline index.html)     (separate build)     │
   │   score assessment  →   author program       →   issue plan / QR      │
   │                                                  read returns         │
   └───────────────────────────────┬───────────────────────────────────────┘
                                   │
                  printed sheet + encrypted QR  │  email (encrypted payload)
                                   │            │
                                   ▼            │
                        ┌──────────────────────────────┐
                        │   Cadence-CLIENT (phone)     │
                        │   separate build, offline    │
                        │   PWA from static host       │
                        └──────────────────────────────┘
```

**Two builds from one Cadence codebase.** The client build has admin routes excluded at compile
time — not hidden behind a runtime role check. The employee's phone must not physically contain the
admin pages.

**Static hosting serves files only.** The client PWA is downloaded from Vercel (E6); no employee
data ever reaches that host. Plan payloads ride in the URL fragment, which browsers never transmit.
The admin build is never deployed — it runs locally and only on the practitioner machine.

**No shared database anywhere.** Every hop is a self-contained document.

**Web-first, with desktop kept available.** All three practitioner apps run in a browser for now.
They do not have to: both codebases already route storage through swappable interfaces (the
Tracker's `window.storage`, Cadence's `src/lib/data/` contract), so wrapping them in a desktop shell
later is a packaging change, not a rewrite. Desktop would dissolve the browser's per-site storage
wall — letting the Tracker and Cadence-Admin share files directly — and would make durability a
non-issue. It is not being done now because ATI's policy on installed software is inconsistent, and
a browser cannot be revoked. If an installed app were blocked or removed after the workflow was
built around it, the whole pipeline would stop, with employees already enrolled. The reverse risk
does not exist.

---

## 3. The workflow

| # | Actor | App | Action |
|---|---|---|---|
| 1 | EIS | HMA-Manual | Score 5 movements per side; flag pain, hypermobility, OA; enter employee details incl. **badge #** |
| 2 | EIS | HMA-Manual | Export for Tracker → paste into the Tracker |
| 3 | EIS | Tracker | Auto-suggestions from scores/hypermobility/quality-focus, then clinical edits; program fitted to the 20-min/day budget |
| 4 | EIS | Tracker | Finalize → export plan payload |
| 5 | EIS | Cadence-Admin | Paste payload; Cadence-Admin generates the setup code and the encrypted QR |
| 6 | EIS | both | Print in advance: the Tracker's illustrated program, plus Cadence-Admin's QR companion page |
| 7 | EIS | — | **Handover at a later appointment** (may be on the factory floor). Give the sheets, say the setup code, help with install |
| 8 | Employee | phone camera | Scan QR from the companion page → browser opens the client app → install |
| 9 | Employee | Cadence-Client | Enter setup code → plan decrypts → choose an app PIN → daily checklist |
| 10 | Employee | Cadence-Client | Tap exercises complete; report pain if it occurs |
| 11 | Employee | Cadence-Client | Pain tap → immediate prompt → sends encrypted report by email |
| 12 | EIS | Cadence-Admin | Paste the email → report decodes into the pain queue → follow up in person |
| 13 | Employee | Cadence-Client | Weekly prompt → sends cumulative progress by the same route |
| 14 | EIS | Cadence-Admin | Batch-paste weekly emails → compliance updates |
| 15 | EIS | HMA-Manual | Re-assess at the re-test date → repeat from 1 |

**Programs are never built with the employee present.** Scoring and handover are separate visits, so everything handed over must be printed in advance and no secret can be captured at issue time (E8).

**HMA-Manual stays fully standalone.** The export is an outbound side-door, never a dependency.
**The Tracker stays offline and local-only.**

---

## 4. Transport

### 4.1 Outbound — the plan QR

Encrypted with an admin-generated setup code (E8), printed on the companion page in advance.

**The QR carries the prescription. The client app carries the content.**

| In the QR | In the client app's bundled library |
|---|---|
| Recognition key, badge #, first name | Exercise name |
| Plan ID, library version, admin email | Instructions |
| Assessment / follow-up / re-test dates | Image |
| Work days, session budget | — |
| Per exercise: ID, days, **effective sets/reps** | — |

Nothing dosage-related is ever inferred from the library. What the EIS prescribed is what the
employee sees, permanently, and it always matches the printed sheet.

**Measured sizes** (12-exercise plan, real library strings):

| Shape | Bytes | Fits QR at EC-H (1,273)? |
|---|---|---|
| Old contract v1, content verbatim | 5,487 | No — 5 codes |
| Assignment-only | 308 | Yes |
| With prescriptions carried | ~525 | Yes |
| Encrypted + encoded | ~760 | Yes, ~500 spare |

Highest error correction is deliberate: phone cameras, plant lighting, creased paper.

### 4.2 Return — email

Same channel for both pain reports and weekly progress.

1. App builds an encrypted payload and opens a pre-addressed email (address embedded in the client
   app from the original plan QR).
2. Body: a readable line, plus the encrypted payload between two obvious markers.
3. EIS selects the whole email, copies, pastes into Cadence-Admin.
4. Cadence-Admin finds **every** payload between markers in whatever was pasted — so a batch of
   emails can be selected, copied and pasted in one action.
5. Decrypts with the stored PIN, matches the recognition key to a local profile, files the data.

**The recognition key belongs to the person, not the plan.** It is generated once, at first plan
issue, and reused for every later plan that employee receives — otherwise a return sent after a
re-assessment cannot be matched to the existing profile. The plan ID changes; the key does not.

**The return payload carries no identifying information** — only the recognition key and the event
data. Cadence-Admin attaches the name, badge and program from its own records. An intercepted
report is meaningless without the practitioner's machine.

The return carries completions, pain events, and thumbs-up/down feedback (E5). Payloads are
cumulative: the phone sends its entire history every time (~22 bytes for four weeks of completions),
so a missed or filtered send self-heals on the next one.

**Fallback:** an on-screen QR the EIS scans at the appointment, for employees who never send.

### 4.3 What email does and doesn't protect

Encryption protects the *content* of a report. It does not hide the *fact* of one — the message
arrives from the employee's own address. That is no different from an employee emailing "my
shoulder hurts," and is acceptable.

---

## 5. Decision record

| # | Decision |
|---|---|
| A1 | **Images: build-time derivatives.** Source PNGs (36 files, 46.6 MB, ~1450×1086) are never modified. The build generates phone-sized copies for the client bundle only. Tracker keeps full quality for print. |
| A2 | **Demo seed stays for dev and tests, stripped from production builds.** Build flag; the dead branch is eliminated at compile time so personas are physically absent from shipped files. Tests import the seed builder directly. Requires new empty states (client: "no plan yet, scan your QR"; admin: empty roster). |
| A3 | **Library copied Tracker → Cadence once finalized.** No generator, no parity test. Version stamped into the QR; an unknown exercise ID makes the client refuse the whole plan and demand an app update rather than render a partial one. **Retired IDs are never reused or renumbered.** |
| A4 | **Client is a separate build** with admin routes excluded at compile time. Consequence to accept: data returning from a personal phone is self-reported by nature and must never be treated as verified. |
| B1 | **Client PWA served from static hosting**, installed to the phone, then fully offline. Install steps printed on the sheet; **no URL in plain text** — the EIS assists if a scan fails. |
| B2 | **Cadence's ingest is rewired** to resolve exercise IDs against its bundled library instead of filing details out of the payload. |
| B3 | **Return path is email, weekly, batch-pasted**, cumulative payload. Appointment scan retained as fallback. |
| B4 | **Nothing on the phone is ever deleted.** Rescanning the same plan restores it; a new plan activates and archives the old one with its history intact. No appointment ordering rule needed. |
| B5 | **HMA-AI is out of scope**, with a note recording what it must eventually emit. |
| B6 | **Cadence-Admin needs an export** — it is the only store holding employee PINs and has no second copy. Export stays on the encrypted machine, never cloud-synced. |
| C1 | **Payload size-regression test** — assert a worst-case plan stays under the EC-H limit. |
| C2 | **QR on the printed sheet, encrypted.** *(Key model superseded by E8 — the key is an admin-generated setup code, not an employee-chosen PIN.)* |
| C3 | **One logical contract, two encodings.** One validator runs on the decoded plan object. The old server-transport contract doc is kept, marked superseded. |
| C4 | Library file format — implementation note, no decision needed. |
| D1 | **Pain flow:** tap → save locally → immediate in-app prompt → encrypted email → admin paste → pain queue → in-person follow-up. Declining or a failed send loses nothing; the event still rides home. |
| D2 | **Cadence-Admin stays.** It issues plans, generates QRs, and reads returns. |
| D3 | **PIN retained.** *(Superseded by E8: the app PIN is a local lock, not the decryption key, and may be changed freely.)* |
| D4 | **Minimum PHI in the QR** — recognition key, badge, first name. Returns carry only the key; the admin machine attaches everything else from local records. |
| D5 | **Compliance figures show an as-of date.** Accepted provisionally; open for revision. |
| E1 | **Tracker → Cadence-Admin hand-off is a paste**, reusing Cadence's existing import page. One action per employee at the appointment. A shared watched folder is the upgrade path if it becomes tedious; relaying through HMA-Manual's local server is rejected because it would break the Tracker's standalone property. |
| E2 | **Two printouts, two purposes.** The Tracker prints the full illustrated program — unchanged, and complete on its own for an employee with no phone or who declines Cadence. Cadence-Admin prints a companion page: QR, install steps, PIN reminder, and a plain exercise list as backup. No print layout is duplicated. |
| E3 | **Web-first; desktop stays a late-binding option.** Build in the browser, keep every read and write behind the existing storage adapters. Revisit if ATI's software policy proves permissive. |
| E4 | **Secrets are 4 digits for now.** Sufficient against the realistic threat (someone picking up a printed sheet). Upgradeable to 6+ later if the offline-cracking exposure ever matters. |
| E5 | **Thumbs-up/down feedback rides home** with completions and pain events. Costs a couple of bytes; Cadence already captures it per assignment. |
| E6 | **Client PWA hosts on Vercel**, as its own project pointed at the Cadence repo — separate from the Tracker's. Configured to build **the client only**; the admin build is never deployed anywhere and stays local to the practitioner machine. Cannot be set up until the build split in Phase 5 exists. |
| E7 | **HMA-Manual gets its own repo before Phase 1.** Its code exists on GitHub only as a folder inside `HMA-Assessment-Suite` (commits through 2026-07-31), and the local working copy has no `.git` at all. Run `RESTRUCTURE-PLAN.md` Phase 2 first — subtree split, create the repo, convert the folder to a clone in place, then `git rm -r HMA-Manual` in HMA-AI. Pause OneDrive while doing it. |
| E8 | **Two secrets, separate jobs.** Cadence-Admin generates a random **setup code** when the plan is built; it encrypts the QR and is the permanent key for every returned report. The EIS conveys it verbally at handover. The employee then chooses their own **app PIN**, which is a local lock only — it never leaves the phone, the EIS never knows it, and changing it breaks nothing. Nothing is captured at the assessment, and everything the employee receives is printed in advance. Consequence: a lost phone needs the setup code from the EIS to re-enroll, so device loss is a conversation rather than self-service. |
| E9 | **Badge # optional in HMA-Manual, required at plan issue.** Anonymous single-field scoring survives. The Tracker flags a badge-less record on import so the gap surfaces before a program is built, not after. |
| E10 | **All 24 missing exercise images sourced before the client ships.** 36 of 60 IDs currently have one; 15 of the 24 gaps are in the auto-suggestion lists, and all six trunk exercises `t1`–`t6` are missing. The gap already affects the printed sheet today, so each image fixes print immediately. |

---

## 6. What exists vs what's missing

### Built

- **HMA-Manual → Tracker export** (`trackerExport.ts`) with movement-key mapping and side order.
- **Tracker re-import merge** — field-classified so authored work survives a re-import.
- **Cadence receiver skeleton** — `ingestPlan()`, `planValidation.js`, `AdminImportPlan.jsx`.
- **Cadence employee view** — daily checklist, weekday-aware, tap-to-complete, inline pain reporting.
- **Cadence admin views** — employee list with compliance, pain queue, employee detail.
- **Tracker scheduler** — `_computeSchedule()` already emits ISO weekdays 1–5 fitted to a 20-min budget.

### Missing

| Gap | Where |
|---|---|
| **Badge # exists nowhere** | Manual schema, `trackerExport.ts`, Tracker form/record |
| **The Tracker never persists the program it builds** | `selectedExercises` / `customSetsReps` / day-split are session-only state |
| Plan payload builder | Tracker |
| PIN capture, encryption, QR generation | Cadence-Admin |
| Separate client build | Cadence |
| QR scan + decrypt + ingest | Cadence-Client |
| Email compose (pain + weekly) | Cadence-Client |
| Marker-extracting paste ingestion | Cadence-Admin |
| Export | Cadence-Admin |
| Empty states | both Cadence builds |

The first two are data-model gaps, not transport gaps. They were required under the old direction
and are required under this one — nothing about that work is wasted.

---

## 7. Phases

### Prerequisites — set up the environment first

The later phases assume a working environment that does not exist yet. None of this is design work;
all of it is invisible until you go to start a phase and find the pieces missing.

| # | Prerequisite | Why it blocks | Blocks |
|---|---|---|---|
| P1 | **Pause OneDrive sync** | Bulk moves + git object writes inside a syncing folder is the likeliest thing to corrupt the split | P2, P4 |
| P2 | **Move the schedule-tracker prototype out of `HMA-Cadence/`**, then clone the real `Dane-Lee/HMA-Cadence` into it | That folder still holds an unrelated 2026-05 prototype — `client/`, `server/`, `AUDIT_FINDINGS_2026-05-14.md` — and it is **the only copy in existence**, in no repo anywhere. Real Cadence has never been cloned to this machine. | Phases 5–7 (all Cadence work) |
| P3 | **`npm install` in the Tracker** | No `node_modules`, so `npm test` cannot run | Phase 1 (import-merge test), Phase 4 (size-regression test) |
| P4 | **Fix `HMA-AI/.git` ownership** (`takeown` / `icacls`) | Owned by `CodexSandboxOffline`, not `dlee5`; git only works via two global `safe.directory` exceptions. A workaround, sitting exactly where Phase 0 performs a subtree split. | Phase 0 |
| P5 | **Split HMA-Manual into its own repo** (E7) | Local folder has no `.git` and has drifted from the 2026-07-31 GitHub snapshot since the reorg | Phase 1 |

P2 and P5 are covered in detail by `RESTRUCTURE-PLAN.md` Phases 5 and 2 respectively.

### Phase 0 — Land feed v2 and give HMA-Manual a repo *(blocks everything)*
Verify Manual → Tracker end to end: score → export → import → build → change a score → re-export →
re-import. Scores must update and authored work must survive. Then merge `hma-manual-tracker-feed-v2`
and `tracker-merge-on-reimport`. ⚠ The Tracker merge auto-deploys to Vercel.

Then split HMA-Manual into its own repo per `RESTRUCTURE-PLAN.md` Phase 2 (E7). Pause OneDrive first.
**Nothing in Phase 1 starts until this lands** — it adds a database migration to a folder that
currently has no version control and has drifted from the 2026-07-31 snapshot on GitHub since the
2026-08-03 reorg.

### Phase 1 — Badge # end to end
Manual: add `employee_number` via the existing `_apply_column_migrations` pattern; add to the
Employee Details section. Export it. Tracker: add the field to the form, `getFormData()`, and
`IMPORT_DETAIL_FIELDS` so an import can fill it but never blank it. Bump the field count in
`tests/import-merge.test.mjs`. Badge stays **optional** in Manual (E9) — add a visible flag on the
Tracker's record list when one is missing, so it surfaces before a program is built.
**Accept:** a badge round-trips Manual → Tracker and survives re-import; a badge-less record is
visibly flagged and still scoreable.

### Phase 2 — Persist the program in the Tracker
Write the finalized selection to the record: plan ID, work days, session budget, and per exercise
the ID, effective prescription, days and sort order. Re-opening the builder restores it rather than
re-deriving suggestions. It joins the never-overwritten class in `mergeImportedRecord`.

**The print sheet must read the persisted schedule, not recompute it.** `_renderPrintSheet()`
currently calls `_computeSchedule()` at print time, and that function has a rebalancing pass — so
recomputing after the plan is stored can put different days on the paper than in the QR.
**Accept:** build a plan, reload, reopen — same program. A Manual re-import with changed scores
leaves it intact. Printed days match the stored days exactly.

### Phase 3 — Library and assets
Finalize the library in the Tracker. Copy it to Cadence with a version stamp. Reconcile the existing
`LIBRARY` constant in `localSeed.js` (demo-only) so there is one clear owner. Add the build step that
generates phone-sized image derivatives, and source the **24 missing exercise images** (E10) —
`b2 b3 b4 b6 b7 c3 c9 co3 co5 l2 l4 l7 s5 s8 sh1 sh3 sh6 sh8 t1 t2 t3 t4 t5 t6`. Each needs a file
in `public/images/` **and** an entry in `DEFAULT_IMAGES`; a file without a registry entry renders
nowhere. Every image also fixes the printed sheet immediately, independent of the client app.
**Accept:** the client bundle carries every exercise ID the Tracker can prescribe, at a size that
installs over cellular.

### Phase 4 — Issue a plan
Tracker emits the payload; the EIS pastes it into Cadence-Admin (E1). Cadence-Admin generates the
setup code (E8) and the recognition key — reusing the employee's existing key if they already have
one — encrypts, and produces the QR. Nothing is captured from the employee at this stage; they are
not present (E8). Two printouts
(E2): the Tracker's existing illustrated program, unchanged, and Cadence-Admin's new companion page
carrying the QR, install steps, PIN reminder and a plain exercise list. Size-regression test (C1).
**Operational rule (G3):** if a plan uses an exercise added since the client was last deployed,
**deploy the client first**. Otherwise the employee's app refuses the whole plan on the version
check — correct behavior, but avoidable.

**Accept:** a scored assessment produces both printouts, and the payload round-trips through
encrypt → QR → decode → decrypt in a test harness. (End-to-end scanning is verified in Phase 5;
Phase 4 cannot depend on a client that does not exist yet.)

### Phase 5 — The client app
Separate build with admin routes excluded. Seed gating and empty states. Ingest rewired to the
bundled library. Scan → setup code → decrypt → **choose an app PIN** → daily checklist. Version-mismatch refusal.
Remove the obsolete `must_change_pin` / `SetPin` temp-PIN flow; the app PIN is a local lock and may
be changed freely without affecting decryption (E8).
Once the split exists, create the Vercel project for the client build (E6).
**Accept:** an employee scans the sheet, installs, enters their PIN, and sees the right exercises on
the right weekday — offline. The deployed bundle contains no admin routes.

### Phase 6 — Pain reporting
Tap → save → immediate prompt → encrypted email. Marker-extracting paste ingestion in Cadence-Admin,
filing to the pain queue via the recognition key. Unsent indicator.
**Accept:** a pain tap reaches the admin pain queue on the correct profile.

### Phase 7 — Weekly return
Weekly prompt, cumulative payload, batch paste. Appointment-scan fallback. As-of dating on compliance.
**Accept:** a week of completions reaches the admin compliance view; a batch of emails ingests in one
paste.

### Phase 8 — Durability and housekeeping
Cadence-Admin export. Backup routine using the Tracker's existing export. Route `auth.jsx`'s
session writes through the data adapter so invariant 8 actually holds. Note HMA-AI's future
interface. Cross-link the READMEs.

---

## 8. Invariants

1. **Exercise IDs are public identifiers.** They are the join key between a QR and the client's
   library. Retired IDs stay retired; never renumber.
2. **The QR carries dosage; the library carries content.** No prescription is ever inferred.
3. **Nothing shares a database.** Every hop is a self-contained document.
4. **No PHI to any AI platform. No cloud database.**
5. **Nothing on the phone is ever deleted.**
6. **A blank never overwrites a value** — governs both the Manual→Tracker merge and every payload.
7. **Returned compliance data is self-reported**, never a verified record.
8. **No direct storage calls.** Every read and write goes through the Tracker's `window.storage` or
   Cadence's data-layer contract. This is what keeps the desktop option cheap; if it slips, the
   conversion becomes an archaeology project. **Already violated:** `auth.jsx` writes the session
   straight to `localStorage`. Route it through the adapter as a cleanup task in Phase 8.

---

## 9. Open items

1. **iOS storage behavior** — a home-screen PWA and Safari may not share storage. Verify on a real
   iPhone. In-app scanning after install avoids the question.
2. **Install instructions must cover the default browser**, not just Safari.
3. **Batch email at scale** — parked, owner has an approach to bring.
4. **D5** — as-of dating accepted provisionally.
5. **Software-policy probe.** Whether an installed application actually runs on the practitioner
   machine is unknown — policy is inconsistent. Testing it is independent of the build and can
   happen any time; the answer decides whether E3 gets revisited.
