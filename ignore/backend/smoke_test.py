"""
Disco Backend Final Smoke Test
==============================
Verifies the complete pipeline for a sample request without emojis to avoid encoding issues.
"""

import sys
import os
import asyncio
import json
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langraph.graph import build_graph

async def run_test(domain: str, prompt: str):
    print(f"\n" + "="*50)
    print(f"TESTING DOMAIN: {domain.upper()}")
    print(f"Prompt: {prompt}")
    print("="*50)
    
    initial_state = {
        "user_prompt": prompt,
        "tabs": [
            {
                "id": 1, 
                "title": f"Recent {domain} information", 
                "url": "https://example.com/topic", 
                "content": f"Detailed content about {domain} specifically for research purposes."
            }
        ],
        "history": [],
        "primary_domain": domain,
        "domain_scores": {domain: 1.0},
        "tab_clusters": [],
        "selected_template": None,
        "template_data": None,
        "react_code": None,
        "widgets": [],
        "error": None,
        "access_token": None,
        "is_valid_ui": False,
        "validation_attempts": 0,
        "sandbox_id": None,
        "sandbox_embed_url": None,
        "sandbox_preview_url": None
    }
    
    graph = build_graph()
    
    try:
        print("Executing Workflow...")
        result = await graph.ainvoke(initial_state, {"recursion_limit": 15})
        
        print(f"\nDONE: WORKFLOW COMPLETED")
        print(f"   Template: {result.get('selected_template')}")
        
        if result.get("react_code"):
            print(f"   React Code: Generated ({len(result['react_code'])} bytes)")
        else:
            print(f"   ERROR: React Code: FAILED")
            
        if result.get("sandbox_id"):
            print(f"   CodeSandbox: Created (ID: {result['sandbox_id']})")
            print(f"   Embed URL: {result['sandbox_embed_url']}")
        else:
            print(f"   INFO: CodeSandbox: FAILED or SKIPPED")
            
        if result.get("error"):
            print(f"   WARNING: Logged Error: {result['error']}")
            
        return result
        
    except Exception as e:
        print(f"ERROR: TEST FAILED: {str(e)}")
        return None

async def main():
    load_dotenv()
    
    # Test 'code' domain
    await run_test("code", "I need to debug some react hooks examples")
    
    print("\n" + "~"*50)

if __name__ == "__main__":
    asyncio.run(main())
