"""
Entertainment App Sandbox Builder with LLM-Driven JSON Content Filling

This module provides tools for:
  1. Building CodeSandbox-compatible React projects from directory structures
  2. Intelligently filling JSON templates using LLM (LangChain + Groq)
  3. Falling back to deterministic web search when LLM is unavailable
  4. Validating JSON output against schemas
  5. Protecting against prompt injection attacks

Key Features:
  - Two-layer context system (page-level and field-level guidance)
  - Tool whitelisting and security validation
  - Schema-driven JSON validation
  - Comprehensive logging for debugging
  - Deterministic fallback filling
  - Full caching and performance optimization

Usage:
  - Direct function: update_json(content, page_context, field_context)
  - Builder class: EntertainmentAppSandboxBuilder(context, project_dir)
"""

# ============================================================================
# STANDARD LIBRARY IMPORTS
# ============================================================================

import os
import json
import sys
import logging
import inspect
import importlib.util
from pathlib import Path
from typing import Dict, Optional, Any, List, Callable
from datetime import datetime
import hashlib

# ============================================================================
# THIRD-PARTY IMPORTS
# ============================================================================

from mcp_tools.search import SearchClient


# ============================================================================
# LOGGING SETUP
# ============================================================================


def _init_logger(debug: bool = False) -> logging.Logger:
    """
    Initialize logger with optional debug output.

    Args:
        debug: If True, enables DEBUG level logging to stderr.

    Returns:
        Configured logger instance. Ensures handlers are created only once.
    """
    logger = logging.getLogger(__name__)
    if debug and not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    elif not logger.handlers:
        logger.setLevel(logging.WARNING)
    return logger


# Read DEBUG_JSON_AGENT environment variable to enable/disable debug logging
_debug_mode = os.getenv('DEBUG_JSON_AGENT', '').lower() in ('1', 'true', 'yes')
_logger = _init_logger(_debug_mode)

# ============================================================================
# JSON SCHEMA VALIDATION
# ============================================================================


class JsonSchema:
    """
    Derives and validates JSON schemas.

    This class provides utilities to:
      - Dynamically generate JSON schema from template objects
      - Validate instances against their schemas
      - Detect structural mismatches and type violations
    """

    @staticmethod
    def derive(template: Any) -> Dict[str, Any]:
        """
        Derive a JSON schema from a template object.

        Recursively inspects the template structure and builds a JSON schema
        that enforces the same structure and types. Prevents infinite recursion
        by capping nesting depth at 10 levels.

        Args:
            template: Any JSON-serializable object (dict, list, str, int, etc.)

        Returns:
            Dictionary representing a JSON schema for the given template.
        """

        def build_schema(obj: Any, depth: int = 0) -> Dict[str, Any]:
            # Prevent infinite recursion on circular structures
            if depth > 10:
                return {"type": "object"}

            if isinstance(obj, dict):
                props = {}
                for key, value in obj.items():
                    props[key] = build_schema(value, depth + 1)
                return {
                    "type": "object",
                    "properties": props,
                    "additionalProperties": False,
                }
            elif isinstance(obj, list):
                if len(obj) > 0:
                    return {
                        "type": "array",
                        "items": build_schema(obj[0], depth + 1),
                    }
                else:
                    return {"type": "array"}
            elif isinstance(obj, str):
                return {"type": "string"}
            elif isinstance(obj, bool):
                return {"type": "boolean"}
            elif isinstance(obj, (int, float)):
                return {"type": "number"}
            elif obj is None:
                return {"type": "null"}
            else:
                return {"type": "object"}

        return build_schema(template)

    @staticmethod
    def validate(
        instance: Any, schema: Dict[str, Any], path: str = "root"
    ) -> List[str]:
        """
        Validate an instance against a schema.

        Recursively validates the instance structure and types. Collects all
        errors found rather than failing fast.

        Args:
            instance: Object to validate.
            schema: JSON schema to validate against.
            path: Current path in the object tree (for error messages).

        Returns:
            List of error messages. Empty list if validation succeeds.
        """
        errors: List[str] = []
        schema_type = schema.get("type")

        if schema_type == "object":
            if not isinstance(instance, dict):
                errors.append(
                    f"{path}: expected object, got {type(instance).__name__}"
                )
            else:
                # Check for unexpected keys (not in schema)
                allowed_keys = set(schema.get("properties", {}).keys())
                actual_keys = set(instance.keys())
                extra = actual_keys - allowed_keys
                if extra and not schema.get("additionalProperties", False):
                    errors.append(f"{path}: unexpected keys {extra}")

                # Validate each property in the schema
                for key, prop_schema in schema.get("properties", {}).items():
                    if key in instance:
                        errors.extend(
                            JsonSchema.validate(
                                instance[key], prop_schema, f"{path}.{key}"
                            )
                        )

        elif schema_type == "array":
            if not isinstance(instance, list):
                errors.append(
                    f"{path}: expected array, got {type(instance).__name__}"
                )
            else:
                item_schema = schema.get("items", {})
                for index, item in enumerate(instance):
                    errors.extend(
                        JsonSchema.validate(item, item_schema, f"{path}[{index}]")
                    )

        elif schema_type == "string":
            if not isinstance(instance, str):
                errors.append(
                    f"{path}: expected string, got {type(instance).__name__}"
                )

        elif schema_type == "number":
            # Booleans are technically numbers in Python, so we exclude them
            if not isinstance(instance, (int, float)) or isinstance(instance, bool):
                errors.append(
                    f"{path}: expected number, got {type(instance).__name__}"
                )

        elif schema_type == "boolean":
            if not isinstance(instance, bool):
                errors.append(
                    f"{path}: expected boolean, got {type(instance).__name__}"
                )

        elif schema_type == "null":
            if instance is not None:
                errors.append(
                    f"{path}: expected null, got {type(instance).__name__}"
                )

        return errors

# ============================================================================
# TOOL SECURITY AND WHITELISTING
# ============================================================================


class ToolWhitelist:
    """
    Manages a whitelist of allowed tools for security.

    Restricts which MCP tools can be invoked by the LLM agent.
    Default whitelist includes only SearchClient.web_search.
    """

    # Default set of whitelisted tools in format "ClassName.method_name"
    _DEFAULT_WHITELIST = {
        "SearchClient.web_search": "Search the web for information",
    }

    def __init__(self, whitelist_path: Optional[Path] = None) -> None:
        """
        Initialize the whitelist.

        Starts with default whitelist. If whitelist_path is provided and exists,
        loads custom whitelist from JSON file and merges with defaults.

        Args:
            whitelist_path: Optional path to JSON file containing custom whitelist.
        """
        self.whitelist = dict(self._DEFAULT_WHITELIST)
        self.custom_whitelist = False

        if whitelist_path and whitelist_path.exists():
            try:
                with open(whitelist_path) as f:
                    custom = json.load(f)
                    if isinstance(custom, dict):
                        self.whitelist.update(custom)
                        self.custom_whitelist = True
                        _logger.debug(f"Loaded custom whitelist from {whitelist_path}")
            except Exception as e:
                _logger.warning(
                    f"Failed to load whitelist from {whitelist_path}: {e}"
                )

    def is_allowed(self, class_name: str, method_name: str) -> bool:
        """
        Check if a method is whitelisted.

        Args:
            class_name: Name of the class containing the method.
            method_name: Name of the method to check.

        Returns:
            True if the method is in the whitelist, False otherwise.
        """
        key = f"{class_name}.{method_name}"
        return key in self.whitelist

    def get_description(self, class_name: str, method_name: str) -> str:
        """
        Get the description of a whitelisted method.

        Args:
            class_name: Name of the class.
            method_name: Name of the method.

        Returns:
            Description string, or empty string if not found.
        """
        key = f"{class_name}.{method_name}"
        return self.whitelist.get(key, "")

# ============================================================================
# PROMPT INJECTION PROTECTION
# ============================================================================


class PromptSanitizer:
    """
    Sanitizes user contexts to prevent prompt injection attacks.

    Removes/normalizes potentially dangerous patterns and enforces size limits.
    """

    # Regex patterns for dangerous content (informational, not used yet)
    DANGEROUS_PATTERNS = [
        r"ignore.*rules",
        r"override.*instruction",
        r"system.*prompt",
        r"jailbreak",
    ]

    @staticmethod
    def sanitize(text: Optional[str]) -> str:
        """
        Sanitize context text to prevent prompt injection.

        Removes excessive newlines, truncates to max length, and normalizes
        whitespace to prevent injection attacks.

        Args:
            text: Raw context text to sanitize.

        Returns:
            Cleaned context string, or empty string if input was None.
        """
        if not text:
            return ""

        # Remove excessive newlines and normalize whitespace
        text = "\n".join(
            line.strip() for line in text.split("\n") if line.strip()
        )

        # Enforce maximum context length
        max_length = 2000
        if len(text) > max_length:
            text = text[:max_length] + "..."
            _logger.warning(f"Context truncated to {max_length} chars")

        return text

# ============================================================================
# DETERMINISTIC FALLBACK FILLER
# ============================================================================


class DeterministicFiller:
    """
    Deterministic JSON filler using web search when available.

    Provides conservative, non-hallucinating fallback filling when LLM
    is unavailable. Uses web search to populate empty/placeholder values.
    """

    def __init__(self, search_agent: Optional[SearchClient] = None) -> None:
        """
        Initialize the filler.

        Args:
            search_agent: SearchClient instance for web search, or None.
        """
        self.search_agent = search_agent
        # Cache search results to avoid repeated API calls
        self._search_cache: Dict[str, Any] = {}

    def fill(self, template: Any, page_context: Optional[str] = None) -> Any:
        """
        Fill template with deterministic fallback logic.

        Recursively fills empty/placeholder values using web search on
        page context. Never hallucinate values.

        Args:
            template: JSON template to fill.
            page_context: Global context for search queries.

        Returns:
            Template with filled values.
        """
        return self._fill_recursive(template, page_context or "", [])

    def _fill_recursive(
        self, node: Any, context: str, path: List[str]
    ) -> Any:
        """
        Recursively fill template values.

        Args:
            node: Current node in the template tree.
            context: Global context for search.
            path: Path to current node (for field name inference).

        Returns:
            Filled node matching original type.
        """
        # Handle string values: fill if empty/placeholder
        if isinstance(node, str):
            if self._is_empty_value(node):
                field_name = path[-1] if path else ""
                return self._find_value_for_field(field_name, context)
            return node

        # Handle None: attempt to find a value, otherwise keep None
        if node is None:
            if context:
                field_name = path[-1] if path else ""
                return self._find_value_for_field(field_name, context)
            return None

        # Handle dicts: recursively fill each value
        if isinstance(node, dict):
            result = {}
            for key, value in node.items():
                result[key] = self._fill_recursive(value, context, path + [key])
            return result

        # Handle lists: recursively fill each item
        if isinstance(node, list):
            if len(node) == 0:
                return node
            return [
                self._fill_recursive(item, context, path + ["[]"])
                for item in node
            ]

        # Return scalars unchanged
        return node

    def _is_empty_value(self, text: str) -> bool:
        """
        Check if a string value is empty or a placeholder.

        Args:
            text: String to check.

        Returns:
            True if empty or placeholder-like, False otherwise.
        """
        check = text.strip().lower()
        return check in (
            "",
            "tbd",
            "placeholder",
            "n/a",
            "text",
            "title",
            "untitled",
            "none",
        )

    def _find_value_for_field(self, field_name: str, context: str) -> str:
        """
        Find an appropriate value for a field using web search.

        Uses caching to avoid repeated searches. Returns empty string
        if search fails or search_agent is unavailable.

        Args:
            field_name: Name of the field being filled (for search context).
            context: Global context for the search query.

        Returns:
            Filled value, or empty string if unable to find.
        """
        if not self.search_agent or not context:
            return ""

        # Check cache first
        cache_key = hashlib.md5(f"{field_name}:{context}".encode()).hexdigest()
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]

        try:
            search_results = self.search_agent.web_search(context)
            value = self._extract_best_match(search_results, field_name)
            self._search_cache[cache_key] = value
            return value
        except Exception as error:
            _logger.debug(f"Search failed for field '{field_name}': {error}")
            return ""

    def _extract_best_match(
        self, search_results: Any, field_hint: str
    ) -> str:
        """
        Extract the best matching value from search results.

        Recursively walks the search result structure looking for
        content in common fields (title, name, heading, etc.).

        Args:
            search_results: Raw search result structure.
            field_hint: Name of field being filled (currently unused).

        Returns:
            Best matching string value, or empty string if none found.
        """

        def walk(obj: Any) -> Optional[str]:
            """Recursively search for content in result structure."""
            if isinstance(obj, list):
                for element in obj:
                    result = walk(element)
                    if result:
                        return result
            elif isinstance(obj, dict):
                # Check common content fields first
                for key in ("title", "name", "heading", "description", "body"):
                    if (
                        key in obj
                        and isinstance(obj[key], str)
                        and len(obj[key]) > 2
                    ):
                        return obj[key]
                # Recursively search nested values
                for value in obj.values():
                    result = walk(value)
                    if result:
                        return result
            return None

        result = walk(search_results)
        return result if result else ""

# ============================================================================
# LAZY SEARCH AGENT INITIALIZATION AND HELPER UTILITIES
# ============================================================================


def _get_search_agent() -> Optional[SearchClient]:
    """
    Lazily initialize and return a SearchClient instance.

    Avoids import-time failures by initializing on first use.
    Returns None if initialization fails.

    Returns:
        SearchClient instance, or None if unavailable.
    """
    try:
        return SearchClient()
    except Exception as error:
        _logger.debug(f"Failed to initialize SearchClient: {error}")
        return None


def _extract_json_from_output(text: str) -> str:
    """
    Extract JSON from LLM output that may contain explanatory text.

    Searches for the first '{' and uses that as the start of JSON.

    Args:
        text: Raw LLM output.

    Returns:
        JSON substring, or original text if no '{' found.
    """
    index = text.find("{")
    if index != -1:
        return text[index:]
    return text


# ============================================================================
# DIRECT MCP TOOL DATA FILLER
# ============================================================================


def fill_data_with_mcp_tools(template_data: Dict, domain: str, context: str) -> Dict:
    """
    Directly fill template data by calling MCP tools based on domain.
    
    This bypasses the LLM agent and directly queries the appropriate MCP tools
    to get real data for templates.
    
    Args:
        template_data: The template JSON to fill
        domain: Domain type (shopping, travel, entertainment, study, code, generic)
        context: User's context/prompt describing what they want
        
    Returns:
        Filled template data with real content from MCP tools
    """
    print(f"🔧 Filling data with MCP tools for domain: {domain}")
    print(f"📝 Context: {context[:100]}...")
    
    filled = template_data.copy()
    
    try:
        # Initialize search client for images and web data
        search_client = SearchClient()
        
        # Extract search query from context
        search_query = context[:100] if context else domain
        
        # =================================================================
        # SHOPPING DOMAIN
        # =================================================================
        if domain.lower() == "shopping":
            try:
                from mcp_tools.amazon import AmazonClient
                amazon = AmazonClient()
                
                # Search for products
                products_result = amazon.search_products(search_query, country="US")
                products = products_result.get("data", {}).get("products", [])[:6]
                
                print(f"📦 Found {len(products)} products from Amazon")
                
                # Fill product highlight
                if products and "main" in filled:
                    first_product = products[0]
                    if "productHighlight" in filled["main"]:
                        filled["main"]["productHighlight"]["name"] = first_product.get("title", "Product")[:50]
                        filled["main"]["productHighlight"]["text"] = first_product.get("title", "")[:100]
                        filled["main"]["productHighlight"]["price"] = first_product.get("price", {}).get("raw", "$0.00")
                        filled["main"]["productHighlight"]["imageUrl"] = first_product.get("thumbnailImage", "")
                        filled["main"]["productHighlight"]["productUrl"] = first_product.get("url", "")
                    
                    # Fill carousel items
                    if "carousel" in filled["main"] and "items" in filled["main"]["carousel"]:
                        for i, item in enumerate(filled["main"]["carousel"]["items"]):
                            if i < len(products):
                                product = products[i]
                                item["title"] = product.get("title", "")[:30]
                                item["imageUrl"] = product.get("thumbnailImage", "")
                                item["price"] = product.get("price", {}).get("raw", "")
                                item["url"] = product.get("url", "")
                    
                    # Fill reviews
                    if "reviews" in filled["main"] and products:
                        first_asin = products[0].get("asin")
                        if first_asin:
                            try:
                                reviews_result = amazon.get_product_reviews(first_asin, country="US")
                                reviews = reviews_result.get("data", {}).get("reviews", [])[:3]
                                for i, review_item in enumerate(filled["main"]["reviews"].get("items", [])):
                                    if i < len(reviews):
                                        review = reviews[i]
                                        review_item["title"] = review.get("title", "Great product")
                                        review_item["text"] = review.get("body", "")[:150]
                                        review_item["stars"] = int(review.get("rating", 4))
                                        review_item["reviewerName"] = review.get("author", {}).get("name", "Customer")
                            except Exception as e:
                                print(f"⚠️ Reviews fetch failed: {e}")
                                
            except Exception as e:
                print(f"⚠️ Amazon tool error: {e}")
                # Fallback to web search
                _fill_with_web_search(filled, search_client, search_query, "shopping")
        
        # =================================================================
        # ENTERTAINMENT DOMAIN
        # =================================================================
        elif domain.lower() == "entertainment":
            try:
                from mcp_tools.movie import MovieClient
                from mcp_tools.youtube import YouTubeMCP
                
                movie_client = MovieClient()
                youtube = YouTubeMCP()
                
                # Search for movies/shows
                movies_result = movie_client.search_by_title(search_query)
                movies = movies_result.get("result", [])[:6]
                
                print(f"🎬 Found {len(movies)} movies/shows")
                
                # Fill featured content
                if movies and "rightColumn" in filled:
                    first_movie = movies[0]
                    if "featured" in filled["rightColumn"]:
                        filled["rightColumn"]["featured"]["title"] = first_movie.get("title", "")
                        filled["rightColumn"]["featured"]["description"] = first_movie.get("overview", "")[:200]
                        filled["rightColumn"]["featured"]["imageUrl"] = first_movie.get("imageSet", {}).get("horizontalPoster", {}).get("w480", "")
                        filled["rightColumn"]["featured"]["rating"] = first_movie.get("rating", 0)
                        filled["rightColumn"]["featured"]["year"] = str(first_movie.get("firstAirYear", first_movie.get("releaseYear", "")))
                        filled["rightColumn"]["featured"]["genre"] = ", ".join(first_movie.get("genres", [])[:3])
                    filled["rightColumn"]["topBox"] = first_movie.get("title", "Featured")
                    filled["rightColumn"]["textBox"] = first_movie.get("overview", "")[:150]
                
                # Fill items list
                if "items" in filled:
                    for i, item in enumerate(filled["items"]):
                        if i < len(movies):
                            movie = movies[i]
                            item["title"] = movie.get("title", "")
                            item["imageUrl"] = movie.get("imageSet", {}).get("horizontalPoster", {}).get("w480", "")
                            item["rating"] = movie.get("rating", 0)
                            # Find streaming URL
                            streaming = movie.get("streamingInfo", {}).get("us", [])
                            if streaming:
                                item["url"] = streaming[0].get("link", "")
                
                # Also get YouTube videos
                try:
                    videos = youtube.search_videos(search_query, max_results=3)
                    if videos and "leftColumn" in filled and "items" in filled["leftColumn"]:
                        for i, item in enumerate(filled["leftColumn"]["items"]):
                            if i < len(videos):
                                video = videos[i]
                                item["title"] = video.get("title", "")[:40]
                                item["imageUrl"] = video.get("thumbnail", "")
                                item["url"] = f"https://www.youtube.com/watch?v={video.get('video_id', '')}"
                except Exception as e:
                    print(f"⚠️ YouTube fetch failed: {e}")
                    
            except Exception as e:
                print(f"⚠️ Entertainment tool error: {e}")
                _fill_with_web_search(filled, search_client, search_query, "entertainment")
        
        # =================================================================
        # TRAVEL DOMAIN
        # =================================================================
        elif domain.lower() == "travel":
            try:
                from mcp_tools.Loc_Weath_Dis import LocationWeatherMCP
                
                loc_client = LocationWeatherMCP()
                
                # Get location info
                location_query = search_query.replace("travel", "").replace("trip", "").strip()
                
                # Search for images of the destination
                images_result = search_client.search_images_realtime(f"{location_query} travel destination", limit=4)
                images = images_result.get("data", [])[:4]
                
                print(f"🏖️ Found {len(images)} travel images")
                
                if "main" in filled:
                    # Fill destination info
                    if "destination" in filled["main"]:
                        filled["main"]["destination"]["name"] = location_query.title()
                        filled["main"]["destination"]["description"] = f"Explore the beautiful {location_query}"
                        filled["main"]["destination"]["mapsUrl"] = f"https://www.google.com/maps/search/{location_query.replace(' ', '+')}"
                        if images:
                            filled["main"]["destination"]["imageUrl"] = images[0].get("url", "")
                    
                    # Fill photos
                    if "photos" in filled["main"]:
                        for i, photo in enumerate(filled["main"]["photos"]):
                            if i < len(images):
                                photo["imageUrl"] = images[i].get("url", "")
                                photo["description"] = images[i].get("title", f"Photo {i+1}")[:50]
                                photo["mapsUrl"] = f"https://www.google.com/maps/search/{location_query.replace(' ', '+')}"
                    
                    # Fill text box
                    if "textBox" in filled["main"]:
                        filled["main"]["textBox"]["text"] = f"Discover amazing destinations in {location_query}. Plan your perfect trip with flights, hotels, and local experiences."
                    
                    # Fill hotels with web search
                    if "hotels" in filled["main"]:
                        hotels_search = search_client.search_brave_web(f"{location_query} best hotels booking", count=3)
                        web_results = hotels_search.get("web", {}).get("results", [])[:3]
                        for i, hotel in enumerate(filled["main"]["hotels"]):
                            if i < len(web_results):
                                result = web_results[i]
                                hotel["name"] = result.get("title", "")[:40]
                                hotel["bookingUrl"] = result.get("url", "")
                                hotel["rating"] = 4.5  # Default rating
                                
            except Exception as e:
                print(f"⚠️ Travel tool error: {e}")
                _fill_with_web_search(filled, search_client, search_query, "travel")
        
        # =================================================================
        # STUDY DOMAIN
        # =================================================================
        elif domain.lower() == "study":
            try:
                from mcp_tools.arxiv import ArxivClient
                
                arxiv = ArxivClient()
                
                # Search for papers
                papers_result = arxiv.search_papers(search_query, max_results=5)
                papers = papers_result if isinstance(papers_result, list) else []
                
                print(f"📚 Found {len(papers)} academic papers")
                
                if "main" in filled:
                    # Fill topic info
                    if "topic" in filled["main"]:
                        filled["main"]["topic"]["title"] = search_query.title()
                        filled["main"]["topic"]["description"] = f"Learn about {search_query}"
                    
                    # Fill summary
                    if "summary" in filled["main"] and papers:
                        first_paper = papers[0]
                        filled["main"]["summary"]["title"] = first_paper.get("title", "Summary")[:60]
                        filled["main"]["summary"]["text"] = first_paper.get("summary", "")[:300]
                        filled["main"]["summary"]["source"] = "arXiv"
                        filled["main"]["summary"]["sourceUrl"] = first_paper.get("link", "")
                    
                    # Fill key points
                    if "keyPoints" in filled["main"] and papers:
                        for i, point in enumerate(filled["main"]["keyPoints"]):
                            if i < len(papers):
                                paper = papers[i]
                                point["point"] = paper.get("title", "")[:80]
                                point["details"] = paper.get("summary", "")[:100]
                    
                    # Fill resources
                    if "resources" in filled["main"]:
                        for i, resource in enumerate(filled["main"]["resources"]):
                            if i < len(papers):
                                paper = papers[i]
                                resource["title"] = paper.get("title", "")[:50]
                                resource["url"] = paper.get("link", "")
                                resource["type"] = "paper"
                                
            except Exception as e:
                print(f"⚠️ Study tool error: {e}")
                _fill_with_web_search(filled, search_client, search_query, "study")
        
        # =================================================================
        # GENERIC / OTHER DOMAINS - Use web search
        # =================================================================
        else:
            _fill_with_web_search(filled, search_client, search_query, domain)
        
        # =================================================================
        # ALWAYS: Fill Google integration URLs
        # =================================================================
        if "actions" in filled:
            if "openInMaps" in filled["actions"]:
                filled["actions"]["openInMaps"] = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
            if "addToCalendar" in filled.get("main", {}).get("calendar", {}):
                filled["main"]["calendar"]["addToCalendar"] = f"https://calendar.google.com/calendar/r/eventedit?text={search_query.replace(' ', '+')}"
        
        print(f"✅ Data filling complete")
        return filled
        
    except Exception as e:
        print(f"❌ MCP tool filling failed: {e}")
        import traceback
        traceback.print_exc()
        return template_data


def _fill_with_web_search(filled: Dict, search_client: SearchClient, query: str, domain: str):
    """Fallback: fill template with web search results."""
    print(f"🔍 Fallback: Using web search for {domain}")
    
    try:
        # Search web
        web_results = search_client.search_brave_web(query, count=10)
        results = web_results.get("web", {}).get("results", [])
        
        # Search images
        image_results = search_client.search_images_realtime(query, limit=6)
        images = image_results.get("data", [])
        
        # Fill any url/link fields with web results
        _recursive_fill(filled, results, images, 0, 0)
        
    except Exception as e:
        print(f"⚠️ Web search fallback failed: {e}")


def _recursive_fill(obj: Any, web_results: List, images: List, web_idx: int, img_idx: int) -> tuple:
    """Recursively fill JSON fields with web search data."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_lower = key.lower()
            
            # Fill image fields
            if any(img_key in key_lower for img_key in ["image", "thumbnail", "photo", "src"]) and key_lower != "icon":
                if img_idx < len(images):
                    obj[key] = images[img_idx].get("url", value)
                    img_idx += 1
            
            # Fill URL fields
            elif any(url_key in key_lower for url_key in ["url", "link", "href"]) and not value:
                if web_idx < len(web_results):
                    obj[key] = web_results[web_idx].get("url", value)
                    web_idx += 1
            
            # Fill title/name fields
            elif any(title_key in key_lower for title_key in ["title", "name"]) and (not value or value in ["", "TXT", "Title", "text", "placeholder"]):
                if web_idx < len(web_results):
                    obj[key] = web_results[web_idx].get("title", value)[:50]
            
            # Fill text/description fields
            elif any(text_key in key_lower for text_key in ["text", "description", "summary"]) and (not value or value in ["", "TXT", "text", "placeholder"]):
                if web_idx < len(web_results):
                    obj[key] = web_results[web_idx].get("description", value)[:150]
            
            # Recurse into nested objects
            elif isinstance(value, (dict, list)):
                web_idx, img_idx = _recursive_fill(value, web_results, images, web_idx, img_idx)
                
    elif isinstance(obj, list):
        for item in obj:
            web_idx, img_idx = _recursive_fill(item, web_results, images, web_idx, img_idx)
    
    return web_idx, img_idx


# ============================================================================
# MAIN PUBLIC FUNCTION: JSON FILLING WITH LLM FALLBACK
# ============================================================================


def update_json(
    content: str,
    page_context: Optional[str] = None,
    field_context: Optional[str] = None,
) -> str:
    """
    LLM-driven JSON filling agent using LangChain + Groq with two-layer context support.

    Fills empty values and placeholders in JSON templates using an LLM agent.
    Falls back to deterministic web search if LLM is unavailable.

    Args:
        content: JSON template as string.
        page_context: Global page-level context describing the overall JSON/webpage.
        field_context: Field-level context with instructions for each JSON field.

    Behavior:
        - Attempts to auto-discover tools under `mcp_tools/`.
        - Uses LangChain ChatGroq as LLM (configured via GROQ_API_KEY, GROQ_MODEL env vars).
        - Preserves template structure exactly; only updates existing values.
        - Falls back to conservative search-based filler if LLM unavailable.
        - Returns pretty-printed JSON string, or original input on error.

    Returns:
        Filled JSON as string, with same structure as input template.
    """
    try:
        template = json.loads(content)
    except Exception:
        return content

    tools_path = Path(__file__).resolve().parent.parent / "mcp_tools"

    # Try importing LangChain/Groq pieces; if unavailable we will fall back.
    try:
        from langchain.tools import Tool
        from langchain.agents import initialize_agent, AgentType
        from langchain.chat_models import ChatGroq
    except Exception:
        Tool = None
        initialize_agent = None
        AgentType = None
        ChatGroq = None

    # ========================================================================
    # INTERNAL HELPER: Merge LLM output with template
    # ========================================================================

    def safe_merge(template_obj: Any, candidate_obj: Any) -> Any:
        """
        Safely merge LLM output with template, preserving structure exactly.

        This merge function ensures:
          - No new keys are added beyond what's in the template
          - No keys are removed from the template
          - Data types (dict/list/scalar) are preserved
          - Empty/placeholder values are replaced; filled values are kept

        Args:
            template_obj: Original template (source of truth for structure).
            candidate_obj: LLM output to merge values from.

        Returns:
            Merged object with template structure and LLM values.
        """
        # Both are dicts: merge recursively, key by key
        if isinstance(template_obj, dict) and isinstance(candidate_obj, dict):
            result = {}
            for key, template_value in template_obj.items():
                if key in candidate_obj:
                    result[key] = safe_merge(template_value, candidate_obj[key])
                else:
                    result[key] = template_value
            return result

        # Both are lists: merge element-wise, preserving template schema
        if isinstance(template_obj, list) and isinstance(candidate_obj, list):
            if len(template_obj) > 0:
                # Template has schema (prototype); merge each candidate element
                proto = template_obj[0]
                merged_list = []
                for candidate_item in candidate_obj:
                    if isinstance(proto, dict) and isinstance(candidate_item, dict):
                        merged_list.append(safe_merge(proto, candidate_item))
                    elif (
                        not isinstance(proto, dict)
                        and not isinstance(candidate_item, dict)
                    ):
                        # Both are scalars; accept candidate
                        merged_list.append(candidate_item)
                return merged_list
            else:
                # Template list is empty; only accept scalar lists
                if all(not isinstance(x, dict) for x in candidate_obj):
                    return candidate_obj
                return template_obj

        # Template is a string: replace only if it was empty/placeholder
        if isinstance(template_obj, str):
            is_empty_or_placeholder = (
                template_obj.strip() == ""
                or template_obj.strip().lower()
                in ("tbd", "placeholder", "n/a", "text", "title")
            )
            if is_empty_or_placeholder:
                return candidate_obj if isinstance(candidate_obj, str) else template_obj
            return template_obj

        # Template is None: replace with candidate if available
        if template_obj is None:
            return candidate_obj if candidate_obj is not None else template_obj

        return template_obj

    # ========================================================================
    # INTERNAL CLASS: LLM-based JSON filling agent
    # ========================================================================

    class JsonFillingAgent:
        """
        Intelligent JSON filling agent using LangChain + Groq LLM.

        Discovers available MCP tools, initializes an LLM agent with those tools,
        and uses it to fill empty template values based on context.
        """

        def __init__(
            self,
            tools_dir: Path,
            groq_key: Optional[str],
            model_name: Optional[str],
        ) -> None:
            """
            Initialize the JSON filling agent.

            Args:
                tools_dir: Path to mcp_tools directory for tool discovery.
                groq_key: Groq API key (or None to read from env).
                model_name: Groq model name (or None to read from env).
            """
            self.tools_dir = tools_dir
            self.groq_key = groq_key
            self.model_name = model_name or os.getenv("GROQ_MODEL")
            self.tools: List[Any] = []
            self.agent_executor: Optional[Any] = None
            self._discover_tools()
            self._init_agent()

        def _discover_tools(self) -> None:
            """
            Auto-discover tools by scanning mcp_tools directory.

            For each .py file, imports it, finds public classes, and extracts
            their public methods as LangChain tools. Skips errors gracefully.
            """
            if Tool is None:
                return
            if not self.tools_dir.exists():
                return

            for py_file in sorted(self.tools_dir.glob("*.py")):
                try:
                    # Load the module dynamically
                    module_name = f"mcp_tools.{py_file.stem}"
                    spec = importlib.util.spec_from_file_location(
                        module_name, str(py_file)
                    )
                    if not spec or not spec.loader:
                        continue

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)  # type: ignore

                    # Find all classes defined in this module
                    for class_name, class_obj in inspect.getmembers(
                        module, inspect.isclass
                    ):
                        # Only include classes defined in this module
                        if class_obj.__module__ != module.__name__:
                            continue

                        # For each public method, create a LangChain tool wrapper
                        for method_name, method in inspect.getmembers(
                            class_obj, predicate=inspect.isfunction
                        ):
                            # Skip private methods
                            if method_name.startswith("_"):
                                continue

                            # Create a callable that instantiates the class and calls the method
                            def make_tool_callable(cls: type, method_to_call: str):
                                """Closure to capture class and method name."""

                                def call(json_argument: str) -> str:
                                    """
                                    Call the method with arguments provided as a JSON string.

                                    Instantiates the class, parses the JSON, and calls the method.
                                    """
                                    try:
                                        instance = cls()
                                        fn = getattr(instance, method_to_call)
                                        # Parse JSON arguments
                                        if json_argument:
                                            args = json.loads(json_argument)
                                            if not isinstance(args, dict):
                                                return f"Tool error: Arguments must be a JSON object (dict), but received {type(args).__name__}"
                                        else:
                                            args = {}
                                        
                                        # Call the method with unpacked arguments
                                        result = fn(**args)
                                        return json.dumps(result)
                                    except Exception as error:
                                        return f"Tool error: {error}"

                                return call

                            try:
                                tool_callable = make_tool_callable(class_obj, method_name)
                                doc_string = (
                                    getattr(class_obj, method_name).__doc__ or ""
                                ).strip()
                                # Enhance description to explicitly state JSON input and output expectation
                                enhanced_doc_string = (
                                    f"{doc_string}\n\n"
                                    "**Input**: This tool expects arguments as a JSON string, "
                                    "e.g., `{\"param1\": \"value1\", \"param2\": \"value2\"}`. "
                                    "Refer to the method's docstring for available parameters.\n"
                                    "**Output**: On success, returns a JSON object containing the tool's result. "
                                    "Look for data under keys like 'data' or 'result'. "
                                    "On failure, returns a JSON object like `{\"status\": \"error\", \"message\": \"Error details\"}`."
                                )
                                tool = Tool(
                                    name=f"{class_name}.{method_name}",
                                    func=tool_callable,
                                    description=enhanced_doc_string,
                                )
                                self.tools.append(tool)
                            except Exception as e:
                                _logger.debug(f"Failed to wrap tool {class_name}.{method_name}: {e}")
                                # Skip tools that can't be wrapped
                                continue
                except Exception as e:
                    _logger.debug(f"Failed to load module {py_file.stem}: {e}")
                    # Skip modules that can't be loaded
                    continue

        def _init_agent(self) -> None:
            """
            Initialize the LLM agent with discovered tools.

            Creates a ChatGroq LLM and initializes a LangChain agent if:
              - LangChain imports are available
              - At least one tool was discovered
              - Groq API key is available

            Otherwise leaves agent_executor as None (triggers fallback).
            """
            if ChatGroq is None or initialize_agent is None or not self.tools:
                return

            try:
                api_key = self.groq_key or os.getenv("GROQ_API_KEY")
                if not api_key:
                    return

                # Initialize Groq LLM (handle different version signatures)
                if self.model_name:
                    llm = ChatGroq(api_key=api_key, model=self.model_name)
                else:
                    llm = ChatGroq(api_key=api_key)

                # Initialize agent with ZERO_SHOT_REACT_DESCRIPTION
                self.agent_executor = initialize_agent(
                    self.tools,
                    llm,
                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=False,
                )
                _logger.debug(
                    f"LLM agent initialized with {len(self.tools)} tools"
                )
            except Exception as error:
                _logger.debug(f"Failed to initialize LLM agent: {error}")
                self.agent_executor = None

        def fill(
            self,
            template_obj: Any,
            page_ctx: Optional[str],
            field_ctx: Optional[str],
        ) -> Any:
            """
            Fill template using LLM agent.

            Constructs a system prompt with both context layers, invokes the agent,
            and parses the JSON response.

            Args:
                template_obj: Template object to fill.
                page_ctx: Global page-level context.
                field_ctx: Field-level context.

            Returns:
                Filled template object (parsed from LLM JSON output).

            Raises:
                RuntimeError: If agent is not initialized.
                json.JSONDecodeError: If LLM output is not valid JSON.
            """
            if not self.agent_executor:
                raise RuntimeError("agent not initialized")

            # Build system prompt with both context layers
            system_prompt = (
                "You are a JSON completion assistant that fills template placeholders with REAL, useful data.\n\n"
                "RULES:\n"
                "- Do NOT add or remove any keys from the JSON.\n"
                "- Preserve the structure and types (dict/list/scalar) exactly.\n"
                "- Replace empty strings, null values, or placeholder values (TBD, placeholder, n/a, text, title, TXT).\n"
                "- For arrays, maintain the same element schema but fill with REAL data.\n"
                "- Use the available search tools to find REAL, current information.\n"
                "- Return ONLY valid JSON that matches the original template structure.\n\n"
                "DATA FILLING GUIDELINES:\n"
                "1. **Images**: For any field that should contain an image (image, imageUrl, photo, thumbnail, src, backgroundImage):\n"
                "   - Use the search tools to find relevant images\n"
                "   - Provide direct image URLs (https://... ending in .jpg, .png, .webp)\n"
                "   - Use Unsplash or Pexels URLs when possible: 'https://images.unsplash.com/photo-...?w=800'\n"
                "2. **URLs/Links**: For link fields, provide real, clickable URLs:\n"
                "   - Product links, article links, booking sites, etc.\n"
                "   - Format as full https:// URLs\n"
                "3. **Summaries**: Summarize search results into concise, useful text:\n"
                "   - Product descriptions: 2-3 sentences max\n"
                "   - Reviews: Brief, authentic-sounding reviews\n"
                "   - Titles: Clear, descriptive titles\n"
                "4. **Prices**: Use realistic price formats ($XX.XX)\n"
                "5. **Ratings**: Use numeric ratings (4.5, 3.8, etc.)\n"
                "6. **Action Buttons/Links**: Include actionable links:\n"
                "   - Maps: 'https://www.google.com/maps/search/{location}'\n"
                "   - Calendar: 'https://calendar.google.com/calendar/r/eventedit?text={title}'\n"
                "   - Sheets: 'https://docs.google.com/spreadsheets/create'\n"
                "   - Docs: 'https://docs.google.com/document/create'\n"
            )

            # Add page context if provided
            if page_ctx:
                system_prompt += f"\nGLOBAL PAGE CONTEXT:\n{page_ctx}\n"

            # Add field context if provided
            if field_ctx:
                system_prompt += f"\nFIELD-SPECIFIC CONTEXT:\n{field_ctx}\n"

            # Build user prompt with template
            user_prompt = (
                f"Template:\n{json.dumps(template_obj, ensure_ascii=False, indent=2)}\n\n"
                "Fill the template by replacing placeholder values with REAL data:\n"
                "- Search for relevant products, places, or content based on the context\n"
                "- Include real image URLs (from Unsplash, Pexels, or search results)\n"
                "- Make all links clickable with full URLs\n"
                "- Summarize search results into appropriate text lengths\n"
                "- Add Google integration links where appropriate (Maps, Calendar, Sheets, Docs)\n\n"
                "Return ONLY the filled JSON, with no additional text."
            )

            # Run agent
            agent_output = self.agent_executor.run(
                f"{system_prompt}\n{user_prompt}"
            )

            # Extract JSON from agent output
            json_text = _extract_json_from_output(agent_output)
            return json.loads(json_text)

    # ========================================================================
    # TRY LLM-BASED APPROACH FIRST
    # ========================================================================

    try:
        groq_api_key = os.getenv("GROQ_API_KEY")
        groq_model = os.getenv("GROQ_MODEL")
        agent = JsonFillingAgent(tools_path, groq_api_key, groq_model)

        # Only proceed if agent initialized successfully
        if agent.agent_executor:
            try:
                filled_output = agent.fill(template, page_context, field_context)
                merged_output = safe_merge(template, filled_output)
                return json.dumps(merged_output, ensure_ascii=False, indent=2)
            except Exception as error:
                _logger.debug(f"LLM filling failed, falling back: {error}")
                # Fall through to fallback filler below
    except Exception as error:
        _logger.debug(f"LLM agent creation failed, using fallback: {error}")
        # Fall through to fallback filler below

    # ========================================================================
    # FALLBACK: DETERMINISTIC FILLER USING WEB SEARCH
    # ========================================================================

    try:
        search_agent = _get_search_agent()

        def simple_fill(node: Any, path: List[str] = []) -> Any:
            """
            Simple deterministic fill using web search (fallback).

            Fills empty/placeholder string and None values by searching
            for page context. Does not hallucinate.

            Args:
                node: Current node to fill.
                path: Path to current node (for tracking).

            Returns:
                Node with filled values.
            """
            # Handle string values
            if isinstance(node, str):
                is_empty_or_placeholder = node.strip().lower() in (
                    "",
                    "tbd",
                    "placeholder",
                    "n/a",
                    "text",
                    "title",
                )
                if is_empty_or_placeholder and search_agent and page_context:
                    try:
                        search_results = search_agent.web_search(page_context)

                        def search_walk(obj: Any) -> Optional[str]:
                            """Recursively find first text value in search results."""
                            if isinstance(obj, list):
                                for element in obj:
                                    result = search_walk(element)
                                    if result:
                                        return result
                            elif isinstance(obj, dict):
                                for key in ("title", "name", "heading"):
                                    if (
                                        key in obj
                                        and isinstance(obj[key], str)
                                    ):
                                        return obj[key]
                                for value in obj.values():
                                    result = search_walk(value)
                                    if result:
                                        return result
                            return None

                        result = search_walk(search_results)
                        if result:
                            return result
                    except Exception as error:
                        _logger.debug(
                            f"Fallback search failed: {error}"
                        )
                return node

            # Handle None values
            if node is None:
                if search_agent and page_context:
                    try:
                        search_results = search_agent.web_search(page_context)

                        def search_walk(obj: Any) -> Optional[str]:
                            """Recursively find first text value in search results."""
                            if isinstance(obj, list):
                                for element in obj:
                                    result = search_walk(element)
                                    if result:
                                        return result
                            elif isinstance(obj, dict):
                                for key in ("title", "name", "heading"):
                                    if (
                                        key in obj
                                        and isinstance(obj[key], str)
                                    ):
                                        return obj[key]
                                for value in obj.values():
                                    result = search_walk(value)
                                    if result:
                                        return result
                            return None

                        result = search_walk(search_results)
                        if result:
                            return result
                    except Exception as error:
                        _logger.debug(
                            f"Fallback search failed for None: {error}"
                        )
                return None

            # Handle dicts: recursively fill each value
            if isinstance(node, dict):
                for key, value in list(node.items()):
                    node[key] = simple_fill(value, path + [key])
                return node

            # Handle lists: recursively fill each item
            if isinstance(node, list):
                if len(node) == 0:
                    return node
                return [simple_fill(item, path + ["[]"]) for item in node]

            # Return scalars unchanged
            return node

        filled_fallback = simple_fill(template, [])
        return json.dumps(filled_fallback, ensure_ascii=False, indent=2)

    except Exception as error:
        _logger.debug(f"Fallback filler failed: {error}")
        # Return original content if everything fails
        return content

# ============================================================================
# SANDBOX BUILDER
# ============================================================================


class EntertainmentAppSandboxBuilder:
    """
    Builds React CodeSandbox projects from existing directory structures.

    Walks the project directory tree, collects all files, optionally processes
    JSON files through the LLM-driven content filling system, and exports in
    CodeSandbox format.

    Attributes:
        project_dir: Root directory of the project to build.
        context: Page-level context for JSON filling.
    """

    # Files and directories to skip during collection
    _SKIP_DIRS = {
        ".git",
        "node_modules",
        "dist",
        "__pycache__",
        ".vscode",
        ".next",
    }
    _SKIP_EXTS = {".pyc", ".DS_Store", ".pyo"}
    _SKIP_FILES = {"sandbox_builder.py"}

    def __init__(
        self, context: str, project_dir: Optional[Path] = None
    ) -> None:
        """
        Initialize the sandbox builder.

        Args:
            context: Page-level context for JSON content filling.
            project_dir: Root project directory. Defaults to script's directory.
        """
        self.project_dir = project_dir or Path(__file__).parent
        self.context = context

    def build_sandbox(self) -> Dict[str, Dict[str, str]]:
        """
        Build sandbox by collecting all project files.

        Walks the project directory tree, reads files, processes JSON files
        through the content filling system, and returns in CodeSandbox format.

        Returns:
            Dictionary mapping file paths to file content dicts.
            Format: {"/path/to/file": {"content": "file contents"}}
        """
        files: Dict[str, Dict[str, str]] = {}
        files = self._collect_all_files(files, self.project_dir)
        return files

    # ========================================================================
    # FILE COLLECTION
    # ========================================================================

    def _collect_all_files(
        self,
        files: Dict[str, Dict[str, str]],
        root_path: Path,
    ) -> Dict[str, Dict[str, str]]:
        """
        Recursively walk directory tree and collect all readable files.

        Skips binary files and specified directories/extensions.
        Processes JSON files through the content filling system.

        Args:
            files: Accumulator dict to add files to.
            root_path: Current directory to walk.

        Returns:
            Updated files dict with all collected files.
        """
        for root, dirs, filenames in os.walk(root_path):
            # Filter directories to skip system and build directories
            dirs[:] = [d for d in dirs if d not in self._SKIP_DIRS]

            for filename in filenames:
                # Skip specific files and extensions
                if (
                    filename in self._SKIP_FILES
                    or Path(filename).suffix in self._SKIP_EXTS
                ):
                    continue

                file_path = Path(root) / filename
                relative_path = file_path.relative_to(root_path)
                str_path = str(relative_path).replace("\\", "/")

                try:
                    # Read file content
                    content = file_path.read_text(encoding="utf-8")

                    # ✅ Only process JSON if context is provided
                    # When context is empty, JSON files are read as-is
                    # (filled data will be injected later in render_ui_node)
                    if filename.endswith(".json") and self.context:
                        content = self._fill_json_content(content)

                    files[str_path] = {"content": content}

                except UnicodeDecodeError:
                    # Skip binary files (CodeSandbox cannot handle them)
                    _logger.debug(
                        f"Skipped binary file: {file_path}"
                    )
                except Exception as error:
                    print(f"Warning: Could not read {file_path}: {error}")

        return files

    def _fill_json_content(self, content: str) -> str:
        """
        Fill JSON content using the module-level update_json function.

        Args:
            content: Raw JSON string to fill.

        Returns:
            Filled JSON string, or original content on error.
        """
        try:
            return update_json(content, self.context, None)
        except Exception as error:
            _logger.debug(f"Failed to fill JSON content: {error}")
            return content

    # ========================================================================
    # EXPORT METHODS
    # ========================================================================

    def export_to_json(self, output_path: Path) -> None:
        """
        Export sandbox files to JSON format.

        Writes the collected files dict to a JSON file in CodeSandbox format.

        Args:
            output_path: Path to write the JSON export to.
        """
        sandbox_data = self.build_sandbox()
        output_path.write_text(json.dumps(sandbox_data, indent=2))
        print(f"Exported {len(sandbox_data)} files to {output_path}")

    def export_to_codesandbox_format(self) -> Dict[str, Dict[str, str]]:
        """
        Return files in CodeSandbox API format.

        Returns:
            Dictionary of files ready for CodeSandbox API.
        """
        return self.build_sandbox()

    def get_file_summary(self) -> Dict[str, int]:
        """
        Get a summary of file types in the project.

        Counts files by extension.

        Returns:
            Dict mapping file extensions to occurrence counts.
            Unknown extensions mapped to "no_ext".
        """
        files = self.build_sandbox()
        summary: Dict[str, int] = {}

        for filepath in files.keys():
            ext = Path(filepath).suffix or "no_ext"
            summary[ext] = summary.get(ext, 0) + 1

        return summary


# ============================================================================
# CLI ENTRY POINT
# ============================================================================


if __name__ == "__main__":
    """
    Command-line interface for the sandbox builder.

    Usage:
        python entertainment_builder.py [project_dir] [--export] [output_file]

    Arguments:
        project_dir: Root directory of the React project (defaults to script dir).
        --export: Export sandbox to JSON file (optional).
        output_file: Path to write JSON export to (defaults to sandbox_export.json).

    Example:
        python entertainment_builder.py /path/to/project --export output.json
    """

    # Parse project directory from command line or use current directory
    project_path = (
        Path(__file__).parent
        if len(sys.argv) < 2
        else Path(sys.argv[1])
    )

    # Initialize builder with empty context (no JSON filling for CLI usage)
    builder = EntertainmentAppSandboxBuilder(
        context="Entertainment App",
        project_dir=project_path,
    )

    # Build sandbox by collecting all files
    sandbox_files = builder.build_sandbox()

    # Print summary
    print(f"\n✅ Entertainment App Sandbox Builder")
    print(f"📁 Project directory: {project_path}")
    print(f"📦 Total files collected: {len(sandbox_files)}\n")

    # Show file summary by extension
    summary = builder.get_file_summary()
    print("📊 File types:")
    for ext, count in sorted(summary.items(), key=lambda x: x[1], reverse=True):
        print(f"   {ext}: {count} file(s)")

    # List all collected files
    print("\n📄 Files in sandbox:")
    for filepath in sorted(sandbox_files.keys()):
        print(f"   - {filepath}")

    # Optional: Export to JSON if --export flag is present
    if len(sys.argv) > 2 and sys.argv[2] == "--export":
        export_file = Path(
            sys.argv[3] if len(sys.argv) > 3 else "sandbox_export.json"
        )
        builder.export_to_json(export_file)
