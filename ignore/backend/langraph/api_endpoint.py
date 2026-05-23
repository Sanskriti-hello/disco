"""FastAPI router for local dashboard generation and clustering."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .graph import build_graph
from services.llm_router import LLMRouter, deterministic_select_domain

router = APIRouter()
llm_router = LLMRouter()


class ErrorModel(BaseModel):
    type: str
    message: str
    provider: str = ""


class TabData(BaseModel):
    id: int
    title: str
    url: str
    content: str = ""
    structured: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ClusterTabsRequest(BaseModel):
    tabs: List[TabData]


class ClusterTabsResponse(BaseModel):
    success: bool
    clusters: List[Dict[str, Any]] = Field(default_factory=list)
    provider: str = ""
    fallback_mode: bool = False
    error: Optional[ErrorModel] = None


class SelectDomainRequest(BaseModel):
    tabs: List[TabData]
    user_prompt: str = ""


class SelectDomainResponse(BaseModel):
    success: bool
    result: Dict[str, Any] = Field(default_factory=dict)
    provider: str = ""
    fallback_mode: bool = False
    error: Optional[ErrorModel] = None


class DomainSelectionRequest(BaseModel):
    domain: str
    tabs: List[TabData]
    user_prompt: Optional[str] = ""
    summary: Optional[str] = ""
    history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    google_token: Optional[str] = None


class DashboardConfigResponse(BaseModel):
    success: bool
    template: str = "generic-1"
    dashboard: Dict[str, Any] = Field(default_factory=dict)
    provider: str = ""
    fallback_mode: bool = False
    error: Optional[ErrorModel] = None


class SummarizeRequest(BaseModel):
    text: str


class SummarizeResponse(BaseModel):
    success: bool
    summary: str = ""
    provider: str = ""
    fallback_mode: bool = False
    error: Optional[ErrorModel] = None


@router.get("/health")
async def health() -> Dict[str, Any]:
    provider_health = llm_router.health()
    return {
        "status": "ok",
        "providers": provider_health,
        "llm_available": provider_health.get("groq_configured") or provider_health.get("gemini_configured"),
    }


@router.post("/api/cluster-tabs", response_model=ClusterTabsResponse)
async def cluster_tabs(request: ClusterTabsRequest):
    try:
        tabs = [t.model_dump() for t in request.tabs]
        clusters, meta = await llm_router.cluster_tabs(tabs)
        return ClusterTabsResponse(
            success=True,
            clusters=clusters,
            provider=meta.get("provider", ""),
            fallback_mode=meta.get("fallback_mode", False),
        )
    except Exception as e:
        return ClusterTabsResponse(
            success=False,
            clusters=[],
            error=ErrorModel(type="cluster_error", message=str(e), provider="backend"),
        )


@router.post("/api/select-domain", response_model=SelectDomainResponse)
async def select_domain(request: SelectDomainRequest):
    try:
        tabs = [t.model_dump() for t in request.tabs]
        result, meta = await llm_router.select_domain(tabs, request.user_prompt)
        payload = {
            "domain": result.get("domain", "generic"),
            "tabs": tabs,
            "summary": result.get("reason", ""),
            "userPrompt": request.user_prompt,
        }
        return SelectDomainResponse(
            success=True,
            result=payload,
            provider=meta.get("provider", ""),
            fallback_mode=meta.get("fallback_mode", False),
        )
    except Exception as e:
        tabs = [t.model_dump() for t in request.tabs]
        fallback = deterministic_select_domain(tabs, request.user_prompt)
        return SelectDomainResponse(
            success=True,
            result={
                "domain": fallback.get("domain", "generic"),
                "tabs": tabs,
                "summary": fallback.get("reason", ""),
                "userPrompt": request.user_prompt,
            },
            provider="deterministic",
            fallback_mode=True,
            error=ErrorModel(type="provider_error", message=str(e), provider="backend"),
        )


@router.post("/api/generate-dashboard", response_model=DashboardConfigResponse)
async def generate_dashboard(request: DomainSelectionRequest):
    valid_domains = ["study", "shopping", "travel", "code", "entertainment", "generic"]
    if request.domain not in valid_domains:
        raise HTTPException(400, f"Invalid domain. Must be one of: {valid_domains}")

    initial_state = {
        "user_prompt": request.user_prompt or f"Create a {request.domain} dashboard",
        "tabs": [tab.model_dump() for tab in request.tabs],
        "history": request.history or [],
        "primary_domain": request.domain,
        "selected_template": None,
        "template_data": None,
        "dashboard": None,
        "error": None,
    }

    try:
        graph = build_graph()
        result_state = await graph.ainvoke(initial_state, {"recursion_limit": 6})

        if result_state.get("error"):
            return DashboardConfigResponse(
                success=False,
                template="generic-1",
                dashboard={},
                error=ErrorModel(type="dashboard_error", message=result_state["error"], provider="backend"),
            )

        return DashboardConfigResponse(
            success=True,
            template=result_state.get("selected_template", "generic-1"),
            dashboard=result_state.get("dashboard", {}),
            provider="backend",
            fallback_mode=False,
        )

    except Exception as e:
        return DashboardConfigResponse(
            success=False,
            template="generic-1",
            dashboard={},
            error=ErrorModel(type="dashboard_error", message=str(e), provider="backend"),
        )


@router.post("/api/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    try:
        summary, meta = await llm_router.summarize(request.text)
        return SummarizeResponse(
            success=True,
            summary=summary,
            provider=meta.get("provider", ""),
            fallback_mode=meta.get("fallback_mode", False),
        )
    except Exception as e:
        return SummarizeResponse(
            success=False,
            summary="",
            error=ErrorModel(type="summarize_error", message=str(e), provider="backend"),
        )
