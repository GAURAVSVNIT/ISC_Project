import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.streams.genesis import genesis_stream

IMAGE_PATH = r"S:\Echelon\backend\test\images\104655605.webp"
OUTPUT_PATH = r"S:\Echelon\backend\test\images\heatmap_output.png"

async def test_gradcam():
    print(f"🔬 Testing Grad-CAM on: {IMAGE_PATH}")
    
    if not os.path.exists(IMAGE_PATH):
        print("❌ Image file not found!")
        return

    with open(IMAGE_PATH, "rb") as f:
        image_bytes = f.read()
    
    print("Running inference with Grad-CAM...")
    result = await genesis_stream.analyze(image_bytes, generate_heatmap=True)
    
    print(f"\n⬇️  ANALYSIS RESULT ⬇️")
    print(f"Status: {result['status']}")
    print(f"Score:  {result['score']:.4f} (0=Real, 1=Fake)")
    
    if "heatmap" in result:
        import base64
        print(f"✅ Heatmap generated!")
        print(f"   Base64 length: {len(result['heatmap'])} chars")
        
        # Save heatmap to file
        heatmap_data = base64.b64decode(result['heatmap'])
        with open(OUTPUT_PATH, "wb") as f:
            f.write(heatmap_data)
        print(f"   Saved to: {OUTPUT_PATH}")
    else:
        print("⚠️ No heatmap generated (score < 0.3)")

if __name__ == "__main__":
    asyncio.run(test_gradcam())
