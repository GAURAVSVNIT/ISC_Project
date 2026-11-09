import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    print("Importing semantic_stream...")
    from backend.streams.semantic import semantic_stream
    print("Import successful.")
    
    async def test():
        print("Testing analyze...")
        # Mock image bytes (1x1 pixel)
        mock_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        
        result = await semantic_stream.analyze(mock_image, "A test claim")
        print("Result:", result)

    if __name__ == "__main__":
        asyncio.run(test())
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
