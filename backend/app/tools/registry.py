"""Assistant tool registry.

Tools are the only way the assistant touches the database, so responses are
grounded in real query results rather than invented numbers. The registry is
designed so a future Hermes runtime can swap implementations behind the same
interface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from sqlalchemy.orm import Session


@dataclass
class ToolContext:
    session: Session
    user_id: str
    request_id: str = ""
    intent_id: str = ""


ToolFn = Callable[[ToolContext, Dict[str, Any]], Dict[str, Any]]


_REGISTRY: Dict[str, "Tool"] = {}


@dataclass
class Tool:
    name: str
    description: str
    fn: ToolFn


def register(name: str, description: str) -> Callable[[ToolFn], ToolFn]:
    def decorator(fn: ToolFn) -> ToolFn:
        _REGISTRY[name] = Tool(name=name, description=description, fn=fn)
        return fn

    return decorator


def get_tool(name: str) -> Tool | None:
    return _REGISTRY.get(name)


def run_tool(name: str, ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    tool = _REGISTRY.get(name)
    if tool is None:
        raise ValueError(f"Unknown tool: {name}")
    return tool.fn(ctx, args)
