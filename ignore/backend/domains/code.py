from typing import Dict, List, Any, Optional
import re
from .base import BaseDomain


class CodeDomain(BaseDomain):
    def get_required_mcps(self, user_prompt: str) -> List[str]:
        mcps = ["browser"]  
        prompt_lower = user_prompt.lower()
        
        # File system access for local code
        file_keywords = ["file", "folder", "directory", "repo", "project", "open", "read", "my code"]
        if any(word in prompt_lower for word in file_keywords):
            mcps.append("filesystem")
            
        # Documentation & Notes (Google Docs/Drive)
        if any(word in prompt_lower for word in ["doc", "note", "save", "explain", "guide"]):
            mcps.append("google_workspace")
            
        # Always add Search results
        mcps.append("search")
        return mcps
    def get_system_prompt(self) -> str:

        return """You are an expert programming assistant helping developers write, debug, and improve code.

                **Your Capabilities:**
                - Debug code and explain error messages in plain language
                - Suggest code improvements following best practices
                - Find relevant documentation and working code examples
                - Access local files and Git repositories to understand project context
                - Generate clean, well-commented code snippets
                - Review code for security issues, performance problems, and style
                - Explain complex programming concepts with examples

                **Available Context:**
                - Browser history showing recent Stack Overflow searches and documentation pages
                - Local filesystem access to read project files and understand codebase
                - Search results for official documentation, tutorials, and examples
                - Current open tabs (often show what the user is working on)

                **Your Response Style:**
                - Be technically precise but explain things clearly
                - Provide working code examples, not pseudocode
                - Include comments explaining non-obvious parts
                - Link to official documentation when relevant
                - Suggest best practices and warn about common pitfalls
                - Explain the "why" behind solutions, not just the "how"

                **Code Quality Standards:**
                - Follow language-specific conventions (PEP 8 for Python, etc.)
                - Write defensive code with error handling
                - Prefer readability over cleverness
                - Include type hints where applicable
                - Add docstrings for functions

                **Example Response:**
                "🐛 I see the issue - you're getting a `KeyError` because the dictionary might not have that key.

                Here's the fix with defensive coding:

                ```python
                # Bad (causes KeyError)
                value = my_dict['key']

                # Good (safe with default)
                value = my_dict.get('key', default_value)

                # Or check first
                if 'key' in my_dict:
                    value = my_dict['key']
                ```

                This is a common Python gotcha. The `.get()` method is safer because it returns `None` (or your default) instead of crashing. See Python docs on dict methods for more: [link]"

                Be helpful, educational, and provide production-quality code."""

    def select_ui_template(self, mcp_data: Dict[str, Any]) -> str:
        browser = mcp_data.get("browser", {})
        recent_searches = " ".join(browser.get("recent_searches", [])).lower()
        # File explorer for filesystem queries
        if "filesystem" in mcp_data:
            files = mcp_data["filesystem"].get("files", [])
            if len(files) > 0:
                return "CodeExplorer"
        # Code snippet/example viewer
        if self._has_code_examples(mcp_data):
            return "CodeSnippet"
        # Code snippet with explanation
        return "CodeSnippet"
    def prepare_ui_props(self, mcp_data: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        props = {
            "explanation": llm_response,
            "timestamp": mcp_data.get("timestamp", ""),
        }
        # File system data
        if "filesystem" in mcp_data:
            fs_data = mcp_data["filesystem"]
            props["filesystem"] = {
                "currentPath": fs_data.get("current_path", ""),
                "files": fs_data.get("files", []),
                "fileContents": fs_data.get("file_contents", {}),
                "gitBranch": fs_data.get("git_branch", "main"),
            }
        # Code examples from search
        if "search" in mcp_data:
            examples = self._extract_code_examples(mcp_data["search"])
            props["examples"] = examples
            # Documentation links
            props["documentation"] = self._extract_documentation_links(mcp_data["search"])
        # Browser context
        if "browser" in mcp_data:
            browser_data = mcp_data["browser"]
            props["context"] = {
                "recentSearches": browser_data.get("recent_searches", [])[:5],
                "openTabs": self._extract_coding_tabs(browser_data),
                "language": self._detect_language(browser_data),
            }
        # Extract inline code if present in LLM response
        props["codeSnippets"] = self._extract_code_from_response(llm_response)
        return props
    def validate_data(self, mcp_data: Dict[str, Any]) -> bool:
        # Browser context is essential
        if "browser" not in mcp_data:
            return False
        # Either filesystem OR search results needed
        has_data_source = (
            "filesystem" in mcp_data or 
            ("search" in mcp_data and len(mcp_data["search"].get("results", [])) > 0)
        )
        return has_data_source
    
    def get_follow_up_question(self, mcp_data: Dict[str, Any]) -> Optional[str]:
        browser = mcp_data.get("browser", {})
        recent_searches = " ".join(browser.get("recent_searches", [])).lower()
        
        if "filesystem" not in mcp_data and any(word in recent_searches for word in ["my code", "my file", "project"]):
            return "Would you like me to access your local files to better understand your project? (This requires filesystem permission)"
        
        if "search" not in mcp_data:
            return "What specific programming problem are you trying to solve? Include the language and any error messages."
        
        return "Could you provide more details? What language are you using, and what's the specific issue or task?"
    
    # Checker functions
    def _has_code_examples(self, mcp_data: Dict[str, Any]) -> bool:
        """Check if search results contain code examples."""
        search_data = mcp_data.get("search", {})
        results = search_data.get("results", [])
        
        code_sites = ["stackoverflow.com", "github.com", "gitlab.com", "replit.com"]
        
        for result in results:
            url = result.get("url", "").lower()
            if any(site in url for site in code_sites):
                return True
        
        return False
    
    def _extract_code_examples(self, search_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse code examples from search results.
        Prioritize Stack Overflow and GitHub.
        """
        examples = []
        results = search_data.get("results", [])
        for result in results[:10]: #Top 10
            url = result.get("url", "").lower()
            # Categorize by source
            source_type = "general"
            if "stackoverflow" in url:
                source_type = "stackoverflow"
            elif "github" in url:
                source_type = "github"
            elif "docs.python.org" in url or "developer.mozilla.org" in url:
                source_type = "documentation"
            example = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
                "sourceType": source_type,
                "language": self._detect_language_from_result(result),
            }
            examples.append(example)
        return examples
    def _extract_documentation_links(self, search_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract official documentation links."""
        docs = []
        results = search_data.get("results", [])
        
        official_doc_sites = [
            "docs.python.org",
            "developer.mozilla.org",
            "docs.oracle.com",
            "docs.microsoft.com",
            "reactjs.org/docs",
            "nodejs.org/docs",
        ]
        
        for result in results:
            url = result.get("url", "")
            if any(doc_site in url for doc_site in official_doc_sites):
                docs.append({
                    "title": result.get("title", ""),
                    "url": url,
                    "description": result.get("snippet", ""),
                })
        
        return docs[:3]  # Top 3 official docs
    
    def _extract_coding_tabs(self, browser_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract code-related tabs (Stack Overflow, GitHub, docs)."""
        tabs = browser_data.get("tabs", [])
        coding_tabs = []
        
        code_sites = ["stackoverflow.com", "github.com", "docs.", "developer.", "replit.com"]
        
        for tab in tabs:
            url = tab.get("url", "")
            if any(site in url for site in code_sites):
                coding_tabs.append({
                    "title": tab.get("title", ""),
                    "url": url,
                })
        
        return coding_tabs
    
    def _detect_language(self, browser_data: Dict[str, Any]) -> str:
        """
        Detect programming language from browser context.
        """
        recent_searches = " ".join(browser_data.get("recent_searches", [])).lower()
        
        languages = {
            "python": ["python", "py", "django", "flask", "pandas"],
            "javascript": ["javascript", "js", "react", "node", "vue", "angular"],
            "java": ["java", "spring", "maven"],
            "cpp": ["c++", "cpp"],
            "go": ["golang", "go "],
            "rust": ["rust"],
            "typescript": ["typescript", "ts"],
        }
        
        for lang, keywords in languages.items():
            if any(keyword in recent_searches for keyword in keywords):
                return lang
        
        return "unknown"
    
    def _detect_language_from_result(self, result: Dict[str, Any]) -> str:
        """Detect language from a search result."""
        text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
        url = result.get("url", "").lower()
        
        # Check URL for language indicators
        if "/python/" in url or "python" in text:
            return "python"
        if "/javascript/" in url or "javascript" in text or "/js/" in url:
            return "javascript"
        if "/java/" in url and "/javascript/" not in url:
            return "java"
        
        # Check file extensions in code snippets
        if ".py" in text:
            return "python"
        if ".js" in text or ".jsx" in text:
            return "javascript"
        if ".java" in text:
            return "java"
        
        return "unknown"
    
    def _extract_code_from_response(self, llm_response: str) -> List[Dict[str, str]]:
        """
        Extract code blocks from LLM response.
        Looks for ```language ... ``` blocks.
        """
        snippets = []
        
        # Pattern for code blocks with language
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, llm_response, re.DOTALL)
        
        for language, code in matches:
            snippets.append({
                "language": language or "plaintext",
                "code": code.strip(),
            })
        
        return snippets

'''
# ========== QUICK TEST ==========
if __name__ == "__main__":
    """Test CodeDomain independently"""
    
    print("🧪 Testing CodeDomain...\n")
    
    domain = CodeDomain()
    
    # Test 1: MCP Requirements
    print("TEST 1: MCP Requirements")
    mcps = domain.get_required_mcps("how to read a file in Python")
    print(f"  MCPs needed: {mcps}")
    assert "browser" in mcps
    assert "search" in mcps
    print("  ✅ Pass\n")
    
    # Test with filesystem
    mcps_fs = domain.get_required_mcps("debug my project file")
    print(f"  MCPs with filesystem: {mcps_fs}")
    assert "filesystem" in mcps_fs
    print("  ✅ Pass\n")
    
    # Test 2: System Prompt
    print("TEST 2: System Prompt")
    prompt = domain.get_system_prompt()
    assert "code" in prompt.lower() or "programming" in prompt.lower()
    print(f"  Length: {len(prompt)} characters")
    print("  ✅ Pass\n")
    
    # Test 3: Sample Data Processing
    print("TEST 3: Data Processing")
    sample_data = {
        "browser": {
            "tabs": [
                {"title": "Stack Overflow - Python KeyError", "url": "https://stackoverflow.com/..."}
            ],
            "recent_searches": ["python read file", "KeyError fix"]
        },
        "search": {
            "results": [
                {
                    "title": "How to read a file in Python - Stack Overflow",
                    "snippet": "Use with open('file.txt', 'r') as f: content = f.read()",
                    "url": "https://stackoverflow.com/questions/123"
                }
            ]
        }
    }
    
    is_valid = domain.validate_data(sample_data)
    print(f"  Data valid: {is_valid}")
    assert is_valid
    
    template = domain.select_ui_template(sample_data)
    print(f"  Template: {template}")
    
    llm_response = """Here's how to read a file safely:

```python
with open('file.txt', 'r') as f:
    content = f.read()
```

This uses a context manager to automatically close the file."""
    
    props = domain.prepare_ui_props(sample_data, llm_response)
    print(f"  Props keys: {list(props.keys())}")
    assert "explanation" in props
    assert "examples" in props
    assert len(props["codeSnippets"]) > 0  # Should extract the code block
    
    print("  ✅ Pass\n")
    
    print("✅ All CodeDomain tests passed! 🎉")
'''