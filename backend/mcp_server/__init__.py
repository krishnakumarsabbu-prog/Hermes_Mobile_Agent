"""Hermes MCP server.

A standalone Model Context Protocol server that exposes the Hermes Personal
Banking simulation backend's financial tools to an MCP client (Hermes Agent).

The server runs as a separate process and communicates with the existing
FastAPI backend over authenticated HTTP. It does NOT import backend internals,
duplicate business logic, or bypass authentication. Authorization of transfers
is intentionally disabled by default.
"""
from __future__ import annotations

__version__ = "1.0.0"
