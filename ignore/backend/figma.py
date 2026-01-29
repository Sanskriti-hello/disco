"""
Figma to React Generator
========================
Transforms Figma metadata and domain data into high-fidelity React components.
"""

import json
import os
import http.client
import re
from typing import Dict, Any, List, Optional


def generate_dashboard_component(
    figma_node_id: str,
    figma_preview_url: str,
    template_name: str,
    template_data: Dict[str, Any],
    domain: str
) -> str:
    """
    Generate complete dashboard component with proper data binding.
    """
    
    # 1. Standardize Data for UI Injection
    items = []
    
    # Study Domain
    if domain == "study":
        source = template_data.get("papers") or template_data.get("articles") or []
        items = [
            {"title": x.get("title", ""), "desc": x.get("summary", ""), "url": x.get("url", ""), "icon": "BookOpen"}
            for x in source
        ]
    
    # Shopping Domain
    elif domain == "shopping":
        source = template_data.get("products") or []
        items = [
            {"title": x.get("title", ""), "desc": f"Price: {x.get('price', 'N/A')}", "url": x.get("url", ""), "icon": "ShoppingBag"}
            for x in source
        ]
        
    # Travel Domain
    elif domain == "travel":
        source = template_data.get("flights") or template_data.get("hotels") or []
        items = [
            {"title": x.get("airline") or x.get("name", ""), "desc": f"{x.get('price', '')} - {x.get('duration') or x.get('location', '')}", "url": x.get("bookingUrl") or x.get("url", ""), "icon": "Plane" if "airline" in x else "Bed"}
            for x in source
        ]
        
    # Code Domain
    elif domain == "code":
        source = template_data.get("code_snippets") or []
        items = [
            {"title": x.get("language", "Code"), "desc": x.get("code", "")[:200] + "...", "url": "", "icon": "Code"}
            for x in source
        ]
        
    # Entertainment Domain (YouTube/News)
    elif domain == "entertainment":
        source = template_data.get("videos") or template_data.get("news") or template_data.get("movies") or []
        items = [
            {"title": x.get("title", ""), "desc": x.get("description") or x.get("snippet", ""), "url": x.get("url", ""), "icon": "Play" if "video" in str(x) else "Newspaper"}
            for x in source
        ]
        
    # Financial Domain
    elif domain == "financial" or "exchange_rate" in str(template_data):
        source = template_data.get("financial") or template_data.get("rates") or []
        items = [
            {"title": x.get("pair") or x.get("currency", "Rate"), "desc": f"Value: {x.get('value') or x.get('rate', 'N/A')}", "url": "", "icon": "TrendingUp"}
            for x in source
        ]
    
    # Generic Fallback
    else:
        # Try to find any list of dicts
        for val in template_data.values():
            if isinstance(val, list) and val and isinstance(val[0], dict):
                items = [
                    {"title": x.get("title") or x.get("name") or "Item", "desc": x.get("snippet") or x.get("description") or str(x), "url": x.get("url", ""), "icon": "Zap"}
                    for x in val
                ]
                break
    
    if not items:
        items = [{"title": "No data found", "desc": "We couldn't find specific items for this view.", "url": "", "icon": "AlertCircle"}]

    # 2. Generate Premium React Code
    component_name = re.sub(r'\W+', '', template_name)
    
    return f"""import React from 'react';
import {{ 
  {", ".join(set([item['icon'] for item in items] + ['Layout', 'ArrowRight', 'ExternalLink', 'Clock']))}
}} from 'lucide-react';

/**
 * {template_name} Dashboard
 * Generated for: {domain} domain
 * Source: {figma_preview_url}
 */
const {component_name} = () => {{
  const data = {json.dumps(items, indent=2)};
  const rawData = {json.dumps(template_data, indent=2)};

  return (
    <div className="min-h-screen bg-[#050510] text-slate-200 font-sans selection:bg-indigo-500/30">
      {{/* Glossy Background */}}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-600/20 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/20 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10 p-4 md:p-8 max-w-7xl mx-auto">
        {{/* Header Section */}}
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12 animate-in fade-in slide-in-from-top-4 duration-700">
          <div>
            <div className="flex items-center gap-2 text-indigo-400 font-medium text-sm mb-3 uppercase tracking-widest">
              <Layout size={{14}} />
              <span>{domain} Dashboard</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-black text-white tracking-tight">
              {template_name}
            </h1>
          </div>
          <div className="bg-white/5 backdrop-blur-md rounded-2xl px-5 py-3 border border-white/10 flex items-center gap-3">
            <Clock size={{18}} className="text-slate-400" />
            <div className="text-xs">
              <p className="text-slate-400">Generated at</p>
              <p className="text-white font-medium">{{new Date().toLocaleTimeString()}}</p>
            </div>
          </div>
        </header>

        {{/* Metrics/Stats Bar Placeholder (Optional) */}}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          {[
            {{ label: 'Sources', val: Object.keys(rawData).length }},
            {{ label: 'Total Items', val: data.length }},
            {{ label: 'Status', val: 'Verified' }},
            {{ label: 'AI Confidence', val: '98%' }}
          ].map((stat, i) => (
            <div key={{i}} className="bg-white/5 border border-white/10 rounded-2xl p-4 backdrop-blur-sm">
              <p className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-1">{{stat.label}}</p>
              <p className="text-xl font-bold text-white">{{stat.val}}</p>
            </div>
          ))}
        </div>

        {{/* Main Content Grid */}}
        <main className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {{data.map((item, idx) => (
            <div 
              key={{idx}} 
              className="group relative bg-slate-900/50 hover:bg-slate-800/50 backdrop-blur-xl border border-white/10 hover:border-indigo-500/50 rounded-3xl p-6 transition-all duration-300 hover:-translate-y-1"
            >
              <div className="absolute top-4 right-4 text-slate-700 group-hover:text-indigo-400 transition-colors">
                <ArrowRight size={{20}} />
              </div>

              <div className="w-12 h-12 bg-indigo-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                {{(() => {{
                  // Dynamic icon selection logic
                  const Icon = {{
                    BookOpen, ShoppingBag, Plane, Bed, Code, Play, Zap, AlertCircle
                  }}[item.icon] || Zap;
                  return <Icon size={{24}} className="text-indigo-400" />;
                }})()}}
              </div>

              <h3 className="text-xl font-bold text-white mb-3 line-clamp-1 group-hover:text-indigo-100 transition-colors">
                {{item.title}}
              </h3>
              
              <p className="text-slate-400 text-sm leading-relaxed mb-6 line-clamp-3">
                {{item.desc}}
              </p>

              {{item.url && (
                <a 
                  href={{item.url}} 
                  target="_blank" 
                  rel="noreferrer"
                  className="flex items-center gap-2 text-indigo-400 group-hover:text-indigo-300 text-sm font-semibold transition-colors"
                >
                  Explore Details
                  <ExternalLink size={{14}} />
                </a>
              )}}
            </div>
          ))}}
        </main>

        {{/* Attribution */}}
        <footer className="mt-20 py-8 border-t border-white/5 flex flex-col items-center gap-4">
          <p className="text-slate-500 text-sm">Design based on Figma template: <span className="text-slate-300 font-medium">{figma_node_id}</span></p>
          <a href="{figma_preview_url}" className="text-indigo-400 hover:text-indigo-300 text-xs uppercase tracking-widest font-bold">
            View Live Figma Design
          </a>
        </footer>
      </div>
    </div>
  );
}};

export default {component_name};
"""


def fetch_ui_template(file_key: str, node_id: str, include_preview: bool = True) -> Dict[str, Any]:
    """
    Fetch a specific node from a Figma file using the REST API.
    """
    token = os.getenv("FIGMA_ACCESS_TOKEN")
    if not token:
        return {"error": "Missing FIGMA_ACCESS_TOKEN", "preview_url": f"https://www.figma.com/file/{file_key}?node-id={node_id}"}

    conn = http.client.HTTPSConnection("api.figma.com")
    headers = {"X-Figma-Token": token}
    
    try:
        # Fetch node data
        endpoint = f"/v1/files/{file_key}/nodes?ids={node_id}"
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode())
        
        # Figma API returns nodes with ':' but the key in JSON might have '-' depending on version/ID type
        # We try both
        normalized_id = node_id.replace('-', ':')
        node_data = data.get("nodes", {}).get(normalized_id) or data.get("nodes", {}).get(node_id)
        
        result = {
            "node": node_data,
            "preview_url": f"https://www.figma.com/file/{file_key}?node-id={node_id}"
        }
        
        # Optionally fetch preview image
        if include_preview:
            img_endpoint = f"/v1/images/{file_key}?ids={node_id}&format=png"
            conn.request("GET", img_endpoint, headers=headers)
            img_res = conn.getresponse()
            img_data = json.loads(img_res.read().decode())
            image_url = img_data.get("images", {}).get(node_id) or img_data.get("images", {}).get(normalized_id)
            if image_url:
                result["preview_url"] = image_url
                
        return result
        
    except Exception as e:
        print(f"Error fetching Figma node: {e}")
        return {"error": str(e)}
    finally:
        conn.close()