"""
Entertainment App Sandbox Builder with LLM-Driven JSON Content Filling

This module provides tools for:
  1. Building CodeSandbox-compatible React projects from directory structures
  2. Intelligently filling JSON templates using LLM (LangChain + Groq)
  3. Falling back to deterministic web search when LLM is unavailable
  4. Validating JSON output against schemas
  5. Protecting against prompt injection attacks

Key Features:
  - Two-layer context system (page-level and field-level guidance)
  - Tool whitelisting and security validation
  - Schema-driven JSON validation
  - Comprehensive logging for debugging
  - Deterministic fallback filling
  - Full caching and performance optimization

Usage:
  - Direct function: update_json(content, page_context, field_context)
  - Builder class: EntertainmentAppSandboxBuilder(context, project_dir)
"""

# ============================================================================
# STANDARD LIBRARY IMPORTS
# ============================================================================

import os
import json
import sys
import logging
import inspect
import importlib.util
from pathlib import Path
from typing import Dict, Optional, Any, List, Callable
from datetime import datetime
import hashlib

# ============================================================================
# THIRD-PARTY IMPORTS
# ============================================================================

from mcp_tools.search import SearchClient


# ============================================================================
# LOGGING SETUP
# ============================================================================


def _init_logger(debug: bool = False) -> logging.Logger:
    """
    Initialize logger with optional debug output.

    Args:
        debug: If True, enables DEBUG level logging to stderr.

    Returns:
        Configured logger instance. Ensures handlers are created only once.
    """
    logger = logging.getLogger(__name__)
    if debug and not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    elif not logger.handlers:
        logger.setLevel(logging.WARNING)
    return logger


# Read DEBUG_JSON_AGENT environment variable to enable/disable debug logging
_debug_mode = os.getenv('DEBUG_JSON_AGENT', '').lower() in ('1', 'true', 'yes')
_logger = _init_logger(_debug_mode)

# ============================================================================
# JSON SCHEMA VALIDATION
# ============================================================================


class JsonSchema:
    """
    Derives and validates JSON schemas.

    This class provides utilities to:
      - Dynamically generate JSON schema from template objects
      - Validate instances against their schemas
      - Detect structural mismatches and type violations
    """

    @staticmethod
    def derive(template: Any) -> Dict[str, Any]:
        """
        Derive a JSON schema from a template object.

        Recursively inspects the template structure and builds a JSON schema
        that enforces the same structure and types. Prevents infinite recursion
        by capping nesting depth at 10 levels.

        Args:
            template: Any JSON-serializable object (dict, list, str, int, etc.)

        Returns:
            Dictionary representing a JSON schema for the given template.
        """

        def build_schema(obj: Any, depth: int = 0) -> Dict[str, Any]:
            # Prevent infinite recursion on circular structures
            if depth > 10:
                return {"type": "object"}

            if isinstance(obj, dict):
                props = {}
                for key, value in obj.items():
                    props[key] = build_schema(value, depth + 1)
                return {
                    "type": "object",
                    "properties": props,
                    "additionalProperties": False,
                }
            elif isinstance(obj, list):
                if len(obj) > 0:
                    return {
                        "type": "array",
                        "items": build_schema(obj[0], depth + 1),
                    }
                else:
                    return {"type": "array"}
            elif isinstance(obj, str):
                return {"type": "string"}
            elif isinstance(obj, bool):
                return {"type": "boolean"}
            elif isinstance(obj, (int, float)):
                return {"type": "number"}
            elif obj is None:
                return {"type": "null"}
            else:
                return {"type": "object"}

        return build_schema(template)

    @staticmethod
    def validate(
        instance: Any, schema: Dict[str, Any], path: str = "root"
    ) -> List[str]:
        """
        Validate an instance against a schema.

        Recursively validates the instance structure and types. Collects all
        errors found rather than failing fast.

        Args:
            instance: Object to validate.
            schema: JSON schema to validate against.
            path: Current path in the object tree (for error messages).

        Returns:
            List of error messages. Empty list if validation succeeds.
        """
        errors: List[str] = []
        schema_type = schema.get("type")

        if schema_type == "object":
            if not isinstance(instance, dict):
                errors.append(
                    f"{path}: expected object, got {type(instance).__name__}"
                )
            else:
                # Check for unexpected keys (not in schema)
                allowed_keys = set(schema.get("properties", {}).keys())
                actual_keys = set(instance.keys())
                extra = actual_keys - allowed_keys
                if extra and not schema.get("additionalProperties", False):
                    errors.append(f"{path}: unexpected keys {extra}")

                # Validate each property in the schema
                for key, prop_schema in schema.get("properties", {}).items():
                    if key in instance:
                        errors.extend(
                            JsonSchema.validate(
                                instance[key], prop_schema, f"{path}.{key}"
                            )
                        )

        elif schema_type == "array":
            if not isinstance(instance, list):
                errors.append(
                    f"{path}: expected array, got {type(instance).__name__}"
                )
            else:
                item_schema = schema.get("items", {})
                for index, item in enumerate(instance):
                    errors.extend(
                        JsonSchema.validate(item, item_schema, f"{path}[{index}]")
                    )

        elif schema_type == "string":
            if not isinstance(instance, str):
                errors.append(
                    f"{path}: expected string, got {type(instance).__name__}"
                )

        elif schema_type == "number":
            # Booleans are technically numbers in Python, so we exclude them
            if not isinstance(instance, (int, float)) or isinstance(instance, bool):
                errors.append(
                    f"{path}: expected number, got {type(instance).__name__}"
                )

        elif schema_type == "boolean":
            if not isinstance(instance, bool):
                errors.append(
                    f"{path}: expected boolean, got {type(instance).__name__}"
                )

        elif schema_type == "null":
            if instance is not None:
                errors.append(
                    f"{path}: expected null, got {type(instance).__name__}"
                )

        return errors

# ============================================================================
# TOOL SECURITY AND WHITELISTING
# ============================================================================


class ToolWhitelist:
    """
    Manages a whitelist of allowed tools for security.

    Restricts which MCP tools can be invoked by the LLM agent.
    Default whitelist includes only SearchClient.web_search.
    """

    # Default set of whitelisted tools in format "ClassName.method_name"
    _DEFAULT_WHITELIST = {
        "SearchClient.web_search": "Search the web for information",
    }

    def __init__(self, whitelist_path: Optional[Path] = None) -> None:
        """
        Initialize the whitelist.

        Starts with default whitelist. If whitelist_path is provided and exists,
        loads custom whitelist from JSON file and merges with defaults.

        Args:
            whitelist_path: Optional path to JSON file containing custom whitelist.
        """
        self.whitelist = dict(self._DEFAULT_WHITELIST)
        self.custom_whitelist = False

        if whitelist_path and whitelist_path.exists():
            try:
                with open(whitelist_path) as f:
                    custom = json.load(f)
                    if isinstance(custom, dict):
                        self.whitelist.update(custom)
                        self.custom_whitelist = True
                        _logger.debug(f"Loaded custom whitelist from {whitelist_path}")
            except Exception as e:
                _logger.warning(
                    f"Failed to load whitelist from {whitelist_path}: {e}"
                )

    def is_allowed(self, class_name: str, method_name: str) -> bool:
        """
        Check if a method is whitelisted.

        Args:
            class_name: Name of the class containing the method.
            method_name: Name of the method to check.

        Returns:
            True if the method is in the whitelist, False otherwise.
        """
        key = f"{class_name}.{method_name}"
        return key in self.whitelist

    def get_description(self, class_name: str, method_name: str) -> str:
        """
        Get the description of a whitelisted method.

        Args:
            class_name: Name of the class.
            method_name: Name of the method.

        Returns:
            Description string, or empty string if not found.
        """
        key = f"{class_name}.{method_name}"
        return self.whitelist.get(key, "")

# ============================================================================
# PROMPT INJECTION PROTECTION
# ============================================================================


class PromptSanitizer:
    """
    Sanitizes user contexts to prevent prompt injection attacks.

    Removes/normalizes potentially dangerous patterns and enforces size limits.
    """

    # Regex patterns for dangerous content (informational, not used yet)
    DANGEROUS_PATTERNS = [
        r"ignore.*rules",
        r"override.*instruction",
        r"system.*prompt",
        r"jailbreak",
    ]

    @staticmethod
    def sanitize(text: Optional[str]) -> str:
        """
        Sanitize context text to prevent prompt injection.

        Removes excessive newlines, truncates to max length, and normalizes
        whitespace to prevent injection attacks.

        Args:
            text: Raw context text to sanitize.

        Returns:
            Cleaned context string, or empty string if input was None.
        """
        if not text:
            return ""

        # Remove excessive newlines and normalize whitespace
        text = "\n".join(
            line.strip() for line in text.split("\n") if line.strip()
        )

        # Enforce maximum context length
        max_length = 2000
        if len(text) > max_length:
            text = text[:max_length] + "..."
            _logger.warning(f"Context truncated to {max_length} chars")

        return text

# ============================================================================
# DETERMINISTIC FALLBACK FILLER
# ============================================================================


class DeterministicFiller:
    """
    Deterministic JSON filler using web search when available.

    Provides conservative, non-hallucinating fallback filling when LLM
    is unavailable. Uses web search to populate empty/placeholder values.
    """

    def __init__(self, search_agent: Optional[SearchClient] = None) -> None:
        """
        Initialize the filler.

        Args:
            search_agent: SearchClient instance for web search, or None.
        """
        self.search_agent = search_agent
        # Cache search results to avoid repeated API calls
        self._search_cache: Dict[str, Any] = {}

    def fill(self, template: Any, page_context: Optional[str] = None) -> Any:
        """
        Fill template with deterministic fallback logic.

        Recursively fills empty/placeholder values using web search on
        page context. Never hallucinate values.

        Args:
            template: JSON template to fill.
            page_context: Global context for search queries.

        Returns:
            Template with filled values.
        """
        return self._fill_recursive(template, page_context or "", [])

    def _fill_recursive(
        self, node: Any, context: str, path: List[str]
    ) -> Any:
        """
        Recursively fill template values.

        Args:
            node: Current node in the template tree.
            context: Global context for search.
            path: Path to current node (for field name inference).

        Returns:
            Filled node matching original type.
        """
        # Handle string values: fill if empty/placeholder
        if isinstance(node, str):
            if self._is_empty_value(node):
                field_name = path[-1] if path else ""
                return self._find_value_for_field(field_name, context)
            return node

        # Handle None: attempt to find a value, otherwise keep None
        if node is None:
            if context:
                field_name = path[-1] if path else ""
                return self._find_value_for_field(field_name, context)
            return None

        # Handle dicts: recursively fill each value
        if isinstance(node, dict):
            result = {}
            for key, value in node.items():
                result[key] = self._fill_recursive(value, context, path + [key])
            return result

        # Handle lists: recursively fill each item
        if isinstance(node, list):
            if len(node) == 0:
                return node
            return [
                self._fill_recursive(item, context, path + ["[]"])
                for item in node
            ]

        # Return scalars unchanged
        return node

    def _is_empty_value(self, text: str) -> bool:
        """
        Check if a string value is empty or a placeholder.

        Args:
            text: String to check.

        Returns:
            True if empty or placeholder-like, False otherwise.
        """
        check = text.strip().lower()
        return check in (
            "",
            "tbd",
            "placeholder",
            "n/a",
            "text",
            "title",
            "untitled",
            "none",
        )

    def _find_value_for_field(self, field_name: str, context: str) -> str:
        """
        Find an appropriate value for a field using web search.

        Uses caching to avoid repeated searches. Returns empty string
        if search fails or search_agent is unavailable.

        Args:
            field_name: Name of the field being filled (for search context).
            context: Global context for the search query.

        Returns:
            Filled value, or empty string if unable to find.
        """
        if not self.search_agent or not context:
            return ""

        # Check cache first
        cache_key = hashlib.md5(f"{field_name}:{context}".encode()).hexdigest()
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]

        try:
            search_results = self.search_agent.web_search(context)
            value = self._extract_best_match(search_results, field_name)
            self._search_cache[cache_key] = value
            return value
        except Exception as error:
            _logger.debug(f"Search failed for field '{field_name}': {error}")
            return ""

    def _extract_best_match(
        self, search_results: Any, field_hint: str
    ) -> str:
        """
        Extract the best matching value from search results.

        Recursively walks the search result structure looking for
        content in common fields (title, name, heading, etc.).

        Args:
            search_results: Raw search result structure.
            field_hint: Name of field being filled (currently unused).

        Returns:
            Best matching string value, or empty string if none found.
        """

        def walk(obj: Any) -> Optional[str]:
            """Recursively search for content in result structure."""
            if isinstance(obj, list):
                for element in obj:
                    result = walk(element)
                    if result:
                        return result
            elif isinstance(obj, dict):
                # Check common content fields first
                for key in ("title", "name", "heading", "description", "body"):
                    if (
                        key in obj
                        and isinstance(obj[key], str)
                        and len(obj[key]) > 2
                    ):
                        return obj[key]
                # Recursively search nested values
                for value in obj.values():
                    result = walk(value)
                    if result:
                        return result
            return None

        result = walk(search_results)
        return result if result else ""

# ============================================================================
# LAZY SEARCH AGENT INITIALIZATION AND HELPER UTILITIES
# ============================================================================


def _get_search_agent() -> Optional[SearchClient]:
    """
    Lazily initialize and return a SearchClient instance.

    Avoids import-time failures by initializing on first use.
    Returns None if initialization fails.

    Returns:
        SearchClient instance, or None if unavailable.
    """
    try:
        return SearchClient()
    except Exception as error:
        _logger.debug(f"Failed to initialize SearchClient: {error}")
        return None


def _extract_json_from_output(text: str) -> str:
    """
    Extract JSON from LLM output that may contain explanatory text.

    Searches for the first '{' and uses that as the start of JSON.

    Args:
        text: Raw LLM output.

    Returns:
        JSON substring, or original text if no '{' found.
    """
    index = text.find("{")
    if index != -1:
        return text[index:]
    return text


# ============================================================================
# MAIN PUBLIC FUNCTION: JSON FILLING WITH LLM FALLBACK
# ============================================================================


def update_json(
    content: str,
    page_context: Optional[str] = None,
    field_context: Optional[str] = None,
) -> str:
    """
    LLM-driven JSON filling agent using LangChain + Groq with two-layer context support.

    Fills empty values and placeholders in JSON templates using an LLM agent.
    Falls back to deterministic web search if LLM is unavailable.

    Args:
        content: JSON template as string.
        page_context: Global page-level context describing the overall JSON/webpage.
        field_context: Field-level context with instructions for each JSON field.

    Behavior:
        - Attempts to auto-discover tools under `mcp_tools/`.
        - Uses LangChain ChatGroq as LLM (configured via GROQ_API_KEY, GROQ_MODEL env vars).
        - Preserves template structure exactly; only updates existing values.
        - Falls back to conservative search-based filler if LLM unavailable.
        - Returns pretty-printed JSON string, or original input on error.

    Returns:
        Filled JSON as string, with same structure as input template.
    """
    try:
        template = json.loads(content)
    except Exception:
        return content

    tools_path = Path(__file__).resolve().parent.parent / "mcp_tools"

    # Try importing LangChain/Groq pieces; if unavailable we will fall back.
    try:
        from langchain.tools import Tool
        from langchain.agents import initialize_agent, AgentType
        from langchain.chat_models import ChatGroq
    except Exception:
        Tool = None
        initialize_agent = None
        AgentType = None
        ChatGroq = None

    # ========================================================================
    # INTERNAL HELPER: Merge LLM output with template
    # ========================================================================

    def safe_merge(template_obj: Any, candidate_obj: Any) -> Any:
        """
        Safely merge LLM output with template, preserving structure exactly.

        This merge function ensures:
          - No new keys are added beyond what's in the template
          - No keys are removed from the template
          - Data types (dict/list/scalar) are preserved
          - Empty/placeholder values are replaced; filled values are kept

        Args:
            template_obj: Original template (source of truth for structure).
            candidate_obj: LLM output to merge values from.

        Returns:
            Merged object with template structure and LLM values.
        """
        # Both are dicts: merge recursively, key by key
        if isinstance(template_obj, dict) and isinstance(candidate_obj, dict):
            result = {}
            for key, template_value in template_obj.items():
                if key in candidate_obj:
                    result[key] = safe_merge(template_value, candidate_obj[key])
                else:
                    result[key] = template_value
            return result

        # Both are lists: merge element-wise, preserving template schema
        if isinstance(template_obj, list) and isinstance(candidate_obj, list):
            if len(template_obj) > 0:
                # Template has schema (prototype); merge each candidate element
                proto = template_obj[0]
                merged_list = []
                for candidate_item in candidate_obj:
                    if isinstance(proto, dict) and isinstance(candidate_item, dict):
                        merged_list.append(safe_merge(proto, candidate_item))
                    elif (
                        not isinstance(proto, dict)
                        and not isinstance(candidate_item, dict)
                    ):
                        # Both are scalars; accept candidate
                        merged_list.append(candidate_item)
                return merged_list
            else:
                # Template list is empty; only accept scalar lists
                if all(not isinstance(x, dict) for x in candidate_obj):
                    return candidate_obj
                return template_obj

        # Template is a string: replace only if it was empty/placeholder
        if isinstance(template_obj, str):
            is_empty_or_placeholder = (
                template_obj.strip() == ""
                or template_obj.strip().lower()
                in ("tbd", "placeholder", "n/a", "text", "title")
            )
            if is_empty_or_placeholder:
                return candidate_obj if isinstance(candidate_obj, str) else template_obj
            return template_obj

        # Template is None: replace with candidate if available
        if template_obj is None:
            return candidate_obj if candidate_obj is not None else template_obj

        return template_obj

    # ========================================================================
    # INTERNAL CLASS: LLM-based JSON filling agent
    # ========================================================================

    class JsonFillingAgent:
        """
        Intelligent JSON filling agent using LangChain + Groq LLM.

        Discovers available MCP tools, initializes an LLM agent with those tools,
        and uses it to fill empty template values based on context.
        """

        def __init__(
            self,
            tools_dir: Path,
            groq_key: Optional[str],
            model_name: Optional[str],
        ) -> None:
            """
            Initialize the JSON filling agent.

            Args:
                tools_dir: Path to mcp_tools directory for tool discovery.
                groq_key: Groq API key (or None to read from env).
                model_name: Groq model name (or None to read from env).
            """
            self.tools_dir = tools_dir
            self.groq_key = groq_key
            self.model_name = model_name or os.getenv("GROQ_MODEL")
            self.tools: List[Any] = []
            self.agent_executor: Optional[Any] = None
            self._discover_tools()
            self._init_agent()

        def _discover_tools(self) -> None:
            """
            Auto-discover tools by scanning mcp_tools directory.

            For each .py file, imports it, finds public classes, and extracts
            their public methods as LangChain tools. Skips errors gracefully.
            """
            if Tool is None:
                return
            if not self.tools_dir.exists():
                return

            for py_file in sorted(self.tools_dir.glob("*.py")):
                try:
                    # Load the module dynamically
                    module_name = f"mcp_tools.{py_file.stem}"
                    spec = importlib.util.spec_from_file_location(
                        module_name, str(py_file)
                    )
                    if not spec or not spec.loader:
                        continue

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)  # type: ignore

                    # Find all classes defined in this module
                    for class_name, class_obj in inspect.getmembers(
                        module, inspect.isclass
                    ):
                        # Only include classes defined in this module
                        if class_obj.__module__ != module.__name__:
                            continue

                        # For each public method, create a LangChain tool wrapper
                        for method_name, method in inspect.getmembers(
                            class_obj, predicate=inspect.isfunction
                        ):
                            # Skip private methods
                            if method_name.startswith("_"):
                                continue

                            # Create a callable that instantiates the class and calls the method
                            def make_tool_callable(cls: type, method_to_call: str):
                                """Closure to capture class and method name."""

                                def call(argument: str):
                                    """
                                    Call the method with the given argument.

                                    Instantiates the class, inspects the method
                                    signature, and calls it with appropriate args.
                                    """
                                    try:
                                        instance = cls()
                                        fn = getattr(instance, method_to_call)
                                        sig = inspect.signature(fn)
                                        positional_params = [
                                            p
                                            for p in sig.parameters.values()
                                            if p.kind
                                            in (
                                                p.POSITIONAL_ONLY,
                                                p.POSITIONAL_OR_KEYWORD,
                                            )
                                        ]

                                        if len(positional_params) == 0:
                                            return fn()
                                        else:
                                            # Pass argument to the method
                                            return fn(argument)
                                    except Exception as error:
                                        return f"Tool error: {error}"

                                return call

                            try:
                                tool_callable = make_tool_callable(class_obj, method_name)
                                doc_string = (
                                    getattr(class_obj, method_name).__doc__ or ""
                                ).strip()
                                tool = Tool(
                                    name=f"{class_name}.{method_name}",
                                    func=tool_callable,
                                    description=doc_string,
                                )
                                self.tools.append(tool)
                            except Exception:
                                # Skip tools that can't be wrapped
                                continue
                except Exception:
                    # Skip modules that can't be loaded
                    continue

        def _init_agent(self) -> None:
            """
            Initialize the LLM agent with discovered tools.

            Creates a ChatGroq LLM and initializes a LangChain agent if:
              - LangChain imports are available
              - At least one tool was discovered
              - Groq API key is available

            Otherwise leaves agent_executor as None (triggers fallback).
            """
            if ChatGroq is None or initialize_agent is None or not self.tools:
                return

            try:
                api_key = self.groq_key or os.getenv("GROQ_API_KEY")
                if not api_key:
                    return

                # Initialize Groq LLM (handle different version signatures)
                if self.model_name:
                    llm = ChatGroq(api_key=api_key, model=self.model_name)
                else:
                    llm = ChatGroq(api_key=api_key)

                # Initialize agent with ZERO_SHOT_REACT_DESCRIPTION
                self.agent_executor = initialize_agent(
                    self.tools,
                    llm,
                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=False,
                )
                _logger.debug(
                    f"LLM agent initialized with {len(self.tools)} tools"
                )
            except Exception as error:
                _logger.debug(f"Failed to initialize LLM agent: {error}")
                self.agent_executor = None

        def fill(
            self,
            template_obj: Any,
            page_ctx: Optional[str],
            field_ctx: Optional[str],
        ) -> Any:
            """
            Fill template using LLM agent.

            Constructs a system prompt with both context layers, invokes the agent,
            and parses the JSON response.

            Args:
                template_obj: Template object to fill.
                page_ctx: Global page-level context.
                field_ctx: Field-level context.

            Returns:
                Filled template object (parsed from LLM JSON output).

            Raises:
                RuntimeError: If agent is not initialized.
                json.JSONDecodeError: If LLM output is not valid JSON.
            """
            if not self.agent_executor:
                raise RuntimeError("agent not initialized")

            # Build system prompt with both context layers
            system_prompt = (
                "You are a JSON completion assistant.\n\n"
                "RULES:\n"
                "- Do NOT add or remove any keys from the JSON.\n"
                "- Preserve the structure and types (dict/list/scalar) exactly.\n"
                "- Only replace empty strings, null values, or placeholder values.\n"
                "- For arrays, maintain the same element schema.\n"
                "- If you cannot determine a value, leave it unchanged.\n"
                "- Return ONLY valid JSON that matches the original template structure.\n"
            )

            # Add page context if provided
            if page_ctx:
                system_prompt += f"\nGLOBAL PAGE CONTEXT:\n{page_ctx}\n"

            # Add field context if provided
            if field_ctx:
                system_prompt += f"\nFIELD-SPECIFIC CONTEXT:\n{field_ctx}\n"

            # Build user prompt with template
            user_prompt = (
                f"Template:\n{json.dumps(template_obj, ensure_ascii=False, indent=2)}\n\n"
                "Fill the template by replacing only empty/placeholder values with appropriate data from the context. "
                "Return ONLY the filled JSON, with no additional text."
            )

            # Run agent
            agent_output = self.agent_executor.run(
                f"{system_prompt}\n{user_prompt}"
            )

            # Extract JSON from agent output
            json_text = _extract_json_from_output(agent_output)
            return json.loads(json_text)

    # ========================================================================
    # TRY LLM-BASED APPROACH FIRST
    # ========================================================================

    try:
        groq_api_key = os.getenv("GROQ_API_KEY")
        groq_model = os.getenv("GROQ_MODEL")
        agent = JsonFillingAgent(tools_path, groq_api_key, groq_model)

        # Only proceed if agent initialized successfully
        if agent.agent_executor:
            try:
                filled_output = agent.fill(template, page_context, field_context)
                merged_output = safe_merge(template, filled_output)
                return json.dumps(merged_output, ensure_ascii=False, indent=2)
            except Exception as error:
                _logger.debug(f"LLM filling failed, falling back: {error}")
                # Fall through to fallback filler below
    except Exception as error:
        _logger.debug(f"LLM agent creation failed, using fallback: {error}")
        # Fall through to fallback filler below

    # ========================================================================
    # FALLBACK: DETERMINISTIC FILLER USING WEB SEARCH
    # ========================================================================

    try:
        search_agent = _get_search_agent()

        def simple_fill(node: Any, path: List[str] = []) -> Any:
            """
            Simple deterministic fill using web search (fallback).

            Fills empty/placeholder string and None values by searching
            for page context. Does not hallucinate.

            Args:
                node: Current node to fill.
                path: Path to current node (for tracking).

            Returns:
                Node with filled values.
            """
            # Handle string values
            if isinstance(node, str):
                is_empty_or_placeholder = node.strip().lower() in (
                    "",
                    "tbd",
                    "placeholder",
                    "n/a",
                    "text",
                    "title",
                )
                if is_empty_or_placeholder and search_agent and page_context:
                    try:
                        search_results = search_agent.web_search(page_context)

                        def search_walk(obj: Any) -> Optional[str]:
                            """Recursively find first text value in search results."""
                            if isinstance(obj, list):
                                for element in obj:
                                    result = search_walk(element)
                                    if result:
                                        return result
                            elif isinstance(obj, dict):
                                for key in ("title", "name", "heading"):
                                    if (
                                        key in obj
                                        and isinstance(obj[key], str)
                                    ):
                                        return obj[key]
                                for value in obj.values():
                                    result = search_walk(value)
                                    if result:
                                        return result
                            return None

                        result = search_walk(search_results)
                        if result:
                            return result
                    except Exception as error:
                        _logger.debug(
                            f"Fallback search failed: {error}"
                        )
                return node

            # Handle None values
            if node is None:
                if search_agent and page_context:
                    try:
                        search_results = search_agent.web_search(page_context)

                        def search_walk(obj: Any) -> Optional[str]:
                            """Recursively find first text value in search results."""
                            if isinstance(obj, list):
                                for element in obj:
                                    result = search_walk(element)
                                    if result:
                                        return result
                            elif isinstance(obj, dict):
                                for key in ("title", "name", "heading"):
                                    if (
                                        key in obj
                                        and isinstance(obj[key], str)
                                    ):
                                        return obj[key]
                                for value in obj.values():
                                    result = search_walk(value)
                                    if result:
                                        return result
                            return None

                        result = search_walk(search_results)
                        if result:
                            return result
                    except Exception as error:
                        _logger.debug(
                            f"Fallback search failed for None: {error}"
                        )
                return None

            # Handle dicts: recursively fill each value
            if isinstance(node, dict):
                for key, value in list(node.items()):
                    node[key] = simple_fill(value, path + [key])
                return node

            # Handle lists: recursively fill each item
            if isinstance(node, list):
                if len(node) == 0:
                    return node
                return [simple_fill(item, path + ["[]"]) for item in node]

            # Return scalars unchanged
            return node

        filled_fallback = simple_fill(template, [])
        return json.dumps(filled_fallback, ensure_ascii=False, indent=2)

    except Exception as error:
        _logger.debug(f"Fallback filler failed: {error}")
        # Return original content if everything fails
        return content

# ============================================================================
# SANDBOX BUILDER
# ============================================================================


class EntertainmentAppSandboxBuilder:
    """
    Builds React CodeSandbox projects from existing directory structures.

    Walks the project directory tree, collects all files, optionally processes
    JSON files through the LLM-driven content filling system, and exports in
    CodeSandbox format.

    Attributes:
        project_dir: Root directory of the project to build.
        context: Page-level context for JSON filling.
    """

    # Files and directories to skip during collection
    _SKIP_DIRS = {
        ".git",
        "node_modules",
        "dist",
        "__pycache__",
        ".vscode",
        ".next",
    }
    _SKIP_EXTS = {".pyc", ".DS_Store", ".pyo"}
    _SKIP_FILES = {"sandbox_builder.py"}

    def __init__(
        self, context: str, project_dir: Optional[Path] = None
    ) -> None:
        """
        Initialize the sandbox builder.

        Args:
            context: Page-level context for JSON content filling.
            project_dir: Root project directory. Defaults to script's directory.
        """
        self.project_dir = project_dir or Path(__file__).parent
        self.context = context

    def build_sandbox(self) -> Dict[str, Dict[str, str]]:
        """
        Build sandbox by collecting all project files.

        Walks the project directory tree, reads files, processes JSON files
        through the content filling system, and returns in CodeSandbox format.

        Returns:
            Dictionary mapping file paths to file content dicts.
            Format: {"/path/to/file": {"content": "file contents"}}
        """
        files: Dict[str, Dict[str, str]] = {}
        files = self._collect_all_files(files, self.project_dir)
        return files

    # ========================================================================
    # FILE COLLECTION
    # ========================================================================

    def _collect_all_files(
        self,
        files: Dict[str, Dict[str, str]],
        root_path: Path,
    ) -> Dict[str, Dict[str, str]]:
        """
        Recursively walk directory tree and collect all readable files.

        Skips binary files and specified directories/extensions.
        Processes JSON files through the content filling system.

        Args:
            files: Accumulator dict to add files to.
            root_path: Current directory to walk.

        Returns:
            Updated files dict with all collected files.
        """
        for root, dirs, filenames in os.walk(root_path):
            # Filter directories to skip system and build directories
            dirs[:] = [d for d in dirs if d not in self._SKIP_DIRS]

            for filename in filenames:
                # Skip specific files and extensions
                if (
                    filename in self._SKIP_FILES
                    or Path(filename).suffix in self._SKIP_EXTS
                ):
                    continue

                file_path = Path(root) / filename
                relative_path = file_path.relative_to(root_path)
                str_path = str(relative_path).replace("\\", "/")

                try:
                    # Read file content
                    content = file_path.read_text(encoding="utf-8")

                    # Process JSON files through content filling system
                    if filename.endswith(".json"):
                        content = self._fill_json_content(content)

                    files[str_path] = {"content": content}

                except UnicodeDecodeError:
                    # Skip binary files (CodeSandbox cannot handle them)
                    _logger.debug(
                        f"Skipped binary file: {file_path}"
                    )
                except Exception as error:
                    print(f"Warning: Could not read {file_path}: {error}")

        return files

    def _fill_json_content(self, content: str) -> str:
        """
        Fill JSON content using the module-level update_json function.

        Args:
            content: Raw JSON string to fill.

        Returns:
            Filled JSON string, or original content on error.
        """
        try:
            return update_json(content, self.context, None)
        except Exception as error:
            _logger.debug(f"Failed to fill JSON content: {error}")
            return content

    # ========================================================================
    # EXPORT METHODS
    # ========================================================================

    def export_to_json(self, output_path: Path) -> None:
        """
        Export sandbox files to JSON format.

        Writes the collected files dict to a JSON file in CodeSandbox format.

        Args:
            output_path: Path to write the JSON export to.
        """
        sandbox_data = self.build_sandbox()
        output_path.write_text(json.dumps(sandbox_data, indent=2))
        print(f"Exported {len(sandbox_data)} files to {output_path}")

    def export_to_codesandbox_format(self) -> Dict[str, Dict[str, str]]:
        """
        Return files in CodeSandbox API format.

        Returns:
            Dictionary of files ready for CodeSandbox API.
        """
        return self.build_sandbox()

    def get_file_summary(self) -> Dict[str, int]:
        """
        Get a summary of file types in the project.

        Counts files by extension.

        Returns:
            Dict mapping file extensions to occurrence counts.
            Unknown extensions mapped to "no_ext".
        """
        files = self.build_sandbox()
        summary: Dict[str, int] = {}

        for filepath in files.keys():
            ext = Path(filepath).suffix or "no_ext"
            summary[ext] = summary.get(ext, 0) + 1

        return summary


# ============================================================================
# CLI ENTRY POINT
# ============================================================================


if __name__ == "__main__":
    """
    Command-line interface for the sandbox builder.

    Usage:
        python entertainment_builder.py [project_dir] [--export] [output_file]

    Arguments:
        project_dir: Root directory of the React project (defaults to script dir).
        --export: Export sandbox to JSON file (optional).
        output_file: Path to write JSON export to (defaults to sandbox_export.json).

    Example:
        python entertainment_builder.py /path/to/project --export output.json
    """

    # Parse project directory from command line or use current directory
    project_path = (
        Path(__file__).parent
        if len(sys.argv) < 2
        else Path(sys.argv[1])
    )

    # Initialize builder with empty context (no JSON filling for CLI usage)
    builder = EntertainmentAppSandboxBuilder(
        context="Entertainment App",
        project_dir=project_path,
    )

    # Build sandbox by collecting all files
    sandbox_files = builder.build_sandbox()

    # Print summary
    print(f"\n✅ Entertainment App Sandbox Builder")
    print(f"📁 Project directory: {project_path}")
    print(f"📦 Total files collected: {len(sandbox_files)}\n")

    # Show file summary by extension
    summary = builder.get_file_summary()
    print("📊 File types:")
    for ext, count in sorted(summary.items(), key=lambda x: x[1], reverse=True):
        print(f"   {ext}: {count} file(s)")

    # List all collected files
    print("\n📄 Files in sandbox:")
    for filepath in sorted(sandbox_files.keys()):
        print(f"   - {filepath}")

    # Optional: Export to JSON if --export flag is present
    if len(sys.argv) > 2 and sys.argv[2] == "--export":
        export_file = Path(
            sys.argv[3] if len(sys.argv) > 3 else "sandbox_export.json"
        )
        builder.export_to_json(export_file)
