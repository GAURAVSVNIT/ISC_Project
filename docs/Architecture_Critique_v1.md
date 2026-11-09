# 🚨 Architecture Critique: The "Media-Gap" Vulnerability
**Date:** Feb 1, 2026
**Status:** CRITICAL GAPS FOUND

## Overview
While the **Image Pipeline** is now secure and optimized, the **Video** and **Audio** pipelines have significant architectural holes. The code assumes a "One Size Fits All" flow which breaks when components are extracted recursively.

---

## 🔒 Gap 1: Video Defense Bypass
**Severity:** HIGH (Security)
*   **The Flow**: `main.py` -> `orchestrator.process_video_request` -> `extract_frame` -> `orchestrator.process_request`.
*   **The Flaw**: `process_request` assumes `ArtShield` was already applied in `main.py`.
*   **Reality**: For videos, `main.py` passes the *whole video* to the orchestrator. The orchestrator extracts a raw frame and sends it to the image pipeline. **ArtShield is NEVER called on this frame.**
*   **Risk**: An adversarial frame inside a video (e.g., a "Subliminal Attack") will bypass the blur/re-encoding defense and hit the ConvNeXt model directly.

## 📉 Gap 2: Video Optimization Fail (Metadata)
**Severity:** MEDIUM (Cost)
*   **The Flow**: `orchestrator.process_request` checks metadata on the input bytes.
*   **The Flaw**: When called from `process_video_request`, the "input bytes" are the *newly extracted JPEG frame*.
*   **Reality**: `ffmpeg`/`moviepy` extraction does **NOT** copy metadata from the MP4 container to the JPEG frame.
*   **Result**: The metadata check always sees a "clean" file. A video tagged "Created by Sora" will simply be ignored, and we will pay GPU costs to analyze it.

## 🔓 Gap 3: Audio "Wild West"
**Severity:** HIGH (Security & Consistency)
*   **The Flow**: `main.py` -> `orchestrator.process_audio_request`.
*   **The Flaw**: This method calls `audio_stream.analyze` directly.
*   **Missing Controls**:
    1.  ❌ **No ArtShield**: No defense against adversarial audio noise.
    2.  ❌ **No Stegnography Check**: Audio is a prime vector for stego.
    3.  ❌ **No Metadata Check**: DeepFake audio tools often leave MP3 tags which we ignore.

---

## 📌 Proposed Fixes (Unified Pipeline)

### Fix 1: Defense-Aware Orchestrator
The `Orchestrator` methods (`process_video`, `process_audio`) must explicitly call `shield.sanitize` on their extracted components before analysis.

### Fix 2: Container Metadata Analysis
For video/audio, we must inspect the **Container Metadata (MP4/MP3)** in `main.py` or the Orchestrator *before* splitting the file. This requires updating `metadata_filter` to handle Video/Audio formats (using `ffmpeg` probes or `hachoir`).

### Fix 3: Standardized Audio Flow
Wrap `process_audio_request` with the same Security/Metadata logic as the image pipeline.
