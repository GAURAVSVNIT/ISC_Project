from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import base64
import asyncio
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
        video_result = await orchestrator.process_video_request(file_bytes, claim)
        
        # Apply Fusion
        vis = video_result.get("visual", {}).get("score", 0.0)
        sem = video_result.get("semantic", {}).get("score", 0.0)
        aud = video_result.get("audio", {}).get("score")
        multi = video_result.get("multimodal", {}).get("score")
        
        v_verdict, v_conf = calculate_fusion_score(vis, sem, aud, multi)
        
        # Explainable AI (LLM Reasoner for Video)
        from .core.llm_reasoner import reasoner
        agg_results = {
            "visual": video_result.get("visual", {}),
            "semantic": video_result.get("semantic", {}),
            "audio": video_result.get("audio", {}),
            "multimodal": video_result.get("multimodal", {}),
            "metadata": video_result.get("metadata", {})
        }
        explanation_text = reasoner.explain(agg_results, claim)
        video_result["explanation"] = explanation_text
        
        # Blockchain (Mock/Real)
        from .core.blockchain import ledger
        audit_data = {
            "claim": claim,
            "verdict": v_verdict,
            "confidence": v_conf,
            "visual_score": vis,
            "timestamp": asyncio.get_event_loop().time()
        }
        video_result["verification"] = ledger.add_block(audit_data)
        
        return video_result
        
    if is_audio:
        # --- AUDIO PIPELINE ---
        stream_results = await orchestrator.process_audio_request(file_bytes, claim)
        
        audio_result = stream_results.get("audio", {})
        is_fake_audio = audio_result.get("score", 0.0) >= 0.5
        
        final_verdict = "Fake" if is_fake_audio else "Authentic"
        confidence = audio_result.get("score", 0.0) if is_fake_audio else (1.0 - audio_result.get("score", 0.0))
        
        return {
            "verdict": final_verdict,
            "confidence_score": float(confidence),
            "explanation": f"Audio analysis indicates {audio_result.get('status', 'Unknown')}",
            "visual": stream_results.get("visual", {}),
            "semantic": stream_results.get("semantic", {}),
            "context": stream_results.get("contextual", {}),
            "audio": audio_result,
            "metadata": None,
            "cost_optimized": False
        }

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
    
@app.websocket("/ws/analyze")
async def analyze_realtime(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analysis with progress updates.
    Provides engaging UX by showing each processing stage.
    """
    await websocket.accept()
    
    try:
        # Receive initial data
        data = await websocket.receive_json()
        image_base64 = data.get("image")
        claim = data.get("claim", "")
        enable_defense = True # Enforced
        
        # Decode image/video
        image_bytes = base64.b64decode(image_base64)
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
        
        if is_video:
             # --- VIDEO PIPELINE ---
             await websocket.send_json({
                "stage": "video_processing",
                "progress": 20,
                "message": "🎥 Analyzing Video Sequence (Frames + Audio)...",
                "status": "processing"
            })
             
             # Heavy lifting done by orchestrator (OpenCV + Models)
             final_result = await orchestrator.process_video_request(image_bytes, claim)
             
             if "error" in final_result:
                 raise Exception(final_result["error"])

             # --- FUSION & AGGREGATION ---
             vis = final_result.get("visual", {}).get("score", 0.0)
             sem = final_result.get("semantic", {}).get("score", 0.0)
             aud = final_result.get("audio", {}).get("score")
             multi = final_result.get("multimodal", {}).get("score")
             
             
             # Calculate Fusion directly (defined in global scope)
             v_verdict, v_conf = calculate_fusion_score(vis, sem, aud, multi)
             
             
             final_result["verdict"] = v_verdict
             final_result["confidence_score"] = float(v_conf)
             
             # Blockchain Audit
             from .core.blockchain import ledger
             audit_data = {
                "claim": claim,
                "verdict": v_verdict,
                "confidence": v_conf,
                "visual_score": vis,
                "model_version": settings.VERSION,
                "timestamp": asyncio.get_event_loop().time()
             }
             verification = ledger.add_block(audit_data)
             final_result["verification"] = verification

             # Explainable AI for Video
             from .core.llm_reasoner import reasoner
             agg_results = {
                 "visual": final_result.get("visual", {}),
                 "semantic": final_result.get("semantic", {}),
                 "audio": final_result.get("audio", {}),
                 "multimodal": final_result.get("multimodal", {}),
                 "metadata": final_result.get("metadata", {})
             }
             final_result["explanation"] = reasoner.explain(agg_results, claim)

             await websocket.send_json({
                "stage": "complete",
                "progress": 100,
                "message": f"✅ Video Analysis Complete - {v_verdict}",
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
