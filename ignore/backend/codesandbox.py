"""
CodeSandbox Integration Module (Async)
=====================================
Creates real CodeSandbox previews from generated React code using the verified Define API.
"""

import os
import json
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class SandboxResult:
    """Result from CodeSandbox creation."""
    success: bool
    sandbox_id: Optional[str] = None
    embed_url: Optional[str] = None
    preview_url: Optional[str] = None
    error: Optional[str] = None


class CodeSandboxClient:
    """
    Client for creating and managing CodeSandbox previews.
    Uses the verified /api/v1/sandboxes/define endpoint.
    """
    
    # Using the verified working endpoint
    API_URL = "https://codesandbox.io/api/v1/sandboxes/define?json=1"
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("CODESANDBOX_API_TOKEN") or os.getenv("SANDBOX_API")
        # Note: Define API often works without token for public sandboxes, 
        # but we'll include it if present.
    
    async def create_sandbox(
        self,
        jsx_code: Optional[str] = None,
        title: Optional[str] = None,
        additional_files: Optional[Dict[str, str]] = None,
        complete_files: Optional[Dict[str, Dict[str, str]]] = None
    ) -> SandboxResult:
        """
        Create a new CodeSandbox from React JSX code asynchronously.
        
        Args:
            jsx_code: Single JSX component (legacy mode)
            title: Sandbox title
            additional_files: Additional files to include (legacy mode)
            complete_files: Complete file structure from SandboxBuilder (NEW)
        
        Returns: SandboxResult with sandbox URLs
        """
        title = title or f"GenTab Dashboard - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # NEW: Use complete_files if provided (full template structure)
        if complete_files:
            print("📦 Using complete template file structure")
            files = complete_files
        else:
            # LEGACY: Build basic structure from single JSX file
            print("⚠️ Using legacy single-file mode with Tailwind CDN")
            
            # Add Tailwind CDN for styling
            index_html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>body { background-color: #050510; color: white; }</style>
</head>
<body>
    <div id="root"></div>
    <script src="index.js"></script>
</body>
</html>
"""
            
        # Try to get the template's specific CSS
        css_content = "body { background-color: #050510; color: white; }"
        if additional_files and "styles.css" in additional_files:
            css_content = additional_files.pop("styles.css")
            
        # Check for props to inject
        props_json = "{}"
        if additional_files and "props.json" in additional_files:
            props_json = additional_files.pop("props.json")

        # Generate index.js, injecting the data directly as a JS object
        index_js_content = f"""import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';

const props = {props_json};
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App {{...props}} />
  </React.StrictMode>
);"""
            
        files = {
            "index.html": { "content": index_html_content },
            "App.jsx": {
                "content": jsx_code or "export default () => 'No code provided';"
            },
            "index.js": { "content": index_js_content },
            "styles.css": { "content": css_content },
            "package.json": {
                "content": json.dumps({
                    "name": "gentab-dashboard-legacy",
                    "version": "1.0.0",
                    "main": "index.js",
                    "dependencies": {
                        "react": "^18.2.0",
                        "react-dom": "^18.2.0",
                        "react-router-dom": "^6.22.0"
                    }
                }, indent=2)
            }
        }
        
        if additional_files:
            for filename, code in additional_files.items():
                if filename == "styles.css": # Explicitly skip styles.css
                    continue
                files[filename] = {"content": code}
        
        payload = {
            "files": files
        }
        
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    sandbox_id = data.get("sandbox_id")
                    if sandbox_id:
                        # Use preview-only embed to avoid SSE deprecation issues
                        # &view=preview shows only the preview pane (no editor)
                        # &disable_devtools=1 disables telemetry/analytics
                        # &disable_sandpack=1 disables sandpack runtime telemetry
                        return SandboxResult(
                            success=True,
                            sandbox_id=sandbox_id,
                            embed_url=f"https://codesandbox.io/embed/{sandbox_id}?fontsize=14&hidenavigation=1&theme=dark&view=preview&codemirror=1&disable_devtools=1&disable_sandpack=1",
                            preview_url=f"https://codesandbox.io/s/{sandbox_id}"
                        )
                    else:
                        return SandboxResult(success=False, error="No sandbox_id in response")
                else:
                    return SandboxResult(success=False, error=f"API Error {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                return SandboxResult(success=False, error=str(e))


async def create_react_sandbox(jsx_code: str, title: Optional[str] = None) -> SandboxResult:
    try:
        client = CodeSandboxClient()
        return await client.create_sandbox(jsx_code, title)
    except Exception as e:
        return SandboxResult(success=False, error=str(e))
