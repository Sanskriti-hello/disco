"""
Amazon MCP Client
==================
A reusable module for interacting with Real-Time Amazon Data API via RapidAPI.

Functions:
    - search_products: Search for products on Amazon
    - get_product_details: Get detailed information about a specific product
    - get_product_offers: Get offers/deals for a product
    - get_product_reviews: Get reviews for a product with filtering options
    - get_review_details: Get details of a specific review
    - get_top_reviews: Get top reviews for a product

Usage:
    from backend.mcp.amazon import AmazonClient
    
    client = AmazonClient(api_key="your_api_key")
    results = client.search_products("laptop", country="US")
"""

import os
import http.client
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class SortBy(Enum):
    """Sort options for product reviews."""
    TOP_REVIEWS = "TOP_REVIEWS"
    MOST_RECENT = "MOST_RECENT"


class StarRating(Enum):
    """Star rating filter options."""
    ALL = "ALL"
    FIVE_STAR = "5_STARS"
    FOUR_STAR = "4_STARS"
    THREE_STAR = "3_STARS"
    TWO_STAR = "2_STARS"
    ONE_STAR = "1_STAR"
    POSITIVE = "POSITIVE"
    CRITICAL = "CRITICAL"


@dataclass
class AmazonConfig:
    """Configuration for Amazon API client."""
    api_key: str
    host: str = "real-time-amazon-data.p.rapidapi.com"
    default_country: str = "IN"


class AmazonClient:
        def llm_search_products(self, payload: str) -> dict:
            """LLM adapter: Search products. Payload: {"query": str, "country": str, "page": int, "sort_by": str, "category_id": str}"""
            import json
            try:
                args = json.loads(payload)
                result = self.search_products(
                    args["query"],
                    args.get("country"),
                    int(args.get("page", 1)),
                    args.get("sort_by"),
                    args.get("category_id")
                )
                return {"status": "success", "result": result}
            except Exception as e:
                return {"status": "error", "message": str(e)}
    """
    Client for the Real-Time Amazon Data API.
    
    This client provides methods to search products, get product details,
    reviews, and offers from Amazon.
    
    Example:
        client = AmazonClient(api_key="your_rapidapi_key")
        products = client.search_products("wireless headphones")
        print(products)
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[AmazonConfig] = None):
        """
        Initialize the Amazon API client.
        
        Args:
            api_key: RapidAPI key. If not provided, reads from RAPIDAPI_KEY env variable.
            config: Optional AmazonConfig object for advanced configuration.
        """
        if config:
            self.config = config
        else:
            key = api_key or os.getenv("RAPIDAPI_KEY")
            if not key:
                raise ValueError(
                    "API key is required. Provide it via api_key parameter "
                    "or set the RAPIDAPI_KEY environment variable."
                )
            self.config = AmazonConfig(api_key=key)
        
        self._headers = {
            "x-rapidapi-key": self.config.api_key,
            "x-rapidapi-host": self.config.host,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an HTTP GET request to the Amazon API.
        
        Args:
            endpoint: API endpoint path (e.g., "/search")
            params: Query parameters as a dictionary
            
        Returns:
            JSON response as a dictionary
            
        Raises:
            ConnectionError: If the request fails
            ValueError: If the response is not valid JSON
        """
        conn = http.client.HTTPSConnection(self.config.host)
        
        # Build query string
        query_string = ""
        if params:
            query_parts = []
            for key, value in params.items():
                if value is not None:
                    # Handle enum values
                    if isinstance(value, Enum):
                        value = value.value
                    # Handle boolean values
                    if isinstance(value, bool):
                        value = str(value).lower()
                    query_parts.append(f"{key}={value}")
            query_string = "?" + "&".join(query_parts)
        
        url = f"{endpoint}{query_string}"
        
        try:
            conn.request("GET", url, headers=self._headers)
            response = conn.getresponse()
            data = response.read().decode("utf-8")
            
            if response.status != 200:
                return {
                    "status": "error",
                    "error_code": response.status,
                    "message": data
                }
            
            return json.loads(data)
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid JSON response: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Request failed: {str(e)}"}
        finally:
            conn.close()
    
    def search_products(
        self,
        query: str,
        country: Optional[str] = None,
        page: int = 1,
        sort_by: Optional[str] = None,
        category_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for products on Amazon.
        
        Args:
            query: Search query string
            country: Country code (default: "US")
            page: Page number for pagination (default: 1)
            sort_by: Sort option (e.g., "RELEVANCE", "PRICE_LOW_TO_HIGH")
            category_id: Optional category ID to filter results
            
        Returns:
            Dictionary containing search results with products list
            
        Example:
            results = client.search_products("laptop", country="US", page=1)
            for product in results.get("data", {}).get("products", []):
                print(product["product_title"])
        """
        params = {
            "query": query,
            "country": country or self.config.default_country,
            "page": page,
        }
        if sort_by:
            params["sort_by"] = sort_by
        if category_id:
            params["category_id"] = category_id
        
        return self._make_request("/search", params)
    
    def get_product_details(
        self,
        asin: str,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific product.
        
        Args:
            asin: Amazon Standard Identification Number (product ID)
            country: Country code (default: "US")
            
        Returns:
            Dictionary containing product details
            
        Example:
            details = client.get_product_details("B07ZPKN6YR")
            print(details.get("data", {}).get("product_title"))
        """
        params = {
            "asin": asin,
            "country": country or self.config.default_country
        }
        return self._make_request("/product-details", params)
    
    def get_product_offers(
        self,
        asin: str,
        country: Optional[str] = None,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get offers/deals for a specific product.
        
        Args:
            asin: Amazon Standard Identification Number (product ID)
            country: Country code (default: "US")
            page: Page number for pagination (default: 1)
            
        Returns:
            Dictionary containing product offers
            
        Example:
            offers = client.get_product_offers("B07ZPKN6YR")
            for offer in offers.get("data", {}).get("offers", []):
                print(offer["price"])
        """
        params = {
            "asin": asin,
            "country": country or self.config.default_country,
            "page": page
        }
        return self._make_request("/product-offers", params)
    
    def get_product_reviews(
        self,
        asin: str,
        country: Optional[str] = None,
        page: int = 1,
        sort_by: SortBy = SortBy.TOP_REVIEWS,
        star_rating: StarRating = StarRating.ALL,
        verified_purchases_only: bool = False,
        images_or_videos_only: bool = False,
        current_format_only: bool = False
    ) -> Dict[str, Any]:
        """
        Get reviews for a specific product with filtering options.
        
        Args:
            asin: Amazon Standard Identification Number (product ID)
            country: Country code (default: "US")
            page: Page number for pagination (default: 1)
            sort_by: Sort order for reviews (default: TOP_REVIEWS)
            star_rating: Filter by star rating (default: ALL)
            verified_purchases_only: Only show verified purchases (default: False)
            images_or_videos_only: Only show reviews with media (default: False)
            current_format_only: Only show current format reviews (default: False)
            
        Returns:
            Dictionary containing product reviews
            
        Example:
            reviews = client.get_product_reviews(
                "B07ZPKN6YR",
                sort_by=SortBy.MOST_RECENT,
                star_rating=StarRating.FIVE_STAR
            )
            for review in reviews.get("data", {}).get("reviews", []):
                print(review["review_title"])
        """
        params = {
            "asin": asin,
            "country": country or self.config.default_country,
            "page": page,
            "sort_by": sort_by,
            "star_rating": star_rating,
            "verified_purchases_only": verified_purchases_only,
            "images_or_videos_only": images_or_videos_only,
            "current_format_only": current_format_only
        }
        return self._make_request("/product-reviews", params)
    
    def get_review_details(
        self,
        review_id: str,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get details of a specific review.
        
        Args:
            review_id: The Amazon review ID
            country: Country code (default: "US")
            
        Returns:
            Dictionary containing review details
            
        Example:
            review = client.get_review_details("R2FZOU359SHU21")
            print(review.get("data", {}).get("review_text"))
        """
        params = {
            "review_id": review_id,
            "country": country or self.config.default_country
        }
        return self._make_request("/product-review-details", params)
    
    def get_top_reviews(
        self,
        asin: str,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get top reviews for a specific product.
        
        Args:
            asin: Amazon Standard Identification Number (product ID)
            country: Country code (default: "US")
            
        Returns:
            Dictionary containing top reviews
            
        Example:
            top_reviews = client.get_top_reviews("B07ZPKN6YR")
            for review in top_reviews.get("data", {}).get("reviews", []):
                print(review["review_title"])
        """
        params = {
            "asin": asin,
            "country": country or self.config.default_country
        }
        return self._make_request("/top-product-reviews", params)


# ============================================================================
# Convenience Functions (for direct import without instantiating client)
# ============================================================================

_default_client: Optional[AmazonClient] = None


def _get_client(api_key: Optional[str] = None) -> AmazonClient:
    """Get or create a default client instance."""
    global _default_client
    if _default_client is None:
        _default_client = AmazonClient(api_key=api_key)
    return _default_client


def search_products(
    query: str,
    country: str = "US",
    page: int = 1,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for products on Amazon.
    
    This is a convenience function that uses a default client instance.
    For more control, use the AmazonClient class directly.
    """
    return _get_client(api_key).search_products(query, country, page)


def get_product_details(
    asin: str,
    country: str = "US",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get product details by ASIN.
    
    This is a convenience function that uses a default client instance.
    """
    return _get_client(api_key).get_product_details(asin, country)


def get_product_reviews(
    asin: str,
    country: str = "US",
    page: int = 1,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get product reviews by ASIN.
    
    This is a convenience function that uses a default client instance.
    """
    return _get_client(api_key).get_product_reviews(asin, country, page)


def get_top_reviews(
    asin: str,
    country: str = "US",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get top reviews for a product by ASIN.
    
    This is a convenience function that uses a default client instance.
    """
    return _get_client(api_key).get_top_reviews(asin, country)


# ============================================================================
# Example usage (only runs when executed directly)
# ============================================================================

if __name__ == "__main__":
    # Example: Test the client
    import os
    
    # You can set your API key as an environment variable
    # export RAPIDAPI_KEY="your_key_here"
    
    api_key = os.getenv("RAPIDAPI_KEY")
    
    if api_key:
        client = AmazonClient(api_key=api_key)
        
        # Search for products
        print("Searching for 'wireless headphones'...")
        results = client.search_products("wireless headphones", country="US")
        print(json.dumps(results, indent=2)[:500])
        
        # Get product reviews
        print("\nGetting reviews for sample ASIN...")
        reviews = client.get_product_reviews("B07ZPKN6YR")
        print(json.dumps(reviews, indent=2)[:500])
    else:
        print("Please set RAPIDAPI_KEY environment variable to test.")
        print("\nAvailable functions:")
        print("  - AmazonClient(api_key).search_products(query)")
        print("  - AmazonClient(api_key).get_product_details(asin)")
        print("  - AmazonClient(api_key).get_product_offers(asin)")
        print("  - AmazonClient(api_key).get_product_reviews(asin)")
        print("  - AmazonClient(api_key).get_review_details(review_id)")
        print("  - AmazonClient(api_key).get_top_reviews(asin)")
