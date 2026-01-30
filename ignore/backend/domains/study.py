from typing import Dict, List, Any, Optional
from .base import BaseDomain

class StudyDomain(BaseDomain):
    """
    Supportive study assistant for researchers and students.
    FIXED: Properly transforms MCP data into UI props
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
        """
        FIXED: Actually extract and transform MCP data properly
        """
        props = {
            "response": llm_response,
            "timestamp": mcp_data.get("timestamp", ""),
            "papers": [],
            "docs": [],
            "tabs": []
        }
        
        # ============================================================
        # FIX 1: ArXiv Papers - Extract actual paper data
        # ============================================================
        if "arxiv" in mcp_data:
            arxiv_results = mcp_data["arxiv"].get("results", [])
            
            # Transform ArXiv API response to UI format
            for paper in arxiv_results[:10]:  # Top 10 papers
                props["papers"].append({
                    "title": paper.get("title", "Untitled Paper"),
                    "authors": paper.get("authors", "Unknown"),
                    "summary": paper.get("summary", "")[:300],  # First 300 chars
                    "abstract": paper.get("summary", ""),
                    "published": paper.get("published", ""),
                    "url": paper.get("link", ""),
                    "pdf_url": paper.get("pdf_url", paper.get("link", "")),
                    "arxiv_id": paper.get("id", ""),
                    "categories": paper.get("categories", [])
                })
        
        # ============================================================
        # FIX 2: Web Search Results - Add related papers/articles
        # ============================================================
        if "search" in mcp_data:
            search_results = mcp_data["search"].get("results", [])
            
            # Add search results as supplementary papers
            for result in search_results[:5]:
                # Only add if looks like academic content
                title = result.get("title", "").lower()
                if any(word in title for word in ["paper", "research", "study", "analysis"]):
                    props["papers"].append({
                        "title": result.get("title", "Article"),
                        "authors": result.get("source", "Web Source"),
                        "summary": result.get("snippet", "")[:300],
                        "abstract": result.get("snippet", ""),
                        "url": result.get("url", ""),
                        "pdf_url": result.get("url", ""),
                        "source": "web_search"
                    })
        
        # ============================================================
        # FIX 3: Google Workspace - Real docs and calendar
        # ============================================================
        if "google_workspace" in mcp_data:
            gw = mcp_data["google_workspace"]
            
            # Drive documents
            drive_files = gw.get("drive", [])
            for file in drive_files[:10]:
                props["docs"].append({
                    "name": file.get("name", "Document"),
                    "url": file.get("webViewLink", ""),
                    "modified": file.get("modifiedTime", ""),
                    "owner": file.get("owner", "Unknown"),
                    "type": file.get("mimeType", "")
                })
            
            # Calendar events
            calendar = gw.get("calendar", {})
            props["calendar_events"] = []
            for event in calendar.get("events", [])[:5]:
                props["calendar_events"].append({
                    "summary": event.get("summary", "Event"),
                    "start": event.get("start", ""),
                    "location": event.get("location", ""),
                    "url": event.get("htmlLink", "")
                })
        
        # ============================================================
        # FIX 4: Browser Tabs Summary
        # ============================================================
        if "browser" in mcp_data:
            tabs = mcp_data["browser"].get("tabs", [])
            props["tabs_summary"] = []
            
            for tab in tabs[:10]:
                props["tabs_summary"].append({
                    "title": tab.get("title", "Tab"),
                    "url": tab.get("url", ""),
                    "content_preview": tab.get("content", "")[:100]
                })
        
        # ============================================================
        # FIX 5: News Updates
        # ============================================================
        if "news" in mcp_data:
            news_results = mcp_data["news"].get("results", [])
            props["news_updates"] = []
            
            for article in news_results[:5]:
                props["news_updates"].append({
                    "title": article.get("title", "News"),
                    "snippet": article.get("snippet", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", "Unknown"),
                    "published": article.get("published_at", "")
                })
        
        # ============================================================
        # CRITICAL: If no papers found, create placeholder with context
        # ============================================================
        if not props["papers"]:
            # Extract topics from browser tabs
            topics = []
            if "browser" in mcp_data:
                for tab in mcp_data["browser"].get("tabs", [])[:5]:
                    title = tab.get("title", "")
                    if title:
                        topics.append(title)
            
            context_summary = f"Based on your {len(topics)} open tabs"
            if topics:
                context_summary += f": {', '.join(topics[:3])}"
            
            props["papers"].append({
                "title": "📚 Research Context",
                "authors": "Your Browser Activity",
                "summary": context_summary + ". Use the search feature to find specific papers.",
                "url": "https://arxiv.org",
                "pdf_url": "",
                "source": "context"
            })
            
        return props

    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        """
        FIXED: More lenient validation - we can work with just browser context
        """
        # At minimum, need browser context
        return "browser" in mcp_data

    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
        if "arxiv" not in mcp_data and "search" not in mcp_data:
            return "What research topic or papers would you like to explore?"
        return None