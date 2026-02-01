"""
News MCP Client
===============
A reusable module for fetching and searching news headlines via the NewsNow RapidAPI.

Functions:
    - search_news: Search news articles by query and date range.
    - get_top_news_by_location: Get top news for a specific country/location.
    - get_top_news_by_category: Get top news in categories like Technology, Business, etc.

Usage:
    from backend.mcp.news import NewsClient
    
    client = NewsClient(api_key="your_api_key")
    results = client.search_news("Artificial Intelligence", location="us")
"""

import os
import http.client
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class NewsConfig:
    """Configuration for News API client."""
    api_key: str
    host: str = "newsnow.p.rapidapi.com"
    default_location: str = "us"
    default_language: str = "en"


class NewsClient:
    """
    Client for the NewsNow API.
    
    Provides methods to search news and get top headlines by location or category.
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[NewsConfig] = None):
        """
        Initialize the News API client.
        
        Args:
            api_key: RapidAPI key. If not provided, reads from RAPIDAPI_KEY env variable.
            config: Optional NewsConfig object for advanced configuration.
        """
        if config:
            self.config = config
        else:
            key = api_key or os.getenv("RAPIDAPI_KEY")
            if not key:
                raise ValueError(
                    "API key is required. Provide it via api_key parameter "
                    "or set the RAPIDAPI_KEY environment variable."
                )
            self.config = NewsConfig(api_key=key)
        
        self._headers = {
            "x-rapidapi-key": self.config.api_key,
            "x-rapidapi-host": self.config.host,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an HTTP POST request to the NewsNow API.
        
        Args:
            endpoint: API endpoint path (e.g., "/newsv2")
            payload: JSON payload for the POST request
            
        Returns:
            JSON response as a dictionary
        """
        conn = http.client.HTTPSConnection(self.config.host)
        
        try:
            json_payload = json.dumps(payload)
            conn.request("POST", endpoint, json_payload, self._headers)
            response = conn.getresponse()
            data = response.read().decode("utf-8")
            
            if response.status != 200:
                return {
                    "status": "error",
                    "error_code": response.status,
                    "message": data
                }
            
            return json.loads(data)
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid JSON response: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Request failed: {str(e)}"}
        finally:
            conn.close()
    
    def search_news(
        self,
        query: str,
        time_bounded: bool = False,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        location: Optional[str] = None,
        language: Optional[str] = None,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Search news articles by keywords.
        
        Args:
            query: Search string (e.g., "AI", "Climate Change")
            time_bounded: Whether to filter by date range
            from_date: Start date in "DD/MM/YYYY" format
            to_date: End date in "DD/MM/YYYY" format
            location: Country code (e.g., "us", "in")
            language: Language code (e.g., "en", "hi")
            page: Page number for pagination
            
        Returns:
            Dictionary containing search results
        """
        payload = {
            "query": query,
            "time_bounded": time_bounded,
            "location": location or self.config.default_location,
            "language": language or self.config.default_language,
            "page": page
        }
        if from_date:
            payload["from_date"] = from_date
        if to_date:
            payload["to_date"] = to_date
            
        return self._make_request("/newsv2", payload)
    
    def get_top_news_by_location(
        self,
        location: Optional[str] = None,
        language: Optional[str] = None,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get top news headlines for a specific location.
        
        Args:
            location: Country code (default: "us")
            language: Language code (default: "en")
            page: Page number
        """
        payload = {
            "location": location or self.config.default_location,
            "language": language or self.config.default_language,
            "page": page
        }
        return self._make_request("/newsv2_top_news_location", payload)
    
    def get_top_news_by_category(
        self,
        category: str,
        location: Optional[str] = None,
        language: Optional[str] = None,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get top headlines for a specific category.
        
        Args:
            category: News category (e.g., "TECHNOLOGY", "BUSINESS", "SPORTS", "ENTERTAINMENT")
            location: Country code
            language: Language code
            page: Page number
        """
        payload = {
            "category": category.upper(),
            "location": location or self.config.default_location,
            "language": language or self.config.default_language,
            "page": page
        }
        return self._make_request("/newsv2_top_news_cat", payload)


# ============================================================================
# Convenience Functions (for direct import)
# ============================================================================

_default_client: Optional[NewsClient] = None


def _get_client(api_key: Optional[str] = None) -> NewsClient:
    """Get or create a default client instance."""
    global _default_client
    if _default_client is None:
        _default_client = NewsClient(api_key=api_key)
    return _default_client


def search_news(query: str, **kwargs) -> Dict[str, Any]:
    """Search for news articles. Convenience function."""
    return _get_client().search_news(query, **kwargs)


def get_top_headlines(category: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch top headlines. 
    If category is provided, searches by category. 
    Otherwise searches by location.
    """
    client = _get_client()
    if category:
        return client.get_top_news_by_category(category, location=location)
    return client.get_top_news_by_location(location=location)


if __name__ == "__main__":
    # Test section
    api_key = os.getenv("RAPIDAPI_KEY")
    if api_key:
        client = NewsClient(api_key=api_key)
        print("Testing News Search...")
        print(json.dumps(client.search_news("Technology"), indent=2)[:500])
    else:
        print("Please set RAPIDAPI_KEY environment variable to test.")
