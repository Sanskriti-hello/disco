from typing import Dict, List, Any, Optional
from .base import BaseDomain

class GenericDomain(BaseDomain):
    """
    General-purpose assistant for all other queries.
    """

    def get_required_mcps(self, user_prompt: str) -> List[str]:
        mcps = ["browser", "search"]
        prompt = user_prompt.lower()
        
        # Location/Weather
        if any(word in prompt for word in ["weather", "near", "local", "where", "city", "time"]):
            mcps.extend(["location", "weather"])
            
        # News
        if any(word in prompt for word in ["news", "latest", "today", "happened"]):
            mcps.append("news")
            
        # Misc Work
        if any(word in prompt for word in ["email", "drive", "file", "calendar"]):
            mcps.append("google_workspace")
            
        return list(set(mcps))

    def select_ui_template(self, mcp_data: Dict[str, Any]) -> str:
        if "weather" in mcp_data and mcp_data["weather"]:
            return "WeatherDashboard"
        if "news" in mcp_data and mcp_data["news"].get("results"):
            return "NewsDashboard"
        if "search" in mcp_data and mcp_data["search"].get("results"):
            return "LinkGrid"
        return "SummaryView"

    def prepare_ui_props(self, mcp_data: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        props = {
            "response": llm_response,
            "timestamp": mcp_data.get("timestamp", ""),
            "items": [],
            "context": {}
        }

        # News
        if "news" in mcp_data and mcp_data["news"].get("results"):
            for item in mcp_data["news"]["results"]:
                props["items"].append({
                    "title": item.get("title"),
                    "description": item.get("snippet"),
                    "url": item.get("url"),
                    "source": item.get("source"),
                })

        # Search Results
        if "search" in mcp_data and mcp_data["search"].get("results"):
            for item in mcp_data["search"]["results"]:
                props["items"].append({
                    "title": item.get("title"),
                    "description": item.get("snippet"),
                    "url": item.get("link"),
                    "source": item.get("source"),
                })

        # Weather / Location
        if "weather" in mcp_data:
            props["weather"] = mcp_data["weather"]
        if "location" in mcp_data:
            loc_results = mcp_data["location"].get("results", [])
            if loc_results:
                props["location"] = loc_results[0]

        # Browser Data
        if "browser" in mcp_data:
            props["context"]["tabs"] = mcp_data["browser"].get("tabs", [])

        return props

    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        return "browser" in mcp_data

    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
        return "How can I help you today?"
    
    def prepare_template_data(
        self, 
        template_id: str, 
        mcp_data: Dict[str, Any], 
        llm_response: str
    ) -> Dict[str, Any]:
        """Transform MCP data for template-specific rendering"""
        
        # Extract items from various sources
        items = []
        
        # News items
        if "news" in mcp_data and mcp_data["news"].get("results"):
            for item in mcp_data["news"]["results"][:10]:
                items.append({
                    "title": item.get("title", "News"),
                    "url": item.get("url", ""),
                    "summary": item.get("snippet", ""),
                    "tags": ["news"],
                    "timestamp": item.get("published_at", "")
                })
        
        # Search results
        if "search" in mcp_data and mcp_data["search"].get("results"):
            for item in mcp_data["search"]["results"][:10]:
                items.append({
                    "title": item.get("title", "Result"),
                    "url": item.get("link", ""),
                    "summary": item.get("snippet", ""),
                    "tags": [],
                    "timestamp": ""
                })
        
        # Browser tabs
        if "browser" in mcp_data:
            for tab in mcp_data["browser"].get("tabs", [])[:10]:
                items.append({
                    "title": tab.get("title", "Tab"),
                    "url": tab.get("url", ""),
                    "summary": tab.get("content", "")[:200],
                    "domain": tab.get("url", "").split("/")[2] if "/" in tab.get("url", "") else "",
                    "tags": []
                })
        
        if template_id == "generic-2":
            # Yellow search dashboard
            return {
                "title": f"Dashboard ({len(items)} items)",
                "items": items,
                "search_enabled": True,
                "categories": ["All", "News", "Search", "Tabs"],
                "total_count": len(items)
            }
        elif template_id == "generic-1":
            # Blue link collection
            return {
                "title": "Your Collection",
                "links": items,
                "category": "general",
                "total_tabs": len(items)
            }
        else:
            # Default fallback
            return {
                "title": llm_response[:50] if llm_response else "Dashboard",
                "items": items
            }