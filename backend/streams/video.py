"""
Stream V: Video Visual Forensics.

Scores sampled frames with an AI-generation detector and aggregates them into a
video-level result with a per-frame timeline and suspicious time segments.

Detector: Community Forensics ViT-S/384 (CVPR 2025), trained on images from
~4,800 generators. It was selected by benchmark on real vs AI-generated video
clips; the project's image detector (Genesis ConvNeXt) scored near chance on
video frames. Numbers and limits are in docs/Video_Pipeline.md.

Each frame is scored on six 384x384 views and averaged:
  - 1 "standard" view  (shortest side resized to 440, centre crop) - global content
  - 5 native-resolution crops (centre + corners, no resizing)      - generator
    fingerprints live in fine pixel detail that resizing destroys
"""

import threading
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from ..config import settings
from ..utils.video_processor import SampledFrame

CROP = 384
STANDARD_SHORT_SIDE = 440
CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
CLIP_STD = (0.26862954, 0.26130258, 0.27577711)

# A frame counts as "flagged" at this score; segments are runs of flagged frames.
FRAME_FLAG_THRESHOLD = 0.5


def find_segments(times: List[float], scores: List[float], threshold: float = FRAME_FLAG_THRESHOLD) -> List[Dict[str, Any]]:
    """Group consecutive flagged frames into time segments."""
    segments: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    for t, s in zip(times, scores):
        if s >= threshold:
            if current is None:
                current = {"start": t, "end": t, "peak": s, "frames": 1}
            else:
                current["end"] = t
                current["peak"] = max(current["peak"], s)
                current["frames"] += 1
        elif current is not None:
            segments.append(current)
            current = None
    if current is not None:
        segments.append(current)
    return [
        {"start": round(seg["start"], 2), "end": round(seg["end"], 2), "peak": round(float(seg["peak"]), 4), "frames": seg["frames"]}
        for seg in segments
    ]


def summarize_frame_scores(
    times: List[float],
    scores: List[float],
    threshold: float,
    margin: float,
) -> Dict[str, Any]:
    """
    Turn per-frame fake probabilities into a video-level result (pure function).

    Video score = mean over frames. On the benchmark the mean, median and
    top-quartile mean ranked videos equally well, and the mean produced no false
    positives on real footage, so the simplest one is used.

    A video that is mostly clean but contains a run of flagged frames (e.g. an
    AI segment spliced into real footage) is marked `partial_suspicion`, which
    the fusion step turns into "Uncertain" instead of "Authentic".
    """
    arr = np.asarray(scores, dtype=np.float64)
    n = int(arr.size)
    if n == 0:
        raise ValueError("no frame scores")

    score = float(arr.mean())
    top_k = max(1, int(np.ceil(n * 0.25)))
    top_quartile = float(np.sort(arr)[-top_k:].mean())
    flagged = int((arr >= FRAME_FLAG_THRESHOLD).sum())
    segments = find_segments(times, [float(x) for x in arr])
    longest_run = max((seg["frames"] for seg in segments), default=0)

    partial = score < threshold and longest_run >= 2 and flagged / n >= 0.15

    if score >= threshold:
        status, label = "Synthetic/Fake", "AI-Generated"
    elif score >= threshold - margin or partial:
        status, label = "Uncertain", "Inconclusive"
    else:
        status, label = "Authentic Media", "Real"

    peak = int(arr.argmax())
    return {
        "score": score,
        "status": status,
        "label": label,
        "partial_suspicion": bool(partial),
        "details": {
            "frames_analyzed": n,
            "frame_mean": round(score, 4),
            "frame_median": round(float(np.median(arr)), 4),
            "frame_max": round(float(arr.max()), 4),
            "frame_min": round(float(arr.min()), 4),
            "frame_std": round(float(arr.std()), 4),
            "top_quartile_mean": round(top_quartile, 4),
            "flagged_frames": flagged,
            "flagged_fraction": round(flagged / n, 4),
        },
        "segments": segments,
        "peak_index": peak,
    }


def motion_level(frames: List[SampledFrame]) -> Optional[float]:
    """Mean absolute pixel change between consecutive sampled frames (0..1). ~0 means a still image."""
    if len(frames) < 2:
        return None
    import cv2

    small = [cv2.resize(f.image, (64, 64), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0 for f in frames]
    diffs = [float(np.abs(a - b).mean()) for a, b in zip(small[:-1], small[1:])]
    return float(np.mean(diffs))


class VideoForensicsStream:
    def __init__(self, scorer: Optional[Callable[[List[np.ndarray]], List[float]]] = None):
        # `scorer` lets tests inject a fake model: RGB frames -> fake probabilities.
        self._scorer = scorer
        self._model = None
        self._torch = None
        self._device = None
        self._mean = None
        self._std = None
        self._lock = threading.Lock()
        self.model_id = settings.VIDEO_DETECTOR_MODEL
        self.load_error: Optional[str] = None

    @property
    def model_name(self) -> str:
        return "Community Forensics ViT-S/384"

    def _ensure_loaded(self) -> bool:
        if self._scorer is not None or self._model is not None:
            return True
        with self._lock:
            if self._model is not None:
                return True
            try:
                import torch
                from transformers import ViTForImageClassification

                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                print(f"[VideoStream] Loading {self.model_id} on {device}...")
                model = ViTForImageClassification.from_pretrained(
                    self.model_id, revision=settings.VIDEO_DETECTOR_REVISION or None
                )
                # The detector is a single-logit (sigmoid) classifier. Earlier uploads of this
                # repo had a wrong 2-class config; refuse those rather than mis-read the output.
                if model.config.num_labels != 1:
                    raise RuntimeError(
                        f"{self.model_id} has num_labels={model.config.num_labels}, expected 1 "
                        "(outdated checkpoint - clear the Hugging Face cache and re-download)"
                    )
                model.to(device).eval()
                self._torch = torch
                self._device = device
                self._mean = torch.tensor(CLIP_MEAN, device=device).view(1, 3, 1, 1)
                self._std = torch.tensor(CLIP_STD, device=device).view(1, 3, 1, 1)
                self._model = model
                self.load_error = None
                print("[VideoStream] Detector loaded.")
                return True
            except Exception as exc:  # network, OOM, bad checkpoint...
                self.load_error = f"{type(exc).__name__}: {exc}"
                print(f"[VideoStream] Failed to load detector: {self.load_error}")
                return False

    # ---- preprocessing (done by hand so it does not depend on the transformers version) ----

    def _views(self, image_rgb: np.ndarray):
        """Six normalised 384x384 views of one frame, shape [6, 3, 384, 384]."""
        torch = self._torch
        F = torch.nn.functional
        t = torch.from_numpy(np.ascontiguousarray(image_rgb)).to(self._device).permute(2, 0, 1)[None].float() / 255.0
        h, w = t.shape[2:]

        # Standard view: shortest side -> 440, centre crop 384.
        scale = STANDARD_SHORT_SIDE / min(h, w)
        resized = F.interpolate(
            t, size=(max(CROP, round(h * scale)), max(CROP, round(w * scale))),
            mode="bicubic", antialias=True, align_corners=False,
        ).clamp(0, 1)
        rh, rw = resized.shape[2:]
        top, left = (rh - CROP) // 2, (rw - CROP) // 2
        views = [resized[:, :, top:top + CROP, left:left + CROP]]

        # Native crops: no resizing unless the frame is smaller than the crop.
        native = t
        if min(h, w) < CROP:
            up = CROP / min(h, w)
            native = F.interpolate(
                t, size=(max(CROP, round(h * up)), max(CROP, round(w * up))),
                mode="bicubic", antialias=True, align_corners=False,
            ).clamp(0, 1)
        nh, nw = native.shape[2:]
        for top, left in (((nh - CROP) // 2, (nw - CROP) // 2), (0, 0), (0, nw - CROP), (nh - CROP, 0), (nh - CROP, nw - CROP)):
            views.append(native[:, :, top:top + CROP, left:left + CROP])

        batch = torch.cat(views)
        return (batch - self._mean) / self._std

    def score_frames(self, images: List[np.ndarray]) -> List[float]:
        """Fake probability (0..1) for each RGB frame."""
        if self._scorer is not None:
            return [float(s) for s in self._scorer(images)]
        if not self._ensure_loaded():
            raise RuntimeError(f"Video detector unavailable ({self.load_error})")

        torch = self._torch
        scores: List[float] = []
        with self._lock, torch.no_grad():
            for image in images:
                views = self._views(image)
                probs = torch.sigmoid(self._model(pixel_values=views).logits).flatten()
                standard = probs[0]
                native = probs[1:].mean()
                scores.append(float(0.5 * standard + 0.5 * native))
        return scores

    def analyze(self, frames: List[SampledFrame]) -> Dict[str, Any]:
        """Synchronous; call from a worker thread. Raises on failure (never returns a fake 0.0)."""
        if not frames:
            raise ValueError("no frames to analyse")
        scores = self.score_frames([f.image for f in frames])
        times = [f.time for f in frames]
        summary = summarize_frame_scores(
            times, scores, settings.VIDEO_FAKE_THRESHOLD, settings.VIDEO_UNCERTAIN_MARGIN
        )
        summary["model"] = f"{self.model_name} · {len(frames)} frames"
        summary["timeline"] = [
            {"index": f.index, "time": round(f.time, 2), "score": round(float(s), 4)}
            for f, s in zip(frames, scores)
        ]
        motion = motion_level(frames)
        if motion is not None:
            summary["details"]["motion"] = round(motion, 5)
            summary["details"]["is_static"] = bool(motion < 0.002)
        return summary


video_stream = VideoForensicsStream()
