from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import base64
import asyncio
import json
import os
from dotenv import load_dotenv

# Explicitly load environment variables
load_dotenv()

from .config import settings
from .schemas import HealthResponse, AnalysisResponse

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

# Set Rate Limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/", tags=["Status"])
@limiter.limit("10/minute")
def root(request: Request):
    return {"status": "API is running", "docs": "/docs"}

@app.get("/health", response_model=HealthResponse, tags=["Status"])
def health_check():
    return {
        "status": "ok",
        "service": "project-veritas-backend"
    }

# --- FUSION ENGINE ---
def calculate_fusion_score(visual_score: float, semantic_score: float, audio_score: float = None, multimodal_score: float = None) -> tuple[str, float]:
    """
    Weighted Late Fusion Strategy:
    - Visual (Genesis): Artifact Detection.
    - Semantic (CLIP): Text-Image Consistency.
    - Audio (Wav2Vec2): Fake Audio Detection.
    - Multimodal (ImageBind): Audio-Visual Consistency.
    """
    # normalize inputs
    s_vis = float(visual_score or 0.0)
    s_sem = float(semantic_score or 0.0) # 1.0 = Consistent (Real)
    
    # Invert Semantic to Risk (1.0 = Inconsistent/Fake)
    risk_sem = 1.0 - s_sem
    
    risk_score = 0.0
    
    if multimodal_score is not None:
        # VIDEO with Semantic Audio-Visual Check
        # Multimodal Score: 1.0 = Consistent (Real). Risk = 1.0 - Score.
        risk_multi = 1.0 - float(multimodal_score)
        
        # New Formula: 
        # Visual (40%) + Multimodal (40%) + Semantic (20%)
        risk_score = (0.4 * s_vis) + (0.4 * risk_multi) + (0.2 * risk_sem)
        
    elif audio_score is not None:
        # Fallback VIDEO (if Multimodal failed but Audio exists?)
        s_aud = float(audio_score or 0.0)
        risk_score = (0.5 * s_vis) + (0.3 * risk_sem) + (0.2 * s_aud)
    else:
        # IMAGE Only
        # Weights: Vis(0.625) + Sem(0.375)
        risk_score = (0.625 * s_vis) + (0.375 * risk_sem)
        
    final_verdict = "Fake" if risk_score >= 0.5 else "Authentic"
    confidence = risk_score if final_verdict == "Fake" else (1.0 - risk_score)
    
    return final_verdict, confidence

class AnalysisError(Exception):
    """Analysis could not produce a trustworthy result (shown to the user as an error)."""


def _format_audio_result(stream_results: dict) -> dict:
    """
    Turn orchestrator.process_audio_request() output into the API response shape.
    A failed detector raises instead of being reported as "Authentic" (an error
    result carries score 0.0, which would otherwise read as 100% authentic).
    """
    audio_result = stream_results.get("audio") or {}
    status = str(audio_result.get("status", "Unknown"))
    if status.startswith("Error"):
        raise AnalysisError(f"Audio analysis failed: {status}")

    score = float(audio_result.get("score", 0.0))
    is_fake = score >= 0.5
    return {
        "verdict": "Fake" if is_fake else "Authentic",
        "confidence_score": float(score if is_fake else 1.0 - score),
        "explanation": f"Audio analysis indicates {status}",
        "visual": stream_results.get("visual", {}),
        "semantic": stream_results.get("semantic", {}),
        "context": stream_results.get("contextual", {}),
        "audio": audio_result,
        "metadata": stream_results.get("metadata"),
        "cost_optimized": bool(stream_results.get("cost_optimized", False)),
        "media_type": "audio",
    }


async def _finalize_video(result: dict, claim: str) -> dict:
    """Add the LLM explanation and the audit-ledger entry to a finished video result."""
    from .core.llm_reasoner import reasoner
    from .core.blockchain import ledger

    # The LLM call is blocking network I/O: keep it off the event loop.
    result["explanation"] = await asyncio.to_thread(reasoner.explain, result, claim)
    result["verification"] = ledger.add_block({
        "claim": claim,
        "media_type": "video",
        "media_sha256": result.get("media_sha256"),
        "verdict": result["verdict"],
        "confidence": result["confidence_score"],
        "visual_score": (result.get("visual") or {}).get("score"),
        "audio_score": (result.get("audio") or {}).get("score") if (result.get("audio") or {}).get("usable") else None,
        "model_version": settings.VERSION,
    })
    return result


@app.post(f"{settings.API_V1_STR}/analyze", response_model=AnalysisResponse, tags=["Analysis"])
@limiter.limit("10/minute")
@limiter.limit("10/minute")
async def analyze(
    request: Request,
    claim: str = Form(...),
    file: UploadFile = File(...)
):
    from .defense.art_shield import shield
    from .core.orchestrator import orchestrator
    from .core.llm_reasoner import reasoner
    
    
    from fastapi import HTTPException
    
    # 1. Validate Content-Length if present
    content_length = file.size
    if content_length and content_length > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 100MB.")

    # Reading file bytes
    file_bytes = await file.read()
    
    # --- 🚨 X-RAY DEBUG BLOCK 🚨 ---
    print(f"DEBUG: Received file size: {len(file_bytes)} bytes")
    if len(file_bytes) > 20:
        print(f"DEBUG: First 20 bytes (Hex): {file_bytes[:20].hex()}")
        print(f"DEBUG: First 20 bytes (Raw): {file_bytes[:20]}")
    else:
        print(f"DEBUG: Full content (Hex): {file_bytes.hex()}")
    # ----------------------------------
    
    # 2. Double check actual size after reading
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 100MB.")

    # Determine Media Type
    content_type = file.content_type if file.content_type else "image/png"
    print(f"DEBUG: Analyzed Content-Type: {content_type} | Filename: {file.filename}")
    
    # DEBUG: Fallback to video/mp4 based on extension
    if content_type in ["application/octet-stream", "binary/octet-stream"]:
        if file.filename.lower().endswith(('.mp4', '.mov', '.webm', '.avi')):
            content_type = "video/mp4"

    # --- 🚨 INFALLIBLE TYPE DETECTION 🚨 ---
    # Try to open as image first. If it fails, it MUST be video/audio.
    
    is_image = False
    is_video = False
    is_audio = content_type.startswith("audio/") # Trust Audio MIME slightly more or rely on failure
    
    import io
    from PIL import Image, UnidentifiedImageError
    
    try:
        # Clone bytes to safe buffer
        check_stream = io.BytesIO(file_bytes)
        img = Image.open(check_stream)
        img.verify() # Check integrity
        is_image = True
        print("DEBUG: PIL successfully identified file as IMAGE.")
    except Exception:
        print("DEBUG: PIL failed to identify image -> Assuming VIDEO/AUDIO path.")
        is_image = False
        is_video = True # Default to video if not image
        
    # Override generic detections
    if is_video and not is_audio:
        content_type = "video/mp4" # Force video type for downstream logic
    
    if is_audio:
        is_video = False # Ensure mutually exclusive handles 

    if is_video:
        # --- VIDEO PIPELINE ---
        from .utils.video_processor import VideoError
        try:
            video_result = await orchestrator.process_video_request(file_bytes, claim, filename=file.filename)
            if video_result.get("media_type") == "audio":
                # Audio-only container (e.g. .m4a) that arrived without an audio MIME type.
                return _format_audio_result(video_result)
            return await _finalize_video(video_result, claim)
        except (VideoError, AnalysisError) as e:
            raise HTTPException(status_code=422, detail=str(e))
        except RuntimeError as e:
            # Detector could not load/run: report it, never guess a verdict.
            raise HTTPException(status_code=503, detail=str(e))

    if is_audio:
        # --- AUDIO PIPELINE ---
        stream_results = await orchestrator.process_audio_request(file_bytes, claim)
        try:
            return _format_audio_result(stream_results)
        except AnalysisError as e:
            raise HTTPException(status_code=422, detail=str(e))

    # --- IMAGE PIPELINE ---
    
    
    # 1. Defense Layer (Mandatory)
    stego_detected = False
    
    # Save raw bytes for metadata analysis (ArtShield strips metadata)
    raw_bytes = file_bytes 
    
    # Check for Steganography (Trailing Bytes) - Use RAW bytes
    if shield.detect_trailing_bytes(raw_bytes):
        print(f"SECURITY WARNING: Suspicious trailing bytes detected in {file.filename}")
        stego_detected = True
    
    # Apply defense preprocessing (ArtShield)
    file_bytes = shield.sanitize(file_bytes)
    
    # 2. Orchestration Layer (Triangle of Truth)
    # Pass both cleaned bytes (for visual models) and raw bytes (for metadata)
    stream_results = await orchestrator.process_request(file_bytes, claim, raw_bytes=raw_bytes)
    
    # Inject Security Warnings into Metadata
    if stego_detected:
        if stream_results.get("metadata") is None:
            stream_results["metadata"] = {}
        stream_results["metadata"]["security_warning"] = "Steganography Detected (Trailing Data)"
    
    visual_result = stream_results.get("visual", {})
    
    # 3. Aggregation Logic
    # If visual forensic score > 0.5 (Fake), verdict is Fake.
    # Otherwise check consistency.
    is_fake_visual = visual_result.get("score", 0.0) >= 0.5
    
    final_verdict = "Fake" if is_fake_visual else "Authentic"
    confidence = visual_result.get("score", 0.0) if is_fake_visual else (1.0 - visual_result.get("score", 0.0))
    
    # 4. Explainable AI (LLM Reasoner)
    explanation_text = reasoner.explain(stream_results, claim)

    # 5. Blockchain Audit Trail
    from .core.blockchain import ledger
    audit_data = {
        "claim": claim,
        "verdict": final_verdict,
        "confidence": confidence,
        "visual_score": visual_result.get("score"),
        "timestamp": asyncio.get_event_loop().time()
    }
    verification = ledger.add_block(audit_data)
    
    # Construct flattened response matching AnalysisResponse schema
    return {
        "verdict": final_verdict,
        "confidence_score": float(confidence),
        "explanation": explanation_text,
        "visual": stream_results.get("visual", {}),
        "semantic": stream_results.get("semantic", {}),
        "context": stream_results.get("contextual", {}),
        "audio": stream_results.get("audio"),
        "metadata": stream_results.get("metadata"),
        "cost_optimized": stream_results.get("cost_optimized", False),
        "verification": verification
    }
    
def _looks_like_audio(data: bytes) -> bool:
    """Sniff common audio containers by magic bytes (MP3, WAV, FLAC, OGG, AAC/ADTS)."""
    h = data[:12]
    if h.startswith(b"ID3") or h.startswith(b"fLaC") or h.startswith(b"OggS"):
        return True
    if h[:4] == b"RIFF" and h[8:12] == b"WAVE":
        return True
    # MPEG audio frame sync (11 set bits) and ADTS AAC
    if len(h) >= 2 and h[0] == 0xFF and (h[1] & 0xE0) == 0xE0:
        return True
    return False

@app.websocket("/ws/analyze")
async def analyze_realtime(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analysis with progress updates.
    Provides engaging UX by showing each processing stage.
    """
    await websocket.accept()
    
    try:
        # Two upload protocols are accepted:
        #  1. Legacy: one JSON message {"image": <base64>, "claim": ...}. Limited by the
        #     WebSocket message size (16 MB by default), so only suitable for small files.
        #  2. Chunked: JSON {"type": "start", "claim", "filename", "size"}, then binary
        #     frames with the file contents, then JSON {"type": "end"}. Used for video.
        data = await websocket.receive_json()
        claim = data.get("claim", "") or ""
        filename = data.get("filename")
        enable_defense = True # Enforced

        if data.get("type") == "start":
            declared = int(data.get("size") or 0)
            if declared > settings.MAX_UPLOAD_SIZE:
                raise AnalysisError("File too large. Maximum size is 100MB.")
            buffer = bytearray()
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    raise WebSocketDisconnect()
                if message.get("bytes") is not None:
                    buffer.extend(message["bytes"])
                    if len(buffer) > settings.MAX_UPLOAD_SIZE:
                        raise AnalysisError("File too large. Maximum size is 100MB.")
                elif message.get("text") is not None:
                    if json.loads(message["text"]).get("type") == "end":
                        break
            image_bytes = bytes(buffer)
        else:
            image_bytes = base64.b64decode(data.get("image") or "")

        if not image_bytes:
            raise AnalysisError("Empty upload.")
        raw_bytes = image_bytes # Save original for metadata check
        
        from .defense.art_shield import shield
        from .core.orchestrator import orchestrator
        from .utils.metadata_filter import metadata_filter
        
        # --- 🚨 ROBUST TYPE DETECTION 🚨 ---
        is_video = False
        import io
        from PIL import Image
        try:
             Image.open(io.BytesIO(image_bytes)).verify()
        except Exception:
             is_video = True # PIL failed -> Assume Video/Audio

        # Audio files (mp3/wav/flac/ogg/aac) must not go to the video pipeline.
        if is_video and _looks_like_audio(image_bytes):
             is_video = False
             await websocket.send_json({
                "stage": "audio_processing",
                "progress": 20,
                "message": "🎵 Analyzing Audio...",
                "status": "processing"
             })

             stream_results = await orchestrator.process_audio_request(image_bytes, claim)
             audio_payload = _format_audio_result(stream_results)
             await websocket.send_json({
                "stage": "complete",
                "progress": 100,
                "message": f"✅ Audio Analysis Complete - {audio_payload['verdict']}",
                "status": "success",
                "results": audio_payload
             })
             return

        if is_video:
             # --- VIDEO PIPELINE ---
             async def video_progress(stage: str, percent: int, message: str):
                 await websocket.send_json({
                    "stage": stage, "progress": percent, "message": message, "status": "processing"
                 })

             final_result = await orchestrator.process_video_request(
                 image_bytes, claim, progress=video_progress, filename=filename
             )

             if final_result.get("media_type") == "audio":
                 # Audio-only container (e.g. .m4a): the orchestrator ran the audio pipeline.
                 audio_payload = _format_audio_result(final_result)
                 await websocket.send_json({
                    "stage": "complete",
                    "progress": 100,
                    "message": f"✅ Audio Analysis Complete - {audio_payload['verdict']}",
                    "status": "success",
                    "results": audio_payload
                 })
                 return

             await video_progress("explanation", 95, "📝 Writing forensic report...")
             final_result = await _finalize_video(final_result, claim)

             await websocket.send_json({
                "stage": "complete",
                "progress": 100,
                "message": f"✅ Video Analysis Complete - {final_result['verdict']}",
                "status": "success",
                "results": final_result
            })
             return

        # --- IMAGE PIPELINE (Mandatory Defense) ---
        # Stage 1: Defense (Mandatory)
        await websocket.send_json({
            "stage": "defense",
            "progress": 5,
            "message": "🛡️ Applying adversarial defense...",
            "status": "processing"
        })
        # Sanitize for visual models
        image_bytes = shield.sanitize(image_bytes)
        await asyncio.sleep(0.3)  # Simulate processing
        
        # Stage 2: Metadata Check - CRITICAL: Use raw_bytes
        await websocket.send_json({
            "stage": "metadata",
            "progress": 15,
            "message": "📋 Checking EXIF metadata...",
            "status": "processing"
        })
        
        metadata_result = metadata_filter.check(raw_bytes)
        
        if metadata_result["should_short_circuit"]:
            # FAST PATH - AI tags found
            await websocket.send_json({
                "stage": "complete",
                "progress": 100,
                "message": "✅ AI metadata detected - instant verdict",
                "status": "success",
                "results": {
                    "verdict": "Fake",
                    "confidence_score": 1.0,
                    "explanation": f"AI software detected in metadata: {metadata_result['ai_tags'][0]}",
                    "visual": {"score": 1.0, "status": "AI-Generated (Metadata)"},
                    "cost_optimized": True
                }
            })
            return
        
        # Stage 3: Visual Analysis (ConvNeXt)
        await websocket.send_json({
            "stage": "visual",
            "progress": 40,
            "message": "🔍 Running ConvNeXt AI detection...",
            "status": "processing"
        })
        
        from .streams.genesis import genesis_stream
        visual_result = await genesis_stream.analyze(image_bytes, generate_heatmap=True)
        
        # Stage 4: Semantic Analysis
        await websocket.send_json({
            "stage": "semantic",
            "progress": 65,
            "message": "🧠 Analyzing claim consistency...",
            "status": "processing"
        })
        
        from .streams.semantic import semantic_stream
        semantic_result = await semantic_stream.analyze(image_bytes, claim)
        
        # Stage 5: Context Search
        await websocket.send_json({
            "stage": "context",
            "progress": 85,
            "message": "🌐 Searching web for evidence...",
            "status": "processing"
        })
        
        # Get context stream result
        context_result = await orchestrator._run_context_stream(claim)
        
        # Stage 6: Complete
        # 3. Aggregation Logic (Weighted Fusion)
        final_verdict, confidence = calculate_fusion_score(
            visual_result.get("score", 0.0),
            semantic_result.get("score", 0.0),
            audio_score=None
        )
        
        # Explainable AI (LLM Reasoner)
        from .core.llm_reasoner import reasoner
        
        # Synthesize results for the reasoner
        agg_results = {
            "visual": visual_result,
            "semantic": semantic_result,
            "contextual": context_result,
            "metadata": metadata_result
        }
        explanation_text = reasoner.explain(agg_results, claim)
        
        # Blockchain Audit Trail
        from .core.blockchain import ledger
        audit_data = {
            "claim": claim,
            "verdict": final_verdict,
            "confidence": confidence,
            "visual_score": visual_result.get("score"),
            "model_version": settings.VERSION
        }
        verification = ledger.add_block(audit_data)
        
        await websocket.send_json({
            "stage": "complete",
            "progress": 100,
            "message": f"Analysis complete - {final_verdict}",
            "status": "success",
            "results": {
                "verdict": final_verdict,
                "confidence_score": float(confidence),
                "explanation": explanation_text,
                "visual": visual_result,
                "semantic": semantic_result,
                "context": context_result,
                "metadata": metadata_result,
                "audio": None,
                "cost_optimized": False,
                "verification": verification
            }
        })
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({
            "stage": "error",
            "progress": 0,
            "message": f" Error: {str(e)}",
            "status": "error"
        })
