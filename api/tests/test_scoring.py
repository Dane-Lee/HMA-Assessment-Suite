from __future__ import annotations

import logging
from pathlib import Path

import pytest

import api.app.services.scoring.extractors as extractor_module
from api.app.services.scoring.extractors import (
    FramePose,
    HybridFeatureExtractor,
    _robust_max,
    _robust_span,
    _smooth_series,
)
from api.app.services.scoring.service import ScoringService, UnscoreableCaptureError
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


def test_pose_extraction_failure_is_logged_and_identified(tmp_path: Path, monkeypatch, caplog):
    video_path = tmp_path / "capture.webm"
    video_path.write_bytes(b"video-data")
    extractor = HybridFeatureExtractor(enable_pose_overlays=False)

    monkeypatch.setattr(extractor_module, "cv2", object())
    monkeypatch.setattr(extractor_module, "mp", object())
    monkeypatch.setattr(extractor_module, "np", object())
    monkeypatch.setattr(
        extractor,
        "_build_context",
        lambda path, movement_key, side: VideoContext(
            path=path,
            side=side,
            movement_key=movement_key,
            file_size_bytes=path.stat().st_size,
            duration_seconds=1.25,
            frame_count=0,
            fps=0.0,
            width=0,
            height=0,
        ),
    )

    def fail_pose_extraction(_context):
        raise RuntimeError("forced pose failure")

    monkeypatch.setattr(extractor, "_extract_with_mediapipe", fail_pose_extraction)

    with caplog.at_level(logging.ERROR, logger=extractor_module.__name__):
        result = extractor.extract(video_path, "trunk_rotation", "left")

    assert result.source == "fallback"
    assert "pose_extraction_failed" in result.quality.warnings
    assert "POSE_EXTRACTION_FAILED" in caplog.text
    assert "movement=trunk_rotation" in caplog.text
    assert "side=left" in caplog.text
    assert "forced pose failure" in caplog.text
    assert video_path.name not in caplog.text


def test_missing_pose_dependencies_are_logged_and_identified(tmp_path: Path, monkeypatch, caplog):
    video_path = tmp_path / "capture.webm"
    video_path.write_bytes(b"video-data")
    extractor = HybridFeatureExtractor(enable_pose_overlays=False)

    monkeypatch.setattr(extractor_module, "cv2", None)
    monkeypatch.setattr(extractor_module, "mp", None)
    monkeypatch.setattr(extractor_module, "np", None)

    with caplog.at_level(logging.WARNING, logger=extractor_module.__name__):
        result = extractor.extract(video_path, "cervical_rotation", "right")

    assert result.source == "fallback"
    assert "pose_dependencies_unavailable" in result.quality.warnings
    assert "POSE_DEPENDENCIES_UNAVAILABLE" in caplog.text
    assert "movement=cervical_rotation" in caplog.text
    assert "side=right" in caplog.text
    assert video_path.name not in caplog.text


def test_valid_video_container_still_becomes_unscoreable_without_pose_service(
    tmp_path: Path, monkeypatch
):
    if extractor_module.cv2 is None or extractor_module.np is None:
        pytest.skip("OpenCV and NumPy are required for the valid-container fixture")
    video_path = tmp_path / "valid-capture.avi"
    writer = extractor_module.cv2.VideoWriter(
        str(video_path),
        extractor_module.cv2.VideoWriter_fourcc(*"MJPG"),
        10.0,
        (64, 64),
    )
    assert writer.isOpened()
    for _ in range(10):
        writer.write(extractor_module.np.zeros((64, 64, 3), dtype=extractor_module.np.uint8))
    writer.release()
    monkeypatch.setattr(extractor_module, "mp", None)
    service = ScoringService(
        Path(__file__).resolve().parents[2] / "config" / "scoring_thresholds.yaml"
    )

    with pytest.raises(UnscoreableCaptureError) as raised:
        service.analyze_capture("trunk_rotation", "left", video_path)
    assert raised.value.quality.width == 64
    assert raised.value.quality.height == 64
    assert "pose_dependencies_unavailable" in raised.value.quality.warnings


def test_cervical_rotation_good_fixture_scores_higher(tmp_path: Path):
    thresholds_path = Path(__file__).resolve().parents[2] / "config" / "scoring_thresholds.yaml"
    service = ScoringService(thresholds_path, allow_fallback_scoring=True)

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
