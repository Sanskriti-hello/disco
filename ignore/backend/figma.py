# backend/mcp/figma.py
"""
Figma REST API client (MCP data source for UI templates)

Fetches design file metadata, specific nodes/components, and export images.
Used by domains/* and ui_engine/* to retrieve pre-designed widgets/templates.

Authentication: Personal Access Token (PAT) with 'file:read' scope
Create token: https://www.figma.com/developers/api#access-tokens

Required .env variables:
    FIGMA_TOKEN=figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

Rate limits: Tier 1 endpoints (~ file/nodes/images) → generally generous for personal use,
but respect limits especially in production[](https://www.figma.com/developers/api#rate-limits)
"""
#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
#https://mcp.tavily.com/mcp/?tavilyApiKey=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
import os
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse, parse_qs
import re

FIGMA_API_BASE = "https://api.figma.com/v1/"

class FigmaAPIError(Exception):
    """Raised for Figma API errors with status & message"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Figma API error {status_code}: {message}")

def parse_figma_url(url: str) -> Dict[str, str]:
    """
    Parses a Figma URL to extract file_key and node_id.
    Example: https://www.figma.com/design/VPntNOQdUs/name?node-id=0-1
    Returns: {"file_key": "VPntNOQdUs", "node_id": "0:1"}
    """
    parsed = urlparse(url)
    
    # Extract file key (e.g. /design/KEY/Title)
    # Matches /design/KEY or /file/KEY
    match = re.search(r"/(?:design|file)/([^/]+)", parsed.path)
    if not match:
        raise ValueError("Invalid Figma URL: Could not find file key")
    
    file_key = match.group(1)
    
    # Extract node_id from query params
    qs = parse_qs(parsed.query)
    node_id = qs.get("node-id", [None])[0]
    
    if node_id:
        # URL uses hyphens (0-1), API uses colons (0:1)
        node_id = node_id.replace("-", ":")
    
    return {
        "file_key": file_key,
        "node_id": node_id
    }



def _get_headers() -> Dict[str, str]:
    token = os.getenv("FIGMA_TOKEN")
    if not token:
        raise FigmaAPIError(401, "FIGMA_TOKEN not set in .env")
    return {
        "X-Figma-Token": token,
        "Accept": "application/json"
    }


def get_file(file_key: str) -> Dict[str, Any]:
    """
    GET /v1/files/:key
    Returns full file metadata + document structure (can be very large).
    Useful for discovery / debugging.
    """
    url = urljoin(FIGMA_API_BASE, f"files/{file_key}")
    response = requests.get(url, headers=_get_headers())
    if response.status_code != 200:
        raise FigmaAPIError(response.status_code, response.text)
    return response.json()


def get_nodes(
    file_key: str,
    node_ids: List[str],
    depth: int = 2,
    geometry: str = "paths"  # "paths" | "outline" | "" (empty = no vectors)
) -> Dict[str, Any]:
    """
    GET /v1/files/:key/nodes?ids=...&depth=...&geometry=...
    Most important endpoint → fetch specific frames/components for UI templates.
    
    Returns: {"nodes": { "id": node_data, ... }, "components": {...}, ...}
    """
    if not node_ids:
        raise ValueError("At least one node_id required")

    url = urljoin(FIGMA_API_BASE, f"files/{file_key}/nodes")
    params = {
        "ids": ",".join(node_ids),
        "depth": depth,
        "geometry": geometry
    }
    response = requests.get(url, headers=_get_headers(), params=params)
    if response.status_code != 200:
        raise FigmaAPIError(response.status_code, response.text)
    
    return response.json()


def get_image_urls(
    file_key: str,
    node_ids: List[str],
    format: str = "png",       # png | jpg | svg | pdf
    scale: float = 2.0,        # 1–4 (higher = retina)
    contents_only: bool = True # exclude background if true
) -> Dict[str, str]:
    """
    GET /v1/images/:key?ids=...&format=...&scale=...&contents_only=...
    Returns temporary signed URLs to rendered images of nodes (valid ~30 days).
    
    Returns: {"images": {"node_id": "https://s3....", ...}}
    """
    url = urljoin(FIGMA_API_BASE, f"images/{file_key}")
    params = {
        "ids": ",".join(node_ids),
        "format": format,
        "scale": str(scale),
        "contents_only": str(contents_only).lower()
    }
    response = requests.get(url, headers=_get_headers(), params=params)
    if response.status_code != 200:
        raise FigmaAPIError(response.status_code, response.text)
    
    data = response.json()
    if "images" not in data or not data["images"]:
        raise FigmaAPIError(404, "No image URLs returned")
    
    return data["images"]


# ── High-level convenience wrapper (recommended main entry point) ─────────────

def fetch_ui_template(
    file_key: str,
    node_id: str,
    include_preview: bool = True,
    preview_format: str = "png",
    preview_scale: float = 2.0
) -> Dict[str, Any]:
    """
    Fetches a single UI template (frame/component) + optional preview image URL.
    
    Returns dict suitable for ui_engine:
    {
        "node_id": "...",
        "node": { ... full node JSON ... },
        "preview_url": "https://..."   (only if include_preview=True)
    }
    """
    nodes_data = get_nodes(file_key, [node_id], depth=2)
    
    if node_id not in nodes_data.get("nodes", {}):
        raise FigmaAPIError(404, f"Node {node_id} not found in file {file_key}")
    
    result = {
        "node_id": node_id,
        "node": nodes_data["nodes"][node_id],
    }
    
    if include_preview:
        urls = get_image_urls(file_key, [node_id], format=preview_format, scale=preview_scale)
        result["preview_url"] = urls.get(node_id)
    
    return result


# ── Quick test / debug block ─────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    from dotenv import load_dotenv

    load_dotenv()

    FILE_KEY = os.getenv("FIGMA_FILE_KEY")
    NODE_ID = os.getenv("FIGMA_NODE_ID")   # e.g. "45:678" or whatever your widget is

    if not FILE_KEY or not NODE_ID:
        print("Set FIGMA_FILE_KEY and FIGMA_NODE_ID in .env to test")
        exit(1)

    try:
        print("\nFetching UI template...")
        template = fetch_ui_template(FILE_KEY, NODE_ID, include_preview=True)
        print(json.dumps(template, indent=2, default=str))  # str for any non-serializable
    except FigmaAPIError as e:
        print(f"Error {e.status_code}: {e.message}")
    except Exception as e:
        print(f"Unexpected error: {e}")