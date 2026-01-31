"""
CodeSandbox Builder – Plain React (No Vite)
Browser-sandbox compatible
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class SandboxBuilder:
    """Builds plain React CodeSandbox projects (no Vite)"""

    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or Path(__file__).parent

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def build_complete_sandbox(
        self,
        template_id: str,
        injected_component: str,
        data: Dict[str, Any]
    ) -> Dict[str, Dict[str, str]]:

        template_path = self.templates_dir / template_id
        if not template_path.exists():
            raise FileNotFoundError(f"Template directory not found: {template_path}")

        files: Dict[str, Dict[str, str]] = {}

        # Copy all template files (assets, styles, etc.)
        files = self._add_all_template_files(files, template_path)

        component_name = self._get_component_name(template_id)

        # Inject main component LAST
        files[f"src/{component_name}.jsx"] = {
            "content": injected_component
        }

        # Core React files
        files["public/index.html"] = {
            "content": self._generate_index_html()
        }

        files["src/index.js"] = {
            "content": self._generate_index_js()
        }

        files["src/App.js"] = {
            "content": self._generate_app_js(component_name)
        }

        # CSS
        if "src/index.css" not in files:
            files["src/index.css"] = {
                "content": self._generate_tailwind_css()
            }

        # package.json
        files["package.json"] = {
            "content": self._generate_package_json()
        }

        return files

    # =========================================================================
    # FILE GENERATORS
    # =========================================================================

    def _generate_package_json(self) -> str:
        package = {
            "name": "codesandbox-react-app",
            "version": "1.0.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "lucide-react": "latest",
                "clsx": "latest",
                "tailwind-merge": "latest",
                "react-scripts": "5.0.1"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build"
            }
        }
        return json.dumps(package, indent=2)

    def _generate_index_html(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Dashboard</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
"""

    def _generate_index_js(self) -> str:
        return """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""

    def _generate_app_js(self, component_name: str) -> str:
        return f"""import React from 'react';
import {component_name} from './{component_name}';

function App() {{
  return <{component_name} />;
}}

export default App;
"""

    def _generate_tailwind_css(self) -> str:
        return """@tailwind base;
@tailwind components;
@tailwind utilities;

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI',
    Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
"""

    # =========================================================================
    # TEMPLATE HELPERS
    # =========================================================================

    def _get_component_name(self, template_id: str) -> str:
        component_map = {
            "code-1": "Frame22",
            "generic-1": "Frame15",
            "generic-2": "Frame15",
            "shopping-1": "Frame1"
        }
        return component_map.get(template_id, "Frame15")

    def _add_all_template_files(
        self,
        files: Dict[str, Dict[str, str]],
        template_path: Path
    ) -> Dict[str, Dict[str, str]]:

        SKIP_DIRS = {".git", "node_modules", "dist", "__pycache__"}
        SKIP_EXTS = {".py", ".pyc", ".DS_Store"}

        for root, dirs, filenames in os.walk(template_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.suffix in SKIP_EXTS:
                    continue

                rel_path = file_path.relative_to(template_path)
                str_path = str(rel_path).replace("\\", "/")

                # Move assets → public
                if str_path.startswith("assets/"):
                    str_path = "public/" + str_path

                try:
                    content = file_path.read_text(encoding="utf-8")
                    if str_path not in files:
                        files[str_path] = {"content": content}
                except UnicodeDecodeError:
                    # Binary files skipped (CodeSandbox limitation)
                    pass

        # Manifest (harmless for browser sandbox)
        files["public/manifest.json"] = {
            "content": json.dumps(
                {
                    "name": "Disco Dashboard",
                    "short_name": "Disco",
                    "start_url": ".",
                    "display": "standalone",
                    "background_color": "#ffffff",
                    "theme_color": "#000000"
                },
                indent=2
            )
        }

        return files


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    builder = SandboxBuilder()

    test_component = """import React from 'react';

export default function Frame22() {
  return (
    <div style={{ background: '#111', color: '#fff', padding: 32 }}>
      Plain React Sandbox Working ✅
    </div>
  );
}
"""

    files = builder.build_complete_sandbox(
        template_id="code-1",
        injected_component=test_component,
        data={}
    )

    print(f"Built sandbox with {len(files)} files:")
    for path in sorted(files):
        print(" -", path)
