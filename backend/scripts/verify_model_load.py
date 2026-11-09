import torch
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.config import settings

def verify_load():
    print("--- Starting Model Verification ---")
    
    # 1. Check Weights File
    weight_path = settings.UNIVERSAL_FAKE_DETECT_PATH
    if os.path.exists(weight_path):
        size = os.path.getsize(weight_path)
        print(f"✅ Weights file found: {weight_path} ({size} bytes)")
    else:
        print(f"❌ Weights file NOT found at {weight_path}")
        return

    # 2. Import CLIP
    print("Importing CLIP...")
    try:
        import clip
        print(f"✅ CLIP module imported. Available models: {clip.available_models()}")
    except ImportError:
        print("❌ CLIP module not installed.")
        return

    # 3. Load Model (This triggers download if not cached)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading CLIP backbone on {device} (this may take time if downloading)...")
    
    try:
        model, preprocess = clip.load("ViT-L/14", device=device)
        print("✅ CLIP Backbone loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading CLIP: {e}")
        return

    # 4. Load Custom Weights
    print("Loading Linear Classifier weights...")
    try:
        fc_weights = torch.load(weight_path, map_location=device)
        print("✅ Custom weights loaded!")
        
        # Verify shape
        if isinstance(fc_weights, dict):
            keys = list(fc_weights.keys())
            print(f"   Weights config: dict with keys {keys}")
        else:
            print(f"   Weights tensor shape: {fc_weights.shape}")
            
    except Exception as e:
        print(f"❌ Error loading custom weights: {e}")
        return

    print("\n🎉 SUCCESS: UniversalFakeDetect is ready for inference!")

if __name__ == "__main__":
    verify_load()
