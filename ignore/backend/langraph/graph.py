"""
LangGraph Orchestrator - State machine definition
Updated to use TemplateRegistry for intelligent template selection
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from domains import get_domain, domain_exists


class AgentState(TypedDict):
    """State schema for the LangGraph agent"""
    user_prompt: str
    tabs: List[Dict[str, Any]]
    history: List[Dict[str, str]]
    
    domain_scores: Dict[str, float]
    primary_domain: Optional[str]
    tab_clusters: List[Dict[str, Any]]
    
    selected_template: Optional[str]
    template_data: Optional[Dict[str, Any]]
    react_code: Optional[str]
    widgets: List[Dict[str, Any]]
    error: Optional[str]


async def domain_logic_node(state: AgentState) -> AgentState:
    """Node: Execute domain-specific logic using BaseDomain architecture"""
    
    domain_name = state["primary_domain"]
    prompt = state["user_prompt"]
    tabs = state["tabs"]
    
    # Check if domain uses BaseDomain architecture
    if domain_exists(domain_name):
        try:
            # Use BaseDomain architecture
            domain = get_domain(domain_name)
            
            # Prepare MCP data (browser context)
            # 1. Identify required MCPs for this request
            required_mcps = domain.get_required_mcps(prompt)
            print(f"[{domain_name}] Required MCPs: {required_mcps}")

            # 2. Fetch MCP Data
            mcp_data = {
                "timestamp": datetime.now().isoformat(),
            }
            
            # --- Browser / Filesystem ---
            if "browser" in required_mcps:
                # In a real scenario, this comes from the extension, but we can augment it
                mcp_data["browser"] = {
                    "tabs": tabs,
                    "recent_searches": state.get("history", [])[:5] if state.get("history") else [],
                    "tab_count": len(tabs),
                    "domains": list(set(tab.get("url", "").split("/")[2] for tab in tabs if "url" in tab))
                }
                
            if "filesystem" in required_mcps:
                from backend.mcp.filesystem import filesystem_mcp
                mcp_data["filesystem"] = {
                    "files": filesystem_mcp.list_files(),
                    "current_path": filesystem_mcp.root_dir
                }

            # --- Search & Information ---
            if "search" in required_mcps:
                from backend.mcp.search import search_mcp
                mcp_data["search"] = search_mcp.search(prompt)

            if "news" in required_mcps:
                from backend.mcp.news import news_mcp
                mcp_data["news"] = news_mcp.get_top_headlines(query=prompt)

            if "arxiv" in required_mcps:
                from backend.mcp.arxiv import arxiv_mcp
                mcp_data["arxiv"] = arxiv_mcp.search_papers(prompt)
            
            # --- Location & Weather ---
            if "location" in required_mcps:
                from backend.mcp.location import location_mcp
                loc = location_mcp.get_current_location()
                mcp_data["location"] = loc
                
            if "weather" in required_mcps:
                from backend.mcp.location import location_mcp
                # Assuming simple look up for now, ideally passing lat/lon from location
                if "location" in mcp_data and "coordinates" in mcp_data["location"]:
                    lat, lon = mcp_data["location"]["coordinates"]
                    mcp_data["weather"] = location_mcp.get_weather(lat, lon)

            # --- Productivity (Google Workspace) ---
            if "google_workspace" in required_mcps:
                from backend.mcp.google_workspace import google_workspace_mcp
                mcp_data["google_workspace"] = {
                    "calendar": google_workspace_mcp.get_calendar_events(),
                    # Could also search drive if needed
                }
                
            # --- Shopping ---
            if "amazon" in required_mcps:
                from backend.mcp.amazon import amazon_mcp
                mcp_data["amazon"] = amazon_mcp.search_products(prompt)
                
            if "ebay" in required_mcps:
                # eBay existing script usage (mocking integration as simple function call)
                # Ideally refactor ebay.py to class, but for now assuming we use a wrapper
                # or just use our search MCP if ebay specific is complex
                mcp_data["ebay"] = [] 

            if "exchange_rate" in required_mcps:
                from backend.mcp.exchange_rate import exchange_rate_mcp
                # Mock conversion example
                mcp_data["exchange_rate"] = exchange_rate_mcp.convert(100, "USD", "INR")

            # --- Entertainment ---
            if "spotify" in required_mcps:
                from backend.mcp.spotify import spotify_mcp
                mcp_data["spotify"] = spotify_mcp.get_recommendations()
                
            if "youtube" in required_mcps:
                # Basic mock for now, could use backend.mcp.youtube if fully implemented
                mcp_data["youtube"] = {"results": []}

            
            # Prepare LLM response (summary of domain-specific insights)
            llm_response = f"Analyzing {len(tabs)} tabs for {domain_name} domain"
            
            # Process through domain
            domain_response = await domain.process(
                user_prompt=prompt,
                mcp_data=mcp_data,
                llm_response=llm_response
            )
            
            # Check if we need more data
            if domain_response.needs_more_data:
                return {
                    **state,
                    "error": domain_response.follow_up_question,
                    "selected_template": "FollowUpQuestion",
                    "template_data": {
                        "question": domain_response.follow_up_question,
                        "domain": domain_name
                    }
                }
            
            return {
                **state,
                "selected_template": domain_response.ui_template,
                "template_data": domain_response.ui_props,
                "widgets": [],
            }
            
        except Exception as e:
            print(f"Domain processing failed: {e}")
            return {
                **state,
                "error": f"Domain logic failed: {str(e)}",
                "primary_domain": "generic"
            }
    
    # Fallback to generic domain
    try:
        generic_domain = get_domain("generic")
        mcp_data = {
            "browser": {"tabs": tabs, "recent_searches": []},
            "timestamp": datetime.now().isoformat(),
        }
        llm_response = "Generic response based on your query"
        
        domain_response = await generic_domain.process(prompt, mcp_data, llm_response)
        
        return {
            **state,
            "selected_template": domain_response.ui_template,
            "template_data": domain_response.ui_props,
        }
    except Exception as e:
        return {
            **state,
            "error": f"All domain handlers failed: {str(e)}",
            "primary_domain": "generic"
        }


async def select_template_node(state: AgentState) -> AgentState:
    """
    Node: Choose final template using TemplateRegistry
    Uses keyword matching and semantic analysis to find best template
    """
    
    # If domain already selected a template, use it
    if state["selected_template"]:
        return state
    
    from backend.ui_templates.registry import TemplateRegistry
    
    # Extract keywords from tabs and prompt
    keywords = []
    
    # From user prompt
    if state.get("user_prompt"):
        keywords.extend(state["user_prompt"].lower().split())
    
    # From tab titles
    for tab in state.get("tabs", [])[:10]:
        title = tab.get("title", "").lower()
        keywords.extend(title.split())
    
    # From tab content (first 100 chars)
    for tab in state.get("tabs", [])[:5]:
        content = tab.get("content", "")[:100].lower()
        keywords.extend(content.split())
    
    # Remove common stop words
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "is", "are", "was", "were", "be", "been", "being", "have", "has",
        "had", "do", "does", "did", "will", "would", "should", "could", "may",
        "might", "must", "can", "this", "that", "these", "those", "with", "from"
    }
    keywords = [k for k in keywords if k not in stop_words and len(k) > 3]
    
    # Use registry to find best template
    registry = TemplateRegistry()
    best_template = registry.find_best_template(
        domain=state["primary_domain"],
        keywords=list(set(keywords))[:20],  # Unique keywords, max 20
        user_prompt=state.get("user_prompt", "")
    )
    
    print(f"✓ Selected template: {best_template} for domain {state['primary_domain']}")
    
    return {
        **state,
        "selected_template": best_template,
        "template_data": state.get("template_data", {})
    }


async def render_ui_node(state: AgentState) -> AgentState:
    """
    Node: Generate React/HTML code from template
    Fetches Figma design and converts to code
    """
    
    from backend.ui_templates.renderer import TemplateRenderer
    
    renderer = TemplateRenderer()
    
    try:
        react_code = await renderer.render(
            template=state["selected_template"],
            data=state["template_data"],
            domain=state["primary_domain"]
        )
        
        return {
            **state,
            "react_code": react_code
        }
        
    except Exception as e:
        print(f"UI rendering failed: {e}")
        return {
            **state,
            "error": f"UI rendering failed: {str(e)}",
            "react_code": None
        }


def build_graph() -> StateGraph:
    """Build the LangGraph state machine"""
    workflow = StateGraph(AgentState)
    
    # Define Nodes
    workflow.add_node("domain_logic", domain_logic_node)
    workflow.add_node("select_template", select_template_node)
    workflow.add_node("render", render_ui_node)
    
    # Define Edges
    workflow.set_entry_point("domain_logic")
    workflow.add_edge("domain_logic", "select_template")
    workflow.add_edge("select_template", "render")
    workflow.add_edge("render", END)
    
    return workflow.compile()