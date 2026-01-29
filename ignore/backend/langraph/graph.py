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
        
        # Process through domain
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
        
        return {
            **state,
            "selected_template": domain_response.ui_template,
            "template_data": domain_response.ui_props
        }
        
    except Exception as e:
        print(f"Domain logic error: {e}")
        return {
            **state,
            "error": f"Domain processing failed: {str(e)}"
        }


async def select_template_node(state: AgentState) -> AgentState:
    """Dynamic template selection using Registry"""
    from ui_templates.registry import TemplateRegistryV2
    
    keywords = []
    if state.get("user_prompt"):
        keywords.extend(state["user_prompt"].lower().split())
    
    for tab in state.get("tabs", [])[:10]:
        title = tab.get("title", "").lower()
        keywords.extend(title.split())
    
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "is", "are", "was", "were"}
    keywords = [k for k in keywords if k not in stop_words and len(k) > 3]
    keywords = list(set(keywords))[:20]
    
    try:
        registry = TemplateRegistryV2()
        template_match = registry.find_best_template(
            domain=state["primary_domain"] or "generic",
            keywords=keywords,
            user_prompt=state.get("user_prompt", "")
        )
        
        template_meta = registry.get_template_meta(state["primary_domain"] or "generic", template_match["template_name"])
        
        return {
            **state,
            "selected_template": template_match["template_name"],
            "figma_node_id": template_meta.get("figma_node_id") if template_meta else "default",
            "figma_preview_url": template_match["figma_url"]
        }
        
    except Exception as e:
        return {
            **state,
            "selected_template": "GenericDashboard",
            "error": f"Registry fetch failed: {str(e)}"
        }


async def render_ui_node(state: AgentState) -> AgentState:
    """Convert selected template and data to React code"""
    from figma import generate_dashboard_component
    
    react_code = generate_dashboard_component(
        figma_node_id=state.get("figma_node_id", "unknown"),
        figma_preview_url=state.get("figma_preview_url", ""),
        template_name=state.get("selected_template", "Dashboard"),
        template_data=state.get("template_data", {}),
        domain=state.get("primary_domain", "generic")
    )
    
    return {
        **state,
        "react_code": react_code
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
    
    # Try to create a real CodeSandbox
    try:
        client = CodeSandboxClient()
        
        # Clean up the code for sandbox (ensure it's a valid module)
        sandbox_code = react_code
        
        # If code uses "export const", convert to default export for sandbox
        if "export default" not in sandbox_code:
            # Extract component name and add default export
            import re
            match = re.search(r'export const (\w+)', sandbox_code)
            if match:
                component_name = match.group(1)
                sandbox_code = sandbox_code + f"\n\nexport default {component_name};"
        
        result = await client.create_sandbox(
            jsx_code=sandbox_code,
            title=f"{state.get('selected_template', 'Dashboard')} - {state.get('primary_domain', 'generic')}"
        )
        
        if result.success:
            print(f"✅ CodeSandbox: UI Rendered Successfully!")
            print(f"   Sandbox ID: {result.sandbox_id}")
            print(f"   Preview: {result.preview_url}")
            
            return {
                **state,
                "is_valid_ui": True,
                "validation_attempts": attempts,
                "sandbox_id": result.sandbox_id,
                "sandbox_embed_url": result.embed_url,
                "sandbox_preview_url": result.preview_url,
                "error": None
            }
        else:
            print(f"❌ CodeSandbox: Render Failed! {result.error}")
            return {
                **state,
                "is_valid_ui": False,
                "validation_attempts": attempts,
                "error": f"CodeSandbox creation failed: {result.error}"
            }
            
    except Exception as e:
        print(f"❌ CodeSandbox: Exception - {str(e)}")
        
        # If CodeSandbox API fails, fall back to basic validation
        # (so the system doesn't completely break if API is down)
        is_valid = "export" in react_code and len(react_code) > 100
        
        return {
            **state,
            "is_valid_ui": is_valid,
            "validation_attempts": attempts,
            "error": f"CodeSandbox API error (using fallback validation): {str(e)}" if not is_valid else None
        }



def should_continue(state: AgentState):
    """Router for the renderer loop"""
    if state["is_valid_ui"]:
        return "end"
    if state.get("validation_attempts", 0) >= 3:
        return "end"
    return "retry"


def build_graph() -> StateGraph:
    """Build LangGraph with Check-and-Loop logic"""
    workflow = StateGraph(AgentState)
    
    # Define Nodes
    workflow.add_node("domain_logic", domain_logic_node)
    workflow.add_node("select_template", select_template_node)
    workflow.add_node("render", render_ui_node)
    workflow.add_node("codesandbox_check", codesandbox_check_node)
    
    # Define Edges
    workflow.set_entry_point("domain_logic")
    workflow.add_edge("domain_logic", "select_template")
    workflow.add_edge("select_template", "render")
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