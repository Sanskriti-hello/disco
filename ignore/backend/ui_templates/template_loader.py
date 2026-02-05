"""
Local Template Loader
Loads React components from local files and manages template selection dynamically.
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import re

class TemplateLoader:
    """Manages loading and selection of local React templates dynamically."""
    
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            templates_dir = os.path.dirname(__file__)
        
        self.templates_dir = Path(templates_dir)
        self.templates = self._discover_templates()
    
    def _discover_templates(self) -> Dict[str, Dict]:
        """
        Dynamically scan the ui_templates directory for valid templates.
        A valid template directory must have a 'src/data.json' file.
        """
        print(f"🔍 Scanning for templates in {self.templates_dir}...")
        templates = {}
        
        if not self.templates_dir.exists():
            print(f"⚠️ Templates directory not found: {self.templates_dir}")
            return {}

        for item in self.templates_dir.iterdir():
            if item.is_dir():
                # Check for src/data.json identifying it as a template
                data_path = item / "src" / "data.json"
                if data_path.exists():
                    template_id = item.name
                    
                    # Try to read some metadata from data.json if possible, or infer from name
                    try:
                        data_content = json.loads(data_path.read_text(encoding='utf-8'))
                        friendly_name = data_content.get("header", {}).get("title", template_id)
                    except:
                        friendly_name = template_id

                    templates[template_id] = {
                        "id": template_id,
                        "name": friendly_name,
                        "path": item,
                        "data_path": data_path,
                        "domain": self._infer_domain(template_id)
                    }
                    print(f"  ✅ Found template: {template_id} ({friendly_name})")
        
        return templates

    def _infer_domain(self, template_id: str) -> str:
        """Simple heuristic to guess domain from folder name."""
        lower_id = template_id.lower()
        if "entertainment" in lower_id: return "entertainment"
        if "shopping" in lower_id: return "shopping"
        if "travel" in lower_id: return "travel"
        if "study" in lower_id: return "study"
        if "code" in lower_id: return "code"
        return "generic"

    def select_template(
        self,
        domain: str,
        keywords: List[str],
        user_prompt: str,
        tab_count: int,
        tab_urls: List[str]
    ) -> Dict[str, Any]:
        """
        Select best template based on domain match.
        """
        # 1. Try exact domain match
        candidates = [t for t in self.templates.values() if t["domain"] == domain]
        
        # 2. Fallback to generic or any if no match
        if not candidates:
            print(f"⚠️ No exact match for domain '{domain}', falling back to generic/all.")
            candidates = list(self.templates.values())
            
        if not candidates:
             # Absolute fallback if directory is empty
             return {"template_id": "generic-fallback", "path": ""}

        # Simple selection: pick the first one or randomize
        # For a "strict" flow, picking the first valid one is stable.
        selected = candidates[0]
        
        print(f"🎨 Selected template: {selected['id']}")
        
        return {
            "template_id": selected["id"],
            "template_name": selected["name"],
            # Return path relative to templates dir for consistency with old API if needed, 
            # but mainly we just need the ID to find files later.
            "path": str(selected["path"]) 
        }

    def validate_data_schema(self, template_id: str, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        # Without registry schema definitions, we skip strict validation 
        # or implement basic checks if needed.
        return True, []

# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    loader = TemplateLoader()
    
    # Test template selection
    result = loader.select_template(
        domain="entertainment",
        keywords=["movie", "netflix"],
        user_prompt="show me movies",
        tab_count=1,
        tab_urls=[]
    )
    
    print("\n=== SELECTED TEMPLATE ===")
    print(f"Template: {result['template_id']}")
    print(f"Name: {result['template_name']}")
