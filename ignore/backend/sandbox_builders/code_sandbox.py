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


class CodeAppSandboxBuilder:
    """Builds plain React CodeSandbox projects from existing directory structure"""

    def __init__(self, project_dir: Optional[Path] = None,context:str):
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
                        content=update_json(content)
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
    def update_json(self,content)->None:
        data=json.loads(content)
        

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


# ============================================================================
# CLI / MAIN
# ============================================================================

if __name__ == "__main__":
    import sys

    project_path = Path(__file__).parent if len(sys.argv) < 2 else Path(sys.argv[1])

    builder = CodeAppSandboxBuilder(project_path)

    # Build sandbox
    sandbox_files = builder.build_sandbox()

    print(f"\n✅ Shopping App Sandbox Builder")
    print(f"📁 Project directory: {project_path}")
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
    if len(sys.argv) > 2 and sys.argv[2] == "--export":
        export_file = Path(sys.argv[3] if len(sys.argv) > 3 else "sandbox_export.json")
        builder.export_to_json(export_file)
