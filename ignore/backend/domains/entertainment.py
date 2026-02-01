from typing import Dict, List, Any, Optional
from .base import BaseDomain

class EntertainmentDomain(BaseDomain):
    """
    Handles: concerts, movies, music, and trending videos.
    """

    def get_required_mcps(self, user_prompt: str) -> List[str]:
        mcps = ["browser", "search"]
        prompt = user_prompt.lower()

        # Music
        if any(word in prompt for word in ["music", "concert", "artist", "song", "spotify", "playlist"]):
            mcps.append("spotify")

        # Videos
        if any(word in prompt for word in ["youtube", "video", "trending", "watch", "channel"]):
            mcps.append("youtube")

        # Movies/Series
        if any(word in prompt for word in ["movie", "film", "series", "show", "netflix", "streaming", "actor"]):
            mcps.append("movie")

        # Scheduling
        if any(word in prompt for word in ["schedule", "remind", "calendar", "date", "booking"]):
            mcps.append("google_workspace")
            
        # Location for events
        if any(word in prompt for word in ["near", "nearby", "tonight", "concert", "event"]):
            mcps.append("location")

        return list(set(mcps))

    def select_ui_template(self, mcp_data: Dict[str, Any]) -> str:
        if "movie" in mcp_data and mcp_data["movie"].get("results"):
            return "MovieCard"
        if "youtube" in mcp_data and mcp_data["youtube"].get("results"):
            return "VideoGrid"
        return "EntertainmentDashboard"

    def prepare_ui_props(self, mcp_data: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        props = {
            "response": llm_response,
            "timestamp": mcp_data.get("timestamp", ""),
            "videos": [],
            "music": {},
            "movies": [],
            "context": {}
        }
        
        # YouTube Videos
        if "youtube" in mcp_data:
            props["videos"] = mcp_data["youtube"].get("results", [])[:12]
            
        # Spotify Music
        if "spotify" in mcp_data:
            props["music"] = mcp_data["spotify"]
            
        # Movie Data
        if "movie" in mcp_data:
            props["movies"] = mcp_data["movie"].get("results", [])
            
        # Location & Events
        if "location" in mcp_data:
            loc_results = mcp_data["location"].get("results", [])
            if loc_results:
                props["current_city"] = loc_results[0].get("name")
                props["nearby_entertainment"] = mcp_data["location"].get("amenities", [])

        # Web Search Context
        if "search" in mcp_data:
            props["web_context"] = mcp_data["search"].get("results", [])
            
        # Browser Context
        if "browser" in mcp_data:
            tabs = mcp_data["browser"].get("tabs", [])
            props["context"]["open_tabs"] = len(tabs)
            props["context"]["related_titles"] = [t.get("title") for t in tabs if "imdb" in t.get("url", "") or "youtube" in t.get("url", "")]

        return props

    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        return "browser" in mcp_data

    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
        return "What movie, artist, or video are you looking for?"

    def prepare_template_data(
        self, 
        template_id: str, 
        mcp_data: Dict[str, Any], 
        llm_response: str
    ) -> Dict[str, Any]:
        """Transform MCP data for template-specific rendering"""
        
        props = self.prepare_ui_props(mcp_data, llm_response)
        
        if template_id == "MovieCard":
            return {
                "title": "Movie Insights",
                "movies": props.get("movies", []),
                "summary": llm_response
            }
        elif template_id == "VideoGrid":
            return {
                "title": "Trending Videos",
                "videos": props.get("videos", []),
                "channel": "Featured"
            }
        else:
            return {
                "title": f"Entertainment: {llm_response[:30]}...",
                "videos": props.get("videos", []),
                "movies": props.get("movies", []),
                "music": props.get("music", {}),
                "summary": llm_response
            }
