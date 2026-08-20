# HMA Assessment Suite — Repo Restructure Plan

**Status:** planned, not started. Nothing in this plan has been executed.
**Audit run:** 2026-08-03 · **Plan written:** 2026-08-08

Carrying the new folder organization over to GitHub. This doc is self-contained — it can be
picked up cold without re-deriving anything.

---

## 1. Verified current state (2026-08-03)

### Folder layout

```
ATI/HMA Assessment Suite/
  HMA-AI/                        git repo -> Dane-Lee/HMA-app.git  (redirects; repo was renamed)
  HMA-Manual/                    NO git
  HMA-Correct-Exercise-Tracker/  git repo -> Dane-Lee/HMA-Correct-Exercise-Tracker
  HMA-Cadence/                   NO git  -- and NOT the real Cadence (see below)
  Project Notes/                 2 .docx, unversioned
```

### The move broke nothing

All start scripts use `Set-Location $PSScriptRoot`; there are **no cross-project relative
paths** between the apps. Every suite passed after the move:

| Suite | Result |
|---|---|
| HMA-AI backend (`api/tests`) | 82 passed |
| HMA-AI web (vitest) | 21 passed (9 files) |
| HMA-Manual backend (`api_manual/tests`) | 5 passed |
| HMA-Manual web (vitest) | 11 passed (3 files) |
| Tracker (`tests/import-merge.test.mjs`) | passed |

The moved `HMA-Manual/` files are byte-identical to what the repo has committed (21 apparent
diffs were CRLF-only). Nothing was lost in the move.

### Open issues this plan resolves

1. **HMA-Manual is outside its own repo and unversioned.** The GitHub repo still tracks
   `HMA-Manual/` at its root, so `git status` in `HMA-AI/` shows **52 pending deletions**.
   **Do not run `git add -A` or `git commit -a` in `HMA-AI/`** until Phase 2 lands.
2. **The `HMA-Cadence/` folder is not HMA Cadence.** It contains `hma_schedule_tracker` — a
   React+Express+SQLite scheduling prototype last touched 2026-05-14. Confirmed against all 18
   commits of `Dane-Lee/HMA-Cadence`: that repo was created 2026-07-02 as "compliance-app Phase 1A
   scaffold" and renamed to HMA Cadence the same day; its first commit is already the PWA. **The
   prototype was never in the Cadence repo**, has no git anywhere, and is the only copy in
   existence. The real Cadence is not cloned anywhere on this machine.
3. **GitHub repo was renamed `HMA-app` → `HMA-Assessment-Suite`.** The local remote URL still says
   `HMA-app.git` and works only via GitHub's redirect.
4. **`HMA-AI/.git` is owned by `CodexSandboxOffline`, not `dlee5`** — git refused to touch it until
   a `safe.directory` exception was added globally (done 2026-08-03; the underlying ownership is
   still wrong).
5. Tracker clone has no `node_modules`, so `npm test` won't run there yet.
6. Both repos sit on unmerged feature branches. Everything is pushed; nothing is local-only.

### Compliance note picked up from the Cadence README

**ATI/Hendrickson IT prohibits Supabase as the database, and PHI must never be sent to any AI
platform.** Cadence now runs on a swappable adapter behind `src/lib/data/`, defaulting to a local
fictional-data adapter; the Supabase implementation is kept unwired, for reference only.

---

## 2. Decisions made (2026-08-08)

| Decision | Choice |
|---|---|
| Repo topology | **Umbrella + per-app repos** (5 repos, MasterMind pattern) |
| Sequencing | **Land feed v2 first**, then restructure |
| Schedule tracker prototype | **Archive to its own repo, move out to the ETS prototypes folder** |

### Target end state

```
Desktop/ATI/HMA Assessment Suite/        <- clone of NEW umbrella repo
├── HMA-AI/                              -> Dane-Lee/HMA-AI       (renamed from HMA-Assessment-Suite)
├── HMA-Manual/                          -> Dane-Lee/HMA-Manual   (NEW, split with history)
├── HMA-Correct-Exercise-Tracker/        -> unchanged
├── HMA-Cadence/                         -> clone of the real repo
└── Project Notes/                       <- tracked by the umbrella
                                            (the 4 app folders are gitignored by it)

Desktop/ATI/Encounter Suite/prototypes/hma-schedule-tracker/
                                         -> Dane-Lee/hma-schedule-tracker (NEW)
```

The suite folder root itself becomes the umbrella clone, so `Project Notes/` and the cross-app
docs get a versioned home and one clone gets you the map of the whole suite.

---

## 3. Phases

### Phase 0 — Safety net

- [ ] **Pause OneDrive sync** for the duration. Bulk file moves + git object writes inside a
      syncing folder is the most likely thing to bite this whole operation.
- [ ] Zip `HMA-Manual/` and `HMA-Cadence/` somewhere outside the suite (they are the two
      unversioned folders). Stops mattering after Phases 2 and 5.
- [ ] Fix `HMA-AI/.git` ownership properly (`takeown` / `icacls`). The `safe.directory` exception
      is a workaround, not a fix.

### Phase 1 — Land feed v2 (blocks everything else)

- [ ] Verify feed v2 end-to-end: score → Export for Tracker → import into Tracker → build an
      exercise program → change a score in Manual → export and import again. **Scores must update
      AND the exercise program must survive.**
- [ ] Merge `tracker-merge-on-reimport` → `main` in the Tracker repo.
      ⚠ **This auto-deploys to Vercel.** Confirm you want it live before pushing.
- [ ] Merge `hma-manual-tracker-feed-v2` → `main` in the AI repo.
      ⚠ That branch carries two independent strands: `45ba3a5` (Manual employee details) and
      `c59c52f` "Harden scoring failures uploads and sessions" — unrelated **AI-app** work
      (F7a/F7b, F14a, F16, 11a) committed by a parallel session onto the Manual branch.
      **OPEN QUESTION: land them together, or split `c59c52f` off first?**

Everything downstream rewrites paths, so both repos must be on a single clean line of history
first. Restructuring before this turns the Phase 2 split into rename conflicts across 52+ files.

### Phase 2 — Split HMA-Manual into its own repo

- [ ] From `main` in HMA-AI: `git subtree split --prefix=HMA-Manual -b hma-manual-only`
      (5 of the 14 commits on main touch it, so real history carries over).
- [ ] `gh repo create Dane-Lee/HMA-Manual`, then push `hma-manual-only:main`.
- [ ] **Write a `.gitignore` for the new repo.** The split will NOT carry one — the ignore rules
      live in the AI repo's *root* `.gitignore`, above the split prefix. Port these with the
      prefix stripped:
      `.env.manual`, `web_manual/dist/`, `web_manual/coverage/`, `data/manual/`,
      `.manual-pytest*/`, `.manual-test-data/`, plus `__pycache__/`, `.pytest_cache/`,
      `node_modules/`, `*.pyc`, `*-dev.out.log`, `*-dev.err.log`.
      **Miss this and the first commit sweeps up `.env.manual` and the test DBs.**
- [ ] Convert the existing folder into the clone in place — `git init`, add remote, `git fetch`,
      `git reset origin/main` — so untracked `.env.manual`, `data/` and `node_modules/` survive.
      Check `git status` after; expect CRLF noise, fix via `core.autocrlf`, don't commit it.
- [ ] In HMA-AI: `git rm -r HMA-Manual` + commit. This intentionally consumes the 52 pending
      deletions. Strip the now-dead `HMA-Manual/*` lines from its `.gitignore`.
- [ ] Re-run both Manual suites (5 backend, 11 vitest) to confirm it works as its own repo.

### Phase 3 — Re-home the AI app

- [ ] Rename the GitHub repo `HMA-Assessment-Suite` → `HMA-AI`. This frees the suite name for the
      umbrella. Note: the `HMA-app` redirect will chain to `HMA-AI`, and creating a new
      `HMA-Assessment-Suite` in Phase 4 breaks that old redirect — stale links then land on the
      umbrella. Harmless here.
- [ ] `git remote set-url origin` to the new name.
- [ ] Commit the pending `README.md` / `TODO.md` edits — they already describe the new layout.

### Phase 4 — Create the umbrella

- [ ] `gh repo create Dane-Lee/HMA-Assessment-Suite` fresh; `git init` at the suite folder root.
- [ ] `.gitignore` the four app folders.
- [ ] Contents: suite README (the four apps, the Manual → Tracker → Cadence data flow, which repo
      is which, clone instructions), this plan, and `Project Notes/`.

### Phase 5 — Fix Cadence

- [ ] Move the prototype to `ATI/Encounter Suite/prototypes/hma-schedule-tracker/`. Matches the
      convention already there (`prototypes/daily-prioritization-list/`) and the prototype's own
      audit note that it was meant to fold into the Encounter Tracking System.
- [ ] `gh repo create Dane-Lee/hma-schedule-tracker`, `git init`, push. Name matches its
      `package.json`. Note: the existing ETS prototype has no repo, so this one is the odd one out.
- [ ] `git clone Dane-Lee/HMA-Cadence` into `HMA-Cadence/`, `npm install`, run its vitest suite.

### Phase 6 — Housekeeping

- [ ] `npm install` in the Tracker so `npm test` runs.
- [ ] Cross-link the READMEs so each repo points back at the umbrella.

---

## 4. Risks

- **Phase 1 is load-bearing.** Skipping it turns the Phase 2 split into a wall of rename conflicts.
- **The Vercel deploy in Phase 1** is the only step with an outside-facing effect.
- **OneDrive + git** during Phases 2–5 — pause sync.
- **The prototype in `HMA-Cadence/` is the only copy anywhere.** Don't delete that folder to make
  room for the real Cadence clone; move it first (Phase 5).

## 5. Open questions before starting

1. Should `c59c52f` land with feed v2, or be split off first?
2. Do you want the Tracker live on Vercel at the moment of the Phase 1 merge?
