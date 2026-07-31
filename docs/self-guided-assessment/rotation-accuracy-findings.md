# Rotation-Accuracy Findings — Trunk & Cervical

Tier-1 synthetic analysis of the two rotation movements' scoring gates. Asks one question:
**can the trunk-rotation and cervical-rotation verdicts be trusted in front of a provider yet?**
Short answer: not without the fixes below. The two gates fail for *opposite* reasons, and both
ride on the same `max()`-over-frames estimator bug.

Date: 2026-06-25. Owner: Dane. Status: analysis complete; follow-up fixes (a) and (b) have since landed (see below).

> **Implementation status (updated 2026-06-26, branch `rotation-accuracy`).** Two of this doc's
> recommendations are now in code:
> - **(a) Robust-peak reducers** replaced the raw `max()`/`min()`/span reducers across the feature
>   layer (`_robust_max` / `_robust_min` / `_robust_span` in
>   [extractors.py](../../api/app/services/scoring/extractors.py)). Where the analysis below says
>   "`max()` inflates ...", production now smooths-then-reduces. Thresholds still need re-tuning
>   against labeled data before the new absolute values can be trusted at the gate.
> - **(b) Ear-visibility yaw cue** is prototyped and proven against the confounds in
>   [models/cervical_ear_yaw_model.py](./models/cervical_ear_yaw_model.py), and is now logged as a
>   non-gating debug metric (`ear_visibility_asymmetry`) on every capture.
> - **(c) Tier-3 ground-truth capture protocol:** [tier3-capture-protocol.md](./tier3-capture-protocol.md).

> **What "Tier 1" means / what is NOT claimed here.** This is a *synthetic* analysis — geometric
> forward models that reproduce the exact production metrics, run against plausible parameter ranges.
> It quantifies *structural* risk (how the gate responds to depth-scale error, body type, noise, and
> compensations) without any captured video. It does **not** measure the real MediaPipe error on real
> people — that is Tier 3 (a ground-truth capture study), which this analysis is meant to scope.
> Reproducible models live in [./models/](./models/).

---

## 1. How the two gates actually work (and a correction)

Both metrics are computed in [api/app/services/scoring/extractors.py](../../api/app/services/scoring/extractors.py),
gated by [config/scoring_thresholds.yaml](../../config/scoring_thresholds.yaml), and turned into faults
in [api/app/services/scoring/movements/](../../api/app/services/scoring/movements/).

**Trunk rotation** — headline gate `trunk_rotation_angle_degrees < 45` →
fault `rotation_below_45_degrees`. The metric
([extractors.py:344-347](../../api/app/services/scoring/extractors.py#L344-L347), `max` at
[:386](../../api/app/services/scoring/extractors.py#L386)):

```
trunk_angle_frame = atan2(|Lshoulder_z − Rshoulder_z|, |Lshoulder_x − Rshoulder_x|)
trunk_rotation_angle_degrees = clamp(max_over_frames(...), 0, 90)
```

This **depends on MediaPipe z-depth** — its weakest output.

**Cervical rotation** — headline gate `chin_midline_clearance_ratio < 0.11` →
fault `chin_does_not_clear_clavicle_midline`. The metric
([extractors.py:321-324](../../api/app/services/scoring/extractors.py#L321-L324),
[:348](../../api/app/services/scoring/extractors.py#L348),
[:381](../../api/app/services/scoring/extractors.py#L381)):

```
nose_offset_frame = |nose_x − mid_shoulder_x| / |Lshoulder_x − Rshoulder_x|
chin_midline_clearance_ratio = clamp(max_over_frames(...), 0, 1.5)
```

> **Correction to an earlier note.** A prior session recorded that *both* rotations are derived from
> z-depth. That is wrong: **cervical uses no z** — it is pure 2D-x (lateral nose offset). Only the
> secondary `forward_head_ratio` setup-check uses z. This changes everything about how cervical should
> be validated: its problem is **validity**, not noise.

---

## 2. Trunk rotation — an accuracy problem (two large, uncalibrated biases)

The `atan2` formula is geometrically exact: a rigid shoulder bar rotated by θ projects to width
`L·cosθ` and depth `L·sinθ`, and `atan2(L·sinθ, L·cosθ) = θ`. It holds only if MediaPipe's z is
(a) on the same metric scale as x and (b) accurate. Neither is guaranteed.

### Bias 1 — systematic depth-scale `s` (analytic, undeniable)

Noiseless, the measured angle is `atan(s·tanθ)`, where `s` = MediaPipe's z-scale relative to x.
`s` is unobservable and varies with framing, distance, and body. Its effect on the *effective* gate:

| MediaPipe z-scale `s` | True rotation needed to read 45° |
|---|---|
| 0.70 (depth compressed) | **55°** |
| 0.85 | **49.6°** |
| 1.00 (nominal) | 45° |
| 1.15 (depth exaggerated) | **41°** |

A ±15% error in an unobservable quantity slides the real gate across a **14° band**. At s=0.85 a
worker who genuinely hits 45° reads 40.4° → **false fault**.

### Bias 2 — `max()` over frames inflates ~+9° from noise alone (a code bug)

`max` of a jittery per-frame series grabs the single most-inflated frame. At perfect scale (s=1.0),
a true 45° peak reads a mean of **54.1° (+9.1°)**. This is fixable with no new data — a robust peak
estimator removes it:

| Peak estimator | Reads true-45° as | Noise inflation |
|---|---|---|
| `max()` (current) | 54.1° | **+9.1°** |
| 90th percentile | 51.7° | +6.7° |
| 75th percentile | 48.9° | +3.9° |
| median (of hold) | 44.9° | **−0.1°** |

### Net effect — the two biases do not cleanly cancel

At nominal scale (s=1.0) the inflation dominates → the gate is **far too lenient**: a worker who
only reaches a true 40° is passed **91% of the time**, making the 45° gate nearly meaningless. Push
to s=0.7 and it flips to **false-faulting** a true-45° worker 35% of the time. Same movement, opposite
verdicts, driven entirely by uncontrolled quantities.

---

## 3. Cervical rotation — a validity problem (it measures displacement, not rotation)

The metric is dimensionless (cm/cm), so the camera cancels — that is *why* it is low-noise and
camera-robust, the opposite of trunk. But the geometry is `ratio = (d_nose/W)·sin(φ)`: it tracks
how far the nose slides sideways, which many non-rotation motions also produce.

### Confounds — how to pass with zero rotation (the headline)

| Build | Real rotation to pass | …or head-slide of | …or side-bend of |
|---|---|---|---|
| narrow (W=32cm) | 20.6° | **3.5 cm** | **8.8°** |
| mid (W=36cm) | 23.3° | 4.0 cm | 9.9° |
| broad (W=40cm) | 26.1° | 4.4 cm | 11° |

The metric **cannot distinguish a ~25° head turn from a 4 cm sideways head-slide or a 10°
ear-to-shoulder tilt** — exactly the compensation patterns a restricted worker uses. The feature is
blind to the cheat it most needs to catch.

### Body-type drift

The effective gate ranges **20.6°→26.1°** across builds (broad shoulders must rotate more to pass).
Smaller than trunk's 14° band, but still uncalibrated.

### Saturation

Because of the `sin`, sensitivity collapses at end-range:

| True angle φ | True degrees per 0.01 ratio step |
|---|---|
| 10° | 2.1° |
| 30° | 2.4° |
| 50° | 3.2° |
| 70° | 6.0° |
| 85° | **23.7°** |

Pass/fail is fine (the gate sits low on the range), but the metric is **useless for grading
severity** above ~50° — relevant when the REBA / safety-manager translation layer is built.

### The better signal is already extracted and thrown away

A pure head-slide does not change which ear is visible; a real rotation does.
`left_ear_visibility` / `right_ear_visibility` are already computed
([extractors.py:227-228](../../api/app/services/scoring/extractors.py#L227-L228)) but were never used.
Ear-visibility asymmetry (optionally with nose-to-ear geometry) is a far more direct yaw cue that
*rejects* the translation/side-bend confounds. This is the highest-leverage cervical fix.

> **Prototyped (b).** [models/cervical_ear_yaw_model.py](./models/cervical_ear_yaw_model.py) models
> ear visibility as a logistic of yaw and shows that at the *same* nose-x displacement the gate reads
> as "pass", ear-asymmetry is ~0.35 for a true ~23 deg turn but ~0 for a 4 cm head-slide or a 10 deg
> side-bend — and stays ~0 no matter how large the confound grows. It is now logged as a non-gating
> debug metric `ear_visibility_asymmetry` so real captures accumulate it for Tier-3 calibration.

---

## 4. The shared bug — `max()`-over-frames inflation generalizes

The same estimator inflates the cervical pass-metric (a true 26° reads as 34–49° depending on jitter
→ also too lenient) and, in fact, **most discriminating features**: `chin_midline_clearance_ratio`,
`lower_extremity_movement_ratio`, `cervical_motion_ratio` (a double-max ratio), `back_knee_depth_ratio`,
`bottom_hand_reach_ratio`, `top_hand_midline_ratio`, `body_rotation_ratio`, and `hand_distance_ratio`
(a `min`, biased the other way). Every `max`/`min`-over-frames reducer is noise-biased in one
direction. Fixing the reducer is a single, broad, no-data change — but it rescales every feature, so
the YAML thresholds must be re-tuned (the existing
[calibration.py](../../api/app/services/scoring/calibration.py) machinery is built for exactly that,
once labeled data exists).

---

## 5. Synthesis — the two gates fail for opposite reasons

| | **Trunk rotation** | **Cervical rotation** |
|---|---|---|
| Signal | shoulder **z-depth** | nose **x-offset** (2D) |
| Camera-robust? | ❌ scale `s` uncontrolled | ✅ cm/cm cancels |
| Per-frame noise | **high** | low |
| Core failure | **accuracy** — `s` warps gate ±7°; verdicts swing with framing | **validity** — credits slide/side-bend as rotation |
| Body-type drift | via `s` | effective gate 20.6→26.1° |
| Shared bug | `max()` inflates +9° | `max()` inflates the ratio |
| Fixable by calibration alone? | partly (need `s`) | **no** — needs a different feature (ears) |

**Throughline:** both share the `max()` inflation (a no-data code fix). Beyond that, trunk needs
*calibration* (pin down `s`); cervical needs a *new feature* (ear-based yaw) — calibration cannot fix
a feature that measures the wrong thing.

---

## 6. Recommended next actions

**No new data required:**
1. ✅ **DONE — Replaced `max()`/`min()` reducers with a robust peak** (edge-padded rolling median,
   then reduce) across the feature layer (`_robust_max` / `_robust_min` / `_robust_span`). Removes the
   +9° trunk inflation and the cervical equivalent. Threshold re-tuning still pending labeled data.
2. ✅ **DONE — Prototyped an ear-visibility-asymmetry cervical feature** and showed it rejects the
   head-slide / side-bend confounds the nose-x metric cannot
   ([models/cervical_ear_yaw_model.py](./models/cervical_ear_yaw_model.py)); logged as the non-gating
   debug metric `ear_visibility_asymmetry`. Whether it augments or replaces the nose-x gate is a
   Tier-3 decision.

**Needs a capture session (Tier 3) — now scoped by this analysis:**
3. **Trunk:** goniometer / floor-marked angles concentrated in the **40–55° band** (where the gray
   zone lives), to pin down `s`. Ground-truth must be tight (±2–3°) because the gate is so
   scale-sensitive.
4. **Cervical:** include **deliberate compensation trials** (pure head-slide, pure side-bend, with no
   rotation) to measure real confound rejection — for both the current metric and any ear-based
   replacement.

---

## 7. Open questions for Dane (clinical)

- The cervical gate trips at only ~21–26° of true rotation, against a normal ROM of ~70–80°. Is
  "clears the clavicle midline" *intended* to catch only severe restriction, or should the gate sit
  higher? (If higher, the saturation problem starts to bite.)
- For trunk, is a binary 45° pass/fail the right clinical construct, or do you eventually want a
  graded angle (which makes accuracy/calibration even more important)?

---

## 8. Reproducing

Three standalone models (numpy only; run with the repo venv):

- [./models/trunk_rotation_risk_model.py](./models/trunk_rotation_risk_model.py) — sections A (scale
  bias), B (gate misclassification), C0/C (max inflation), D (jitter sensitivity), E (estimator
  comparison).
- [./models/cervical_rotation_validity_model.py](./models/cervical_rotation_validity_model.py) —
  sections A (transfer curve), B (confounds), C (saturation), D (shared max inflation).
- [./models/cervical_ear_yaw_model.py](./models/cervical_ear_yaw_model.py) — the (b) prototype:
  A (ear-asymmetry transfer curve), B/B2 (confound rejection vs nose-x), C (separability under
  visibility noise), D (robustness to the sharpness/noise the Tier-3 capture would pin down).

```
.venv/Scripts/python.exe docs/self-guided-assessment/models/trunk_rotation_risk_model.py
.venv/Scripts/python.exe docs/self-guided-assessment/models/cervical_rotation_validity_model.py
.venv/Scripts/python.exe docs/self-guided-assessment/models/cervical_ear_yaw_model.py
```

Key assumptions (swept, not asserted as truth): shoulder width 0.16 normalized / 32–40 cm; nose
2D-x jitter σ≈0.005, shoulder z jitter σ≈0.02; 8 near-peak frames feeding `max()`; nose 10 cm ahead
of the cervical axis, 23 cm above the side-bend axis. The unknowns these stand in for (`s`, the real
σ, anthropometry) are exactly what Tier 3 would measure.
