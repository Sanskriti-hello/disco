from typing import Dict, List, Any, Optional
from .base import BaseDomain

class EntertainmentDomain(BaseDomain):
    """
    Handles: concerts, movies, music, events, streaming
    
    Example queries:
    - "Find concerts near me this weekend"
    - "What's trending on YouTube?"
    - "Recommend movies based on my taste"
    """
    def get_required_mcps(self, user_prompt: str) -> List[str]:
        # Decides which MCPs to call based on user's query
        mcps = ["browser"]
        prompt_lower = user_prompt.lower()
        
        # Location for local events
        if any(word in prompt_lower for word in ["concert", "near", "tonight", "show", "live", "event"]):
            mcps.append("location") 
            
        # Spotify for music recs
        if any(word in prompt_lower for word in ["music", "concert", "artist", "recommend", "song", "spotify"]):
            mcps.append("spotify")  
            
        # YouTube for video content
        if any(word in prompt_lower for word in ["youtube", "video", "trending", "watch"]):
            mcps.append("youtube")  
            
        # Google Workspace (Calendar) for scheduling events
        if any(word in prompt_lower for word in ["schedule", "remind", "calendar", "book", "date"]):
            mcps.append("google_workspace")
      
        # Web search mandatory
        mcps.append("search")
        
        return mcps
    
    def get_system_prompt(self) -> str:
        
        return """You are an enthusiastic entertainment assistant helping users discover amazing experiences.

                **Your Capabilities:**
                - Find live concerts, shows, and events based on user's location and music taste
                - Recommend movies and TV shows based on viewing history
                - Surface trending content on YouTube, Spotify, and other platforms
                - Provide event details: venue, timing, ticket prices, artist information

                **Available Context:**
                - User's current location (for "near me" queries)
                - Music listening history from Spotify (for personalized recommendations)
                - Browser history (to understand entertainment preferences)
                - Current date/time (for "tonight", "this weekend" queries)

                **Your Tone:**
                - Be enthusiastic but not over-the-top
                - Focus on actionable recommendations
                - Include relevant details (price, time, location)
                - Suggest 2-3 top options rather than overwhelming with choices

                **Example Response:**
                "🎸 Great news! I found 2 concerts perfect for your indie rock taste this weekend:

                1. **Tame Impala** at Chase Center - Saturday 8PM ($89+)
                2. **Beach House** at The Fillmore - Sunday 7:30PM (Sold Out, waitlist available)

                Both are within 5 miles of downtown SF. Want me to add one to your calendar?"
                Keep it concise, helpful, and exciting!"""
    
    def select_ui_template(self, mcp_data: Dict[str, Any]) -> str:
        
        # Used to choose which UI template to use(Example cases - need to
        # decide based on final templates)
        
        has_location = "location" in mcp_data
        has_spotify = "spotify" in mcp_data
        has_youtube = "youtube" in mcp_data
        
        has_events = self._has_event_data(mcp_data.get("search", {}))
        
        # Decision tree for template selection (will be modified based on templates)
        
        # Case 1: Concert/Event cards (location + event data)
        if has_location and has_events:
            return "ConcertCard"  # ← This must match extension/components/ConcertCard.jsx
        
        # Case 2: Music recommendations carousel
        if has_spotify:
            return "MusicRecommendations"
        
        # Case 3: Video grid for YouTube
        if has_youtube:
            return "VideoGrid"
        
        # Default: Generic list
        return "EntertainmentList"
    
    def prepare_ui_props(self, mcp_data: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        
        # Transforms messy MCP data into clean React props for the selected UI template.
        props = {
            "userMessage": llm_response,  # What the LLM said
            "timestamp": mcp_data.get("timestamp", ""),
        }
        
        # Add location data if available
        if "location" in mcp_data:
            props["location"] = {
                "city": mcp_data["location"].get("city", "Unknown"),
                "state": mcp_data["location"].get("state", ""),
                "coordinates": mcp_data["location"].get("coordinates", [0, 0]),
            }
        
        # Extract concert/event data from search results
        if "search" in mcp_data and self._has_event_data(mcp_data["search"]):
            events = self._extract_events(mcp_data["search"])
            props["events"] = events
        
        # Add Spotify recommendations
        if "spotify" in mcp_data:
            spotify_data = mcp_data["spotify"]
            props["recommendations"] = {
                "topArtists": spotify_data.get("top_artists", [])[:5],  # Top 5
                "recentTracks": spotify_data.get("recent_tracks", [])[:10],
                "genres": spotify_data.get("top_genres", []),
            }
        
        # Add YouTube videos
        if "youtube" in mcp_data:
            youtube_data = mcp_data["youtube"]
            props["videos"] = youtube_data.get("results", [])[:12]  # Grid of 12
        
        # Add browser context for personalization
        if "browser" in mcp_data:
            browser_data = mcp_data["browser"]
            props["context"] = {
                "recentSearches": browser_data.get("recent_searches", [])[:5],
                "openTabs": len(browser_data.get("tabs", [])),
            }
        
        return props
    
    # ***Optional Checks

    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        # Improvements to be made, you can add more checks to ask follow up questions
        
        # Making data from browser mandatory
        if "browser" not in mcp_data:
            return False
        # An example for check (location here)
        if self._is_event_query(mcp_data) and "location" not in mcp_data:
            return False
        
        return True
    
    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
        #  Ask for follow-up questions for missing data
        #  Can be improved, based on final servers
        if "location" not in mcp_data and self._is_event_query(mcp_data):
            return "I need your location to find nearby events. Could you share your city or enable location access?"
        
        if "spotify" not in mcp_data:
            return "To personalize recommendations, connect your Spotify account or tell me your favorite artists/genres!"
        
        return "What kind of entertainment are you looking for? (concerts, movies, music, videos)"
    
    # ========== HELPER METHODS ==========
    # Checks and data extraction methods - can be added as needed
    
    def _is_event_query(self, mcp_data: Dict[str, Any]) -> bool:
        """Check if user is asking about events/concerts"""
        browser = mcp_data.get("browser", {})
        recent_searches = " ".join(browser.get("recent_searches", [])).lower()
        
        event_keywords = ["concert", "event", "show", "tour", "live", "tickets"]
        return any(keyword in recent_searches for keyword in event_keywords)
    
    def _has_event_data(self, search_data: Dict[str, Any]) -> bool:
        """Check if search results contain event information"""
        results = search_data.get("results", [])
        
        event_keywords = ["concert", "tour", "tickets", "venue", "showtime", "event"]
        
        for result in results:
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            text = f"{title} {snippet}"
            
            if any(keyword in text for keyword in event_keywords):
                return True
        
        return False
    
    def _extract_events(self, search_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse search results to extract structured event data.
        
        In production, you'd use:
        - NER (Named Entity Recognition) for venue extraction
        - Date parsing libraries for date extraction
        - Regex for price extraction
        
        For now, we'll do simple extraction.
        """
        events = []
        results = search_data.get("results", [])
        
        for result in results[:5]:  # Top 5 results
            event = {
                "title": result.get("title", "Unknown Event"),
                "description": result.get("snippet", ""),
                "url": result.get("url", ""),
                "imageUrl": result.get("image", "https://via.placeholder.com/300x200"),
                
                "venue": self._extract_venue(result),
                "date": self._extract_date(result),
                "price": self._extract_price(result),
            }
            events.append(event)
        
        return events
    
    def _extract_venue(self, result: Dict[str, Any]) -> str:
        """Extract venue name from result (placeholder)"""
        # TODO: Use regex or NER
        # Look for patterns like "at [Venue Name]"
        snippet = result.get("snippet", "")
        if " at " in snippet:
            parts = snippet.split(" at ")
            if len(parts) > 1:
                return parts[1].split(",")[0].strip()
        return "Venue TBA"
    
    def _extract_date(self, result: Dict[str, Any]) -> str:
        """Extract date from result (placeholder)"""
        # TODO: Use date parsing library like dateutil
        return result.get("date", "Date TBA")
    
    def _extract_price(self, result: Dict[str, Any]) -> str:
        """Extract price from result (placeholder)"""
        # TODO: Use regex to find $XX patterns
        snippet = result.get("snippet", "")
        if "$" in snippet:
            # Simple extraction
            import re
            price_match = re.search(r'\$\d+', snippet)
            if price_match:
                return price_match.group() + "+"
        return "Price TBA"