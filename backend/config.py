import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Project Veritas API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")
    OCR_SPACE_API_KEY: str = os.getenv("OCR_SPACE_API_KEY", "")
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Validation
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100 MB

    # Model Paths
    UNIVERSAL_FAKE_DETECT_PATH: str = "backend/weights/fc_weights.pth"

    # --- Video pipeline ---
    # Frame-level AI-generation detector. Chosen by benchmark (see docs/Video_Pipeline.md);
    # the revision is pinned so the weights cannot change underneath us.
    VIDEO_DETECTOR_MODEL: str = "buildborderless/CommunityForensics-DeepfakeDet-ViT"
    VIDEO_DETECTOR_REVISION: str = "ac6ee457bea904a373065754107451793b56db00"
    # Frame sampling: FRAMES_PER_SECOND of video, clamped to [MIN, MAX].
    VIDEO_FRAMES_PER_SECOND: float = 1.5
    VIDEO_MIN_FRAMES: int = 8
    VIDEO_MAX_FRAMES: int = 24
    # Videos longer than this are rejected (the frontend already limits uploads to 20 s).
    VIDEO_MAX_DURATION_S: float = 300.0
    # risk >= THRESHOLD -> Fake; risk in [THRESHOLD - MARGIN, THRESHOLD) -> Uncertain.
    VIDEO_FAKE_THRESHOLD: float = 0.5
    VIDEO_UNCERTAIN_MARGIN: float = 0.15
    # If False (default), a flagged voice track with clean pictures gives "Uncertain", not
    # "Fake": the voice detector produced false alarms on genuine speech in spot checks.
    VIDEO_AUDIO_CAN_CONVICT: bool = False
    # ImageBind audio-visual consistency (4.8 GB checkpoint). Informational only:
    # it is reported but never changes the verdict.
    VIDEO_AV_CONSISTENCY: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
