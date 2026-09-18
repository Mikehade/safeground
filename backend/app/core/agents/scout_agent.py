"""
Scout agent — safety-aware route intelligence.
The star of the show.
"""
import logging
from typing import Any, AsyncGenerator, Dict

from app.core.agents.base import BaseAgent

from utils.logger import get_logger

logger = get_logger()


class ScoutAgent(BaseAgent):

    def __init__(
        self,
        llm_model,
        tool_registry,
        prompt_template,
        scout_service,
        use_graph: bool = False,
        langgraph_model=None,
        checkpointer=None,
        **kwargs,
    ):
        super().__init__(
            llm_model=llm_model,
            tool_registry=tool_registry,
            prompt_template=prompt_template,
            use_graph=use_graph,
            langgraph_model=langgraph_model,
            checkpointer=checkpointer,
            **kwargs,
        )
        self.scout_service = scout_service

    async def run(
        self, message: str, context: Dict[str, Any], **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if self.use_graph:
            async for resp in self._run_graph_path(message, context, **kwargs):
                yield resp
        else:
            async for resp in self._run_llm_path(message, context, **kwargs):
                yield resp
