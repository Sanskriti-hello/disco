"""
Quick Integration Test - Local Template System
Tests the complete pipeline from template selection to React code generation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_template_selection():
    print("\n=== TEST 1: Template Selection ===")
    from ui_templates.template_loader import TemplateLoader
    
    loader = TemplateLoader()
    
    # Test code domain selection
    result = loader.select_template(
        domain="code",
        keywords=["github", "debug", "python"],
        user_prompt="help me debug python",
        tab_count=3,
        tab_urls=["https://github.com/test"]
    )
    
    print(f"✓ Selected: {result['template_id']}")
    print(f"  Score: {result['score']:.2f}")
    assert result['template_id'] == 'code-1', "Should select code-1 for code domain"
    
    # Test shopping domain
    result2 = loader.select_template(
        domain="shopping",
        keywords=["buy", "laptop", "price"],
        user_prompt="buy laptop under $1000",
        tab_count=5,
        tab_urls=["https://amazon.com"]
    )
    
    print(f"✓ Selected: {result2['template_id']}")
    assert result2['template_id'] == 'shopping-1', "Should select shopping-1"
    
    print("✅ Template selection works!\n")
    return True


def test_domain_data_transform():
    print("=== TEST 2: Domain Data Transformation ===")
    from domains import get_domain
    
    # Test code domain
    code_domain = get_domain('code')
    
    mock_mcp_data = {
        "browser": {
            "tabs": [
                {"title": "Python Tutorial", "url": "https://docs.python.org", "content": "def example():\n    pass"}
            ]
        },
        "search": {
            "results": [
                {"title": "Python Docs", "url": "https://python.org", "snippet": "Official documentation"}
            ]
        }
    }
    
    template_data = code_domain.prepare_template_data(
        template_id="code-1",
        mcp_data=mock_mcp_data,
        llm_response="Here's your code help"
    )
    
    print(f"✓ Code domain returns: {list(template_data.keys())}")
    assert "code_snippets" in template_data, "Should have code_snippets"
    assert "documentation" in template_data, "Should have documentation"
    
    # Test shopping domain
    shopping_domain = get_domain('shopping')
    
    mock_shopping_data = {
        "amazon": {
            "data": {
                "products": [
                    {
                        "product_title": "Laptop",
                        "product_price": "$999",
                        "product_star_rating": "4.5",
                        "product_num_ratings": 1200,
                        "product_url": "https://amazon.com/laptop"
                    }
                ]
            }
        }
    }
    
    shopping_template_data = shopping_domain.prepare_template_data(
        template_id="shopping-1",
        mcp_data=mock_shopping_data,
        llm_response="Here are laptops under $1000"
    )
    
    print(f"✓ Shopping domain returns: {list(shopping_template_data.keys())}")
    assert "products" in shopping_template_data, "Should have products"
    assert len(shopping_template_data["products"]) > 0, "Should have at least 1 product"
    
    print("✅ Domain data transformation works!\n")
    return True


def test_component_loading():
    print("=== TEST 3: Component Loading ===")
    from ui_templates.template_loader import TemplateLoader
    
    loader = TemplateLoader()
    
    # Test loading code-1
    code = loader.load_template_component('code-1')
    print(f"✓ Loaded code-1: {len(code)} chars")
    assert len(code) > 1000, "Component should be substantial"
    assert "import React" in code, "Should be a React component"
    
    # Test loading generic-1
    generic = loader.load_template_component('generic-1')
    print(f"✓ Loaded generic-1: {len(generic)} chars")
    assert len(generic) > 1000, "Component should be substantial"
    
    print("✅ Component loading works!\n")
    return True


def test_data_injection():
    print("=== TEST 4: Data Injection ===")
    from ui_templates.template_loader import TemplateLoader
    from ui_templates.data_injector import DataInjector
    
    loader = TemplateLoader()
    injector = DataInjector()
    
    # Load code-1 template
    react_code = loader.load_template_component('code-1')
    
    # Inject test data
    test_data = {
        "title": "My Code Dashboard",
        "code_snippets": [
            {
                "language": "python",
                "code": "def hello():\n    print('world')",
                "filename": "test.py",
                "explanation": "Test function"
            }
        ],
        "documentation": [
            {"title": "Python Docs", "content": "Official docs", "url": "https://python.org"}
        ],
        "terminal_output": "Everything looks good!"
    }
    
    injected = injector.inject_data(
        react_code=react_code,
        template_id='code-1',
        data=test_data,
theme_config={}
    )
    
    print(f"✓ Injected data: {len(injected)} chars")
    assert len(injected) >= len(react_code), "Injected code should be same or larger"
    assert "My Code Dashboard" in injected, "Title should be injected"
    
    print("✅ Data injection works!\n")
    return True


def test_full_pipeline():
    print("=== TEST 5: Full Pipeline (template_generator.py) ===")
    from template_generator import generate_dashboard_from_template
    
    test_data = {
        "title": "Test Dashboard",
        "links": [
            {"title": "Link 1", "url": "https://example.com", "summary": "Test"},
            {"title": "Link 2", "url": "https://example.org", "summary": "Test 2"}
        ]
    }
    
    user_context = {
        "keywords": ["test", "links"],
        "user_prompt": "show my links",
        "tab_count": 2,
        "tab_urls": ["https://example.com"]
    }
    
    result = generate_dashboard_from_template(
        domain="generic",
        template_data=test_data,
        user_context=user_context
    )
    
    print(f"✓ Generated: {len(result)} chars")
    assert len(result) > 500, "Should generate substantial code"
    assert "import React" in result, "Should be React component"
    assert "export default" in result or "export {" in result, "Should have export"
    
    print("✅ Full pipeline works!\n")
    return True


def main():
    print("\n" + "="*70)
    print("  LOCAL TEMPLATE SYSTEM - INTEGRATION TEST")
    print("="*70)
    
    tests = [
        ("Template Selection", test_template_selection),
        ("Domain Data Transform", test_domain_data_transform),
        ("Component Loading", test_component_loading),
        ("Data Injection", test_data_injection),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("="*70)
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! System is ready for deployment.")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please review errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
