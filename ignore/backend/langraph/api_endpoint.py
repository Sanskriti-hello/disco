"""
FastAPI Router - Main entry point for extension
Receives domain selection + tabs, runs LangGraph, returns dashboard config
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from .graph import build_graph
from domains import get_domain, domain_exists

router = APIRouter()


class TabData(BaseModel):
    """Schema for individual tab"""
    id: int
    title: str
    url: str
    content: str


class DomainSelectionRequest(BaseModel):
    """Request from extension after user selects domain"""
    domain: str
    tabs: List[TabData]
    user_prompt: Optional[str] = ""
    summary: Optional[str] = ""
    history: Optional[List[Dict[str, Any]]] = []
    google_token: Optional[str] = None


class DashboardConfigResponse(BaseModel):
    """Response sent back to extension"""
    success: bool
    domain: str
    selected_template: str
    template_url: Optional[str] = None
    figma_node_id: Optional[str] = None
    ui_props: Dict[str, Any]
    react_code: Optional[str] = None
    widgets: List[Dict[str, Any]] = []
    error: Optional[str] = None
    # CodeSandbox integration
    sandbox_id: Optional[str] = None
    sandbox_embed_url: Optional[str] = None
    sandbox_preview_url: Optional[str] = None


@router.post("/api/generate-dashboard", response_model=DashboardConfigResponse)
async def generate_dashboard(request: DomainSelectionRequest):
    """
    Main endpoint: Receives domain selection from extension
    Runs LangGraph workflow to generate dashboard config
    """
    
    try:
        # 1. Validate domain
        valid_domains = ["study", "shopping", "travel", "code", "entertainment", "generic"]
        if request.domain not in valid_domains:
            raise HTTPException(400, f"Invalid domain. Must be one of: {valid_domains}")
        
        # 2. Convert tabs to dict format for LangGraph
        tabs_data = [tab.model_dump() for tab in request.tabs]
        
        # 3. Build initial state for LangGraph
        initial_state = {
            "user_prompt": request.user_prompt or f"Create a {request.domain} dashboard",
            "tabs": tabs_data,
            "history": request.history or [],
            "primary_domain": request.domain,
            "domain_scores": {request.domain: 1.0},
            "tab_clusters": [],  # Already clustered in extension
            "selected_template": None,
            "template_data": None,
            "react_code": None,
            "widgets": [],
            "error": None,
            "access_token": request.google_token,
            # CodeSandbox validation state
            "is_valid_ui": False,
            "validation_attempts": 0,
            "sandbox_id": None,
            "sandbox_embed_url": None,
            "sandbox_preview_url": None
        }
        
        # 4. Run LangGraph workflow
        graph = build_graph()
        
        # Execute from domain_logic node (skip classification since we already have domain)
        result_state = await graph.ainvoke(initial_state, {"recursion_limit": 10})
        
        # 5. Check for errors
        if result_state.get("error"):
            return DashboardConfigResponse(
                success=False,
                domain=request.domain,
                selected_template="ErrorView",
                ui_props={"error": result_state["error"]},
                error=result_state["error"]
            )
        
        # 6. Get template information
        template_name = result_state.get("selected_template", "GenericDashboard")
        template_data = result_state.get("template_data", {})
        
        # 7. Fetch Figma template info (if available)
        figma_info = await get_figma_template_info(request.domain, template_name)
        
        # 8. Return dashboard config with CodeSandbox URLs
        return DashboardConfigResponse(
            success=True,
            domain=request.domain,
            selected_template=template_name,
            template_url=figma_info.get("preview_url") if figma_info else None,
            figma_node_id=figma_info.get("node_id") if figma_info else None,
            ui_props=template_data,
            react_code=result_state.get("react_code"),
            widgets=result_state.get("widgets", []),
            sandbox_id=result_state.get("sandbox_id"),
            sandbox_embed_url=result_state.get("sandbox_embed_url"),
            sandbox_preview_url=result_state.get("sandbox_preview_url")
        )
        
    except Exception as e:
        print(f"Dashboard generation failed: {e}")
        raise HTTPException(500, f"Dashboard generation failed: {str(e)}")


@router.post("/api/get-template-preview")
async def get_template_preview(domain: str, template_name: str):
    """
    Get Figma preview for a specific template
    Used by extension to show template options before generation
    """
    
    try:
        figma_info = await get_figma_template_info(domain, template_name)
        
        if not figma_info:
            raise HTTPException(404, "Template not found")
        
        return {
            "template_name": template_name,
            "domain": domain,
            "preview_url": figma_info.get("preview_url"),
            "node_id": figma_info.get("node_id"),
            "description": figma_info.get("description", "")
        }
        
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch template: {str(e)}")


async def get_figma_template_info(domain: str, template_name: str) -> Optional[Dict[str, Any]]:
    """
    Helper: Fetches Figma template info from templates registry
    Returns: {node_id, preview_url, description}
    """
    
    try:
        from ui_templates.registry import TemplateRegistryV2
        from figma import fetch_ui_template
        import os
        
        registry = TemplateRegistryV2()
        template_meta = registry.get_template_meta(domain, template_name)
        
        if not template_meta:
            return None
            
        # If node_id is not already parsed (e.g. fresh from JSON), ensure it is
        if not template_meta.get("figma_node_id") and template_meta.get("figma_url"):
             # Handled by get_templates_for_domain inside the registry usually
             registry.get_templates_for_domain(domain)
             template_meta = registry.get_template_meta(domain, template_name)

        if not template_meta.get("figma_node_id"):
            return None
        
        # Use file key from template if available, else from env
        file_key = template_meta.get("figma_file_key") or os.getenv("FIGMA_FILE_KEY")
        if not file_key:
            return None
        
        # Fetch from Figma
        figma_data = fetch_ui_template(
            file_key,
            template_meta["figma_node_id"],
            include_preview=True
        )
        
        return {
            "node_id": template_meta["figma_node_id"],
            "preview_url": figma_data.get("preview_url"),
            "description": template_meta.get("description", ""),
            "node_data": figma_data.get("node")
        }
        
    except Exception as e:
        print(f"Failed to fetch Figma template: {e}")
        return None