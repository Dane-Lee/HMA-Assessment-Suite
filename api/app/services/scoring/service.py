from __future__ import annotations

import logging
from copy import deepcopy
from pathlib import Path

import yaml

from .extractors import HybridFeatureExtractor
from .movements import get_movement_scorers
from .types import CaptureQuality, CaptureScore

logger = logging.getLogger(__name__)


class UnscoreableCaptureError(RuntimeError):
    def __init__(self, quality: CaptureQuality) -> None:
        super().__init__("Pose analysis was unavailable; provider review is required.")
        self.quality = quality


class ScoringService:
    def __init__(
        self,
        thresholds_path: Path,
        *,
        enable_pose_overlays: bool = True,
        max_pose_trace_frames: int = 48,
        allow_fallback_scoring: bool = False,
    ) -> None:
        self.base_thresholds = yaml.safe_load(thresholds_path.read_text(encoding="utf-8"))
        self.thresholds = deepcopy(self.base_thresholds)
        self.extractor = HybridFeatureExtractor(
            enable_pose_overlays=enable_pose_overlays,
            max_pose_trace_frames=max_pose_trace_frames,
        )
        self.allow_fallback_scoring = allow_fallback_scoring
        self.scorers = get_movement_scorers()

    def apply_threshold_overrides(self, overrides: dict[str, dict[str, float]]) -> None:
        self.thresholds = deepcopy(self.base_thresholds)
        for movement_key, movement_overrides in overrides.items():
            if movement_key not in self.thresholds:
                continue
            for threshold_key, value in movement_overrides.items():
                if threshold_key in self.thresholds[movement_key]:
                    self.thresholds[movement_key][threshold_key] = value

    def set_threshold_override(self, movement_key: str, threshold_key: str, value: float) -> None:
        if movement_key not in self.thresholds:
            raise KeyError(f"Unsupported movement '{movement_key}'.")
        if threshold_key not in self.thresholds[movement_key]:
            raise KeyError(f"Unsupported threshold '{threshold_key}'.")
        self.thresholds[movement_key][threshold_key] = value

    def analyze_capture(self, movement_key: str, side: str, video_path: Path) -> CaptureScore:
        scorer = self.scorers.get(movement_key)
        if scorer is None:
            raise KeyError(f"Unsupported movement '{movement_key}'.")
        extraction = self.extractor.extract(video_path, movement_key, side)
        if extraction.source == "fallback" and not self.allow_fallback_scoring:
            logger.warning(
                "CAPTURE_UNSCOREABLE | movement=%s side=%s reasons=%s",
                movement_key,
                side,
                ",".join(extraction.quality.warnings),
            )
            raise UnscoreableCaptureError(extraction.quality)
        thresholds = self.thresholds[movement_key]
        result = scorer.score(extraction, thresholds)
        logger.info(
            "SCORE | movement=%s side=%s source=%s",
            movement_key,
            side,
            extraction.source,
        )
        return result
