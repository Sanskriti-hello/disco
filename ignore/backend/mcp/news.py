import os
import requests
from typing import List, Dict, Any

class NewsMCP:
    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2"

    def get_top_headlines(self, category: str = "general", limit: int = 5) -> List[Dict[str, Any]]:
        if self.api_key:
            try:
                resp = requests.get(
                    f"{self.base_url}/top-headlines",
                    params={"apiKey": self.api_key, "category": category, "pageSize": limit}
                )
                if resp.status_code == 200:
                    return resp.json().get("articles", [])
            except Exception as e:
                print(f"[NewsMCP] API Error: {e}")
        
        return self._mock_news(category, limit)

    def _mock_news(self, category: str, limit: int) -> List[Dict[str, Any]]:
        return [
            {
                "title": f"Breaking News in {category.capitalize()}: Story {i+1}",
                "description": "This is a mock news article description.",
                "url": "https://example.com/news",
                "urlToImage": "https://via.placeholder.com/300x200",
                "source": {"name": "Mock News Daily"}
            }
            for i in range(limit)
        ]

news_mcp = NewsMCP()
