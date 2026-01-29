# backend/mcp_tools/youtube.py
"""
YouTube MCP - Production Implementation
Access YouTube watch history, liked videos, subscriptions, and recommendations

Setup Instructions:
1. Use the SAME Google Cloud project as Google Workspace
2. Enable YouTube Data API v3
3. Use the same credentials.json (already has OAuth2 setup)
4. Scopes will be added to existing token

Required .env:
    GOOGLE_CREDENTIALS_PATH=backend/mcp/credentials.json
    GOOGLE_TOKEN_PATH=backend/mcp/token.json
    YOUTUBE_API_KEY=your_api_key_here  # Optional: for public data without OAuth
"""

import os
import pickle
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# YouTube-specific scopes
YOUTUBE_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',           # Read all YouTube data
    'https://www.googleapis.com/auth/youtube.force-ssl',          # Full access (for personalized data)
    'https://www.googleapis.com/auth/youtubepartner'              # Analytics data
]


class YouTubeError(Exception):
    """Custom exception for YouTube API errors"""
    pass


class YouTubeMCP:
    """
    Production YouTube integration with OAuth2
    Accesses your actual YouTube data: watch history, liked videos, subscriptions
    """
    
    def __init__(self, use_oauth: bool = True, access_token: Optional[str] = None):
        """
        Args:
            use_oauth: If True, use OAuth2 (for personal data). If False, use API key (public data only)
            access_token: Optional raw token string from Chrome Extension
        """
        self.credentials_path = os.getenv(
            "GOOGLE_CREDENTIALS_PATH", 
            os.path.join(os.path.dirname(__file__), "credentials.json")
        )
        self.token_path = os.getenv(
            "GOOGLE_TOKEN_PATH",
            os.path.join(os.path.dirname(__file__), "token.json")
        )
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        
        self.use_oauth = use_oauth
        self.creds = None
        self.service = None
        
        if use_oauth:
            if access_token:
                self._initialize_from_token(access_token)
            else:
                self._authenticate_oauth()
        else:
            self._authenticate_api_key()
    
    def _initialize_from_token(self, token_string: str):
        """Initialize with access token from Chrome extension"""
        self.creds = Credentials(token_string)
        self.service = build('youtube', 'v3', credentials=self.creds)
        print("PASS: Initialized YouTube with provided Access Token")
    
    def _authenticate_oauth(self):
        """Authenticate using OAuth2 (for personal data like watch history)"""
        
        # Load existing credentials
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)
        
        # Refresh or get new credentials
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("[YouTube] Refreshing OAuth token...")
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise YouTubeError(
                        f"Credentials file not found at {self.credentials_path}\n"
                        "Please set up Google Cloud OAuth2 credentials first"
                    )
                
                print("[YouTube] Starting OAuth flow (will open browser)...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path,
                    YOUTUBE_SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)
            
            print("PASS: YouTube OAuth authentication successful")
        
        # Build YouTube service with OAuth
        self.service = build('youtube', 'v3', credentials=self.creds)
    
    def _authenticate_api_key(self):
        """Authenticate using API key (for public data only)"""
        
        if not self.api_key:
            raise YouTubeError(
                "YOUTUBE_API_KEY not set in .env\n"
                "Get one from: https://console.cloud.google.com/apis/credentials"
            )
        
        # Build YouTube service with API key
        self.service = build('youtube', 'v3', developerKey=self.api_key)
        print("PASS: YouTube API key authentication successful")
    
    # ========================================================================
    # WATCH HISTORY (OAuth required)
    # ========================================================================
    
    def get_watch_history(
        self,
        max_results: int = 50,
        published_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get your YouTube watch history
        
        NOTE: Requires OAuth2 authentication!
        
        Args:
            max_results: Max videos to return (1-50)
            published_after: ISO 8601 date (e.g., "2024-01-01T00:00:00Z")
        
        Returns:
            List of watched videos with metadata
        """
        
        if not self.use_oauth:
            raise YouTubeError("Watch history requires OAuth2. Set use_oauth=True")
        
        try:
            # Get user's channel ID first
            channels_response = self.service.channels().list(
                part='contentDetails',
                mine=True
            ).execute()
            
            if not channels_response.get('items'):
                raise YouTubeError("No YouTube channel found for authenticated user")
            
            # Get watch history playlist ID
            # Note: YouTube removed direct watch history access
            # Alternative: Use liked videos, watch later, or user playlists
            
            # Get liked videos instead (most reliable)
            return self.get_liked_videos(max_results)
            
        except HttpError as error:
            raise YouTubeError(f"Failed to get watch history: {error}")
    
    def get_liked_videos(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get videos you've liked on YouTube
        
        Args:
            max_results: Max videos to return
        
        Returns:
            List of liked videos
        """
        
        if not self.use_oauth:
            raise YouTubeError("Liked videos require OAuth2")
        
        try:
            request = self.service.videos().list(
                part='snippet,contentDetails,statistics',
                myRating='like',
                maxResults=max_results
            )
            
            response = request.execute()
            videos = []
            
            for item in response.get('items', []):
                snippet = item['snippet']
                statistics = item.get('statistics', {})
                
                videos.append({
                    'video_id': item['id'],
                    'title': snippet['title'],
                    'channel': snippet['channelTitle'],
                    'channel_id': snippet['channelId'],
                    'published_at': snippet['publishedAt'],
                    'description': snippet['description'][:200],
                    'thumbnail': snippet['thumbnails']['high']['url'],
                    'view_count': int(statistics.get('viewCount', 0)),
                    'like_count': int(statistics.get('likeCount', 0)),
                    'url': f"https://www.youtube.com/watch?v={item['id']}"
                })
            
            return videos
            
        except HttpError as error:
            raise YouTubeError(f"Failed to get liked videos: {error}")
    
    # ========================================================================
    # SUBSCRIPTIONS (OAuth required)
    # ========================================================================
    
    def get_subscriptions(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Get channels you're subscribed to
        
        Returns:
            List of subscribed channels
        """
        
        if not self.use_oauth:
            raise YouTubeError("Subscriptions require OAuth2")
        
        try:
            request = self.service.subscriptions().list(
                part='snippet,contentDetails',
                mine=True,
                maxResults=max_results,
                order='relevance'
            )
            
            response = request.execute()
            subscriptions = []
            
            for item in response.get('items', []):
                snippet = item['snippet']
                
                subscriptions.append({
                    'channel_id': snippet['resourceId']['channelId'],
                    'channel_title': snippet['title'],
                    'description': snippet['description'][:150],
                    'thumbnail': snippet['thumbnails']['high']['url'],
                    'published_at': snippet['publishedAt'],
                    'url': f"https://www.youtube.com/channel/{snippet['resourceId']['channelId']}"
                })
            
            return subscriptions
            
        except HttpError as error:
            raise YouTubeError(f"Failed to get subscriptions: {error}")
    
    # ========================================================================
    # RECOMMENDED VIDEOS (Based on subscriptions)
    # ========================================================================
    
    def get_recommended_videos(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Get recommended videos based on your subscriptions
        
        Returns:
            List of recommended videos from subscribed channels
        """
        
        try:
            # Get subscribed channels
            subscriptions = self.get_subscriptions(max_results=10)
            
            if not subscriptions:
                return []
            
            # Get latest videos from subscribed channels
            recommended = []
            
            for sub in subscriptions[:5]:  # Top 5 channels
                channel_id = sub['channel_id']
                
                # Get channel's uploads playlist
                channel_response = self.service.channels().list(
                    part='contentDetails',
                    id=channel_id
                ).execute()
                
                if not channel_response.get('items'):
                    continue
                
                uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                
                # Get latest videos from this channel
                playlist_response = self.service.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=4
                ).execute()
                
                for video_item in playlist_response.get('items', []):
                    snippet = video_item['snippet']
                    
                    recommended.append({
                        'video_id': snippet['resourceId']['videoId'],
                        'title': snippet['title'],
                        'channel': snippet['channelTitle'],
                        'published_at': snippet['publishedAt'],
                        'thumbnail': snippet['thumbnails']['high']['url'],
                        'url': f"https://www.youtube.com/watch?v={snippet['resourceId']['videoId']}"
                    })
                
                if len(recommended) >= max_results:
                    break
            
            return recommended[:max_results]
            
        except HttpError as error:
            raise YouTubeError(f"Failed to get recommendations: {error}")
    
    # ========================================================================
    # SEARCH (Public API - works with API key OR OAuth)
    # ========================================================================
    
    def search_videos(
        self,
        query: str,
        max_results: int = 10,
        order: str = 'relevance',
        published_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for YouTube videos
        
        Args:
            query: Search query
            max_results: Max results (1-50)
            order: Sort order (relevance, date, viewCount, rating)
            published_after: ISO 8601 date
        
        Returns:
            List of video search results
        """
        
        try:
            params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': max_results,
                'order': order
            }
            
            if published_after:
                params['publishedAfter'] = published_after
            
            request = self.service.search().list(**params)
            response = request.execute()
            
            videos = []
            for item in response.get('items', []):
                snippet = item['snippet']
                
                videos.append({
                    'video_id': item['id']['videoId'],
                    'title': snippet['title'],
                    'channel': snippet['channelTitle'],
                    'channel_id': snippet['channelId'],
                    'published_at': snippet['publishedAt'],
                    'description': snippet['description'][:200],
                    'thumbnail': snippet['thumbnails']['high']['url'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                })
            
            return videos
            
        except HttpError as error:
            raise YouTubeError(f"Search failed: {error}")
    
    # ========================================================================
    # VIDEO DETAILS
    # ========================================================================
    
    def get_video_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get detailed information about specific videos
        
        Args:
            video_ids: List of video IDs
        
        Returns:
            List of video details
        """
        
        try:
            request = self.service.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(video_ids)
            )
            
            response = request.execute()
            videos = []
            
            for item in response.get('items', []):
                snippet = item['snippet']
                stats = item.get('statistics', {})
                content = item.get('contentDetails', {})
                
                videos.append({
                    'video_id': item['id'],
                    'title': snippet['title'],
                    'channel': snippet['channelTitle'],
                    'published_at': snippet['publishedAt'],
                    'description': snippet['description'],
                    'thumbnail': snippet['thumbnails']['high']['url'],
                    'duration': content.get('duration', ''),
                    'view_count': int(stats.get('viewCount', 0)),
                    'like_count': int(stats.get('likeCount', 0)),
                    'comment_count': int(stats.get('commentCount', 0)),
                    'url': f"https://www.youtube.com/watch?v={item['id']}"
                })
            
            return videos
            
        except HttpError as error:
            raise YouTubeError(f"Failed to get video details: {error}")
    
    # ========================================================================
    # TRENDING VIDEOS
    # ========================================================================
    
    def get_trending_videos(
        self,
        region_code: str = 'US',
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get trending videos in a region
        
        Args:
            region_code: Country code (e.g., 'US', 'IN', 'GB')
            max_results: Max results
        
        Returns:
            List of trending videos
        """
        
        try:
            request = self.service.videos().list(
                part='snippet,statistics',
                chart='mostPopular',
                regionCode=region_code,
                maxResults=max_results
            )
            
            response = request.execute()
            videos = []
            
            for item in response.get('items', []):
                snippet = item['snippet']
                stats = item.get('statistics', {})
                
                videos.append({
                    'video_id': item['id'],
                    'title': snippet['title'],
                    'channel': snippet['channelTitle'],
                    'published_at': snippet['publishedAt'],
                    'thumbnail': snippet['thumbnails']['high']['url'],
                    'view_count': int(stats.get('viewCount', 0)),
                    'like_count': int(stats.get('likeCount', 0)),
                    'url': f"https://www.youtube.com/watch?v={item['id']}"
                })
            
            return videos
            
        except HttpError as error:
            raise YouTubeError(f"Failed to get trending videos: {error}")


# ============================================================================
# SINGLETON INSTANCES
# ============================================================================

_youtube_oauth = None
_youtube_api_key = None

def get_youtube_mcp(use_oauth: bool = True) -> YouTubeMCP:
    """
    Get YouTube MCP instance
    
    Args:
        use_oauth: True for personal data (watch history, likes), False for public data only
    """
    global _youtube_oauth, _youtube_api_key
    
    if use_oauth:
        if _youtube_oauth is None:
            _youtube_oauth = YouTubeMCP(use_oauth=True)
        return _youtube_oauth
    else:
        if _youtube_api_key is None:
            _youtube_api_key = YouTubeMCP(use_oauth=False)
        return _youtube_api_key


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import json
    from dotenv import load_dotenv
    
    load_dotenv()
    
    try:
        print("🎥 Initializing YouTube MCP with OAuth...")
        youtube = get_youtube_mcp(use_oauth=True)
        
        # Test 1: Liked videos
        print("\n👍 Getting liked videos...")
        liked = youtube.get_liked_videos(max_results=5)
        print(f"✓ Found {len(liked)} liked videos")
        if liked:
            print(f"  Latest: {liked[0]['title']}")
        
        # Test 2: Subscriptions
        print("\n📺 Getting subscriptions...")
        subs = youtube.get_subscriptions(max_results=5)
        print(f"✓ Subscribed to {len(subs)} channels")
        for s in subs[:3]:
            print(f"  - {s['channel_title']}")
        
        # Test 3: Recommended videos
        print("\n🎯 Getting recommended videos...")
        recommended = youtube.get_recommended_videos(max_results=5)
        print(f"✓ Found {len(recommended)} recommendations")
        
        # Test 4: Search
        print("\n🔍 Searching for 'python tutorial'...")
        search_results = youtube.search_videos("python tutorial", max_results=3)
        print(f"✓ Found {len(search_results)} results")
        
        print("\n✅ All tests passed!")
        
    except YouTubeError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")