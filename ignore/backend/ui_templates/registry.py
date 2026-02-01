# backend/ui_templates/registry_v2.py
"""
Template Registry V2 - Uses Figma URLs instead of hardcoded node IDs
Dynamically discovers and scores templates from Figma files
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class TemplateRegistryV2:
    """
    Updated registry that stores Figma file URLs and dynamically
    discovers templates using the enhanced Figma client
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        if registry_path is None:
            registry_path = os.path.join(
                os.path.dirname(__file__),
                "templates_v2.json"
            )
        
        self.registry_path = registry_path
        self.templates = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Dict[str, Any]]:
        """Load registry from JSON"""
        
        if not os.path.exists(self.registry_path):
            return self._get_default_registry()
        
        try:
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading registry: {e}")
            return self._get_default_registry()
    
    def _get_default_registry(self) -> Dict[str, Dict[str, Any]]:
        """
        Default registry with Figma FILE URLs (not node IDs)
        Each domain has ONE Figma file containing multiple templates
        """
        return {
            "study": {
                "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/study-domain",
                "templates": {
                    "PaperList": {
                        "description": "Grid view of research papers",
                        "best_for": ["research", "papers", "articles", "arxiv"],
                        "keywords": ["paper", "research", "academic", "publication"],
                        "figma_node_id": "1:2"
                    },
                    "NoteTaker": {
                        "description": "Split view with notes and content",
                        "best_for": ["documentation", "tutorials", "learning", "notes"],
                        "keywords": ["notes", "editor", "markdown", "document"],
                        "figma_node_id": "1:3"
                    },
                    "QuizCard": {
                        "description": "Flashcard-style quiz interface",
                        "best_for": ["studying", "memorization", "practice", "exam"],
                        "keywords": ["quiz", "flashcard", "test", "practice"],
                        "figma_node_id": "1:4"
                    }
                }
            },
            
            "shopping": {
                "figma_url": "https://www.figma.com/design/Wlf3wJeUUoXN8DBY4QtBMs/shopping?node-id=0-1",
                "templates": {
                    "ProductGrid": {
                        "description": "Grid of products with images",
                        "best_for": ["browsing", "comparing", "multiple items"],
                        "keywords": ["product", "grid", "shop", "catalog"],
                        "figma_file_key": "Wlf3wJeUUoXN8DBY4QtBMs",
                        "figma_node_id": "0:1"
                    },
                    "PriceComparison": {
                        "description": "Price comparison table",
                        "best_for": ["comparing prices", "deals", "specifications"],
                        "keywords": ["compare", "price", "table", "specs"],
                        "figma_file_key": "Wlf3wJeUUoXN8DBY4QtBMs",
                        "figma_node_id": "0:1"
                    }
                }
            },
            
            "travel": {
                "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/travel-domain",
                "templates": {
                    "FlightTracker": {
                        "description": "Flight comparison interface",
                        "best_for": ["flights", "booking", "airports"],
                        "keywords": ["flight", "airline", "airport", "booking"],
                        "figma_node_id": "3:1"
                    },
                    "HotelFinder": {
                        "description": "Hotel search with ratings",
                        "best_for": ["accommodation", "hotels", "stays"],
                        "keywords": ["hotel", "accommodation", "booking", "room"],
                        "figma_node_id": "3:2"
                    }
                }
            },
            
            "code": {
                "figma_url": "https://www.figma.com/design/JX502dwBhbh7pMFV3nuGpi/code-1?node-id=0-1",
                "templates": {
                    "CodeViewer": {
                        "description": "Syntax-highlighted code display",
                        "best_for": ["code snippets", "examples", "documentation"],
                        "keywords": ["code", "snippet", "syntax", "programming"],
                        "figma_file_key": "JX502dwBhbh7pMFV3nuGpi",
                        "figma_node_id": "0:1"
                    },
                    "RepoExplorer": {
                        "description": "GitHub repository overview",
                        "best_for": ["repositories", "github", "projects"],
                        "keywords": ["repo", "github", "git", "project"],
                        "figma_file_key": "JX502dwBhbh7pMFV3nuGpi",
                        "figma_node_id": "0:1"
                    }
                }
            },
            
            "entertainment": {
                "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/entertainment-domain",
                "templates": {
                    "EventCard": {
                        "description": "Event listings with dates",
                        "best_for": ["events", "concerts", "shows"],
                        "keywords": ["event", "concert", "show", "venue"],
                        "figma_node_id": "5:1"
                    },
                    "MediaPlayer": {
                        "description": "Video/music player",
                        "best_for": ["videos", "music", "streaming"],
                        "keywords": ["player", "video", "music", "media"],
                        "figma_node_id": "5:2"
                    }
                }
            },
            
            "generic": {
                "figma_url": "https://www.figma.com/design/hTDboSi9SgURHs3KrewNNB/generic-2?node-id=1-786",
                "templates": {
                    "SummaryView": {
                        "description": "General content summary",
                        "best_for": ["summary", "overview", "general"],
                        "keywords": ["summary", "overview", "content", "text"],
                        "figma_file_key": "hTDboSi9SgURHs3KrewNNB",
                        "figma_node_id": "1:786"
                    },
                    "LinkGrid": {
                        "description": "Grid of links with previews",
                        "best_for": ["links", "bookmarks", "collection"],
                        "keywords": ["link", "bookmark", "grid", "collection"],
                        "figma_file_key": "PxLCYxuApLFWLVOiCeaCd6",
                        "figma_node_id": "0:1"
                    },
                    "NewsDashboard": {
                        "description": "List of news articles",
                        "best_for": ["news", "articles", "headlines"],
                        "keywords": ["news", "article", "headline", "breaking"],
                        "figma_file_key": "hTDboSi9SgURHs3KrewNNB",
                        "figma_node_id": "1:850"
                    },
                    "WeatherDashboard": {
                        "description": "Current weather and forecast",
                        "best_for": ["weather", "forecast", "temperature"],
                        "keywords": ["weather", "forecast", "temperature", "climate"],
                        "figma_file_key": "hTDboSi9SgURHs3KrewNNB",
                        "figma_node_id": "1:900"
                    }
                }
            }
        }
    
    def find_best_template(
        self,
        domain: str,
        keywords: List[str],
        user_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        Find best template for domain using keyword scoring
        
        Returns:
            {
                "template_name": "PaperList",
                "figma_url": "https://...",
                "template_hints": ["research", "papers"],
                "score": 12.0
            }
        """
        
        domain_data = self.templates.get(domain, self.templates.get("generic"))
        templates = domain_data.get("templates", {})
        
        if not templates:
            return {
                "template_name": "SummaryView",
                "figma_url": self.templates["generic"]["figma_url"],
                "template_hints": [],
                "score": 0
            }
        
        # Score each template
        scores = {}
        search_text = f"{user_prompt} {' '.join(keywords)}".lower()
        
        for template_name, template_info in templates.items():
            score = 0
            
            # Match against best_for
            for keyword in template_info.get("best_for", []):
                if keyword.lower() in search_text:
                    score += 3
            
            # Match against template keywords
            for keyword in template_info.get("keywords", []):
                if keyword.lower() in search_text:
                    score += 2
            
            # Match against description
            if any(word in template_info.get("description", "").lower() for word in keywords):
                score += 1
            
            scores[template_name] = score
        
        # Get best match
        best_template = max(scores.items(), key=lambda x: x[1])[0]
        template_info = templates[best_template]
        
        return {
            "template_name": best_template,
            "figma_url": domain_data["figma_url"],
            "template_hints": template_info.get("best_for", []),
            "keywords": template_info.get("keywords", []),
            "score": scores[best_template]
        }
    
    def get_template_meta(self, domain: str, template_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific template"""
        domain_data = self.templates.get(domain)
        if not domain_data:
            return None
        
        template_info = domain_data.get("templates", {}).get(template_name)
        if not template_info:
            return None
            
        return {
            "template_name": template_name,
            "figma_url": domain_data.get("figma_url"),
            "description": template_info.get("description", ""),
            "best_for": template_info.get("best_for", []),
            "keywords": template_info.get("keywords", []),
            "figma_node_id": template_info.get("figma_node_id"),
            "figma_file_key": template_info.get("figma_file_key")
        }
    
    def get_templates_for_domain(self, domain: str) -> Dict[str, Any]:
        """Get all templates for a specific domain"""
        return self.templates.get(domain, {}).get("templates", {})

    def save_registry(self):
        """Save registry to file"""
        try:
            with open(self.registry_path, 'w') as f:
                json.dump(self.templates, f, indent=2)
            print(f"✓ Registry saved to {self.registry_path}")
        except Exception as e:
            print(f"Failed to save registry: {e}")


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    registry = TemplateRegistryV2()
    
    # Test finding best template
    result = registry.find_best_template(
        domain="study",
        keywords=["research", "papers", "machine", "learning", "arxiv"],
        user_prompt="Create a dashboard for my research papers"
    )
    
    print("\n=== BEST TEMPLATE ===")
    print(f"Template: {result['template_name']}")
    print(f"Figma URL: {result['figma_url']}")
    print(f"Hints: {result['template_hints']}")
    print(f"Score: {result['score']}")