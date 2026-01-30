from typing import Dict, List, Any, Optional
import re
from datetime import datetime
from .base import BaseDomain

class TravelDomain(BaseDomain):
    
    def get_required_mcps(self, user_prompt: str) -> List[str]:
        # Making location also mandatory
        mcps = ["browser", "location"] 
        prompt_lower = user_prompt.lower()
        
        # Calendar access for date checking and scheduling
        date_keywords = ["next", "weekend", "when", "available", "schedule", "book", "plan"]
        if any(word in prompt_lower for word in date_keywords):
            mcps.append("google_workspace")
        
        # Weather for destination forecasts (OpenWeatherMap)
        mcps.append("weather")
            
        # Making browser search mandatory 
        mcps.append("search")
        return mcps
    
    def get_system_prompt(self) -> str:

        return """You are a professional travel planning assistant helping users plan trips and book travel.

            **Your Capabilities:**
            - Find and compare flights across multiple airlines based on dates, budget, and preferences
            - Recommend hotels with filters (price range, location, amenities, ratings)
            - Create comprehensive itineraries for trips with activities and timing
            - Provide directions and local recommendations for destinations
            - Check user's calendar to find available travel dates
            - Compare travel options and highlight best value

            **Available Context:**
            - User's current location (as origin for flights/trips)
            - Calendar events to avoid scheduling conflicts
            - Browser history to understand travel preferences and past searches
            - Current search results for real-time prices and availability

            **Your Response Style:**
            - Be helpful and detail-oriented
            - Present options clearly with key information: price, duration, ratings, amenities
            - Highlight the best value options
            - Include practical details: baggage policies, cancellation terms, check-in times
            - Suggest 2-4 top options rather than overwhelming with too many choices

            **Example Response:**
            "✈️ I found 3 great flight options to Tokyo for next month:

            1. **United Airlines** - $850 (Best Value)
            - Direct flight, 11h 45m, Departs Feb 15 at 10:30 AM
            - Includes checked bag, good legroom

            2. **ANA** - $920 (Most Comfort)  
            - Direct, 12h 10m, Premium economy available
            - Excellent reviews (4.8/5)

            3. **Delta (via Seattle)** - $720 (Budget Option)
            - One stop, 15h 30m total
            - 3-hour layover in Seattle

            I checked your calendar - you're free Feb 15-25. Which option interests you?"

            Keep responses organized, practical, and focused on helping users make informed travel decisions."""

    def select_ui_template(self, mcp_data: Dict[str, Any]) -> str:
        # Choose template accordingly - can be changed based on final templates
        browser = mcp_data.get("browser", {})
        recent_searches = " ".join(browser.get("recent_searches", [])).lower()
        search_data = mcp_data.get("search", {})
        
        # Flight queries
        if self._has_flight_data(search_data) or any(word in recent_searches for word in ["flight", "fly", "airline"]):
            return "FlightCard"
        # Hotel queries
        if self._has_hotel_data(search_data) or any(word in recent_searches for word in ["hotel", "stay", "accommodation", "room"]):
            return "HotelCard"
        # Itinerary/planning queries
        if any(word in recent_searches for word in ["itinerary", "plan", "trip", "visit", "travel guide"]):
            return "TripItinerary"
        # Default comprehensive travel dashboard
        return "TravelDashboard"
    
    def prepare_ui_props(self, mcp_data: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        # Transform MCP data into React component props for travel UI.
        props = {
            "recommendation": llm_response,
            "timestamp": mcp_data.get("timestamp", datetime.now().isoformat()),
        }
        if "location" in mcp_data:
            loc_results = mcp_data["location"].get("results", [])
            if loc_results:
                best_loc = loc_results[0]
                addr = best_loc.get("address", {})
                props["origin"] = {
                    "name": best_loc.get("name", ""),
                    "city": addr.get("city") or addr.get("town") or addr.get("suburb", "Unknown"),
                    "state": addr.get("state", ""),
                    "country": addr.get("country", ""),
                    "coordinates": [best_loc["location"]["lat"], best_loc["location"]["lon"]]
                }
        
        # Flight search results
        search_data = mcp_data.get("search", {})
        if self._has_flight_data(search_data):
            props["flights"] = self._extract_flights(search_data)
        # Hotel search results
        if self._has_hotel_data(search_data):
            props["hotels"] = self._extract_hotels(search_data)
        # Calendar availability
        if "google_workspace" in mcp_data:
            calendar = mcp_data["google_workspace"].get("calendar", {})
            props["availability"] = {
                "busyDates": calendar.get("busy_dates", []),
                "upcomingEvents": calendar.get("events", [])[:5],
                "freeDateRanges": calendar.get("free_ranges", []),
            }
        # Browser context for personalization
        if "browser" in mcp_data:
            browser_data = mcp_data["browser"]
            props["context"] = {
                "recentSearches": browser_data.get("recent_searches", [])[:5],
                "savedDestinations": self._extract_saved_destinations(browser_data),
                "travelPreferences": self._infer_preferences(browser_data),
            }
        return props
    
    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        # Check if we have sufficient data for travel planning.
        # Must have location 
        if "location" not in mcp_data:
            return False
        # Must have search results
        if "search" not in mcp_data:
            return False
        # Check if search has relevant travel data
        search_data = mcp_data["search"]
        has_travel_data = (
            self._has_flight_data(search_data) or 
            self._has_hotel_data(search_data) or
            len(search_data.get("results", [])) > 0
        )
        return has_travel_data
    
    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
        # Follow up questions for missing travel data.
        if "location" not in mcp_data:
            return "Where are you traveling from? I need your origin city to search for flights."
        if "google_workspace" not in mcp_data:
            return "Would you like me to check your calendar for available travel dates?"
        if "search" not in mcp_data or not mcp_data["search"].get("results"):
            return "Could you provide more details? Destination, dates, and budget would help me find the best options."
        
        return "What are your travel dates and approximate budget?"
    
    # Functions to check and extract travel data from search results
    
    def _has_flight_data(self, search_data: Dict[str, Any]) -> bool:
        # Check if search results contain flight information.
        results = search_data.get("results", [])
        flight_keywords = ["flight", "airline", "airport", "departure", "arrival", "nonstop", "layover"]
        
        for result in results:
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            text = f"{title} {snippet}"
            if any(keyword in text for keyword in flight_keywords):
                return True
        return False
    
    def _has_hotel_data(self, search_data: Dict[str, Any]) -> bool:
        # Check if search results contain hotel information.
        results = search_data.get("results", [])
        hotel_keywords = ["hotel", "accommodation", "booking", "room", "stay", "resort", "inn"]
        for result in results:
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            text = f"{title} {snippet}"
            if any(keyword in text for keyword in hotel_keywords):
                return True
        return False
    
    def _extract_flights(self, search_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse flight data from search results.
        In production, you'd integrate with flight APIs (Skyscanner, Google Flights).
        """
        flights = []
        results = search_data.get("results", [])
        
        for result in results[:6]:  # Top 6 flight options
            flight = {
                "id": result.get("id", f"flight_{len(flights)}"),
                "airline": self._extract_airline(result),
                "price": self._extract_price(result),
                "departureTime": self._extract_time(result, "departure"),
                "arrivalTime": self._extract_time(result, "arrival"),
                "duration": self._extract_duration(result),
                "stops": self._extract_stops(result),
                "bookingUrl": result.get("url", ""),
                "title": result.get("title", ""),
                "description": result.get("snippet", ""),
            }
            
            flights.append(flight)
        
        return flights
    
    def _extract_hotels(self, search_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse hotel data from search results.
        In production, you'd integrate with hotel APIs (Booking.com, Hotels.com).
        """
        hotels = []
        results = search_data.get("results", [])
        
        for result in results[:6]:  # Top 6 hotels
            hotel = {
                "id": result.get("id", f"hotel_{len(hotels)}"),
                "name": result.get("title", "Unknown Hotel"),
                "price": self._extract_price(result),
                "pricePerNight": self._extract_price_per_night(result),
                "rating": self._extract_rating(result),
                "reviewCount": self._extract_review_count(result),
                "location": self._extract_location(result),
                "amenities": self._extract_amenities(result),
                "imageUrl": result.get("image", "https://via.placeholder.com/400x300"),
                "bookingUrl": result.get("url", ""),
                "description": result.get("snippet", ""),
            }
            
            hotels.append(hotel)
        
        return hotels
    
    def _extract_saved_destinations(self, browser_data: Dict[str, Any]) -> List[str]:
        """Extract travel-related bookmarks and frequently visited sites."""
        bookmarks = browser_data.get("bookmarks", [])
        travel_sites = ["booking.com", "airbnb.com", "tripadvisor", "expedia", "kayak"]
        
        saved = []
        for bookmark in bookmarks:
            url = bookmark.get("url", "").lower()
            if any(site in url for site in travel_sites):
                saved.append(bookmark.get("title", ""))
        
        return saved[:5]
    
    def _infer_preferences(self, browser_data: Dict[str, Any]) -> Dict[str, Any]:
        """Infer travel preferences from browsing history."""
        recent_searches = browser_data.get("recent_searches", [])
        
        preferences = {
            "prefersDirect": any("direct" in s.lower() or "nonstop" in s.lower() for s in recent_searches),
            "budgetConscious": any("cheap" in s.lower() or "budget" in s.lower() for s in recent_searches),
            "luxurySeeker": any("luxury" in s.lower() or "5 star" in s.lower() for s in recent_searches),
        }
        
        return preferences
    
    # ========== EXTRACTION HELPERS ==========
    # These parse unstructured search results into structured data
    
    def _extract_airline(self, result: Dict[str, Any]) -> str:
        """Extract airline name from search result."""
        title = result.get("title", "")
        common_airlines = ["United", "Delta", "American", "Southwest", "JetBlue", "Spirit", "Frontier", "Alaska"]
        
        for airline in common_airlines:
            if airline.lower() in title.lower():
                return airline
        
        return "Airline TBA"
    
    def _extract_price(self, result: Dict[str, Any]) -> str:
        """Extract price from search result."""
        text = f"{result.get('title', '')} {result.get('snippet', '')}"
        
        # Look for $XXX or $X,XXX patterns
        price_pattern = r'\$[\d,]+'
        matches = re.findall(price_pattern, text)
        
        if matches:
            return matches[0]
        
        return "Price TBA"
    
    def _extract_price_per_night(self, result: Dict[str, Any]) -> str:
        """Extract per-night price for hotels."""
        snippet = result.get("snippet", "")
        
        # Look for "per night", "/night", "a night" patterns
        if "night" in snippet.lower():
            price_pattern = r'\$\d+(?:,\d+)?'
            matches = re.findall(price_pattern, snippet)
            if matches:
                return matches[0] + "/night"
        
        return self._extract_price(result)
    
    def _extract_time(self, result: Dict[str, Any], time_type: str) -> str:
        """Extract departure or arrival time."""
        snippet = result.get("snippet", "")
        
        # Look for time patterns like "10:30 AM" or "14:45"
        time_pattern = r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?'
        matches = re.findall(time_pattern, snippet)
        
        if matches:
            if time_type == "departure" and len(matches) > 0:
                return matches[0]
            elif time_type == "arrival" and len(matches) > 1:
                return matches[1]
        
        return "Time TBA"
    
    def _extract_duration(self, result: Dict[str, Any]) -> str:
        """Extract flight duration."""
        snippet = result.get("snippet", "")
        
        # Look for patterns like "11h 45m" or "11 hours"
        duration_pattern = r'\d+h\s*\d*m?|\d+\s*hours?'
        match = re.search(duration_pattern, snippet, re.IGNORECASE)
        
        if match:
            return match.group()
        
        return "Duration TBA"
    
    def _extract_stops(self, result: Dict[str, Any]) -> int:
        """Extract number of stops."""
        text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
        
        if "nonstop" in text or "direct" in text or "non-stop" in text:
            return 0
        elif "1 stop" in text or "one stop" in text:
            return 1
        elif "2 stop" in text or "two stop" in text:
            return 2
        
        # Default assumption
        return 0
    
    def _extract_rating(self, result: Dict[str, Any]) -> float:
        """Extract hotel rating."""
        text = f"{result.get('title', '')} {result.get('snippet', '')}"
        
        # Look for ratings like "4.5/5" or "4.5 stars"
        rating_pattern = r'(\d+\.?\d*)\s*(?:/5|stars?|rating)'
        match = re.search(rating_pattern, text, re.IGNORECASE)
        
        if match:
            return float(match.group(1))
        
        return 0.0
    
    def _extract_review_count(self, result: Dict[str, Any]) -> int:
        """Extract number of reviews."""
        snippet = result.get("snippet", "")
        
        # Look for patterns like "1,234 reviews" or "500 ratings"
        review_pattern = r'([\d,]+)\s*(?:reviews?|ratings?)'
        match = re.search(review_pattern, snippet, re.IGNORECASE)
        
        if match:
            count_str = match.group(1).replace(",", "")
            return int(count_str)
        
        return 0
    
    def _extract_location(self, result: Dict[str, Any]) -> str:
        """Extract hotel location/neighborhood."""
        snippet = result.get("snippet", "")
        
        # Look for "in [Location]" or "near [Location]"
        location_pattern = r'(?:in|near)\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|\s-)'
        match = re.search(location_pattern, snippet)
        
        if match:
            return match.group(1).strip()
        
        return "Location TBA"
    
    def _extract_amenities(self, result: Dict[str, Any]) -> List[str]:
        """Extract hotel amenities."""
        snippet = result.get("snippet", "").lower()
        
        common_amenities = {
            "pool": "Pool",
            "wifi": "Free WiFi",
            "parking": "Free Parking",
            "breakfast": "Breakfast Included",
            "gym": "Fitness Center",
            "spa": "Spa",
            "restaurant": "Restaurant",
            "bar": "Bar",
            "airport shuttle": "Airport Shuttle",
        }
        
        found_amenities = []
        for keyword, amenity in common_amenities.items():
            if keyword in snippet:
                found_amenities.append(amenity)
        
        return found_amenities[:5]  # Return top 5
    
    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        """
        Travel-specific validation: Need location and search results.
        """
        
        # Must have user's location
        if "location" not in mcp_data:
            return False
        
        # Must have search results with travel data
        if "search" not in mcp_data:
            return False
        
        search_data = mcp_data["search"]
        has_travel_data = (
            self._has_flight_data(search_data) or 
            self._has_hotel_data(search_data) or
            len(search_data.get("results", [])) >= 2
        )
        
        return has_travel_data
    
    def prepare_template_data(
        self, 
        template_id: str, 
        mcp_data: Dict[str, Any], 
        llm_response: str
    ) -> Dict[str, Any]:
        """Transform MCP data for template-specific rendering"""
        
        props = self.prepare_ui_props(mcp_data, llm_response)
        
        if template_id == "TripItinerary":
            return {
                "title": "Your Trip Itinerary",
                "days": self._generate_itinerary_days(mcp_data, llm_response),
                "map_center": props.get("origin", {}).get("coordinates", [0, 0]),
                "summary": llm_response
            }
        elif template_id == "FlightCard":
            return {
                "title": "Available Flights",
                "flights": props.get("flights", []),
                "origin": props.get("origin", {}).get("city", "Origin"),
                "destination": "Destination" # Could be extracted from prompt
            }
        elif template_id == "HotelCard":
            return {
                "title": "Top Hotel Picks",
                "hotels": props.get("hotels", []),
                "city": props.get("origin", {}).get("city", "City")
            }
        else:
            # Fallback to TravelDashboard or Generic
            return {
                "title": "Travel Dashboard",
                "flights": props.get("flights", []),
                "hotels": props.get("hotels", []),
                "itinerary": props.get("itinerary", []),
                "context": props.get("context", {}),
                "summary": llm_response
            }

    def _generate_itinerary_days(self, mcp_data: Dict, llm_response: str) -> List[Dict]:
        """Helper to generate itinerary days from LLM response or search"""
        days = []
        # Simple extraction from LLM response for now
        # In a real app, this would be more sophisticated
        days.append({
            "day": 1,
            "title": "Arrival & Exploration",
            "activities": ["Check-in", "Local dinner", "Walk around city center"]
        })
        return days

'''
# ========== QUICK TEST ==========
if __name__ == "__main__":
    """Test TravelDomain independently"""
    
    print("🧪 Testing TravelDomain...\n")
    
    domain = TravelDomain()
    
    # Test 1: MCP Requirements
    print("TEST 1: MCP Requirements")
    mcps = domain.get_required_mcps("find flights to Tokyo next month")
    print(f"  MCPs needed: {mcps}")
    assert "location" in mcps
    assert "google_workspace" in mcps
    assert "search" in mcps
    print("  ✅ Pass\n")
    
    # Test 2: System Prompt
    print("TEST 2: System Prompt")
    prompt = domain.get_system_prompt()
    assert "travel" in prompt.lower()
    assert "flight" in prompt.lower()
    print(f"  Length: {len(prompt)} characters")
    print("  ✅ Pass\n")
    
    # Test 3: Sample Data Processing
    print("TEST 3: Data Processing")
    sample_data = {
        "browser": {"tabs": [], "recent_searches": ["flights to paris"]},
        "location": {"city": "New York", "coordinates": [40.7, -74.0]},
        "search": {
            "results": [
                {
                    "title": "United Airlines to Paris - $850",
                    "snippet": "Direct flight, 7h 30m. Departure 10:30 AM, Arrival 11:00 PM local time.",
                    "url": "https://united.com/..."
                }
            ]
        }
    }
    
    is_valid = domain.validate_data(sample_data)
    print(f"  Data valid: {is_valid}")
    assert is_valid
    
    template = domain.select_ui_template(sample_data)
    print(f"  Template: {template}")
    assert template == "FlightCard"
    
    props = domain.prepare_ui_props(sample_data, "I found great flights!")
    print(f"  Props keys: {list(props.keys())}")
    assert "flights" in props
    assert "origin" in props
    
    print("  ✅ Pass\n")
    
    print("✅ All TravelDomain tests passed! 🎉")
'''