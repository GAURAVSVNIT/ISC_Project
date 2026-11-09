
import httpx
import logging
import asyncio
import re
import difflib
from typing import List, Dict, Any, Optional
from backend.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContextGrounding:
    """
    Level 3: Contextual Grounding Layer (Pure Evidence).
    Retrieves and ranks external evidence for a textual claim.
    No verdict, no scoring, no judgment.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SERPAPI_API_KEY
        if not self.api_key:
            logger.warning("SerpApi API key is missing. Web fetching will fail.")
        self.base_url = "https://serpapi.com/search.json"

    async def execute_pipeline(self, claim_text: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Orchestrates evidence retrieval and ranking.
        """
        if not claim_text:
            return {"query": claim_text, "evidence": []}

        # 1. Generate Queries
        queries = self._generate_queries(claim_text)
        
        # 2. Fetch Evidence (Async)
        raw_items = await self._fetch_all_evidence(queries)
        
        if not raw_items:
            return {"query": claim_text, "evidence": []}

        # 3. Process & Rank (Relevance only)
        ranked_evidence = self._rank_evidence(claim_text, raw_items)
        
        # 4. Limit to Top K
        selected_evidence = ranked_evidence[:top_k]
        
        return {
            "query": claim_text,
            "evidence": selected_evidence
        }

    def _generate_queries(self, claim: str) -> List[str]:
        """Generate diverse search queries to maximize coverage."""
        # Clean claim
        clean = re.sub(r'[^\w\s]', '', claim).strip()
        
        # Simple heuristic generation
        queries = [
            claim,  # Exact
            f"{clean} details",
            f"{clean} news",
            f"truth about {clean}",
            f"{clean} fact check"
        ]
        return list(set(queries))

    async def _fetch_all_evidence(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Fetch results for all queries concurrently."""
        tasks = [self._fetch_single_query(q) for q in queries]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_items = []
        seen_links = set()
        
        for res in results_list:
            if isinstance(res, list):
                for item in res:
                    link = item.get("link")
                    if link and link not in seen_links:
                        seen_links.add(link)
                        all_items.append(item)
        
        return all_items

    async def _fetch_single_query(self, query: str) -> List[Dict[str, Any]]:
        """Fetch ~5 results for a single query."""
        if not self.api_key:
            return []
            
        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": "google",
            "num": 5
        }
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(self.base_url, params=params, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                
                extracted = []
                # Organic results
                for item in data.get("organic_results", []):
                    extracted.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "link": item.get("link", ""),
                        "source": item.get("source", "Web"),
                        "date": item.get("date", "")
                    })
                # Knowledge Graph
                if "knowledge_graph" in data:
                    kg = data["knowledge_graph"]
                    extracted.append({
                        "title": kg.get("title", "Knowledge Graph"),
                        "snippet": kg.get("description", ""),
                        "link": kg.get("source", {}).get("link", ""),
                        "source": "Google Knowledge Graph",
                        "date": ""
                    })
                return extracted
            except Exception as e:
                logger.error(f"Search failed for '{query}': {e}")
                return []

    def _rank_evidence(self, claim: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank by semantic relevance to the claim."""
        for item in items:
            content = f"{item['title']} {item['snippet']}"
            # Relevance score: 0 to 1
            item['relevance_score'] = difflib.SequenceMatcher(None, claim.lower(), content.lower()).ratio()
            
        # Sort desc by relevance
        ranked = sorted(items, key=lambda x: x['relevance_score'], reverse=True)
        
        # Clean up temporary score if strictly not needed in final output, 
        # but useful for downstream debugging? User asked for strict struct.
        # "Each result must be annotated with...?" No, user said:
        # "Output contract: title, snippet, link, source, date".
        # Relevance is used ONLY for ranking.
        
        final_items = []
        for item in ranked:
            final_items.append({
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "link": item.get("link"),
                "source": item.get("source"),
                "date": item.get("date")
            })
            
        return final_items

# Simple self-test
if __name__ == "__main__":
    async def main():
        print("Testing Pure Evidence Context Grounding...")
        grounding = ContextGrounding()
        
        res = await grounding.execute_pipeline("The Eiffel Tower is in Paris")
        import json
        print(json.dumps(res, indent=2))

    asyncio.run(main())
