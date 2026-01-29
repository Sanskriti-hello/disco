from typing import Dict,List,Any,Optional
from .base import BaseDomain

class ShoppingDomain(BaseDomain):
    """
    Handles: product search,comparison,pricing,recomendation

    Example queries:
        "Compare iPhone and Samsung"
        "Which phone should i buy under 50000
        "Show pros and cons of these laptops"
    """

    def get_required_mcps(self,user_prompt: str) -> List[str]:
        mcps=["browser"]
        prompt=user_prompt.lower()
        
        # Product Comparison or search
        if any(word in prompt for word in ["compare","vs","difference","best","suitable","affordable"]):
            mcps.append("search")
            
        # Recommendation
        if any(word in  prompt for word in ["buy","recommend","suggest","choose","rating","review"]):
            mcps.append("reviews")
            
        # Amazon & eBay for products
        mcps.extend(["amazon", "ebay"])
            
        # Price and Currency
        if any(word in prompt for word in ["price","cheap","budget","under"]):
            mcps.append("pricing")
            
        # International shopping checks
        if any(word in prompt for word in ["usd", "eur", "convert", "currency", "foreign"]):
            mcps.append("exchange_rate")
            
        # location
        if any(word in prompt for word in ["near", "nearby", "store", "offline"]):
            mcps.append("location")
        
        mcps.append("search")
        return list(set(mcps))
     


    def get_system_prompt(self) -> str:
        return """
    You are a smart shopping assistant helping users make better purchase decisions.

Your capabilities:
- Compare products clearly and objectively
- Highlight pros and cons
- Recommend the best options based on user needs
- Consider budget, features, and overall value for money

Reasoning approach:
- First understand the users intent and constraints
- Compare relevant options using available data
- Filter out poor-value choices
- Recommend 2-3 best options with clear justification

Rules:
- Do not hallucinate exact prices
- Use price ranges if unsure
- If information is incomplete, state assumptions clearly
- Stay unbiased and factual

Preference handling:
- If user preferences are provided (e.g., budget sensitivity, quality focus), prioritize recommendations accordingly

Output guidelines:
- Keep responses concise and structured
- Use bullet points for pros and cons
- Clearly state who each option is best for

Tone:
- Helpful
- Practical
- Decision-focused

Example:
"Based on your budget of ₹30,000, Phone A offers excellent battery life and consistent performance, while Phone B stands out for its camera quality. If battery life matters more, Phone A is the better choice; for photography, Phone B is preferable."
    """


    def select_ui_template(self,mcp_data:Dict[str,Any]) -> str:
        if "reviews" in mcp_data and "pricing" in mcp_data:
            return "ProductRecomendation"
        if "search" in mcp_data:
            return "ProductComparisonTable"
        
        return "ShoppingList"

    def prepare_ui_props(
            self, mcp_data:Dict[str,Any],llm_response: str
    ) -> Dict[str,Any]:
        
        props={
            "userMessage": llm_response,
            "timestamp": mcp_data.get("timestamp","")
        }
        if "search" in mcp_data:
            props["products"] = mcp_data["search"].get("results", [])
        if "pricing" in mcp_data:
            props["pricing"] = mcp_data["pricing"]
        if "reviews" in mcp_data:
            props["reviews"] = mcp_data["reviews"]
        if "location" in mcp_data:
            props["location"] = mcp_data["location"]
        
        return props
    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        """
        Check whether we have the minimum data required
        to proceed with a shopping response.
        """

        #  Browser context is mandatory
        if "browser" not in mcp_data:
            return False

        #  We must have at least some product-related data
        if "search" not in mcp_data and "reviews" not in mcp_data:
            return False
        if "location" in mcp_data and not mcp_data["location"]:
            return False


        # If we reach here, data is sufficient
        return True

    def get_follow_up_question(self, mcp_data:Dict[str,Any]) -> Optional[str]:
        # Browser context missing
        if "browser" not in mcp_data:
            return (
                "I need access to your browsing context to help you better. "
                "Could you please allow it"
            )
        # Location was required but not provided
        if "location" not in mcp_data:
            return (
                "To help you find nearby stores, could you share your city"
                "or allow location access"
            )
        # No product information available
        if "search" not in mcp_data and "reviews" not in mcp_data:
            return (
                "Could you tell me which product or category you are interested in?"
            )
        #Genric fallback
        return (
    "To help me recommend the best option, could you tell me what matters most "
    "to you for this product? For example: price, quality, performance, brand, "
    "or specific features."
)