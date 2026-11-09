import asyncio
from typing import Dict, Any
import os

from ..streams.genesis import genesis_stream
from ..streams.semantic import semantic_stream
from ..utils.metadata_filter import metadata_filter
from ..utils.video_processor import extract_components
import os
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

    async def process_video_request(self, file_bytes: bytes, claim: str):
        """
        Process a VIDEO request:
        1. Container Metadata Check (Short Circuit)
        2. Extract Middle Frame -> Shield -> Stream A/B
        3. Extract Audio -> Stream D
        """
        # 1. Container Metadata Check (Optimization)
        metadata_result = metadata_filter.check(file_bytes)
        if metadata_result["should_short_circuit"]:
             return {
                "visual": {"score": 1.0, "status": "AI-Generated (Metadata)"},
                "semantic": {"score": 0.0, "status": "Skipped"},
                "audio": {"score": 1.0, "status": "AI-Generated (Metadata)"},
                "contextual": {"found": False},
                "metadata": metadata_result,
                "cost_optimized": True,
                "verdict": "Fake"
            }

        results = {}
        
        # 2. Component Extraction
        components = await extract_components(file_bytes)
        if not components:
            return {"error": "Failed to process video file."}
            
        image_path = components.get("image_path")
        audio_path = components.get("audio_path")
        
        tasks = []
        
        # 3. Visual Tasks (Stream A + Stream B + Metadata)
        img_bytes = None
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, "rb") as f:
                    img_bytes = f.read()
                
                # Cleanup frame file
                try: os.remove(image_path)
                except: pass
                
                # --- CRITICAL FIX: Apply ArtShield to Frame ---
                from ..defense.art_shield import shield
                # Apply same "Light Touch" defense as main image pipeline
                # 1. Save raw for fallback/metadata check inside process_request
                raw_frame_bytes = img_bytes
                # 2. Sanitize (Blur 0.5 + Resize)
                img_bytes = shield.sanitize(img_bytes)
                print(f"[Orchestrator] Video Frame Sanitized. Size: {len(img_bytes)} bytes")
                # -----------------------------------------------
            except Exception as e:
                print(f"[Orchestrator] Error processing frame: {e}")
                return {"error": f"Frame processing failing: {str(e)}"}

        # Sanity Check & Debug
        if not img_bytes:
            return {"error": "Video frame extraction failed (no bytes loaded)."}

        print(f"[Orchestrator] Read {len(img_bytes)} bytes. Header: {img_bytes[:10].hex() if len(img_bytes)>10 else img_bytes}")
        try:
            from PIL import Image
            import io
            Image.open(io.BytesIO(img_bytes)).verify()
            print("[Orchestrator] PIL Verify Success (Valid JPEG)")
        except Exception as e:
            print(f"[Orchestrator] CRITICAL: Generated frame is invalid: {e}")
            return {"error": "Internal Error: Extracted video frame caused encoding failure."}
        

        
      
        # 4. Execute Parallel
        pipeline_results = await asyncio.gather(*tasks, return_exceptions=True)
        from ..streams.genesis import genesis_stream
        from ..streams.semantic import semantic_stream
        from ..streams.audio import audio_stream
        from ..streams.multimodal import multimodal_stream
        
        # Define tasks
        task_visual = genesis_stream.analyze(img_bytes)
        task_semantic = semantic_stream.analyze(img_bytes, claim)
        
        # Task Audio
        async def run_audio():
            if audio_path and os.path.exists(audio_path):
                with open(audio_path, 'rb') as f:
                    a_bytes = f.read()
                return await audio_stream.analyze(a_bytes)
            return {"score": 0.0, "status": "No Audio"}
            
        task_audio = run_audio()

        # Task Multimodal (ImageBind)
        async def run_multimodal():
            if audio_path and os.path.exists(audio_path):
                # We use the extracted keyframe as the vision input for speed
                return await asyncio.to_thread(multimodal_stream.analyze, image_path, audio_path)
            return {"score": 0.0, "status": "No Audio for Multimodal"}

        task_multimodal = run_multimodal()

        # Execute
        results_list = await asyncio.gather(task_visual, task_semantic, task_audio, task_multimodal, return_exceptions=True)
        vis, sem, aud, multi = results_list
        
        # Clean up temp files (Critical!)
        try:
             if os.path.exists(image_path): os.remove(image_path)
             if audio_path and os.path.exists(audio_path): os.remove(audio_path)
        except Exception as e:
             print(f"[Orchestrator] cleanup error: {e}")

        # Assemble
        final = {
            "visual": vis if not isinstance(vis, Exception) else {"score": 0.0, "error": str(vis)},
            "semantic": sem if not isinstance(sem, Exception) else {"score": 0.0, "error": str(sem)},
            "audio": aud if not isinstance(aud, Exception) else {"score": 0.0, "error": str(aud)},
            "multimodal": multi if not isinstance(multi, Exception) else {"score": 0.0, "error": str(multi)}
        }
        
        return final    

orchestrator = Orchestrator()
