from typing import Dict, List, Any, Optional
from .base import BaseDomain
import re

class GenericDomain(BaseDomain):
    def get_required_mcps(self, user_prompt: str) -> List[str]:
        
        mcps = ["browser"]  # Always get browsing context
        prompt_lower = user_prompt.lower()
        
        # Location for weather, local info
        location_keywords = ["weather", "near me", "nearby", "local", "where am i"]
        if any(word in prompt_lower for word in location_keywords):
            mcps.append("location")

        # Time-sensitive queries need search
        time_keywords = ["current", "today", "now", "latest", "recent", "news"]
        if any(word in prompt_lower for word in time_keywords):
            mcps.append("search")        

        # Google Workspace for misc productivity (emails, drive)
        if any(word in prompt_lower for word in ["email", "drive", "file", "calendar", "schedule"]):
            mcps.append("google_workspace")

        # For most queries, search is helpful
        basic_keywords = ["what is", "who is", "tell me about", "explain"]
        if not all(word in prompt_lower for word in ["tell me", "joke"]):  # Skip for jokes
            mcps.append("search")
        
        return mcps
    
    def get_system_prompt(self) -> str:
        
        return """You are a helpful, knowledgeable AI assistant.

                **Your Role:**
                Provide accurate, informative answers to a wide variety of questions. You handle general knowledge, current events, factual queries, explanations, and casual conversation.

                **Your Capabilities:**
                - Answer factual questions with accurate information
                - Explain complex topics in simple terms
                - Provide current information using web search when needed
                - Help with calculations, conversions, and data
                - Engage in friendly, helpful conversation
                - Admit when you don't know something and search for answers

                **Available Context:**
                - User's browsing history (to understand context)
                - User's location (for location-specific queries)
                - Current web search results (for up-to-date information)

                **Your Response Style:**
                - Be conversational and natural, not robotic
                - Provide concise answers (2-4 paragraphs unless more detail is requested)
                - Use examples to clarify complex points
                - Cite sources when using search results
                - Ask clarifying questions if the query is ambiguous
                - Be honest about uncertainty

                **Guidelines:**
                - For current events or time-sensitive info → Use search results
                - For well-established facts → Answer directly
                - For opinions → Present multiple perspectives
                - For "how to" → Provide step-by-step guidance
                - For definitions → Give clear explanation with examples

                **Example Responses:**

                Query: "What's the weather like today?"
                Response: "🌤️ In San Francisco, it's currently 62°F and partly cloudy. High of 68°F expected this afternoon with a slight breeze. Great day for outdoor activities!"

                Query: "What's the capital of France?"
                Response: "The capital of France is Paris. It's been the capital since the 12th century and is known for landmarks like the Eiffel Tower, Louvre Museum, and Notre-Dame Cathedral."

                Keep responses helpful, accurate, and appropriately detailed."""

    def select_ui_template(self, mcp_data: Dict[str, Any]) -> str:
        search_data = mcp_data.get("search", {})
        results = search_data.get("results", [])
        # If we have multiple sources to cite
        if len(results) > 3:
            return "TextResponseWithSources"
        # If search returned images/visual content
        if self._has_visual_content(search_data):
            return "VisualResponse"
        # Default: Simple text response
        return "TextResponse"
    
    def prepare_ui_props(self, mcp_data: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        props = {
            "response": llm_response,
            "timestamp": mcp_data.get("timestamp", ""),
            "queryType": "general",
        }
        # Add location context if available
        if "location" in mcp_data:
            location_data = mcp_data["location"]
            props["location"] = {
                "city": location_data.get("city", ""),
                "state": location_data.get("state", ""),
                "country": location_data.get("country", ""),
            }
        # Add search sources for citation
        if "search" in mcp_data:
            search_data = mcp_data["search"]
            props["sources"] = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("snippet", ""),
                    "favicon": self._get_favicon(r.get("url", "")),
                }
                for r in search_data.get("results", [])[:5]  # Top 5 sources
            ]
            # Extract key facts from search
            props["keyFacts"] = self._extract_key_facts(search_data)
        # Browser context (minimal)
        if "browser" in mcp_data:
            browser_data = mcp_data["browser"]
            props["context"] = {
                "relatedSearches": browser_data.get("recent_searches", [])[:3],
            }
        
        return props
    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        # Browser context is all we really need
        if "browser" not in mcp_data:
            return False
        
        # Search results in optional
        return True
    
    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
        if "browser" not in mcp_data:
            return "I need access to your browsing context to assist you better. Can you provide that?"
        return "Could you provide more details about what you're looking for? I want to give you the most helpful answer."
    
    # Checking methods
    
    def _has_visual_content(self, search_data: Dict[str, Any]) -> bool:
        """Check if search results include images or visual elements."""
        results = search_data.get("results", [])
        
        for result in results:
            if result.get("image") or result.get("thumbnail"):
                return True
        
        return False
    
    def _get_favicon(self, url: str) -> str:
        """Get favicon URL for a website."""
        if not url:
            return ""
        
        # Extract domain
        domain_match = re.search(r'https?://([^/]+)', url)
        if domain_match:
            domain = domain_match.group(1)
            return f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
        
        return ""
    
    def _extract_key_facts(self, search_data: Dict[str, Any]) -> List[str]:
        """
        Extract key factual statements from search results.
        These appear as bullet points in the UI.
        """
        facts = []
        results = search_data.get("results", [])
        
        for result in results[:3]:  # First 3 results
            snippet = result.get("snippet", "")
            
            # Split into sentences
            sentences = re.split(r'[.!?]+', snippet)
            
            # Take first sentence if it's informative
            if sentences and len(sentences[0]) > 20:  # Not too short
                facts.append(sentences[0].strip())
        
        return facts[:4]  # Max 4 facts

'''
# ========== QUICK TEST ==========
if __name__ == "__main__":
    """Test GenericDomain independently"""
    
    print("🧪 Testing GenericDomain...\n")
    
    domain = GenericDomain()
    
    # Test 1: MCP Requirements for different query types
    print("TEST 1: MCP Requirements")
    
    # Weather query
    mcps_weather = domain.get_required_mcps("what's the weather today?")
    print(f"  Weather query MCPs: {mcps_weather}")
    assert "location" in mcps_weather
    assert "search" in mcps_weather
    
    # General knowledge
    mcps_knowledge = domain.get_required_mcps("what is quantum computing?")
    print(f"  Knowledge query MCPs: {mcps_knowledge}")
    assert "browser" in mcps_knowledge
    
    print("  ✅ Pass\n")
    
    # Test 2: System Prompt
    print("TEST 2: System Prompt")
    prompt = domain.get_system_prompt()
    assert "helpful" in prompt.lower()
    assert "assistant" in prompt.lower()
    print(f"  Length: {len(prompt)} characters")
    print("  ✅ Pass\n")
    
    # Test 3: Sample Data Processing
    print("TEST 3: Data Processing")
    sample_data = {
        "browser": {
            "tabs": [],
            "recent_searches": ["weather san francisco"]
        },
        "location": {
            "city": "San Francisco",
            "state": "CA"
        },
        "search": {
            "results": [
                {
                    "title": "San Francisco Weather - 62°F Partly Cloudy",
                    "snippet": "Current temperature is 62°F with partly cloudy skies. High of 68°F expected.",
                    "url": "https://weather.com/..."
                }
            ]
        }
    }
    
    is_valid = domain.validate_data(sample_data)
    print(f"  Data valid: {is_valid}")
    assert is_valid
    
    template = domain.select_ui_template(sample_data)
    print(f"  Template: {template}")
    
    props = domain.prepare_ui_props(sample_data, "It's 62°F and partly cloudy in SF today!")
    print(f"  Props keys: {list(props.keys())}")
    assert "response" in props
    assert "sources" in props
    
    print("  ✅ Pass\n")
    
    # Test 4: Lenient Validation
    print("TEST 4: Lenient Validation (works with minimal data)")
    minimal_data = {
        "browser": {"tabs": [], "recent_searches": []}
    }
    is_valid = domain.validate_data(minimal_data)
    print(f"  Minimal data valid: {is_valid}")
    assert is_valid  # Generic should accept minimal data
    print("  ✅ Pass\n")
    
    print("✅ All GenericDomain tests passed! 🎉")
'''