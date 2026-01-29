import os
import requests
from typing import List, Dict, Any 

class SearchMCP:
    def __init__(self):
        self.brave_key = os.getenv("BRAVE_API_KEY")
        self.tavily_key = os.getenv("TAVILY_API_KEY")

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Perform a web search using available provider (Brave > Tavily > Mock).
        """
        if self.brave_key:
            return self._search_brave(query, limit)
        elif self.tavily_key:
            return self._search_tavily(query, limit)
        
        return self._mock_search(query, limit)

    def _search_brave(self, query: str, limit: int) -> Dict[str, Any]:
        try:
            headers = {"Accept": "application/json", "X-Subscription-Token": self.brave_key}
            resp = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": limit},
                headers=headers
            )
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data.get("web", {}).get("results", []):
                    results.append({
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "snippet": item.get("description"),
                        "thumbnail": item.get("thumbnail", {}).get("src") if item.get("thumbnail") else None
                    })
                return {"results": results, "source": "brave"}
        except Exception as e:
            print(f"[SearchMCP] Brave Error: {e}")
        return self._mock_search(query, limit)

    def _search_tavily(self, query: str, limit: int) -> Dict[str, Any]:
        # Implementation for Tavily would go here
        return self._mock_search(query, limit)

    def _mock_search(self, query: str, limit: int) -> Dict[str, Any]:
        return {
            "results": [
                {
                    "title": f"Result {i+1} for {query}",
                    "url": f"https://example.com/result-{i}",
                    "snippet": f"This is a simulated search result for {query}. It contains text relevant to the query.",
                }
                for i in range(limit)
            ],
            "source": "mock"
        }

search_mcp = SearchMCP()
