import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.streams.genesis import genesis_stream

IMAGE_PATH = r"S:\Echelon\backend\test\images\104655605.webp"

async def test_image():
    print(f"--- Manual Verification: {IMAGE_PATH} ---")
    
    if not os.path.exists(IMAGE_PATH):
        print("❌ Image file not found!")
        return

    print("Reading image file...")
    with open(IMAGE_PATH, "rb") as f:
        image_bytes = f.read()
    
    print(f"Input size: {len(image_bytes)} bytes")
    print("Sending to Visual Stream (ConvNeXt Genesis)...")
    
    # Run analysis
    result = await genesis_stream.analyze(image_bytes)
    
    print("\n⬇️  ANALYSIS RESULT ⬇️")
    print("-------------------------")
    print(f"Status: {result['status']}")
    print(f"Score:  {result['score']:.4f} (0=Real, 1=Fake)")
    print(f"Model:  {result['model']}")
    print("-------------------------")

if __name__ == "__main__":
    asyncio.run(test_image())
