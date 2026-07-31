from __future__ import annotations

from pathlib import Path

from api.app.services.scoring.extractors import (
    FramePose,
    HybridFeatureExtractor,
    _robust_max,
    _robust_span,
    _smooth_series,
)
from api.app.services.scoring.service import ScoringService
from api.app.services.scoring.types import VideoContext


def _neutral_frame(timestamp: float, **overrides) -> FramePose:
    """A plausible neutral standing pose; override only the landmarks a test cares about."""
    defaults = dict(
        timestamp_seconds=timestamp,
        landmarks={},
        nose_x=0.50, nose_y=0.30, nose_z=-0.20,
        left_ear_visibility=0.90, right_ear_visibility=0.90,
        left_shoulder_x=0.55, right_shoulder_x=0.45,
        left_shoulder_y=0.40, right_shoulder_y=0.40,
        left_shoulder_z=0.0, right_shoulder_z=0.0,
        left_hip_x=0.54, right_hip_x=0.46,
        left_hip_y=0.70, right_hip_y=0.70,
        left_hip_z=0.0, right_hip_z=0.0,
        left_knee_x=0.54, right_knee_x=0.46,
        left_knee_y=0.85, right_knee_y=0.85,
        left_ankle_x=0.54, right_ankle_x=0.46,
        left_ankle_y=0.98, right_ankle_y=0.98,
        left_heel_y=0.99, right_heel_y=0.99,
        left_foot_y=1.0, right_foot_y=1.0,
        left_wrist_x=0.50, right_wrist_x=0.50,
        left_wrist_y=0.55, right_wrist_y=0.55,
    )
    defaults.update(overrides)
    return FramePose(**defaults)


def _cervical_context() -> VideoContext:
    return VideoContext(
        path=Path("synthetic-cervical.webm"),
        side="right",
        movement_key="cervical_rotation",
        file_size_bytes=1000,
        duration_seconds=3.0,
        frame_count=30,
        fps=10.0,
        width=720,
        height=1280,
    )


def test_ear_visibility_asymmetry_rejects_head_slide_confound():
    """The production nose-x metric credits a pure lateral head-slide as rotation; the
    prototype ear-visibility-asymmetry cue (debug-only) correctly reads ~0 yaw for it,
    and lights up for a genuine head turn. Proves confound rejection in the real pipeline.
    See docs/self-guided-assessment/models/cervical_ear_yaw_model.py."""
    extractor = HybridFeatureExtractor(enable_pose_overlays=False)
    context = _cervical_context()

    # A genuine head turn: one ear faces the camera, the other self-occludes; nose stays near
    # the midline (axial yaw moves the nose mostly in depth, not in x).
    yaw_frames = [
        _neutral_frame(i / 10.0, left_ear_visibility=0.95, right_ear_visibility=0.30)
        for i in range(5)
    ]
    # A pure head-slide: both ears keep facing forward (no asymmetry), but the nose is shifted
    # laterally enough to clear the 0.11 gate -> the production metric is fooled.
    slide_frames = [_neutral_frame(i / 10.0, nose_x=0.52) for i in range(5)]

    yaw = extractor._derive_features(yaw_frames, context).debug_metrics
    slide = extractor._derive_features(slide_frames, context).debug_metrics

    # production metric: the slide clears the gate (>= 0.11) -> falsely credited as rotation
    assert slide["chin_midline_clearance_ratio"] >= 0.11
    # prototype metric: ~0 for the slide (no real yaw), clearly positive for the true turn
    assert slide["ear_visibility_asymmetry"] < 0.05
    assert yaw["ear_visibility_asymmetry"] > 0.3
    assert yaw["ear_visibility_asymmetry"] > slide["ear_visibility_asymmetry"]


def test_smooth_series_rejects_single_frame_spike():
    # a steady ~0.10 signal with one 0.40 single-frame landmark glitch
    spike = [0.10, 0.11, 0.10, 0.40, 0.10, 0.12, 0.11, 0.10]
    assert max(spike) == 0.40            # raw max() grabs the spike (the bug)
    assert _robust_max(spike) <= 0.15    # robust peak rejects it

    # a genuinely sustained peak is preserved, not erased
    sustained = [0.10, 0.20, 0.30, 0.30, 0.30, 0.20, 0.10]
    assert _robust_max(sustained) == 0.30

    # edge-padded median fully removes an isolated spike even in a 3-sample series
    assert _smooth_series([0.1, 0.9, 0.1]) == [0.1, 0.1, 0.1]

    # span collapses when both extremes are lone outliers
    assert _robust_span([0.5, 0.5, 0.9, 0.5, 0.1, 0.5]) < (0.9 - 0.1)


def test_cervical_rotation_good_fixture_scores_higher(tmp_path: Path):
    thresholds_path = Path(__file__).resolve().parents[2] / "config" / "scoring_thresholds.yaml"
    service = ScoringService(thresholds_path)

    good_path = tmp_path / "good-cervical.webm"
    poor_path = tmp_path / "poor-cervical.webm"
    good_path.write_bytes(b"good-video-data")
    poor_path.write_bytes(b"poor-video-data")

    good = service.analyze_capture("cervical_rotation", "right", good_path)
    poor = service.analyze_capture("cervical_rotation", "right", poor_path)

    assert good.score >= poor.score
    assert good.metrics["chin_midline_clearance_ratio"] >= poor.metrics["chin_midline_clearance_ratio"]
    assert good.pose_trace is None
    assert good.quality.overlay_available is False
    assert good.quality.status == "unavailable"
