"""
Base agent ABC — choosable between llm+tools path and LangGraph path.
Same pattern as Elle's agents.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional

from utils.logger import get_logger

logger = get_logger()


class BaseAgent(ABC):

    def __init__(
        self,
        llm_model,
        tool_registry,
        prompt_template,
        use_graph: bool = False,
        langgraph_model=None,
        checkpointer=None,
        **kwargs,
    ):
        self.llm_model = llm_model
        self.tool_registry = tool_registry
        self.prompt_template = prompt_template
        self.use_graph = use_graph
        self.langgraph_model = langgraph_model
        self.checkpointer = checkpointer

        if use_graph and langgraph_model:
            self._build_graph()

    def _build_graph(self):
        """Build LangGraph StateGraph. Override in subclass."""
        raise NotImplementedError("Subclass must implement _build_graph")

    @abstractmethod
    async def run(
        self, message: str, context: Dict[str, Any], **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        pass

    async def _run_llm_path(
        self, message: str, context: Dict[str, Any], **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Direct llm + tool loop via BedrockModel.prompt()."""
        self.llm_model.tool_registry = self.tool_registry
        system = self.prompt_template.render(context)

        async for response in self.llm_model.prompt(
            text=message,
            system_prompt=system,
            message_history=context.get("history", []),
            enable_tools=True,
        ):
            yield response

    async def _run_graph_path(
        self, message: str, context: Dict[str, Any], **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """LangGraph execution path. Subclass implements with compiled graph."""
        raise NotImplementedError("Graph path not implemented yet")
        yield  # pragma: no cover — makes this a generator
