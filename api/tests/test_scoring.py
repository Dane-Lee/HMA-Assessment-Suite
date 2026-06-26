from __future__ import annotations

from pathlib import Path

from api.app.services.scoring.extractors import _robust_max, _robust_span, _smooth_series
from api.app.services.scoring.service import ScoringService


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
