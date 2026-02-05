"""
Search MCP Client
=================
A comprehensive search module providing web, image, and video search capabilities
using Brave Search and Tavily via RapidAPI and direct MCP integration.

Features:
    - Web Search (Brave & Tavily)
    - Image Search (Brave & Real-Time Image Search)
    - Video Search (Brave)
    - Support for .env configuration

Required .env variables:
    RAPIDAPI_KEY=your_rapidapi_key
    TAVILY_API_KEY=your_tavily_api_key (optional, fallback provided)
"""

import os
import http.client
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import quote, urlparse


@dataclass
class SearchConfig:
    """Configuration for Search API clients."""
    api_key: str
    tavily_key: Optional[str] = None
    brave_host: str = "brave-api12.p.rapidapi.com"
    image_search_host: str = "real-time-image-search.p.rapidapi.com"
    tavily_mcp_url: str = "https://mcp.tavily.com/mcp/"


class SearchClient:
    """
    Unified Search Client for Brave, Tavily, and Real-Time Search.
    """
    
    def __init__(self, api_key: Optional[str] = None, tavily_key: Optional[str] = None):
        """
        Initialize the Search Client.
        
        Args:
            api_key: RapidAPI key.
            tavily_key: Tavily API key.
        """
        self.config = SearchConfig(
            api_key=api_key or os.getenv("RAPIDAPI_KEY"),
            tavily_key=tavily_key or os.getenv("TAVILY_API_KEY", "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")
        )
        
        if not self.config.api_key:
            raise ValueError("RAPIDAPI_KEY is required in environment or constructor.")
            
        self._headers = {
            "x-rapidapi-key": self.config.api_key,
            "Content-Type": "application/json"
        }

    def _make_rapid_get_request(self, host: str, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Internal helper for RapidAPI GET requests."""
        conn = http.client.HTTPSConnection(host)
        
        query_parts = [f"{k}={quote(str(v))}" for k, v in params.items() if v is not None]
        url = f"{endpoint}?{'&'.join(query_parts)}"
        
        try:
            headers = self._headers.copy()
            headers["x-rapidapi-host"] = host
            conn.request("GET", url, headers=headers)
            response = conn.getresponse()
            data = response.read().decode("utf-8")
            
            if response.status != 200:
                return {"status": "error", "code": response.status, "message": data}
            
            return json.loads(data)
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()

    # --- BRAVE SEARCH TOOLS ---

    def search_brave_web(self, query: str, count: int = 10) -> Dict[str, Any]:
        """
        Search the web using Brave Search engine. Returns web pages matching the query.
        
        Use this tool to find general information, articles, news, tutorials, or any web content.
        The results include page titles, URLs, and text snippets.
        
        Args:
            query: The search query string (e.g., 'python async tutorial', 'best coffee shops NYC')
            count: Number of results to return (default: 10, max: 20)
            
        Returns:
            Dict containing 'web' key with list of results, each having:
            - title: Page title
            - url: Page URL
            - description: Text snippet from the page
            
        Example:
            search_brave_web("machine learning basics", count=5)
        """
        params = {"q": query, "count": count}
        return self._make_rapid_get_request(self.config.brave_host, "/web/search", params)

    def search_brave_images(self, query: str, count: int = 10) -> Dict[str, Any]:
        """
        Search for images using Brave Search. Returns image URLs and metadata.
        
        Use this tool when you need to find images, photos, graphics, or visual content.
        
        Args:
            query: What images to search for (e.g., 'sunset beach', 'modern logo design')
            count: Number of image results (default: 10)
            
        Returns:
            Dict containing 'images' key with list of image results, each having:
            - url: Direct image URL
            - thumbnail: Thumbnail URL
            - source_url: Page where image was found
            - title: Image title/alt text
            
        Example:
            search_brave_images("minimalist wallpaper", count=8)
        """
        params = {"q": query, "count": count}
        return self._make_rapid_get_request(self.config.brave_host, "/images/search", params)

    def search_brave_videos(self, query: str, count: int = 10) -> Dict[str, Any]:
        """
        Search for videos across the web using Brave Search.
        
        Use this tool to find videos from YouTube, Vimeo, and other video platforms.
        
        Args:
            query: What videos to search for (e.g., 'cooking tutorial', 'python crash course')
            count: Number of video results (default: 10)
            
        Returns:
            Dict containing 'videos' key with list of video results, each having:
            - url: Video URL
            - thumbnail: Video thumbnail image
            - title: Video title
            - duration: Video length
            - description: Video description
            
        Example:
            search_brave_videos("react hooks tutorial", count=5)
        """
        params = {"q": query, "count": count}
        return self._make_rapid_get_request(self.config.brave_host, "/videos/search", params)

    # --- REAL-TIME IMAGE SEARCH ---

    def search_images_realtime(
        self, 
        query: str, 
        limit: int = 10,
        region: str = "us",
        safe_search: str = "off"
    ) -> Dict[str, Any]:
        """
        Perform a high-quality real-time image search with advanced filtering options.
        
        This provides better quality images than Brave search with more filter options.
        Use for finding high-resolution images with specific requirements.
        
        Args:
            query: Image search query (e.g., 'abstract background', 'cute puppies')
            limit: Maximum number of results (default: 10)
            region: Region code for localized results, e.g., 'us', 'uk', 'de' (default: 'us')
            safe_search: Content filter - 'on' for safe mode, 'off' for all content (default: 'off')
            
        Returns:
            Dict with high-resolution image results including direct URLs and metadata
            
        Example:
            search_images_realtime("nature landscape", limit=5, region="us", safe_search="on")
        """
        params = {
            "query": query,
            "limit": limit,
            "region": region,
            "safe_search": safe_search,
            "size": "any",
            "color": "any",
            "type": "any",
            "time": "any",
            "usage_rights": "any"
        }
        return self._make_rapid_get_request(self.config.image_search_host, "/search", params)

    # --- TAVILY SEARCH ---

    def search_tavily(self, query: str, search_depth: str = "smart") -> Dict[str, Any]:
        """
        Perform an AI-optimized web search using Tavily. Best for research and factual queries.
        
        Tavily provides AI-summarized answers along with source citations. Use this when you need
        researched answers rather than just a list of links. Better for complex questions.
        
        Args:
            query: The research query (e.g., 'what are the benefits of meditation?')
            search_depth: 'smart' for balanced results, 'deep' for comprehensive research (default: 'smart')
            
        Returns:
            Dict containing:
            - answer: AI-generated summary answer
            - results: List of source URLs with content excerpts
            - images: Related images if available
            
        Example:
            search_tavily("how does quantum computing work?", search_depth="deep")
        """
        # Tavily usually uses a POST request to their API
        # but since the user provided an MCP link, we can simulate or use their API directly.
        # For simplicity and reliability in this module, we use the standard API call.
        conn = http.client.HTTPSConnection("api.tavily.com")
        payload = json.dumps({
            "api_key": self.config.tavily_key,
            "query": query,
            "search_depth": search_depth,
            "include_answer": True,
            "include_images": True
        })
        
        headers = {'Content-Type': "application/json"}
        
        try:
            conn.request("POST", "/search", payload, headers)
            response = conn.getresponse()
            data = response.read().decode("utf-8")
            return json.loads(data)
        except Exception as e:
            return {"status": "error", "message": f"Tavily request failed: {str(e)}"}
        finally:
            conn.close()

    def web_search(self, query: str, provider: str = "brave") -> Dict[str, Any]:
        """
        Generic web search method that allows switching providers.
        """
        if provider.lower() == "tavily":
            return self.search_tavily(query)
        return self.search_brave_web(query)


# --- Convenience Functions ---

_default_client: Optional[SearchClient] = None

def _get_client() -> SearchClient:
    global _default_client
    if _default_client is None:
        _default_client = SearchClient()
    return _default_client

def web_search(query: str, provider: str = "brave"):
    return _get_client().web_search(query, provider=provider)

def image_search(query: str, real_time: bool = True):
    if real_time:
        return _get_client().search_images_realtime(query)
    return _get_client().search_brave_images(query)

def video_search(query: str):
    return _get_client().search_brave_videos(query)


if __name__ == "__main__":
    # Test section
    if os.getenv("RAPIDAPI_KEY"):
        client = SearchClient()
        print("Testing Brave Web Search...")
        print(json.dumps(client.search_brave_web("python programming"), indent=2)[:500])
        
        print("\nTesting Real-Time Image Search...")
        print(json.dumps(client.search_images_realtime("futuristic city"), indent=2)[:500])
    else:
        print("Set RAPIDAPI_KEY to test.")
        print("Tavily MCP Link stored for integration: https://mcp.tavily.com/mcp/?tavilyApiKey=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")