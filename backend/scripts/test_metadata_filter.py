import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.utils.metadata_filter import metadata_filter

def test_metadata_filter():
    test_images = {
        "Real Photo": r"backend\test\images\images.jpg",
        "AI-Generated": r"backend\test\images\ai-generated-9050182_1280.jpg"
    }
    
    print("=" * 70)
    print("METADATA PRE-FILTER TEST")
    print("=" * 70)
    
    for label, path in test_images.items():
        print(f"\n📁 Testing: {label}")
        print(f"   Path: {path}")
        print("-" * 70)
        
        try:
            with open(path, "rb") as f:
                image_bytes = f.read()
            
            result = metadata_filter.check(image_bytes)
            
            print(f"   Verdict: {result['verdict']}")
            print(f"   Confidence: {result['confidence']}")
            print(f"   Short Circuit: {'✅ YES (SAVE $$)' if result['should_short_circuit'] else '❌ NO (Run full pipeline)'}")
            print(f"   Reason: {result['reason']}")
            print(f"   AI Tags: {result['ai_tags'] or 'None'}")
            print(f"   Camera Data: {'Yes' if result['has_camera_metadata'] else 'No'}")
            
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print("\n" + "=" * 70)
    print("COST ANALYSIS:")
    print("- If 30% of images have AI tags → 30% cost reduction")
    print("- Metadata check: ~1ms vs GPU: ~200ms + API: ~1000ms")
    print("=" * 70)

if __name__ == "__main__":
    test_metadata_filter()
