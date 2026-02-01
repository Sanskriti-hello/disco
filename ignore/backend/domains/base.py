from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import os

# Import MCP Tools for data fetching
# MCP Tools will be imported lazily in fetch_mcp_data

@dataclass
class DomainResponse:
    """Standardized response from a domain agent."""
    ui_template: str
    ui_props: Dict[str, Any]
    needs_more_data: bool = False
    follow_up_question: Optional[str] = None
    mcp_results: Dict[str, Any] = field(default_factory=dict)

class BaseDomain:
    """Base class for all domain-specific logic."""
    
    def get_required_mcps(self, user_prompt: str) -> List[str]:
        """Identify which MCP tools are needed for this query."""
        return ["browser"]  # Default
    
    async def process(self, user_prompt: str, browser_data: Dict[str, Any], access_token: Optional[str] = None) -> DomainResponse:
        """Main entry point for domain processing."""
        
        # 1. Get required MCPs
        required_mcps = self.get_required_mcps(user_prompt)
        
        # 2. Fetch MCP Data
        mcp_data = self.fetch_mcp_data(required_mcps, user_prompt, browser_data, access_token)
        mcp_data["timestamp"] = datetime.now().isoformat()
        mcp_data["browser"] = browser_data
        mcp_data["tab_summary"] = self.summarize_tabs(browser_data.get("tabs", []))
        
        # 3. Validate
        if not self.validate_data(mcp_data):
            return DomainResponse(
                ui_template="FollowUpQuestion",
                ui_props={"question": self.get_follow_up_question(mcp_data)},
                needs_more_data=True,
                follow_up_question=self.get_follow_up_question(mcp_data),
                mcp_results=mcp_data
            )
        
        # 4. Generate LLM Summary/Response (Simulated for now)
        llm_response = self.generate_llm_response(user_prompt, mcp_data)
        
        # 5. Select UI template & Prepare Props
        template = self.select_ui_template(mcp_data)
        props = self.prepare_ui_props(mcp_data, llm_response)
        
        return DomainResponse(
            ui_template=template,
            ui_props=props,
            mcp_results=mcp_data
        )

    def fetch_mcp_data(self, mcps: List[str], prompt: str, browser: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch data from all required MCP tools."""
        results = {}
        
        for mcp in mcps:
            try:
                if mcp == "search":
                    from mcp_tools.search import SearchClient
                    results["search"] = SearchClient().web_search(prompt)
                elif mcp == "location":
                    from mcp_tools.Loc_Weath_Dis import places_search
                    results["location"] = places_search(prompt)
                elif mcp == "weather":
                    from mcp_tools.Loc_Weath_Dis import lookup_weather
                    # For weather, we normally need coordinates. Mocking for now.
                    results["weather"] = lookup_weather(28.6139, 77.2090) 
                elif mcp == "google_workspace":
                    from mcp_tools.google_workspace import GoogleWorkspaceMCP
                    client = GoogleWorkspaceMCP(access_token=token)
                    results["google_workspace"] = {
                        "calendar": client.get_calendar_events(),
                        "gmail": client.search_gmail("is:unread"),
                        "drive": client.search_drive(prompt)
                    }
                elif mcp == "youtube":
                    from mcp_tools.youtube import YouTubeMCP
                    client = YouTubeMCP(access_token=token)
                    results["youtube"] = client.search_videos(prompt)
                elif mcp == "amazon":
                    from mcp_tools.amazon import AmazonClient
                    results["amazon"] = AmazonClient().search_products(prompt)
                elif mcp == "spotify":
                    from mcp_tools.spotify import SpotifyClient
                    results["spotify"] = SpotifyClient().search(prompt)
                elif mcp == "movie":
                    from mcp_tools.movie import MovieClient
                    results["movie"] = MovieClient().search_by_title(title=prompt)
                elif mcp == "news":
                    from mcp_tools.news import NewsClient
                    results["news"] = NewsClient().search_news(prompt)
                elif mcp == "financial":
                    from mcp_tools.exchange_rate import FinancialClient
                    results["financial"] = FinancialClient().convert_currency("USD", "INR", 1.0)
                elif mcp == "arxiv":
                    from mcp_tools.arxiv import ArxivClient
                    results["arxiv"] = ArxivClient().search_papers(prompt)
            except Exception as e:
                print(f"Error fetching {mcp}: {e}")
                results[mcp] = {"error": str(e)}
        
        return results

    def summarize_tabs(self, tabs: List[Dict[str, Any]]) -> str:
        """Create a concise text summary of all open tabs."""
        if not tabs:
            return "No tabs are currently open."
        
        summaries = []
        for i, tab in enumerate(tabs[:15]): # Limit to top 15
            title = tab.get("title", "Untitled")
            url = tab.get("url", "")
            summaries.append(f"[{i+1}] {title} ({url})")
            
        return "Browser Context Summary:\n" + "\n".join(summaries)

    def generate_llm_response(self, prompt: str, data: Dict[str, Any]) -> str:
        """Summarize all context data into a core message."""
        tabs = data.get("browser", {}).get("tabs", [])
        return f"I've analyzed your {len(tabs)} tabs and gathered real-time info from APIs to help with your request: '{prompt}'."

    def select_ui_template(self, mcp_data: Dict[str, Any]) -> str:
        """Logic to select the best UI template."""
        return "GenericDashboard"

    def prepare_ui_props(self, mcp_data: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        """Transform raw MCP data into UI properties."""
        return {
            "response": llm_response,
            "data": mcp_data
        }

    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        """Check if required data is present."""
        return True

    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
        """Question to ask if data is missing."""
        return "Can you provide more information or clarify your request?"
    
    def prepare_template_data(
        self, 
        template_id: str, 
        mcp_data: Dict[str, Any], 
        llm_response: str
    ) -> Dict[str, Any]:
        """
        Transform MCP data to match specific template requirements.
        This should be overridden by subclasses for template-specific formatting.
        
        Args:
            template_id: ID of selected template (e.g., "code-1", "shopping-1")
            mcp_data: Raw data from MCP tools
            llm_response: Generated summary/response text
        
        Returns: Dictionary matching the template's data schema
        """
        # Default implementation - subclasses should override
        return {
            "title": llm_response,
            "items": [],
            "data": mcp_data
        }
