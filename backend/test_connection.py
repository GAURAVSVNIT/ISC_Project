
import asyncio
import sys
import os

# Ensure backend module can be imported
sys.path.append(os.getcwd())

from backend.streams.context import ContextGrounding

async def test_serpapi_connection():
    print("--- Testing SerpApi Connection ---")
    grounding = ContextGrounding()
    
    if not grounding.api_key:
        print("FAIL: API Key not found.")
        return False

    # Test with a simple query
    query = "Apple Inc"
    print(f"Querying: {query}...")
    
    result = await grounding.execute_pipeline(query, verification_keywords=["technology", "iPhone", "Apple"])
    
    if result["status"] == "failed":
        print(f"FAIL: Pipeline failed with error: {result.get('error')}")
        return False
        
    results_list = result.get("results", [])
    if not results_list:
        print("WARNING: No results returned. API might be working but returned empty.")
        # This might be valid if query is weird, but for 'Apple Inc' it should return stuff.
        # Check raw response if available (not currently returned in execute_pipeline success path)
    
    print(f"SUCCESS: Retrieved {len(results_list)} results.")
    
    # Check verification
    verified_count = sum(1 for r in results_list if r.get("verification_status") == "verified")
    print(f"Verified items: {verified_count}/{len(results_list)}")
    
    if len(results_list) > 0:
        print("First result title:", results_list[0].get("title"))
        return True
    return False

if __name__ == "__main__":
    success = asyncio.run(test_serpapi_connection())
    if success:
        print("\nTest PASSED.")
        sys.exit(0)
    else:
        print("\nTest FAILED.")
        sys.exit(1)
