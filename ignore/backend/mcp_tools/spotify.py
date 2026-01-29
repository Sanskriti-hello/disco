"""
Spotify MCP Client
==================
A comprehensive module for interacting with music, artists, albums, and concerts 
via the Spotify23 RapidAPI.

Functions:
    - search: Search for tracks, artists, albums, etc.
    - get_track_details: Get specific track information.
    - get_track_lyrics: Get lyrics for a specific track.
    - get_artist_details: Get artist profile and discography.
    - get_album_details: Get album information and tracklist.
    - get_concerts: Search for live events/concerts.

Usage:
    from backend.mcp.spotify import SpotifyClient
    
    client = SpotifyClient(api_key="your_api_key")
    results = client.search("Daft Punk", search_type="artist")
"""

import os
import http.client
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import quote


@dataclass
class SpotifyConfig:
    """Configuration for Spotify API client."""
    api_key: str
    host: str = "spotify23.p.rapidapi.com"


class SpotifyClient:
    """
    Client for the Spotify23 API via RapidAPI.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Spotify Client.
        
        Args:
            api_key: RapidAPI key. If not provided, reads from RAPIDAPI_KEY env variable.
        """
        key = api_key or os.getenv("RAPIDAPI_KEY")
        if not key:
            raise ValueError("RAPIDAPI_KEY is required.")
        self.config = SpotifyConfig(api_key=key)
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

    # --- SEARCH ---

    def search(
        self, 
        query: str, 
        search_type: str = "multi", 
        offset: int = 0, 
        limit: int = 10,
        number_of_top_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for tracks, artists, albums, etc.
        
        Args:
            query: The search term.
            search_type: 'multi', 'tracks', 'artists', 'albums', 'playlists', 'genres', 'shows', 'episodes', 'users'.
            offset: Result offset for pagination.
            limit: Max results.
            number_of_top_results: Number of top results to return.
        """
        params = {
            "q": query,
            "type": search_type,
            "offset": offset,
            "limit": limit,
            "numberOfTopResults": number_of_top_results
        }
        return self._make_request("/search/", params)

    # --- TRACKS & LYRICS ---

    def get_tracks(self, track_ids: List[str]) -> Dict[str, Any]:
        """Get details for one or more tracks."""
        params = {"ids": ",".join(track_ids)}
        return self._make_request("/tracks/", params)

    def get_track_lyrics(self, track_id: str) -> Dict[str, Any]:
        """Get lyrics for a specific track."""
        params = {"id": track_id}
        return self._make_request("/track_lyrics/", params)

    # --- ARTISTS ---

    def get_artists(self, artist_ids: List[str]) -> Dict[str, Any]:
        """Get profile information for one or more artists."""
        params = {"ids": ",".join(artist_ids)}
        return self._make_request("/artists/", params)

    def get_artist_albums(self, artist_id: str, offset: int = 0, limit: int = 20) -> Dict[str, Any]:
        """Get albums by a specific artist."""
        params = {"id": artist_id, "offset": offset, "limit": limit}
        return self._make_request("/artist_albums/", params)

    def get_artist_singles(self, artist_id: str, offset: int = 0, limit: int = 20) -> Dict[str, Any]:
        """Get singles by a specific artist."""
        params = {"id": artist_id, "offset": offset, "limit": limit}
        return self._make_request("/artist_singles/", params)

    def get_artist_featuring(self, artist_id: str) -> Dict[str, Any]:
        """Get tracks where the artist is featured."""
        params = {"id": artist_id}
        return self._make_request("/artist_featuring/", params)

    # --- ALBUMS ---

    def get_albums(self, album_ids: List[str]) -> Dict[str, Any]:
        """Get information for one or more albums."""
        params = {"ids": ",".join(album_ids)}
        return self._make_request("/albums/", params)

    def get_album_tracks(self, album_id: str, offset: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Get all tracks in an album."""
        params = {"id": album_id, "offset": offset, "limit": limit}
        return self._make_request("/album_tracks/", params)

    # --- GENRES & PODCASTS ---

    def get_genre_view(self, genre_id: str, content_limit: int = 10, limit: int = 20) -> Dict[str, Any]:
        """Get content for a specific genre."""
        params = {"id": genre_id, "content_limit": content_limit, "limit": limit}
        return self._make_request("/genre_view/", params)

    def get_podcast_episodes(self, podcast_id: str, offset: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Get episodes for a specific podcast."""
        params = {"id": podcast_id, "offset": offset, "limit": limit}
        return self._make_request("/podcast_episodes/", params)

    # --- CONCERTS ---

    def get_concerts(self, location_code: str = "US") -> Dict[str, Any]:
        """Get list of upcoming concerts by location (ISO country code)."""
        params = {"gl": location_code}
        return self._make_request("/concerts/", params)

    def get_concert_details(self, concert_id: str) -> Dict[str, Any]:
        """Get details for a specific concert."""
        params = {"id": concert_id}
        return self._make_request("/concert/", params)


# --- Convenience Functions ---

_default_client: Optional[SpotifyClient] = None

def _get_client() -> SpotifyClient:
    global _default_client
    if _default_client is None:
        _default_client = SpotifyClient()
    return _default_client

def search_music(query: str, search_type: str = "multi"):
    """Generic search for music content."""
    return _get_client().search(query, search_type=search_type)

def get_track_lyrics(track_id: str):
    """Get lyrics for a track."""
    return _get_client().get_track_lyrics(track_id)

def get_upcoming_concerts(location: str = "US"):
    """Get concerts in a specific country."""
    return _get_client().get_concerts(location)


if __name__ == "__main__":
    # Test section
    if os.getenv("RAPIDAPI_KEY"):
        client = SpotifyClient()
        print("Testing Spotify Search (Artist: Radiohead)...")
        print(json.dumps(client.search("Radiohead", search_type="artist"), indent=2)[:500])
        
        print("\nTesting Concert Search (US)...")
        print(json.dumps(client.get_concerts("US"), indent=2)[:500])
    else:
        print("Set RAPIDAPI_KEY to test.")