"""
CodeSandbox Integration Module (Async)
=====================================
Creates real CodeSandbox previews from generated plain React code
(Browser-sandbox compatible, NO Vite)
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

    API_URL = "https://codesandbox.io/api/v1/sandboxes/define?json=1"

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = (
            api_token
            or os.getenv("CODESANDBOX_API_TOKEN")
            or os.getenv("SANDBOX_API")
        )

    async def create_sandbox(
        self,
        jsx_code: Optional[str] = None,
        title: Optional[str] = None,
        additional_files: Optional[Dict[str, str]] = None,
        complete_files: Optional[Dict[str, Dict[str, str]]] = None
    ) -> SandboxResult:
        """
        Create a CodeSandbox React preview.

        Priority:
        1. complete_files (from SandboxBuilder)
        2. legacy single-component mode
        """

        title = title or f"GenTab Dashboard – {datetime.now():%Y%m%d_%H%M%S}"

        # ==============================================================
        # FULL TEMPLATE MODE (RECOMMENDED)
        # ==============================================================

        if complete_files:
            files = complete_files

        # ==============================================================
        # LEGACY MODE (FIXED FOR BROWSER SANDBOX)
        # ==============================================================

        else:
            if not jsx_code:
                return SandboxResult(success=False, error="jsx_code is required in legacy mode")

            files = {
                "public/index.html": {
                    "content": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>GenTab Preview</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
"""
                },

                "src/index.js": {
                    "content": """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
                },

                "src/App.js": {
                    "content": jsx_code
                },

                "src/styles.css": {
                    "content": """* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI',
    Roboto, sans-serif;
  background: #0a0a1a;
  color: white;
  min-height: 100vh;
}
"""
                },

                "package.json": {
                    "content": json.dumps(
                        {
                            "name": "gentab-dashboard",
                            "version": "1.0.0",
                            "private": True,
                            "dependencies": {
                                "react": "^18.2.0",
                                "react-dom": "^18.2.0",
                                "react-scripts": "5.0.1",
                                "lucide-react": "latest",
                                "clsx": "latest",
                                "tailwind-merge": "latest"
                            },
                            "scripts": {
                                "start": "react-scripts start",
                                "build": "react-scripts build"
                            }
                        },
                        indent=2
                    )
                }
            }

            if additional_files:
                for filename, code in additional_files.items():
                    files[filename] = {"content": code}

        # ==============================================================
        # API REQUEST
        # ==============================================================

        payload = {"files": files}

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )

                if resp.status_code != 200:
                    return SandboxResult(
                        success=False,
                        error=f"API Error {resp.status_code}: {resp.text[:200]}"
                    )

                data = resp.json()
                sandbox_id = data.get("sandbox_id")

                if not sandbox_id:
                    return SandboxResult(success=False, error="No sandbox_id in response")

                return SandboxResult(
                    success=True,
                    sandbox_id=sandbox_id,
                    embed_url=(
                        f"https://codesandbox.io/embed/{sandbox_id}"
                        "?fontsize=14&hidenavigation=1&theme=dark"
                        "&view=preview&disable_devtools=1&disable_sandpack=1"
                    ),
                    preview_url=f"https://codesandbox.io/s/{sandbox_id}"
                )

            except Exception as e:
                return SandboxResult(success=False, error=str(e))


# ============================================================================
# CONVENIENCE WRAPPER
# ============================================================================

async def create_react_sandbox(
    jsx_code: str,
    title: Optional[str] = None
) -> SandboxResult:
    client = CodeSandboxClient()
    return await client.create_sandbox(jsx_code=jsx_code, title=title)
