import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.streams.genesis import genesis_stream

async def test_convnext():
    test_images = {
        "REAL": r"backend\test\images\images.jpg",
        "FAKE": r"backend\test\images\ai-generated-9050182_1280.jpg"
    }
    
    for label, path in test_images.items():
        print(f"\n{'='*60}")
        print(f"Testing: {label} - {path}")
        print(f"{'='*60}")
        
        with open(path, "rb") as f:
            image_bytes = f.read()
        
        result = await genesis_stream.analyze(image_bytes)
        
        status_emoji = "✅" if (label == "FAKE" and result["score"] > 0.5) or (label == "REAL" and result["score"] < 0.5) else "❌"
        
        print(f"{status_emoji} Score: {result['score']:.4f}")
        print(f"   Status: {result['status']}")
        print(f"   Model: {result.get('model', 'N/A')}")
        if 'details' in result:
            print(f"   Details: Fake={result['details']['fake_prob']:.4f}, Real={result['details']['real_prob']:.4f}")

if __name__ == "__main__":
    asyncio.run(test_convnext())
