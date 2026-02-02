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
            with open(registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid registry JSON: {e}")

    # ============================================================
    # TEMPLATE SELECTION
    # ============================================================

    def select_template(
        self,
        domain: str,
        keywords: List[str],
        user_prompt: str,
        tab_count: int,
        tab_urls: List[str],
    ) -> Dict[str, Any]:
        """
        Select best template using weighted scoring
        """
        templates = self.registry.get("templates", {})
        weights = self.selection_config.get("weights", {})
        min_threshold = self.selection_config.get("min_score_threshold", 0.3)
        default_template = self.selection_config.get(
            "default_template", "generic-1"
        )

        keywords_lower = [kw.lower() for kw in keywords]
        user_prompt_lower = user_prompt.lower()

        scores: Dict[str, float] = {}

        for template_id, template_config in templates.items():
            matching = template_config.get("matching", {})

            # ----------------------------------------------------
            # 1. Keyword match
            # ----------------------------------------------------
            template_keywords = [
                kw.lower() for kw in matching.get("keywords", [])
            ]
            keyword_matches = sum(
                1 for kw in keywords_lower if kw in template_keywords
            )
            keyword_score = min(
                keyword_matches / max(len(template_keywords), 1), 1.0
            )

            # ----------------------------------------------------
            # 2. Domain match
            # ----------------------------------------------------
            template_domains = matching.get("domains", [])
            fallback_domains = matching.get("fallback_domains", [])

            if domain in template_domains:
                domain_score = 1.0
            elif domain in fallback_domains:
                domain_score = 0.5
            else:
                domain_score = 0.0

            # ----------------------------------------------------
            # 3. URL pattern match
            # ----------------------------------------------------
            url_patterns = matching.get("url_patterns", [])
            url_matches = 0

            if url_patterns and tab_urls:
                for url in tab_urls:
                    for pattern in url_patterns:
                        regex_pattern = pattern.replace("*", ".*")
                        if re.search(regex_pattern, url, re.IGNORECASE):
                            url_matches += 1
                            break

                url_score = min(url_matches / len(tab_urls), 1.0)
            else:
                url_score = 0.0

            # ----------------------------------------------------
            # 4. Tab count match
            # ----------------------------------------------------
            min_tab_count = matching.get("min_tab_count", 0)
            tab_count_score = 1.0 if tab_count >= min_tab_count else 0.5

            # ----------------------------------------------------
            # Weighted total
            # ----------------------------------------------------
            total_score = (
                keyword_score * weights.get("keyword_match", 0.4)
                + domain_score * weights.get("domain_match", 0.3)
                + url_score * weights.get("url_pattern_match", 0.2)
                + tab_count_score * weights.get("tab_count_match", 0.1)
            )

            # Priority boost
            priority = matching.get("priority", 5)
            total_score *= priority / 10.0

            scores[template_id] = total_score

        # --------------------------------------------------------
        # Pick best template
        # --------------------------------------------------------
        best_template_id = max(scores, key=scores.get)
        best_score = scores[best_template_id]

        if best_score < min_threshold:
            print(
                f"⚠️ Best score ({best_score:.2f}) below threshold "
                f"({min_threshold}), using default: {default_template}"
            )
            best_template_id = default_template
            best_score = scores.get(default_template, 0.0)

        template_config = templates[best_template_id]

        result = {
            "template_id": best_template_id,
            "template_name": template_config.get(
                "name", best_template_id
            ),
            "component_path": str(
                self.templates_dir
                / best_template_id
                / "index.tsx"
            ),
            "theme": template_config.get("theme", {}),
            "features": template_config.get("features", []),
            "data_schema": template_config.get("data_schema", ""),
            "required_fields": template_config.get("required_fields", []),
            "optional_fields": template_config.get("optional_fields", []),
            "score": best_score,
        }

        print(
            f"🎨 Selected template: {best_template_id} "
            f"(score: {best_score:.2f})"
        )

        return result

    # ============================================================
    # TEMPLATE LOADING
    # ============================================================

    def load_template_component(self, template_id: str) -> str:
        """
        Load React template entry file (index.tsx)
        """
        template_dir = self.templates_dir / template_id
        entry = template_dir / "index.tsx"

        if not entry.exists():
            raise FileNotFoundError(
                f"Template entry not found: {entry}"
            )

        try:
            with open(entry, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise IOError(
                f"Failed to load template {template_id}: {e}"
            )

    def load_template_config(self, template_id: str) -> Dict[str, Any]:
        """
        Load Tailwind config path for template
        """
        config_path = (
            self.templates_dir / template_id / "tailwind.config.js"
        )

        if not config_path.exists():
            return {}

        return {
            "path": str(config_path),
        }

    # ============================================================
    # DATA VALIDATION
    # ============================================================

    def validate_data_schema(
        self, template_id: str, data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that required fields exist in data
        """
        templates = self.registry.get("templates", {})
        if template_id not in templates:
            return False, [f"Unknown template: {template_id}"]

        required_fields = templates[template_id].get(
            "required_fields", []
        )

        missing = [
            field
            for field in required_fields
            if field not in data or data[field] in (None, [], "")
        ]

        return len(missing) == 0, missing

    def get_template_info(
        self, template_id: str
    ) -> Optional[Dict[str, Any]]:
        return self.registry.get("templates", {}).get(template_id)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    loader = TemplateLoader()

    result = loader.select_template(
        domain="study",
        keywords=["flashcards", "quiz", "summary"],
        user_prompt="summarize this and give me flashcards",
        tab_count=3,
        tab_urls=["https://arxiv.org/abs/1706.03762"],
    )

    print("\n=== SELECTED TEMPLATE ===")
    print(result)

    is_valid, missing = loader.validate_data_schema(
        result["template_id"],
        {
            "summary": "Test summary",
            "flashcards": [],
            "quiz": [],
        },
    )

    print("\nData valid:", is_valid)
    print("Missing:", missing)
