# backend/figma_to_react.py
"""
Figma to React Converter
Transforms Figma node JSON into React component code

Note: This is a simplified version. For production, consider:
- figma-to-react plugin
- html-to-figma + Anima plugin
- Custom rendering with Figma REST API data
"""

from typing import Dict, Any, List
import json


def figma_node_to_react(
    node_data: Dict[str, Any],
    template_data: Dict[str, Any],
    component_name: str = "DynamicDashboard"
) -> str:
    """
    Convert Figma node JSON to React component code
    
    Args:
        node_data: Figma node JSON from API
        template_data: Data to inject (from domain agent)
        component_name: Name of React component
    
    Returns:
        React component code as string
    """
    
    # Extract node properties
    node_type = node_data.get("document", {}).get("type", "FRAME")
    node_name = node_data.get("document", {}).get("name", "Unknown")
    
    # Extract layout info
    bounds = node_data.get("document", {}).get("absoluteBoundingBox", {})
    width = bounds.get("width", 800)
    height = bounds.get("height", 600)
    
    # Generate component
    return f"""import React from 'react';

/**
 * {component_name}
 * Generated from Figma: {node_name}
 * Type: {node_type}
 * Dimensions: {width}x{height}
 */

export const {component_name} = (props) => {{
  // Extract data from props
  const {{
    title = "Dashboard",
    data = [],
    timestamp = new Date().toISOString()
  }} = props;

  return (
    <div 
      className="w-full min-h-screen bg-gradient-to-br from-gray-900 to-black p-6"
      style={{{{ maxWidth: '{width}px' }}}}
    >
      {{/* Header */}}
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2">
          {{title}}
        </h1>
        <p className="text-gray-400 text-sm">
          Generated from Figma template: {node_name}
        </p>
      </header>

      {{/* Main Content */}}
      <main className="space-y-6">
        {{/* Render dynamic content */}}
        {{data && data.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {{data.map((item, index) => (
              <div 
                key={{index}}
                className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/20"
              >
                <h3 className="text-white font-semibold mb-2">
                  {{item.title || `Item ${{index + 1}}`}}
                </h3>
                <p className="text-gray-300 text-sm">
                  {{item.description || "No description"}}
                </p>
              </div>
            ))}}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-400">No data available</p>
          </div>
        )}}
      </main>

      {{/* Footer */}}
      <footer className="mt-8 text-center text-gray-500 text-xs">
        Last updated: {{new Date(timestamp).toLocaleString()}}
      </footer>
    </div>
  );
}};

export default {component_name};
"""


def generate_dashboard_component(
    figma_node_id: str,
    figma_preview_url: str,
    template_name: str,
    template_data: Dict[str, Any],
    domain: str
) -> str:
    """
    Generate complete dashboard component with proper data binding
    
    This is the function called by the render_ui_node in LangGraph
    """
    
    # Extract data structure
    data_items = []
    
    # Domain-specific data extraction
    if domain == "study":
        papers = template_data.get("papers", [])
        data_items = [
            {
                "title": p.get("title", ""),
                "description": p.get("summary", ""),
                "url": p.get("url", "")
            }
            for p in papers
        ]
    
    elif domain == "shopping":
        products = template_data.get("products", [])
        data_items = [
            {
                "title": p.get("title", ""),
                "description": f"Price: {p.get('price', 'N/A')}",
                "url": p.get("url", "")
            }
            for p in products
        ]
    
    elif domain == "travel":
        flights = template_data.get("flights", [])
        data_items = [
            {
                "title": f"{f.get('airline', '')} - {f.get('price', '')}",
                "description": f"{f.get('departureTime', '')} → {f.get('arrivalTime', '')}",
                "url": f.get("bookingUrl", "")
            }
            for f in flights
        ]
    
    else:
        # Generic fallback
        data_items = template_data.get("items", [])
    
    # Generate component
    return f"""import React from 'react';

/**
 * {template_name} Dashboard
 * Domain: {domain}
 * Figma Node: {figma_node_id}
 * Preview: {figma_preview_url}
 */

export const {template_name.replace(' ', '')} = () => {{
  const data = {json.dumps(data_items, indent=4)};
  
  const template_data = {json.dumps(template_data, indent=4)};

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-black p-8">
      {{/* Background Effects */}}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-blue-500 rounded-full filter blur-3xl opacity-20 animate-pulse" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-500 rounded-full filter blur-3xl opacity-20 animate-pulse" />
      </div>

      <div className="relative max-w-7xl mx-auto">
        {{/* Header */}}
        <header className="mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">
            {template_name}
          </h1>
          <p className="text-gray-300 text-lg">
            Powered by AI • Generated from your browser tabs
          </p>
        </header>

        {{/* Content Grid */}}
        <main className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {{data.map((item, index) => (
            <article 
              key={{index}}
              className="group bg-white/10 backdrop-blur-xl rounded-2xl p-6 border border-white/20 hover:border-purple-400 hover:bg-white/15 transition-all duration-300 cursor-pointer"
            >
              <h3 className="text-white font-bold text-xl mb-3 group-hover:text-purple-300 transition-colors">
                {{item.title}}
              </h3>
              <p className="text-gray-300 text-sm mb-4 line-clamp-3">
                {{item.description}}
              </p>
              {{item.url && (
                <a 
                  href={{item.url}} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-purple-400 hover:text-purple-300 text-sm font-medium inline-flex items-center gap-2"
                >
                  View More
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={{2}} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </a>
              )}}
            </article>
          ))}}
        </main>

        {{/* Figma Preview Link */}}
        <footer className="mt-12 text-center">
          <a 
            href="{figma_preview_url}"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block text-gray-400 hover:text-white text-sm transition-colors"
          >
            View Figma Design →
          </a>
        </footer>
      </div>
    </div>
  );
}};

export default {template_name.replace(' ', '')};
"""


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # Test generation
    template_data = {
        "papers": [
            {
                "title": "Attention Is All You Need",
                "summary": "Introduces Transformer architecture...",
                "url": "https://arxiv.org/abs/1706.03762"
            },
            {
                "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                "summary": "Revolutionary NLP model...",
                "url": "https://arxiv.org/abs/1810.04805"
            }
        ]
    }
    
    code = generate_dashboard_component(
        figma_node_id="123:456",
        figma_preview_url="https://figma.com/preview.png",
        template_name="PaperList",
        template_data=template_data,
        domain="study"
    )
    
    print(code)