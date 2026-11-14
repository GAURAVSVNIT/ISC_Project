from pydantic import BaseModel
from typing import Optional, Dict, Any, List

# --- Request Models ---

class AnalyzeRequest(BaseModel):
    claim: str
    media_url: Optional[str] = None
    # For file uploads, we generally handle them via Form data, 
    # but if we passed URLs this would be used.
    # In this project we'll likely use Multipart forms, so this model 
    # might be for the JSON part or metadata.
    enable_defense: bool = False

# --- Response Models ---

class StreamResult(BaseModel):
    score: float
    status: str
    details: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    verdict: str
    confidence_score: float
    explanation: str
    visual: Dict[str, Any]
    semantic: Dict[str, Any]
    context: Dict[str, Any]
    audio: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    cost_optimized: bool = False
    verification: Optional[Dict[str, Any]] = None # Blockchain Audit Data
    # Video pipeline
    media_type: Optional[str] = None            # "image" | "audio" | "video"
    media_sha256: Optional[str] = None          # SHA-256 of the uploaded file (also in the ledger)
    risk_score: Optional[float] = None          # 0 = authentic, 1 = fake (before thresholding)
    video: Optional[Dict[str, Any]] = None      # container facts, per-frame timeline, segments
    multimodal: Optional[Dict[str, Any]] = None # audio-visual consistency (informational)

class HealthResponse(BaseModel):
    status: str
    service: str
