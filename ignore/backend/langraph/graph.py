# backend/langraph/graph.py
"""
LangGraph with Sandbox Builder - MCP Tools as Primary Data Source
Domain agents are kept as ghost files but bypassed in favor of sandbox_builder logic.
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
import json

# NOTE: domains/ are kept as ghost files but NOT used in main flow
# from domains import get_domain, domain_exists  # DEPRECATED - kept for reference


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


def _build_page_context(state: AgentState) -> str:
    """
    Build page context from browser tabs for MCP-based JSON filling.
    
    This replaces domain agent processing with a unified context string
    that the LLM agent uses to fill template JSON data.
    """
    domain = state.get("primary_domain", "generic")
    prompt = state.get("user_prompt", "")
    tabs = state.get("tabs", [])
    
    # Build context from tabs
    tab_summaries = []
    for tab in tabs[:10]:  # Limit to 10 tabs
        title = tab.get("title", "Untitled")
        url = tab.get("url", "")
        content = tab.get("content", "")[:500]  # Truncate content
        tab_summaries.append(f"- {title} ({url}): {content[:200]}...")
    
    context = f"""
Domain: {domain}
User Request: {prompt}
Open Tabs:
{chr(10).join(tab_summaries) if tab_summaries else "No tabs available"}
"""
    return context.strip()


async def sandbox_logic_node(state: AgentState) -> AgentState:
    """
    Execute sandbox-based logic using MCP tools for data acquisition.
    
    This replaces the deprecated domain_logic_node that used domain agents.
    Uses entertainment_builder's update_json for LLM-driven JSON filling.
    """
    
    domain_name = state["primary_domain"] or "generic"
    prompt = state["user_prompt"]
    tabs = state["tabs"]
    
    attempts = state.get("validation_attempts", 0)
    if attempts > 3:
        return {**state, "error": "Maximum attempts reached"}
    
    try:
        print(f"🚀 Sandbox Logic Node - Domain: {domain_name}")
        
        # Build context for MCP-based filling
        page_context = _build_page_context(state)
        print(f"📋 Page context built ({len(page_context)} chars)")
        
        # Select template first
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
        
        template_id = template_info["template_id"]
        print(f"🎨 Selected template: {template_id}")
        
        # Load template's data.json for filling
        # Note: Template directories may have different naming (e.g., entertainment-template vs entertainment-1)
        # We search for matching directories based on domain
        from pathlib import Path
        import glob
        
        ui_templates_dir = Path(__file__).parent.parent / "ui_templates"
        data_json_path = None
        
        # Try direct template_id path first
        direct_path = ui_templates_dir / template_id / "src" / "data.json"
        if direct_path.exists():
            data_json_path = direct_path
        else:
            # Search for domain-matching template directories
            domain_prefix = domain_name.lower()
            for template_dir in ui_templates_dir.iterdir():
                if template_dir.is_dir() and domain_prefix in template_dir.name.lower():
                    candidate_path = template_dir / "src" / "data.json"
                    if candidate_path.exists():
                        data_json_path = candidate_path
                        print(f"📁 Found matching template directory: {template_dir.name}")
                        break
        
        template_data = {}
        
        if data_json_path and data_json_path.exists():
            try:
                raw_json = data_json_path.read_text(encoding='utf-8')
                
                # Use sandbox_builder's LLM-driven JSON filling with MCP tools
                from sandbox_builders.entertainment_builder import update_json
                
                # Build field-level context from template structure
                field_context = f"""
Fill this JSON template for a {domain_name} dashboard.
User wants: {prompt}
Use real data from web search when needed.
"""
                
                filled_json = update_json(
                    content=raw_json,
                    page_context=page_context,
                    field_context=field_context
                )
                
                template_data = json.loads(filled_json)
                print(f"📦 Filled template data with keys: {list(template_data.keys())}")
                
            except Exception as e:
                print(f"⚠️ JSON filling failed, using raw template: {e}")
                template_data = json.loads(raw_json) if 'raw_json' in locals() else {}
        else:
            print(f"⚠️ No data.json found for domain: {domain_name}")
            # Generate minimal template data
            template_data = {
                "title": prompt[:50] if prompt else f"{domain_name.title()} Dashboard",
                "domain": domain_name,
                "items": []
            }
        
        return {
            **state,
            "selected_template": template_id,
            "template_data": template_data
        }
        
    except Exception as e:
        print(f"❌ Sandbox logic error: {e}")
        import traceback
        traceback.print_exc()
        return {**state, "error": f"Sandbox processing failed: {str(e)}"}


# Alias for backward compatibility - the graph uses this name
domain_logic_node = sandbox_logic_node


async def render_ui_node(state: AgentState) -> AgentState:
    """Build CodeSandbox file structure from template directory with LLM-filled data"""
    
    try:
        from pathlib import Path
        from sandbox_builders.entertainment_builder import EntertainmentAppSandboxBuilder
        import json
        
        template_id = state.get("selected_template", "generic-1")
        domain = state.get("primary_domain", "generic")
        user_prompt = state.get("user_prompt", "")
        template_data = state.get("template_data", {})  # Get the LLM-filled data
        
        # Build context for the sandbox builder
        page_context = _build_page_context(state)
        
        # Find the template directory
        ui_templates_dir = Path(__file__).parent.parent / "ui_templates"
        template_path = ui_templates_dir / template_id
        
        if not template_path.exists():
            # Try finding by domain
            for template_dir in ui_templates_dir.iterdir():
                if template_dir.is_dir() and domain in template_dir.name.lower():
                    template_path = template_dir
                    break
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template directory not found: {template_id}")
        
        print(f"📁 Building sandbox from template directory: {template_path.name}")
        
        # Use EntertainmentAppSandboxBuilder to build the complete sandbox
        builder = EntertainmentAppSandboxBuilder(
            context=page_context,
            project_dir=template_path
        )
        
        sandbox_files = builder.build_sandbox()
        
        # INJECT THE LLM-FILLED DATA into data.json
        if template_data:
            filled_json_content = json.dumps(template_data, ensure_ascii=False, indent=2)
            
            # Find and replace data.json in sandbox_files
            data_json_keys = [k for k in sandbox_files.keys() if 'data.json' in k]
            if data_json_keys:
                for key in data_json_keys:
                    sandbox_files[key] = {"content": filled_json_content}
                    print(f"✅ Injected LLM-filled data into {key}")
            else:
                # Add data.json if it doesn't exist
                sandbox_files["src/data.json"] = {"content": filled_json_content}
                print(f"✅ Added src/data.json with LLM-filled data")
        
        print(f"📦 Built sandbox with {len(sandbox_files)} files")
        
        # Extract App.jsx or main component as react_code for backward compatibility
        react_code = None
        for path, file_data in sandbox_files.items():
            if "App.jsx" in path or "App.js" in path:
                react_code = file_data.get("content", "")
                break
        
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
    Create live CodeSandbox and return preview URLs
    """
    sandbox_files = state.get("sandbox_files", {})
    attempts = state.get("validation_attempts", 0) + 1
    template_id = state.get("selected_template", "generic-1")
    
    print(f"🔬 Creating CodeSandbox (Attempt {attempts})...")
    
    # Validate we have files
    if not sandbox_files or len(sandbox_files) == 0:
        print("❌ No sandbox files generated")
        return {
            **state,
            "is_valid_ui": False,
            "validation_attempts": attempts,
            "error": "No sandbox files generated"
        }
    
    # Check for essential files
    has_html = any("index.html" in path for path in sandbox_files.keys())
    has_js = any(".js" in path or ".jsx" in path for path in sandbox_files.keys())
    
    if not (has_html or has_js):
        print("❌ Missing essential files (HTML or JS)")
        return {
            **state,
            "is_valid_ui": False,
            "validation_attempts": attempts,
            "error": "Missing essential files in sandbox"
        }
    
    # Use CodeSandboxClient to create CodeSandbox URL
    try:
        from sandbox_builders.code_sandbox import CodeSandboxClient
        
        client = CodeSandboxClient()
        result = await client.create_sandbox(sandbox_files, title=f"Dashboard - {template_id}")
        
        if result.success:
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
            # Still mark as valid since we have files, just no live URL
            print(f"⚠️ CodeSandbox creation failed, but files are available locally")
            return {
                **state,
                "is_valid_ui": True,
                "validation_attempts": attempts,
                "sandbox_id": f"local-{template_id}",
                "sandbox_embed_url": None,
                "sandbox_preview_url": None,
                "error": f"CodeSandbox API error: {result.error}"
            }
            
    except Exception as e:
        print(f"❌ CodeSandbox error: {e}")
        import traceback
        traceback.print_exc()
        # Still mark as valid since we have files
        return {
            **state,
            "is_valid_ui": True,
            "validation_attempts": attempts,
            "sandbox_id": f"local-{template_id}",
            "sandbox_embed_url": None,
            "sandbox_preview_url": None,
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