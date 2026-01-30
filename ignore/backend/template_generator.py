"""
Template Generator - Local Template System (FIXED)
NO Figma, NO dashboard.html fallback - ONLY local templates
"""

import json
from typing import Dict, Any, List
from pathlib import Path


async def generate_dashboard_from_template(
    domain: str,
    template_data: Dict[str, Any],
    user_context: Dict[str, Any]
) -> str:
    """
    Generate React component from local template with data injection
    
    Args:
        domain: Selected domain (study, shopping, code, generic, etc.)
        template_data: Data from domain agent (already transformed)
        user_context: Tab info, keywords, user_prompt
    
    Returns: Complete React component code ready for CodeSandbox
    """
    from ui_templates.template_loader import TemplateLoader
    from ui_templates.data_injector import DataInjector
    from domains import get_domain
    
    loader = TemplateLoader()
    injector = DataInjector()
    
    # 1. Select the best template
    template_info = loader.select_template(
        domain=domain, 
        keywords=user_context.get("keywords", []),
        user_prompt=user_context.get("user_prompt", ""),
        tab_count=user_context.get("tab_count", 0),
        tab_urls=user_context.get("tab_urls", [])
    )
    print(f"🎨 Selected template: {template_info['template_id']} (score: {template_info['score']:.2f})")
    
    # 2. Transform data for template-specific structure
    try:
        domain_agent = get_domain(domain)
        template_props = domain_agent.prepare_template_data(
            template_info['template_id'],
            template_data,
            ""
        )
        print(f"📦 Prepared template data with keys: {list(template_props.keys())}")
    except Exception as e:
        print(f"⚠️ Failed to prepare template data: {e}")
        template_props = template_data
    
    # 3. Load template component from disk
    try:
        react_code = loader.load_template_component(template_info['template_id'])
        theme_config = loader.load_template_config(template_info['template_id'])
        
        print(f"✅ Loaded component: {len(react_code)} chars")
    except Exception as e:
        print(f"❌ Failed to load template: {e}")
        raise Exception(f"Template loading failed: {e}")
    
    # 4. Inject data into template (REGEX ONLY - no LLM dependency)
    try:
        print(f"💉 Injecting data into template: {template_info['template_id']}")
        final_code = injector.inject_data(
            react_code=react_code,
            template_id=template_info['template_id'],
            data=template_props,
            theme_config=theme_config
        )
        
        print(f"✅ Generated {len(final_code)} chars of React code")
        
        # Ensure proper export
        final_code = ensure_proper_export(final_code, template_info)
        
        return final_code
        
    except Exception as e:
        print(f"❌ Data injection failed: {e}")
        raise Exception(f"Data injection failed: {e}")


def ensure_proper_export(react_code: str, template_info: Dict) -> str:
    """Ensure React component has proper default export"""
    if "export default" in react_code:
        return react_code
    
    import re
    match = re.search(r'(?:const|function)\s+(\w+)\s*=', react_code)
    if match:
        component_name = match.group(1)
        react_code += f"\n\nexport default {component_name};"
    
    return react_code