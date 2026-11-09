import pytest
import asyncio
from backend.streams.semantic import semantic_stream

@pytest.mark.asyncio
async def test_scenario_b_mismatch():
    """
    Scenario B: The Narrative Fake (Mismatch)
    User claims "mismatch", Stream B should flag it.
    """
    print("\n[Scenario B] Testing Semantic Stream with Mismatch Claim...")
    
    mock_image_bytes = b"dummy_data"
    
    # Positive Case
    claim_consistent = "This is a truthful claim."
    result = await semantic_stream.analyze(mock_image_bytes, claim_consistent)
    print(f"Consistent Result: {result}")
    assert result["status"] == "Consistent"
    assert result["score"] > 0.5
    
    # Negative Case (Trigger mock mismatch)
    claim_inconsistent = "This image shows a mismatch."
    result_fake = await semantic_stream.analyze(mock_image_bytes, claim_inconsistent)
    print(f"Mismatch Result: {result_fake}")
    assert result_fake["status"] == "Inconsistent"
    assert result_fake["score"] < 0.5

if __name__ == "__main__":
    asyncio.run(test_scenario_b_mismatch())
