from typing import Dict, List, Any, Optional
from .base import BaseDomain

class ShoppingDomain(BaseDomain):
    """
    Handles: product search, comparison, pricing, recommendation
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
            mcps.append("weather") # Might as well check weather for shopping trip
        
        return list(set(mcps))

    def select_ui_template(self, mcp_data: Dict[str, Any]) -> str:
        if "amazon" in mcp_data and mcp_data["amazon"].get("results"):
            return "ProductComparisonTable"
        return "ShoppingDashboard"

    def prepare_ui_props(self, mcp_data: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        props = {
            "response": llm_response,
            "timestamp": mcp_data.get("timestamp", ""),
            "products": [],
            "context": {}
        }
        
        # Amazon Data
        if "amazon" in mcp_data:
            amazon_data = mcp_data["amazon"]
            props["products"].extend(amazon_data.get("results", []))
            
        # Search Data (Web context)
        if "search" in mcp_data:
            props["web_context"] = mcp_data["search"].get("results", [])
            
        # Financial / Conversion
        if "financial" in mcp_data:
            props["currency_info"] = mcp_data["financial"]
            
        # Location
        if "location" in mcp_data:
            loc_results = mcp_data["location"].get("results", [])
            if loc_results:
                props["nearby_stores"] = mcp_data["location"].get("amenities", {}).get("elements", [])
                props["user_location"] = loc_results[0]

        # Browser Tabs Summary
        if "browser" in mcp_data:
            tabs = mcp_data["browser"].get("tabs", [])
            props["context"]["open_tabs_count"] = len(tabs)
            props["context"]["active_products"] = [t.get("title") for t in tabs if "amazon" in t.get("url", "") or "ebay" in t.get("url", "")]

        return props

    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        # Browser context is mandatory
        if "browser" not in mcp_data:
            return False
        # Search or Amazon is needed
        return "search" in mcp_data or "amazon" in mcp_data

    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
        if "browser" not in mcp_data:
            return "I need to see your browser context to help find products."
        return "What product or category are you looking for, and what's your budget?"