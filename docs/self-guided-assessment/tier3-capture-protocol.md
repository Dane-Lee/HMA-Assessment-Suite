# Tier-3 Ground-Truth Capture Protocol — Trunk & Cervical Rotation

A concrete capture study to replace the *synthetic* assumptions in
[rotation-accuracy-findings.md](./rotation-accuracy-findings.md) with measured ground truth.
Tier-1 (synthetic) quantified the **structural** risk; it could not measure the real numbers.
This protocol measures them, against a goniometer / inclinometer reference, using the **exact
production single-phone rig** — so the result is directly the error of what ships.

Date: 2026-06-26. Owner: Dane (ergonomist). Status: protocol drafted, not yet run.

---

## 0. What this study has to decide

Each item below is an open quantity from the Tier-1 analysis. The study exists to pin it down.

| # | Unknown (from Tier-1) | Decision it gates |
|---|---|---|
| U1 | MediaPipe depth-scale `s` (warps the trunk 45° gate across a ~14° band) | Re-tune `rotation_angle_min_degrees`, or add per-capture `s` normalization |
| U2 | Real per-frame trunk noise σ (drives the `max()` inflation, now mitigated by `_robust_max`) | Confirm the robust reducer actually removes the inflation on real video |
| U3 | Cervical construct validity — does `chin_midline_clearance_ratio` track true yaw across 0–80°? | Keep / re-gate / grade-vs-binary the cervical metric |
| U4 | **Confound rejection** — how much do real head-slide / side-bend inflate each metric? | Whether the ear cue must **augment or replace** nose-x |
| U5 | Ear-model parameters `k` (visibility-vs-yaw sharpness), neutral baseline, σ_vis | Turn `ear_visibility_asymmetry` from prototype into a real gate |
| U6 | Body-type drift (effective gate vs biacromial width) | Whether to normalize gates by build |

**Success = a labeled dataset large enough to (a) fit `s`, (b) re-tune the two YAML thresholds via
[calibration.py](../../api/app/services/scoring/calibration.py), and (c) plot confound-rejection
curves for nose-x vs ear-asymmetry.**

---

## 1. Equipment

- **The production rig, unchanged.** Single phone on a prop at the height/distance the self-guided
  flow instructs (replicate `config/movements.json` `camera_setup_self` once written). The whole
  point is to measure the shipped path, so do not "improve" the camera.
- **Trunk axial-rotation reference (pick one, ±2–3° target):**
  - *Overhead reference camera* (phone on ceiling mount / tripod boom) marking the shoulder-line
    angle relative to the floor — clean ground truth for axial rotation. **Not** fed to scoring; it
    is the ruler, not an input. Or
  - *Trunk inclinometer / IMU* (e.g., a phone IMU app strapped over the sternum or across the
    shoulders) logging yaw. Or
  - *Floor-marked foot/torso angles*: tape rays at 0/30/40/45/50/55/60° from the camera axis; subject
    rotates shoulders to the marked ray with a fixed pelvis.
- **Cervical yaw reference (pick one, ±2–3° target):**
  - *CROM device* (cervical range-of-motion goniometer) — the clinical standard; Dane has access. Or
  - *Head-mounted IMU* (clip a phone/earbud IMU to a headband) logging yaw. Or
  - *Overhead reference camera* tracking a short head-mounted pointer.
- **Tape measure** (head-slide distance, cm) and a **wall-mounted protractor / inclinometer** for
  side-bend angle.
- **Metronome / timer** for consistent ~1.5–2 s end-range holds (the production capture samples a few
  near-peak frames; a held pose is what the reducer sees).

> Ground-truth tightness matters more for trunk than cervical: the trunk gate is so scale-sensitive
> that a ±5° reference error would swamp the effect we are trying to measure. Aim ±2–3°.

---

## 2. Subjects

- **6–10 subjects** spanning the anthropometric range that drives U6: narrow / mid / broad biacromial
  width (≈32 / 36 / 40 cm), both sexes, a range of heights. Record each subject's measured shoulder
  width and nose-to-C7 offsets (the Tier-1 models assumed `d_nose≈10 cm`, `h_nose≈23 cm` — measure them).
- **Both sides** for every movement (the metric and the faults are side-aware).
- This yields well over the **≥20 labeled examples with ≥5 disagreements** that `calibration.py`
  needs to re-tune a threshold, with margin for a held-out test split.

Consent & privacy: this is a **controlled internal calibration study**, not the self-guided product
flow. Unlike production (which persists no raw video), you will want to **retain** these clips to
re-run analysis as the metric changes — so use an explicit study-specific consent and a defined
retention window. Keep this dataset out of the production storage path.

---

## 3. Protocol A — Trunk rotation (targets U1, U2, U6)

For each subject, each side:

1. **Calibration ladder.** Rotate the shoulders to each reference target in turn —
   **30, 40, 45, 50, 55, 60°** — hold ~2 s at each, pelvis fixed (mark feet/hips). Concentrate
   density in the **40–55° gray zone** where the gate lives. 2 reps per target.
2. **Free max.** One slow rotation to comfortable end-range, held — to see the metric's top end.
3. **Noise probe.** One trial holding a *single* target (45°) for ~6 s without moving — isolates
   per-frame jitter so U2 (and the `_robust_max` fix) can be checked directly: raw `max()` vs
   `_robust_max` over a truly static pose should now read nearly the same.

Log, per trial: reference angle, side, and the full `debug_metrics` (already includes
`trunk_rotation_angle_degrees`, `cervical_motion_ratio`, etc.).

**Analysis:** plot measured `trunk_rotation_angle_degrees` vs reference → fit `s` from
`measured = atan(s·tan(true))`; check whether `s` is stable within subject / across build; quantify
residual noise; then re-tune `trunk_rotation.rotation_angle_min_degrees` (or add `s`-normalization).

---

## 4. Protocol B — Cervical rotation (targets U3, U4, U5, U6)

For each subject, each side:

1. **Rotation ladder (validity, U3).** Head turn to **10, 20, 30, 45, 60, 75°** by the cervical
   reference, neutral posture otherwise, hold ~1.5 s, 2 reps each. Spans below and above the ~21–26°
   the current gate trips at, into the saturation zone.
2. **Compensation trials (confound rejection, U4) — the headline.** With **zero head rotation**:
   - *Pure head-slide:* translate the head laterally **2, 4, 6 cm** (tape-measured), eyes forward.
   - *Pure side-bend:* ear-to-shoulder tilt **10, 20, 30°** (inclinometer), no rotation.
   - *Combined cheat:* a restricted-worker-style slide + small bend together.
   Hold each ~1.5 s, 2 reps.
3. **Forward-head setup probe.** One trial with deliberate forward-head / rounded-shoulder posture
   (exercises `forward_head_ratio`, the one cervical sub-metric that uses z).

Log, per trial: reference yaw (or "0 — slide 4 cm" / "0 — bend 20°"), side, and full `debug_metrics`
— now including **`ear_visibility_asymmetry`** and `ear_visibility_asymmetry_norm` alongside
`chin_midline_clearance_ratio`.

**Analysis:**
- **Transfer curve (U3):** `chin_midline_clearance_ratio` vs true yaw — confirm/deny the `sin`
  saturation and where the 0.11 gate really sits per build (U6).
- **Confound rejection (U4):** for the compensation trials, tabulate how far each metric moves with
  *zero* rotation. The Tier-1 prediction: nose-x climbs with slide/bend (false rotation), ear-asymmetry
  stays flat. Plot ROC for "real yaw present vs compensation" for each metric. This is the
  augment-vs-replace decision.
- **Ear-model calibration (U5):** fit `k`, baseline, and σ_vis in
  [models/cervical_ear_yaw_model.py](./models/cervical_ear_yaw_model.py) to the measured
  visibility-vs-yaw points; replace the assumed values; re-confirm the separation margin on real data.

---

## 5. Outputs

1. **Labeled CSV** — one row per trial: subject id, build measurements, movement, side, reference
   ground truth, trial type (ladder / slide / bend / forward-head), and every `debug_metrics` field.
2. **Fitted `s`** (trunk) with its stability range, and the re-tuned trunk threshold.
3. **Confound-rejection curves** for nose-x vs ear-asymmetry, and the augment-or-replace call for U4.
4. **Calibrated ear-model constants**, feeding a follow-up decision on promoting
   `ear_visibility_asymmetry` from debug metric to a scored fault.
5. **Re-tuned `config/scoring_thresholds.yaml`** via `calibration.py`, now that the robust reducer
   has rescaled the features.

---

## 6. Out of scope / sequencing

- This protocol does **not** change the production privacy posture; it is a separate, consented
  calibration capture. The shipped self-guided flow still persists no raw video.
- Run **Protocol A and B in one session per subject** to amortize setup.
- Trunk and cervical analyses are independent — whichever reference gear is ready first can go first.
