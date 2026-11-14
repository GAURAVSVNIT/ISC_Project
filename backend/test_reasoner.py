
import asyncio
import argparse
import sys
import os
import json

# Ensure project root is in path
sys.path.append(os.getcwd())

from backend.streams.context import ContextGrounding
from backend.core.llm_reasoner import LLMReasoner
from backend.config import settings
from openai import AsyncOpenAI

async def run_test(image_path: str, caption: str):
    print(f"\n--- Starting Multimodal Reasoner Test ---")
    print(f"Image: {image_path}")
    print(f"Caption: {caption}")
    
    # 1. Fetch Context (Stream C)
    print("\n[1] Fetching Contextual Grounding Data...")
    grounding = ContextGrounding()
    context_result = await grounding.execute_pipeline(caption)
    
    context_data = context_result.get("evidence", [])
    if context_data:
        print(f"   -> Found {len(context_data)} evidence items.")
    else:
        print(f"   -> No ground truth evidence found.")

    # 2. Construct Prompt (LLM Reasoner)
    print("\n[2] Constructing Prompt via LLMReasoner...")
    reasoner = LLMReasoner()
    
    messages = reasoner.construct_prompt(
        image_source=image_path,
        caption=caption,
        context_data=context_data
    )
    print("   -> Prompt constructed successfully.")

    # 3. Execute API Call (Simulating Orchestrator role)
    print("\n[3] Executing API Call (Orchestrator Simulation)...")
    if not settings.GROQ_API_KEY:
        print("Error: GROQ_API_KEY not set in environment or config. Cannot execute model.")
        print("Dumping prompt structure instead:")
        print(json.dumps(messages, indent=2))
        return

    client = AsyncOpenAI(api_key=settings.GROQ_API_KEY, base_url=settings.GROQ_BASE_URL)
    
    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0
        )
        content = response.choices[0].message.content
        analysis = json.loads(content)
        
        print("\n[4] Final Verdict:")
        print("-" * 30)
        print(json.dumps(analysis, indent=2))
        print("-" * 30)
        
    except Exception as e:
        print(f"Error during API execution: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Phase 2 Reasoning Core")
    parser.add_argument("--image", type=str, help="Path to image file or URL", 
                        default="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Frank_Sinatra_in_1957.jpg/800px-Frank_Sinatra_in_1957.jpg")
    parser.add_argument("--caption", type=str, help="Claim to verify", 
                        default="Frank Sinatra posing for a mugshot in 1938")
    
    args = parser.parse_args()
    
    asyncio.run(run_test(args.image, args.caption))
