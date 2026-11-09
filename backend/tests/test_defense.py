import pytest
from backend.defense.art_shield import shield
from PIL import Image
import io

def test_scenario_c_defense_mechanism():
    """
    Scenario C Step 2: Veritas Shield
    Turn on 'Veritas Shield' and verify image matches processing pipeline.
    """
    print("\n[Scenario C] Testing Veritas Shield...")
    
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    original_bytes = img_byte_arr.getvalue()
    
    # Apply defense
    sanitized_bytes = shield.sanitize(original_bytes)
    
    # Verify we got bytes back
    assert isinstance(sanitized_bytes, bytes)
    assert len(sanitized_bytes) > 0
    
    # Verify image is still valid
    out_img = Image.open(io.BytesIO(sanitized_bytes))
    assert out_img.format == "JPEG"
    # Size might be slightly different due to resize, but close
    w, h = out_img.size
    assert w == 100 and h == 100
    
    print("Defense mechanism successfully processed image.")

if __name__ == "__main__":
    test_scenario_c_defense_mechanism()
