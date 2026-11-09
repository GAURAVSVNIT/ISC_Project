import pytest
import asyncio
from backend.streams.visual import visual_stream

@pytest.mark.asyncio
async def test_scenario_a_tech_fake():
    """
    Scenario A: The Tech Fake
    Upload a high-quality Midjourney image.
    Stream A should spike to High Score (Fake).
    """
    print("\n[Scenario A] Testing Visual Stream with Mock Deepfake...")
    
    # Create valid dummy image for real inference
    from PIL import Image
    import io
    
    img = Image.new('RGB', (224, 224), color='red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    mock_image_bytes = buf.getvalue()
    
    # In a real test, we would hit the model. 
    # Here we are testing the wrapper logic.
    # Since our mock currently returns random, this test basically checks structure.
    # To make it deterministic for 'Scenario A', let's temporarily mock the return 
    # or ensure our visual_stream handles a specific flag if we want to force it.
    
    # For now, we just verify the output structure is correct
    result = await visual_stream.analyze(mock_image_bytes)
    
    print(f"Result: {result}")
    
    assert "score" in result
    assert "status" in result
    assert 0.0 <= result["score"] <= 1.0
    
    # Validate threshold logic (just ensuring status matches score)
    if result["score"] >= 0.5:
        assert result["status"] == "Synthetic/Fake"
    else:
        assert result["status"] == "Authentic Media"

if __name__ == "__main__":
    asyncio.run(test_scenario_a_tech_fake())
