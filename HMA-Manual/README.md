# HMA-Manual

HMA-Manual is a sister program to the original HMA app. It uses separate app folders and separate data storage:

- Backend: `api_manual`
- Frontend: `web_manual`
- Config: `config_manual`
- Data: `data/manual`

Open this `HMA-Manual` folder in VS Code when you want to work only on the sister app.

The manual app intentionally does not call the original scoring service. Review videos are temporary files for provider review only.

## What it does

- **Provider-scored HMA** — login (optional TOTP MFA), consent-gated assessment, per-side 0–3 scoring
  for the five movements with collapsible fault-qualifier checklists and provider notes.
- **Scoring rules** match the official HMA sheet: each movement's final score is the **lower of the two
  sides**, total is out of **15**, and bands are **0–5 (High) / 6–10 (Moderate) / 11–15 (Low)**.
- **Clinical flags that drive corrective exercises** — **pain** (per side), **hypermobility**
  (per movement), and **osteoarthritis / OA** (per assessment).
- **Review videos** — per movement side, optional and temporary. Attach a file, or **record in the
  browser** (see Camera Recording). Auto-purged on retention expiry or provider confirmation.
- **Employee mobile capture** — issue a secure upload link (the "Issue Mobile Video Request" modal on
  the scoring page) that opens the employee's phone camera to record and upload their assigned movements.
- **Export to the Corrective Exercise Tracker** — see below.

## Corrective Exercise Tracker export

The Manual app is the front door of the HMA suite (**Manual → Corrective Exercise Tracker → Cadence**).
On an assessment's **Results** page, **Send Scores to the Tracker** produces the Tracker's own JSON
record (scores, pain, hypermobility, OA). Use **Download for Tracker** or **Copy JSON**, then in the
HMA Corrective Exercise Tracker open **Import → Paste JSON**. The Tracker turns it into a corrective
exercise plan.

**Employee details.** New Assessment requires only a participant name or ID, so anonymous scoring stays
a single field. A collapsed **Employee Details (Optional)** section adds first/last name, company,
department, shift, and location; anything filled in is carried into the export so it does not have to be
re-keyed in the Tracker. When first/last name are left blank the participant name is split as a
fallback — on the **last** space ("Mary Jo Smith" → Mary Jo / Smith), and "Last, First" is understood.

**Re-scoring.** The Manual assessment's id is reused as the Tracker record id. Fix a score and export
again, and the Tracker **updates** the record it already holds: scores, pain, hypermobility, OA and
employee details refresh, while the exercise plan, observations, quality focus, and follow-up/re-test
dates built inside the Tracker are preserved. Notes refresh only while they are unedited in the Tracker.
(This requires the Tracker at `tracker-merge-on-reimport` or later; older builds skip the re-import.)

## Camera Recording

The provider scoring page can record review clips in the browser: **Record** on a movement side opens a
live viewfinder (`getUserMedia`), records with `MediaRecorder`, and lets you keep or retake the clip
before saving it like any uploaded file. Browsers only grant camera access in a **secure context**, so
this works on **localhost** in development and requires **HTTPS** in production (the reverse-proxy setup
below provides it).

## Local Development

1. Copy `.env.manual.example` to `.env.manual` and change the bootstrap password.
2. Start the app:

```powershell
.\start-manual-dev.ps1
```

The manual frontend runs at `http://localhost:5182` and the manual backend runs at `http://localhost:8003`.

## Public Deployment Notes

Run HMA and HMA-Manual behind a reverse proxy. The public proxy should terminate HTTPS and route separate hostnames to private app ports, for example:

- `hma.example.com` -> original HMA
- `hma-manual.example.com` -> HMA-Manual

For public deployment, enable provider MFA, use named provider accounts, and complete the compliance review for employee movement videos and retention.
