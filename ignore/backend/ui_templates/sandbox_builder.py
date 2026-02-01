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
        
        # 10. RECURSIVELY copy ALL files from template directory (overwriting above if needed)
        # This ensures assets, images, styles, and extra components are all included
        try:
            files = self._add_all_template_files(files, template_path, template_id)
        except Exception as e:
            print(f"Error recursively adding files: {e}")
        
        # 10.5 If index.css was NOT in template, add the default one now
        if "src/index.css" not in files:
            files["src/index.css"] = {
                "content": self._generate_tailwind_css()
            }
        
        # 11. Ensure main component is injected with the processed code
        # We re-add this LAST to ensure the injected version takes precedence over the file on disk
        component_name = self._get_component_name(template_id)
        
        # FIX ASSET PATHS: Make them absolute from the root
        injected_component = injected_component.replace('src="assets/', 'src="/assets/')
        injected_component = injected_component.replace('url(assets/', 'url(/assets/')
        
        files[f"src/pages/{component_name}.jsx"] = {
            "content": injected_component
        }
        
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
            "tailwind-merge": "latest",
            "react-router-dom": "^6.22.0"
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
    <link rel="manifest" href="/manifest.json" />
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


    def _add_all_template_files(self, files: Dict, template_path: Path, template_id: str) -> Dict:
        """Recursively add all files from template directory"""
        
        # Skip these directories/files
        SKIP_DIRS = {'.git', 'node_modules', 'dist', '__pycache__'}
        SKIP_EXTS = {'.py', '.pyc', '.DS_Store'}
        
        for root, dirs, filenames in os.walk(template_path):
            # Modify dirs in-place to skip specific directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            
            for filename in filenames:
                file_path = Path(root) / filename
                rel_path = file_path.relative_to(template_path)
                str_path = str(rel_path).replace("\\", "/") # Normalize for web
                
                # MOVE ASSETS TO PUBLIC
                # If the file is in 'assets/', move it to 'public/assets/'
                if str_path.startswith("assets/"):
                    str_path = "public/" + str_path
                
                if file_path.suffix in SKIP_EXTS:
                    continue
                
                # Check for binary files
                try:
                    content = file_path.read_text(encoding='utf-8')
                    if str_path not in files:
                         files[str_path] = {"content": content}
                         
                except UnicodeDecodeError:
                     # Binary file handling
                     print(f"⚠️ Skipping binary file: {str_path} (CodeSandbox JSON API limitation)")
                     pass
        
        # Add Manifest (CodeSandbox specific fix)
        files["public/manifest.json"] = {
            "content": json.dumps({
                "name": "Disco Dashboard",
                "short_name": "Disco",
                "start_url": ".",
                "scope": "/",
                "display": "standalone",
                "background_color": "#ffffff",
                "theme_color": "#000000",
                "icons": []
            }, indent=2)
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
