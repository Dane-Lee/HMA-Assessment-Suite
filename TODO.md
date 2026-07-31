# HMA App — TODO

Consolidated task list for both the AI app (`api/` + `web/`) and the Manual sister app (`HMA-Manual/`).
Source of truth for the AI roadmap is [docs/self-guided-assessment/phase-plan.md](docs/self-guided-assessment/phase-plan.md).

Last reviewed: 2026-07-31

**Branch state:** `hma-manual-ui-polish` (Manual app) and `rotation-accuracy` (AI scoring) are merged
into `main`. Current integration work is on `hma-manual-tracker-feed-v2`.

---

## AI App (Self-Guided Employee Assessment)

### ✅ Done
- **Phase 1 — Identity, magic links, role separation.** Employee/magic-link/session tables,
  `auth_tokens`, provider + self-session routes, role-aware middleware, and the self-flow frontend.
- **Phase 2 (capture mechanics, partial)** — recorder, quality telemetry, mobile capture, and
  provider pose overlays. The score-acceptance quality gate remains open below.
- **Commercial hardening — 2026-07-31:**
  - [x] **F7a/F7b:** structured pose-failure diagnostics; production now fails closed to
        unscoreable/provider-review state. Deterministic fallback requires explicit test/dev opt-in.
  - [x] **F14a:** request-body and exact file-byte upload limits are enforced while streaming;
        partial/invalid uploads are cleaned up.
  - [x] **F16:** per-client throttling on provider PIN and employee magic-link session creation.
  - [x] **11a:** automated failure-path harness for unavailable pose services, valid/corrupt media,
        oversized/empty/unsupported uploads, migration safety, throttling, and UI review handling.

### 🔲 Phase 0 — Groundwork (blocking; long lead time)
- [ ] Shoot the **demo videos** (5 looping clips, both sides) and drop into `web/public/`.
      None present yet — only the logo.
- [ ] Add content-schema fields to `config/movements.json` (`demo_video_url`, `coaching_cues`,
      `camera_setup_self`, `common_mistakes`, `recording_seconds_min/max`).
- [ ] **Legal / consent review**; add the `employer_distribution_acknowledged` consent flag.
- [ ] Confirm **HIPAA scope** for self-administered + employer-distributed flow.
- [ ] Verify **MediaPipe + OpenCV in the production runtime**. Production fallback scoring is now
      disabled by default; an unavailable pose service produces an unscoreable/provider-review clip.
- [ ] **Rotation-accuracy validation** — Tier-1 synthetic analysis DONE
      ([docs/self-guided-assessment/rotation-accuracy-findings.md](docs/self-guided-assessment/rotation-accuracy-findings.md)):
      trunk gate rides on uncalibrated z-scale + a `max()` inflation bug; cervical metric is blind to
      slide/side-bend confounds.
  - [x] (a) Robust-peak estimator fix — `_robust_max`/`_min`/`_span` replace raw `max()`/`min()`/span.
  - [x] (b) Ear-visibility cervical yaw prototype — proven to reject the slide/side-bend confounds
        ([models/cervical_ear_yaw_model.py](docs/self-guided-assessment/models/cervical_ear_yaw_model.py));
        logged as non-gating debug metric `ear_visibility_asymmetry`.
  - [ ] (c) **Tier-3 ground-truth capture** — protocol drafted
        ([docs/self-guided-assessment/tier3-capture-protocol.md](docs/self-guided-assessment/tier3-capture-protocol.md));
        blocked on a capture session. Feeds threshold re-tuning (`calibration.py`) + augment-vs-replace call.
- [ ] Personal **mobile camera-prop reality test** for all 5 movements to calibrate coaching copy.

### 🔲 Phase 2 — Remaining
- [ ] **Finding 8 — score-acceptance quality gate (NEXT):** define and enforce the minimum usable
      detection rate, required-landmark visibility, duration/framing, and retake-versus-review rules.
- [ ] **Finding 10 — server-authoritative provenance:** finalize from server-owned capture records;
      do not accept client-authored app scores, metrics, source, or quality as authoritative evidence.
- [ ] **Findings 1/5 — employee ownership + link semantics:** bind assessments to employees and
      make issued links resolve only the intended employee/assessment lifecycle.
- [ ] **Finding 12 — scoped mobile authorization:** replace provider-wide mobile privileges with
      assessment-scoped participant credentials.
- [ ] **Findings 2/15 — lifecycle + incomplete semantics:** represent draft/submitted/returned/
      reviewed states and incomplete or unscoreable movements without misleading totals.
- [ ] Wire demo videos + content schema into the per-movement screens.
- [ ] Replace **scoring placeholders** with real logic — `excessive_effort_placeholder`,
      `finger_walking_placeholder` in `api/app/services/scoring/movements/`.

### 🔲 Phase 3 — Provider review queue (~1 week) — NOT STARTED
- [ ] Add `submission_status` field to assessments.
- [ ] `POST /api/provider/assessments/{id}/return-for-retake`.
- [ ] `POST /api/provider/assessments/{id}/publish`.
- [ ] `/provider/inbox` page (filterable, pain-flag first, then oldest unreviewed).
- [ ] Per-submission review view: per-side playback, score override, summary-text field.

### 🔲 Phase 4 — Employee status & summary view (~0.5 week) — NOT STARTED
- [ ] `GET /api/self/assessment` returning current state + published provider summary.
- [ ] Employee landing shows status (`submitted` / `returned_for_retake` / `reviewed`).
- [ ] `returned_for_retake` deep-links into just the flagged movements.
- [ ] `reviewed` shows plain-English summary (no numbers, no fault list).

### ⏸ Deferred / out of scope
- [ ] Phase 5 — Email notifications (deferred until volume justifies it).
- [ ] Phase 6 — Corrective exercises (separate project; own decision doc).

---

## Manual App (`HMA-Manual/`)

Provider-scored, no AI. Full scoring workflow + Corrective Exercise Tracker feed + in-app camera
(see [HMA-Manual/README.md](HMA-Manual/README.md)).

### ✅ Done
- **Core manual workflow** — provider login (+ optional MFA), consent-gated assessments, per-side
  0–3 scoring with fault checklists + notes, per-movement review videos (upload/replace/delete,
  retention purge), employee mobile upload links, audit log, results + history. Final per movement =
  **lower of the two sides**; total **/15**; bands **0–5 / 6–10 / 11–15** — matches the official HMA sheet.
- **Fault vocab aligned to the official HMA reference sheet** — added shoulder
  "overlapping hands (hypermobility)"; dropped the `*_placeholder` key names.
- **Corrective Exercise Tracker feed** (`560a033`): captures **pain** (per side), **hypermobility**
  (per movement), and **OA** (per assessment) — the inputs that drive the Tracker's exercise
  selection — plus an **Export for Tracker** button (download/copy) that emits the Tracker's JSON
  record shape. Load via the Tracker's **Import → Paste JSON**. Verified end-to-end
  (Manual → Tracker → built exercise program). DB migrated in place (additive columns).
- **UI polish** (`06ea160`): reusable hover-"i" tooltips (helper prose moved off-page), collapsible
  fault qualifiers, upload-link moved into a modal, single centered "Complete Assessment" button,
  removed the duplicate OA checkbox from New Assessment, Title Case on all labels.
- **In-app webcam recorder** (`92f1a37`): Record button in the provider "Optional Review Video"
  block — live viewfinder (`getUserMedia`) → record (`MediaRecorder`) → Use/Retake → becomes the
  pending clip → **Save Video** uploads it. Requires HTTPS or localhost for camera access.
- **Admin password** reset off the shipped default.

### 🔲 Next (resume here)
- [x] **Merged to `main`** (2026-07-31) — the whole `hma-manual-ui-polish` stack fast-forwarded in.
- [ ] **Device-test the camera recorder** (provider laptop webcam + a phone) and the employee capture flow.
- [ ] Apply the owner's **UX notes** collected while testing the Manual app.
- [ ] (Optional) Add the same **live recorder to the employee upload page** (today it uses a native
      `capture="environment"` file input).
- [x] **Tracker feed v2** (2026-07-31) — both halves done:
  - Manual side: optional **Employee Details** section on New Assessment (first/last name, company,
    department, shift, location), collapsed by default so anonymous scoring stays one field. Stored
    as additive columns, carried into the export. Name fallback now splits on the LAST space and
    understands "Last, First".
  - Tracker side (separate repo `Dane-Lee/HMA-Correct-Exercise-Tracker`, branch
    `tracker-merge-on-reimport`, **not pushed**): re-importing an id you already hold now **updates**
    it instead of skipping. Scores/pain/hypermobility/OA/details refresh; **exercise plan,
    observations, quality focus, follow-up and re-test dates are preserved**. Notes refresh only
    while they are unedited since the last import. `npm test` covers the rules.
- [ ] **Verify Tracker feed v2 end-to-end** — score, export, import, build a plan, re-score, re-export,
      confirm the plan survives and the scores change. Then push the Tracker branch.

### 🔲 Deployment / hardening (before public use)
- [ ] Run HMA + HMA-Manual behind a **reverse proxy** with separate hostnames + HTTPS termination
      (also required for the in-app camera off localhost).
- [ ] Enable **provider MFA**.
- [ ] Move from single bootstrap password to **named provider accounts**.
- [ ] Complete **compliance review** for employee movement video handling and retention.
