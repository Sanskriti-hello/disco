"""
CodeSandbox Integration Module (Async)
=====================================
Creates real CodeSandbox previews from generated React code using httpx.
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
    """
    
    API_URL = "https://api.codesandbox.io/api/v1/sandboxes"
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("CODESANDBOX_API_TOKEN") or os.getenv("SANDBOX_API")
        if not self.api_token:
            raise ValueError("CodeSandbox API token is required. Set CODESANDBOX_API_TOKEN or SANDBOX_API in .env")
    
    async def create_sandbox(
        self,
        jsx_code: str,
        title: Optional[str] = None,
        additional_files: Optional[Dict[str, str]] = None
    ) -> SandboxResult:
        """
        Create a new CodeSandbox from React JSX code asynchronously.
        """
        title = title or f"GenTab Dashboard - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Build the files structure according to the official guide
        files = {
            "App.jsx": {
                "code": jsx_code,
                "isBinary": False
            },
            "index.js": {
                "code": """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);""",
                "isBinary": False
            },
            "styles.css": {
                "code": """/* Base styles for GenTab Dashboard */
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Inter', system-ui, sans-serif;
  background: #050510;
  color: white;
  min-height: 100vh;
}
""",
                "isBinary": False
            },
            "package.json": {
                "code": json.dumps({
                    "name": "gentab-dashboard",
                    "version": "1.0.0",
                    "main": "index.js",
                    "dependencies": {
                        "react": "^18.2.0",
                        "react-dom": "^18.2.0"
                    }
                }, indent=2),
                "isBinary": False
            }
        }
        
        if additional_files:
            for filename, code in additional_files.items():
                files[filename] = {"code": code, "isBinary": False}
        
        payload = {
            "template": "react",
            "title": title,
            "files": files
        }
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    self.API_URL,
                    headers={"Authorization": f"Bearer {self.api_token}"},
                    json=payload,
                    timeout=30.0
                )
                data = resp.json()
                
                if resp.status_code in [200, 201]:
                    sandbox_id = data.get("sandbox_id") or data.get("id")
                    return SandboxResult(
                        success=True,
                        sandbox_id=sandbox_id,
                        embed_url=f"https://codesandbox.io/embed/{sandbox_id}?fontsize=14&hidenavigation=1&theme=dark",
                        preview_url=f"https://codesandbox.io/p/sandbox/{sandbox_id}"
                    )
                else:
                    return SandboxResult(success=False, error=data.get("message", f"API Error {resp.status_code}"))
            except Exception as e:
                return SandboxResult(success=False, error=str(e))


async def create_react_sandbox(jsx_code: str, title: Optional[str] = None) -> SandboxResult:
    try:
        client = CodeSandboxClient()
        return await client.create_sandbox(jsx_code, title)
    except Exception as e:
        return SandboxResult(success=False, error=str(e))
