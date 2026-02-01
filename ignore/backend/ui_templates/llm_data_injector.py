"""
LLM-Based Data Injector - Intelligent Template Data Injection
Uses Gemini to intelligently inject data into React components while preserving structure
"""

import os
import json
from typing import Dict, Any, Optional
import google.generativeai as genai


class LLMDataInjector:
    """Uses LLM to intelligently inject data into React templates"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None
            print("⚠️ No GEMINI_API_KEY found - LLM injection disabled, using fallback")
    
    async def inject_data_with_llm(
        self,
        react_code: str,
        template_id: str,
        data: Dict[str, Any],
        theme_config: Dict[str, Any]
    ) -> str:
        """
        Use LLM to intelligently inject data into React component
        
        Args:
            react_code: Original React component code
            template_id: Template ID (code-1, shopping-1, etc.)
            data: Data to inject
            theme_config: Theme configuration
        
        Returns: Modified React component with data injected
        """
        if not self.model:
            print("⚠️ Falling back to regex injection (no LLM)")
            from ui_templates.data_injector import DataInjector
            injector = DataInjector()
            return injector.inject_data(react_code, template_id, data, theme_config)
        
        prompt = self._build_injection_prompt(react_code, template_id, data, theme_config)
        
        try:
            response = await self.model.generate_content_async(prompt)
            injected_code = self._extract_code_from_response(response.text)
            
            # Validate the injected code
            if self._validate_injected_code(injected_code, react_code):
                print("✅ LLM injection successful")
                return injected_code
            else:
                print("⚠️  LLM injection validation failed, using fallback")
                from ui_templates.data_injector import DataInjector
                injector = DataInjector()
                return injector.inject_data(react_code, template_id, data, theme_config)
                
        except Exception as e:
            print(f"❌ LLM injection error: {e}, using fallback")
            from ui_templates.data_injector import DataInjector
            injector = DataInjector()
            return injector.inject_data(react_code, template_id, data, theme_config)
    
    def _build_injection_prompt(
        self,
        react_code: str,
        template_id: str,
        data: Dict[str, Any],
        theme_config: Dict[str, Any]
    ) -> str:
        """Build prompt for LLM to inject data"""
        
        data_json = json.dumps(data, indent=2)
        theme_json = json.dumps(theme_config, indent=2)
        
        prompt = f"""You are a React code transformation expert. Your task is to inject dynamic data into a React component template while PRESERVING all existing styling, classes, and structure.

**Template ID:** {template_id}

**Original React Component:**
```jsx
{react_code}
```

**Data to Inject:**
```json
{data_json}
```

**Theme Configuration:**
```json
{theme_json}
```

**Instructions:**
1. **PRESERVE STYLING**: Do NOT remove or modify any className, style, or CSS properties
2. **PRESERVE STRUCTURE**: Keep all div IDs, nested elements, and component hierarchy intact
3. **INJECT DATA SMARTLY**: Replace placeholder text and static arrays with dynamic data:
   - Replace static titles like "TITLE" or "Dashboard" with `{{data.title}}`
   - Replace static card arrays with `.map()` over data arrays
   - Use conditional rendering for optional fields (e.g., `{{data.price_range && ...}}`)
4. **ICONS & APIS**: If the template uses icons from lucide-react, keep all icon imports and usages
5. **DYNAMIC RENDERING**: Make the component truly dynamic - data should flow through props or state
6. **TAILWIND CLASSES**: Do NOT modify any Tailwind CSS classes
7. **EXPORT**: Ensure component has proper `export default`

**Template-Specific Rules:**

{self._get_template_specific_rules(template_id)}

**Output:**
Return ONLY the complete modified React component code. Do NOT include explanations or markdown code blocks - just the raw JSX code.
"""
        return prompt
    
    def _get_template_specific_rules(self, template_id: str) -> str:
        """Get template-specific injection rules"""
        rules = {
            "code-1": """
- Inject code snippets into the large code display area (Rectangle_65)
- Display documentation links in the sidebar
- Show terminal output at the bottom
- Preserve the green #00FF41 matrix theme
- Keep all file/folder tree structures""",
            
            "generic-1": """
- Create cards for each link in data.links
- Show favicon, title, URL, and summary for each link
- Preserve the blue #3B82F6 card theme
- Add hover effects on cards""",
            
            "generic-2": """
- Make search bar functional (filter items)
- Display items in masonry grid
- Show tags/categories
- Preserve yellow/amber #FBBF24 theme
- Enable filter/sort functionality""",
            
            "shopping-1": """
- Create product cards for each item in data.products
- Show price, rating (stars), review count
- Display "original_price" with strikethrough if different from current price
- Preserve purple/pink theme (#A855F7, #EC4899)
- Make ratings visual with star icons"""
        }
        return rules.get(template_id, "- Inject data following React best practices")
    
    def _extract_code_from_response(self, response_text: str) -> str:
        """Extract code from LLM response (handle markdown code blocks)"""
        # If response has markdown code blocks, extract them
        if "```" in response_text:
            # Find code between ```jsx or ```javascript and ```
            import re
            match = re.search(r'```(?:jsx|javascript|js)?\n(.*?)\n```', response_text, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # Otherwise return as-is
        return response_text.strip()
    
    def _validate_injected_code(self, injected_code: str, original_code: str) -> bool:
        """Validate that injection preserved structure"""
        # Basic validation checks
        checks = [
            len(injected_code) > len(original_code) * 0.5,  # Not too short
            "import React" in injected_code,  # Has React import
            "export default" in injected_code or "export {" in injected_code,  # Has export
            injected_code.count("{") == injected_code.count("}"),  # Balanced braces
            injected_code.count("(") == injected_code.count(")"),  # Balanced parens
        ]
        
        return all(checks)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def test_injection():
        injector = LLMDataInjector()
        
        test_code = """import React from 'react';

const TestComponent = () => {
  return (
    <div className="bg-gray-900 text-white p-8">
      <h1 className="text-4xl font-bold">TITLE</h1>
      <div className="grid grid-cols-3 gap-4">
        {/* Static cards here */}
      </div>
    </div>
  );
};

export default TestComponent;"""
        
        test_data = {
            "title": "My Dashboard",
            "items": [
                {"title": "Item 1", "url": "https://example.com"},
                {"title": "Item 2", "url": "https://example.org"}
            ]
        }
        
        result = await injector.inject_data_with_llm(
            react_code=test_code,
            template_id="generic-1",
            data=test_data,
            theme_config={}
        )
        
        print("=== INJECTED CODE ===")
        print(result[:500])
    
    asyncio.run(test_injection())
