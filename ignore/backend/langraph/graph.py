"""LangGraph pipeline for local dashboard payload generation (no remote sandbox)."""

from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
import json

from schemas.dashboard_schema import normalize_dashboard_payload


class AgentState(TypedDict):
    user_prompt: str
    tabs: List[Dict[str, Any]]
    history: List[Dict[str, str]]

    primary_domain: Optional[str]
    selected_template: Optional[str]

    template_data: Optional[Dict[str, Any]]
    dashboard: Optional[Dict[str, Any]]
    error: Optional[str]


def _build_page_context(state: AgentState) -> str:
    domain = state.get("primary_domain", "generic")
    prompt = state.get("user_prompt", "")
    tabs = state.get("tabs", [])

    tab_summaries = []
    for tab in tabs[:10]:
        title = tab.get("title", "Untitled")
        url = tab.get("url", "")
        content = tab.get("content", "")[:500]
        tab_summaries.append(f"- {title} ({url}): {content[:200]}...")

    return (
        f"Domain: {domain}\n"
        f"User Request: {prompt}\n"
        f"Open Tabs:\n{chr(10).join(tab_summaries) if tab_summaries else 'No tabs available'}"
    )


async def generate_dashboard_payload_node(state: AgentState) -> AgentState:
    domain_name = state.get("primary_domain") or "generic"
    prompt = state.get("user_prompt", "")
    tabs = state.get("tabs", [])

    try:
        from pathlib import Path
        from ui_templates.template_loader import TemplateLoader
        from sandbox_builders.entertainment_builder import fill_data_with_mcp_tools

        loader = TemplateLoader()
        keywords = prompt.lower().split() + [tab.get("title", "").lower() for tab in tabs[:5]]
        keywords = [k for k in keywords if len(k) > 3][:20]

        template_info = loader.select_template(
            domain=domain_name,
            keywords=keywords,
            user_prompt=prompt,
            tab_count=len(tabs),
            tab_urls=[tab.get("url", "") for tab in tabs],
        )
        template_id = template_info["template_id"]

        ui_templates_dir = Path(__file__).parent.parent / "ui_templates"
        data_json_path = ui_templates_dir / template_id / "src" / "data.json"

        if not data_json_path.exists():
            for template_dir in ui_templates_dir.iterdir():
                if template_dir.is_dir() and domain_name.lower() in template_dir.name.lower():
                    candidate = template_dir / "src" / "data.json"
                    if candidate.exists():
                        data_json_path = candidate
                        template_id = template_dir.name
                        break

        if data_json_path.exists():
            template_structure = json.loads(data_json_path.read_text(encoding="utf-8"))
            template_data = fill_data_with_mcp_tools(
                template_data=template_structure,
                domain=domain_name,
                context=_build_page_context(state),
                tabs_structured_data=tabs,
            )
        else:
            template_data = {
                "title": prompt[:80] if prompt else f"{domain_name.title()} Dashboard",
                "summary": "Generated from current browsing context",
            }

        dashboard = normalize_dashboard_payload(template_data, domain_name)

        return {
            **state,
            "selected_template": template_id,
            "template_data": template_data,
            "dashboard": dashboard,
            "error": None,
        }

    except Exception as e:
        return {**state, "error": f"Dashboard generation failed: {str(e)}"}


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)
    workflow.add_node("generate_payload", generate_dashboard_payload_node)
    workflow.set_entry_point("generate_payload")
    workflow.add_edge("generate_payload", END)
    return workflow.compile()
