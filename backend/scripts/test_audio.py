import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

print("1. Testing Imports...")
try:
    import librosa
    print("   [+] librosa imported")
except ImportError as e:
    print(f"   [-] librosa FAILED: {e}")

try:
    from backend.streams.audio import audio_stream
    print("   [+] AudioStream imported")
except ImportError as e:
    print(f"   [-] AudioStream import FAILED: {e}")
    sys.exit(1)

print("\n2. Testing Model Loading (Lazy Load)...")
try:
    success = audio_stream._ensure_models_loaded()
    if success:
        print("   [+] Model loaded successfully!")
    else:
        print("   [-] Model loading returned False.")
except Exception as e:
    print(f"   [-] Model loading crashed: {e}")
