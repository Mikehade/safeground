"""
Base tool classes and registry for LLM tool calling.
Auto-generates both Bedrock toolSpec and OpenAI function configs
from underscore-prefixed methods via introspection.
"""
import inspect
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, get_type_hints

from utils.logger import get_logger

logger = get_logger()


class BaseTool(ABC):
    """
    Base class for all tools.
    Methods prefixed with _ (single underscore, not dunder) become tools.
    """

    def __init__(
        self,
        enabled_tools: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        self.kwargs = kwargs
        self.enabled_tools = enabled_tools

    @classmethod
    def generate_bedrock_config(
        cls, enabled_tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate Bedrock toolSpec configuration from class methods."""
        tools = []
        methods = inspect.getmembers(cls, predicate=inspect.isfunction)

        for method_name, method in methods:
            if (
                method_name.startswith("_")
                and not method_name.startswith("__")
                and method_name
                not in ("_generate_method_spec", "_generate_openai_function_spec")
            ):
                tool_name = method_name[1:]
                if enabled_tools is None or tool_name in enabled_tools:
                    tool_spec = cls._generate_method_spec(method_name, method)
                    tools.append(tool_spec)

        return {"tools": tools, "toolChoice": {"auto": {}}}

    @classmethod
    def generate_openai_config(
        cls, enabled_tools: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Generate OpenAI functions configuration from class methods."""
        functions = []
        methods = inspect.getmembers(cls, predicate=inspect.isfunction)

        for method_name, method in methods:
            if method_name.startswith("_") and not method_name.startswith("__"):
                tool_name = method_name[1:]
                if enabled_tools is None or tool_name in enabled_tools:
                    func_spec = cls._generate_openai_function_spec(
                        method_name, method
                    )
                    functions.append(func_spec)

        return functions

    @classmethod
    def _generate_method_spec(
        cls, method_name: str, method: Callable
    ) -> Dict[str, Any]:
        """Generate Bedrock toolSpec for a single method."""
        signature = inspect.signature(method)
        parameters = signature.parameters
        type_hints = get_type_hints(method)

        # Extract first line of docstring as description
        doc = method.__doc__.strip().split("\n")[0] if method.__doc__ else ""

        tool_spec: Dict[str, Any] = {
            "toolSpec": {
                "name": method_name[1:],
                "description": doc,
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    }
                },
            }
        }

        type_mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        for param_name, param in parameters.items():
            if param_name in ("self", "kwargs"):
                continue

            param_type = type_hints.get(param_name, str)
            param_type_str = type_mapping.get(param_type, "string")

            tool_spec["toolSpec"]["inputSchema"]["json"]["properties"][
                param_name
            ] = {
                "type": param_type_str,
                "description": f"The {param_name.replace('_', ' ')}",
            }

            if param.default == inspect.Parameter.empty:
                tool_spec["toolSpec"]["inputSchema"]["json"]["required"].append(
                    param_name
                )

        return tool_spec

    @classmethod
    def _generate_openai_function_spec(
        cls, method_name: str, method: Callable
    ) -> Dict[str, Any]:
        """Generate OpenAI function spec for a single method."""
        signature = inspect.signature(method)
        parameters = signature.parameters
        type_hints = get_type_hints(method)

        doc = method.__doc__.strip().split("\n")[0] if method.__doc__ else ""

        func_spec: Dict[str, Any] = {
            "name": method_name[1:],
            "description": doc,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }

        type_mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        for param_name, param in parameters.items():
            if param_name in ("self", "kwargs"):
                continue

            param_type = type_hints.get(param_name, str)
            param_type_str = type_mapping.get(param_type, "string")

            func_spec["parameters"]["properties"][param_name] = {
                "type": param_type_str,
                "description": f"The {param_name.replace('_', ' ')}",
            }

            if param.default == inspect.Parameter.empty:
                func_spec["parameters"]["required"].append(param_name)

        return func_spec

    def get_tool_method(self, tool_name: str) -> Optional[Callable]:
        return getattr(self, f"_{tool_name}", None)

    @abstractmethod
    async def execute(
        self, tool_name: str, tool_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass


class ToolRegistry:
    """
    Registry combining multiple tool classes.
    Generates merged config and routes execution.
    """

    def __init__(
        self, tool_classes: Optional[List[BaseTool]] = None
    ) -> None:
        self.tool_classes = tool_classes or []
        self._tool_map: Dict[str, BaseTool] = {}
        self._build_tool_map()

    def _build_tool_map(self) -> None:
        for tool_class in self.tool_classes:
            methods = inspect.getmembers(tool_class, predicate=inspect.ismethod)
            for method_name, _ in methods:
                if method_name.startswith("_") and not method_name.startswith(
                    "__"
                ):
                    tool_name = method_name[1:]
                    if (
                        tool_class.enabled_tools is None
                        or tool_name in tool_class.enabled_tools
                    ):
                        self._tool_map[tool_name] = tool_class

        logger.info(
            f"Tool registry: {len(self._tool_map)} tools: "
            f"{list(self._tool_map.keys())}"
        )

    def generate_tool_config(self) -> Dict[str, Any]:
        """Generate merged Bedrock tool configuration."""
        if not self.tool_classes:
            return {}

        all_tools = []
        for tool_class in self.tool_classes:
            config = tool_class.__class__.generate_bedrock_config(
                enabled_tools=tool_class.enabled_tools
            )
            all_tools.extend(config.get("tools", []))

        return {"tools": all_tools, "toolChoice": {"auto": {}}}

    def generate_openai_functions(self) -> List[Dict[str, Any]]:
        """Generate merged OpenAI functions configuration."""
        if not self.tool_classes:
            return []

        all_functions = []
        for tool_class in self.tool_classes:
            functions = tool_class.__class__.generate_openai_config(
                enabled_tools=tool_class.enabled_tools
            )
            all_functions.extend(functions)
        return all_functions

    async def execute_tool(
        self, tool_name: str, tool_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        tool_class = self._tool_map.get(tool_name)
        if not tool_class:
            logger.error(f"Tool not found: {tool_name}")
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found in registry",
            }
        try:
            return await tool_class.execute(tool_name, tool_input)
        except Exception as e:
            logger.error(f"Error executing '{tool_name}': {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def get_available_tools(self) -> List[str]:
        return list(self._tool_map.keys())
