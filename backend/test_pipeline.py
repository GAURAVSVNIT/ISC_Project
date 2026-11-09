
import asyncio
import argparse
import sys
import os
import json
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from backend.core.orchestrator import Orchestrator

async def run_pipeline_test(image_path: str, caption: str):
    print(f"\n--- Starting Full Pipeline Test ---")
    print(f"Image: {image_path}")
    print(f"Caption: {caption}")
    
    orchestrator = Orchestrator()
    
    # Helper to load bytes
    import requests
    def get_bytes(path_or_url):
        if path_or_url.startswith("http"):
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            resp = requests.get(path_or_url, headers=headers)
            print(f"DEBUG: Download Status Code: {resp.status_code}")
            print(f"DEBUG: Content Type: {resp.headers.get('Content-Type')}")
            return resp.content
        with open(path_or_url, "rb") as f:
            return f.read()

    print(f"\n[Loading Image] {image_path}")
    try:
        image_bytes = get_bytes(image_path)
    except Exception as e:
        print(f"Error loading image: {e}")
        return

    print("\n[Running Pipelines...]")
    # The Orchestrator method is process_request(file_bytes, claim)
    result = await orchestrator.process_request(image_bytes, caption)
    
    print("\n[Final Output]")
    print("-" * 50)
    print(json.dumps(result, indent=2))
    print("-" * 50)
    
    with open("pipeline_result.json", "w") as f:
        json.dump(result, f, indent=2)

    if result.get("status") == "success":
        print("\n✅ Pipeline SUCCESS")
    else:
        print("\n❌ Pipeline FAILED or INCOMPLETE (Check API Keys/Errors)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PVeritas Pipeline Test")
    parser.add_argument("--image", type=str, help="Path to image file or URL", 
                        default="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Frank_Sinatra_in_1957.jpg/800px-Frank_Sinatra_in_1957.jpg")
    parser.add_argument("--caption", type=str, help="Claim to verify", 
                        default="Frank Sinatra posing for a mugshot in 1938")
    
    args = parser.parse_args()
    
    asyncio.run(run_pipeline_test(args.image, args.caption))
