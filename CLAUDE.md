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

An entry is not optional bookkeeping. It is the only channel between the two sessions.

## Where the plans live

- **[PIPELINE-WORKFLOW-PLAN.md](PIPELINE-WORKFLOW-PLAN.md)** — the HMA-Manual → Tracker → Cadence
  pipeline. Offline QR + email architecture. 29 recorded decisions, phases, invariants, open items.
  **Read before any pipeline work.**
- **[RESTRUCTURE-PLAN.md](RESTRUCTURE-PLAN.md)** — repo topology history. **Its Manual-split proposal
  is cancelled** (see HANDOFF 2026-08-20); kept for the Cadence-clone procedure and its audit record.
- **[TODO.md](TODO.md)** — AI app + Manual app task list.

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
