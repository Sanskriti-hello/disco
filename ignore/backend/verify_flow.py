import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from langraph.graph import sandbox_logic_node
from ui_templates.template_loader import TemplateLoader
from sandbox_builders.entertainment_builder import update_json

async def verify_flow():
    print("🚀 Starting Verification Flow...")
    
    # 1. Test Template Loader
    print("\n🔍 Testing TemplateLoader...")
    loader = TemplateLoader()
    template = loader.select_template(
        domain="entertainment",
        keywords=["movie"],
        user_prompt="find me action movies",
        tab_count=1,
        tab_urls=[]
    )
    print(f"✅ Template Selected: {template['template_id']}")
    
    # 2. Test Sandbox Logic Node (Mock State)
    print("\n🧠 Testing Sandbox Logic Node...")
    mock_state = {
        "primary_domain": "entertainment",
        "user_prompt": "Show me top rated action movies from 2024",
        "tabs": [{"title": "Google", "url": "https://google.com"}],
        "history": [],
        "validation_attempts": 0
    }
    
    try:
        new_state = await sandbox_logic_node(mock_state)
        
        if "error" in new_state:
            print(f"❌ Error in logic node: {new_state['error']}")
            return

        print(f"✅ Template ID in State: {new_state.get('selected_template')}")
        
        data = new_state.get("template_data", {})
        print(f"📦 Template Data Keys: {list(data.keys())}")
        
        # Check if data looks filled (not just empty template)
        # This confirms MCP tools + LLM ran
        print(f"📄 Sample Data: {str(data)[:200]}...")
        
    except Exception as e:
        print(f"❌ Exception in logic node: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_flow())
