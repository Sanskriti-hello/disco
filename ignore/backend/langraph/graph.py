# backend/langraph/graph.py
"""
LangGraph with LOCAL TEMPLATES ONLY - No Figma, No Fallbacks
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
    
    error: Optional[str]
    access_token: Optional[str]
    react_code: Optional[str]
    
    # CodeSandbox
    is_valid_ui: bool
    validation_attempts: int
    sandbox_id: Optional[str]
    sandbox_embed_url: Optional[str]
    sandbox_preview_url: Optional[str]
    sandbox_files: Optional[Dict[str, Dict[str, str]]]


async def domain_logic_node(state: AgentState) -> AgentState:
    """Execute domain-specific logic and select template"""
    
    domain_name = state["primary_domain"] or "generic"
    prompt = state["user_prompt"]
    tabs = state["tabs"]
    
    attempts = state.get("validation_attempts", 0)
    if attempts > 3:
        return {**state, "error": "Maximum attempts reached"}

    if not domain_exists(domain_name):
        return {**state, "error": f"Domain {domain_name} not found"}
    
    try:
        domain = get_domain(domain_name)
        
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
                "template_data": {"question": domain_response.follow_up_question}
            }
        
        # Select template
        from ui_templates.template_loader import TemplateLoader
        loader = TemplateLoader()
        
        keywords = prompt.lower().split() + [tab.get("title", "").lower() for tab in tabs[:5]]
        keywords = [k for k in keywords if len(k) > 3][:20]
        
        template_info = loader.select_template(
            domain=domain_name,
            keywords=keywords,
            user_prompt=prompt,
            tab_count=len(tabs),
            tab_urls=[tab.get("url", "") for tab in tabs]
        )
        
        # Transform data for template
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
        return {**state, "error": f"Domain processing failed: {str(e)}"}


async def render_ui_node(state: AgentState) -> AgentState:
    """Generate React code from local template with data injection"""
    
    keywords = []
    if state.get("user_prompt"):
        keywords.extend(state["user_prompt"].lower().split())
    
    for tab in state.get("tabs", [])[:10]:
        title = tab.get("title", "").lower()
        keywords.extend(title.split())
    
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "is", "are", "was", "were"}
    keywords = [k for k in keywords if k not in stop_words and len(k) > 3]
    keywords = list(set(keywords))[:20]
    
    user_context = {
        "keywords": keywords,
        "user_prompt": state.get("user_prompt", ""),
        "tab_count": len(state.get("tabs", [])),
        "tab_urls": [tab.get("url", "") for tab in state.get("tabs", [])]
    }
    
    try:
        # Import the fixed generator (no LLM, no Figma)
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__) + "/..")
        
        from template_generator import generate_dashboard_from_template
        
        react_code = await generate_dashboard_from_template(
            domain=state.get("primary_domain", "generic"),
            template_data=state.get("template_data", {}),
            user_context=user_context
        )
        
        # Build complete CodeSandbox file structure
        from ui_templates.sandbox_builder import SandboxBuilder
        builder = SandboxBuilder()
        
        sandbox_files = builder.build_complete_sandbox(
            template_id=state.get("selected_template", "generic-1"),
            injected_component=react_code,
            data=state.get("template_data", {})
        )
        
        print(f"📦 Built sandbox with {len(sandbox_files)} files")
        
        return {
            **state,
            "react_code": react_code,
            "sandbox_files": sandbox_files
        }
        
    except Exception as e:
        print(f"❌ Template generation error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            **state,
            "react_code": None,
            "error": f"Template generation failed: {str(e)}"
        }


async def codesandbox_check_node(state: AgentState) -> AgentState:
    """
    Create CodeSandbox and validate
    """
    from codesandbox import CodeSandboxClient
    
    react_code = state.get("react_code", "")
    sandbox_files = state.get("sandbox_files", {})
    attempts = state.get("validation_attempts", 0) + 1
    
    print(f"🔬 Creating CodeSandbox (Attempt {attempts})...")
    
    # Validate we have code
    if not react_code or not sandbox_files:
        print("❌ No React code or sandbox files generated")
        return {
            **state,
            "is_valid_ui": False,
            "validation_attempts": attempts,
            "error": "No code generated"
        }
    
    # Create CodeSandbox with complete file structure
    try:
        client = CodeSandboxClient()
        
        # PERMANENT: Use legacy sandbox mode as it is more stable for the user.
        print("✅ Using legacy sandbox mode for stability.")
        
        template_id = state.get("selected_template", "generic-1")
        
        # Load the correct CSS and data for the template
        additional_files = {}
        try:
            from pathlib import Path
            import json

            # Load legacy CSS for code-1, or the original for others
            css_filename = "code-1-legacy.css" if template_id == "code-1" else f"{template_id}/src/index.css"
            css_path = Path(__file__).parent.parent / "ui_templates" / css_filename
            
            if css_path.exists():
                additional_files["styles.css"] = css_path.read_text(encoding='utf-8')
                print(f"✅ Loaded CSS: {css_filename}")

            # Serialize data to pass as props
            template_data = state.get("template_data", {})
            additional_files["props.json"] = json.dumps(template_data)

        except Exception as e:
            print(f"⚠️ Could not load template files: {e}")

        result = await client.create_sandbox(
            jsx_code=react_code,
            title=f"Dashboard - {template_id}",
            additional_files=additional_files,
            complete_files=None
        )
        
        if result.success:
            print(f"✅ CodeSandbox created: {result.sandbox_id}")
            print(f"   Embed URL: {result.embed_url}")
            
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
            print(f"❌ CodeSandbox creation failed: {result.error}")
            return {
                **state,
                "is_valid_ui": False,
                "validation_attempts": attempts,
                "error": f"CodeSandbox failed: {result.error}"
            }
            
    except Exception as e:
        print(f"❌ CodeSandbox error: {e}")
        return {
            **state,
            "is_valid_ui": False,
            "validation_attempts": attempts,
            "error": f"CodeSandbox error: {str(e)}"
        }


def should_continue(state: AgentState):
    """Router for renderer loop"""
    if state["is_valid_ui"]:
        return "end"
    if state.get("validation_attempts", 0) >= 3:
        return "end"
    return "retry"


def build_graph() -> StateGraph:
    """Build LangGraph with local template system"""
    workflow = StateGraph(AgentState)
    
    # Nodes
    workflow.add_node("domain_logic", domain_logic_node)
    workflow.add_node("render", render_ui_node)
    workflow.add_node("codesandbox_check", codesandbox_check_node)
    
    # Edges
    workflow.set_entry_point("domain_logic")
    workflow.add_edge("domain_logic", "render")
    workflow.add_edge("render", "codesandbox_check")
    
    # Conditional loop
    workflow.add_conditional_edges(
        "codesandbox_check",
        should_continue,
        {
            "retry": "domain_logic",
            "end": END
        }
    )
    
    return workflow.compile()