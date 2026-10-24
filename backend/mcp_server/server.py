"""MCP server entry point using stdio transport.

Protocol messages travel on stdout; diagnostic logs go to stderr. The server
creates a single BackendClient, registers read-only tools plus transfer
preparation and cancellation, and shuts the client down cleanly on exit.

Authorization of transfers is disabled by default and not registered as a tool.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys

from mcp.server import Server
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

from mcp_server.config import ServerSettings, get_settings
from mcp_server.errors import ToolError, ToolValidationError, error_result, text_result
from mcp_server.http_client import BackendClient, BackendError
from mcp_server.tools import handler_for, tools_for_settings

logger = logging.getLogger("hermes_mcp.server")

# MCP protocol version negotiated with the client.
PROTOCOL_VERSION = "2024-11-05"


def _configure_logging() -> None:
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def build_server(settings: ServerSettings) -> tuple[Server, BackendClient]:
    server = Server("hermes-personal-banking")
    client = BackendClient(settings)
    tools = tools_for_settings(settings)

    @server.list_tools()
    async def handle_list_tools() -> ListToolsResult:
        return ListToolsResult(tools=[t for t, _ in tools])

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict | None) -> CallToolResult:
        handler = handler_for(name, settings)
        if handler is None:
            content = error_result(f"Unknown tool: {name}")
            return CallToolResult(content=content, isError=True)
        args = arguments or {}
        try:
            result = await handler(client, settings, args)
            content = text_result(result)
            return CallToolResult(content=content, isError=False)
        except ToolValidationError as exc:
            logger.warning("Validation failed for %s: %s", name, exc.message)
            return CallToolResult(content=error_result(exc.message), isError=True)
        except ToolError as exc:
            logger.warning("Tool error in %s: %s", name, exc.message)
            return CallToolResult(content=error_result(exc.message), isError=True)
        except BackendError as exc:
            logger.warning("Backend error in %s [%s]: %s", name, exc.code, exc.message)
            return CallToolResult(content=error_result(exc.message), isError=True)
        except Exception as exc:
            logger.exception("Unexpected error in tool %s", name)
            return CallToolResult(content=error_result("An unexpected error occurred."), isError=True)

    return server, client


async def run_async() -> None:
    settings = get_settings()
    _configure_logging()
    logger.info("Starting Hermes MCP server (backend=%s)", settings.backend_base_url)
    server, client = build_server(settings)

    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="hermes-personal-banking",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    finally:
        await client.close()
        logger.info("Hermes MCP server stopped.")


def main() -> None:
    try:
        asyncio.run(run_async())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
