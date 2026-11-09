import requests
import binascii
import os
import sys

# Test Images
TEST_IMAGES = {
    # "REAL": r"s:\Echelon\backend\test\images\images.jpg",
    "FAKE": r"s:\Echelon\backend\test\images\ai-generated-small.jpg"
}

API_URL = "https://jenil1236-convnext-gradcam-api.hf.space/predict"

def test_genesis(label, image_path):
    print(f"\n--- Testing {label} Image: {image_path} ---")
    if not os.path.exists(image_path):
        print("❌ File not found.")
        return

    output_filename = f"gradcam_{label.lower()}.png"

    try:
        with open(image_path, "rb") as f:
            files = {
                "file": ("image.jpg", f, "image/jpeg")
            }
            print("Sending request to Genesis API...")
            response = requests.post(API_URL, files=files, timeout=30)
            
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return

        data = response.json()
        pred = data.get("prediction", "Unknown")
        print(f"🔮 Prediction: {pred}")

        # Save Heatmap
        hex_map = data.get("heatmap")
        if hex_map:
            png_bytes = binascii.unhexlify(hex_map)
            with open(output_filename, "wb") as f:
                f.write(png_bytes)
            print(f"🔥 Heatmap saved to {output_filename}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("Evaluating Genesis Model (ConvNeXt)...")
    for label, path in TEST_IMAGES.items():
        test_genesis(label, path)
