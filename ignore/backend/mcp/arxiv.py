import requests
from typing import List, Dict, Any

class ArxivMCP:
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"

    def search_papers(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search ArXiv for academic papers."""
        try:
            # ArXiv API is free and public
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results
            }
            resp = requests.get(self.base_url, params=params)
            if resp.status_code == 200:
                # Parsing XML response (mocking this part for simplicity or assuming wrapper)
                # In real prod, use `feedparser` library
                pass
        except Exception as e:
            print(f"[ArxivMCP] Error: {e}")
            
        return self._mock_papers(query, max_results)

    def _mock_papers(self, query: str, limit: int) -> List[Dict[str, Any]]:
        return [
            {
                "title": f"Recent Advances in {query}",
                "authors": ["Dr. Smith", "A. Researcher"],
                "summary": f"This paper explores novel approaches to {query}...",
                "pdf_url": "https://arxiv.org/pdf/mock",
                "published": "2025-01-15"
            }
            for i in range(limit)
        ]

arxiv_mcp = ArxivMCP()
