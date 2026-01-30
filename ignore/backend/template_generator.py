"""
Template Generator - Local Template System
Replaces figma.py with local React component loading and data injection
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
    NEW IMPLEMENTATION using local templates
    
    Args:
        domain: Selected domain (study, shopping, code, generic, etc.)
        template_data: Data from domain agent (already transformed)
        user_context: Tab info, keywords, user_prompt
    
    Returns: Complete React component code ready for CodeSandbox
    """
    from ui_templates.template_loader import TemplateLoader
    from domains import get_domain
    
    loader = TemplateLoader()
    
    
    # 1. Select the best template
    # figma_url is deprecated in loader.select_template, using context instead
    template_info = loader.select_template(
        domain=domain, 
        keywords=user_context.get("keywords", []),
        user_prompt=user_context.get("user_prompt", ""),
        tab_count=user_context.get("tab_count", 0),
        tab_urls=user_context.get("tab_urls", [])
    )
    print(f"🎨 Selected template: {template_info['template_id']} (score: {template_info['score']:.2f})")
    
    # 2. Extract specific data needed for the template
    try:
        domain_agent = get_domain(domain)
        # Transform general MCP data into template-specific props
        template_props = domain_agent.prepare_template_data(
            template_info['template_id'],
            template_data,
            "" # Empty response for now as injection happens via LLM
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
        # Fallback to simple component
        return generate_fallback_component(template_data, domain)
    
    # 4. Inject data into template using LLM
    try:
        # Try LLM-based injection
        from ui_templates.llm_data_injector import LLMDataInjector
        llm_injector = LLMDataInjector()
        
        print(f"💉 Injecting data using LLM into: {template_info['template_id']}")
        final_code = await llm_injector.inject_data_with_llm(
            react_code=react_code,
            template_id=template_info['template_id'],
            data=template_props,
            theme_config=theme_config
        )
        
        print(f"✅ Generated {len(final_code)} chars of React code (LLM injection)")
        
        # Ensure the component exports properly
        final_code = ensure_proper_export(final_code, template_info)
        
        return final_code
        
    except Exception as e:
        print(f"❌ LLM Data injection failed: {e}. Falling back to regex.")
        try:
            from ui_templates.data_injector import DataInjector
            injector = DataInjector()
            final_code = injector.inject_data(
                react_code=react_code,
                template_id=template_info['template_id'],
                data=template_props,
                theme_config=theme_config
            )
            return ensure_proper_export(final_code, template_info)
        except:
            return generate_fallback_component(template_data, domain)


def ensure_proper_export(react_code: str, template_info: Dict) -> str:
    """
    Ensure the React component has proper default export for CodeSandbox
    
    Args:
        react_code: Generated React code
        template_info: Template metadata
    
    Returns: React code with proper export
    """
    # If already has default export, return as is
    if "export default" in react_code:
        return react_code
    
    # Otherwise, add default export
    # Extract the main component name from the file
    import re
    
    # Look for const ComponentName or function ComponentName
    match = re.search(r'(?:const|function)\s+(\w+)\s*=', react_code)
    if match:
        component_name = match.group(1)
        react_code += f"\n\nexport default {component_name};"
        return react_code
    
    # If still no match, just return original
    return react_code


def generate_fallback_component(data: Dict[str, Any], domain: str) -> str:
    """
    Generate a simple fallback React component when template loading fails
    
    Args:
        data: Template data
        domain: Domain name
    
    Returns: Basic React component with data display
    """
    title = data.get("title", f"{domain.title()} Dashboard")
    
    # Generate a simple list of items
    items_html = ""
    
    # Try different data field names
    items = data.get("items", data.get("links", data.get("products", data.get("papers", []))))
    
    if isinstance(items, list) and items:
        items_li = []
        for item in items[:10]:
            if isinstance(item, dict):
                item_title = item.get("title", item.get("name", "Item"))
                item_url = item.get("url", "#")
                items_li.append(f'<li><a href="{item_url}" className="text-blue-400 hover:underline">{item_title}</a></li>')
        
        if items_li:
            items_html = f"<ul className='list-disc pl-5 space-y-2'>{''.join(items_li)}</ul>"
    
    component = f"""
import React from 'react';

const FallbackDashboard = () => {{
  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-6">{title}</h1>
        <div className="bg-gray-800 rounded-lg p-6">
          {items_html if items_html else '<p className="text-gray-400">No data available</p>'}
        </div>
      </div>
    </div>
  );
}};

export default FallbackDashboard;
"""
    
    return component


# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================

def generate_dashboard_component(
    figma_node_id: str,
    figma_preview_url: str,
    template_name: str,
    template_data: Dict[str, Any],
    domain: str
) -> str:
    """
    ⚠️ DEPRECATED - Maintained for backward compatibility
    
    This function signature matches the old figma.py interface.
    It now delegates to the new generate_dashboard_from_template function.
    """
    print("⚠️ Using deprecated generate_dashboard_component - please update to generate_dashboard_from_template")
    
    # Extract keywords from template_name for context
    keywords = template_name.lower().split()
    
    user_context = {
        "keywords": keywords,
        "user_prompt": template_data.get("response", ""),
        "tab_count": len(template_data.get("tabs", [])),
        "tab_urls": [tab.get("url", "") for tab in template_data.get("tabs", [])] if "tabs" in template_data else []
    }
    
    return generate_dashboard_from_template(domain, template_data, user_context)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # Test with sample data
    test_data = {
        "title": "Test Dashboard",
        "items": [
            {"title": "Item 1", "url": "https://example.com", "summary": "Test item 1"},
            {"title": "Item 2", "url": "https://example.com", "summary": "Test item 2"}
        ]
    }
    
    test_context = {
        "keywords": ["test", "dashboard"],
        "user_prompt": "show me test data",
        "tab_count": 5,
        "tab_urls": ["https://example.com"]
    }
    
    print("=== TESTING TEMPLATE GENERATOR ===")
    result = generate_dashboard_from_template("generic", test_data, test_context)
    print(f"\nGenerated {len(result)} characters")
    print(f"\nFirst 500 chars:\n{result[:500]}")
