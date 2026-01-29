import os
import requests
from typing import List, Dict, Any, Optional

class AmazonMCP:
    def __init__(self):
        self.access_key = os.getenv("AMAZON_ACCESS_KEY")
        self.secret_key = os.getenv("AMAZON_SECRET_KEY")
        self.partner_tag = os.getenv("AMAZON_PARTNER_TAG")
        self.region = os.getenv("AMAZON_REGION", "US")

    def search_products(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for products on Amazon.
        Uses PA-API if keys are present, otherwise returns mock data.
        """
        if self._can_use_api():
            return self._search_api(query, limit)
        return self._mock_search(query, limit)

    def _can_use_api(self) -> bool:
        return bool(self.access_key and self.secret_key and self.partner_tag)

    def _search_api(self, query: str, limit: int) -> List[Dict[str, Any]]:
        # In a real implementation, this would sign requests and call the PA-API
        # specific to the region. For brevity, assuming typical PA-API wrapper usage.
        print(f"[AmazonMCP] searching API for: {query}")
        return []

    def _mock_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        print(f"[AmazonMCP] Mock search for: {query}")
        return [
            {
                "title": f"Mock Amazon Product for {query} - Option {i+1}",
                "price": f"${(i+1)*25}.99",
                "url": f"https://amazon.com/dp/mock{i}",
                "image": "https://via.placeholder.com/150",
                "rating": 4.5
            }
            for i in range(limit)
        ]

amazon_mcp = AmazonMCP()
