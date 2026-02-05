"""
FastAPI Router - FIXED for Local Templates Only
Returns CodeSandbox embed URLs directly
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from .graph import build_graph
# NOTE: domains/ are kept as ghost files but NOT used in main flow
# from domains import get_domain, domain_exists  # DEPRECATED

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
    """Response sent back to extension - SIMPLIFIED"""
    success: bool
    domain: str
    selected_template: str
    ui_props: Dict[str, Any]
    react_code: Optional[str] = None
    error: Optional[str] = None
    
    # CodeSandbox URLs (PRIMARY OUTPUT)
    sandbox_id: Optional[str] = None
    sandbox_embed_url: Optional[str] = None
    sandbox_preview_url: Optional[str] = None


@router.post("/api/generate-dashboard", response_model=DashboardConfigResponse)
async def generate_dashboard(request: DomainSelectionRequest):
    """
    Main endpoint: Generate dashboard using LOCAL TEMPLATES ONLY
    Returns CodeSandbox embed URL
    """
    
    print("Received request to generate dashboard")
    try:
        # 1. Validate domain
        valid_domains = ["study", "shopping", "travel", "code", "entertainment", "generic"]
        if request.domain not in valid_domains:
            raise HTTPException(400, f"Invalid domain. Must be one of: {valid_domains}")
        
        # 2. Convert tabs
        tabs_data = [tab.model_dump() for tab in request.tabs]
        
        # 3. Build initial state
        initial_state = {
            "user_prompt": request.user_prompt or f"Create a {request.domain} dashboard",
            "tabs": tabs_data,
            "history": request.history or [],
            "primary_domain": request.domain,
            "domain_scores": {request.domain: 1.0},
            "tab_clusters": [],
            "selected_template": None,
            "template_data": None,
            "react_code": None,
            "error": None,
            "access_token": request.google_token,
            "is_valid_ui": False,
            "validation_attempts": 0,
            "sandbox_id": None,
            "sandbox_embed_url": None,
            "sandbox_preview_url": None,
            "sandbox_files": None
        }
        
        # 4. Run LangGraph
        graph = build_graph()
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
        
        # 6. Return CodeSandbox URLs
        template_name = result_state.get("selected_template", "GenericDashboard")
        template_data = result_state.get("template_data", {})
        
        return DashboardConfigResponse(
            success=True,
            domain=request.domain,
            selected_template=template_name,
            ui_props=template_data,
            react_code=result_state.get("react_code"),
            sandbox_id=result_state.get("sandbox_id"),
            sandbox_embed_url=result_state.get("sandbox_embed_url"),
            sandbox_preview_url=result_state.get("sandbox_preview_url")
        )
        
    except Exception as e:
        print(f"Dashboard generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Dashboard generation failed: {str(e)}")