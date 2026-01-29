"""
COMPLETE WORKFLOW - End-to-End Dashboard Generation
Shows how all pieces fit together
"""

import os
import json
from typing import Dict, Any, List
from datetime import datetime

# ============================================================================
# STEP 1: Domain Agent Processes Tabs + MCP Data
# ============================================================================

def process_domain_logic(domain: str, tabs: List[Dict], user_prompt: str) -> Dict[str, Any]:
    """
    Execute domain-specific logic to extract structured data
    
    Returns:
    {
        "template_hint": "PaperList",  # Suggested template name
        "ui_props": {...},              # Data to populate template
        "keywords": ["research", "ml"], # For Figma search
    }
    """
    
    from domains import get_domain
    
    domain_instance = get_domain(domain)
    
    # 1. Get required MCPs
    required_mcps = domain_instance.get_required_mcps(user_prompt)
    print(f"[{domain}] Required MCPs: {required_mcps}")
    
    # 2. Fetch MCP Data (CRITICAL: Must be implemented per MCP)
    mcp_data = fetch_mcp_data(required_mcps, tabs, user_prompt)
    
    # 3. Validate data
    if not domain_instance.validate_data(mcp_data):
        follow_up = domain_instance.get_follow_up_question(mcp_data)
        return {
            "error": "Insufficient data",
            "follow_up": follow_up,
            "needs_more_data": True
        }
    
    # 4. Get template selection from domain
    selected_template = domain_instance.select_ui_template(mcp_data)
    
    # 5. Prepare UI props (CRITICAL: Domain-specific data transformation)
    llm_response = f"Analysis complete for {domain}"  # In real version, call LLM
    ui_props = domain_instance.prepare_ui_props(mcp_data, llm_response)
    
    # 6. Extract keywords for Figma search
    keywords = extract_keywords_from_tabs(tabs) + user_prompt.split()
    
    return {
        "template_hint": selected_template,
        "ui_props": ui_props,
        "keywords": list(set(keywords))[:20],
        "domain": domain,
        "needs_more_data": False
    }


# ============================================================================
# STEP 2: Fetch MCP Data (WITH ERROR HANDLING)
# ============================================================================

def fetch_mcp_data(required_mcps: List[str], tabs: List[Dict], user_prompt: str) -> Dict[str, Any]:
    """
    Fetch data from required MCPs with proper error handling
    """
    
    mcp_data = {
        "timestamp": datetime.now().isoformat(),
        "browser": {
            "tabs": tabs,
            "tab_count": len(tabs)
        }
    }
    
    # Import MCPs dynamically to avoid crashes
    for mcp_name in required_mcps:
        try:
            if mcp_name == "search":
                from mcp.search import search_mcp
                mcp_data["search"] = search_mcp.search(user_prompt)
            
            elif mcp_name == "arxiv":
                from mcp.arxiv import arxiv_mcp
                mcp_data["arxiv"] = arxiv_mcp.search_papers(user_prompt)
            
            elif mcp_name == "location":
                from mcp.location import location_mcp
                mcp_data["location"] = location_mcp.get_current_location()
            
            elif mcp_name == "google_workspace":
                from mcp.google_workspace import google_workspace_mcp
                mcp_data["google_workspace"] = {
                    "calendar": google_workspace_mcp.get_calendar_events()
                }
            
            elif mcp_name == "filesystem":
                from mcp.filesystem import filesystem_mcp
                mcp_data["filesystem"] = {
                    "files": filesystem_mcp.list_files()
                }
            
            # Add more MCPs as needed
            
        except ImportError as e:
            print(f"⚠️ MCP '{mcp_name}' not available: {e}")
            # Continue without this MCP - domain should handle missing data
        
        except Exception as e:
            print(f"❌ Error fetching {mcp_name}: {e}")
    
    return mcp_data


# ============================================================================
# STEP 3: Select Figma Template
# ============================================================================

def select_figma_template(
    domain: str,
    keywords: List[str],
    template_hint: str = None
) -> Dict[str, Any]:
    """
    Select best Figma template using enhanced Figma API
    
    Returns:
    {
        "node_id": "123:456",
        "node_name": "PaperList",
        "preview_url": "https://...",
        "figma_data": {...}
    }
    """
    
    from fixed_figma import select_best_template, parse_figma_url
    
    # Get Figma file URL from environment or config
    figma_file_key = os.getenv("FIGMA_FILE_KEY")
    
    if not figma_file_key:
        print("⚠️ No FIGMA_FILE_KEY found, using mock template")
        return {
            "node_id": "mock:123",
            "node_name": template_hint or "GenericTemplate",
            "preview_url": None,
            "figma_data": {}
        }
    
    try:
        # Use enhanced Figma API to find best template
        result = select_best_template(
            file_key=figma_file_key,
            keywords=keywords,
            domain=domain,
            user_prompt=""
        )
        
        return {
            "node_id": result["node_id"],
            "node_name": result["name"],
            "preview_url": result.get("preview_url"),
            "figma_data": result.get("node_data", {})
        }
        
    except Exception as e:
        print(f"❌ Figma selection failed: {e}")
        return {
            "node_id": "fallback:generic",
            "node_name": "GenericDashboard",
            "preview_url": None,
            "figma_data": {}
        }


# ============================================================================
# STEP 4: Convert Figma to React
# ============================================================================

def convert_figma_to_react(
    figma_data: Dict[str, Any],
    ui_props: Dict[str, Any],
    template_name: str
) -> str:
    """
    Convert Figma node structure to React component code
    
    NOTE: This is a SIMPLIFIED version. In production, use:
    - figma-to-react plugin
    - Anima plugin
    - Custom parser based on Figma API response
    """
    
    # For now, generate a generic React component
    # TODO: Replace with actual Figma-to-React conversion
    
    props_json = json.dumps(ui_props, indent=2)
    
    return f"""
import React from 'react';

/**
 * {template_name} Dashboard
 * Auto-generated from Figma
 */

export const {template_name.replace(' ', '')} = () => {{
  const data = {props_json};
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black p-8">
      <div className="max-w-7xl mx-auto">
        {{/* Header */}}
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            {template_name}
          </h1>
          <p className="text-gray-300">
            Generated dashboard based on your tabs
          </p>
        </header>
        
        {{/* Main Content */}}
        <main className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {{data.items && data.items.map((item, i) => (
            <div key={{i}} className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <h3 className="text-white font-semibold mb-2">{{item.title || `Item ${{i + 1}}`}}</h3>
              <p className="text-gray-300 text-sm">{{item.description || "No description"}}</p>
            </div>
          ))}}
        </main>
      </div>
    </div>
  );
}};

export default {template_name.replace(' ', '')};
"""


# ============================================================================
# STEP 5: COMPLETE END-TO-END WORKFLOW
# ============================================================================

async def generate_dashboard(
    domain: str,
    tabs: List[Dict[str, Any]],
    user_prompt: str = ""
) -> Dict[str, Any]:
    """
    🎯 MAIN FUNCTION: Complete dashboard generation workflow
    
    Args:
        domain: Selected domain (study, shopping, travel, etc.)
        tabs: List of browser tabs with content
        user_prompt: Optional user request
    
    Returns:
        Dashboard configuration ready for frontend rendering
    """
    
    print(f"\n{'='*60}")
    print(f"DASHBOARD GENERATION WORKFLOW")
    print(f"{'='*60}\n")
    
    # STEP 1: Process domain logic
    print("1️⃣ Processing domain logic...")
    domain_result = process_domain_logic(domain, tabs, user_prompt)
    
    if domain_result.get("needs_more_data"):
        return {
            "error": domain_result["error"],
            "follow_up": domain_result["follow_up"]
        }
    
    print(f"   ✓ Template hint: {domain_result['template_hint']}")
    print(f"   ✓ Keywords: {domain_result['keywords'][:5]}...")
    
    # STEP 2: Select Figma template
    print("\n2️⃣ Selecting Figma template...")
    figma_result = select_figma_template(
        domain=domain,
        keywords=domain_result["keywords"],
        template_hint=domain_result["template_hint"]
    )
    print(f"   ✓ Selected: {figma_result['node_name']} (ID: {figma_result['node_id']})")
    
    # STEP 3: Convert to React
    print("\n3️⃣ Converting Figma to React code...")
    react_code = convert_figma_to_react(
        figma_data=figma_result["figma_data"],
        ui_props=domain_result["ui_props"],
        template_name=figma_result["node_name"]
    )
    print(f"   ✓ Generated {len(react_code)} chars of React code")
    
    # STEP 4: Return dashboard config
    print("\n4️⃣ Finalizing dashboard config...")
    dashboard_config = {
        "success": True,
        "domain": domain,
        "selected_template": figma_result["node_name"],
        "figma_node_id": figma_result["node_id"],
        "figma_preview_url": figma_result["preview_url"],
        "ui_props": domain_result["ui_props"],
        "react_code": react_code,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"   ✓ Dashboard ready for rendering\n")
    print(f"{'='*60}\n")
    
    return dashboard_config


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_keywords_from_tabs(tabs: List[Dict]) -> List[str]:
    """Extract meaningful keywords from tab titles and content"""
    keywords = []
    
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "is", "are", "was", "were", "be", "been", "being", "have", "has"
    }
    
    for tab in tabs[:10]:  # First 10 tabs
        title = tab.get("title", "").lower()
        content = tab.get("content", "")[:200].lower()
        
        # Extract words
        words = title.split() + content.split()
        
        # Filter
        keywords.extend([
            w for w in words
            if len(w) > 3 and w not in stop_words and w.isalpha()
        ])
    
    return list(set(keywords))


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Mock tabs data
    sample_tabs = [
        {
            "id": 1,
            "title": "Attention Is All You Need - arXiv",
            "url": "https://arxiv.org/abs/1706.03762",
            "content": "We propose a new simple network architecture, the Transformer..."
        },
        {
            "id": 2,
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "url": "https://arxiv.org/abs/1810.04805",
            "content": "We introduce a new language representation model called BERT..."
        },
        {
            "id": 3,
            "title": "ResNet Paper - Deep Residual Learning",
            "url": "https://arxiv.org/abs/1512.03385",
            "content": "Deeper neural networks are more difficult to train..."
        }
    ]
    
    # Run workflow
    result = asyncio.run(generate_dashboard(
        domain="study",
        tabs=sample_tabs,
        user_prompt="Create a research paper dashboard"
    ))
    
    print("\n📊 DASHBOARD CONFIG:")
    print(json.dumps({
        "success": result["success"],
        "domain": result["domain"],
        "template": result["selected_template"],
        "node_id": result["figma_node_id"],
        "props_keys": list(result["ui_props"].keys())
    }, indent=2))
    
    print("\n📝 React Code (first 500 chars):")
    print(result["react_code"][:500] + "...")