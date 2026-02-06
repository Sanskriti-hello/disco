"""
MCP Tool Descriptions for LLM Agent
====================================
This module provides comprehensive tool descriptions that the LLM agent uses
to understand what each MCP tool does, its inputs, outputs, and when to use it.

Updated to use SerpAPI-based tools which provide real, working data.
"""

TOOL_DESCRIPTIONS = {
    # =========================================================================
    # SERPAPI SEARCH TOOLS (serpapi_tools.py) - PRODUCTION READY
    # =========================================================================
    "SerpAPIClient.search_web": {
        "name": "Google Web Search",
        "description": "Search Google for web pages, articles, and information. Returns organic results with titles, URLs, and snippets.",
        "inputs": {
            "query": "str - Search query (e.g., 'best laptops 2024', 'python tutorials')",
            "location": "str - Location for localized results (default: 'United States')",
            "num": "int - Number of results (default: 10)",
            "hl": "str - Language code (default: 'en')",
            "gl": "str - Country code (default: 'us')"
        },
        "outputs": "Dict with organic_results, knowledge_graph, related_searches, answer_box, top_stories",
        "use_when": "Need to find general information, articles, documentation, or any web content"
    },
    
    "SerpAPIClient.search_images": {
        "name": "Google Image Search",
        "description": "Search Google Images. Returns high-quality image URLs, thumbnails, and sources.",
        "inputs": {
            "query": "str - What images to search for (e.g., 'sunset beach', 'modern architecture')",
            "location": "str - Location for results (default: 'United States')",
            "num": "int - Number of images (default: 20)"
        },
        "outputs": "Dict with images list containing {title, url, thumbnail, source, link, width, height}",
        "use_when": "Need to find images, photos, or visual content for any purpose"
    },
    
    "SerpAPIClient.search_news": {
        "name": "Google News Search",
        "description": "Search Google News for recent articles and headlines on any topic.",
        "inputs": {
            "query": "str - News search query (e.g., 'technology', 'climate change')",
            "hl": "str - Language code (default: 'en')",
            "gl": "str - Country code (default: 'us')"
        },
        "outputs": "Dict with articles list containing {title, link, source, date, snippet, thumbnail}",
        "use_when": "Need current news, headlines, or recent coverage of any topic"
    },
    
    "SerpAPIClient.search_shopping": {
        "name": "Google Shopping Search",
        "description": "Search Google Shopping for products with prices, ratings, and purchase links.",
        "inputs": {
            "query": "str - Product search query (e.g., 'iPhone 15', 'wireless headphones')",
            "location": "str - Location for pricing (default: 'United States')"
        },
        "outputs": "Dict with products list containing {title, price, link, source, rating, reviews, thumbnail, delivery}",
        "use_when": "Need to compare products and prices across multiple retailers"
    },
    
    "SerpAPIClient.search_amazon": {
        "name": "Amazon Product Search",
        "description": "Search Amazon directly for products with Prime status, ratings, and current prices.",
        "inputs": {
            "query": "str - Product search query",
            "domain": "str - Amazon domain (default: 'amazon.com')"
        },
        "outputs": "Dict with products list containing {asin, title, price, rating, reviews_count, link, thumbnail, is_prime, is_best_seller}",
        "use_when": "Need Amazon-specific product data including Prime eligibility and bestseller status"
    },
    
    "SerpAPIClient.search_local": {
        "name": "Google Local/Places Search",
        "description": "Search for local businesses and places (restaurants, hotels, services) with ratings and contact info.",
        "inputs": {
            "query": "str - Local search query (e.g., 'pizza near me', 'hotels in NYC')",
            "location": "str - Location context (e.g., 'Austin, Texas')",
            "hl": "str - Language code (default: 'en')",
            "gl": "str - Country code (default: 'us')"
        },
        "outputs": "Dict with places list containing {title, place_id, address, phone, rating, reviews, hours, website, gps_coordinates}",
        "use_when": "Need to find local businesses, restaurants, hotels, or services in a specific area"
    },
    
    "SerpAPIClient.search_events": {
        "name": "Google Events Search",
        "description": "Search for events (concerts, shows, festivals, activities) in a location.",
        "inputs": {
            "query": "str - Event search query (e.g., 'concerts in Austin', 'tech conferences 2024')",
            "hl": "str - Language code (default: 'en')"
        },
        "outputs": "Dict with events list containing {title, date, address, venue, link, thumbnail, description, ticket_info}",
        "use_when": "Need to find events, concerts, shows, or activities"
    },
    
    "SerpAPIClient.search_scholar": {
        "name": "Google Scholar Search",
        "description": "Search Google Scholar for academic papers, research articles, and citations.",
        "inputs": {
            "query": "str - Academic search query (e.g., 'machine learning', 'climate change research')",
            "hl": "str - Language code (default: 'en')",
            "num": "int - Number of results (default: 10)"
        },
        "outputs": "Dict with papers list containing {title, link, snippet, authors, summary, cited_by, pdf_link}",
        "use_when": "Need academic research papers, scholarly articles, or scientific publications"
    },
    
    "SerpAPIClient.search_flights": {
        "name": "Google Flights Search",
        "description": "Search for flights between airports with pricing and airline options.",
        "inputs": {
            "departure_id": "str - Departure airport code (e.g., 'JFK', 'LAX')",
            "arrival_id": "str - Arrival airport code",
            "outbound_date": "str - Departure date (YYYY-MM-DD)",
            "return_date": "str - Return date for round trip (optional)",
            "currency": "str - Currency for prices (default: 'USD')",
            "adults": "int - Number of passengers (default: 1)"
        },
        "outputs": "Dict with flights list containing {price, airline, duration, stops, departure_time, arrival_time}",
        "use_when": "Need to find flight prices and options between cities"
    },
    
    "SerpAPIClient.explore_destinations": {
        "name": "Google Travel Explore",
        "description": "Explore travel destinations from a departure city with suggested prices.",
        "inputs": {
            "departure_id": "str - Departure airport code",
            "currency": "str - Currency for prices (default: 'USD')"
        },
        "outputs": "Dict with destinations list containing {title, country, airport_code, price, image, description}",
        "use_when": "Need travel destination suggestions and inspiration"
    },
    
    "SerpAPIClient.get_stock_info": {
        "name": "Google Finance Stock",
        "description": "Get stock/financial information for a ticker symbol.",
        "inputs": {
            "ticker": "str - Stock ticker (e.g., 'GOOGL:NASDAQ', 'AAPL:NASDAQ')"
        },
        "outputs": "Dict with {ticker, title, price, currency, price_change, price_change_percentage, market_cap, graph}",
        "use_when": "Need stock prices, market data, or financial information"
    },
    
    "SerpAPIClient.get_market_trends": {
        "name": "Google Finance Markets",
        "description": "Get market trends and indices (gainers, losers, most active).",
        "inputs": {
            "trend": "str - Type: 'indexes', 'most-active', 'gainers', 'losers'"
        },
        "outputs": "Dict with market_trends data",
        "use_when": "Need market overview, trending stocks, or index data"
    },
    
    "SerpAPIClient.get_place_reviews": {
        "name": "Google Maps Reviews",
        "description": "Get customer reviews for a specific place from Google Maps.",
        "inputs": {
            "data_id": "str - Place data_id from local search results",
            "hl": "str - Language code (default: 'en')"
        },
        "outputs": "Dict with reviews list containing {user, rating, date, snippet, likes}",
        "use_when": "Need customer reviews and ratings for a specific business"
    },
    
    # =========================================================================
    # AMAZON TOOLS (amazon.py)
    # =========================================================================
    "AmazonClient.search_products": {
        "name": "Amazon Product Search",
        "description": "Search for products on Amazon. Returns product titles, prices, ratings, images, and ASINs.",
        "inputs": {
            "query": "str - Product search query (e.g., 'wireless headphones', 'laptop stand')",
            "country": "str - Country code e.g. 'US', 'IN', 'UK' (default: 'US')",
            "page": "int - Page number for pagination (default: 1)",
            "sort_by": "str - Sort option (optional)",
            "category_id": "str - Amazon category ID (optional)"
        },
        "outputs": "Dict with 'data' containing list of products with {asin, title, price, rating, image_url, url}",
        "use_when": "Need to find products, compare prices, or get product recommendations"
    },
    
    "AmazonClient.get_product_details": {
        "name": "Amazon Product Details",
        "description": "Get detailed information about a specific Amazon product using its ASIN.",
        "inputs": {
            "asin": "str - Amazon Standard Identification Number (product ID)",
            "country": "str - Country code (default: 'US')"
        },
        "outputs": "Dict with full product details including description, features, specs",
        "use_when": "Need detailed info about a specific Amazon product"
    },
    
    "AmazonClient.get_product_reviews": {
        "name": "Amazon Product Reviews",
        "description": "Get customer reviews for an Amazon product with filtering options.",
        "inputs": {
            "asin": "str - Amazon product ID",
            "country": "str - Country code",
            "sort_by": "SortBy - TOP_REVIEWS or MOST_RECENT",
            "star_rating": "StarRating - ALL, 5_STARS, 4_STARS, etc.",
            "verified_purchases_only": "bool - Filter to verified purchases"
        },
        "outputs": "Dict with list of reviews including text, rating, date, author",
        "use_when": "Need customer feedback, reviews, or ratings for a product"
    },
    
    "AmazonClient.get_product_offers": {
        "name": "Amazon Product Offers",
        "description": "Get available offers and deals for a product including different sellers and prices.",
        "inputs": {
            "asin": "str - Amazon product ID",
            "country": "str - Country code",
            "page": "int - Page number"
        },
        "outputs": "Dict with offers including prices, conditions, seller info",
        "use_when": "Need to compare prices from different sellers"
    },
    
    # =========================================================================
    # MOVIE/TV TOOLS (movie.py)
    # =========================================================================
    "MovieClient.search_by_title": {
        "name": "Movie/TV Search",
        "description": "Search for movies or TV shows by title. Includes streaming availability info.",
        "inputs": {
            "title": "str - Movie or show title to search for",
            "country": "str - Country code for streaming availability (default: 'us')",
            "show_type": "str - 'movie' or 'series'",
            "series_granularity": "str - 'show' or 'episode'"
        },
        "outputs": "Dict with matches including streaming platforms where available",
        "use_when": "Need to find movies/shows and where to stream them"
    },
    
    "MovieClient.search_by_filters": {
        "name": "Movie/TV Discovery",
        "description": "Discover movies or shows using filters like genre, rating, year.",
        "inputs": {
            "show_type": "str - 'movie' or 'series'",
            "country": "str - Country code",
            "genres": "List[str] - Genre IDs to filter by",
            "order_by": "str - Field to sort by",
            "order_direction": "str - 'asc' or 'desc'"
        },
        "outputs": "List of matching shows with streaming info",
        "use_when": "Want to discover content by genre, popularity, etc."
    },
    
    "MovieClient.get_show_details": {
        "name": "Movie/TV Details",
        "description": "Get detailed information about a specific movie or TV show.",
        "inputs": {
            "show_id": "str - Unique show ID from search results",
            "series_granularity": "str - 'show' or 'episode' level detail"
        },
        "outputs": "Dict with full show details, cast, streaming platforms",
        "use_when": "Need complete info about a specific movie/show"
    },
    
    "MovieClient.get_genres": {
        "name": "Movie/TV Genres",
        "description": "Get list of all available movie/TV genres and their IDs.",
        "inputs": {},
        "outputs": "Dict mapping genre names to IDs",
        "use_when": "Need genre IDs for filtered search"
    },
    
    # =========================================================================
    # SPOTIFY TOOLS (spotify.py)
    # =========================================================================
    "SpotifyClient.search": {
        "name": "Spotify Search",
        "description": "Search Spotify for tracks, artists, albums, playlists, podcasts.",
        "inputs": {
            "query": "str - Search query",
            "search_type": "str - 'multi', 'tracks', 'artists', 'albums', 'playlists', 'shows'",
            "offset": "int - Result offset for pagination",
            "limit": "int - Max results (default: 10)"
        },
        "outputs": "Dict with matching tracks, artists, albums etc.",
        "use_when": "Need to find music, artists, albums, or podcasts"
    },
    
    "SpotifyClient.get_tracks": {
        "name": "Spotify Track Details",
        "description": "Get detailed information about specific Spotify tracks.",
        "inputs": {
            "track_ids": "List[str] - Spotify track IDs"
        },
        "outputs": "Dict with track details including duration, popularity, preview URL",
        "use_when": "Need details about specific songs"
    },
    
    "SpotifyClient.get_track_lyrics": {
        "name": "Spotify Lyrics",
        "description": "Get lyrics for a specific Spotify track.",
        "inputs": {
            "track_id": "str - Spotify track ID"
        },
        "outputs": "Dict with synced lyrics if available",
        "use_when": "Need song lyrics"
    },
    
    "SpotifyClient.get_artists": {
        "name": "Spotify Artist Info",
        "description": "Get profile information for Spotify artists.",
        "inputs": {
            "artist_ids": "List[str] - Spotify artist IDs"
        },
        "outputs": "Dict with artist profiles, followers, genres",
        "use_when": "Need artist information and stats"
    },
    
    "SpotifyClient.get_artist_albums": {
        "name": "Spotify Artist Albums",
        "description": "Get all albums by a specific artist.",
        "inputs": {
            "artist_id": "str - Spotify artist ID",
            "offset": "int - Pagination offset",
            "limit": "int - Max results"
        },
        "outputs": "List of albums with release dates, track counts",
        "use_when": "Need an artist's discography"
    },
    
    "SpotifyClient.get_concerts": {
        "name": "Spotify Concerts",
        "description": "Get upcoming concerts and live events by location.",
        "inputs": {
            "location_code": "str - ISO country code (default: 'US')"
        },
        "outputs": "List of upcoming concerts with dates, venues, artists",
        "use_when": "Need to find live music events"
    },
    
    # =========================================================================
    # NEWS TOOLS (news.py)
    # =========================================================================
    "NewsClient.get_top_headlines": {
        "name": "Top News Headlines",
        "description": "Get top news headlines from various sources. Can filter by country and category.",
        "inputs": {
            "country": "str - Country code e.g. 'us', 'gb', 'in'",
            "category": "str - 'business', 'entertainment', 'health', 'science', 'sports', 'technology'"
        },
        "outputs": "List of news articles with titles, descriptions, sources, URLs",
        "use_when": "Need current news headlines"
    },
    
    "NewsClient.search_news": {
        "name": "News Search",
        "description": "Search for news articles by keyword across multiple sources.",
        "inputs": {
            "query": "str - Search query",
            "language": "str - Language code (default: 'en')",
            "sort_by": "str - 'relevancy', 'popularity', 'publishedAt'"
        },
        "outputs": "List of matching news articles",
        "use_when": "Need to find news on a specific topic"
    },
    
    # =========================================================================
    # ARXIV TOOLS (arxiv.py)
    # =========================================================================
    "ArxivClient.search_papers": {
        "name": "ArXiv Paper Search",
        "description": "Search for academic papers on arXiv by keyword, author, or category.",
        "inputs": {
            "query": "str - Search query (supports arXiv query syntax)",
            "max_results": "int - Number of papers to return",
            "sort_by": "str - 'relevance', 'lastUpdatedDate', 'submittedDate'"
        },
        "outputs": "List of papers with titles, abstracts, authors, PDF links",
        "use_when": "Need academic research papers"
    },
    
    # =========================================================================
    # SUMMARIZE TOOLS (summarize.py)
    # =========================================================================
    "summarize_text": {
        "name": "Text Summarizer",
        "description": "Summarize long text content into a concise summary using Gemini AI.",
        "inputs": {
            "text": "str - The text content to summarize"
        },
        "outputs": "str - Concise summary focusing on key concepts and results",
        "use_when": "Need to condense long articles, papers, or text content"
    },
    
    # =========================================================================
    # EXCHANGE RATE TOOLS (exchange_rate.py)
    # =========================================================================
    "ExchangeRateClient.get_rates": {
        "name": "Currency Exchange Rates",
        "description": "Get current exchange rates for currencies.",
        "inputs": {
            "base_currency": "str - Base currency code (e.g., 'USD', 'EUR')",
            "target_currencies": "List[str] - Target currency codes"
        },
        "outputs": "Dict with exchange rates",
        "use_when": "Need currency conversion rates"
    },
    
    "ExchangeRateClient.convert": {
        "name": "Currency Converter",
        "description": "Convert an amount from one currency to another.",
        "inputs": {
            "amount": "float - Amount to convert",
            "from_currency": "str - Source currency code",
            "to_currency": "str - Target currency code"
        },
        "outputs": "Dict with converted amount",
        "use_when": "Need to convert money between currencies"
    },
    
    # =========================================================================
    # LOCATION & WEATHER TOOLS (Loc_Weath_Dis.py)
    # =========================================================================
    "LocationWeatherMCP.search_places": {
        "name": "Place Search",
        "description": "Search for places using Nominatim/OpenStreetMap. Returns location data with coordinates, addresses, and nearby amenities.",
        "inputs": {
            "queries": "List[str] - List of place names or addresses to search"
        },
        "outputs": "Dict with place results including {name, address, lat, lon, map_url, nearby_amenities}",
        "use_when": "Need to find locations, addresses, or nearby places"
    },
    
    "LocationWeatherMCP.lookup_weather": {
        "name": "Weather Lookup",
        "description": "Get current weather conditions for a location using OpenWeatherMap API.",
        "inputs": {
            "lat": "float - Latitude coordinate",
            "lon": "float - Longitude coordinate"
        },
        "outputs": "Dict with weather data including temperature, conditions, humidity, wind",
        "use_when": "Need current weather information for a location"
    },
    
    "LocationWeatherMCP.compute_routes": {
        "name": "Route Calculator",
        "description": "Compute driving/walking routes between two locations using OSRM.",
        "inputs": {
            "origin": "str - Starting location (address or place name)",
            "destination": "str - Ending location (address or place name)"
        },
        "outputs": "Dict with route info including distance, duration, step-by-step directions, map_url",
        "use_when": "Need directions or travel time between locations"
    },
    
    # =========================================================================
    # GOOGLE WORKSPACE TOOLS (google_workspace.py)
    # =========================================================================
    "GoogleWorkspaceMCP.get_calendar_events": {
        "name": "Google Calendar Events",
        "description": "Get upcoming calendar events with free/busy time analysis.",
        "inputs": {
            "time_min": "str - Start time in ISO format (optional, defaults to now)",
            "time_max": "str - End time in ISO format (optional, defaults to 7 days)",
            "max_results": "int - Maximum events to return (default: 10)"
        },
        "outputs": "Dict with {events, busy_dates, free_ranges}",
        "use_when": "Need user's calendar events or availability"
    },
    
    "GoogleWorkspaceMCP.create_event": {
        "name": "Create Calendar Event",
        "description": "Create a new Google Calendar event.",
        "inputs": {
            "summary": "str - Event title",
            "start_time": "str - Start time in ISO format",
            "end_time": "str - End time in ISO format",
            "description": "str - Event description (optional)",
            "location": "str - Event location (optional)",
            "attendees": "List[str] - Email addresses of attendees (optional)"
        },
        "outputs": "Dict with {status, link, event_id}",
        "use_when": "Need to create/schedule a calendar event"
    },
    
    "GoogleWorkspaceMCP.search_drive": {
        "name": "Google Drive Search",
        "description": "Search for files in Google Drive by name or content.",
        "inputs": {
            "query": "str - Search query for file names",
            "limit": "int - Maximum results (default: 10)",
            "file_types": "List[str] - Filter by type: 'document', 'spreadsheet', 'presentation', 'pdf'"
        },
        "outputs": "List of files with {id, name, mimeType, webViewLink, modifiedTime}",
        "use_when": "Need to find or access Google Drive files"
    },
    
    "GoogleWorkspaceMCP.get_file_content": {
        "name": "Google Doc Content",
        "description": "Get the text content of a Google Doc.",
        "inputs": {
            "file_id": "str - Google Drive file ID"
        },
        "outputs": "str - Plain text content of the document",
        "use_when": "Need to read contents of a Google Doc"
    },
    
    "GoogleWorkspaceMCP.search_gmail": {
        "name": "Gmail Search",
        "description": "Search Gmail messages using Gmail search syntax.",
        "inputs": {
            "query": "str - Gmail search query (e.g., 'from:user@example.com', 'is:unread')",
            "max_results": "int - Maximum messages to return (default: 10)"
        },
        "outputs": "List of emails with {id, from, to, subject, date, snippet}",
        "use_when": "Need to search or retrieve emails"
    },
    
    # =========================================================================
    # FLASHCARD TOOLS (flashcard.py)
    # =========================================================================
    "FlashcardGenerator.generate_flashcards": {
        "name": "Flashcard Generator",
        "description": "Generate study flashcards from text content or a topic.",
        "inputs": {
            "content": "str - Text content to create flashcards from",
            "num_cards": "int - Number of flashcards to generate (default: 10)",
            "difficulty": "str - 'easy', 'medium', 'hard'"
        },
        "outputs": "List of flashcards with {question, answer, topic}",
        "use_when": "Need to create study flashcards from material"
    },
    
    # =========================================================================
    # QUIZ TOOLS (quiz.py)
    # =========================================================================
    "QuizGenerator.generate_quiz": {
        "name": "Quiz Generator",
        "description": "Generate quiz questions from text content or a topic.",
        "inputs": {
            "content": "str - Text content or topic to create quiz from",
            "num_questions": "int - Number of questions (default: 5)",
            "question_type": "str - 'multiple_choice', 'true_false', 'short_answer'"
        },
        "outputs": "List of quiz questions with {question, options, correct_answer, explanation}",
        "use_when": "Need to create practice quizzes or assessments"
    },
}


def get_tool_description(tool_name: str) -> dict:
    """Get description for a specific tool."""
    return TOOL_DESCRIPTIONS.get(tool_name, {})


def get_all_descriptions() -> dict:
    """Get all tool descriptions."""
    return TOOL_DESCRIPTIONS


def format_for_llm_prompt() -> str:
    """Format all tool descriptions as a string for LLM system prompts."""
    lines = ["# Available Tools\n"]
    
    for tool_id, info in TOOL_DESCRIPTIONS.items():
        lines.append(f"## {info.get('name', tool_id)}")
        lines.append(f"**Tool ID**: `{tool_id}`")
        lines.append(f"**Description**: {info.get('description', 'No description')}")
        
        if info.get('inputs'):
            lines.append("**Inputs**:")
            for param, desc in info['inputs'].items():
                lines.append(f"  - `{param}`: {desc}")
        
        lines.append(f"**Returns**: {info.get('outputs', 'Unknown')}")
        lines.append(f"**Use When**: {info.get('use_when', 'Unknown')}")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_for_llm_prompt())
