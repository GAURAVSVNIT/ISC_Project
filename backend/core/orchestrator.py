import asyncio
import hashlib
import os
import shutil
import tempfile
from typing import Any, Awaitable, Callable, Dict, Optional

from ..streams.genesis import genesis_stream
from ..streams.semantic import semantic_stream
from ..utils.metadata_filter import metadata_filter
# from ..streams.context import context_stream (Dev 3 will implement)

class Orchestrator:
    """
    Manages the parallel execution of the Tri-Stream pipeline.
    
    COST OPTIMIZATION:
    Metadata pre-filter checks EXIF data FIRST.
    If AI generation tags found → instant verdict (no GPU/API costs).
    """
    
    async def process_request(self, file_bytes: bytes, claim: str, raw_bytes: bytes = None) -> Dict[str, Any]:
        """
        Orchestrate the 3 streams with metadata pre-filtering.
        
        Args:
            file_bytes: The image bytes to analyze (cleaned/sanitized).
            claim: User's claim.
            raw_bytes: Original raw bytes (with metadata) for the pre-filter.
        
        Flow:
        1. Metadata check (on RAW bytes) (1ms)
        2. If HIGH confidence AI → SHORT CIRCUIT
        3. Otherwise → Full pipeline (on CLEAN bytes)
        """
        
        # ===== PHASE 1: Metadata Pre-Filter (Cost Saver) =====
        print(f"[Orchestrator] Processing Request. Payload Size: {len(file_bytes)/1024:.2f} KB")

        metadata_result = metadata_filter.check(file_bytes)
        # Critical Fix: Check metadata on RAW bytes before ArtShield strips it
        bytes_to_check = raw_bytes if raw_bytes is not None else file_bytes
        metadata_result = metadata_filter.check(bytes_to_check)
        
        if metadata_result["should_short_circuit"]:
            # ✅ AI TAGS FOUND - Skip expensive compute
            return {
                "visual": {
                    "score": 1.0,  # Max score
                    "status": "AI-Generated (Metadata)",
                    "model": "EXIF Pre-Filter"
                },
                "semantic": {"score": 0.0, "status": "Skipped (metadata flag)"},
                "contextual": {"found": False, "details": "Skipped (metadata flag)"},
                "metadata": metadata_result,
                "cost_optimized": True,  # Flag for analytics
                "verdict": "FAKE"
            }
        
        # ===== PHASE 2: Full Pipeline (Metadata inconclusive) =====
        # Metadata absent, suspicious, or claims "real" (could be faked)
        # → Run expensive GPU + API checks
        
        # Define async tasks for each stream
        task_a = genesis_stream.analyze(file_bytes)
        task_b = semantic_stream.analyze(file_bytes, claim)
        # Using verified context stream
        from ..streams.context_xfacta import fetch_xfacta_evidence
        task_c = self._run_context_stream(claim)
        
        # Run in parallel
        results = await asyncio.gather(task_a, task_b, task_c, return_exceptions=True)
        
        visual_res, semantic_res, context_res = results
        
        # Handle exceptions gracefully
        if isinstance(visual_res, Exception):
            visual_res = {"score": 0.0, "status": f"Error: {str(visual_res)}"}
        if isinstance(semantic_res, Exception):
            semantic_res = {"score": 0.0, "status": f"Error: {str(semantic_res)}"}
        if isinstance(context_res, Exception):
            context_res = {"found": False, "error": f"{str(context_res)}"}
            
        return {
            "visual": visual_res,
            "semantic": semantic_res,
            "contextual": context_res,
            "metadata": metadata_result,
            "cost_optimized": False  # Full pipeline executed
        }

    async def _run_context_stream(self, claim: str):
        """
        Wrapper for Context Stream (SerpApi/DuckDuckGo)
        """
        from ..streams.context_xfacta import fetch_xfacta_evidence
        
        try:
             # simple sync call
             evidence_data = fetch_xfacta_evidence(claim)
             evidence_text = evidence_data.get("text", "")
             sources = evidence_data.get("sources", [])
             
             print(f"[Orchestrator] Context Stream Data: Found={bool(evidence_text)}, Sources={len(sources)}")

             return {
                 "evidence_found": bool(evidence_text),
                 "sources": sources if sources else ["DuckDuckGo"], 
                 "summary": evidence_text[:300] + "..." if len(evidence_text) > 300 else evidence_text
             }
        except Exception as e:
            return {"found": False, "error": str(e)}

    async def process_audio_request(self, file_bytes: bytes, claim: str) -> Dict[str, Any]:
        """
        Orchestration for Audio Files (Stream D + Context).
        """
        from ..streams.audio import audio_stream
        from ..defense.art_shield import shield # Import Shield
        
        # 1. Container Metadata Check (Cost Opt)
        metadata_result = metadata_filter.check(file_bytes)
        if metadata_result["should_short_circuit"]:
             return {
                "visual": {"score": 0.0, "status": "N/A"},
                "semantic": {"score": 0.0, "status": "N/A"},
                "audio": {"score": 1.0, "status": "AI-Generated (Metadata)", "model": "Header Pre-Filter"},
                "contextual": {"found": False},
                "metadata": metadata_result,
                "cost_optimized": True,
                "verdict": "Fake"
            }

        # 2. Defense Layer (Stego + Sanitization)
        # Note: We do NOT re-encode audio (destroy spectral data), but we check for Stego
        stego_warning = None
        if shield.detect_trailing_bytes(file_bytes):
            stego_warning = "Steganography Detected (Trailing Data)"

        # Define async tasks
        task_d = audio_stream.analyze(file_bytes)
        task_c = self._run_context_stream(claim) if claim else asyncio.sleep(0, result={"found": False, "summary": "No claim provided"})
        
        # Run in parallel
        results = await asyncio.gather(task_d, task_c, return_exceptions=True)
        audio_res, context_res = results
        
        # Handle exceptions
        if isinstance(audio_res, Exception):
            audio_res = {"score": 0.0, "status": f"Error: {str(audio_res)}", "model": "AudioStream"}
        if isinstance(context_res, Exception):
            context_res = {"found": False, "error": str(context_res)}

        # Inject Security Warning
        if stego_warning:
             if metadata_result is None: metadata_result = {}
             metadata_result["security_warning"] = stego_warning

        return {
            "visual": {"score": 0.0, "status": "N/A (Audio Input)"},
            "semantic": {"score": 0.0, "status": "N/A (Audio Input)"},
            "audio": audio_res,
            "contextual": context_res,
            "metadata": metadata_result,
            "cost_optimized": False
        }

    async def process_video_request(
        self,
        file_bytes: bytes,
        claim: str,
        progress: Optional[Callable[[str, int, str], Awaitable[None]]] = None,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        End-to-end video analysis.

        1. Probe the container (reject non-videos; hand audio-only files to the audio pipeline)
        2. Provenance check: C2PA Content Credentials + AI-tool tags  -> may short-circuit
        3. Sample frames across the whole video + extract the audio track
        4. Stream V: score every sampled frame, build timeline and suspicious segments
        5. Stream D on the audio track; claim consistency and web context (informational)
        6. Fuse visual + audio into verdict / confidence

        `progress(stage, percent, message)` is awaited between steps (used by the WebSocket).
        Raises VideoError for uploads that cannot be analysed. Model failures propagate as
        exceptions too: an error must never be reported as an "Authentic" verdict.
        """
        from ..config import settings
        from ..utils import video_processor as vp
        from ..utils.video_metadata import inspect_video_metadata
        from ..streams.video import video_stream
        from .fusion import fuse_video, audio_is_usable

        async def report(stage: str, percent: int, message: str):
            if progress is not None:
                await progress(stage, percent, message)

        media_sha256 = hashlib.sha256(file_bytes).hexdigest()
        workdir = tempfile.mkdtemp(prefix="echelon_video_")
        ext = os.path.splitext(filename or "")[1].lower()
        if ext not in (".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v", ".m4a", ".3gp"):
            ext = ".mp4"
        video_path = os.path.join(workdir, f"input{ext}")
        wav_path = os.path.join(workdir, "audio.wav")

        try:
            def _write():
                with open(video_path, "wb") as fh:
                    fh.write(file_bytes)
            await asyncio.to_thread(_write)

            # ---- 1. Probe ----
            await report("video_probe", 8, "🎞️ Reading video container...")
            info = await asyncio.to_thread(vp.probe, video_path)

            if not info.has_video:
                if info.has_audio:
                    # Audio in a video container (e.g. .m4a): analyse it as audio.
                    extracted = await asyncio.to_thread(vp.extract_audio, video_path, wav_path)
                    if not extracted:
                        raise vp.VideoError("The file has an audio track but it could not be decoded.")
                    with open(extracted, "rb") as fh:
                        wav_bytes = fh.read()
                    await report("audio_processing", 30, "🎵 Audio-only file - analysing audio...")
                    result = await self.process_audio_request(wav_bytes, claim)
                    result["media_type"] = "audio"
                    result["media_sha256"] = media_sha256
                    return result
                raise vp.VideoError("This file is not a readable video (unsupported format or corrupt upload).")

            if info.duration and info.duration > settings.VIDEO_MAX_DURATION_S:
                raise vp.VideoError(
                    f"Video is {info.duration:.0f}s long; the limit is {settings.VIDEO_MAX_DURATION_S:.0f}s."
                )

            # ---- 2. Provenance (no model cost) ----
            await report("metadata", 12, "📋 Checking provenance (C2PA, container tags)...")
            metadata_result = await asyncio.to_thread(inspect_video_metadata, video_path, info)
            if metadata_result["should_short_circuit"]:
                return {
                    "media_type": "video",
                    "media_sha256": media_sha256,
                    "verdict": "Fake",
                    "confidence_score": 0.95,
                    "risk_score": 0.95,
                    "visual": {"score": 1.0, "status": "AI-Generated (Metadata)", "model": "Provenance check"},
                    "semantic": {"score": 0.0, "status": "N/A (skipped)"},
                    "context": {"evidence_found": False, "summary": "", "sources": []},
                    "audio": None,
                    "metadata": metadata_result,
                    "video": {**info.public(), "frames_analyzed": 0, "timeline": [], "segments": [],
                              "drivers": ["metadata"], "notes": [metadata_result["reason"]]},
                    "cost_optimized": True,
                }

            # ---- 3. Decode: frames + audio in parallel ----
            n_frames = vp.frames_to_sample(
                info.duration, settings.VIDEO_FRAMES_PER_SECOND, settings.VIDEO_MIN_FRAMES, settings.VIDEO_MAX_FRAMES
            )
            await report("video_frames", 20, f"🎥 Sampling {n_frames} frames across the video...")
            frames_job = asyncio.to_thread(vp.sample_frames, video_path, info, n_frames)
            if info.has_audio is False:
                frames, audio_file = await frames_job, None
            else:
                frames, audio_file = await asyncio.gather(
                    frames_job, asyncio.to_thread(vp.extract_audio, video_path, wav_path, settings.VIDEO_MAX_DURATION_S)
                )
            if not frames:
                raise vp.VideoError("Could not decode any frames from this video.")

            # ---- 4. Visual forensics on every sampled frame ----
            await report("visual", 35, f"🔍 Scanning {len(frames)} frames for AI-generation artifacts...")
            visual = await asyncio.to_thread(video_stream.analyze, frames)

            # ---- 5. Audio + claim signals ----
            await report("audio", 65, "🎵 Analysing audio track, claim and web context...")
            has_claim = bool(claim and claim.strip())
            middle = frames[len(frames) // 2]

            async def run_semantic():
                if not has_claim:
                    return {"score": 0.0, "status": "N/A (no claim)"}
                from PIL import Image
                import io
                buf = io.BytesIO()
                Image.fromarray(middle.image).save(buf, format="PNG")
                return await asyncio.to_thread(lambda: asyncio.run(semantic_stream.analyze(buf.getvalue(), claim)))

            async def run_context():
                if not has_claim:
                    return {"evidence_found": False, "summary": "", "sources": []}
                return await asyncio.to_thread(lambda: asyncio.run(self._run_context_stream(claim)))

            audio, semantic, context = await asyncio.gather(
                self._analyze_video_audio(audio_file), run_semantic(), run_context(), return_exceptions=True
            )
            if isinstance(audio, Exception):
                audio = {"score": 0.0, "status": f"Error: {audio}", "usable": False}
            if isinstance(semantic, Exception):
                semantic = {"score": 0.0, "status": f"Error: {semantic}"}
            if isinstance(context, Exception):
                context = {"evidence_found": False, "summary": "", "sources": [], "error": str(context)}

            multimodal = None
            if settings.VIDEO_AV_CONSISTENCY and audio_is_usable(audio):
                await report("multimodal", 82, "🔗 Checking audio-visual consistency...")
                multimodal = await asyncio.to_thread(self._run_av_consistency, middle, audio_file, workdir)

            # ---- 6. Fusion ----
            await report("fusion", 90, "⚖️ Combining signals into a verdict...")
            fusion = fuse_video(
                visual, audio, settings.VIDEO_FAKE_THRESHOLD, settings.VIDEO_UNCERTAIN_MARGIN,
                audio_can_convict=settings.VIDEO_AUDIO_CAN_CONVICT,
            )

            timeline = visual.pop("timeline")
            segments = visual.pop("segments")
            peak_index = visual.pop("peak_index")
            for entry, frame in zip(timeline, frames):
                entry["thumb"] = vp.thumbnail_b64(frame.image, width=160)
            peak = frames[peak_index]
            video_block = {
                **info.public(),
                "frames_analyzed": len(frames),
                "timeline": timeline,
                "segments": segments,
                "peak_frame": {
                    "index": peak.index,
                    "time": round(peak.time, 2),
                    "score": timeline[peak_index]["score"],
                    "image": vp.thumbnail_b64(peak.image, width=640, quality=80),
                },
                "drivers": fusion["drivers"],
                "notes": fusion["notes"],
            }

            result = {
                "media_type": "video",
                "media_sha256": media_sha256,
                "verdict": fusion["verdict"],
                "confidence_score": fusion["confidence_score"],
                "risk_score": fusion["risk_score"],
                "visual": visual,
                "semantic": semantic,
                "context": context,
                "audio": audio,
                "metadata": metadata_result,
                "video": video_block,
                "cost_optimized": False,
            }
            if multimodal is not None:
                result["multimodal"] = multimodal
            return result
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    async def _analyze_video_audio(self, audio_file: Optional[str]) -> Dict[str, Any]:
        """Run the synthetic-voice detector on an extracted track. `usable` says whether it may vote."""
        from ..utils import video_processor as vp

        if not audio_file:
            return {"score": 0.0, "status": "No Audio Track", "usable": False}
        level = await asyncio.to_thread(vp.audio_rms, audio_file)
        if level < 0.003:  # about -50 dBFS: nothing to analyse
            return {"score": 0.0, "status": "Silent Audio Track", "usable": False, "details": {"rms": round(level, 5)}}

        from ..streams.audio import audio_stream
        with open(audio_file, "rb") as fh:
            audio_bytes = fh.read()
        result = await asyncio.to_thread(lambda: asyncio.run(audio_stream.analyze(audio_bytes)))
        result["usable"] = not str(result.get("status", "")).startswith("Error")
        return result

    def _run_av_consistency(self, frame, audio_file: str, workdir: str) -> Dict[str, Any]:
        """ImageBind similarity between one frame and the audio. Informational; never votes."""
        try:
            from PIL import Image
            from ..streams.multimodal import multimodal_stream

            frame_path = os.path.join(workdir, "av_frame.png")
            Image.fromarray(frame.image).save(frame_path)
            return multimodal_stream.analyze(frame_path, audio_file)
        except Exception as exc:
            return {"score": 0.0, "status": "Error", "details": str(exc)}

orchestrator = Orchestrator()
