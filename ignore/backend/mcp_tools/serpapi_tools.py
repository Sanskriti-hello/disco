"""
SerpAPI Unified Search Tools
============================
Comprehensive search tools using SerpAPI for real data retrieval.
Replaces fake/non-working MCP tools with production-ready implementations.

Supported engines:
- Google Search (web, images, news, shopping, local, events, scholar)
- Google Finance & Markets
- Google Flights & Travel
- Google Maps Reviews
- Amazon Products

Setup:
    pip install google-search-results
    
Environment:
    SERPAPI_KEY - Your SerpAPI key
"""

import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Default API key from environment, fallback to provided key
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "547d7427ab2c82036b19f65cc17730906280cd3510f006fc1be7cf5bb6c97463")


class SerpAPIClient:
    """
    Unified SerpAPI client for all Google and Amazon searches.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or SERPAPI_KEY
        self._serpapi = None
    
    def _get_client(self):
        """Lazy load SerpAPI"""
        if self._serpapi is None:
            try:
                from serpapi import GoogleSearch
                self._serpapi = GoogleSearch
            except ImportError:
                raise ImportError("Please install serpapi: pip install google-search-results")
        return self._serpapi
    
    def _search(self, params: Dict) -> Dict:
        """Execute a SerpAPI search with the given params."""
        params["api_key"] = self.api_key
        GoogleSearch = self._get_client()
        search = GoogleSearch(params)
        return search.get_dict()
    
    # =========================================================================
    # GOOGLE WEB SEARCH
    # =========================================================================
    
    def search_web(
        self, 
        query: str, 
        location: str = "United States",
        num: int = 10,
        hl: str = "en",
        gl: str = "us"
    ) -> Dict[str, Any]:
        """
        Search Google for web results.
        
        Args:
            query: Search query
            location: Location for localized results
            num: Number of results (max 100)
            hl: Language code
            gl: Country code
            
        Returns:
            Dict with organic_results, knowledge_graph, etc.
        """
        params = {
            "engine": "google",
            "q": query,
            "location": location,
            "google_domain": "google.com",
            "hl": hl,
            "gl": gl,
            "num": num
        }
        
        try:
            results = self._search(params)
            return {
                "query": query,
                "organic_results": results.get("organic_results", []),
                "knowledge_graph": results.get("knowledge_graph", {}),
                "related_searches": results.get("related_searches", []),
                "answer_box": results.get("answer_box", {}),
                "top_stories": results.get("top_stories", [])
            }
        except Exception as e:
            return {"error": str(e), "query": query}
    
    # =========================================================================
    # GOOGLE IMAGES
    # =========================================================================
    
    def search_images(
        self, 
        query: str, 
        location: str = "United States",
        num: int = 20,
        hl: str = "en",
        gl: str = "us"
    ) -> Dict[str, Any]:
        """
        Search Google Images.
        
        Args:
            query: Image search query
            location: Location for results
            num: Number of images
            
        Returns:
            Dict with images_results containing thumbnails and original URLs
        """
        params = {
            "engine": "google_images",
            "q": query,
            "location": location,
            "google_domain": "google.com",
            "hl": hl,
            "gl": gl,
            "num": num
        }
        
        try:
            results = self._search(params)
            images = results.get("images_results", [])
            
            # Format for easier consumption
            formatted = []
            for img in images[:num]:
                formatted.append({
                    "title": img.get("title", ""),
                    "url": img.get("original", ""),
                    "thumbnail": img.get("thumbnail", ""),
                    "source": img.get("source", ""),
                    "link": img.get("link", ""),
                    "width": img.get("original_width", 0),
                    "height": img.get("original_height", 0)
                })
            
            return {"query": query, "images": formatted}
        except Exception as e:
            return {"error": str(e), "query": query}
    
    # =========================================================================
    # GOOGLE NEWS
    # =========================================================================
    
    def search_news(
        self, 
        query: str,
        hl: str = "en",
        gl: str = "us"
    ) -> Dict[str, Any]:
        """
        Search Google News for articles.
        
        Args:
            query: News search query
            
        Returns:
            Dict with news_results containing headlines, sources, dates
        """
        params = {
            "engine": "google_news",
            "q": query,
            "hl": hl,
            "gl": gl
        }
        
        try:
            results = self._search(params)
            news = results.get("news_results", [])
            
            formatted = []
            for article in news[:20]:
                formatted.append({
                    "title": article.get("title", ""),
                    "link": article.get("link", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "date": article.get("date", ""),
                    "snippet": article.get("snippet", ""),
                    "thumbnail": article.get("thumbnail", "")
                })
            
            return {"query": query, "articles": formatted}
        except Exception as e:
            return {"error": str(e), "query": query}
    
    # =========================================================================
    # GOOGLE SHOPPING (Amazon alternative)
    # =========================================================================
    
    def search_shopping(
        self, 
        query: str, 
        location: str = "United States"
    ) -> Dict[str, Any]:
        """
        Search Google Shopping for products.
        
        Args:
            query: Product search query
            location: Location for pricing
            
        Returns:
            Dict with shopping_results containing products, prices, ratings
        """
        params = {
            "engine": "google_shopping",
            "q": query,
            "location": location
        }
        
        try:
            results = self._search(params)
            products = results.get("shopping_results", [])
            
            formatted = []
            for product in products[:20]:
                formatted.append({
                    "title": product.get("title", ""),
                    "price": product.get("extracted_price", product.get("price", "")),
                    "price_raw": product.get("price", ""),
                    "link": product.get("link", ""),
                    "source": product.get("source", ""),
                    "rating": product.get("rating", 0),
                    "reviews": product.get("reviews", 0),
                    "thumbnail": product.get("thumbnail", ""),
                    "delivery": product.get("delivery", "")
                })
            
            return {"query": query, "products": formatted}
        except Exception as e:
            return {"error": str(e), "query": query}
    
    # =========================================================================
    # AMAZON PRODUCTS
    # =========================================================================
    
    def search_amazon(
        self, 
        query: str, 
        domain: str = "amazon.com"
    ) -> Dict[str, Any]:
        """
        Search Amazon for products.
        
        Args:
            query: Product search query
            domain: Amazon domain (amazon.com, amazon.co.uk, etc.)
            
        Returns:
            Dict with products including prices, ratings, prime status
        """
        params = {
            "engine": "amazon",
            "k": query,
            "amazon_domain": domain
        }
        
        try:
            results = self._search(params)
            products = results.get("organic_results", [])
            
            formatted = []
            for product in products[:15]:
                formatted.append({
                    "asin": product.get("asin", ""),
                    "title": product.get("title", ""),
                    "price": product.get("price", {}).get("raw", "") if isinstance(product.get("price"), dict) else product.get("price", ""),
                    "extracted_price": product.get("price", {}).get("extracted_value", 0) if isinstance(product.get("price"), dict) else 0,
                    "rating": product.get("rating", 0),
                    "reviews_count": product.get("reviews", 0),
                    "link": product.get("link", ""),
                    "thumbnail": product.get("thumbnail", ""),
                    "is_prime": product.get("is_prime", False),
                    "is_best_seller": product.get("is_best_seller", False)
                })
            
            return {"query": query, "products": formatted}
        except Exception as e:
            return {"error": str(e), "query": query}
    
    # =========================================================================
    # GOOGLE LOCAL (Places)
    # =========================================================================
    
    def search_local(
        self, 
        query: str, 
        location: str = "United States",
        hl: str = "en",
        gl: str = "us"
    ) -> Dict[str, Any]:
        """
        Search Google Local/Maps for businesses and places.
        
        Args:
            query: Local search query (e.g., "pizza near me", "hotels in NYC")
            location: Location context
            
        Returns:
            Dict with local_results containing businesses, ratings, addresses
        """
        params = {
            "engine": "google_local",
            "q": query,
            "location": location,
            "google_domain": "google.com",
            "hl": hl,
            "gl": gl
        }
        
        try:
            results = self._search(params)
            places = results.get("local_results", [])
            
            formatted = []
            for place in places[:15]:
                formatted.append({
                    "title": place.get("title", ""),
                    "place_id": place.get("place_id", ""),
                    "data_id": place.get("data_id", ""),
                    "address": place.get("address", ""),
                    "phone": place.get("phone", ""),
                    "rating": place.get("rating", 0),
                    "reviews": place.get("reviews", 0),
                    "type": place.get("type", ""),
                    "price": place.get("price", ""),
                    "hours": place.get("hours", ""),
                    "thumbnail": place.get("thumbnail", ""),
                    "gps_coordinates": place.get("gps_coordinates", {}),
                    "website": place.get("website", ""),
                    "directions": place.get("directions", "")
                })
            
            return {"query": query, "places": formatted}
        except Exception as e:
            return {"error": str(e), "query": query}
    
    # =========================================================================
    # GOOGLE EVENTS
    # =========================================================================
    
    def search_events(
        self, 
        query: str,
        hl: str = "en"
    ) -> Dict[str, Any]:
        """
        Search Google Events.
        
        Args:
            query: Event search query (e.g., "concerts in Austin")
            
        Returns:
            Dict with events including dates, venues, ticket links
        """
        params = {
            "engine": "google_events",
            "q": query,
            "hl": hl
        }
        
        try:
            results = self._search(params)
            events = results.get("events_results", [])
            
            formatted = []
            for event in events[:15]:
                formatted.append({
                    "title": event.get("title", ""),
                    "date": event.get("date", {}).get("when", "") if isinstance(event.get("date"), dict) else "",
                    "start_date": event.get("date", {}).get("start_date", "") if isinstance(event.get("date"), dict) else "",
                    "address": event.get("address", []),
                    "venue": event.get("venue", {}).get("name", "") if isinstance(event.get("venue"), dict) else "",
                    "link": event.get("link", ""),
                    "thumbnail": event.get("thumbnail", ""),
                    "description": event.get("description", ""),
                    "ticket_info": event.get("ticket_info", [])
                })
            
            return {"query": query, "events": formatted}
        except Exception as e:
            return {"error": str(e), "query": query}
    
    # =========================================================================
    # GOOGLE SCHOLAR
    # =========================================================================
    
    def search_scholar(
        self, 
        query: str,
        hl: str = "en",
        num: int = 10
    ) -> Dict[str, Any]:
        """
        Search Google Scholar for academic papers.
        
        Args:
            query: Academic search query
            num: Number of results
            
        Returns:
            Dict with papers including titles, authors, citations, PDF links
        """
        params = {
            "engine": "google_scholar",
            "q": query,
            "hl": hl,
            "num": num
        }
        
        try:
            results = self._search(params)
            papers = results.get("organic_results", [])
            
            formatted = []
            for paper in papers[:num]:
                resources = paper.get("resources", [])
                pdf_link = ""
                for r in resources:
                    if r.get("file_format") == "PDF":
                        pdf_link = r.get("link", "")
                        break
                
                formatted.append({
                    "title": paper.get("title", ""),
                    "link": paper.get("link", ""),
                    "snippet": paper.get("snippet", ""),
                    "authors": paper.get("publication_info", {}).get("authors", []),
                    "summary": paper.get("publication_info", {}).get("summary", ""),
                    "cited_by": paper.get("inline_links", {}).get("cited_by", {}).get("total", 0),
                    "pdf_link": pdf_link,
                    "year": paper.get("publication_info", {}).get("summary", "").split(",")[0] if paper.get("publication_info", {}).get("summary") else ""
                })
            
            return {"query": query, "papers": formatted}
        except Exception as e:
            return {"error": str(e), "query": query}
    
    # =========================================================================
    # GOOGLE FINANCE
    # =========================================================================
    
    def get_stock_info(
        self, 
        ticker: str
    ) -> Dict[str, Any]:
        """
        Get stock/financial information.
        
        Args:
            ticker: Stock ticker (e.g., "GOOGL:NASDAQ", "AAPL:NASDAQ")
            
        Returns:
            Dict with stock price, change, market data
        """
        params = {
            "engine": "google_finance",
            "q": ticker
        }
        
        try:
            results = self._search(params)
            
            summary = results.get("summary", {})
            graph = results.get("graph", [])
            
            return {
                "ticker": ticker,
                "title": summary.get("title", ""),
                "stock": summary.get("stock", ""),
                "exchange": summary.get("exchange", ""),
                "price": summary.get("price", 0),
                "currency": summary.get("currency", "USD"),
                "price_change": summary.get("price_change", {}).get("amount", 0),
                "price_change_percentage": summary.get("price_change", {}).get("percentage", 0),
                "previous_close": summary.get("previous_close", 0),
                "market_cap": summary.get("market_cap", ""),
                "graph": graph[:20] if graph else []
            }
        except Exception as e:
            return {"error": str(e), "ticker": ticker}
    
    def get_market_trends(
        self, 
        trend: str = "indexes"
    ) -> Dict[str, Any]:
        """
        Get market trends and indices.
        
        Args:
            trend: Type of trend ("indexes", "most-active", "gainers", "losers")
            
        Returns:
            Dict with market data
        """
        params = {
            "engine": "google_finance_markets",
            "trend": trend
        }
        
        try:
            results = self._search(params)
            
            return {
                "trend": trend,
                "market_trends": results.get("market_trends", []),
                "market_trends_tab": results.get("market_trends_tab", [])
            }
        except Exception as e:
            return {"error": str(e), "trend": trend}
    
    # =========================================================================
    # GOOGLE FLIGHTS
    # =========================================================================
    
    def search_flights(
        self, 
        departure_id: str, 
        arrival_id: str,
        outbound_date: str,
        return_date: str = None,
        currency: str = "USD",
        adults: int = 1
    ) -> Dict[str, Any]:
        """
        Search Google Flights.
        
        Args:
            departure_id: Departure airport code (e.g., "JFK", "LAX")
            arrival_id: Arrival airport code
            outbound_date: Departure date (YYYY-MM-DD)
            return_date: Return date for round trip (optional)
            currency: Currency for prices
            adults: Number of adult passengers
            
        Returns:
            Dict with flight options, prices, airlines
        """
        params = {
            "engine": "google_flights",
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "outbound_date": outbound_date,
            "currency": currency,
            "adults": adults,
            "type": "1" if return_date else "2"  # 1 = round trip, 2 = one way
        }
        
        if return_date:
            params["return_date"] = return_date
        
        try:
            results = self._search(params)
            
            best_flights = results.get("best_flights", [])
            other_flights = results.get("other_flights", [])
            
            formatted_flights = []
            for flight in (best_flights + other_flights)[:10]:
                legs = flight.get("flights", [])
                formatted_flights.append({
                    "price": flight.get("price", 0),
                    "type": flight.get("type", ""),
                    "airline": flight.get("airline", legs[0].get("airline") if legs else ""),
                    "airline_logo": flight.get("airline_logo", ""),
                    "duration": flight.get("total_duration", 0),
                    "stops": len(legs) - 1 if legs else 0,
                    "departure_time": legs[0].get("departure_airport", {}).get("time", "") if legs else "",
                    "arrival_time": legs[-1].get("arrival_airport", {}).get("time", "") if legs else "",
                    "legs": legs
                })
            
            return {
                "departure": departure_id,
                "arrival": arrival_id,
                "date": outbound_date,
                "flights": formatted_flights,
                "price_insights": results.get("price_insights", {})
            }
        except Exception as e:
            return {"error": str(e), "departure": departure_id, "arrival": arrival_id}
    
    # =========================================================================
    # GOOGLE TRAVEL EXPLORE
    # =========================================================================
    
    def explore_destinations(
        self, 
        departure_id: str,
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Explore travel destinations from a departure city.
        
        Args:
            departure_id: Departure airport code
            currency: Currency for prices
            
        Returns:
            Dict with destination suggestions and prices
        """
        params = {
            "engine": "google_travel_explore",
            "departure_id": departure_id,
            "currency": currency,
            "type": "2"
        }
        
        try:
            results = self._search(params)
            destinations = results.get("destinations", [])
            
            formatted = []
            for dest in destinations[:20]:
                formatted.append({
                    "title": dest.get("title", ""),
                    "country": dest.get("country", ""),
                    "airport_code": dest.get("airports", [{}])[0].get("id", "") if dest.get("airports") else "",
                    "price": dest.get("price", 0),
                    "image": dest.get("image", ""),
                    "description": dest.get("description", "")
                })
            
            return {"departure": departure_id, "destinations": formatted}
        except Exception as e:
            return {"error": str(e), "departure": departure_id}
    
    # =========================================================================
    # GOOGLE MAPS REVIEWS
    # =========================================================================
    
    def get_place_reviews(
        self, 
        data_id: str,
        hl: str = "en"
    ) -> Dict[str, Any]:
        """
        Get reviews for a place from Google Maps.
        
        Args:
            data_id: Place data ID from local search results
            hl: Language
            
        Returns:
            Dict with reviews, ratings, user info
        """
        params = {
            "engine": "google_maps_reviews",
            "data_id": data_id,
            "hl": hl
        }
        
        try:
            results = self._search(params)
            reviews = results.get("reviews", [])
            
            formatted = []
            for review in reviews[:20]:
                formatted.append({
                    "user": review.get("user", {}).get("name", ""),
                    "rating": review.get("rating", 0),
                    "date": review.get("date", ""),
                    "snippet": review.get("snippet", ""),
                    "likes": review.get("likes", 0),
                    "user_link": review.get("user", {}).get("link", ""),
                    "user_thumbnail": review.get("user", {}).get("thumbnail", "")
                })
            
            return {
                "data_id": data_id,
                "reviews": formatted,
                "rating": results.get("place_info", {}).get("rating", 0),
                "total_reviews": results.get("place_info", {}).get("reviews", 0)
            }
        except Exception as e:
            return {"error": str(e), "data_id": data_id}


# ============================================================================
# CONVENIENCE FUNCTIONS (for backward compatibility)
# ============================================================================

_client = None

def get_serpapi_client() -> SerpAPIClient:
    """Get singleton SerpAPI client."""
    global _client
    if _client is None:
        _client = SerpAPIClient()
    return _client


def search_web(query: str, **kwargs) -> Dict:
    """Search Google Web."""
    return get_serpapi_client().search_web(query, **kwargs)

def search_images(query: str, **kwargs) -> Dict:
    """Search Google Images."""
    return get_serpapi_client().search_images(query, **kwargs)

def search_news(query: str, **kwargs) -> Dict:
    """Search Google News."""
    return get_serpapi_client().search_news(query, **kwargs)

def search_shopping(query: str, **kwargs) -> Dict:
    """Search Google Shopping."""
    return get_serpapi_client().search_shopping(query, **kwargs)

def search_amazon(query: str, **kwargs) -> Dict:
    """Search Amazon."""
    return get_serpapi_client().search_amazon(query, **kwargs)

def search_local(query: str, **kwargs) -> Dict:
    """Search Google Local/Places."""
    return get_serpapi_client().search_local(query, **kwargs)

def search_events(query: str, **kwargs) -> Dict:
    """Search Google Events."""
    return get_serpapi_client().search_events(query, **kwargs)

def search_scholar(query: str, **kwargs) -> Dict:
    """Search Google Scholar."""
    return get_serpapi_client().search_scholar(query, **kwargs)

def search_flights(departure: str, arrival: str, date: str, **kwargs) -> Dict:
    """Search Google Flights."""
    return get_serpapi_client().search_flights(departure, arrival, date, **kwargs)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import json
    
    print("🔍 Testing SerpAPI Tools...\n")
    
    client = SerpAPIClient()
    
    # Test 1: Web Search
    print("1️⃣ Testing Web Search...")
    result = client.search_web("best laptops 2024", num=3)
    if "error" not in result:
        print(f"   ✅ Found {len(result.get('organic_results', []))} web results")
    else:
        print(f"   ❌ Error: {result.get('error')}")
    
    # Test 2: Shopping
    print("\n2️⃣ Testing Shopping Search...")
    result = client.search_shopping("iPhone 15", location="Austin, Texas")
    if "error" not in result:
        print(f"   ✅ Found {len(result.get('products', []))} products")
        if result.get("products"):
            p = result["products"][0]
            print(f"   📦 First: {p.get('title', '')[:50]}... - {p.get('price', 'N/A')}")
    else:
        print(f"   ❌ Error: {result.get('error')}")
    
    # Test 3: Images
    print("\n3️⃣ Testing Image Search...")
    result = client.search_images("sunset beach", num=5)
    if "error" not in result:
        print(f"   ✅ Found {len(result.get('images', []))} images")
    else:
        print(f"   ❌ Error: {result.get('error')}")
    
    # Test 4: News
    print("\n4️⃣ Testing News Search...")
    result = client.search_news("technology")
    if "error" not in result:
        print(f"   ✅ Found {len(result.get('articles', []))} articles")
    else:
        print(f"   ❌ Error: {result.get('error')}")
    
    # Test 5: Local
    print("\n5️⃣ Testing Local Search...")
    result = client.search_local("coffee shops", location="Austin, Texas")
    if "error" not in result:
        print(f"   ✅ Found {len(result.get('places', []))} places")
    else:
        print(f"   ❌ Error: {result.get('error')}")
    
    print("\n✅ SerpAPI Tools Ready!")
