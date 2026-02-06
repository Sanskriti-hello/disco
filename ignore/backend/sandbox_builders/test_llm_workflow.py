
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))
from entertainment_builder import update_json

if __name__ == "__main__":
    print("[DEBUG] Starting LLM workflow test...")
    test_json = '{"query": "laptop", "country": "US", "page": 1}'
    template = '{"products": ""}'
    try:
        result = update_json(template, page_context="Amazon product search", field_context=test_json)
        print("[DEBUG] LLM workflow result:")
        print(result)
    except Exception as e:
        print(f"[DEBUG] Exception during LLM workflow: {e}")
