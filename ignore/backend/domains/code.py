from typing import Dict, List, Any, Optional
import re
from .base import BaseDomain

class CodeDomain(BaseDomain):
    """
    Expert programming assistant for debugging and development.
    """

    def get_required_mcps(self, user_prompt: str) -> List[str]:
        mcps = ["browser", "search"]
        prompt = user_prompt.lower()
        
        # Documentation & Notes
        if any(word in prompt for word in ["doc", "note", "save", "explain", "google", "drive"]):
            mcps.append("google_workspace")
            
        return list(set(mcps))

    def select_ui_template(self, mcp_data: Dict[str, Any]) -> str:
        return "CodeSnippet"

    def prepare_ui_props(self, mcp_data: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        props = {
            "response": llm_response,
            "timestamp": mcp_data.get("timestamp", ""),
            "code_snippets": self._extract_code_from_response(llm_response),
            "web_docs": [],
            "project_notes": []
        }
        
        # Web Search Data
        if "search" in mcp_data:
            props["web_docs"] = mcp_data["search"].get("results", [])
            
        # Google Workspace Data
        if "google_workspace" in mcp_data:
            props["project_notes"] = mcp_data["google_workspace"].get("drive", [])
            
        # Browser Context
        if "browser" in mcp_data:
            tabs = mcp_data["browser"].get("tabs", [])
            props["related_tabs"] = [
                {"title": t.get("title"), "url": t.get("url")}
                for t in tabs if any(site in t.get("url", "") for site in ["github", "stackoverflow", "docs"])
            ]
            
        return props

    def _extract_code_from_response(self, llm_response: str) -> List[Dict[str, str]]:
        """Extract code blocks from LLM response."""
        snippets = []
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, llm_response, re.DOTALL)
        for language, code in matches:
            snippets.append({
                "language": language or "plaintext",
                "code": code.strip(),
            })
        return snippets

    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        return "browser" in mcp_data

    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
        return "What programming language or specific error are you working on?"