import os
import requests
from pathlib import Path

# Config
# Raw URL for the weights file from the official repo
WEIGHTS_URL = "https://github.com/WisconsinAIVision/UniversalFakeDetect/raw/main/pretrained_weights/fc_weights.pth"
WEIGHTS_DIR = Path("backend/weights")
WEIGHTS_PATH = WEIGHTS_DIR / "fc_weights.pth"

def setup_weights():
    print(f"Setting up weights in {WEIGHTS_DIR.resolve()}...")
    
    if not WEIGHTS_DIR.exists():
        WEIGHTS_DIR.mkdir(parents=True)
        print("Created weights directory.")

    print(f"Downloading real weights from {WEIGHTS_URL}...")
    
    try:
        response = requests.get(WEIGHTS_URL, stream=True)
        response.raise_for_status()
        
        with open(WEIGHTS_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print("✅ Download complete! Real weights are ready.")
        print(f"File size: {os.path.getsize(WEIGHTS_PATH)} bytes")
        
    except Exception as e:
        print(f"❌ Error downloading weights: {e}")

if __name__ == "__main__":
    setup_weights()
