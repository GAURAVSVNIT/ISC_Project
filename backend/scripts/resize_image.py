from PIL import Image
import os

INPUT_PATH = r"s:\Echelon\backend\test\images\ai-generated-9050182_1280.jpg"
OUTPUT_PATH = r"s:\Echelon\backend\test\images\ai-generated-small.jpg"

if os.path.exists(INPUT_PATH):
    img = Image.open(INPUT_PATH)
    print(f"Original Size: {img.size}")
    img = img.resize((512, 512)) # Reasonable for ConvNeXt
    img.save(OUTPUT_PATH, quality=85)
    print(f"Resized Saved: {OUTPUT_PATH}")
else:
    print("Input file not found")
