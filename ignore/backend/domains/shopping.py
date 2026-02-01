from typing import Dict, List, Any, Optional
from .base import BaseDomain

class ShoppingDomain(BaseDomain):
    """
    Handles: product search, comparison, pricing, recommendation
    FIXED: Properly transforms Amazon/Search MCP data into UI props
    """

    def get_required_mcps(self, user_prompt: str) -> List[str]:
        mcps = ["browser", "search", "amazon"]
        prompt = user_prompt.lower()
        
        # Financial for currency conversion
        if any(word in prompt for word in ["usd", "eur", "convert", "currency", "price", "budget"]):
            mcps.append("financial")
            
        # Location for local stores
        if any(word in prompt for word in ["near", "nearby", "store", "offline", "local"]):
            mcps.append("location")
            mcps.append("weather")
        
        return list(set(mcps))

    def select_ui_template(self, mcp_data: Dict[str, Any]) -> str:
        if "amazon" in mcp_data and mcp_data["amazon"].get("data", {}).get("products"):
            return "ProductGrid"
        return "ShoppingDashboard"

    def prepare_ui_props(self, mcp_data: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        """
        FIXED: Actually extract Amazon product data properly
        """
        props = {
            "response": llm_response,
            "timestamp": mcp_data.get("timestamp", ""),
            "products": [],
            "context": {}
        }
        
        # ============================================================
        # FIX 1: Amazon Product Data - Extract real products
        # ============================================================
        if "amazon" in mcp_data:
            amazon_data = mcp_data["amazon"]
            
            # Handle Amazon API response structure
            products_list = amazon_data.get("data", {}).get("products", [])
            
            for product in products_list[:12]:  # Top 12 products
                props["products"].append({
                    "title": product.get("product_title", "Product"),
                    "name": product.get("product_title", "Product"),
                    "price": product.get("product_price", "N/A"),
                    "rating": product.get("product_star_rating", 0),
                    "reviews": product.get("product_num_ratings", 0),
                    "url": product.get("product_url", ""),
                    "image": product.get("product_photo", ""),
                    "asin": product.get("asin", ""),
                    "availability": product.get("product_availability", ""),
                    "prime": product.get("is_prime", False)
                })
        
        # ============================================================
        # FIX 2: Web Search - Add general shopping results
        # ============================================================
        if "search" in mcp_data:
            search_results = mcp_data["search"].get("results", [])
            props["web_context"] = []
            
            for result in search_results[:8]:
                # Add as supplementary products if no Amazon data
                if not props["products"]:
                    props["products"].append({
                        "title": result.get("title", "Item"),
                        "name": result.get("title", "Item"),
                        "price": "Check Store",
                        "url": result.get("url", ""),
                        "image": result.get("image", ""),
                        "snippet": result.get("snippet", "")
                    })
                
                props["web_context"].append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("snippet", "")
                })
        
        # ============================================================
        # FIX 3: Currency/Financial Info
        # ============================================================
        if "financial" in mcp_data:
            financial = mcp_data["financial"]
            props["currency_info"] = {
                "conversion": financial.get("conversion", {}),
                "rates": financial.get("rates", {})
            }
        
        # ============================================================
        # FIX 4: Location-based stores
        # ============================================================
        if "location" in mcp_data:
            loc_results = mcp_data["location"].get("results", [])
            if loc_results:
                props["user_location"] = {
                    "name": loc_results[0].get("name", ""),
                    "coordinates": loc_results[0].get("location", {})
                }
                
                # Nearby stores from amenities
                props["nearby_stores"] = []
                amenities = mcp_data["location"].get("amenities", {}).get("elements", [])
                for store in amenities[:5]:
                    props["nearby_stores"].append({
                        "name": store.get("tags", {}).get("name", "Local Store"),
                        "type": store.get("tags", {}).get("shop", "store"),
                        "address": store.get("tags", {}).get("addr:street", "")
                    })
        
        # ============================================================
        # FIX 5: Browser Context
        # ============================================================
        if "browser" in mcp_data:
            tabs = mcp_data["browser"].get("tabs", [])
            props["context"]["open_tabs_count"] = len(tabs)
            
            # Extract product names from tabs
            props["context"]["active_products"] = []
            for tab in tabs:
                title = tab.get("title", "")
                if any(site in tab.get("url", "") for site in ["amazon", "ebay", "walmart", "target"]):
                    props["context"]["active_products"].append(title)
        
        # ============================================================
        # CRITICAL: If no products found, create contextual placeholder
        # ============================================================
        if not props["products"]:
            # Try to infer what user was looking for
            search_query = ""
            if "browser" in mcp_data:
                tabs = mcp_data["browser"].get("tabs", [])
                if tabs:
                    # Get first shopping-related tab
                    for tab in tabs:
                        if any(word in tab.get("title", "").lower() for word in ["buy", "shop", "product", "price"]):
                            search_query = tab.get("title", "")
                            break
            
            props["products"].append({
                "title": "🛍️ Start Shopping",
                "name": "No products found yet",
                "price": "—",
                "url": "https://amazon.com",
                "snippet": f"Search for products to get started. {f'Based on: {search_query}' if search_query else ''}",
                "image": "",
                "source": "placeholder"
            })
        
        return props

    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        """
        FIXED: More lenient - can work with browser context alone
        """
        return "browser" in mcp_data

    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
        if "amazon" not in mcp_data and "search" not in mcp_data:
            return "What product are you looking for, and what's your budget?"
        return None
    
    def prepare_template_data(
        self, 
        template_id: str, 
        mcp_data: Dict[str, Any], 
        llm_response: str
    ) -> Dict[str, Any]:
        """Transform MCP data for template-specific rendering"""
        
        if template_id == "shopping-1":
            # E-commerce product grid template
            products = []
            
            # Extract Amazon products
            if "amazon" in mcp_data:
                amazon_data = mcp_data["amazon"]
                # Handle direct data or nested data structure
                products_list = []
                if "data" in amazon_data and "products" in amazon_data["data"]:
                    products_list = amazon_data["data"]["products"]
                elif "products" in amazon_data:
                    products_list = amazon_data["products"]
                
                print(f"DEBUG: Found {len(products_list)} products from Amazon MCP")
                
                for product in products_list[:12]:
                    products.append({
                        "title": product.get("product_title", "Product"),
                        "price": product.get("product_price", "N/A"),
                        "original_price": product.get("product_original_price"),
                        "rating": float(product.get("product_star_rating", "0") or 0),
                        "review_count": int(product.get("product_num_ratings", 0) or 0),
                        "url": product.get("product_url", ""),
                        "image_url": product.get("product_photo", ""),
                        "availability": product.get("product_availability", ""),
                        "features": product.get("product_details", [])[:3] if product.get("product_details") else []
                    })
            
            # Fallback to search results
            if not products and "search" in mcp_data:
                for result in mcp_data["search"].get("results", [])[:8]:
                    products.append({
                        "title": result.get("title", "Product"),
                        "price": "Check Store",
                        "rating": 0,
                        "review_count": 0,
                        "url": result.get("url", ""),
                        "image_url": "",
                        "availability": "Available",
                        "features": [result.get("snippet", "")[:100]]
                    })
            
            # Calculate price range
            price_range = None
            prices = []
            for p in products:
                price_str = p.get("price", "")
                # Try to extract numeric price
                import re
                price_match = re.search(r'[\d,]+\.?\d*', str(price_str))
                if price_match:
                    try:
                        prices.append(float(price_match.group().replace(',', '')))
                    except:
                        pass
            
            if prices:
                price_range = {"min": min(prices), "max": max(prices)}
            
            return {
                "title": "Product Comparison",
                "products": products,
                "price_range": price_range,
                "sort_by": "price",
                "show_comparison": True
            }
        else:
            # Fallback to generic template
            return {
                "title": "Shopping Dashboard",
                "links": [
                    {
                        "title": p.get("name", p.get("title", "Product")),
                        "url": p.get("url", ""),
                        "summary": f"{p.get('price', 'N/A')} - {p.get('snippet', '')}",
                        "domain": "shopping"
                    }
                    for p in self.prepare_ui_props(mcp_data, llm_response).get("products", [])
                ]
            }