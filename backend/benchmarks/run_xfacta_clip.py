import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import sys
import os

# Add backend directory to sys.path to allow imports
# When running via 'uv run backend/benchmarks/...' from root, we need to add 'backend' to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from integrations.xfacta_loader import XFactaLoader
except ImportError:
    # If the above fails, might be direct execution or different structure
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'integrations')))
    from integrations.xfacta_loader import XFactaLoader

def main():
    # 1. Setup CLIP ViT-L/14 (The Heavy Model)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading CLIP ViT-L/14 on {device}...")

    model_id = "openai/clip-vit-large-patch14"
    try:
        model = CLIPModel.from_pretrained(model_id).to(device)
        processor = CLIPProcessor.from_pretrained(model_id)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # 2. Load XFacta Data
    # Assuming XFacta dataset is in d:\CODING\Echelon\backend\data
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data')
    # Resolve absolute path
    data_path = os.path.abspath(data_path)
    
    loader = XFactaLoader(data_path) 
    
    print(f"Loading data from {data_path}...")
    fakes = loader.load_batch(1, "fake_sample")
    reals = loader.load_batch(1, "real_sample")

    if not fakes and not reals:
        print(f"No data found at {data_path}. Please check the path.")
        return

    def get_clip_score(image_path, text):
        try:
            image = Image.open(image_path).convert("RGB")
            inputs = processor(
                text=[text[:77]], 
                images=image, 
                return_tensors="pt", 
                padding=True
            ).to(device)
            
            with torch.no_grad():
                outputs = model(**inputs)
                # Normalize embeddings for Cosine Similarity
                img_embeds = outputs.image_embeds / outputs.image_embeds.norm(p=2, dim=-1, keepdim=True)
                text_embeds = outputs.text_embeds / outputs.text_embeds.norm(p=2, dim=-1, keepdim=True)
                
                # Calculate Similarity (0.0 to 1.0)
                score = (img_embeds @ text_embeds.t()).item()
                return score
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return 0.0

    # 3. Benchmark Loop
    print("\n---  Benchmarking XFacta Fakes ---")
    if fakes:
        for item in fakes[:10]: # Test first 10
            score = get_clip_score(item['image'], item['claim'])
            print(f"Claim: {item['claim'][:40]}... | CLIP Score: {score:.3f}")
    else:
        print("No fake samples found for batch 1.")

    print("\n---  Benchmarking XFacta Reals ---")
    if reals:
        for item in reals[:10]: # Test first 10
            score = get_clip_score(item['image'], item['claim'])
            print(f"Claim: {item['claim'][:40]}... | CLIP Score: {score:.3f}")
    else:
        print("No real samples found for batch 1.")

if __name__ == "__main__":
    main()
