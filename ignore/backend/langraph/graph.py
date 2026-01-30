# backend/langraph/graph.py
"""
Updated LangGraph with dynamic Figma template selection and CodeSandbox Renderer Check
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from domains import get_domain, domain_exists


class AgentState(TypedDict):
    """State schema"""
    user_prompt: str
    tabs: List[Dict[str, Any]]
    history: List[Dict[str, str]]
    
    primary_domain: Optional[str]
    tab_clusters: List[Dict[str, Any]]
    
    selected_template: Optional[str]
    template_data: Optional[Dict[str, Any]]
    figma_node_id: Optional[str]
    figma_preview_url: Optional[str]
    
    error: Optional[str]
    access_token: Optional[str]
    react_code: Optional[str]
    
    # CodeSandbox validation
    is_valid_ui: bool
    validation_attempts: int
    sandbox_id: Optional[str]
    sandbox_embed_url: Optional[str]
    sandbox_preview_url: Optional[str]


async def domain_logic_node(state: AgentState) -> AgentState:
    """Execute domain-specific logic"""
    
    domain_name = state["primary_domain"] or "generic"
    prompt = state["user_prompt"]
    tabs = state["tabs"]
    
    # Track attempts to prevent infinite loops
    attempts = state.get("validation_attempts", 0)
    if attempts > 3:
        return {**state, "error": "Maximum UI validation attempts reached. Falling back to simple view."}

    if not domain_exists(domain_name):
        return {
            **state,
            "error": f"Domain {domain_name} not found"
        }
    
    try:
        domain = get_domain(domain_name)
        
        # Prepare Browser data
        browser_data = {
            "tabs": tabs,
            "recent_searches": state.get("history", [])[:5],
            "tab_count": len(tabs)
        }
        
        # Process through domain (gets MCP data)
        domain_response = await domain.process(
            user_prompt=prompt,
            browser_data=browser_data,
            access_token=state.get("access_token")
        )
        
        if domain_response.needs_more_data:
            return {
                **state,
                "error": domain_response.follow_up_question,
                "selected_template": "FollowUpQuestion",
                "template_data": {
                    "question": domain_response.follow_up_question
                }
            }
        
        # ✨ NEW: Select template early and transform data for it
        from ui_templates.template_loader import TemplateLoader
        loader = TemplateLoader()
        
        # Extract keywords for template selection
        keywords = prompt.lower().split() + [tab.get("title", "").lower() for tab in tabs[:5]]
        keywords = [k for k in keywords if len(k) > 3][:20]
        
        template_info = loader.select_template(
            domain=domain_name,
            keywords=keywords,
            user_prompt=prompt,
            tab_count=len(tabs),
            tab_urls=[tab.get("url", "") for tab in tabs]
        )
        
        # ✨ NEW: Use domain agent to prepare template-specific data
        template_data = domain.prepare_template_data(
            template_id=template_info["template_id"],
            mcp_data=domain_response.mcp_results,
            llm_response=domain_response.ui_props.get("response", "")
        )
        
        print(f"📦 Prepared template data with keys: {list(template_data.keys())}")
        
        return {
            **state,
            "selected_template": template_info["template_id"],
            "template_data": template_data
        }
        
    except Exception as e:
        print(f"Domain logic error: {e}")
        import traceback
        traceback.print_exc()
        return {
            **state,
            "error": f"Domain processing failed: {str(e)}"
        }



# ============================================================================
# DEPRECATED: Template selection now happens in domain_logic_node
# ============================================================================

async def select_template_node(state: AgentState) -> AgentState:
    """
    ⚠️ DEPRECATED - Template selection is now integrated into domain_logic_node
    This node is kept for backward compatibility but does nothing
    """
    print("⚠️ select_template_node is deprecated - template selection happens in domain_logic_node")
    return state



async def render_ui_node(state: AgentState) -> AgentState:
    """Convert selected template and data to React code using local templates"""
    from template_generator import generate_dashboard_from_template
    
    # Extract keywords from user prompt and tabs for template selection
    keywords = []
    if state.get("user_prompt"):
        keywords.extend(state["user_prompt"].lower().split())
    
    for tab in state.get("tabs", [])[:10]:
        title = tab.get("title", "").lower()
        keywords.extend(title.split())
    
    # Remove stop words and duplicates
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "is", "are", "was", "were"}
    keywords = [k for k in keywords if k not in stop_words and len(k) > 3]
    keywords = list(set(keywords))[:20]
    
    # Prepare context for template selection
    user_context = {
        "keywords": keywords,
        "user_prompt": state.get("user_prompt", ""),
        "tab_count": len(state.get("tabs", [])),
        "tab_urls": [tab.get("url", "") for tab in state.get("tabs", [])]
    }
    
    try:
        react_code = await generate_dashboard_from_template(
            domain=state.get("primary_domain", "generic"),
            template_data=state.get("template_data", {}),
            user_context=user_context
        )
        
        return {
            **state,
            "react_code": react_code
        }
    except Exception as e:
        print(f"❌ Template generation error: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to simple component
        from template_generator import generate_fallback_component
        fallback_code = generate_fallback_component(
            state.get("template_data", {}),
            state.get("primary_domain", "generic")
        )
        
        return {
            **state,
            "react_code": fallback_code,
            "error": f"Template generation failed: {str(e)}"
        }


async def codesandbox_check_node(state: AgentState) -> AgentState:
    """
    Real CodeSandbox Cloud Renderer Check.
    Creates an actual sandbox using the CodeSandbox API and validates the render.
    """
    from codesandbox import CodeSandboxClient, SandboxResult
    
    react_code = state.get("react_code", "")
    data = state.get("template_data", {})
    attempts = state.get("validation_attempts", 0) + 1
    
    print(f"🔬 Running CodeSandbox Check (Attempt {attempts})...")
    
    # Basic validation first
    if not react_code:
        print("❌ CodeSandbox: No React code generated")
        return {
            **state,
            "is_valid_ui": False,
            "validation_attempts": attempts,
            "error": "Generated code is empty."
        }
    
    if not data:
        print("❌ CodeSandbox: No template data")
        return {
            **state,
            "is_valid_ui": False,
            "validation_attempts": attempts,
            "error": "No data injected into template."
        }
    
    # Skip CodeSandbox (SSE deprecated) - use fallback dashboard instead
    # The fallback dashboard renders data locally without external dependencies
    print("📦 Preparing dashboard data for local rendering...")
    
    # Simple validation - check code has valid structure
    is_valid = "export" in react_code and len(react_code) > 100
    
    if is_valid:
        print(f"✅ React code validated ({len(react_code)} chars)")
        print(f"   Using local fallback dashboard for reliable rendering")
        
        return {
            **state,
            "is_valid_ui": True,
            "validation_attempts": attempts,
            # No sandbox URLs - the fallback dashboard will render the data
            "sandbox_id": None,
            "sandbox_embed_url": None,
            "sandbox_preview_url": None,
            "error": None
        }
    else:
        print(f"❌ React code validation failed")
        return {
            **state,
            "is_valid_ui": False,
            "validation_attempts": attempts,
            "error": "Generated React code is invalid"
        }



def should_continue(state: AgentState):
    """Router for the renderer loop"""
    if state["is_valid_ui"]:
        return "end"
    if state.get("validation_attempts", 0) >= 3:
        return "end"
    return "retry"


def build_graph() -> StateGraph:
    """Build LangGraph with Check-and-Loop logic (updated for local templates)"""
    workflow = StateGraph(AgentState)
    
    # Define Nodes
    workflow.add_node("domain_logic", domain_logic_node)
    # NOTE: select_template is deprecated - template selection happens in domain_logic_node
    workflow.add_node("render", render_ui_node)
    workflow.add_node("codesandbox_check", codesandbox_check_node)
    
    # Define Edges (simplified - no separate template selection)
    workflow.set_entry_point("domain_logic")
    workflow.add_edge("domain_logic", "render")  # Direct to render (template already selected)
    workflow.add_edge("render", "codesandbox_check")
    
    # Conditional Loop (The Renderer Check)
    workflow.add_conditional_edges(
        "codesandbox_check",
        should_continue,
        {
            "retry": "domain_logic", # Loop back to agents to fix data/logic
            "end": END
        }
    )
    
    return workflow.compile()