"""
ArXiv MCP Client
=================
A reusable module for searching academic research papers on ArXiv via RapidAPI.

Functions:
    - search_papers: Search for research papers by term
    - search_by_author: Search papers by author name
    - search_by_category: Search papers by ArXiv category

Usage:
    from backend.mcp.arxiv import ArxivClient
    
    client = ArxivClient(api_key="your_api_key")
    results = client.search_papers("machine learning", num_results=10)
"""

import os
import http.client
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from urllib.parse import quote


class DateType(Enum):
    """Date type options for filtering papers."""
    SUBMISSION_DATE = "Submission Date"
    LAST_UPDATED = "Last Updated"


class SearchField(Enum):
    """Search field options."""
    ALL = "All fields"
    TITLE = "Title"
    ABSTRACT = "Abstract"
    AUTHOR = "Author"
    COMMENTS = "Comments"
    JOURNAL_REF = "Journal Reference"
    SUBJECT_CLASS = "Subject Class"
    REPORT_NUM = "Report Number"


@dataclass
class ArxivConfig:
    """Configuration for ArXiv API client."""
    api_key: str
    host: str = "arxiv-research-paper-search.p.rapidapi.com"


class ArxivClient:
    """
    Client for the ArXiv Research Paper Search API.
    
    This client provides methods to search for academic papers on ArXiv.
    
    Example:
        client = ArxivClient(api_key="your_rapidapi_key")
        papers = client.search_papers("transformer neural networks")
        for paper in papers.get("results", []):
            print(paper["title"])
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[ArxivConfig] = None):
        """
        Initialize the ArXiv API client.
        
        Args:
            api_key: RapidAPI key. If not provided, reads from RAPIDAPI_KEY env variable.
            config: Optional ArxivConfig object for advanced configuration.
        """
        if config:
            self.config = config
        else:
            key = api_key or os.getenv("RAPIDAPI_KEY")
            if not key:
                raise ValueError(
                    "API key is required. Provide it via api_key parameter "
                    "or set the RAPIDAPI_KEY environment variable."
                )
            self.config = ArxivConfig(api_key=key)
        
        self._headers = {
            "x-rapidapi-key": self.config.api_key,
            "x-rapidapi-host": self.config.host
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an HTTP GET request to the ArXiv API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters as a dictionary
            
        Returns:
            JSON response as a dictionary
        """
        conn = http.client.HTTPSConnection(self.config.host)
        
        # Build query string
        query_string = ""
        if params:
            query_parts = []
            for key, value in params.items():
                if value is not None:
                    # Handle enum values
                    if isinstance(value, Enum):
                        value = value.value
                    # URL encode the value
                    encoded_value = quote(str(value), safe='')
                    query_parts.append(f"{key}={encoded_value}")
            query_string = "?" + "&".join(query_parts)
        
        url = f"{endpoint}{query_string}"
        
        try:
            conn.request("GET", url, headers=self._headers)
            response = conn.getresponse()
            data = response.read().decode("utf-8")
            
            if response.status != 200:
                return {
                    "status": "error",
                    "error_code": response.status,
                    "message": data
                }
            
            return json.loads(data)
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid JSON response: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Request failed: {str(e)}"}
        finally:
            conn.close()
    
    def search_papers(
        self,
        search_term: str,
        start: int = 0,
        num_results: int = 10,
        date_type: DateType = DateType.SUBMISSION_DATE,
        field: SearchField = SearchField.ALL
    ) -> Dict[str, Any]:
        """
        Search for research papers on ArXiv.
        
        Args:
            search_term: The search query (e.g., "machine learning", "LLM")
            start: Starting index for pagination (default: 0)
            num_results: Number of results to return (default: 10, max: 50)
            date_type: Filter by submission date or last updated
            field: Which field to search in (title, abstract, author, etc.)
            
        Returns:
            Dictionary containing search results with papers list
            
        Example:
            results = client.search_papers("transformer", num_results=5)
            for paper in results.get("results", []):
                print(f"Title: {paper['title']}")
                print(f"Authors: {paper['authors']}")
                print(f"Abstract: {paper['abstract'][:200]}...")
        """
        params = {
            "search_term": search_term,
            "start": start,
            "num_results": min(num_results, 50),  # API max is 50
            "date_type": date_type,
            "field": field
        }
        return self._make_request("/arxiv_search", params)
    
    def search_by_author(
        self,
        author_name: str,
        start: int = 0,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search for papers by a specific author.
        
        Args:
            author_name: Name of the author to search for
            start: Starting index for pagination
            num_results: Number of results to return
            
        Returns:
            Dictionary containing papers by the author
            
        Example:
            papers = client.search_by_author("Yann LeCun")
        """
        return self.search_papers(
            search_term=author_name,
            start=start,
            num_results=num_results,
            field=SearchField.AUTHOR
        )
    
    def search_by_title(
        self,
        title: str,
        start: int = 0,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search for papers by title.
        
        Args:
            title: Title or keywords to search for
            start: Starting index for pagination
            num_results: Number of results to return
            
        Returns:
            Dictionary containing matching papers
            
        Example:
            papers = client.search_by_title("attention is all you need")
        """
        return self.search_papers(
            search_term=title,
            start=start,
            num_results=num_results,
            field=SearchField.TITLE
        )
    
    def search_recent(
        self,
        search_term: str,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search for recent papers (sorted by last updated).
        
        Args:
            search_term: The search query
            num_results: Number of results to return
            
        Returns:
            Dictionary containing recent papers matching the query
            
        Example:
            recent = client.search_recent("GPT-4", num_results=5)
        """
        return self.search_papers(
            search_term=search_term,
            num_results=num_results,
            date_type=DateType.LAST_UPDATED
        )


# ============================================================================
# Convenience Functions (for direct import without instantiating client)
# ============================================================================

_default_client: Optional[ArxivClient] = None


def _get_client(api_key: Optional[str] = None) -> ArxivClient:
    """Get or create a default client instance."""
    global _default_client
    if _default_client is None:
        _default_client = ArxivClient(api_key=api_key)
    return _default_client


def search_papers(
    search_term: str,
    num_results: int = 10,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for research papers on ArXiv.
    
    This is a convenience function that uses a default client instance.
    For more control, use the ArxivClient class directly.
    
    Example:
        from backend.mcp.arxiv import search_papers
        results = search_papers("deep learning", num_results=5)
    """
    return _get_client(api_key).search_papers(search_term, num_results=num_results)


def search_by_author(
    author_name: str,
    num_results: int = 10,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for papers by author name.
    
    This is a convenience function that uses a default client instance.
    """
    return _get_client(api_key).search_by_author(author_name, num_results=num_results)


def search_by_title(
    title: str,
    num_results: int = 10,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for papers by title.
    
    This is a convenience function that uses a default client instance.
    """
    return _get_client(api_key).search_by_title(title, num_results=num_results)


def search_recent(
    search_term: str,
    num_results: int = 10,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for recent papers.
    
    This is a convenience function that uses a default client instance.
    """
    return _get_client(api_key).search_recent(search_term, num_results=num_results)


# ============================================================================
# Example usage (only runs when executed directly)
# ============================================================================

if __name__ == "__main__":
    api_key = os.getenv("RAPIDAPI_KEY")
    
    if api_key:
        client = ArxivClient(api_key=api_key)
        
        # Search for papers
        print("Searching for 'LLM' papers...")
        results = client.search_papers("llm", num_results=5)
        print(json.dumps(results, indent=2)[:1000])
        
        # Search by author
        print("\nSearching for papers by 'Hinton'...")
        author_papers = client.search_by_author("Hinton", num_results=3)
        print(json.dumps(author_papers, indent=2)[:500])
    else:
        print("Please set RAPIDAPI_KEY environment variable to test.")
        print("\nAvailable functions:")
        print("  - ArxivClient(api_key).search_papers(search_term)")
        print("  - ArxivClient(api_key).search_by_author(author_name)")
        print("  - ArxivClient(api_key).search_by_title(title)")
        print("  - ArxivClient(api_key).search_recent(search_term)")