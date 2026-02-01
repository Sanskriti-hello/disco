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
    
    def prepare_template_data(
        self, 
        template_id: str, 
        mcp_data: Dict[str, Any], 
        llm_response: str
    ) -> Dict[str, Any]:
        """Transform MCP data for template-specific rendering"""
        
        if template_id == "code-1":
            # Code terminal template
            return {
                "title": "Code Assistant",
                "code_snippets": self._extract_code_from_tabs_and_search(mcp_data),
                "documentation": self._extract_documentation(mcp_data),
                "terminal_output": llm_response,
                "related_repos": self._extract_github_repos(mcp_data)
            }
        else:
            # Fallback to generic template
            return {
                "title": "Code Dashboard",
                "links": self._extract_code_links(mcp_data),
                "summary": llm_response
            }
    
    def _extract_code_from_tabs_and_search(self, mcp_data: Dict) -> List[Dict]:
        """Extract code snippets from browser tabs and search results"""
        snippets = []
        
        # From LLM response
        snippets.extend(self._extract_code_from_response(mcp_data.get("tab_summary", "")))
        
        # From search results
        if "search" in mcp_data:
            for result in mcp_data["search"].get("results", [])[:3]:
                snippet_text = result.get("snippet", "")
                if "```" in snippet_text or any(kw in snippet_text for kw in ["function", "def ", "class ", "import "]):
                    snippets.append({
                        "language": "python",
                        "code": snippet_text[:200],
                        "filename": result.get("title", "snippet.py"),
                        "explanation": result.get("title", "")
                    })
        
        # Default snippet if none found
        if not snippets:
            snippets.append({
                "language": "python",
                "code": "# No code found in your tabs\n# Open some code-related pages to see snippets here",
                "filename": "welcome.py",
                "explanation": "Start exploring code!"
            })
        
        return snippets[:5]
    
    def _extract_documentation(self, mcp_data: Dict) -> List[Dict]:
        """Extract documentation links from search and browser"""
        docs = []
        
        if "search" in mcp_data:
            for result in mcp_data["search"].get("results", [])[:5]:
                if any(site in result.get("url", "") for site in ["docs.", "developer.", "api."]):
                    docs.append({
                        "title": result.get("title", "Documentation"),
                        "content": result.get("snippet", ""),
                        "url": result.get("url", "")
                    })
        
        if "browser" in mcp_data:
            for tab in mcp_data["browser"].get("tabs", []):
                if any(site in tab.get("url", "") for site in ["github.com", "stackoverflow.com", "docs."]):
                    docs.append({
                        "title": tab.get("title", "Tab"),
                        "content": tab.get("content", "")[:150],
                        "url": tab.get("url", "")
                    })
        
        return docs[:10]
    
    def _extract_github_repos(self, mcp_data: Dict) -> List[Dict]:
        """Extract GitHub repository links"""
        repos = []
        
        if "browser" in mcp_data:
            for tab in mcp_data["browser"].get("tabs", []):
                if "github.com" in tab.get("url", ""):
                    repos.append({
                        "name": tab.get("title", "Repository"),
                        "url": tab.get("url", ""),
                        "stars": 0  # Could be enhanced with GitHub API
                    })
        
        return repos[:5]
    
    def _extract_code_links(self, mcp_data: Dict) -> List[Dict]:
        """Extract code-related links for generic template"""
        links = []
        
        if "browser" in mcp_data:
            for tab in mcp_data["browser"].get("tabs", [])[:10]:
                links.append({
                    "title": tab.get("title", "Tab"),
                    "url": tab.get("url", ""),
                    "summary": tab.get("content", "")[:200],
                    "domain": tab.get("url", "").split("/")[2] if "/" in tab.get("url", "") else ""
                })
        
        return links