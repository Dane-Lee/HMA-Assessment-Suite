# Working in this repo

## Two machines, two Claude sessions

This estate is worked on from **two machines** — a personal computer and an ATI work computer —
each with its own Claude session. **Neither session can see the other.** They have drifted before:
on 2026-08-20 the personal machine was 7 commits stale and nearly performed a `git subtree split`
from dead history.

**Therefore, every session, without being asked:**

1. **Read [HANDOFF.md](HANDOFF.md) first**, before touching anything. It is the shared log of what
   the other session did, decided, and why.
2. **`git fetch` and check how stale this clone is** before any git operation that rewrites history
   or removes files. Staleness is not visible without fetching.
3. **Append an entry to [HANDOFF.md](HANDOFF.md) before finishing** — what you did, what you
   decided, *why*, and anything the other session must know before it touches the same area.
   Newest entry at the top. Commit it with the work it describes.
4. **Push before you stop, even when the work is unfinished.** Unpushed work is invisible work —
   the other machine cannot see a local commit, an unversioned folder, or an uncommitted file. If
   the work is not ready for `main`, push it to a **branch**. A branch makes it visible without
   merging it into anything, which is the whole point: you get to avoid the collision *and* the
   other session gets to know the work exists.
5. **Never record a claim you did not verify.** See "Facts, not claims" below.

An entry is not optional bookkeeping. It is the only channel between the two sessions.

Rule 2 is now also enforced by a **SessionStart hook** (`tools/session-start-check.mjs`, wired in
`.claude/settings.json`) that fetches all three repos and prints staleness plus the newest handoff
heading before either session types anything. The hook exists because rule 2 was already written
here on 2026-08-20 and a session still went stale — a document is advisory, a hook is not. Do not
treat the hook as a substitute for reading HANDOFF.md; it prints one heading, not the entry.

## Facts, not claims

The 2026-08-20 handoff recorded *"Tracker `npm install` was run; `npm test` passes."* The Tracker
had **no `test` script at all** — `npm test` there would have failed outright. Nobody could check
the claim, and it cost the other session real time before it was disproved.

So: **`STATUS.md` is generated, never written.** Run `node tools/estate-status.mjs` to regenerate
it. Everything in it is the output of a command that actually ran on the machine named at the top —
repo HEADs and ahead/behind, which check commands genuinely exist and what they returned, how many
exercises still lack artwork. A check that could not run says so; *"deps not installed here"* is a
fact, silence is not.

When you want to tell the other session that something works, **make it verifiable** — commit a
test, or regenerate `STATUS.md` — rather than asserting it in prose. Prose in HANDOFF.md is for
decisions and reasoning, which cannot be generated. State is for `STATUS.md`.

## No fixed ownership split — which raises the stakes

Work is divided **opportunistically**, not by app or by layer (decided 2026-08-21). Either machine
may touch anything.

That is a deliberate choice, and it has a cost worth naming: the two sessions collided on
2026-08-20 because both independently designed the same QR handoff, and nothing structural prevents
that happening again. With no lanes, the handoff log, `STATUS.md` and the startup hook carry the
**entire** coordination load. Under a split you could get away with a thin log; here you cannot.

Practical consequence: **before starting any substantial piece of design, check HANDOFF.md and
`STATUS.md` for whether the other session is already on it.** Duplicated design is the specific
failure this estate has already had once.

## Where the plans live

- **[PIPELINE-WORKFLOW-PLAN.md](PIPELINE-WORKFLOW-PLAN.md)** — the HMA-Manual → Tracker → Cadence
  pipeline. Offline QR + email architecture. 29 recorded decisions, phases, invariants, open items.
  **Read before any pipeline work.**
- **[RESTRUCTURE-PLAN.md](RESTRUCTURE-PLAN.md)** — repo topology history. **Its Manual-split proposal
  is cancelled** (see HANDOFF 2026-08-20); kept for the Cadence-clone procedure and its audit record.
- **[TODO.md](TODO.md)** — AI app + Manual app task list.
- **[STATUS.md](STATUS.md)** — **generated, do not edit.** Current repo/check/artwork state as
  derived facts. Regenerate with `node tools/estate-status.mjs`.

## Checks that actually exist

Run these rather than assuming — and note the machine each was last run on, since dependencies are
not installed everywhere.

| what | command | from |
|---|---|---|
| Tracker exercise library | `npm test` | `HMA-Tracker-app/` |
| Tracker build | `npm run build` | `HMA-Tracker-app/` |
| API + Manual API | `pytest` | repo root |
| Estate status | `node tools/estate-status.mjs` | repo root |

`pytest` needs the repo root on `sys.path`; `pytest.ini` handles that, so a bare `pytest` works from
any directory. Before that file existed it failed *everywhere*, including the root, and only
`python -m pytest` worked — if you see `ModuleNotFoundError: No module named 'api'`, check that
`pytest.ini` is still present rather than changing how you invoke it.

The Tracker suite checks the five parallel structures keyed by exercise id stay in agreement, that
retired ids are not revived, and that no two exercises in the same picker are near-duplicates. That
last check exists because `s8` and `b7` were the same exercise under near-anagram names, both
reachable from the `sld` picker. **Adding an exercise means touching five structures plus
`DEFAULT_IMAGES` — run `npm test` after, it will tell you what you missed.**

## Repo topology (decided 2026-08-20)

```
HMA-Assessment-Suite   (this repo)  api/ web/ config/ + HMA-Manual/ + HMA-Overlay/
HMA-Correct-Exercise-Tracker        own repo, deploys to Vercel on push
HMA-Cadence                         own repo, will deploy its CLIENT build to Vercel
```

Separate repos are for things that **deploy independently**. AI, Manual and Overlay are local-only
tools and stay in this repo. **Do not propose splitting them out** — that was considered and
rejected on 2026-08-20 because it forces a migration across two machines for no deployment benefit.

## Machine-specific hazard — personal computer only

On the personal machine, `HMA-Manual/` was physically moved **out** of this repo's folder during a
2026-08-03 reorg, so `git status` there shows **~54 pending deletions** of `HMA-Manual/*`.
The files are safe; they live one level up. **Never run `git add -A` or `git commit -a` in this
repo on that machine** — it would commit the removal of the entire Manual app. Stage files
explicitly by name.

The work computer does not have this problem.

## Non-negotiables across the estate

- **No PHI to any AI platform. No cloud database.** Supabase is prohibited by ATI/Hendrickson IT.
- **Exercise IDs (`l1`, `s3`, `co2`…) are public identifiers** joining the Tracker, Overlay and
  Cadence. Retired IDs stay retired. Never renumber.
- **Cadence is employee-facing and receives only a finished exercise plan** — never demand-match
  findings, never scores.
- **Overlay is admin-facing only.** No employee-facing view belongs there.
