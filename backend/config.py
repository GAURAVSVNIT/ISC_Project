import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Project Veritas API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")
    OCR_SPACE_API_KEY: str = os.getenv("OCR_SPACE_API_KEY", "")
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Validation
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100 MB

    # Model Paths
    UNIVERSAL_FAKE_DETECT_PATH: str = "backend/weights/fc_weights.pth"
    
    class Config:
        env_file = ".env"

settings = Settings()
