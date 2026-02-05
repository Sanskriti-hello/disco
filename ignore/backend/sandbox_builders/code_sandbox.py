"""
Shopping App Sandbox Builder – Plain React (No Vite)
Browser-sandbox compatible builder using os.walk
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
from mcp_tools.search import SearchClient

SearchAgent=SearchClient(os.getenv('RAPID_API_KEY'),os.getenv('TAVILY_KEY'))

def update_json(content: str, context: str) -> str:
    data = json.loads(content)
    if "dependencies" in data:
        data["dependencies"]["context"] = context
    return json.dumps(data, indent=2)

class CodeAppSandboxBuilder:
    """Builds plain React CodeSandbox projects from existing directory structure"""

    def __init__(self, context:str, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(__file__).parent
        self.context=context

    def build_sandbox(self) -> Dict[str, Dict[str, str]]:
        """Walk through project directory and collect all files for sandbox"""
        files: Dict[str, Dict[str, str]] = {}

        # Copy all existing files from project directory
        files = self._collect_all_files(files, self.project_dir)

        return files

    # =========================================================================
    # FILE COLLECTION
    # =========================================================================

    def _collect_all_files(
        self,
        files: Dict[str, Dict[str, str]],
        root_path: Path
    ) -> Dict[str, Dict[str, str]]:
        """Walk directory tree and collect all readable files"""

        SKIP_DIRS = {".git", "node_modules", "dist", "__pycache__", ".vscode", ".next"}
        SKIP_EXTS = {".pyc", ".DS_Store", ".pyo"}
        SKIP_FILES = {"sandbox_builder.py"}

        for root, dirs, filenames in os.walk(root_path):
            # Filter out directories we should skip
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in filenames:
                # Skip specific files and extensions
                if filename in SKIP_FILES or Path(filename).suffix in SKIP_EXTS:
                    continue
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(root_path)
                str_path = str(rel_path).replace("\\", "/")

                try:
                    content = file_path.read_text(encoding="utf-8")
                    if filename.endswith('.json'):
                        content=update_json(content, self.context)
                    files[str_path] = {"content": content}
                except UnicodeDecodeError:
                    # Skip binary files (CodeSandbox limitation)
                    pass
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")

        return files

    # =========================================================================
    # EXPORT METHODS
    # =========================================================================

    def export_to_json(self, output_path: Path) -> None:
        """Export sandbox files to JSON format"""
        sandbox_data = self.build_sandbox()
        output_path.write_text(json.dumps(sandbox_data, indent=2))
        print(f"Exported {len(sandbox_data)} files to {output_path}")

    def export_to_codesandbox_format(self) -> Dict[str, Dict[str, str]]:
        """Return files in CodeSandbox API format"""
        return self.build_sandbox()

    def get_file_summary(self) -> Dict[str, int]:
        """Get a summary of file types in the project"""
        files = self.build_sandbox()
        summary: Dict[str, int] = {}

        for filepath in files.keys():
            ext = Path(filepath).suffix or "no_ext"
            summary[ext] = summary.get(ext, 0) + 1

        return summary

    def create_codesandbox_url(self) -> tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        Create a CodeSandbox and return URLs
        
        Returns:
            Tuple of (success, sandbox_id, embed_url, preview_url)
        """
        try:
            import requests
            
            api_key = os.getenv("SANDBOX_API")
            if not api_key:
                print("⚠️ SANDBOX_API environment variable not set")
                return (False, None, None, "No API key")
            
            files = self.build_sandbox()
            
            # CodeSandbox Define API
            payload = {"files": files}
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            print(f"📤 Uploading {len(files)} files to CodeSandbox...")
            
            response = requests.post(
                "https://codesandbox.io/api/v1/sandboxes/define",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                sandbox_id = data.get("sandbox_id")
                embed_url = f"https://codesandbox.io/embed/{sandbox_id}"
                preview_url = f"https://codesandbox.io/s/{sandbox_id}"
                
                print(f"✅ CodeSandbox created: {sandbox_id}")
                print(f"   Embed: {embed_url}")
                print(f"   Preview: {preview_url}")
                
                return (True, sandbox_id, embed_url, preview_url)
            else:
                error_msg = f"API error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return (False, None, None, error_msg)
                
        except Exception as e:
            print(f"❌ CodeSandbox creation failed: {e}")
            return (False, None, None, str(e))


# ============================================================================
# CLI / MAIN
# ============================================================================

if __name__ == "__main__":
    import sys

    # Assuming 'context' is provided as the first argument, and 'project_path' as the second optional argument
    # This part might need adjustment based on how 'CodeAppSandboxBuilder' is instantiated in the main script.
    # For now, let's assume a dummy context if not provided for CLI execution.
    _cli_context = "default_cli_context"
    _cli_project_path = None

    if len(sys.argv) > 1:
        _cli_context = sys.argv[1]
    if len(sys.argv) > 2:
        _cli_project_path = Path(sys.argv[2])

    builder = CodeAppSandboxBuilder(context=_cli_context, project_dir=_cli_project_path)

    # Build sandbox
    sandbox_files = builder.build_sandbox()

    print(f"\n✅ Shopping App Sandbox Builder")
    print(f"📁 Project directory: {builder.project_dir}")
    print(f"📦 Total files collected: {len(sandbox_files)}\n")

    # Show file summary
    summary = builder.get_file_summary()
    print("📊 File types:")
    for ext, count in sorted(summary.items(), key=lambda x: x[1], reverse=True):
        print(f"   {ext}: {count} file(s)")

    # List all files
    print("\n📄 Files in sandbox:")
    for filepath in sorted(sandbox_files.keys()):
        print(f"   - {filepath}")

    # Optional: Export to JSON
    if "--export" in sys.argv:
        export_index = sys.argv.index("--export")
        export_file = Path(sys.argv[export_index + 1] if len(sys.argv) > export_index + 1 else "sandbox_export.json")
        builder.export_to_json(export_file)


# ============================================================================
# CODESANDBOX CLIENT
# ============================================================================

import httpx
from dataclasses import dataclass
from datetime import datetime


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
    Client for creating CodeSandbox previews from existing project files.
    Integrates with SandboxBuilder to use real project structure.
    """

    API_URL = "https://codesandbox.io/api/v1/sandboxes/define?json=1"

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("SANDBOX_API")

    async def create_sandbox(
        self,
        sandbox_files: Dict[str, Dict[str, str]],
        title: Optional[str] = None
    ) -> SandboxResult:
        """
        Create a CodeSandbox preview from SandboxBuilder files.
        
        Args:
            sandbox_files: Files dict from SandboxBuilder.build_sandbox()
            title: Optional custom title
        """
        
        title = title or f"Dashboard – {datetime.now():%Y%m%d_%H%M%S}"

        payload = {"files": sandbox_files}

        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        async with httpx.AsyncClient() as client:
            try:
                print(f"📤 Uploading {len(sandbox_files)} files to CodeSandbox...")
                
                resp = await client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                    timeout=30.0,
                )

                # Raise for non-2xx responses
                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError:
                    return SandboxResult(
                        success=False,
                        error=f"API Error {resp.status_code}: {resp.text[:200]}",
                    )

                # Ensure response is valid JSON
                try:
                    data = resp.json()
                except ValueError:
                    return SandboxResult(success=False, error="Invalid JSON response from API")

                sandbox_id = data.get("sandbox_id")
                if not sandbox_id:
                    return SandboxResult(success=False, error="No sandbox_id in response")

                embed_url = f"https://codesandbox.io/embed/{sandbox_id}?fontsize=14&hidenavigation=1&theme=dark&view=preview"
                preview_url = f"https://codesandbox.io/s/{sandbox_id}"

                print(f"✅ CodeSandbox created: {sandbox_id}")
                print(f"   Embed: {embed_url}")
                print(f"   Preview: {preview_url}")

                return SandboxResult(
                    success=True,
                    sandbox_id=sandbox_id,
                    embed_url=embed_url,
                    preview_url=preview_url,
                )

            except httpx.RequestError as e:
                return SandboxResult(success=False, error=f"Request error: {e}")
            except Exception as e:
                return SandboxResult(success=False, error=str(e))


async def deploy_to_codesandbox(
    sandbox_files: Dict[str, Dict[str, str]],
    title: Optional[str] = None
) -> SandboxResult:
    """
    Deploy sandbox files to CodeSandbox.
    """
    client = CodeSandboxClient()
    return await client.create_sandbox(sandbox_files, title)