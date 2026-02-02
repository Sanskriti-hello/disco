"""
CodeSandbox Builder - CRA + Tailwind (NO VITE)
Creates full CodeSandbox payload compatible with react-scripts
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class SandboxBuilder:
    """Builds CRA + Tailwind CodeSandbox file structures"""

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

        # 1️⃣ Add ALL template files (assets, etc.)
        files = self._add_all_template_files(files, template_path)

        # 2️⃣ Core CRA files
        files["package.json"] = {"content": self._generate_package_json()}
        files["tailwind.config.js"] = {"content": self._generate_tailwind_config()}
        files["postcss.config.js"] = {"content": self._generate_postcss_config()}
        files["public/index.html"] = {"content": self._generate_index_html()}
        files["src/index.js"] = {"content": self._generate_index_js()}
        files["src/App.js"] = {
            "content": self._generate_app_js(self._get_component_name(template_id))
        }

        # 3️⃣ Tailwind CSS
        files["src/index.css"] = {"content": self._generate_tailwind_css()}

        # 4️⃣ Inject main component LAST (takes precedence)
        component_name = self._get_component_name(template_id)

        injected_component = injected_component.replace('src="assets/', 'src="/assets/')
        injected_component = injected_component.replace('url(assets/', 'url(/assets/')

        files[f"src/pages/{component_name}.jsx"] = {
            "content": injected_component
        }

        return files

    # =========================================================================
    # GENERATORS
    # =========================================================================

    def _generate_package_json(self) -> str:
        return json.dumps(
            {
                "name": "react-tailwind",
                "private": True,
                "version": "1.0.0",
                "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                    "react-scripts": "5.0.1"
                },
                "devDependencies": {
                    "tailwindcss": "^3.4.0",
                    "postcss": "^8.4.32",
                    "autoprefixer": "^10.4.16"
                },
                "scripts": {
                    "start": "react-scripts start",
                    "build": "react-scripts build"
                }
            },
            indent=2
        )

    def _generate_tailwind_config(self) -> str:
        return """module.exports = {
  content: [
    "./src/**/*.{js,jsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
"""

    def _generate_postcss_config(self) -> str:
        return """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
"""

    def _generate_index_html(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>React Tailwind App</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
"""

    def _generate_index_js(self) -> str:
        return """import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""

    def _generate_app_js(self, component_name: str) -> str:
        return f"""import React from "react";
import {component_name} from "./pages/{component_name}";

export default function App() {{
  return (
    <div className="relative min-h-screen">
      <{component_name} />
    </div>
  );
}}
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
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI",
    Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue",
    sans-serif;
}
"""

    # =========================================================================
    # UTILITIES
    # =========================================================================

    def _get_component_name(self, template_id: str) -> str:
        return {
            "code-1": "Frame22",
            "generic-1": "Frame15",
            "generic-2": "Frame15",
            "shopping-1": "Frame1",
        }.get(template_id, "Frame15")

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
                rel_path = file_path.relative_to(template_path)
                str_path = str(rel_path).replace("\\", "/")

                if file_path.suffix in SKIP_EXTS:
                    continue

                # Move assets → public/assets
                if str_path.startswith("assets/"):
                    str_path = "public/" + str_path

                try:
                    content = file_path.read_text(encoding="utf-8")
                    if str_path not in files:
                        files[str_path] = {"content": content}
                except UnicodeDecodeError:
                    # Binary files skipped (CodeSandbox JSON limitation)
                    pass

        # Manifest (safe default)
        files["public/manifest.json"] = {
            "content": json.dumps(
                {
                    "name": "App",
                    "short_name": "App",
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

    test_component = """import React from "react";

const Frame22 = () => {
  return (
    <div className="bg-gray-900 text-white p-8 text-xl">
      Tailwind is working 🎉
    </div>
  );
};

export default Frame22;
"""

    files = builder.build_complete_sandbox(
        template_id="code-1",
        injected_component=test_component,
        data={}
    )

    print(f"Built sandbox with {len(files)} files:")
    for k in sorted(files.keys()):
        print(" -", k)
