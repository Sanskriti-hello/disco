"""
Local Template Loader
Loads React components from local files and manages template selection
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import re


class TemplateLoader:
    """Manages loading and selection of local React templates"""
    
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            templates_dir = os.path.dirname(__file__)
        
        self.templates_dir = Path(templates_dir)
        self.registry = self._load_registry()
        self.selection_config = self.registry.get("selection_algorithm", {})
    
    def _load_registry(self) -> Dict:
        """Load template registry from JSON"""
        registry_path = self.templates_dir / "registry.json"
        
        if not registry_path.exists():
            raise FileNotFoundError(f"Registry not found at {registry_path}")
        
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid registry JSON: {e}")
    
    def select_template(
        self,
        domain: str,
        keywords: List[str],
        user_prompt: str,
        tab_count: int,
        tab_urls: List[str]
    ) -> Dict[str, Any]:
        """
        Intelligently select best template based on context using weighted scoring
        
        Args:
            domain: Selected domain (study, shopping, code, generic, etc.)
            keywords: Extracted keywords from user prompt and tabs
            user_prompt: Original user request
            tab_count: Number of open tabs
            tab_urls: List of tab URLs
        
        Returns:
            {
                "template_id": "code-1",
                "template_name": "Terminal Code View",
                "component_path": "/absolute/path/to/Frame22.jsx",
                "app_path": "/absolute/path/to/App.jsx",
                "theme": {...},
                "features": [...],
                "data_schema": "CodeTemplateData",
                "required_fields": [...],
                "score": 0.85
            }
        """
        templates = self.registry.get("templates", {})
        weights = self.selection_config.get("weights", {})
        min_threshold = self.selection_config.get("min_score_threshold", 0.3)
        default_template = self.selection_config.get("default_template", "generic-1")
        
        # Normalize inputs
        keywords_lower = [kw.lower() for kw in keywords]
        user_prompt_lower = user_prompt.lower()
        
        scores = {}
        
        for template_id, template_config in templates.items():
            matching = template_config.get("matching", {})
            
            # 1. Keyword Match Score (weight: 0.4)
            template_keywords = [kw.lower() for kw in matching.get("keywords", [])]
            keyword_matches = sum(1 for kw in keywords_lower if kw in template_keywords)
            keyword_score = min(keyword_matches / max(len(template_keywords), 1), 1.0)
            
            # 2. Domain Match Score (weight: 0.3)
            template_domains = matching.get("domains", [])
            fallback_domains = matching.get("fallback_domains", [])
            
            if domain in template_domains:
                domain_score = 1.0
            elif domain in fallback_domains:
                domain_score = 0.5
            else:
                domain_score = 0.0
            
            # 3. URL Pattern Match Score (weight: 0.2)
            url_patterns = matching.get("url_patterns", [])
            url_matches = 0
            if url_patterns:
                for url in tab_urls:
                    for pattern in url_patterns:
                        # Simple wildcard matching (* becomes .*)
                        regex_pattern = pattern.replace("*", ".*")
                        if re.search(regex_pattern, url, re.IGNORECASE):
                            url_matches += 1
                            break
                url_score = min(url_matches / len(tab_urls), 1.0) if tab_urls else 0.0
            else:
                url_score = 0.0
            
            # 4. Tab Count Match Score (weight: 0.1)
            min_tab_count = matching.get("min_tab_count", 0)
            if tab_count >= min_tab_count:
                tab_count_score = 1.0
            else:
                tab_count_score = 0.5  # Partial credit
            
            # Calculate weighted total
            total_score = (
                keyword_score * weights.get("keyword_match", 0.4) +
                domain_score * weights.get("domain_match", 0.3) +
                url_score * weights.get("url_pattern_match", 0.2) +
                tab_count_score * weights.get("tab_count_match", 0.1)
            )
            
            # Apply priority boost
            priority = matching.get("priority", 5)
            total_score *= (priority / 10.0)  # Normalize priority
            
            scores[template_id] = total_score
        
        # Select template with highest score
        best_template_id = max(scores, key=scores.get)
        best_score = scores[best_template_id]
        
        # Fallback to default if score too low
        if best_score < min_threshold:
            print(f"⚠️ Best score ({best_score:.2f}) below threshold ({min_threshold}), using default template: {default_template}")
            best_template_id = default_template
            best_score = scores.get(default_template, 0.0)
        
        # Build result
        template_config = templates[best_template_id]
        result = {
            "template_id": best_template_id,
            "template_name": template_config.get("name", best_template_id),
            "component_path": str(self.templates_dir / template_config["component_path"]),
            "app_path": str(self.templates_dir / template_config.get("app_path", "")),
            "config_path": str(self.templates_dir / template_config.get("config_path", "")),
            "theme": template_config.get("theme", {}),
            "features": template_config.get("features", []),
            "data_schema": template_config.get("data_schema", ""),
            "required_fields": template_config.get("required_fields", []),
            "optional_fields": template_config.get("optional_fields", []),
            "score": best_score
        }
        
        print(f"🎨 Selected template: {best_template_id} (score: {best_score:.2f})")
        
        return result
    
    def load_template_component(self, template_id: str) -> str:
        """
        Load React component source code from file
        
        Args:
            template_id: ID of template to load (e.g., "code-1")
        
        Returns: Full JSX source code as string
        """
        templates = self.registry.get("templates", {})
        if template_id not in templates:
            raise ValueError(f"Template {template_id} not found in registry")
        
        template_config = templates[template_id]
        component_path = self.templates_dir / template_config["component_path"]
        
        if not component_path.exists():
            raise FileNotFoundError(f"Component file not found: {component_path}")
        
        try:
            with open(component_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to load component {template_id}: {e}")
    
    def load_template_config(self, template_id: str) -> Dict:
        """
        Load Tailwind config for template
        
        Args:
            template_id: ID of template
        
        Returns: Parsed config object (or empty dict if not found)
        """
        templates = self.registry.get("templates", {})
        if template_id not in templates:
            return {}
        
        template_config = templates[template_id]
        config_path = self.templates_dir / template_config.get("config_path", "")
        
        if not config_path.exists():
            print(f"⚠️ Config file not found: {config_path}")
            return {}
        
        try:
            # Tailwind config is JS, not JSON - return path for now
            # In practice, we mainly need the theme info which is in registry.json
            return {
                "path": str(config_path),
                "theme": template_config.get("theme", {})
            }
        except Exception as e:
            print(f"⚠️ Failed to load config: {e}")
            return {}
    
    def validate_data_schema(
        self,
        template_id: str,
        data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that provided data matches template requirements
        
        Args:
            template_id: ID of template
            data: Data dictionary to validate
        
        Returns: (is_valid, missing_fields)
        """
        templates = self.registry.get("templates", {})
        if template_id not in templates:
            return False, [f"Unknown template: {template_id}"]
        
        template_config = templates[template_id]
        required_fields = template_config.get("required_fields", [])
        
        missing_fields = []
        for field in required_fields:
            if field not in data or not data[field]:
                missing_fields.append(field)
        
        is_valid = len(missing_fields) == 0
        return is_valid, missing_fields
    
    def get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get full template configuration"""
        return self.registry.get("templates", {}).get(template_id)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    loader = TemplateLoader()
    
    # Test template selection
    result = loader.select_template(
        domain="code",
        keywords=["github", "debug", "react", "error"],
        user_prompt="help me debug this React hook",
        tab_count=5,
        tab_urls=["https://github.com/user/repo", "https://stackoverflow.com/questions/123"]
    )
    
    print("\n=== SELECTED TEMPLATE ===")
    print(f"Template: {result['template_id']}")
    print(f"Name: {result['template_name']}")
    print(f"Score: {result['score']:.2f}")
    print(f"Features: {result['features']}")
    
    # Test data validation
    test_data = {"code_snippets": [{"language": "python", "code": "print('hello')"}]}
    is_valid, missing = loader.validate_data_schema(result['template_id'], test_data)
    print(f"\nData valid: {is_valid}, Missing: {missing}")
