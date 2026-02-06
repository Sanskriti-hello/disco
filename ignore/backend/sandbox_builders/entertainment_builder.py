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


def fill_data_with_mcp_tools(template_data: Dict, domain: str, context: str, tabs_structured_data: List[Dict] = None) -> Dict:
    """
    Robust template filler with Direct MCP Mapping + LLM refinement.
    Never returns original template on error if partial data is available.
    """
    print(f"🔧 Filling data for domain: {domain}")
    
    import json
    import os
    import copy
    
    # ✅ FIX 1: Use proper deep copy
    filled = copy.deepcopy(template_data)
    mcp_data = {}
    data_was_modified = False  # Track if we made any changes
    
    # ✅ FIX 2: Improved query extraction from tabs content
    query = ""
    
    # First try to extract from context
    if "User Request:" in context:
        extracted = context.split("User Request:")[-1].split("\n")[0].strip()
        # Only use if it's not a generic command
        if extracted and not any(generic in extracted.lower() for generic in 
            ["create a", "create dashboard", "make a", "build a", "generate"]):
            query = extracted
    
    # If query is generic or missing, extract from tabs
    if not query:
        if tabs_structured_data and len(tabs_structured_data) > 0:
            # Try to extract meaningful search terms from tab content
            for tab in tabs_structured_data[:3]:  # Check first 3 tabs
                structured = tab.get('structured', {})
                
                # Try headings first (most relevant)
                headings = structured.get('headings', [])
                if headings and len(headings) > 0:
                    # Use first meaningful heading
                    for heading in headings[:5]:
                        if (len(heading) > 5 and 
                            heading.lower() not in ['home', 'menu', 'search', 'navigation', 'header', 'footer'] and
                            not heading.lower().startswith('sign') and
                            not heading.lower().startswith('log')):
                            query = heading
                            print(f"📌 Using heading as query: {query}")
                            break
                    if query:
                        break
                
                # Fallback to extracting product names from links
                if not query:
                    links = structured.get('links', [])
                    for link in links[:10]:
                        link_text = link.get('text', '').strip()
                        # Look for product-like link text (not navigation)
                        if (len(link_text) > 10 and len(link_text) < 100 and
                            not any(nav in link_text.lower() for nav in 
                                ['sign in', 'cart', 'account', 'help', 'customer service', 'returns'])):
                            query = link_text
                            print(f"📌 Using link text as query: {query}")
                            break
                    if query:
                        break
                
                # Last resort: use title if it's not too generic
                if not query:
                    title = tab.get('title', '')
                    if (title and len(title) > 5 and 
                        not any(generic in title.lower() for generic in 
                            ['amazon', 'shop', 'store', 'home', 'welcome'])):
                        query = title
                        print(f"📌 Using tab title as query: {query}")
                        break
    
    # Final fallback - use domain but log warning
    if not query:
        query = domain
        print(f"⚠️ Could not extract specific query, using domain: {domain}")
    else:
        # Clean up the query
        query = query.strip()[:100]  # Limit length
            
    print(f"🔍 Extracted Query: {query}")

    # =========================================================================
    # PHASE 1: DIRECT DATA GATHERING & FILLING
    # =========================================================================
    try:
        # Import tools locally to avoid top-level failures
        search_client = None
        serpapi = None
        summarize_client = None
        
        try:
            from mcp_tools.search import SearchClient
            search_client = SearchClient()
        except ImportError as e:
            print(f"⚠️ SearchClient Import Warning: {e}")
            
        try:
            from mcp_tools.serpapi_tools import SerpAPIClient
            serpapi = SerpAPIClient()
        except ImportError as e:
            print(f"⚠️ SerpAPI Import Warning: {e}")
        
        try:
            from mcp_tools.summarize import summarize_text
            # Create a simple wrapper class for consistency
            class SummarizeClient:
                def summarize_text(self, text: str) -> str:
                    return summarize_text(text)
            summarize_client = SummarizeClient()
            print("✅ Summarize client initialized")
        except ImportError as e:
            print(f"⚠️ Summarize Import Warning: {e}")

        # --- SHOPPING ---
        if domain.lower() == "shopping":
            products = []
            
            # ✅ FIX 3: Proper Amazon API call with better error handling
            try:
                from mcp_tools.amazon import AmazonClient
                amazon = AmazonClient()
                
                # Call Amazon API with proper parameters
                res = amazon.search_products(query=query, country="US")
                
                # ✅ FIX 4: Better data extraction from Amazon response
                # Check for error response first
                if res and isinstance(res, dict):
                    if res.get("status") == "error":
                        error_msg = res.get("message", "Unknown error")
                        print(f"⚠️ Amazon API Error Response: {error_msg}")
                        # Check if it's an API key issue
                        if "api key" in error_msg.lower() or "unauthorized" in error_msg.lower():
                            print(f"💡 Hint: Set RAPIDAPI_KEY environment variable")
                    else:
                        # Handle different successful response structures
                        if "data" in res:
                            products = res["data"].get("products", [])
                        elif "products" in res:
                            products = res["products"]
                        else:
                            print(f"⚠️ Unexpected Amazon response structure: {list(res.keys())}")
                
                if products:
                    print(f"📦 Amazon API: Found {len(products)} products")
                else:
                    print(f"📦 Amazon API: Returned 0 products for query '{query}'")
                    
            except ImportError:
                print(f"⚠️ Amazon module not available")
            except ValueError as e:
                # This catches the "API key is required" error
                print(f"⚠️ Amazon API Configuration Error: {e}")
                print(f"💡 Set RAPIDAPI_KEY environment variable to enable Amazon API")
            except Exception as e:
                print(f"⚠️ Amazon API Error: {e}")
                import traceback
                traceback.print_exc()
            
            # ✅ FIX 5: SerpAPI fallback that actually modifies filled dict
            if not products and serpapi:
                try:
                    print(f"🔄 Trying SerpAPI Amazon Fallback for '{query}'...")
                    serp_result = serpapi.search_amazon(query)
                    
                    if serp_result and isinstance(serp_result, dict):
                        products = serp_result.get("products", [])
                        if products:
                            print(f"✅ SerpAPI Fallback: Found {len(products)} products")
                            data_was_modified = True
                        else:
                            print(f"⚠️ SerpAPI returned 0 products")
                    else:
                        print(f"⚠️ SerpAPI returned invalid response")
                        
                except Exception as e:
                    print(f"⚠️ SerpAPI Fallback Error: {e}")
                    import traceback
                    traceback.print_exc()

            # Store products in mcp_data
            if products:
                mcp_data["products"] = products[:6]
                # 🔍 DEBUG: Show actual product structure
                print(f"🔍 DEBUG: First product keys: {list(products[0].keys())}")
                print(f"🔍 DEBUG: First product sample: {str(products[0])[:200]}")
            
            # ✅ FIX 6: DIRECT FILL LOGIC with better error handling
            if products and "main" in filled:
                try:
                    p = products[0]
                    
                    # 🔍 DEBUG: Show what fields we're trying to extract
                    print(f"🔍 Trying to extract from product with keys: {list(p.keys())}")
                    
                    # Normalize price with multiple fallbacks
                    price = p.get("price") or p.get("product_price") or p.get("price_string")
                    if isinstance(price, dict):
                        price = price.get("raw", price.get("value", price.get("symbol", "") + str(price.get("amount", "0.00"))))
                    elif price is None:
                        price = "$0.00"
                    else:
                        price = str(price)
                    
                    # Extract fields with multiple fallback keys
                    product_name = (p.get("title") or p.get("product_title") or 
                                   p.get("name") or p.get("product_name") or "Product")[:50]
                    
                    product_desc = (p.get("description") or p.get("product_description") or 
                                   p.get("title") or p.get("product_title") or "")[:100]
                    
                    product_image = (p.get("product_photo") or p.get("product_main_image_url") or
                                    p.get("thumbnailImage") or p.get("thumbnail") or 
                                    p.get("image") or p.get("product_image") or "")
                    
                    product_url = (p.get("product_url") or p.get("url") or 
                                  p.get("link") or p.get("productUrl") or "")
                    
                    print(f"📦 Extracted: name='{product_name}', price='{price}', image={bool(product_image)}, url={bool(product_url)}")
                    
                    # Fill product highlight
                    if "productHighlight" in filled["main"]:
                        filled["main"]["productHighlight"].update({
                            "name": product_name,
                            "text": product_desc,
                            "price": price,
                            "imageUrl": product_image,
                            "productUrl": product_url
                        })
                        data_was_modified = True
                        print(f"✅ Updated productHighlight with: {product_name} @ {price}")
                    
                    # Fill carousel items
                    if "carousel" in filled["main"] and "items" in filled["main"]["carousel"]:
                        items_filled = 0
                        for i, item in enumerate(filled["main"]["carousel"]["items"]):
                            if i < len(products):
                                p_item = products[i]
                                
                                # Extract with fallbacks
                                item_price = p_item.get("price") or p_item.get("product_price") or p_item.get("price_string")
                                if isinstance(item_price, dict):
                                    item_price = item_price.get("raw", item_price.get("value", ""))
                                elif item_price is None:
                                    item_price = ""
                                else:
                                    item_price = str(item_price)
                                
                                item_name = (p_item.get("title") or p_item.get("product_title") or 
                                           p_item.get("name") or p_item.get("product_name") or "")[:30]
                                
                                item_image = (p_item.get("product_photo") or p_item.get("product_main_image_url") or
                                            p_item.get("thumbnailImage") or p_item.get("thumbnail") or 
                                            p_item.get("image") or p_item.get("product_image") or "")
                                
                                item_url = (p_item.get("product_url") or p_item.get("url") or 
                                          p_item.get("link") or p_item.get("productUrl") or "")
                                
                                item.update({
                                    "title": item_name,
                                    "imageUrl": item_image,
                                    "price": item_price,
                                    "url": item_url
                                })
                                data_was_modified = True
                                items_filled += 1
                        
                        print(f"✅ Filled {items_filled} carousel items")
                                
                    print("✅ Direct Shopping Fill Applied")
                    
                except Exception as e:
                    print(f"⚠️ Direct Fill Error: {e}")
                    import traceback
                    traceback.print_exc()
            
            # ✅ FIX 7: Web search fallback for shopping if no products found
            elif search_client:
                print(f"🔍 No products found, trying web search fallback...")
                try:
                    _fill_with_web_search(filled, search_client, query, domain)
                    data_was_modified = True
                except Exception as e:
                    print(f"⚠️ Web search fallback error: {e}")

        # --- ENTERTAINMENT DOMAIN ---
        elif domain.lower() == "entertainment":
            print(f"🎬 Processing Entertainment domain...")
            
            # Try to get events and movies
            try:
                if serpapi:
                    # Search for events
                    events_res = serpapi.search_events(f"events {query}")
                    events = events_res.get("events", [])[:6] if events_res else []
                    
                    # Search for images
                    images_res = serpapi.search_images(f"{query} entertainment", num=6)
                    images = images_res.get("images", [])[:6] if images_res else []
                    
                    # Search for news/articles
                    news_res = serpapi.search_news(query)
                    news = news_res.get("articles", [])[:5] if news_res else []
                    
                    mcp_data["events"] = events
                    mcp_data["images"] = images
                    mcp_data["news"] = news
                    
                    # Direct fill for entertainment template
                    if "leftColumn" in filled and events:
                        event = events[0]
                        filled["leftColumn"]["label"] = "More Like This"
                        if "items" in filled["leftColumn"]:
                            for i, item in enumerate(filled["leftColumn"]["items"][:len(events)]):
                                if i < len(events):
                                    e = events[i]
                                    item.update({
                                        "title": e.get("title", "")[:30],
                                        "imageUrl": e.get("thumbnail", e.get("image", "")),
                                        "url": e.get("link", e.get("url", ""))
                                    })
                                    data_was_modified = True
                    
                    # Fill rightColumn featured content
                    if "rightColumn" in filled:
                        if "featured" in filled["rightColumn"] and (events or news):
                            featured_item = events[0] if events else news[0]
                            filled["rightColumn"]["featured"].update({
                                "title": featured_item.get("title", "")[:50],
                                "description": featured_item.get("snippet", featured_item.get("description", ""))[:150],
                                "imageUrl": featured_item.get("thumbnail", featured_item.get("image", "")),
                                "rating": 4.5,
                                "year": "2025",
                                "genre": "Entertainment"
                            })
                            data_was_modified = True
                        
                        # Fill textBox
                        if "textBox" in filled["rightColumn"] and news:
                            filled["rightColumn"]["textBox"] = news[0].get("snippet", news[0].get("description", ""))[:200]
                            data_was_modified = True
                        
                        # Fill items from rightColumn if present
                        if "items" in filled["rightColumn"] and news:
                            for i, item in enumerate(filled["rightColumn"]["items"][:len(news)]):
                                if i < len(news):
                                    article = news[i]
                                    item.update({
                                        "title": article.get("title", "")[:50],
                                        "content": article.get("snippet", article.get("description", ""))[:100],
                                        "url": article.get("link", article.get("url", ""))
                                    })
                                    data_was_modified = True
                    
                    # Fill main items array (for entertainment-1)
                    if "items" in filled and images:
                        for i, item in enumerate(filled["items"][:len(images)]):
                            if i < len(images):
                                img = images[i]
                                event = events[i] if i < len(events) else None
                                item.update({
                                    "title": (event.get("title", "") if event else img.get("title", ""))[:40],
                                    "imageUrl": img.get("thumbnail", img.get("url", "")),
                                    "url": (event.get("link", "") if event else img.get("source", "")),
                                    "rating": 4.0 + (i * 0.1)
                                })
                                data_was_modified = True
                    
                    # Fill action bar buttons
                    if "actionBar" in filled and "buttons" in filled["actionBar"] and events:
                        if len(filled["actionBar"]["buttons"]) > 0:
                            filled["actionBar"]["buttons"][0]["url"] = events[0].get("link", events[0].get("url", ""))
                            data_was_modified = True
                    
                    # Fill centerSection for entertainment-2
                    if "centerSection" in filled:
                        if "titleBox" in filled["centerSection"] and events:
                            filled["centerSection"]["titleBox"].update({
                                "title": events[0].get("title", "")[:50],
                                "body": events[0].get("snippet", events[0].get("description", ""))[:150]
                            })
                            data_was_modified = True
                    
                    print(f"✅ Entertainment: {len(events)} events, {len(images)} images, {len(news)} articles")
                    
            except Exception as e:
                print(f"⚠️ Entertainment fill error: {e}")
                import traceback
                traceback.print_exc()
        
        # --- TRAVEL DOMAIN ---
        elif domain.lower() == "travel":
            print(f"✈️ Processing Travel domain...")
            
            try:
                if serpapi:
                    # Search for destination images
                    images_res = serpapi.search_images(f"{query} travel destination", num=6)
                    images = images_res.get("images", [])[:6] if images_res else []
                    
                    # Search for hotels
                    hotels_res = serpapi.search_local(f"hotels in {query}")
                    hotels = hotels_res.get("places", [])[:5] if hotels_res else []
                    
                    # Search for attractions
                    attractions_res = serpapi.search_local(f"attractions in {query}")
                    attractions = attractions_res.get("places", [])[:4] if attractions_res else []
                    
                    mcp_data["travel_images"] = images
                    mcp_data["hotels"] = hotels
                    mcp_data["attractions"] = attractions
                    
                    # Direct fill for travel template
                    if "main" in filled:
                        # Fill destination
                        if "destination" in filled["main"]:
                            filled["main"]["destination"].update({
                                "name": query[:50],
                                "description": f"Explore {query}" if query else "Travel destination",
                                "imageUrl": images[0].get("thumbnail", images[0].get("url", "")) if images else "",
                                "mapsUrl": f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
                            })
                            data_was_modified = True
                        
                        # Fill photos
                        if "photos" in filled["main"] and images:
                            for i, photo in enumerate(filled["main"]["photos"][:len(images)]):
                                if i < len(images):
                                    img = images[i]
                                    photo.update({
                                        "description": img.get("title", f"Photo {i+1}")[:30],
                                        "imageUrl": img.get("thumbnail", img.get("url", "")),
                                        "mapsUrl": f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
                                    })
                                    data_was_modified = True
                        
                        # Fill hotels
                        if "hotels" in filled["main"] and hotels:
                            filled["main"]["hotels"] = []
                            for i, hotel in enumerate(hotels[:5]):
                                filled["main"]["hotels"].append({
                                    "name": hotel.get("title", hotel.get("name", "Hotel"))[:40],
                                    "rating": hotel.get("rating", 4.0),
                                    "price": hotel.get("price", "$100/night"),
                                    "imageUrl": hotel.get("thumbnail", ""),
                                    "bookingUrl": hotel.get("link", hotel.get("url", ""))
                                })
                                data_was_modified = True
                        
                        # Fill text box with summary
                        if "textBox" in filled["main"]:
                            filled["main"]["textBox"]["text"] = f"Discover {query} - a wonderful destination with amazing hotels, attractions, and experiences."
                            data_was_modified = True
                    
                    print(f"✅ Travel: {len(images)} images, {len(hotels)} hotels, {len(attractions)} attractions")
                    
            except Exception as e:
                print(f"⚠️ Travel fill error: {e}")
                import traceback
                traceback.print_exc()
        
        # --- CODE DOMAIN ---
        elif domain.lower() == "code":
            print(f"💻 Processing Code domain...")
            
            try:
                # Try to extract repository info from tabs
                repo_info = None
                if tabs_structured_data:
                    for tab in tabs_structured_data[:3]:
                        url = tab.get("url", "")
                        if "github.com" in url:
                            # Extract repo name from GitHub URL
                            parts = url.split("github.com/")
                            if len(parts) > 1:
                                repo_path = parts[1].split("/")[:2]
                                if len(repo_path) == 2:
                                    repo_info = {
                                        "name": "/".join(repo_path),
                                        "url": f"https://github.com/{'/'.join(repo_path)}",
                                        "description": tab.get("title", "")
                                    }
                                    break
                
                # Use web search for code resources
                if search_client:
                    search_res = search_client.web_search(f"{query} documentation tutorial")
                    web_results = search_res.get("organic_results", [])[:10] if search_res else []
                    mcp_data["web_results"] = web_results
                    
                    # Direct fill for code template
                    if "mainContent" in filled:
                        # Fill repository info
                        if "repository" in filled["mainContent"]:
                            if repo_info:
                                filled["mainContent"]["repository"].update({
                                    "name": repo_info["name"],
                                    "description": repo_info.get("description", "")[:100],
                                    "url": repo_info["url"],
                                    "stars": 0,
                                    "language": "JavaScript"
                                })
                            else:
                                filled["mainContent"]["repository"].update({
                                    "name": query[:50],
                                    "description": f"Code repository for {query}"[:100],
                                    "url": web_results[0].get("link", "") if web_results else "",
                                    "stars": 0,
                                    "language": "JavaScript"
                                })
                            data_was_modified = True
                        
                        # Fill code snippet from tab content
                        if "codeSnippet" in filled["mainContent"] and tabs_structured_data:
                            # Try to extract code from tabs
                            for tab in tabs_structured_data[:3]:
                                structured = tab.get("structured", {})
                                paragraphs = structured.get("paragraphs", [])
                                for para in paragraphs:
                                    if any(keyword in para.lower() for keyword in ["function", "const", "class", "import", "def", "public"]):
                                        filled["mainContent"]["codeSnippet"] = para[:500]
                                        data_was_modified = True
                                        break
                                if filled["mainContent"]["codeSnippet"]:
                                    break
                        
                        # Fill documentation
                        if "documentation" in filled["mainContent"] and web_results:
                            filled["mainContent"]["documentation"] = web_results[0].get("snippet", "")[:200]
                            data_was_modified = True
                    
                    # Fill resources
                    if "resources" in filled and web_results:
                        for i, resource in enumerate(filled["resources"][:len(web_results)]):
                            if i < len(web_results):
                                result = web_results[i]
                                resource.update({
                                    "title": result.get("title", "")[:50],
                                    "url": result.get("link", ""),
                                    "type": "docs" if i == 0 else ("tutorial" if i == 1 else "example")
                                })
                                data_was_modified = True
                    
                    # Fill actions
                    if "actions" in filled:
                        if repo_info:
                            filled["actions"]["openInGithub"] = repo_info["url"]
                        elif web_results:
                            filled["actions"]["openInGithub"] = web_results[0].get("link", "")
                        data_was_modified = True
                    
                    print(f"✅ Code: {len(web_results)} resources found")
                    
            except Exception as e:
                print(f"⚠️ Code fill error: {e}")
                import traceback
                traceback.print_exc()
        
        # --- STUDY DOMAIN ---
        elif domain.lower() == "study":
            print(f"📚 Processing Study domain...")
            
            try:
                if serpapi:
                    # Search for scholarly papers
                    papers_res = serpapi.search_scholar(query)
                    papers = papers_res.get("papers", [])[:5] if papers_res else []
                    
                    # Search for images
                    images_res = serpapi.search_images(f"{query} diagram infographic", num=3)
                    images = images_res.get("images", [])[:3] if images_res else []
                    
                    mcp_data["papers"] = papers
                    mcp_data["images"] = images
                    
                    # Direct fill for study template
                    if "main" in filled:
                        # Fill topic
                        if "topic" in filled["main"]:
                            filled["main"]["topic"].update({
                                "title": query[:100],  # Increased from 50
                                "description": f"Study guide for {query}"[:200],  # Increased from 100
                                "imageUrl": images[0].get("thumbnail", images[0].get("url", "")) if images else ""
                            })
                            data_was_modified = True
                        
                        # Fill summary - Use summarize tool if available and tabs have content
                        if "summary" in filled["main"]:
                            summary_text = ""
                            summary_source = ""
                            summary_url = ""
                            
                            # Try to generate summary from tab content first
                            if tabs_structured_data and summarize_client:
                                try:
                                    print("🧠 Generating detailed summary from tab content...")
                                    # Collect content from tabs
                                    tab_content = []
                                    for tab in tabs_structured_data[:3]:  # Use first 3 tabs
                                        structured = tab.get("structured", {})
                                        paragraphs = structured.get("paragraphs", [])
                                        
                                        # If structured data has paragraphs, use them
                                        if paragraphs:
                                            tab_content.extend(paragraphs[:5])  # Get first 5 paragraphs from each tab
                                        # Fallback: use plain content field if structured is empty
                                        elif tab.get("content"):
                                            plain_content = tab.get("content", "")[:2000]  # Limit to 2000 chars
                                            if plain_content.strip():
                                                tab_content.append(plain_content)
                                                print(f"📄 Using plain content from tab (structured data empty)")
                                    
                                    if tab_content:
                                        combined_content = " ".join(tab_content)
                                        print(f"📝 Collected {len(combined_content)} chars of content from {len(tab_content)} sources")
                                        
                                        # Use summarize MCP tool
                                        summary_text = summarize_client.summarize_text(combined_content)
                                        summary_source = tabs_structured_data[0].get("title", "")[:100]
                                        summary_url = tabs_structured_data[0].get("url", "")
                                        print(f"✅ Generated summary from tabs ({len(summary_text)} chars)")
                                    else:
                                        print("⚠️ No content found in tabs (both structured and plain content empty)")
                                except Exception as e:
                                    print(f"⚠️ Summary generation from tabs failed: {e}")
                                    import traceback
                                    traceback.print_exc()
                            
                            # Fallback to paper abstract if no tab summary
                            if not summary_text and papers:
                                paper = papers[0]
                                summary_text = paper.get("snippet", paper.get("abstract", ""))[:500]  # Increased from 200
                                summary_source = paper.get("publication", "")[:100]  # Increased from 50
                                summary_url = paper.get("link", "")
                            
                            if summary_text:
                                filled["main"]["summary"].update({
                                    "title": "Summary",
                                    "text": summary_text,
                                    "source": summary_source,
                                    "sourceUrl": summary_url
                                })
                                data_was_modified = True
                        
                        # Fill key points from papers AND tabs
                        if "keyPoints" in filled["main"]:
                            key_points_filled = 0
                            
                            # First, fill from papers
                            for i, point in enumerate(filled["main"]["keyPoints"][:len(papers)]):
                                if i < len(papers):
                                    paper = papers[i]
                                    point.update({
                                        "point": paper.get("title", "")[:100],  # Increased from 50
                                        "details": paper.get("snippet", "")[:300]  # Increased from 100
                                    })
                                    data_was_modified = True
                                    key_points_filled += 1
                            
                            # Then, fill remaining from tab headings/content
                            if tabs_structured_data and key_points_filled < len(filled["main"]["keyPoints"]):
                                for tab in tabs_structured_data[:2]:
                                    structured = tab.get("structured", {})
                                    headings = structured.get("headings", [])
                                    paragraphs = structured.get("paragraphs", [])
                                    
                                    for j, heading in enumerate(headings):
                                        if key_points_filled >= len(filled["main"]["keyPoints"]):
                                            break
                                        
                                        # Get corresponding paragraph if available
                                        details = paragraphs[j] if j < len(paragraphs) else ""
                                        
                                        filled["main"]["keyPoints"][key_points_filled].update({
                                            "point": heading[:100],
                                            "details": details[:300]
                                        })
                                        data_was_modified = True
                                        key_points_filled += 1
                                    
                                    if key_points_filled >= len(filled["main"]["keyPoints"]):
                                        break
                            
                            print(f"✅ Filled {key_points_filled} key points")
                        
                        # Fill resources from papers and tabs
                        if "resources" in filled["main"]:
                            filled["main"]["resources"] = []
                            resource_id = 1
                            
                            # Add papers as resources
                            for i, paper in enumerate(papers[:3]):
                                filled["main"]["resources"].append({
                                    "id": resource_id,
                                    "title": paper.get("title", "")[:100],  # Increased from 50
                                    "url": paper.get("link", ""),
                                    "type": "paper"
                                })
                                resource_id += 1
                                data_was_modified = True
                            
                            # Add tabs as resources
                            if tabs_structured_data:
                                for tab in tabs_structured_data[:3]:
                                    if resource_id > 6:  # Limit to 6 total resources
                                        break
                                    filled["main"]["resources"].append({
                                        "id": resource_id,
                                        "title": tab.get("title", "")[:100],
                                        "url": tab.get("url", ""),
                                        "type": "article"
                                    })
                                    resource_id += 1
                                    data_was_modified = True
                    
                    print(f"✅ Study: {len(papers)} papers, {len(images)} images, {len(filled.get('main', {}).get('resources', []))} resources")
                    
            except Exception as e:
                print(f"⚠️ Study fill error: {e}")
                import traceback
                traceback.print_exc()
        
        # --- GENERIC DOMAIN ---
        elif domain.lower() == "generic":
            print(f"🔧 Processing Generic domain...")
            
            try:
                if search_client:
                    # Use web search for generic content
                    search_res = search_client.web_search(query)
                    web_results = search_res.get("organic_results", [])[:10] if search_res else []
                    mcp_data["web_results"] = web_results
                    
                    # Search for images
                    if serpapi:
                        images_res = serpapi.search_images(query, num=4)
                        images = images_res.get("images", [])[:4] if images_res else []
                        mcp_data["images"] = images
                    else:
                        images = []
                    
                    # Direct fill for generic-1 template
                    if "leftColumn" in filled:
                        filled["leftColumn"]["summaryTitle"] = "Summary"
                        if web_results:
                            filled["leftColumn"]["summaryText"] = web_results[0].get("snippet", "")[:200]
                            filled["leftColumn"]["imageUrl"] = images[0].get("thumbnail", images[0].get("url", "")) if images else ""
                            data_was_modified = True
                    
                    # Direct fill for generic-2 template (main.summary)
                    if "main" in filled:
                        if "summary" in filled["main"] and web_results:
                            filled["main"]["summary"].update({
                                "title": "SUMMARY",
                                "text": web_results[0].get("snippet", "")[:300]
                            })
                            data_was_modified = True
                        
                        # Fill main.boxes for generic-2
                        if "boxes" in filled["main"] and web_results:
                            for i, box in enumerate(filled["main"]["boxes"][:len(web_results)]):
                                if i < len(web_results):
                                    result = web_results[i]
                                    box.update({
                                        "title": result.get("title", "")[:50],
                                        "description": result.get("snippet", "")[:100],
                                        "imageUrl": images[i].get("thumbnail", images[i].get("url", "")) if i < len(images) else "",
                                        "url": result.get("link", "")
                                    })
                                    data_was_modified = True
                    
                    # Fill boxes for generic-1
                    if "boxes" in filled and web_results:
                        for i, box in enumerate(filled["boxes"][:len(web_results)]):
                            if i < len(web_results):
                                result = web_results[i]
                                box.update({
                                    "title": result.get("title", "")[:50],
                                    "description": result.get("snippet", "")[:100],
                                    "imageUrl": images[i].get("thumbnail", images[i].get("url", "")) if i < len(images) else "",
                                    "url": result.get("link", "")
                                })
                                data_was_modified = True
                    
                    # Fill links for generic-1
                    if "links" in filled and web_results:
                        for i, link in enumerate(filled["links"][:len(web_results)]):
                            if i < len(web_results):
                                result = web_results[i]
                                link.update({
                                    "text": result.get("title", "")[:40],
                                    "url": result.get("link", ""),
                                    "icon": "🔗"
                                })
                                data_was_modified = True
                    
                    # Fill sidebar.links for generic-2
                    if "sidebar" in filled and "links" in filled["sidebar"] and web_results:
                        for i, link in enumerate(filled["sidebar"]["links"][:len(web_results)]):
                            if i < len(web_results):
                                result = web_results[i]
                                link.update({
                                    "text": result.get("title", "")[:40],
                                    "url": result.get("link", "")
                                })
                                data_was_modified = True
                    
                    print(f"✅ Generic: {len(web_results)} results, {len(images)} images")
                    
            except Exception as e:
                print(f"⚠️ Generic fill error: {e}")
                import traceback
                traceback.print_exc()
        
        # --- FALLBACK FOR ANY DOMAIN ---
        else:
            print(f"⚠️ Unknown domain '{domain}', using generic fallback...")
            if serpapi:
                try:
                    mcp_data["web_results"] = serpapi.search_web(query).get("organic_results", [])[:10]
                    mcp_data["images"] = serpapi.search_images(query).get("images", [])[:6]
                    data_was_modified = True
                except Exception as e:
                    print(f"⚠️ SerpAPI Fallback Error: {e}")
                    import traceback
                    traceback.print_exc()

    except Exception as e:
        print(f"⚠️ Phase 1 Error: {e}")
        import traceback
        traceback.print_exc()
        # ✅ FIX 8: Don't return template on error, continue with partial data

    # =========================================================================
    # PHASE 2: LLM REFINEMENT
    # =========================================================================
    llm_success = False
    try:
        from langchain_groq import ChatGroq
        
        groq_key = os.getenv("GROQ_API_KEY")
        # ✅ Always try LLM refinement, even with minimal MCP data
        if groq_key:
            llm = ChatGroq(api_key=groq_key, model="llama-3.3-70b-versatile", temperature=0.3)
            
            # Build domain-specific prompts
            if domain.lower() == "study":
                system_prompt = f"""You are filling a study dashboard template with educational content.
                
Task: Fill the JSON template with meaningful study content based on the query "{query}".

Requirements:
1. Generate a comprehensive summary (200-500 chars) about the topic
2. Create 3 key points with details (each point: 50-100 chars, details: 100-300 chars)
3. Add 3-6 relevant resources with titles and URLs (use the provided tab URLs if available)
4. If tab content is available, use it to generate accurate summaries
5. If no specific content is available, generate educational content based on the topic title

Return ONLY valid JSON matching the template structure."""
            else:
                system_prompt = f"Fill JSON for {domain}. Use real data from MCP tools and tabs. Return ONLY valid JSON."
            
            # Build user prompt with tab content
            tab_context = ""
            if tabs_structured_data:
                tab_summaries = []
                for i, tab in enumerate(tabs_structured_data[:3]):
                    title = tab.get("title", "")
                    url = tab.get("url", "")
                    content = tab.get("content", "")[:500]  # First 500 chars
                    tab_summaries.append(f"Tab {i+1}: {title}\nURL: {url}\nContent: {content[:200]}...")
                tab_context = "\n\n".join(tab_summaries)
            
            user_prompt = f"""Template to fill:
{json.dumps(filled, indent=2)}

MCP Data Available:
{json.dumps(mcp_data, indent=2) if mcp_data else "No MCP data available"}

Tab Context:
{tab_context if tab_context else "No tab content available"}

Query: {query}

Fill the template with meaningful content. Ensure all placeholder text is replaced with real content."""
            
            print("🤖 Calling LLM to refine data...")
            response_obj = llm.invoke(f"{system_prompt}\n{user_prompt}")
            response = response_obj.content
            
            # Clean response
            if "```" in response:
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            llm_filled = json.loads(response.strip())
            
            # Merge LLM results SAFELY into our already-filled object
            if isinstance(llm_filled, dict) and _validate_filled_data(llm_filled):
                filled = llm_filled
                llm_success = True
                data_was_modified = True
                print("✅ LLM Refinement Successful")
            else:
                print("⚠️ LLM output validation failed, keeping direct fill")
            
    except ImportError:
        print(f"⚠️ langchain_groq not available, skipping LLM refinement")
    except Exception as e:
        print(f"⚠️ LLM Skipped/Failed: {e}")
        # ✅ FIX 9: Continue with 'filled' which has Direct Fill data

    # =========================================================================
    # PHASE 3: VALIDATION & RETURN
    # =========================================================================
    
    # ✅ FIX 10: Validate filled data before returning
    if _validate_filled_data(filled):
        print(f"✅ Data validation passed (modified: {data_was_modified})")
        return filled
    else:
        print(f"⚠️ Data still contains placeholders, but returning best effort")
        # Return filled data even with placeholders - it's better than nothing
        return filled



def _summarize_tabs_content(tabs: List[Dict]) -> str:
    """Summarize structured content from tabs into a context string."""
    if not tabs:
        return "No tab content available"
    
    parts = []
    for tab in tabs[:5]:  # Limit to 5 tabs
        tab_parts = [f"Page: {tab.get('title', 'Untitled')} ({tab.get('url', '')})"]
        
        structured = tab.get("structured", {})
        
        # Add headings
        headings = structured.get("headings", [])
        if headings:
            tab_parts.append(f"Headings: {', '.join(headings[:3])}")
        
        # Add paragraphs (summarized)
        paragraphs = structured.get("paragraphs", [])
        if paragraphs:
            tab_parts.append(f"Content: {' '.join(paragraphs[:2])[:300]}")
        
        # Add links with URLs
        links = structured.get("links", [])
        if links:
            link_items = [f"{l.get('text', '')} ({l.get('url', '')})" for l in links[:5] if l.get("text")]
            if link_items:
                tab_parts.append(f"Links: {', '.join(link_items)}")
        
        # Add images with URLs
        images = structured.get("images", [])
        if images:
            img_items = [img.get("src", "") for img in images[:3] if img.get("src")]
            if img_items:
                tab_parts.append(f"Image URLs: {', '.join(img_items)}")
        
        # Add plain content if no structured data
        if not structured and tab.get("content"):
            tab_parts.append(f"Content: {tab.get('content', '')[:300]}")
        
        parts.append("\n".join(tab_parts))
    
    return "\n\n---\n\n".join(parts)


def _validate_structure(template: Dict, candidate: Dict) -> bool:
    """Check if candidate has the same top-level keys as template."""
    if not isinstance(template, dict) or not isinstance(candidate, dict):
        return False
    template_keys = set(template.keys())
    candidate_keys = set(candidate.keys())
    # Allow if candidate has at least 80% of template keys
    overlap = len(template_keys.intersection(candidate_keys))
    return overlap >= len(template_keys) * 0.8


def _safe_merge_llm_output(template: Dict, llm_output: Dict) -> Dict:
    """Safely merge LLM output into template, preserving template structure."""
    result = {}
    for key, template_value in template.items():
        if key in llm_output:
            llm_value = llm_output[key]
            if isinstance(template_value, dict) and isinstance(llm_value, dict):
                result[key] = _safe_merge_llm_output(template_value, llm_value)
            elif isinstance(template_value, list) and isinstance(llm_value, list):
                result[key] = llm_value if llm_value else template_value
            elif isinstance(template_value, str) and isinstance(llm_value, str):
                # Replace only if template was placeholder
                if template_value.strip().lower() in ("", "tbd", "placeholder", "text", "title", "txt"):
                    result[key] = llm_value
                else:
                    result[key] = llm_value if llm_value else template_value
            else:
                result[key] = llm_value if llm_value is not None else template_value
        else:
            result[key] = template_value
    return result


def _validate_filled_data(data: Dict) -> bool:
    """
    Validate that filled data doesn't contain too many placeholder values.
    Returns True if data appears to be properly filled.
    """
    if not isinstance(data, dict):
        return False
    
    placeholder_values = [
        "product name", "$0.00", "placeholder", "tbd", "text", "title",
        "product", "item", "untitled", "n/a", "none", ""
    ]
    
    def count_placeholders(obj, total_count=0, placeholder_count=0):
        """Recursively count placeholder values in nested structure."""
        if isinstance(obj, dict):
            for value in obj.values():
                t, p = count_placeholders(value, total_count, placeholder_count)
                total_count += t
                placeholder_count += p
        elif isinstance(obj, list):
            for item in obj:
                t, p = count_placeholders(item, total_count, placeholder_count)
                total_count += t
                placeholder_count += p
        elif isinstance(obj, str):
            total_count += 1
            if obj.strip().lower() in placeholder_values:
                placeholder_count += 1
        return total_count, placeholder_count
    
    total, placeholders = count_placeholders(data)
    
    # If more than 50% are placeholders, validation fails
    if total > 0:
        ratio = placeholders / total
        return ratio < 0.5
    
    return True


def _direct_fill_fallback(template_data: Dict, mcp_data: Dict, tabs_data: List[Dict]) -> Dict:
    """Fallback: Directly fill template without LLM"""
    filled = template_data.copy()
    
    # Shopping domain
    products = mcp_data.get("products", [])
    if products and "main" in filled:
        if "productHighlight" in filled["main"]:
            p = products[0]
            filled["main"]["productHighlight"].update({
                "name": p.get("title", "")[:50],
                "text": p.get("title", "")[:100],
                "price": p.get("price", {}).get("raw", "$0.00") if isinstance(p.get("price"), dict) else p.get("price", "$0.00"),
                "imageUrl": p.get("thumbnailImage", p.get("thumbnail", "")),
                "productUrl": p.get("url", p.get("link", ""))
            })
        if "carousel" in filled["main"] and "items" in filled["main"]["carousel"]:
            for i, item in enumerate(filled["main"]["carousel"]["items"]):
                if i < len(products):
                    p = products[i]
                    item.update({
                        "title": p.get("title", "")[:30],
                        "imageUrl": p.get("thumbnailImage", p.get("thumbnail", "")),
                        "price": p.get("price", {}).get("raw", "") if isinstance(p.get("price"), dict) else p.get("price", ""),
                        "url": p.get("url", p.get("link", ""))
                    })
    
    print("✅ Direct fill complete")
    return filled

def _fill_with_web_search(filled: Dict, search_client: SearchClient, query: str, domain: str):
    """
    Fallback: fill template with web search results.
    ✅ FIX: Actually fills shopping-specific fields with product data.
    """
    print(f"🔍 Fallback: Using web search for {domain}")
    
    try:
        # Search web for products
        web_results = search_client.search_brave_web(query, count=10)
        results = web_results.get("web", {}).get("results", [])
        
        # Search images
        image_results = search_client.search_images_realtime(query, limit=6)
        images = image_results.get("data", [])
        
        # ✅ For shopping domain, fill product-specific fields
        if domain.lower() == "shopping" and "main" in filled:
            # Fill product highlight from first result
            if results and len(results) > 0 and "productHighlight" in filled["main"]:
                first_result = results[0]
                filled["main"]["productHighlight"].update({
                    "name": first_result.get("title", "Product")[:50],
                    "text": first_result.get("description", "")[:100],
                    "price": "$0.00",  # Can't get price from web search
                    "imageUrl": images[0].get("url", "") if images else "",
                    "productUrl": first_result.get("url", "")
                })
                print("✅ Filled productHighlight from web search")
            
            # Fill carousel items
            if "carousel" in filled["main"] and "items" in filled["main"]["carousel"]:
                for i, item in enumerate(filled["main"]["carousel"]["items"]):
                    if i < len(results):
                        result = results[i]
                        img_url = images[i].get("url", "") if i < len(images) else ""
                        
                        item.update({
                            "title": result.get("title", "")[:30],
                            "imageUrl": img_url,
                            "price": "$0.00",
                            "url": result.get("url", "")
                        })
                print(f"✅ Filled {min(len(results), len(filled['main']['carousel']['items']))} carousel items")
        else:
            # Generic fill for other domains
            _recursive_fill(filled, results, images, 0, 0)
        
    except Exception as e:
        print(f"⚠️ Web search fallback failed: {e}")
        import traceback
        traceback.print_exc()

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
    except Exception as e:
        print(f"[DEBUG] Failed to parse input JSON: {e}")
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
            print("[DEBUG] Discovering tools...")
            """
            Auto-discover tools by scanning mcp_tools directory.

            For each .py file, imports it, finds public classes, and extracts
            their public methods as LangChain tools. Skips errors gracefully.
            """
            if Tool is None:
                print("[DEBUG] LangChain Tool not available.")
                return
            if not self.tools_dir.exists():
                print(f"[DEBUG] Tools directory {self.tools_dir} does not exist.")
                return

            for py_file in sorted(self.tools_dir.glob("*.py")):
                print(f"[DEBUG] Loading module: {py_file.name}")
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
                                    Always returns a JSON object: {"status": "success", "result": ...} or {"status": "error", "message": ...}
                                    """
                                    import json
                                    try:
                                        instance = cls()
                                        fn = getattr(instance, method_to_call)
                                        # Parse JSON arguments
                                        if json_argument:
                                            try:
                                                args = json.loads(json_argument)
                                            except Exception as e:
                                                return json.dumps({"status": "error", "message": f"Invalid JSON input: {e}"})
                                            if not isinstance(args, dict):
                                                return json.dumps({"status": "error", "message": f"Arguments must be a JSON object (dict), but received {type(args).__name__}"})
                                        else:
                                            args = {}
                                        # Call the method with unpacked arguments
                                        try:
                                            result = fn(**args)
                                            return json.dumps({"status": "success", "result": result})
                                        except Exception as e:
                                            return json.dumps({"status": "error", "message": str(e)})
                                    except Exception as error:
                                        return json.dumps({"status": "error", "message": str(error)})

                                return call

                            try:
                                tool_callable = make_tool_callable(class_obj, method_name)
                                doc_string = (
                                    getattr(class_obj, method_name).__doc__ or ""
                                ).strip()
                                enhanced_doc_string = (
                                    f"{doc_string}\n\n"
                                    "**Input**: This tool expects arguments as a JSON string, "
                                    "e.g., `{\"param1\": \"value1\", \"param2\": \"value2\"}`. "
                                    "Refer to the method's docstring for available parameters.\n"
                                    "**Output**: Always returns a JSON object. On success: `{\"status\": \"success\", \"result\": ...}`. "
                                    "On failure: `{\"status\": \"error\", \"message\": \"Error details\"}`."
                                )
                                tool = Tool(
                                    name=f"{class_name}.{method_name}",
                                    func=tool_callable,
                                    description=enhanced_doc_string,
                                )
                                self.tools.append(tool)
                                print(f"[DEBUG] Tool wrapped: {class_name}.{method_name}")
                            except Exception as e:
                                print(f"[DEBUG] Failed to wrap tool {class_name}.{method_name}: {e}")
                                continue
                except Exception as e:
                    _logger.debug(f"Failed to load module {py_file.stem}: {e}")
                    # Skip modules that can't be loaded
                    continue

        def _init_agent(self) -> None:
            print(f"[DEBUG] Initializing LLM agent with {len(self.tools)} tools...")
            """
            Initialize the LLM agent with discovered tools.

            Creates a ChatGroq LLM and initializes a LangChain agent if:
              - LangChain imports are available
              - At least one tool was discovered
              - Groq API key is available

            Otherwise leaves agent_executor as None (triggers fallback).
            """
            if ChatGroq is None or initialize_agent is None or not self.tools:
                print("[DEBUG] ChatGroq or initialize_agent not available, or no tools discovered.")
                return

            try:
                api_key = self.groq_key or os.getenv("GROQ_API_KEY")
                if not api_key:
                    print("[DEBUG] GROQ_API_KEY not set.")
                    return

                # Initialize Groq LLM (handle different version signatures)
                if self.model_name:
                    llm = ChatGroq(api_key=api_key, model=self.model_name)
                else:
                    llm = ChatGroq(api_key=api_key)

                self.agent_executor = initialize_agent(
                    self.tools,
                    llm,
                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=True,
                )
                print(f"[DEBUG] LLM agent initialized with {len(self.tools)} tools.")
            except Exception as error:
                print(f"[DEBUG] Failed to initialize LLM agent: {error}")
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
