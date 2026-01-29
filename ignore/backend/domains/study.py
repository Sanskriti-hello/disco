from typing import Dict, List, Any, Optional
from .base import BaseDomain

class StudyDomain(BaseDomain):
    """
    Supportive study assistant for researchers and students.
    """

    def get_required_mcps(self, user_prompt: str) -> List[str]:
        mcps = ["browser", "search"]
        prompt = user_prompt.lower()

        # Research focus
        if any(word in prompt for word in ["research", "paper", "arxiv", "science", "technical", "ml", "ai"]):
            mcps.append("arxiv")

        # Productivity/Docs
        if any(word in prompt for word in ["summarize", "notes", "write", "google", "drive", "doc", "calendar"]):
            mcps.append("google_workspace")
            
        # News for current events in research
        if any(word in prompt for word in ["news", "latest", "update", "current"]):
            mcps.append("news")

        return list(set(mcps))

    def select_ui_template(self, mcp_data: Dict[str, Any]) -> str:
        if "arxiv" in mcp_data and mcp_data["arxiv"].get("results"):
            return "PaperList"
        return "StudyDashboard"

    def prepare_ui_props(self, mcp_data: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        props = {
            "response": llm_response,
            "timestamp": mcp_data.get("timestamp", ""),
            "papers": [],
            "docs": [],
            "tabs": []
        }
        
        # ArXiv Papers
        if "arxiv" in mcp_data:
            props["papers"] = mcp_data["arxiv"].get("results", [])
            
        # Google Workspace (Drive & Calendar)
        if "google_workspace" in mcp_data:
            gw = mcp_data["google_workspace"]
            props["docs"] = gw.get("drive", [])
            props["calendar_events"] = gw.get("calendar", {}).get("events", [])
            
        # Web Search
        if "search" in mcp_data:
            props["web_context"] = mcp_data["search"].get("results", [])
            
        # News
        if "news" in mcp_data:
            props["news_updates"] = mcp_data["news"].get("results", [])

        # Tab Summary
        if "browser" in mcp_data:
            tabs = mcp_data["browser"].get("tabs", [])
            props["tabs_summary"] = [
                {"title": t.get("title"), "url": t.get("url")}
                for t in tabs[:10]
            ]
            
        return props

    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        return "browser" in mcp_data

    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
        return "What topic are you studying, or which documents should I help you summarize?"