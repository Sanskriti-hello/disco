"""
Template Data Injector
Intelligently injects MCP data into React component structure
"""

import re
import json
from typing import Dict, Any, List


class DataInjector:
    """
    Injects domain data into template React components
    Preserves template structure, styling, and features
    """
    
    def inject_data(
        self,
        react_code: str,
        template_id: str,
        data: Dict[str, Any],
        theme_config: Dict[str, Any]
    ) -> str:
        """
        Main injection method - routes to template-specific injectors
        
        Args:
            react_code: Original React component source
            template_id: Which template we're using
            data: Transformed MCP data matching template schema
            theme_config: Tailwind/style config
        
        Returns: Modified React code with data injected
        """
        print(f"💉 Injecting data into template: {template_id}")
        
        # Route to specialized injector
        if template_id == "code-1":
            return self._inject_code_template(react_code, data)
        elif template_id == "generic-1":
            return self._inject_generic_blue(react_code, data)
        elif template_id == "generic-2":
            return self._inject_generic_yellow(react_code, data)
        elif template_id == "shopping-1":
            return self._inject_shopping(react_code, data)
        else:
            print(f"⚠️ No specialized injector for {template_id}, using generic")
            return self._inject_generic_fallback(react_code, data)
    
    def _inject_code_template(self, code: str, data: Dict) -> str:
        """
        Specialized injection for code-1 template (green terminal theme)
        
        Expected data schema:
        {
            "code_snippets": [{language, code, filename, explanation}],
            "documentation": [{title, content, url}],
            "terminal_output": "...",
            "related_repos": [{name, url, stars}]
        }
        """
        # Replace TITLE placeholder
        title = data.get("title", "Code Dashboard")
        code = re.sub(
            r'TITLE',
            title,
            code
        )
        
        # Generate code snippets display
        code_snippets = data.get("code_snippets", [])
        if code_snippets:
            # Create a formatted code display section
            snippet = code_snippets[0]  # Show first snippet
            code_display = f"""
            <div className="font-mono text-sm">
              <div className="text-[#00FF41] mb-2">{snippet.get('filename', 'code.py')}</div>
              <pre className="bg-[#0D1117] p-4 rounded overflow-auto">
                <code className="text-[#00FF41]">{snippet.get('code', '// No code available')[:500]}</code>
              </pre>
            </div>
            """
            
            # Try to inject into Rectangle_65 (main code area)
            code = re.sub(
                r'(id="_1_786__Rectangle_65"[^>]*>)(\s*)(</div>)',
                rf'\1\2{code_display}\2\3',
                code,
                flags=re.DOTALL
            )
        
        # Inject documentation links if available
        documentation = data.get("documentation", [])
        if documentation:
            doc_links = "\n".join([
                f'<a href="{doc.get("url", "#")}" className="text-[#39FF14] hover:underline block">{doc.get("title", "Doc")}</a>'
                for doc in documentation[:5]
            ])
            
            # Inject into sidebar (Rectangle_67)
            code = re.sub(
                r'(id="_1_789__Rectangle_67"[^>]*>)(\s *)(</div>)',
                rf'\1\2<div className="p-4">{doc_links}</div>\2\3',
                code,
                flags=re.DOTALL
            )
        
        return code
    
    def _inject_generic_blue(self, code: str, data: Dict) -> str:
        """
        Specialized injection for generic-1 template (blue link cards)
        
        Expected data schema:
        {
            "links": [{title, url, summary, favicon, domain}],
            "category": "...",
            "total_tabs": 10
        }
        """
        links = data.get("links", [])
        category = data.get("category", "Your Links")
        
        # Replace title
        code = re.sub(r'TITLE', category, code)
        
        # Generate link cards
        if links:
            cards_html = []
            for link in links[:12]:  # Show up to 12 links
                card = f"""
                <div className="bg-[#1E40AF] rounded-lg p-4 hover:bg-[#2563EB] transition-colors">
                  <h3 className="text-white font-semibold mb-2">{link.get('title', 'Untitled')}</h3>
                  <p className="text-[#60A5FA] text-sm mb-2">{link.get('summary', '')[:150]}</p>
                  <a href="{link.get('url', '#')}" className="text-[#3B82F6] text-xs hover:underline">{link.get('domain', link.get('url', ''))}</a>
                </div>
                """
                cards_html.append(card)
            
            cards_section = f"""
            <div className="grid grid-cols-2 gap-4 p-4">
              {''.join(cards_html)}
            </div>
            """
            
            # Try to inject into main content area
            code = re.sub(
                r'(<div[^>]*Frame_23[^>]*>)',
                rf'\1{cards_section}',
                code,
                flags=re.DOTALL,
                count=1
            )
        
        return code
    
    def _inject_generic_yellow(self, code: str, data: Dict) -> str:
        """
        Specialized injection for generic-2 template (yellow search dashboard)
        
        Expected data schema:
        {
            "items": [{title, url, summary, tags, timestamp}],
            "search_enabled": true,
            "categories": [...],
            "total_count": 15
        }
        """
        items = data.get("items", [])
        total_count = data.get("total_count", len(items))
        
        # Replace title with count
        code = re.sub(r'TITLE', f'Search Dashboard ({total_count} items)', code)
        
        # Generate search results
        if items:
            item_cards = []
            for item in items[:20]:  # Up to 20 items
                tags_html = ' '.join([
                    f'<span className="bg-[#FDE68A] text-[#78350F] px-2 py-1 rounded text-xs">{tag}</span>'
                    for tag in item.get('tags', [])[:3]
                ])
                
                card = f"""
                <div className="bg-[#D97706] rounded-lg p-4 mb-4">
                  <h3 className="text-white font-semibold mb-2">{item.get('title', 'Item')}</h3>
                  <p className="text-[#FDE68A] text-sm mb-2">{item.get('summary', '')[:200]}</p>
                  <div className="flex gap-2 mb-2">{tags_html}</div>
                  <a href="{item.get('url', '#')}" className="text-[#FBBF24] text-xs hover:underline">View →</a>
                </div>
                """
                item_cards.append(card)
            
            results_section = f"""
            <div className="p-4">
              <input type="text" placeholder="Search..." className="w-full p-2 rounded bg-[#374151] text-white mb-4" />
              <div className="masonry-grid">
                {''.join(item_cards)}
              </div>
            </div>
            """
            
            code = re.sub(
                r'(<div[^>]*Frame_23[^>]*>)',
                rf'\1{results_section}',
                code,
                flags=re.DOTALL,
                count=1
            )
        
        return code
    
    def _inject_shopping(self, code: str, data: Dict) -> str:
        """
        Specialized injection for shopping-1 template (purple e-commerce grid)
        
        Expected data schema:
        {
            "products": [{title, price, original_price, rating, review_count, url, image_url}],
            "price_range": {min, max},
            "sort_by": "price"
        }
        """
        products = data.get("products", [])
        price_range = data.get("price_range", {})
        
        # Replace title
        code = re.sub(r'TITLE', 'Product Comparison', code)
        
        # Generate product cards
        if products:
            product_cards = []
            for product in products[:12]:  # Up to 12 products
                # Star rating visualization
                rating = product.get('rating', 0)
                stars = '⭐' * int(rating) + '☆' * (5 - int(rating))
                
                # Price display
                price = product.get('price', 'N/A')
                original_price = product.get('original_price', '')
                price_display = f'<span className="text-[#F0ABFC] font-bold text-xl">{price}</span>'
                if original_price and original_price != price:
                    price_display += f' <span className="text-gray-400 line-through text-sm">{original_price}</span>'
                
                card = f"""
                <div className="bg-[#27272A] rounded-lg p-4 hover:shadow-lg transition-shadow">
                  <div className="bg-[#3F3F46] h-32 rounded mb-2 flex items-center justify-center">
                    <span className="text-gray-400">Image</span>
                  </div>
                  <h3 className="text-white font-semibold mb-2 line-clamp-2">{product.get('title', 'Product')}</h3>
                  <div className="text-[#FBBF24] text-sm mb-1">{stars} ({product.get('review_count', 0)})</div>
                  <div className="mb-2">{price_display}</div>
                  <a href="{product.get('url', '#')}" className="bg-[#A855F7] text-white px-4 py-2 rounded hover:bg-[#9333EA] block text-center text-sm">View Deal</a>
                </div>
                """
                product_cards.append(card)
            
            products_section = f"""
            <div className="p-4">
              <div className="grid grid-cols-3 gap-4">
                {''.join(product_cards)}
              </div>
            </div>
            """
            
            code = re.sub(
                r'(<div[^>]*Frame_23[^>]*>)',
                rf'\1{products_section}',
                code,
                flags=re.DOTALL,
                count=1
            )
        
        return code
    
    def _inject_generic_fallback(self, code: str, data: Dict) -> str:
        """
        Fallback injector for unknown templates
        Simply replaces TITLE and injects a data summary
        """
        # Replace title
        title = data.get("title", "Dashboard")
        code = re.sub(r'TITLE', title, code)
        
        # Create simple data summary
        data_summary = f"""
        <div className="p-4 bg-gray-800 text-white">
          <h2>Data Summary</h2>
          <pre>{json.dumps(data, indent=2)[:500]}</pre>
        </div>
        """
        
        # Try to inject somewhere
        code = re.sub(
            r'(<div[^>]*>)',
            rf'\1{data_summary}',
            code,
            count=1
        )
        
        return code


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    injector = DataInjector()
    
    # Test with sample code template
    sample_code = """
    <div id="_1_791__TITLE">TITLE</div>
    <div id="_1_786__Rectangle_65"></div>
    <div id="_1_789__Rectangle_67"></div>
    """
    
    test_data = {
        "title": "Python Debug Helper",
        "code_snippets": [
            {
                "language": "python",
                "code": "def hello():\n    print('world')",
                "filename": "app.py"
            }
        ],
        "documentation": [
            {"title": "Python Docs", "url": "https://docs.python.org"}
        ]
    }
    
    result = injector.inject_data(sample_code, "code-1", test_data, {})
    print("=== INJECTED CODE ===")
    print(result[:500])
