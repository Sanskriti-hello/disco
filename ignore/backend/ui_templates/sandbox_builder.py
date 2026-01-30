"""
CodeSandbox Builder - Complete Template Folder Integration
Creates full CodeSandbox with all template files, dependencies, and configurations
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import shutil


class SandboxBuilder:
    """Builds complete CodeSandbox file structures from local templates"""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        # Templates are directly in ui_templates/, NOT in a components subfolder
        self.templates_dir = templates_dir or Path(__file__).parent
    
    def build_complete_sandbox(
        self,
        template_id: str,
        injected_component: str,
        data: Dict[str, Any]
    ) -> Dict[str, Dict[str, str]]:
        """
        Build complete file structure for CodeSandbox
        
        Args:
            template_id: Template ID (e.g., "code-1")
            injected_component: The main component with data injected
            data: Template data for reference
        
        Returns: Dictionary of {filepath: {"content": file_content}}
        """
        template_path = self.templates_dir / template_id
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template directory not found: {template_path}")
        
        files = {}
        
        # 1. Load package.json with all dependencies
        files["package.json"] = {
            "content": self._load_package_json(template_path)
        }
        
        # 2. Load tailwind config
        tailwind_path = template_path / "tailwind.config.js"
        if tailwind_path.exists():
            files["tailwind.config.js"] = {
                "content": tailwind_path.read_text(encoding='utf-8')
            }
        
        # 3. Load postcss config
        postcss_path = template_path / "postcss.config.js"
        if postcss_path.exists():
            files["postcss.config.js"] = {
                "content": postcss_path.read_text(encoding='utf-8')
            }
        
        # 4. Load vite config
        vite_config_path = template_path / "vite.config.js"
        if vite_config_path.exists():
            files["vite.config.js"] = {
                "content": vite_config_path.read_text(encoding='utf-8')
            }
        
        # 5. Create index.html
        files["index.html"] = {
            "content": self._generate_index_html(template_id)
        }
        
        # 6. Add the main injected component
        component_name = self._get_component_name(template_id)
        files[f"src/{component_name}.jsx"] = {
            "content": injected_component
        }
        
        # 7. Create simplified App.jsx (no router, just render main component)
        files["src/App.jsx"] = {
            "content": self._generate_simple_app(component_name)
        }
        
        # 8. Create index.jsx entry point
        files["src/index.jsx"] = {
            "content": self._generate_index_jsx()
        }
        
        # 9. Add styles with Tailwind directives
        files["src/index.css"] = {
            "content": self._generate_tailwind_css()
        }
        
        # 10. Copy any additional pages/components from template
        src_path = template_path / "src" / "pages"
        if src_path.exists():
            files = self._add_additional_components(files, src_path, template_id)
        
        return files
    
    def _load_package_json(self, template_path: Path) -> str:
        """Load and enhance package.json with all necessary dependencies"""
        package_path = template_path / "package.json"
        
        if package_path.exists():
            with open(package_path, 'r', encoding='utf-8') as f:
                package = json.load(f)
        else:
            package = {}
        
        # Ensure essential dependencies
        dependencies = package.get("dependencies", {})
        dependencies.update({
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "lucide-react": "latest",
            "clsx": "latest",
            "tailwind-merge": "latest"
        })
        
        # Add dev dependencies
        dev_dependencies = package.get("devDependencies", {})
        dev_dependencies.update({
            "tailwindcss": "^3.4.0",
            "postcss": "^8.4.32",
            "autoprefixer": "^10.4.16",
            "@vitejs/plugin-react": "^4.2.0",
            "vite": "^5.0.0"
        })
        
        package["dependencies"] = dependencies
        package["devDependencies"] = dev_dependencies
        package["scripts"] = {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
        }
        
        return json.dumps(package, indent=2)
    
    def _get_component_name(self, template_id: str) -> str:
        """Get main component filename for template"""
        component_map = {
            "code-1": "Frame22",
            "generic-1": "Frame15",
            "generic-2": "Frame15",
            "shopping-1": "Frame1"
        }
        return component_map.get(template_id, "Frame15")
    
    def _generate_index_html(self, template_id: str) -> str:
        """Generate index.html with proper Tailwind setup"""
        return '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/index.jsx"></script>
  </body>
</html>'''
    
    def _generate_simple_app(self, component_name: str) -> str:
        """Generate simplified App.jsx without router"""
        return f'''import React from 'react';
import {component_name} from './{component_name}.jsx';

const App = () => {{
  return <{component_name} />;
}};

export default App;'''
    
    def _generate_index_jsx(self) -> str:
        """Generate index.jsx entry point"""
        return '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);'''
    
    def _generate_tailwind_css(self) -> str:
        """Generate CSS with Tailwind directives"""
        return '''@tailwind base;
@tailwind components;
@tailwind utilities;

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}'''
    
    def _add_additional_components(
        self,
        files: Dict,
        src_path: Path,
        template_id: str
    ) -> Dict:
        """Add any additional component files from template"""
        main_component = self._get_component_name(template_id)
        
        for component_file in src_path.glob("*.jsx"):
            # Skip the main component (already injected)
            if component_file.stem == main_component:
                continue
            
            # Add other components as-is
            rel_path = f"src/pages/{component_file.name}"
            files[rel_path] = {
                "content": component_file.read_text(encoding='utf-8')
            }
        
        return files


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    builder = SandboxBuilder()
    
    # Test building complete sandbox
    test_component = """import React from 'react';

const Frame22 = () => {
  return <div className="bg-gray-900 text-white p-8">Test Component</div>;
};

export default Frame22;"""
    
    files = builder.build_complete_sandbox(
        template_id="code-1",
        injected_component=test_component,
        data={}
    )
    
    print(f"Built sandbox with {len(files)} files:")
    for filepath in sorted(files.keys()):
        size = len(files[filepath]["content"])
        print(f"  - {filepath} ({size} bytes)")
