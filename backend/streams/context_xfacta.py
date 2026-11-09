import os
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()

def fetch_xfacta_evidence(query, max_results=3):
    """
    Uses SerpApi (Google Search) to find evidence.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        print("Error: SERPAPI_API_KEY not found in environment variables.")
        return ""

    try:
        print(f"DEBUG: Searching for '{query}' using SerpApi...")
        params = {
            "q": query,
            "api_key": api_key,
            "num": max_results
        }
        
        search = GoogleSearch(params)
        results = search.get_dict().get("organic_results", [])
        
        print(f"DEBUG: Found {len(results)} results.")
        evidence_data = {
            "text": "",
            "sources": []
        }
        
        if results:
            # Combine snippets into one evidence block for summary
            snippets = [r.get('snippet', r.get('title', '')) for r in results]
            links = [r.get('link', '') for r in results]
            
            evidence_data["text"] = "\n".join([f"- {s}" for s in snippets])
            evidence_data["sources"] = links
            
        return evidence_data
    except Exception as e:
        print(f"Error fetching evidence: {e}")
        return {"text": "", "sources": []}
