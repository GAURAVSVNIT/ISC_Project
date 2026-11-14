"""
Provenance check for video files (runs before any model).

Two sources of evidence, both read from the container, not from pixel data:

1. Container/stream tags (encoder, comment, title...) naming a known AI video tool.
2. A C2PA "Content Credentials" manifest embedded in an MP4/MOV. If the manifest
   declares the IPTC digital source type `trainedAlgorithmicMedia`, the file states
   about itself that it is AI-generated (Sora, Veo, Firefly etc. write this).

The manifest signature is NOT cryptographically validated here, so this is a
declaration found in the file, not proof. Absence of metadata proves nothing:
re-encoding or a social-media upload strips it.

Unlike the generic binary scan in metadata_filter, nothing here searches raw
compressed video bytes for short strings, which produces false positives.
"""

import os
import re
import struct
from typing import Any, Dict, List, Optional

from .video_processor import VideoInfo

# usertype of the ISO-BMFF `uuid` box that holds a C2PA manifest store
C2PA_UUID = bytes.fromhex("d8fec3d61b0e483c92975828877ec481")
MAX_MANIFEST_BYTES = 8 * 1024 * 1024

# (pattern, display name) matched against container tag VALUES only.
AI_TOOL_PATTERNS = [
    (r"\bsora\b", "OpenAI Sora"),
    (r"\brunway(ml)?\b", "Runway"),
    (r"\bpika(\s?labs)?\b", "Pika"),
    (r"\bkling\b", "Kling"),
    (r"\bluma\b|\bdream machine\b", "Luma Dream Machine"),
    (r"\bveo\b", "Google Veo"),
    (r"\bhailuo\b|\bminimax\b", "MiniMax Hailuo"),
    (r"\bheygen\b", "HeyGen"),
    (r"\bsynthesia\b", "Synthesia"),
    (r"\bd-id\b", "D-ID"),
    (r"\bstable video\b|\bstability\.?ai\b", "Stable Video Diffusion"),
    (r"\banimatediff\b", "AnimateDiff"),
    (r"\bcogvideo", "CogVideo"),
    (r"\bhunyuan", "HunyuanVideo"),
    (r"\bcomfyui\b", "ComfyUI"),
    (r"\bmidjourney\b", "Midjourney"),
    (r"\bdeepfacelab\b|\bfaceswap\b|\broop\b|\bfacefusion\b", "Face-swap tool"),
    (r"\bai[- ]generated\b|\bgenerated (by|with|using) ai\b|\bmade with ai\b", "AI-generated label"),
]

# Tags written by phones/cameras. Presence is weak evidence of a camera original.
CAMERA_TAG_KEYS = (
    "com.apple.quicktime.make", "com.apple.quicktime.model", "com.android.version",
    "com.android.manufacturer", "com.android.model", "make", "model", "location",
    "com.apple.quicktime.location.iso6709",
)

# Names looked for inside a C2PA manifest, only to tell the user who produced it.
C2PA_GENERATOR_NAMES = [
    b"OpenAI", b"Sora", b"Google", b"Veo", b"Adobe Firefly", b"Firefly", b"Runway",
    b"Microsoft", b"Meta AI", b"Kling", b"Pika", b"Luma", b"Truepic", b"Leica", b"Sony", b"Nikon", b"Canon",
]


def _iter_top_level_boxes(path: str):
    """Yield (type, payload_offset, payload_size) for each top-level ISO-BMFF box."""
    size_on_disk = os.path.getsize(path)
    with open(path, "rb") as fh:
        offset = 0
        while offset + 8 <= size_on_disk:
            fh.seek(offset)
            header = fh.read(8)
            if len(header) < 8:
                return
            size, box_type = struct.unpack(">I4s", header)
            header_len = 8
            if size == 1:
                large = fh.read(8)
                if len(large) < 8:
                    return
                size = struct.unpack(">Q", large)[0]
                header_len = 16
            elif size == 0:
                size = size_on_disk - offset
            if size < header_len or offset + size > size_on_disk:
                return  # not a well-formed box structure; stop quietly
            yield box_type, offset + header_len, size - header_len
            offset += size


def read_c2pa(path: str) -> Optional[Dict[str, Any]]:
    """Find a C2PA manifest store in an MP4/MOV. Returns None if there is none."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(12)
        if len(head) < 12 or head[4:8] not in (b"ftyp", b"moov", b"free", b"wide", b"mdat", b"skip", b"styp"):
            return None  # not ISO-BMFF (e.g. WebM/AVI)

        for box_type, payload_offset, payload_size in _iter_top_level_boxes(path):
            if box_type != b"uuid" or payload_size < 16:
                continue
            with open(path, "rb") as fh:
                fh.seek(payload_offset)
                if fh.read(16) != C2PA_UUID:
                    continue
                manifest = fh.read(min(payload_size - 16, MAX_MANIFEST_BYTES))

            source_type = None
            if b"compositeWithTrainedAlgorithmicMedia" in manifest:
                source_type = "compositeWithTrainedAlgorithmicMedia"
            if b"trainedAlgorithmicMedia" in manifest.replace(b"compositeWithTrainedAlgorithmicMedia", b""):
                source_type = "trainedAlgorithmicMedia"
            generators = [name.decode() for name in C2PA_GENERATOR_NAMES if name in manifest]
            return {
                "present": True,
                "ai_generated": source_type is not None,
                "digital_source_type": source_type,
                "generators": generators,
                "signature_validated": False,
            }
    except OSError:
        return None
    return None


# Tag keys that describe the software that WROTE the file. A tool name here is strong
# evidence. In free-text keys (title, comment...) a word like "Sora" or "veo" can be
# an ordinary word, so those only count as a hint and never decide the verdict.
SOFTWARE_TAG_KEYS = (
    "encoder", "software", "tool", "creator_tool", "encoded_by", "writing_application",
    "com.apple.quicktime.software", "handler_name", "vendor_id",
)
EXPLICIT_LABEL = "AI-generated label"


def _is_software_key(key: str) -> bool:
    return key.split(".", 1)[-1] in SOFTWARE_TAG_KEYS or key in SOFTWARE_TAG_KEYS


def _match_ai_tools(tags: Dict[str, str]):
    """Returns (strong_hits, hints)."""
    strong: List[str] = []
    hints: List[str] = []
    for key, value in tags.items():
        lowered = value.lower()
        for pattern, name in AI_TOOL_PATTERNS:
            if re.search(pattern, lowered):
                hit = f"{key}: {value[:80]} ({name})"
                bucket = strong if (_is_software_key(key) or name == EXPLICIT_LABEL) else hints
                if hit not in bucket:
                    bucket.append(hit)
    return strong, hints


def inspect_video_metadata(path: str, info: VideoInfo) -> Dict[str, Any]:
    """
    Returns the same shape as metadata_filter.check() plus `container` and `c2pa`.
    `should_short_circuit` is True when the file itself declares it is AI-made.
    """
    tags = info.tags or {}
    ai_tags, hints = _match_ai_tools(tags)
    c2pa = read_c2pa(path)

    reasons: List[str] = []
    if c2pa and c2pa["ai_generated"]:
        who = f" ({', '.join(c2pa['generators'][:3])})" if c2pa["generators"] else ""
        ai_tags.insert(0, f"C2PA: {c2pa['digital_source_type']}{who}")
        reasons.append("Content Credentials (C2PA) in the file declare it AI-generated")
    if len(ai_tags) > (1 if c2pa and c2pa["ai_generated"] else 0):
        reasons.append("container metadata names an AI video tool")

    has_camera = any(key in tags or f"video.{key}" in tags for key in CAMERA_TAG_KEYS)
    container = {
        "format": info.format_name,
        "encoder": tags.get("encoder") or tags.get("video.encoder"),
        "creation_time": tags.get("creation_time") or tags.get("video.creation_time"),
    }

    if ai_tags:
        return {
            "verdict": "FAKE",
            "confidence": "HIGH",
            "ai_tags": ai_tags,
            "has_camera_metadata": has_camera,
            "should_short_circuit": True,
            "reason": "; ".join(reasons),
            "container": container,
            "c2pa": c2pa,
            "hints": hints,
        }

    if c2pa:
        reason = "Content Credentials (C2PA) present with no AI-generation declaration (signature not validated)"
    elif has_camera:
        reason = "Camera/phone metadata present (can be forged)"
    else:
        reason = "No provenance metadata (normal after re-encoding or social-media upload)"
    return {
        "verdict": "UNKNOWN",
        "confidence": "LOW",
        "ai_tags": [],
        "has_camera_metadata": has_camera,
        "should_short_circuit": False,
        "reason": reason,
        "container": container,
        "c2pa": c2pa,
        "hints": hints,
    }
