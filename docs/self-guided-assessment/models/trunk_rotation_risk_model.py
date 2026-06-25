"""
Tier-1 synthetic risk model for the single-camera TRUNK-ROTATION 45 deg gate.

Reproduces the EXACT metric the production extractor uses
(api/app/services/scoring/extractors.py lines 344-347 + 386):

    trunk_angle_frame = atan2(|Lsh_z - Rsh_z|, |Lsh_x - Rsh_x| + 1e-6)
    trunk_rotation_angle_degrees = clamp(max_over_frames(trunk_angle_frame), 0, 90)
    FAULT "rotation_below_45_degrees" if trunk_rotation_angle_degrees < 45

Question: given that MediaPipe's z is only "roughly" the same scale as x (scale
factor s) and is jittery (per-landmark noise sigma), how often does the gate
mislabel a worker whose TRUE peak trunk rotation is known?

Forward model: shoulders = rigid horizontal bar (width W) rotating by true angle
theta about the vertical spine axis. In normalized image coords with the camera
on the +z axis:
    x_L = +r cos(theta)              z_L = +r sin(theta) * s
    x_R = -r cos(theta)              z_R = -r sin(theta) * s     (r = W/2)
Noiseless, s=1:  atan2(|dz|,|dx|) = atan2(2r sin, 2r cos) = theta  (exact recovery).
Noiseless, s!=1: measured = atan(s * tan(theta))   <-- pure systematic bias.
Then add Gaussian landmark noise and the max-over-frames the real code applies.
"""
from __future__ import annotations

import math
import numpy as np

GATE_DEG = 45.0
EPSILON = 1e-6

# ---- defaults (swept below; single-point numbers are NOT claimed as truth) ----
SHOULDER_W   = 0.16    # shoulder width in normalized image-width units (full/upper body framing)
SIGMA_X      = 0.006   # per-landmark x jitter (x is the well-calibrated axis -> small)
SIGMA_Z      = 0.020   # per-landmark z jitter (MediaPipe's weakest output -> larger)
N_PEAK_FRAMES = 8      # frames near the held peak that feed max() (~1.3 s hold @ 6 fps)
SWAY_DEG     = 1.0     # residual sway at the held peak (kept small so max-inflation = noise, not biomechanics)
M_TRIALS     = 6000    # Monte Carlo trials per cell


def analytic_measured(true_deg: float, z_scale: float) -> float:
    """Noiseless measured angle: atan(s * tan(theta)). The systematic-bias curve."""
    t = math.radians(true_deg)
    return math.degrees(math.atan2(z_scale * math.sin(t), math.cos(t)))


def simulate_measured_peak(true_peak_deg, *, shoulder_width=SHOULDER_W, z_scale=1.0,
                           sigma_x=SIGMA_X, sigma_z=SIGMA_Z, n_peak_frames=N_PEAK_FRAMES,
                           sway_deg=SWAY_DEG, rng) -> float:
    r = shoulder_width / 2.0
    best = 0.0
    for _ in range(n_peak_frames):
        theta = math.radians(true_peak_deg + rng.normal(0.0, sway_deg))
        xL = r * math.cos(theta) + rng.normal(0.0, sigma_x)
        xR = -r * math.cos(theta) + rng.normal(0.0, sigma_x)
        zL = r * math.sin(theta) * z_scale + rng.normal(0.0, sigma_z)
        zR = -r * math.sin(theta) * z_scale + rng.normal(0.0, sigma_z)
        dx = abs(xL - xR) + EPSILON
        dz = abs(zL - zR)
        ang = math.degrees(math.atan2(dz, dx))
        if ang > best:                       # the real code's max() over frames
            best = ang
    return min(best, 90.0)


def p_flag(true_deg, *, z_scale, sigma_z=SIGMA_Z, sigma_x=SIGMA_X,
           shoulder_width=SHOULDER_W, n=N_PEAK_FRAMES, trials=M_TRIALS, rng):
    """P(gate flags 'rotation_below_45') and mean/std of the measured peak."""
    vals = np.fromiter(
        (simulate_measured_peak(true_deg, shoulder_width=shoulder_width, z_scale=z_scale,
                                sigma_x=sigma_x, sigma_z=sigma_z, n_peak_frames=n, rng=rng)
         for _ in range(trials)),
        dtype=float, count=trials,
    )
    return float(np.mean(vals < GATE_DEG)), float(vals.mean()), float(vals.std())


def gray_zone(z_scale, *, sigma_z=SIGMA_Z, rng, lo=0.10, hi=0.90):
    """True-angle band where P(flag) falls from hi to lo (the 'coin-flip' region)."""
    grid = np.arange(20.0, 75.01, 0.5)
    ps = np.array([p_flag(d, z_scale=z_scale, sigma_z=sigma_z, trials=2500, rng=rng)[0] for d in grid])
    def cross(level):
        below = np.where(ps <= level)[0]
        return float(grid[below[0]]) if len(below) else float('nan')
    return cross(hi), cross(lo)   # (true angle where P drops below 0.9, below 0.1)


def main() -> None:
    rng = np.random.default_rng(20260624)
    z_scales = [0.70, 0.85, 1.00, 1.15]
    decision_angles = [40, 45, 48, 50, 55]
    bias_angles = [35, 40, 45, 50, 55, 60]

    print("=" * 78)
    print("TRUNK-ROTATION 45 deg GATE — SYNTHETIC RISK MODEL")
    print("=" * 78)
    print(f"shoulder_w={SHOULDER_W}  sigma_x={SIGMA_X}  sigma_z={SIGMA_Z}  "
          f"max-frames={N_PEAK_FRAMES}  sway={SWAY_DEG} deg  trials={M_TRIALS}")
    print("'s' = MediaPipe z-scale vs x.  s<1 = depth compressed (under-reads rotation).")

    # ---- A. Pure systematic bias (noise-free): measured = atan(s*tan(theta)) ----
    print("\n[A] SYSTEMATIC BIAS (noise-free) — measured angle for a given TRUE angle")
    print("    true:   " + "".join(f"{a:>8}" for a in bias_angles))
    for s in z_scales:
        row = "".join(f"{analytic_measured(a, s):>8.1f}" for a in bias_angles)
        print(f"    s={s:<4} {row}")
    print("    -> the TRUE angle a worker must reach for the app to READ exactly 45 deg:")
    line = "    "
    for s in z_scales:
        # solve atan(s*tan(theta)) = 45  ->  tan(theta) = 1/s  ->  theta = atan(1/s)
        need = math.degrees(math.atan(1.0 / s))
        line += f" s={s}:{need:>5.1f}deg "
    print(line)

    # ---- B. Gate misclassification with noise, across the z-scale sweep ----
    print("\n[B] P(flagged 'below 45') at decision-relevant TRUE angles  [mean measured +/- sd]")
    header = "    true ang:" + "".join(f"{a:>12}" for a in decision_angles)
    print(header)
    for s in z_scales:
        cells = []
        for a in decision_angles:
            pf, mu, sd = p_flag(a, z_scale=s, rng=rng)
            cells.append(f"{pf*100:>4.0f}% {mu:>4.1f}")
        print(f"    s={s:<5}" + "".join(f"{c:>12}" for c in cells))
    print("    (read: at true=50 a worker clearly passes by 5 deg; %=odds the app still faults them)")

    # ---- C0. The max() estimator is upward-biased by noise alone (s=1.00, no scale error) ----
    print("\n[C0] max()-OVER-FRAMES INFLATION from noise alone (perfect scale s=1.00)")
    print("     true peak ->  mean measured peak  (inflation)   [the estimator's own upward bias]")
    for a in (40, 45, 50):
        _, mu, _ = p_flag(a, z_scale=1.0, rng=rng)
        print(f"     {a:>3} deg   ->   {mu:>5.1f} deg          (+{mu - a:>4.1f} deg)")

    # ---- C. Separating random noise from systematic scale ----
    print("\n[C] NOISE-ONLY effect (perfect scale s=1.00) vs SCALE-COMPRESSED (s=0.85)")
    for s in (1.00, 0.85):
        gz_hi, gz_lo = gray_zone(s, rng=rng)
        ff50 = p_flag(50, z_scale=s, rng=rng)[0]      # false-fault: truly passes, gets flagged
        ff48 = p_flag(48, z_scale=s, rng=rng)[0]
        miss40 = 1.0 - p_flag(40, z_scale=s, rng=rng)[0]  # miss: truly fails, slips through
        print(f"    s={s}:  false-fault@48={ff48*100:4.0f}%  false-fault@50={ff50*100:4.0f}%  "
              f"miss@40={miss40*100:4.0f}%  gray-zone(P.9->P.1)= {gz_hi:.1f}->{gz_lo:.1f} deg")

    # ---- D. Sensitivity to z jitter at the boundary (s=1.0, true=45) ----
    print("\n[D] z-JITTER sensitivity at the boundary (s=1.00, true=45 deg)")
    print("    sigma_z:   " + "".join(f"{sz:>9}" for sz in (0.01, 0.02, 0.04, 0.06)))
    cells = []
    for sz in (0.01, 0.02, 0.04, 0.06):
        pf, mu, sd = p_flag(45, z_scale=1.0, sigma_z=sz, rng=rng)
        cells.append(f"{pf*100:>3.0f}%/{sd:>3.1f}")
    print("    P(flag)/sd:" + "".join(f"{c:>9}" for c in cells))
    print("    (sd = spread of the measured peak in degrees; grows with z jitter)")

    # ---- E. Does a robust peak estimator (percentile) beat max()? (s=1.00) ----
    print("\n[E] ESTIMATOR CHOICE vs the +9 deg max() inflation (s=1.00, true=45, sigma_z=0.02)")
    print("    a pure code change, no new data needed:")
    reducers = {
        "max() [current]": lambda a: float(np.max(a)),
        "p90":             lambda a: float(np.percentile(a, 90)),
        "p75":             lambda a: float(np.percentile(a, 75)),
        "median":          lambda a: float(np.percentile(a, 50)),
    }
    r = math.radians(45.0)
    for name, fn in reducers.items():
        infl = []
        for _ in range(M_TRIALS):
            frames = []
            for _ in range(N_PEAK_FRAMES):
                th = math.radians(45.0 + rng.normal(0.0, SWAY_DEG))
                xL = 0.08 * math.cos(th) + rng.normal(0, SIGMA_X)
                xR = -0.08 * math.cos(th) + rng.normal(0, SIGMA_X)
                zL = 0.08 * math.sin(th) + rng.normal(0, SIGMA_Z)
                zR = -0.08 * math.sin(th) + rng.normal(0, SIGMA_Z)
                frames.append(math.degrees(math.atan2(abs(zL - zR) + EPSILON, abs(xL - xR) + EPSILON)))
            infl.append(fn(np.array(frames)))
        arr = np.array(infl)
        print(f"    {name:<18} mean={arr.mean():>5.1f} deg  (+{arr.mean() - 45:>4.1f})  sd={arr.std():>4.1f}")
    print("    (lower inflation + lower sd = a peak estimate that actually means 45 deg)")

    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()
