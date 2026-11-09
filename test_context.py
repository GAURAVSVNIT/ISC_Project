import asyncio
import os
from dotenv import load_dotenv

# Mock internal import path
import sys
sys.path.append(os.getcwd())

from backend.streams.context_xfacta import fetch_xfacta_evidence

def test_context():
    print("Testing Context XFacta...")
    # Load env for API key
    load_dotenv()
    
    query = "The earth is flat"
    result = fetch_xfacta_evidence(query)
    
    print(f"Query: {query}")
    print(f"Evidence Found: {bool(result['text'])}")
    print(f"Text Length: {len(result['text'])}")
    print(f"Sources: {result['sources']}")
    
    if result['text']:
        print("SUCCESS: Context stream is working.")
    else:
        print("FAILURE: No text returned.")

if __name__ == "__main__":
    test_context()
