print("DEBUG: Script started")
"""
Data Flow Test Script
====================
Tests that MCP data is properly transformed and injected into React components.

This script verifies:
1. ✅ MCP data is fetched
2. ✅ Domain transforms it to UI props
3. ✅ Figma generator extracts items
4. ✅ React code contains real data
"""

import sys
import os
import asyncio
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from domains import get_domain

def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

async def test_domain_data_extraction(domain_name: str, test_query: str):
    """Test a specific domain's data extraction pipeline"""
    
    print_header(f"Testing {domain_name.upper()} Domain")
    
    # Get domain instance
    domain = get_domain(domain_name)
    print(f"✓ Domain loaded: {domain.__class__.__name__}")
    
    # Simulate browser data
    browser_data = {
        "tabs": [
            {
                "id": 1,
                "title": f"Test {domain_name} content",
                "url": f"https://example.com/{domain_name}",
                "content": test_query
            }
        ],
        "recent_searches": [test_query],
        "tab_count": 1
    }
    
    print(f"DEBUG: Calling domain.process for {domain_name}")
    # Process through domain
    print(f"\n🔄 Processing domain logic...")
    result = await domain.process(
        user_prompt=test_query,
        browser_data=browser_data,
        access_token=None
    )
    print(f"DEBUG: domain.process finished for {domain_name}")
    
    print(f"✓ UI Template: {result.ui_template}")
    print(f"✓ UI Props Keys: {list(result.ui_props.keys())}")
    
    # Check for data
    data_found = False
    data_count = 0
    data_sample = None
    
    # Try to find list data in props
    for key, value in result.ui_props.items():
        if isinstance(value, list) and len(value) > 0:
            data_found = True
            data_count = len(value)
            data_sample = value[0] if value else None
            print(f"\n📊 Found data in '{key}': {data_count} items")
            break
    
    if data_sample:
        print(f"\n✅ SAMPLE DATA:")
        print(json.dumps(data_sample, indent=2)[:500])
    else:
        print(f"\n⚠️ NO LIST DATA FOUND")
        print(f"UI Props content:")
        print(json.dumps(result.ui_props, indent=2)[:500])
    
    # Test React code generation
    print(f"\n🎨 Testing React code generation...")
    
    from figma import generate_dashboard_component
    
    react_code = generate_dashboard_component(
        figma_node_id="test:1",
        figma_preview_url="https://figma.com/test",
        template_name=result.ui_template,
        template_data=result.ui_props,
        domain=domain_name
    )
    
    print(f"✓ React code generated: {len(react_code)} characters")
    
    # Check if code contains actual data
    has_data_array = 'const data =' in react_code
    has_placeholder = '"No data found"' in react_code or '"title": "📋' in react_code
    has_real_data = has_data_array and not has_placeholder
    
    if has_real_data:
        print(f"✅ React code contains REAL DATA")
        # Extract a sample from the data array
        try:
            data_start = react_code.find('const data = [')
            data_end = react_code.find('];', data_start)
            data_snippet = react_code[data_start:data_start+300]
            print(f"\nData array preview:")
            print(data_snippet + "...")
        except:
            pass
    elif has_placeholder:
        print(f"⚠️ React code contains PLACEHOLDER DATA")
    else:
        print(f"❌ React code has NO DATA ARRAY")
    
    # Final verdict
    print(f"\n{'='*70}")
    if data_found and has_real_data:
        print(f"✅ {domain_name.upper()} DOMAIN: PASS")
        print(f"   - MCP data extracted: ✓")
        print(f"   - UI props populated: ✓")
        print(f"   - React code generated: ✓")
    elif data_found and not has_real_data:
        print(f"⚠️ {domain_name.upper()} DOMAIN: PARTIAL")
        print(f"   - MCP data extracted: ✓")
        print(f"   - UI props populated: ✓")
        print(f"   - React code generated: ✗ (placeholder only)")
    else:
        print(f"❌ {domain_name.upper()} DOMAIN: FAIL")
        print(f"   - MCP data extracted: ✗")
        print(f"   - UI props populated: ✗")
        print(f"   - React code generated: ✗")
    print(f"{'='*70}\n")
    
    return data_found and has_real_data


async def main():
    """Test all domains"""
    
    print("\n" + "="*70)
    print("  DATA FLOW VALIDATION TEST")
    print("  Testing MCP → Domain → Figma → React pipeline")
    print("="*70)
    
    # Define test cases
    test_cases = [
        ("shopping", "wireless headphones under $100"),
        ("generic", "latest news"),
        ("generic", "weather in London"),
        ("code", "react hooks tutorial")
    ]
    
    results = {}
    
    for domain_name, query in test_cases:
        try:
            success = await test_domain_data_extraction(domain_name, query)
            results[domain_name] = success
        except Exception as e:
            print(f"❌ {domain_name} test CRASHED: {e}")
            results[domain_name] = False
            import traceback
            traceback.print_exc()
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for domain, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}  {domain}")
    
    print(f"\n{'='*70}")
    print(f"Results: {passed}/{total} domains passed")
    print(f"{'='*70}\n")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Data flow is working correctly.")
        return True
    elif passed > 0:
        print("⚠️ PARTIAL SUCCESS. Some domains need fixing.")
        print("\nNext steps:")
        print("1. Check which domains failed")
        print("2. Verify MCP API keys are set")
        print("3. Check domain prepare_ui_props() methods")
        print("4. Verify figma.py data extraction logic")
        return False
    else:
        print("❌ ALL TESTS FAILED!")
        print("\nPossible causes:")
        print("1. MCP API keys not set (check .env)")
        print("2. Domain files not updated")
        print("3. figma.py not updated")
        print("4. Network issues")
        return False


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Loaded .env file")
    except:
        print("⚠️ No .env file or dotenv not installed")
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)