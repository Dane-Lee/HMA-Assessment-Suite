"""
Tier-1 validity model for the single-camera CERVICAL-ROTATION gate.

Reproduces the EXACT production metric
(api/app/services/scoring/extractors.py lines 321-324, 348, 381):

    nose_offset_frame = |nose_x - mid_shoulder_x| / (|Lsh_x - Rsh_x| + 1e-6)
    chin_midline_clearance_ratio = clamp(max_over_frames(nose_offset_frame), 0, 1.5)
    FAULT "chin_does_not_clear_clavicle_midline" if ratio < 0.11   (scoring_thresholds.yaml)

Unlike trunk rotation this uses NO z — it is pure 2D-x, so it is camera-robust and
low-noise. The risk is VALIDITY, not noise: does lateral nose displacement actually
encode axial neck-rotation angle phi?

Geometry (top-down, vertical rotation axis through the neck):
    nose sits d_nose cm in front of the rotation axis.
    rotate head by phi  ->  nose_x displacement = d_nose * sin(phi)   (NOT phi)
    ratio = d_nose * sin(phi) / W      (W = biacromial shoulder width, cm)
          = (d_nose / W) * sin(phi)
Three consequences fall out of that sin():
  (1) sin() saturates -> near end-range the metric can't grade severity.
  (2) (d_nose/W) is an anthropometric constant -> the SAME true angle maps to
      different ratios for different body types -> the effective gate angle drifts.
  (3) ratio responds to ANY lateral nose displacement: pure sideways head
      translation or lateral side-bend inflate it identically to real rotation.
The metric is dimensionless cm/cm, so the camera cancels (that's why it's stable) --
but it measures lateral displacement, not rotation. Stable != valid.
"""
from __future__ import annotations

import math
import numpy as np

GATE = 0.11          # chin_midline_clearance_ratio_min (scoring_thresholds.yaml)
EPSILON = 1e-6

# ---- anthropometry (cm) ----
D_NOSE = 10.0        # horizontal nose-tip distance ahead of the cervical rotation axis
H_NOSE = 23.0        # vertical nose distance above the cervicothoracic side-bend axis (~C7/T1)
W_BY_BUILD = {"narrow (W=32)": 32.0, "mid (W=36)": 36.0, "broad (W=40)": 40.0}

# ---- 2D-x landmark jitter (the nose/shoulder x are MediaPipe's well-calibrated axis) ----
SIGMA_X = 0.005      # per-landmark x jitter, normalized image units
SHOULDER_W_NORM = 0.16
N_PEAK_FRAMES = 8
M_TRIALS = 6000


def ratio_from_angle(phi_deg: float, d_nose=D_NOSE, w=36.0) -> float:
    return (d_nose / w) * math.sin(math.radians(phi_deg))


def angle_for_ratio(ratio: float, d_nose=D_NOSE, w=36.0) -> float:
    arg = ratio * w / d_nose
    return math.degrees(math.asin(arg)) if arg <= 1.0 else float("nan")


def main() -> None:
    rng = np.random.default_rng(20260624)
    print("=" * 80)
    print("CERVICAL-ROTATION GATE (ratio < 0.11) — SYNTHETIC VALIDITY MODEL")
    print("=" * 80)
    print(f"d_nose={D_NOSE}cm  h_nose={H_NOSE}cm  builds={list(W_BY_BUILD)}  gate ratio={GATE}")
    print("metric = (d_nose/W)*sin(phi); NO z, camera-robust, but encodes displacement not angle")

    # ---- A. Transfer curve: ratio vs true angle, and where the gate lands per build ----
    angles = [10, 20, 26, 30, 45, 60, 75, 90]
    print("\n[A] TRANSFER CURVE  ratio = (d_nose/W)*sin(phi)   [pass when ratio >= 0.11]")
    print("    true phi:  " + "".join(f"{a:>7}" for a in angles))
    for label, w in W_BY_BUILD.items():
        cells = "".join(f"{ratio_from_angle(a, D_NOSE, w):>7.3f}" for a in angles)
        print(f"    {label:<14}{cells}")
    print("\n    -> EFFECTIVE GATE: true neck angle at which each build first reads 'pass':")
    for label, w in W_BY_BUILD.items():
        print(f"       {label:<14} clears 0.11 at phi = {angle_for_ratio(GATE, D_NOSE, w):>4.1f} deg")
    print("    (same gate, different verdict by body type — broad shoulders must rotate MORE)")

    # ---- B. CONFOUNDS: non-rotation motions that satisfy the gate identically ----
    print("\n[B] CONFOUNDS — how to PASS the gate with ZERO real rotation")
    print("    motion that alone reaches ratio = 0.11:")
    for label, w in W_BY_BUILD.items():
        t_cm = GATE * w                                   # pure lateral head slide
        sin_b = GATE * w / H_NOSE                          # lateral side-bend
        beta = math.degrees(math.asin(sin_b)) if sin_b <= 1 else float("nan")
        phi_true = angle_for_ratio(GATE, D_NOSE, w)
        print(f"    {label:<14} real-rotation {phi_true:>4.1f} deg  ==  "
              f"head-slide {t_cm:>4.1f} cm  ==  side-bend {beta:>4.1f} deg")
    print("    (a few cm of sideways head shift, or a slight ear-to-shoulder tilt, = 'passed')")

    # ---- C. SATURATION: discrimination collapses at end-range ----
    print("\n[C] SATURATION — true degrees needed to move the ratio by one 0.01 step")
    print("    (sensitivity d(ratio)/d(phi) = (d_nose/W)*cos(phi); W=36)")
    for phi in (10, 30, 50, 70, 85):
        sens = (D_NOSE / 36.0) * math.cos(math.radians(phi))   # per radian
        deg_per_001 = 0.01 / (sens * math.pi / 180.0)
        print(f"    at phi={phi:>2} deg:  {deg_per_001:>4.1f} deg of true rotation per 0.01 ratio")
    print("    (near end-range one ratio step spans many degrees -> can't grade severity)")

    # ---- D. SHARED max()+jitter inflation on the ratio (same estimator bug as trunk) ----
    print("\n[D] max()+JITTER inflation of the ratio (mid build W_norm=0.16, true phi=26 -> ratio~0.11)")
    true_ratio = ratio_from_angle(26.0, D_NOSE, 36.0)
    def sim_ratio_peak(true_ratio, sigma_x):
        best = 0.0
        for _ in range(N_PEAK_FRAMES):
            nose = true_ratio * SHOULDER_W_NORM + rng.normal(0, sigma_x)
            midsh = rng.normal(0, sigma_x / math.sqrt(2))
            sw = SHOULDER_W_NORM + rng.normal(0, sigma_x / math.sqrt(2))
            best = max(best, abs(nose - midsh) / (abs(sw) + EPSILON))
        return best
    for sx in (0.003, 0.005, 0.008):
        vals = np.array([sim_ratio_peak(true_ratio, sx) for _ in range(M_TRIALS)])
        eff_angle = angle_for_ratio(min(vals.mean(), (D_NOSE/36.0)), D_NOSE, 36.0)
        print(f"    sigma_x={sx}:  measured ratio mean={vals.mean():.3f} (true {true_ratio:.3f}, "
              f"+{vals.mean()-true_ratio:.3f})  ~reads as phi={eff_angle:.0f} deg")
    print("    (max() inflates the pass-metric too -> the gate is also too LENIENT, like trunk)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
