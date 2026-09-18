"""
Abstract base LLM model.
Concrete implementations: BedrockModel (now), OpenAIModel (later).
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

from jinja2 import Template

from utils.logger import get_logger

logger = get_logger()


class BaseLLMModel(ABC):

    def __init__(
        self,
        model_id: str,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        tool_registry=None,
        **kwargs,
    ):
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tool_registry = tool_registry

    @abstractmethod
    async def invoke(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        stream: bool = True,
        enable_tools: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def prompt(
        self,
        text: Optional[str] = None,
        system_prompt: str = "",
        system_context: Optional[Dict[str, Any]] = None,
        message_history: Optional[List[Dict[str, Any]]] = None,
        enable_tools: bool = False,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        pass

    @staticmethod
    def render_template(
        template_str: str, context: Dict[str, Any]
    ) -> str:
        """Render a Jinja2 template string with context."""
        return Template(template_str).render(**context)

    @staticmethod
    def clean_message_history(
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Remove consecutive same-role messages."""
        if not messages:
            return messages
        cleaned = [messages[0]]
        for msg in messages[1:]:
            if msg["role"] != cleaned[-1]["role"]:
                cleaned.append(msg)
        return cleaned
