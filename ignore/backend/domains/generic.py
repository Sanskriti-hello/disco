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
        if "location" in mcp_data and "weather" in mcp_data:
            return "WeatherDashboard"
        return "GenericDashboard"

    def prepare_ui_props(self, mcp_data: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        props = {
            "response": llm_response,
            "timestamp": mcp_data.get("timestamp", ""),
            "search_results": [],
            "context": {}
        }
        
        # Search Results
        if "search" in mcp_data:
            props["search_results"] = mcp_data["search"].get("results", [])
            
        # Weather / Location
        if "weather" in mcp_data:
            props["weather"] = mcp_data["weather"]
        if "location" in mcp_data:
            loc_results = mcp_data["location"].get("results", [])
            if loc_results:
                props["location"] = loc_results[0]
                
        # News
        if "news" in mcp_data:
            props["news"] = mcp_data["news"].get("results", [])

        # Browser Data
        if "browser" in mcp_data:
            props["context"]["tabs"] = mcp_data["browser"].get("tabs", [])
            
        return props

    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        return "browser" in mcp_data

    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
        return "How can I help you today?"