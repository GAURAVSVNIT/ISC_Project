"""
Tests for the video detection pipeline.

No model weights or network are needed: the frame detector is replaced by an
injected scorer, and the videos are generated on the fly with OpenCV/ffmpeg.

Run from the repo root:  python -m pytest backend/tests/test_video_pipeline.py
"""

import asyncio
import os
import struct
import subprocess

import cv2
import numpy as np
import pytest

from backend.core.fusion import audio_is_usable, fuse_video
from backend.streams.video import (
    VideoForensicsStream,
    find_segments,
    summarize_frame_scores,
)
from backend.utils import video_processor as vp
from backend.utils.video_metadata import C2PA_UUID, inspect_video_metadata, read_c2pa

FFMPEG = vp._ffmpeg_exe()
needs_ffmpeg = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg not available")


# ---------------------------------------------------------------- fixtures

def _write_silent_video(path: str, seconds: float = 2.0, fps: int = 10, size=(320, 240)) -> str:
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    assert writer.isOpened(), "OpenCV could not open a video writer"
    for i in range(int(seconds * fps)):
        frame = np.full((size[1], size[0], 3), 30, dtype=np.uint8)
        x = 10 + i * 8
        cv2.rectangle(frame, (x, 80), (x + 60, 160), (0, 200, 255), -1)  # moving box -> real motion
        writer.write(frame)
    writer.release()
    return path


@pytest.fixture(scope="module")
def silent_video(tmp_path_factory):
    return _write_silent_video(str(tmp_path_factory.mktemp("vid") / "silent.mp4"))


@pytest.fixture(scope="module")
def video_with_audio(tmp_path_factory, silent_video):
    if FFMPEG is None:
        pytest.skip("ffmpeg not available")
    out = str(tmp_path_factory.mktemp("vid") / "with_audio.mp4")
    subprocess.run(
        [FFMPEG, "-nostdin", "-y", "-v", "error", "-i", silent_video,
         "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
         "-c:v", "copy", "-c:a", "aac", "-shortest", out],
        check=True,
    )
    return out


@pytest.fixture(scope="module")
def audio_only_file(tmp_path_factory):
    if FFMPEG is None:
        pytest.skip("ffmpeg not available")
    out = str(tmp_path_factory.mktemp("aud") / "voice.m4a")
    subprocess.run(
        [FFMPEG, "-nostdin", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=300:duration=2", "-c:a", "aac", out],
        check=True,
    )
    return out


def _box(box_type: bytes, payload: bytes) -> bytes:
    return struct.pack(">I4s", 8 + len(payload), box_type) + payload


def _write_mp4_with_c2pa(path, manifest: bytes) -> str:
    data = _box(b"ftyp", b"isom\x00\x00\x02\x00isomiso2") + _box(b"uuid", C2PA_UUID + manifest) + _box(b"mdat", b"\x00" * 64)
    with open(path, "wb") as fh:
        fh.write(data)
    return str(path)


# ---------------------------------------------------------------- decoding

def test_probe_reads_basic_facts(silent_video):
    info = vp.probe(silent_video)
    assert info.has_video
    assert (info.width, info.height) == (320, 240)
    assert abs(info.fps - 10) < 0.5
    assert abs(info.duration - 2.0) < 0.3
    assert info.frame_count in range(18, 23)
    assert not info.has_audio


def test_probe_rejects_garbage(tmp_path):
    junk = tmp_path / "junk.mp4"
    junk.write_bytes(os.urandom(20_000))
    assert not vp.probe(str(junk)).has_video


@pytest.mark.parametrize("duration,expected", [(0.5, 8), (4.0, 8), (10.0, 15), (20.0, 24), (120.0, 24)])
def test_frames_to_sample_is_clamped(duration, expected):
    assert vp.frames_to_sample(duration, per_second=1.5, minimum=8, maximum=24) == expected


def test_sample_frames_spreads_across_video(silent_video):
    info = vp.probe(silent_video)
    frames = vp.sample_frames(silent_video, info, 8)
    assert len(frames) == 8
    times = [f.time for f in frames]
    assert times == sorted(times) and len(set(times)) == 8
    assert times[0] < 0.4 and times[-1] > 1.5, "samples must cover start and end, not one spot"
    assert frames[0].image.shape == (240, 320, 3) and frames[0].image.dtype == np.uint8
    # The box moves, so first and last frame must differ (we are not re-reading one frame).
    assert np.abs(frames[0].image.astype(int) - frames[-1].image.astype(int)).mean() > 1


def test_sample_frames_survives_wrong_frame_count(silent_video):
    """Containers often over-report the frame count; sampling must still return frames."""
    info = vp.probe(silent_video)
    info.frame_count *= 3
    frames = vp.sample_frames(silent_video, info, 8)
    assert len(frames) >= 4


def test_sample_frames_without_frame_count(silent_video):
    info = vp.probe(silent_video)
    info.frame_count = 0
    assert len(vp.sample_frames(silent_video, info, 6)) == 6


def test_large_frames_are_downscaled():
    frame = np.zeros((2160, 3840, 3), dtype=np.uint8)
    assert max(vp._prepare(frame).shape[:2]) == vp.MAX_FRAME_SIDE


@needs_ffmpeg
def test_extract_audio(video_with_audio, silent_video, tmp_path):
    wav = vp.extract_audio(video_with_audio, str(tmp_path / "a.wav"))
    assert wav and os.path.getsize(wav) > 1024
    assert vp.audio_rms(wav) > 0.01
    assert vp.extract_audio(silent_video, str(tmp_path / "none.wav")) is None


def test_thumbnail_is_small_jpeg():
    import base64
    thumb = base64.b64decode(vp.thumbnail_b64(np.zeros((480, 640, 3), dtype=np.uint8), width=160))
    assert thumb[:2] == b"\xff\xd8" and len(thumb) < 20_000


# ---------------------------------------------------------------- provenance

def test_ai_tool_in_software_tag_short_circuits(tmp_path):
    info = vp.VideoInfo(has_video=True, tags={"encoder": "Sora 2 by OpenAI"})
    result = inspect_video_metadata(str(tmp_path / "missing.mp4"), info)
    assert result["should_short_circuit"] and result["verdict"] == "FAKE"
    assert any("Sora" in tag for tag in result["ai_tags"])


def test_ordinary_word_in_title_is_only_a_hint(tmp_path):
    """'veo' (Spanish 'I see') or a person named Sora in a title must not convict a video."""
    info = vp.VideoInfo(has_video=True, tags={"title": "Lo que veo desde mi ventana", "artist": "Sora Tanaka"})
    result = inspect_video_metadata(str(tmp_path / "missing.mp4"), info)
    assert not result["should_short_circuit"]
    assert result["ai_tags"] == [] and len(result["hints"]) == 2


def test_explicit_ai_label_in_comment_short_circuits(tmp_path):
    info = vp.VideoInfo(has_video=True, tags={"comment": "This clip is AI-generated"})
    assert inspect_video_metadata(str(tmp_path / "missing.mp4"), info)["should_short_circuit"]


def test_normal_encoder_tags_are_clean(tmp_path):
    info = vp.VideoInfo(has_video=True, tags={"encoder": "Lavf60.16.100", "video.handler_name": "VideoHandler",
                                               "com.apple.quicktime.make": "Apple"})
    result = inspect_video_metadata(str(tmp_path / "missing.mp4"), info)
    assert not result["should_short_circuit"] and result["has_camera_metadata"]


def test_c2pa_ai_declaration_detected(tmp_path):
    path = _write_mp4_with_c2pa(
        tmp_path / "c2pa.mp4",
        b'jumb...c2pa...{"digitalSourceType":"http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"} OpenAI Sora',
    )
    c2pa = read_c2pa(path)
    assert c2pa["present"] and c2pa["ai_generated"]
    assert c2pa["digital_source_type"] == "trainedAlgorithmicMedia"
    assert "OpenAI" in c2pa["generators"] and c2pa["signature_validated"] is False
    result = inspect_video_metadata(path, vp.VideoInfo(has_video=True))
    assert result["should_short_circuit"] and result["ai_tags"][0].startswith("C2PA")


def test_c2pa_camera_manifest_is_not_flagged(tmp_path):
    path = _write_mp4_with_c2pa(tmp_path / "cam.mp4", b'jumb c2pa {"digitalSourceType":".../digitalCapture"} Sony')
    c2pa = read_c2pa(path)
    assert c2pa["present"] and not c2pa["ai_generated"]
    assert not inspect_video_metadata(path, vp.VideoInfo(has_video=True))["should_short_circuit"]


def test_no_c2pa_in_plain_video_or_non_mp4(silent_video, tmp_path):
    assert read_c2pa(silent_video) is None
    webm = tmp_path / "x.webm"
    webm.write_bytes(b"\x1a\x45\xdf\xa3" + os.urandom(500) + b"trainedAlgorithmicMedia")
    assert read_c2pa(str(webm)) is None, "a stray string outside a C2PA box must not count"


# ---------------------------------------------------------------- frame scores -> video result

def _summary(scores):
    times = [i * 0.5 for i in range(len(scores))]
    return summarize_frame_scores(times, scores, threshold=0.5, margin=0.15)


def test_summary_fake_authentic_uncertain():
    assert _summary([0.9] * 10)["status"] == "Synthetic/Fake"
    assert _summary([0.05] * 10)["status"] == "Authentic Media"
    assert _summary([0.4] * 10)["status"] == "Uncertain"


def test_summary_flags_spliced_segment():
    """Mostly clean video with a short AI run: mean stays low but it must not read as clean."""
    scores = [0.02] * 12 + [0.95, 0.9, 0.97] + [0.02] * 5
    out = _summary(scores)
    assert out["score"] < 0.35
    assert out["partial_suspicion"] and out["status"] == "Uncertain"
    assert out["segments"] == [{"start": 6.0, "end": 7.0, "peak": 0.97, "frames": 3}]
    assert out["peak_index"] == 14


def test_single_noisy_frame_is_not_partial_suspicion():
    out = _summary([0.05] * 19 + [0.8])
    assert not out["partial_suspicion"] and out["status"] == "Authentic Media"


def test_find_segments_groups_runs():
    segs = find_segments([0, 1, 2, 3, 4, 5], [0.9, 0.8, 0.1, 0.7, 0.1, 0.6])
    assert [(s["start"], s["end"], s["frames"]) for s in segs] == [(0, 1, 2), (3, 3, 1), (5, 5, 1)]


def test_stream_with_injected_scorer(silent_video):
    info = vp.probe(silent_video)
    frames = vp.sample_frames(silent_video, info, 8)
    stream = VideoForensicsStream(scorer=lambda images: [0.9] * len(images))
    out = stream.analyze(frames)
    assert out["status"] == "Synthetic/Fake" and abs(out["score"] - 0.9) < 1e-6
    assert len(out["timeline"]) == 8 and out["details"]["frames_analyzed"] == 8
    assert out["details"]["is_static"] is False  # the box moves


def test_stream_raises_instead_of_returning_zero():
    """A broken detector must surface as an error, never as a 0.0 ('authentic') score."""
    def broken(_images):
        raise RuntimeError("model exploded")
    with pytest.raises(RuntimeError):
        VideoForensicsStream(scorer=broken).analyze([vp.SampledFrame(0, 0.0, np.zeros((64, 64, 3), np.uint8))])


# ---------------------------------------------------------------- fusion

def test_fusion_visual_only():
    out = fuse_video({"score": 0.9}, None)
    assert out["verdict"] == "Fake" and out["drivers"] == ["visual"] and abs(out["confidence_score"] - 0.9) < 1e-9
    out = fuse_video({"score": 0.05}, {"score": 0.0, "status": "No Audio Track", "usable": False})
    assert out["verdict"] == "Authentic" and abs(out["confidence_score"] - 0.95) < 1e-9


def test_fusion_synthetic_voice_on_real_pictures():
    """Voice flagged, pictures clean: a warning (Uncertain) by default, Fake only if configured."""
    audio = {"score": 0.97, "status": "Synthetic/Fake", "usable": True}
    out = fuse_video({"score": 0.05}, audio)
    assert out["verdict"] == "Uncertain" and out["drivers"] == ["audio"]
    assert abs(out["risk_score"] - 0.97) < 1e-9, "the raw risk still shows the strong audio signal"
    assert any("voice" in note.lower() for note in out["notes"])

    out = fuse_video({"score": 0.05}, audio, audio_can_convict=True)
    assert out["verdict"] == "Fake" and abs(out["confidence_score"] - 0.97) < 1e-9


def test_fusion_both_signals_flagged():
    out = fuse_video({"score": 0.8}, {"score": 0.9, "status": "Synthetic/Fake", "usable": True})
    assert out["verdict"] == "Fake" and out["drivers"] == ["visual", "audio"]
    assert abs(out["confidence_score"] - 0.9) < 1e-9


def test_fusion_clean_voice_never_lowers_a_visual_detection():
    out = fuse_video({"score": 0.8}, {"score": 0.02, "status": "Authentic Audio", "usable": True})
    assert out["verdict"] == "Fake" and abs(out["risk_score"] - 0.8) < 1e-9


def test_fusion_ignores_failed_or_silent_audio():
    for audio in ({"score": 0.99, "status": "Error: boom"}, {"score": 0.99, "status": "Silent Audio Track", "usable": False}):
        assert not audio_is_usable(audio)
        assert fuse_video({"score": 0.05}, audio)["verdict"] == "Authentic"


def test_fusion_uncertain_band_and_partial():
    assert fuse_video({"score": 0.42}, None)["verdict"] == "Uncertain"
    assert fuse_video({"score": 0.2, "partial_suspicion": True}, None)["verdict"] == "Uncertain"
    assert fuse_video({"score": 0.2}, None)["verdict"] == "Authentic"


# ---------------------------------------------------------------- audio label mapping

def test_audio_fake_index_follows_label_names():
    from backend.streams.audio import AudioStream
    assert AudioStream._find_fake_index({0: "AIVoice", 1: "HumanVoice"}) == 0
    assert AudioStream._find_fake_index({"0": "real", "1": "fake"}) == 1
    assert AudioStream._find_fake_index({0: "bonafide", 1: "spoof"}) == 1
    with pytest.raises(ValueError):
        AudioStream._find_fake_index({0: "LABEL_0", 1: "LABEL_1"})


# ---------------------------------------------------------------- orchestrator end to end

@pytest.fixture
def orchestrator_with_fake_detector(monkeypatch):
    from backend.core.orchestrator import orchestrator
    from backend.streams import video as video_module

    def set_score(value):
        monkeypatch.setattr(video_module.video_stream, "_scorer", lambda images: [value] * len(images))
    return orchestrator, set_score


def _run(coro):
    return asyncio.run(coro)


def test_orchestrator_video_end_to_end(orchestrator_with_fake_detector, silent_video):
    orchestrator, set_score = orchestrator_with_fake_detector
    set_score(0.92)
    stages = []

    async def progress(stage, percent, message):
        stages.append((stage, percent))

    with open(silent_video, "rb") as fh:
        data = fh.read()
    result = _run(orchestrator.process_video_request(data, "", progress=progress, filename="clip.mp4"))

    assert result["media_type"] == "video" and result["verdict"] == "Fake"
    assert abs(result["confidence_score"] - 0.92) < 1e-6
    assert len(result["media_sha256"]) == 64
    video = result["video"]
    assert video["frames_analyzed"] == 8 and len(video["timeline"]) == 8
    assert all(entry["thumb"] for entry in video["timeline"]) and video["peak_frame"]["image"]
    assert video["drivers"] == ["visual"]
    assert result["audio"]["usable"] is False                      # no audio track -> did not vote
    assert result["semantic"]["status"].startswith("N/A")          # no claim -> no claim check
    assert not result["cost_optimized"]
    percents = [p for _, p in stages]
    assert percents == sorted(percents) and stages[0][0] == "video_probe"

    set_score(0.03)
    result = _run(orchestrator.process_video_request(data, "", filename="clip.mp4"))
    assert result["verdict"] == "Authentic"


def test_orchestrator_rejects_non_video(orchestrator_with_fake_detector):
    orchestrator, set_score = orchestrator_with_fake_detector
    set_score(0.5)
    with pytest.raises(vp.VideoError):
        _run(orchestrator.process_video_request(os.urandom(30_000), "", filename="junk.mp4"))


def test_orchestrator_metadata_short_circuit(orchestrator_with_fake_detector, tmp_path):
    orchestrator, set_score = orchestrator_with_fake_detector

    def must_not_run(_images):
        raise AssertionError("detector ran although metadata already settled the verdict")
    from backend.streams import video as video_module
    video_module.video_stream._scorer = must_not_run

    # A real, decodable video with a C2PA AI declaration appended as a top-level box.
    path = _write_silent_video(str(tmp_path / "base.mp4"), seconds=1.0)
    with open(path, "rb") as fh:
        data = fh.read() + _box(b"uuid", C2PA_UUID + b"c2pa trainedAlgorithmicMedia Runway")
    try:
        result = _run(orchestrator.process_video_request(data, "", filename="gen.mp4"))
    finally:
        set_score(0.0)
    assert result["verdict"] == "Fake" and result["cost_optimized"]
    assert result["metadata"]["c2pa"]["ai_generated"] and result["video"]["drivers"] == ["metadata"]


@needs_ffmpeg
def test_orchestrator_routes_audio_only_container(orchestrator_with_fake_detector, audio_only_file, monkeypatch):
    orchestrator, set_score = orchestrator_with_fake_detector
    set_score(0.5)
    seen = {}

    async def fake_audio_pipeline(file_bytes, claim):
        seen["wav"] = file_bytes[:4]
        return {"audio": {"score": 0.1, "status": "Authentic Audio"}, "visual": {}, "semantic": {}, "contextual": {}}
    monkeypatch.setattr(orchestrator, "process_audio_request", fake_audio_pipeline)

    with open(audio_only_file, "rb") as fh:
        result = _run(orchestrator.process_video_request(fh.read(), "", filename="voice.m4a"))
    assert result["media_type"] == "audio" and seen["wav"] == b"RIFF"


def test_temp_files_are_cleaned_up(orchestrator_with_fake_detector, silent_video, monkeypatch, tmp_path):
    orchestrator, set_score = orchestrator_with_fake_detector
    set_score(0.1)
    import tempfile
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    with open(silent_video, "rb") as fh:
        _run(orchestrator.process_video_request(fh.read(), "", filename="clip.mp4"))
    assert [p for p in os.listdir(tmp_path) if p.startswith("echelon_video_")] == []
