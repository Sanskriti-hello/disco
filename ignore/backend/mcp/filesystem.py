import os
from typing import List, Dict, Any

class FilesystemMCP:
    def __init__(self):
        # Restrict to safe directory
        self.root_dir = os.path.abspath(os.getenv("PROJECT_ROOT", "."))

    def list_files(self, path: str = ".") -> List[str]:
        """List files in the directory."""
        print(f"[FilesystemMCP] Listing files in: {path}")
        # In real usage, ensure path is within allowed root
        return ["backend/", "frontend/", "README.md", "requirements.txt"]

    def read_file(self, path: str) -> str:
        """Read content of a file."""
        print(f"[FilesystemMCP] Reading file: {path}")
        return "# Mock file content\ndef main():\n    print('Hello World')"

    def get_git_status(self) -> Dict[str, Any]:
        """Get current git branch and status."""
        return {
            "branch": "main",
            "modified": ["backend/mcp/filesystem.py"]
        }

filesystem_mcp = FilesystemMCP()
