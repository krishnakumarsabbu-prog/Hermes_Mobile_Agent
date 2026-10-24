"""Tool-facing error types and MCP content assembly.

Tool errors are returned to the model as MCP error content, never raised as
uncaught exceptions. This keeps protocol messages on stdout and diagnostics on
stderr.
"""
from __future__ import annotations

import json
from typing import Any

from mcp.types import TextContent


class ToolValidationError(Exception):
    """Client-side input validation failure for a tool call."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ToolError(Exception):
    """A tool-level failure mapped from a backend or runtime error."""

    def __init__(self, message: str, *, code: str = "TOOL_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


def text_result(payload: Any) -> list[TextContent]:
    """Wrap a JSON-serializable payload as successful MCP text content."""
    return [TextContent(type="text", text=json.dumps(payload, default=str, ensure_ascii=False))]


def error_result(message: str) -> list[TextContent]:
    """Wrap an error message as MCP error-flagged text content."""
    return [TextContent(type="text", text=json.dumps({"error": message}, ensure_ascii=False))]
