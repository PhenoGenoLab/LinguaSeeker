"""Generic MCP client for external tool servers.

Callers describe one server in ``Settings.mcp``; this module owns connection
setup (streamable HTTP, SSE, or stdio), tool invocation, and result decoding.
Tool results are expected to be JSON objects: either ``structuredContent`` or a
JSON text content block.
"""

from __future__ import annotations

import asyncio
import json
import shlex
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from loguru import logger
from mcp import Client
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters

from src.core.config import McpServerConfig


class McpToolError(RuntimeError):
    """An MCP connection or tool-call failure."""


class McpToolClient:
    """Call one configured MCP tool and return its decoded JSON object."""

    def __init__(self, config: McpServerConfig, *, name: str = "mcp"):
        self._config = config
        self._name = name

    async def call(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invoke the configured tool and decode its JSON result."""
        config = self._config
        if not config.enabled:
            raise McpToolError(f"{self._name} MCP server is not enabled")
        if not config.tool:
            raise McpToolError(f"{self._name} MCP tool name is not configured")

        async with self._connect() as client:
            try:
                result = await asyncio.wait_for(
                    client.call_tool(config.tool, arguments),
                    timeout=config.timeout,
                )
            except asyncio.TimeoutError as exc:
                raise McpToolError(f"{self._name} MCP tool '{config.tool}' timed out") from exc

        if getattr(result, "is_error", False):
            raise McpToolError(f"{self._name} MCP tool '{config.tool}' returned an error: {_text(result)}")

        payload = getattr(result, "structured_content", None)
        if payload is None:
            payload = getattr(result, "structuredContent", None)
        if payload is not None:
            return dict(payload)

        text = _text(result)
        if not text:
            raise McpToolError(f"{self._name} MCP tool '{config.tool}' returned no content")
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise McpToolError(f"{self._name} MCP tool '{config.tool}' did not return JSON") from exc
        if not isinstance(decoded, dict):
            raise McpToolError(f"{self._name} MCP tool '{config.tool}' returned a non-object JSON payload")
        return decoded

    @asynccontextmanager
    async def _connect(self) -> AsyncIterator[Client]:
        config = self._config
        transport = config.transport.strip().lower()
        logger.debug("Connecting to {} MCP server via {}", self._name, transport)

        if transport == "stdio":
            if not config.command.strip():
                raise McpToolError(f"{self._name} MCP stdio transport requires a command")
            parts = shlex.split(config.command)
            if not parts:
                raise McpToolError(f"{self._name} MCP stdio command is empty")
            params = StdioServerParameters(command=parts[0], args=parts[1:])
            async with Client(server=params, read_timeout_seconds=config.timeout) as client:
                yield client
            return

        if not config.url.strip():
            raise McpToolError(f"{self._name} MCP {transport} transport requires a url")

        if transport == "sse":
            async with sse_client(config.url) as (read_stream, write_stream):
                async with Client(
                    read_stream,
                    write_stream,
                    read_timeout_seconds=config.timeout,
                ) as client:
                    yield client
            return

        if transport == "streamable_http":
            async with Client(server=config.url, read_timeout_seconds=config.timeout) as client:
                yield client
            return

        raise McpToolError(f"{self._name} MCP transport is unsupported: {config.transport}")


def _text(result: Any) -> str:
    """Join text content blocks from a tool result."""
    blocks = getattr(result, "content", None) or []
    parts = [getattr(block, "text", "") for block in blocks]
    return "\n".join(part for part in parts if part)
