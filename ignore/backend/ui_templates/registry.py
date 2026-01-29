"""
Template Registry - Maps domains to available UI templates
Stores Figma node IDs and metadata for each template
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

# Fix import to point to backend.figma
try:
    from backend.figma import parse_figma_url
except ImportError:
    # Fallback if running directly or different structure
    try:
        from figma import parse_figma_url 
    except ImportError:
        pass


class TemplateRegistry:
    # ... (init and load methods unchanged) ...

    # ... (get_default_registry method unchanged) ...
    
    def get_templates_for_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Get all templates for a specific domain"""
        templates = self.templates.get(domain, self.templates.get("generic", []))
        
        # Ensure node_id is populated if missing but url exists
        for t in templates:
            if "figma_node_id" not in t and "figma_url" in t:
                try:
                    parsed = parse_figma_url(t["figma_url"])
                    t["figma_node_id"] = parsed["node_id"]
                    t["figma_file_key"] = parsed["file_key"]
                except Exception as e:
                    print(f"Warning: Could not parse URL for {t['name']}: {e}")
        
        return templates
    
    def get_template_meta(self, domain: str, template_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific template"""
        templates = self.get_templates_for_domain(domain)
        
        for template in templates:
            if template["name"] == template_name:
                return template
        
        return None
    
    def find_best_template(
        self,
        domain: str,
        keywords: List[str],
        user_prompt: str = ""
    ) -> str:
        # ... (find_best_template logic unchanged) ...
        templates = self.get_templates_for_domain(domain)
        
        if not templates:
            return "SummaryView"  # Fallback
        
        # Score each template
        scores = {}
        search_text = f"{user_prompt} {' '.join(keywords)}".lower()
        
        for template in templates:
            score = 0
            
            # Match against best_for keywords
            for keyword in template.get("best_for", []):
                if keyword in search_text:
                    score += 3
            
            # Match against description
            if any(word in template.get("description", "").lower() for word in keywords):
                score += 1
            
            scores[template["name"]] = score
        
        # Return highest scoring template
        if scores:
            best_template = max(scores.items(), key=lambda x: x[1])[0]
            return best_template
        
        # Fallback to first template
        return templates[0]["name"]
    
    def save_registry(self):
        """Save current registry to JSON file"""
        try:
            with open(self.registry_path, 'w') as f:
                json.dump(self.templates, f, indent=2)
            print(f"Registry saved to {self.registry_path}")
        except Exception as e:
            print(f"Failed to save registry: {e}")
    
    def add_template(
        self,
        domain: str,
        name: str,
        figma_url: str,
        description: str,
        best_for: List[str],
        widgets: List[str]
    ):
        """Add a new template to the registry"""
        
        if domain not in self.templates:
            self.templates[domain] = []
        
        try:
            parsed = parse_figma_url(figma_url)
            node_id = parsed["node_id"]
            file_key = parsed["file_key"]
        except Exception:
            node_id = None
            file_key = None
            print("Warning: Could not parse Figma URL")
            
        template = {
            "name": name,
            "figma_url": figma_url,
            "figma_node_id": node_id,
            "figma_file_key": file_key,
            "description": description,
            "best_for": best_for,
            "widgets": widgets
        }
        
        self.templates[domain].append(template)
        self.save_registry()
            "study": [
                {
                    "name": "PaperList",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/study-domain?node-id=45-678",
                    "description": "Grid view of research papers with thumbnails",
                    "best_for": ["research", "papers", "articles"],
                    "widgets": ["paper_card", "citation_tool", "notes_panel"]
                },
                {
                    "name": "NoteTaker",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/study-domain?node-id=45-679",
                    "description": "Split view with notes and content",
                    "best_for": ["documentation", "tutorials", "learning"],
                    "widgets": ["markdown_editor", "outline_view"]
                },
                {
                    "name": "QuizCard",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/study-domain?node-id=45-680",
                    "description": "Flashcard-style quiz interface",
                    "best_for": ["studying", "memorization", "practice"],
                    "widgets": ["flashcard", "progress_tracker"]
                },
                {
                    "name": "ResearchSummary",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/study-domain?node-id=45-681",
                    "description": "Consolidated summary with key insights",
                    "best_for": ["review", "synthesis", "overview"],
                    "widgets": ["summary_card", "topic_graph"]
                },
                {
                    "name": "CourseTracker",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/study-domain?node-id=45-682",
                    "description": "Course progress and module tracking",
                    "best_for": ["courses", "mooc", "curriculum"],
                    "widgets": ["progress_bar", "module_list", "schedule"]
                }
            ],
            
            "shopping": [
                {
                    "name": "ProductGrid",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/shopping-domain?node-id=46-100",
                    "description": "Grid layout showing products with images",
                    "best_for": ["browsing", "comparing", "multiple items"],
                    "widgets": ["product_card", "filter_panel", "sort_dropdown"]
                },
                {
                    "name": "PriceComparison",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/shopping-domain?node-id=46-101",
                    "description": "Side-by-side price comparison table",
                    "best_for": ["comparing prices", "deals", "specifications"],
                    "widgets": ["comparison_table", "price_graph"]
                },
                {
                    "name": "WishlistView",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/shopping-domain?node-id=46-102",
                    "description": "Saved items with price tracking",
                    "best_for": ["wishlist", "tracking", "favorites"],
                    "widgets": ["wishlist_card", "price_alert", "stock_status"]
                },
                {
                    "name": "DealTracker",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/shopping-domain?node-id=46-103",
                    "description": "Highlights deals and discounts",
                    "best_for": ["deals", "sales", "coupons"],
                    "widgets": ["deal_card", "countdown_timer", "savings_badge"]
                },
                {
                    "name": "CartSummary",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/shopping-domain?node-id=46-104",
                    "description": "Shopping cart with total calculation",
                    "best_for": ["checkout", "cart", "purchase"],
                    "widgets": ["cart_item", "total_display", "coupon_input"]
                }
            ],
            
            "travel": [
                {
                    "name": "TravelCard",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/travel-domain?node-id=47-200",
                    "description": "Destination cards with photos and info",
                    "best_for": ["destinations", "exploring", "inspiration"],
                    "widgets": ["destination_card", "image_gallery", "info_panel"]
                },
                {
                    "name": "ItineraryView",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/travel-domain?node-id=47-201",
                    "description": "Timeline-based trip itinerary",
                    "best_for": ["planning", "itinerary", "schedule"],
                    "widgets": ["timeline", "activity_card", "map_preview"]
                },
                {
                    "name": "MapWidget",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/travel-domain?node-id=47-202",
                    "description": "Interactive map with markers",
                    "best_for": ["navigation", "locations", "geography"],
                    "widgets": ["map_view", "location_marker", "route_display"]
                },
                {
                    "name": "FlightTracker",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/travel-domain?node-id=47-203",
                    "description": "Flight comparison and booking info",
                    "best_for": ["flights", "booking", "airports"],
                    "widgets": ["flight_card", "price_calendar", "airline_logo"]
                },
                {
                    "name": "HotelFinder",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/travel-domain?node-id=47-204",
                    "description": "Hotel search with ratings and amenities",
                    "best_for": ["accommodation", "hotels", "stays"],
                    "widgets": ["hotel_card", "rating_stars", "amenities_list"]
                }
            ],
            
            "code": [
                {
                    "name": "CodeViewer",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/code-domain?node-id=48-300",
                    "description": "Syntax-highlighted code display",
                    "best_for": ["code snippets", "examples", "documentation"],
                    "widgets": ["code_block", "copy_button", "language_selector"]
                },
                {
                    "name": "RepoExplorer",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/code-domain?node-id=48-301",
                    "description": "GitHub repository overview",
                    "best_for": ["repositories", "github", "projects"],
                    "widgets": ["repo_card", "file_tree", "commit_history"]
                },
                {
                    "name": "DocReader",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/code-domain?node-id=48-302",
                    "description": "Documentation browser with navigation",
                    "best_for": ["docs", "api reference", "guides"],
                    "widgets": ["doc_nav", "content_viewer", "search_bar"]
                },
                {
                    "name": "IssueTracker",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/code-domain?node-id=48-303",
                    "description": "List of issues/bugs with status",
                    "best_for": ["issues", "bugs", "tasks"],
                    "widgets": ["issue_card", "status_badge", "priority_label"]
                },
                {
                    "name": "APIPlayground",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/code-domain?node-id=48-304",
                    "description": "Interactive API testing interface",
                    "best_for": ["api", "testing", "endpoints"],
                    "widgets": ["request_builder", "response_viewer", "auth_panel"]
                }
            ],
            
            "entertainment": [
                {
                    "name": "EventCard",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/entertainment-domain?node-id=49-400",
                    "description": "Event listings with dates and venues",
                    "best_for": ["events", "concerts", "shows"],
                    "widgets": ["event_card", "date_display", "venue_info"]
                },
                {
                    "name": "MediaPlayer",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/entertainment-domain?node-id=49-401",
                    "description": "Video/music player interface",
                    "best_for": ["videos", "music", "streaming"],
                    "widgets": ["player_controls", "progress_bar", "volume_slider"]
                },
                {
                    "name": "StreamingDashboard",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/entertainment-domain?node-id=49-402",
                    "description": "Content recommendations from streaming",
                    "best_for": ["netflix", "streaming", "recommendations"],
                    "widgets": ["content_row", "thumbnail_card", "rating_display"]
                },
                {
                    "name": "PlaylistManager",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/entertainment-domain?node-id=49-403",
                    "description": "Music playlist with tracks",
                    "best_for": ["spotify", "playlists", "music"],
                    "widgets": ["track_list", "play_button", "duration_display"]
                },
                {
                    "name": "GameLibrary",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/entertainment-domain?node-id=49-404",
                    "description": "Game collection with covers",
                    "best_for": ["games", "gaming", "library"],
                    "widgets": ["game_card", "cover_image", "platform_badge"]
                }
            ],
            
            "generic": [
                {
                    "name": "SummaryView",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/generic-domain?node-id=50-500",
                    "description": "General content summary",
                    "best_for": ["summary", "overview", "general"],
                    "widgets": ["text_card", "bullet_list"]
                },
                {
                    "name": "LinkGrid",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/generic-domain?node-id=50-501",
                    "description": "Grid of links with previews",
                    "best_for": ["links", "bookmarks", "collection"],
                    "widgets": ["link_card", "preview_image"]
                },
                {
                    "name": "TabList",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/generic-domain?node-id=50-502",
                    "description": "Simple list of open tabs",
                    "best_for": ["tabs", "list", "basic"],
                    "widgets": ["tab_item", "favicon"]
                },
                {
                    "name": "TimeTracker",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/generic-domain?node-id=50-503",
                    "description": "Time spent on websites",
                    "best_for": ["analytics", "tracking", "productivity"],
                    "widgets": ["time_chart", "site_breakdown"]
                },
                {
                    "name": "SearchDashboard",
                    "figma_url": "https://www.figma.com/design/VPntNOQdUsyjQ22UMWMaeG/generic-domain?node-id=50-504",
                    "description": "Search bar with recent queries",
                    "best_for": ["search", "queries", "exploration"],
                    "widgets": ["search_input", "history_list"]
                }
            ]
        }
    
    def get_templates_for_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Get all templates for a specific domain"""
        return self.templates.get(domain, self.templates.get("generic", []))
    
    def get_template_meta(self, domain: str, template_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific template"""
        templates = self.get_templates_for_domain(domain)
        
        for template in templates:
            if template["name"] == template_name:
                return template
        
        return None
    
    def find_best_template(
        self,
        domain: str,
        keywords: List[str],
        user_prompt: str = ""
    ) -> str:
        """
        Find the best matching template based on keywords and prompt
        
        Args:
            domain: Target domain
            keywords: Extracted keywords from tabs/history
            user_prompt: User's request
        
        Returns:
            Template name (best match)
        """
        templates = self.get_templates_for_domain(domain)
        
        if not templates:
            return "SummaryView"  # Fallback
        
        # Score each template
        scores = {}
        search_text = f"{user_prompt} {' '.join(keywords)}".lower()
        
        for template in templates:
            score = 0
            
            # Match against best_for keywords
            for keyword in template.get("best_for", []):
                if keyword in search_text:
                    score += 3
            
            # Match against description
            if any(word in template.get("description", "").lower() for word in keywords):
                score += 1
            
            scores[template["name"]] = score
        
        # Return highest scoring template
        if scores:
            best_template = max(scores.items(), key=lambda x: x[1])[0]
            return best_template
        
        # Fallback to first template
        return templates[0]["name"]
    
    def save_registry(self):
        """Save current registry to JSON file"""
        try:
            with open(self.registry_path, 'w') as f:
                json.dump(self.templates, f, indent=2)
            print(f"Registry saved to {self.registry_path}")
        except Exception as e:
            print(f"Failed to save registry: {e}")
    
    def add_template(
        self,
        domain: str,
        name: str,
        figma_node_id: str,
        description: str,
        best_for: List[str],
        widgets: List[str]
    ):
        """Add a new template to the registry"""
        
        if domain not in self.templates:
            self.templates[domain] = []
        
        template = {
            "name": name,
            "figma_node_id": figma_node_id,
            "description": description,
            "best_for": best_for,
            "widgets": widgets
        }
        
        self.templates[domain].append(template)
        self.save_registry()


# =========================================================================
# CLI for managing templates
# =========================================================================

if __name__ == "__main__":
    import sys
    
    registry = TemplateRegistry()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python template_registry.py init          # Create default registry")
        print("  python template_registry.py list <domain> # List templates")
        print("  python template_registry.py find <domain> <keywords>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        registry.save_registry()
        print("✓ Registry initialized with default templates")
    
    elif command == "list":
        domain = sys.argv[2] if len(sys.argv) > 2 else "study"
        templates = registry.get_templates_for_domain(domain)
        print(f"\n{domain.upper()} Templates:")
        for t in templates:
            print(f"  • {t['name']}: {t['description']}")
            print(f"    Figma ID: {t['figma_node_id']}")
            print(f"    Best for: {', '.join(t['best_for'])}\n")
    
    elif command == "find":
        domain = sys.argv[2] if len(sys.argv) > 2 else "study"
        keywords = sys.argv[3:] if len(sys.argv) > 3 else ["research"]
        
        best = registry.find_best_template(domain, keywords)
        print(f"✓ Best template: {best}")