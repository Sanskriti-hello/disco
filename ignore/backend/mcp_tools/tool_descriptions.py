"""
MCP Tool Descriptions for LLM Agent
====================================
This module provides comprehensive tool descriptions that the LLM agent uses
to understand what each MCP tool does, its inputs, outputs, and when to use it.

The entertainment_builder.py discovers tools by scanning method docstrings.
This registry provides additional context and can be injected into prompts.
"""

TOOL_DESCRIPTIONS = {
    # =========================================================================
    # SEARCH TOOLS (search.py)
    # =========================================================================
    "SearchClient.search_brave_web": {
        "name": "Web Search (Brave)",
        "description": "Search the web for information using Brave Search engine. Returns titles, URLs, and snippets of matching web pages.",
        "inputs": {
            "query": "str - The search query (e.g., 'best restaurants in NYC', 'python tutorials')",
            "count": "int - Number of results to return (default: 10, max: 20)"
        },
        "outputs": "Dict with 'web' key containing list of {title, url, description} results",
        "use_when": "Need to find general information, articles, news, or any web content"
    },
    
    "SearchClient.search_brave_images": {
        "name": "Image Search (Brave)",
        "description": "Search for images using Brave Search. Returns image URLs, thumbnails, and source pages.",
        "inputs": {
            "query": "str - What images to search for (e.g., 'sunset beach', 'modern architecture')",
            "count": "int - Number of image results (default: 10)"
        },
        "outputs": "Dict with 'images' key containing list of {url, thumbnail, source_url, title} results",
        "use_when": "Need to find images, photos, graphics, or visual content"
    },
    
    "SearchClient.search_brave_videos": {
        "name": "Video Search (Brave)",
        "description": "Search for videos across the web. Returns video URLs, thumbnails, durations, and descriptions.",
        "inputs": {
            "query": "str - What videos to search for (e.g., 'cooking tutorial', 'music video')",
            "count": "int - Number of video results (default: 10)"
        },
        "outputs": "Dict with 'videos' key containing list of {url, thumbnail, title, duration, description} results",
        "use_when": "Need to find videos from YouTube, Vimeo, or other video platforms"
    },
    
    "SearchClient.search_images_realtime": {
        "name": "Real-Time Image Search",
        "description": "High-quality real-time image search with advanced filtering. Better quality than Brave image search.",
        "inputs": {
            "query": "str - Image search query",
            "limit": "int - Max results (default: 10)",
            "region": "str - Region code e.g. 'us', 'uk' (default: 'us')",
            "safe_search": "str - 'on' or 'off' (default: 'off')"
        },
        "outputs": "Dict with image results including high-resolution URLs",
        "use_when": "Need high-quality images with filtering options"
    },
    
    "SearchClient.search_tavily": {
        "name": "Web Search (Tavily)",
        "description": "AI-optimized web search using Tavily. Returns answers along with sources. Better for research queries.",
        "inputs": {
            "query": "str - The research query",
            "search_depth": "str - 'smart' or 'deep' (default: 'smart')"
        },
        "outputs": "Dict with 'answer' (AI summary) and 'results' (source URLs and content)",
        "use_when": "Need AI-summarized answers for research or factual queries"
    },
    
    # =========================================================================
    # YOUTUBE TOOLS (youtube.py)
    # =========================================================================
    "YouTubeMCP.search_videos": {
        "name": "YouTube Video Search",
        "description": "Search for YouTube videos by keyword. Returns video IDs, titles, thumbnails, view counts, and channel info.",
        "inputs": {
            "query": "str - Search query for videos",
            "max_results": "int - Number of results (1-50, default: 10)",
            "order": "str - Sort order: 'relevance', 'date', 'viewCount', 'rating'",
            "published_after": "str - ISO 8601 date to filter recent videos (optional)"
        },
        "outputs": "List of dicts with {video_id, title, description, thumbnail, channel, view_count, published_at}",
        "use_when": "Need to find YouTube videos on a topic"
    },
    
    "YouTubeMCP.get_video_details": {
        "name": "YouTube Video Details",
        "description": "Get detailed information about specific YouTube videos including stats, descriptions, and metadata.",
        "inputs": {
            "video_ids": "List[str] - List of YouTube video IDs to get details for"
        },
        "outputs": "List of video detail objects with full metadata",
        "use_when": "Need detailed info about specific YouTube videos"
    },
    
    "YouTubeMCP.get_trending_videos": {
        "name": "YouTube Trending",
        "description": "Get currently trending videos on YouTube for a specific region.",
        "inputs": {
            "region_code": "str - Country code e.g. 'US', 'IN', 'GB' (default: 'US')",
            "max_results": "int - Number of trending videos (default: 10)"
        },
        "outputs": "List of trending video objects",
        "use_when": "Need to show popular/trending content on YouTube"
    },
    
    "YouTubeMCP.get_watch_history": {
        "name": "YouTube Watch History",
        "description": "Get user's personal YouTube watch history. Requires OAuth authentication.",
        "inputs": {
            "max_results": "int - Number of history items (1-50, default: 50)",
            "published_after": "str - ISO 8601 date filter (optional)"
        },
        "outputs": "List of watched videos with timestamps",
        "use_when": "Need user's personal watch history (requires OAuth)"
    },
    
    "YouTubeMCP.get_liked_videos": {
        "name": "YouTube Liked Videos",
        "description": "Get videos the user has liked on YouTube. Requires OAuth.",
        "inputs": {
            "max_results": "int - Number of liked videos (default: 50)"
        },
        "outputs": "List of liked videos",
        "use_when": "Need user's liked/favorite YouTube content"
    },
    
    "YouTubeMCP.get_subscriptions": {
        "name": "YouTube Subscriptions",
        "description": "Get channels the user is subscribed to. Requires OAuth.",
        "inputs": {
            "max_results": "int - Number of subscriptions (default: 50)"
        },
        "outputs": "List of subscribed channels",
        "use_when": "Need user's YouTube channel subscriptions"
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
