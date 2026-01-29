"""
Backend Integration Test Script
================================
This script provides an end-to-end test of the entire backend pipeline,
simulating what happens when the Chrome extension calls the API.

It will:
1. Test all domain imports
2. Test the LangGraph build
3. Test the full dashboard generation workflow
4. Report any mock data or placeholders that could cause issues
"""

import sys
import os
import asyncio
import json

# Ensure backend modules are discoverable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from domains import get_domain, list_domains
from langraph.graph import build_graph, AgentState
from ui_templates.registry import TemplateRegistryV2

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_domain_imports():
    """Test that all domains can be imported and instantiated."""
    print_header("1. Testing Domain Imports")
    
    domains = list_domains()
    print(f"Registered domains: {domains}")
    
    issues = []
    for domain_name in domains:
        try:
            domain = get_domain(domain_name)
            print(f"  ✓ {domain_name}: {domain.__class__.__name__}")
        except Exception as e:
            issues.append(f"{domain_name}: {e}")
            print(f"  ✗ {domain_name}: FAILED - {e}")
    
    return len(issues) == 0, issues

def test_graph_build():
    """Test that the LangGraph can be built."""
    print_header("2. Testing LangGraph Build")
    
    try:
        graph = build_graph()
        print(f"  ✓ Graph built successfully")
        print(f"  ✓ Nodes: domain_logic, select_template, render, codesandbox_check")
        return True, []
    except Exception as e:
        print(f"  ✗ Graph build FAILED: {e}")
        return False, [str(e)]

def test_registry():
    """Test the template registry."""
    print_header("3. Testing Template Registry")
    
    try:
        registry = TemplateRegistryV2()
        
        for domain in ["study", "shopping", "code", "entertainment"]:
            result = registry.find_best_template(
                domain=domain,
                keywords=["test"],
                user_prompt="test query"
            )
            print(f"  ✓ {domain}: {result['template_name']} (score: {result['score']:.2f})")
        
        return True, []
    except Exception as e:
        print(f"  ✗ Registry FAILED: {e}")
        return False, [str(e)]

async def test_full_workflow():
    """Test the complete dashboard generation workflow."""
    print_header("4. Testing Full Workflow (Study Domain)")
    
    # Simulate extension request
    initial_state = {
        "user_prompt": "Create a dashboard for my research papers",
        "tabs": [
            {"id": 1, "title": "Attention Is All You Need - ArXiv", "url": "https://arxiv.org/abs/1706.03762", "content": "Transformer architecture paper"},
            {"id": 2, "title": "BERT Paper", "url": "https://arxiv.org/abs/1810.04805", "content": "NLP language model"},
        ],
        "history": [],
        "primary_domain": "study",
        "tab_clusters": [],
        "selected_template": None,
        "template_data": None,
        "figma_node_id": None,
        "figma_preview_url": None,
        "error": None,
        "access_token": None,
        "react_code": None,
        "is_valid_ui": False,
        "validation_attempts": 0
    }
    
    issues = []
    
    try:
        graph = build_graph()
        result = await graph.ainvoke(initial_state, {"recursion_limit": 15})
        
        print(f"  Domain: {result.get('primary_domain')}")
        print(f"  Template: {result.get('selected_template')}")
        print(f"  Figma Node: {result.get('figma_node_id')}")
        print(f"  UI Valid: {result.get('is_valid_ui')}")
        print(f"  Attempts: {result.get('validation_attempts')}")
        
        if result.get("error"):
            print(f"  ⚠️ Error: {result.get('error')}")
            issues.append(f"Workflow error: {result.get('error')}")
        
        if result.get("react_code"):
            code_len = len(result["react_code"])
            print(f"  ✓ React Code Generated: {code_len} chars")
            
            # Check for placeholder content
            code = result["react_code"]
            if "TODO" in code:
                issues.append("React code contains TODO placeholders")
            if "mock" in code.lower() and "data" in code.lower():
                issues.append("React code may contain mock data references")
        else:
            issues.append("No React code was generated")
            print(f"  ✗ No React code generated")
        
        # Check template_data
        template_data = result.get("template_data", {})
        if not template_data:
            issues.append("template_data is empty")
        else:
            print(f"  ✓ Template Data Keys: {list(template_data.keys())}")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        print(f"  ✗ Workflow FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, [str(e)]

def check_env_variables():
    """Check for required environment variables."""
    print_header("5. Checking Environment Variables")
    
    required = ["RAPIDAPI_KEY"]
    optional = ["FIGMA_ACCESS_TOKEN", "FIGMA_FILE_KEY", "TAVILY_API_KEY"]
    
    issues = []
    
    for var in required:
        value = os.getenv(var)
        if value:
            print(f"  ✓ {var}: Set ({len(value)} chars)")
        else:
            print(f"  ✗ {var}: MISSING (Required)")
            issues.append(f"Missing required env var: {var}")
    
    for var in optional:
        value = os.getenv(var)
        if value:
            print(f"  ✓ {var}: Set ({len(value)} chars)")
        else:
            print(f"  ⚠️ {var}: Not set (Optional)")
    
    return len(issues) == 0, issues

def check_mcp_imports():
    """Check that all MCP tools can be imported."""
    print_header("6. Checking MCP Tool Imports")
    
    mcps = [
        ("mcp_tools.search", "SearchClient"),
        ("mcp_tools.arxiv", "ArxivClient"),
        ("mcp_tools.youtube", "YouTubeMCP"),
        ("mcp_tools.spotify", "SpotifyClient"),
        ("mcp_tools.movie", "MovieClient"),
        ("mcp_tools.news", "NewsClient"),
        ("mcp_tools.amazon", "AmazonClient"),
        ("mcp_tools.exchange_rate", "FinancialClient"),
        ("mcp_tools.google_workspace", "GoogleWorkspaceMCP"),
    ]
    
    issues = []
    
    for module, class_name in mcps:
        try:
            mod = __import__(module, fromlist=[class_name])
            cls = getattr(mod, class_name)
            print(f"  ✓ {module}.{class_name}")
        except Exception as e:
            print(f"  ✗ {module}.{class_name}: {e}")
            issues.append(f"{module}.{class_name}: {e}")
    
    return len(issues) == 0, issues

async def main():
    print("\n" + "="*60)
    print("  DISCO BACKEND INTEGRATION TEST")
    print("="*60)
    
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("\n.env file loaded")
    except:
        print("\nNo .env file or dotenv not installed")
    
    all_passed = True
    all_issues = []
    
    # Run tests
    passed, issues = test_domain_imports()
    all_passed = all_passed and passed
    all_issues.extend(issues)
    
    passed, issues = test_graph_build()
    all_passed = all_passed and passed
    all_issues.extend(issues)
    
    passed, issues = test_registry()
    all_passed = all_passed and passed
    all_issues.extend(issues)
    
    passed, issues = check_env_variables()
    all_passed = all_passed and passed
    all_issues.extend(issues)
    
    passed, issues = check_mcp_imports()
    all_passed = all_passed and passed
    all_issues.extend(issues)
    
    passed, issues = await test_full_workflow()
    all_passed = all_passed and passed
    all_issues.extend(issues)
    
    # Summary
    print_header("SUMMARY")
    
    if all_passed:
        print("  ✅ ALL TESTS PASSED")
        print("  The backend is ready for production use.")
    else:
        print("  ❌ SOME TESTS FAILED")
        print("\n  Issues found:")
        for issue in all_issues:
            print(f"    - {issue}")
    
    return all_passed

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
