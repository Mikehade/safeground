"""Behavioral unit tests for BaseTool and ToolRegistry.

Tests: Bedrock/OpenAI config generation, tool routing, execution, error handling.
"""
from typing import Any, Dict

import pytest

from app.core.tools.base import BaseTool, ToolRegistry


class DummyTool(BaseTool):
    """Minimal concrete tool for testing."""

    def __init__(self, enabled_tools=None, **kwargs):
        super().__init__(enabled_tools=enabled_tools, **kwargs)

    async def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        method = self.get_tool_method(tool_name)
        if not method:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        result = await method(**{**tool_input, **self.kwargs})
        return result if isinstance(result, dict) else {"success": True, "data": result}

    async def _greet(self, name: str, **kwargs) -> Dict[str, Any]:
        """Say hello to someone."""
        return {"success": True, "greeting": f"Hello {name}"}

    async def _add(self, a: int, b: int, **kwargs) -> Dict[str, Any]:
        """Add two numbers."""
        return {"success": True, "result": a + b}

    async def _failing(self, **kwargs) -> Dict[str, Any]:
        """A tool that always fails."""
        raise RuntimeError("tool crashed")


class TestBaseToolConfigGeneration:

    def test_generates_bedrock_config_for_all_tools(self):
        config = DummyTool.generate_bedrock_config()
        tools = config["tools"]

        names = {t["toolSpec"]["name"] for t in tools}
        assert "greet" in names
        assert "add" in names
        assert "failing" in names

    def test_generates_bedrock_config_with_enabled_filter(self):
        config = DummyTool.generate_bedrock_config(enabled_tools=["greet"])
        tools = config["tools"]

        assert len(tools) == 1
        assert tools[0]["toolSpec"]["name"] == "greet"

    def test_bedrock_spec_includes_required_parameters(self):
        config = DummyTool.generate_bedrock_config(enabled_tools=["greet"])
        spec = config["tools"][0]["toolSpec"]

        assert spec["name"] == "greet"
        assert "name" in spec["inputSchema"]["json"]["properties"]
        assert "name" in spec["inputSchema"]["json"]["required"]

    def test_generates_openai_config(self):
        functions = DummyTool.generate_openai_config()
        names = {f["name"] for f in functions}

        assert "greet" in names
        assert "add" in names

    def test_openai_config_respects_enabled_filter(self):
        functions = DummyTool.generate_openai_config(enabled_tools=["add"])

        assert len(functions) == 1
        assert functions[0]["name"] == "add"
        assert "a" in functions[0]["parameters"]["required"]
        assert "b" in functions[0]["parameters"]["required"]

    def test_extracts_description_from_docstring(self):
        config = DummyTool.generate_bedrock_config(enabled_tools=["greet"])
        desc = config["tools"][0]["toolSpec"]["description"]

        assert desc == "Say hello to someone."


class TestBaseToolExecution:

    @pytest.mark.asyncio
    async def test_executes_tool_by_name(self):
        tool = DummyTool()
        result = await tool.execute("greet", {"name": "Lagos"})

        assert result["success"] is True
        assert result["greeting"] == "Hello Lagos"

    @pytest.mark.asyncio
    async def test_returns_error_for_unknown_tool(self):
        tool = DummyTool()
        result = await tool.execute("nonexistent", {})

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_get_tool_method_returns_method(self):
        tool = DummyTool()
        method = tool.get_tool_method("greet")
        assert method is not None
        assert callable(method)

    def test_get_tool_method_returns_none_for_missing(self):
        tool = DummyTool()
        assert tool.get_tool_method("nonexistent") is None


class TestToolRegistry:

    def test_builds_tool_map_from_classes(self):
        tool = DummyTool(enabled_tools=["greet", "add"])
        registry = ToolRegistry(tool_classes=[tool])

        available = registry.get_available_tools()
        assert "greet" in available
        assert "add" in available

    def test_respects_enabled_tools_filter(self):
        tool = DummyTool(enabled_tools=["greet"])
        registry = ToolRegistry(tool_classes=[tool])

        available = registry.get_available_tools()
        assert "greet" in available
        assert "add" not in available

    def test_generates_merged_bedrock_config(self):
        tool1 = DummyTool(enabled_tools=["greet"])
        tool2 = DummyTool(enabled_tools=["add"])
        registry = ToolRegistry(tool_classes=[tool1, tool2])

        config = registry.generate_tool_config()
        names = {t["toolSpec"]["name"] for t in config["tools"]}
        assert names == {"greet", "add"}

    def test_generates_merged_openai_functions(self):
        tool = DummyTool(enabled_tools=["greet", "add"])
        registry = ToolRegistry(tool_classes=[tool])

        functions = registry.generate_openai_functions()
        names = {f["name"] for f in functions}
        assert names == {"greet", "add"}

    @pytest.mark.asyncio
    async def test_routes_execution_to_correct_tool(self):
        tool = DummyTool(enabled_tools=["greet", "add"])
        registry = ToolRegistry(tool_classes=[tool])

        result = await registry.execute_tool("add", {"a": 3, "b": 7})
        assert result["result"] == 10

    @pytest.mark.asyncio
    async def test_returns_error_for_unregistered_tool(self):
        registry = ToolRegistry(tool_classes=[])

        result = await registry.execute_tool("ghost", {})
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_handles_tool_execution_error(self):
        tool = DummyTool(enabled_tools=["failing"])
        registry = ToolRegistry(tool_classes=[tool])

        result = await registry.execute_tool("failing", {})
        assert result["success"] is False
        assert "tool crashed" in result["error"]

    def test_empty_registry_returns_empty_config(self):
        registry = ToolRegistry(tool_classes=[])
        assert registry.generate_tool_config() == {}
        assert registry.generate_openai_functions() == []
