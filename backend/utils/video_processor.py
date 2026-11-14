"""
Video decoding utilities for the video detection pipeline.

- probe():          container/stream facts (duration, fps, resolution, audio track, tags)
- sample_frames():  N frames spread evenly over the whole video
- extract_audio():  audio track as 16 kHz mono WAV
- audio_rms():      loudness of an extracted WAV (to skip silent tracks)
- thumbnail_b64():  small JPEG preview of a frame for the UI

Everything here is synchronous; the orchestrator runs it in a worker thread.
"""

import base64
import json
import math
import os
import shutil
import subprocess
import wave
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import cv2
import numpy as np


class VideoError(Exception):
    """The upload is not a video we can analyse (corrupt, unsupported, too long...)."""


@dataclass
class VideoInfo:
    width: int = 0
    height: int = 0
    fps: float = 0.0
    frame_count: int = 0
    duration: float = 0.0
    video_codec: Optional[str] = None
    has_video: bool = False
    has_audio: Optional[bool] = None  # None = unknown (ffprobe unavailable)
    audio_codec: Optional[str] = None
    format_name: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)  # container + stream tags, lower-cased keys

    def public(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "fps": round(self.fps, 3),
            "frame_count": self.frame_count,
            "duration": round(self.duration, 3),
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "has_audio": bool(self.has_audio),
            "format": self.format_name,
        }


@dataclass
class SampledFrame:
    index: int          # frame number in the video
    time: float         # seconds from start
    image: np.ndarray   # RGB uint8, HxWx3


MAX_FRAME_SIDE = 1920  # larger frames (4K) are downscaled to bound memory


def _ffprobe_exe() -> Optional[str]:
    return shutil.which("ffprobe")


def _ffmpeg_exe() -> Optional[str]:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _parse_rate(rate: Optional[str]) -> float:
    if not rate or rate in ("0/0", "N/A"):
        return 0.0
    try:
        if "/" in rate:
            num, den = rate.split("/")
            return float(num) / float(den) if float(den) else 0.0
        return float(rate)
    except ValueError:
        return 0.0


def _to_float(value) -> float:
    try:
        f = float(value)
        return f if math.isfinite(f) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _probe_ffprobe(path: str) -> Optional[VideoInfo]:
    exe = _ffprobe_exe()
    if not exe:
        return None
    try:
        proc = subprocess.run(
            [exe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )
        if proc.returncode != 0:
            return VideoInfo()  # ffprobe ran and could not read the file
        data = json.loads(proc.stdout.decode("utf-8", errors="ignore") or "{}")
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        return None

    info = VideoInfo(has_audio=False)
    fmt = data.get("format", {}) or {}
    info.format_name = fmt.get("format_name")
    info.duration = _to_float(fmt.get("duration"))
    for key, value in (fmt.get("tags") or {}).items():
        info.tags[str(key).lower()] = str(value)

    for stream in data.get("streams", []) or []:
        kind = stream.get("codec_type")
        for key, value in (stream.get("tags") or {}).items():
            info.tags.setdefault(f"{kind}.{str(key).lower()}", str(value))
        if kind == "video" and not info.has_video:
            # Cover art in audio files is reported as a video stream; skip it.
            if (stream.get("disposition") or {}).get("attached_pic"):
                continue
            info.has_video = True
            info.video_codec = stream.get("codec_name")
            info.width = int(stream.get("width") or 0)
            info.height = int(stream.get("height") or 0)
            info.fps = _parse_rate(stream.get("avg_frame_rate")) or _parse_rate(stream.get("r_frame_rate"))
            if not info.duration:
                info.duration = _to_float(stream.get("duration"))
            try:
                info.frame_count = int(stream.get("nb_frames") or 0)
            except ValueError:
                info.frame_count = 0
        elif kind == "audio" and not info.has_audio:
            info.has_audio = True
            info.audio_codec = stream.get("codec_name")

    if info.has_video and not info.frame_count and info.duration and info.fps:
        info.frame_count = int(round(info.duration * info.fps))
    return info


def _probe_opencv(path: str) -> VideoInfo:
    info = VideoInfo()
    cap = cv2.VideoCapture(path)
    try:
        if not cap.isOpened():
            return info
        info.has_video = True
        info.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        info.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        info.fps = _to_float(cap.get(cv2.CAP_PROP_FPS))
        info.frame_count = max(0, int(_to_float(cap.get(cv2.CAP_PROP_FRAME_COUNT))))
        if info.fps > 0 and info.frame_count > 0:
            info.duration = info.frame_count / info.fps
    finally:
        cap.release()
    return info


def probe(path: str) -> VideoInfo:
    """Read container facts. Never raises for unreadable files: check `has_video`."""
    info = _probe_ffprobe(path)
    if info is None:  # ffprobe not installed
        info = _probe_opencv(path)
    elif info.has_video and (not info.fps or not info.frame_count):
        fallback = _probe_opencv(path)
        info.fps = info.fps or fallback.fps
        info.frame_count = info.frame_count or fallback.frame_count
        if not info.duration and info.fps and info.frame_count:
            info.duration = info.frame_count / info.fps
    return info


def frames_to_sample(duration: float, per_second: float, minimum: int, maximum: int) -> int:
    wanted = int(round(max(duration, 0.0) * per_second))
    return max(minimum, min(maximum, wanted))


def _prepare(frame_bgr: np.ndarray) -> np.ndarray:
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    longest = max(h, w)
    if longest > MAX_FRAME_SIDE:
        scale = MAX_FRAME_SIDE / longest
        rgb = cv2.resize(rgb, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    return rgb


def _sample_by_seek(cap, indices: List[int], fps: float) -> List[SampledFrame]:
    frames: List[SampledFrame] = []
    for idx in indices:
        # Frame counts in containers are often off by a few; step back a little on failure.
        for attempt in (idx, idx - 2, idx - 5):
            if attempt < 0:
                continue
            cap.set(cv2.CAP_PROP_POS_FRAMES, attempt)
            ok, frame = cap.read()
            if ok and frame is not None:
                frames.append(SampledFrame(attempt, attempt / fps if fps else 0.0, _prepare(frame)))
                break
    return frames


def _sample_sequential(path: str, count: int, fps: float, max_frames_to_read: int) -> List[SampledFrame]:
    """Fallback for files that cannot seek or do not report a frame count."""
    cap = cv2.VideoCapture(path)
    total = 0
    try:
        while total < max_frames_to_read and cap.grab():
            total += 1
    finally:
        cap.release()
    if total == 0:
        return []

    wanted = sorted({min(total - 1, int((k + 0.5) * total / count)) for k in range(count)})
    frames: List[SampledFrame] = []
    cap = cv2.VideoCapture(path)
    try:
        position = 0
        for target in wanted:
            while position < target and cap.grab():
                position += 1
            ok, frame = cap.read()
            position += 1
            if not ok or frame is None:
                break
            frames.append(SampledFrame(target, target / fps if fps else 0.0, _prepare(frame)))
    finally:
        cap.release()
    return frames


def sample_frames(path: str, info: VideoInfo, count: int) -> List[SampledFrame]:
    """Return up to `count` frames spread evenly across the video (centre of each time slice)."""
    count = max(1, count)
    fps = info.fps if info.fps > 0 else 25.0
    frames: List[SampledFrame] = []

    if info.frame_count > 0:
        total = info.frame_count
        indices = sorted({min(total - 1, int((k + 0.5) * total / count)) for k in range(count)})
        cap = cv2.VideoCapture(path)
        try:
            if cap.isOpened():
                frames = _sample_by_seek(cap, indices, fps)
        finally:
            cap.release()
        if len(frames) >= max(1, len(indices) // 2):
            return frames

    limit = int(max(info.duration, 60.0) * fps * 1.5) + 1000
    sequential = _sample_sequential(path, count, fps, limit)
    return sequential if len(sequential) > len(frames) else frames


def extract_audio(path: str, out_wav: str, max_seconds: Optional[float] = None) -> Optional[str]:
    """Write the audio track as 16 kHz mono PCM WAV. Returns None if there is no usable audio."""
    exe = _ffmpeg_exe()
    if not exe:
        return None
    cmd = [exe, "-nostdin", "-y", "-v", "error", "-i", path, "-vn"]
    if max_seconds:
        cmd += ["-t", str(max_seconds)]
    cmd += ["-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", out_wav]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    except (subprocess.SubprocessError, OSError):
        return None
    # A WAV with only a header (44 bytes) means the track was empty.
    if proc.returncode == 0 and os.path.exists(out_wav) and os.path.getsize(out_wav) > 1024:
        return out_wav
    if os.path.exists(out_wav):
        try:
            os.remove(out_wav)
        except OSError:
            pass
    return None


def audio_rms(wav_path: str) -> float:
    """RMS level (0..1) of a 16-bit PCM WAV produced by extract_audio()."""
    try:
        with wave.open(wav_path, "rb") as wav:
            if wav.getsampwidth() != 2:
                return 0.0
            raw = wav.readframes(wav.getnframes())
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        if samples.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(samples ** 2)))
    except (wave.Error, OSError, EOFError):
        return 0.0


def thumbnail_b64(image_rgb: np.ndarray, width: int = 160, quality: int = 70) -> str:
    """Base64 JPEG preview of an RGB frame."""
    h, w = image_rgb.shape[:2]
    if w > width:
        scale = width / w
        image_rgb = cv2.resize(image_rgb, (width, max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    ok, buffer = cv2.imencode(".jpg", cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, quality])
    return base64.b64encode(buffer).decode("ascii") if ok else ""
