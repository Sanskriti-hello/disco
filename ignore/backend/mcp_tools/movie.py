"""
Movie & Streaming MCP Client
============================
A comprehensive module for searching movies and TV shows, and checking their 
streaming availability across various platforms via the Streaming Availability RapidAPI.

Functions:
    - search_by_title: Search for movies or shows by their title.
    - search_by_filters: Discover content using advanced filters (genres, year, etc.).
    - get_show_details: Get detailed information about a specific movie or series.
    - get_genres: List all available genres and their IDs.

Usage:
    from backend.mcp.movie import MovieClient
    
    client = MovieClient(api_key="your_api_key")
    results = client.search_by_title("Inception")
"""

import os
import http.client
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import quote


@dataclass
class MovieConfig:
    """Configuration for Movie API client."""
    api_key: str
    host: str = "streaming-availability.p.rapidapi.com"
    default_language: str = "en"
    default_country: str = "us"


class MovieClient:
    """
    Client for the Streaming Availability API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Movie Client.
        
        Args:
            api_key: RapidAPI key. If not provided, reads from RAPIDAPI_KEY env variable.
        """
        key = api_key or os.getenv("RAPIDAPI_KEY")
        if not key:
            raise ValueError("RAPIDAPI_KEY is required.")
        self.config = MovieConfig(api_key=key)
        self._headers = {
            "x-rapidapi-key": self.config.api_key,
            "x-rapidapi-host": self.config.host,
            "Content-Type": "application/json"
        }

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Internal helper for API GET requests."""
        conn = http.client.HTTPSConnection(self.config.host)
        
        # Build query string
        query_parts = [f"{k}={quote(str(v))}" for k, v in params.items() if v is not None]
        url = f"{endpoint}?{'&'.join(query_parts)}" if query_parts else endpoint
        
        try:
            conn.request("GET", url, headers=self._headers)
            response = conn.getresponse()
            data = response.read().decode("utf-8")
            
            if response.status != 200:
                return {"status": "error", "code": response.status, "message": data}
            
            return json.loads(data)
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()

    def search_by_title(
        self, 
        title: str, 
        country: Optional[str] = None,
        show_type: str = "movie", 
        series_granularity: str = "show"
    ) -> Dict[str, Any]:
        """
        Search for movies or shows by title.
        
        Args:
            title: The title to search for.
            country: Country code (e.g., 'us', 'gb').
            show_type: 'movie' or 'series'.
            series_granularity: 'show' or 'episode'.
        """
        params = {
            "title": title,
            "country": country or self.config.default_country,
            "show_type": show_type,
            "series_granularity": series_granularity,
            "output_language": self.config.default_language
        }
        return self._make_request("/shows/search/title", params)

    def search_by_filters(
        self,
        show_type: str = "movie",
        country: Optional[str] = None,
        order_by: str = "original_title",
        order_direction: str = "asc",
        genres: Optional[List[str]] = None,
        genres_relation: str = "and",
        series_granularity: str = "show"
    ) -> Dict[str, Any]:
        """
        Discover content using advanced filters.
        
        Args:
            show_type: 'movie' or 'series'.
            country: Country code.
            order_by: Field to sort by.
            order_direction: 'asc' or 'desc'.
            genres: List of genre IDs.
            genres_relation: 'and' or 'or'.
            series_granularity: 'show' or 'episode'.
        """
        params = {
            "show_type": show_type,
            "country": country or self.config.default_country,
            "order_by": order_by,
            "order_direction": order_direction,
            "genres_relation": genres_relation,
            "series_granularity": series_granularity,
            "output_language": self.config.default_language
        }
        if genres:
            params["genres"] = ",".join(genres)
            
        return self._make_request("/shows/search/filters", params)

    def get_show_details(self, show_id: str, series_granularity: str = "episode") -> Dict[str, Any]:
        """
        Get detailed information about a specific show.
        
        Args:
            show_id: The unique ID of the show.
            series_granularity: 'show' or 'episode'.
        """
        params = {
            "series_granularity": series_granularity,
            "output_language": self.config.default_language
        }
        return self._make_request(f"/shows/{show_id}", params)

    def get_genres(self) -> Dict[str, Any]:
        """
        List all available genres and their IDs.
        """
        params = {"output_language": self.config.default_language}
        return self._make_request("/genres", params)


# --- Convenience Functions ---

_default_client: Optional[MovieClient] = None

def _get_client() -> MovieClient:
    global _default_client
    if _default_client is None:
        _default_client = MovieClient()
    return _default_client

def search_movies(title: str):
    """Search for movies by title."""
    return _get_client().search_by_title(title=title, show_type="movie")

def search_series(title: str):
    """Search for TV series by title."""
    return _get_client().search_by_title(title=title, show_type="series")

def get_genres():
    """Get all movie/show genres."""
    return _get_client().get_genres()


if __name__ == "__main__":
    # Test section
    if os.getenv("RAPIDAPI_KEY"):
        client = MovieClient()
        print("Testing Movie Search (Title: The Matrix)...")
        print(json.dumps(client.search_by_title("The Matrix"), indent=2)[:500])
        
        print("\nTesting Genre Lookup...")
        print(json.dumps(client.get_genres(), indent=2)[:500])
    else:
        print("Set RAPIDAPI_KEY to test.")
