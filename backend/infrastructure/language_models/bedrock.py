"""
AWS Bedrock LLM provider with async support, streaming, and tool calling.
Trimmed from Elle's BedrockModel — same invoke_with_fallback + tool loop.
"""
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from infrastructure.language_models.base import BaseLLMModel

from utils.logger import get_logger

logger = get_logger()

DEFAULT_MODEL_ID = (
   "global.anthropic.claude-sonnet-4-6"
)

_RETRYABLE_ERROR_CODES = {
    "ThrottlingException",
    "ModelNotReadyException",
    "ServiceUnavailableException",
    "ModelTimeoutException",
    "InternalServerException",
}


class BedrockModel(BaseLLMModel):

    def __init__(
        self,
        aws_access_key: str,
        aws_secret_key: str,
        model_id: str = DEFAULT_MODEL_ID,
        region_name: str = "us-east-1",
        temperature: float = 0.7,
        max_tokens: int = 8192,
        tool_registry=None,
        **kwargs,
    ):
        super().__init__(
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            tool_registry=tool_registry,
            **kwargs,
        )
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.region_name = region_name
        self.tool_call_count = 0
        self.tool_tokens = 0

        self.boto_config = Config(
            signature_version="v4",
            retries={"max_attempts": 3, "mode": "adaptive"},
            connect_timeout=10,
            read_timeout=180,
        )

        self._sessions: Dict[str, aioboto3.Session] = {
            region_name: aioboto3.Session(
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=region_name,
            )
        }

    def _get_session(self, region: str) -> aioboto3.Session:
        if region not in self._sessions:
            self._sessions[region] = aioboto3.Session(
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=region,
            )
        return self._sessions[region]

    async def _get_client(self, region: Optional[str] = None):
        session = self._get_session(region or self.region_name)
        return session.client("bedrock-runtime", config=self.boto_config)

    def _build_payload(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        enable_tools: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        effective_model_id = model_id or self.model_id
        payload: Dict[str, Any] = {
            "modelId": effective_model_id,
            "messages": messages,
            "inferenceConfig": {
                "temperature": temperature or self.temperature,
                "maxTokens": max_tokens or self.max_tokens,
            },
        }
        if system:
            payload["system"] = [{"text": system}]
        if enable_tools and self.tool_registry:
            tool_config = self.tool_registry.generate_tool_config()
            if tool_config and tool_config.get("tools"):
                payload["toolConfig"] = tool_config
        return payload

    async def invoke(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        stream: bool = True,
        enable_tools: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_id: Optional[str] = None,
        region: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        payload = self._build_payload(
            messages, system, enable_tools, temperature, max_tokens, model_id,
        )
        async with await self._get_client(region=region) as client:
            response = await client.converse(**payload)
            return response

    async def prompt(
        self,
        text: Optional[str] = None,
        system_prompt: str = "",
        system_context: Optional[Dict[str, Any]] = None,
        message_history: Optional[List[Dict[str, Any]]] = None,
        enable_tools: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        self.tool_call_count = 0
        self.tool_tokens = 0

        system = None
        if system_prompt:
            system = self.render_template(
                system_prompt, system_context or {}
            )

        messages = (message_history or []).copy()
        if text:
            messages = self.clean_message_history(messages)
            messages.append({"role": "user", "content": [{"text": text}]})

        if not messages:
            raise ValueError("At least one message is required")

        try:
            response = await self.invoke(
                messages=messages,
                system=system,
                enable_tools=enable_tools,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            initial_tokens = response.get("usage", {}).get("totalTokens", 0)

            if enable_tools and self._has_tool_calls(response):
                response = await self._handle_tool_calls(
                    response=response,
                    messages=messages,
                    system=system,
                    **kwargs,
                )

            response["toolCallCount"] = self.tool_call_count
            response["toolTokens"] = self.tool_tokens
            response["totalTokens"] = initial_tokens + self.tool_tokens
            yield response

        except Exception as e:
            logger.error(f"Error in Bedrock prompt: {e}", exc_info=True)
            raise

    async def _handle_tool_calls(
        self,
        response: Dict[str, Any],
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        max_iterations: int = 15,
        **kwargs,
    ) -> Dict[str, Any]:
        iteration = 0
        current = response

        while self._has_tool_calls(current) and iteration < max_iterations:
            iteration += 1
            logger.info(f"Tool call iteration {iteration}/{max_iterations}")

            messages.append(
                {
                    "role": "assistant",
                    "content": current["output"]["message"]["content"],
                }
            )

            tool_results = []
            for block in current["output"]["message"]["content"]:
                if "toolUse" in block:
                    self.tool_call_count += 1
                    result = await self._execute_tool(block["toolUse"])
                    tool_results.append(result)

            messages.append({"role": "user", "content": tool_results})

            current = await self.invoke(
                messages=messages,
                system=system,
                enable_tools=True,
                **kwargs,
            )

            usage = current.get("usage", {})
            self.tool_tokens += usage.get("totalTokens", 0)

        return current

    def _has_tool_calls(self, response: Dict[str, Any]) -> bool:
        try:
            if response.get("stopReason") == "tool_use":
                return True
            content = (
                response.get("output", {})
                .get("message", {})
                .get("content", [])
            )
            return any("toolUse" in block for block in content)
        except (KeyError, TypeError):
            return False

    async def _execute_tool(self, tool_use: Dict[str, Any]) -> Dict[str, Any]:
        tool_use_id = tool_use["toolUseId"]
        tool_name = tool_use["name"]
        tool_input = tool_use["input"]

        logger.info(f"Executing tool: {tool_name}")
        try:
            if self.tool_registry:
                output = await self.tool_registry.execute_tool(
                    tool_name, tool_input
                )
            else:
                output = {"error": "No tool registry configured"}
            return {
                "toolResult": {
                    "toolUseId": tool_use_id,
                    "content": [{"text": json.dumps(output)}],
                }
            }
        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            return {
                "toolResult": {
                    "toolUseId": tool_use_id,
                    "content": [{"text": json.dumps({"error": str(e)})}],
                    "status": "error",
                }
            }

    def extract_text_response(self, response: Dict[str, Any]) -> str:
        try:
            content = response["output"]["message"]["content"]
            return "\n".join(
                block["text"] for block in content if "text" in block
            )
        except (KeyError, TypeError):
            return ""
