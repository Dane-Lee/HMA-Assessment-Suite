"""
Tier-1 PROTOTYPE: an ear-visibility-asymmetry cervical-yaw feature, and proof that it
rejects the two confounds the production nose-x metric cannot.

Companion to cervical_rotation_validity_model.py, which showed the production gate
(chin_midline_clearance_ratio = (d_nose/W)*sin(phi)) is *valid only if the lateral nose
displacement came from rotation* - but a pure sideways HEAD-SLIDE or a lateral SIDE-BEND
produces the identical displacement, so the gate credits both as rotation.

This model proposes a different signal, already extracted but unused in production
(api/app/services/scoring/extractors.py:227-228 -> left_ear_visibility / right_ear_visibility),
and shows it separates true axial yaw from those two confounds.

WHY EAR VISIBILITY ENCODES YAW (and displacement does not)
----------------------------------------------------------
MediaPipe reports a per-landmark `visibility` in [0,1] that rises when a landmark faces
the camera and falls as it rotates out of view / self-occludes. The two ears sit on the
lateral axis of the head:
  * Axial yaw (turning the head left/right) swings one ear toward the camera and the other
    behind the head -> the visibilities split apart. This is the ONLY one of the three
    motions that changes which ear faces the camera.
  * A pure lateral head-slide is a translation: head orientation is unchanged, so both ears
    keep facing the same way -> asymmetry stays ~0 (the nose-x metric, by contrast, moves
    with the slide).
  * A pure side-bend (ear-to-shoulder roll about the fore-aft axis) tips the ears vertically
    but does not change their facing angle to the camera -> asymmetry stays ~0 to first order
    (the nose-x metric moves, because the nose swings laterally about the lower spine).

So ear-visibility asymmetry is a *yaw-specific* cue; lateral nose displacement is not.

MODEL
-----
Each ear's facing angle to the camera changes by +/-phi under yaw. Model visibility as a
logistic of that facing angle (monotone, saturating - matching how `visibility` behaves):

    v_toward = sigmoid(a + k*sin(phi))     # ear rotating toward the camera
    v_away   = sigmoid(a - k*sin(phi))     # ear rotating behind the head
    asym     = |v_toward - v_away|          # the yaw cue (signed version keeps direction)

`a` sets the neutral baseline (both ears ~0.85 head-on); it CANCELS in the asymmetry.
`k` sets how sharply visibility responds to yaw. Both are swept, not asserted.
Under the two confounds phi stays 0, so asym is driven only by visibility noise.

Nothing here is the production metric yet - it is a feasibility proof to justify a Tier-3
capture that measures real ear-visibility-vs-angle so `k`, the baseline, and the noise can
be pinned down against goniometer ground truth.
"""
from __future__ import annotations

import math
import numpy as np

# ---- production gate + anthropometry, shared with cervical_rotation_validity_model.py ----
GATE = 0.11          # chin_midline_clearance_ratio_min (scoring_thresholds.yaml)
D_NOSE = 10.0        # nose-tip distance ahead of the cervical (yaw) axis, cm
H_NOSE = 23.0        # nose distance above the cervicothoracic (side-bend) axis, cm
W_MID = 36.0         # biacromial width, cm (mid build)

# ---- ear-visibility model ----
A_BASE = math.log(0.85 / 0.15)   # logistic bias -> ~0.85 visibility for both ears head-on
K_VIS = 3.3                       # nominal visibility-vs-yaw sharpness
SIGMA_VIS = 0.03                  # per-landmark visibility jitter (MediaPipe is noisy here)
N_PEAK_FRAMES = 8
M_TRIALS = 8000


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def ear_asym(phi_deg: float, k: float = K_VIS) -> float:
    """Noiseless |v_toward - v_away| at yaw phi (baseline a cancels)."""
    s = math.sin(math.radians(phi_deg))
    return abs(sigmoid(A_BASE + k * s) - sigmoid(A_BASE - k * s))


def nose_ratio_yaw(phi_deg: float, w: float = W_MID) -> float:
    return (D_NOSE / w) * math.sin(math.radians(phi_deg))


def nose_ratio_slide(t_cm: float, w: float = W_MID) -> float:
    return t_cm / w


def nose_ratio_sidebend(beta_deg: float, w: float = W_MID) -> float:
    return (H_NOSE / w) * math.sin(math.radians(beta_deg))


def gate_matched_inputs() -> tuple[float, float, float]:
    """The (yaw, slide, side-bend) that each independently drive nose-x to exactly the gate."""
    phi = math.degrees(math.asin(GATE * W_MID / D_NOSE))
    t = GATE * W_MID
    beta = math.degrees(math.asin(GATE * W_MID / H_NOSE))
    return phi, t, beta


def main() -> None:
    rng = np.random.default_rng(20260626)
    print("=" * 84)
    print("CERVICAL EAR-VISIBILITY YAW FEATURE - CONFOUND-REJECTION PROOF (prototype)")
    print("=" * 84)
    print(f"baseline visibility={sigmoid(A_BASE):.2f}  k={K_VIS}  sigma_vis={SIGMA_VIS}  gate(nose-x)={GATE}")

    # ---- A. Transfer curve: the feature is monotone in yaw and zero at neutral ----
    print("\n[A] EAR-ASYMMETRY TRANSFER CURVE  asym = |v_toward - v_away|  (noiseless)")
    print("    true yaw phi:   " + "".join(f"{a:>7}" for a in (0, 10, 20, 30, 45, 60)))
    print("    v_toward:       " + "".join(f"{sigmoid(A_BASE + K_VIS*math.sin(math.radians(a))):>7.2f}" for a in (0, 10, 20, 30, 45, 60)))
    print("    v_away:         " + "".join(f"{sigmoid(A_BASE - K_VIS*math.sin(math.radians(a))):>7.2f}" for a in (0, 10, 20, 30, 45, 60)))
    print("    asymmetry:      " + "".join(f"{ear_asym(a):>7.3f}" for a in (0, 10, 20, 30, 45, 60)))
    print("    (monotone, 0 at neutral - a direct yaw cue, unlike saturating sin-displacement)")

    # ---- B. THE HEADLINE: at the SAME gate-matched displacement, ears tell the 3 apart ----
    phi, t, beta = gate_matched_inputs()
    print("\n[B] CONFOUND REJECTION - three motions tuned so NOSE-X reads identically (= gate 0.11)")
    print(f"    {'motion':<22}{'nose-x ratio':>14}{'ear-asym':>12}   verdict by each feature")
    rows = [
        (f"real yaw {phi:.0f} deg", nose_ratio_yaw(phi), ear_asym(phi)),
        (f"head-slide {t:.1f} cm", nose_ratio_slide(t), ear_asym(0.0)),
        (f"side-bend {beta:.0f} deg", nose_ratio_sidebend(beta), ear_asym(0.0)),
    ]
    for name, nose, asym in rows:
        print(f"    {name:<22}{nose:>14.3f}{asym:>12.3f}   "
              f"nose-x: PASS(rotated)   ears: {'YAW' if asym > 0.12 else 'no-yaw'}")
    print("    -> nose-x is identical for all three (cannot tell rotation from the 2 cheats);")
    print("       ear-asymmetry is high ONLY for true yaw, ~0 for both confounds.")

    # ---- B2. ...and the rejection does NOT degrade as the confound grows ----
    print("\n[B2] ROBUSTNESS: grow each confound well past the gate - nose-x runs away, ears stay flat")
    print(f"    {'confound size':<22}{'nose-x ratio':>14}{'ear-asym':>12}")
    for t_cm in (4.0, 8.0, 12.0):
        print(f"    head-slide {t_cm:>4.1f} cm      {nose_ratio_slide(t_cm):>14.3f}{ear_asym(0.0):>12.3f}")
    for b in (10, 20, 30):
        print(f"    side-bend  {b:>4} deg     {nose_ratio_sidebend(b):>14.3f}{ear_asym(0.0):>12.3f}")
    print("    (a worker can slide 12 cm or bend 30 deg and 'pass' nose-x; ear-asym never moves)")

    # ---- C. Separability under visibility noise (Monte Carlo over the max()-peak reducer) ----
    def peak_asym(phi_deg: float) -> float:
        s = math.sin(math.radians(phi_deg))
        vt = sigmoid(A_BASE + K_VIS * s)
        va = sigmoid(A_BASE - K_VIS * s)
        best = 0.0
        for _ in range(N_PEAK_FRAMES):
            nt = vt + rng.normal(0, SIGMA_VIS)
            na = va + rng.normal(0, SIGMA_VIS)
            best = max(best, abs(nt - na))
        return best

    print(f"\n[C] SEPARABILITY UNDER NOISE (sigma_vis={SIGMA_VIS}, peak over {N_PEAK_FRAMES} frames, {M_TRIALS} trials)")
    scenarios = {
        f"real yaw {phi:.0f} deg (at gate)": phi,
        "head-slide (phi=0)": 0.0,
        "side-bend (phi=0)": 0.0,
    }
    stats = {}
    for label, p in scenarios.items():
        vals = np.array([peak_asym(p) for _ in range(M_TRIALS)])
        stats[label] = vals
        print(f"    {label:<28} ear-asym  mean={vals.mean():.3f}  p05={np.percentile(vals,5):.3f}  p95={np.percentile(vals,95):.3f}")
    yaw_key = next(iter(scenarios))
    confound_max = max(stats["head-slide (phi=0)"].max(), stats["side-bend (phi=0)"].max())
    yaw_min = stats[yaw_key].min()
    thr = 0.5 * (confound_max + yaw_min)
    print(f"    -> threshold {thr:.3f} separates true yaw from BOTH confounds with margin "
          f"{yaw_min - confound_max:+.3f} (worst-case yaw - worst-case confound)")
    print("    (note: the max()-peak reducer biases the confounds UP off zero - use the robust")
    print("     reducer _robust_max from extractors.py here too, same lesson as the trunk fix)")

    # ---- D. Robustness across the two unknowns the Tier-3 capture would pin down ----
    print("\n[D] ROBUSTNESS of the gate-margin to k (visibility sharpness) and sigma_vis")
    print(f"    {'k \\ sigma':<10}" + "".join(f"{sv:>10}" for sv in (0.02, 0.04, 0.06)))
    for k in (2.5, 3.3, 4.5):
        cells = []
        for sv in (0.02, 0.04, 0.06):
            def pk(phi_deg, _k=k, _sv=sv):
                s = math.sin(math.radians(phi_deg))
                vt, va = sigmoid(A_BASE + _k * s), sigmoid(A_BASE - _k * s)
                return max(abs((vt + rng.normal(0, _sv)) - (va + rng.normal(0, _sv))) for _ in range(N_PEAK_FRAMES))
            yaw_vals = np.array([pk(phi) for _ in range(2000)])
            conf_vals = np.array([pk(0.0) for _ in range(2000)])
            margin = np.percentile(yaw_vals, 5) - np.percentile(conf_vals, 95)
            cells.append(f"{margin:>+10.3f}")
        print(f"    k={k:<8}" + "".join(cells))
    print("    (p05[yaw] - p95[confound]; positive => separable. Holds across plausible params,")
    print("     even at the 23 deg gate-borderline. Bigger yaw separates further.)")

    print("\n" + "=" * 84)
    print("CONCLUSION: ear-visibility asymmetry is a yaw-specific cue that rejects the head-slide")
    print("and side-bend confounds the nose-x gate cannot. Additive next step (done): log it as a")
    print("debug metric on real captures; Tier-3 capture then calibrates k/baseline/noise vs a")
    print("goniometer and decides whether it augments or replaces chin_midline_clearance_ratio.")
    print("=" * 84)


if __name__ == "__main__":
    main()
