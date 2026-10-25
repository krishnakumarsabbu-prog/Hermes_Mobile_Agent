"""Async client for the local Hermes Agent Gateway.

The Gateway exposes an OpenAI-compatible chat completions endpoint at
``/v1/chat/completions``. Hermes resolves its registered MCP skills/tools
itself; when it returns ``tool_calls`` we execute them locally against the
real backend tool registry so the response is grounded in actual database
results, then feed the tool output back to Hermes and continue the
conversation.

Tool execution is delegated to a caller-supplied coroutine factory so the
assistant service can share its request session (avoiding nested-write
deadlocks on SQLite) while keeping this client transport-only. When no
executor is supplied the bridge opens its own scoped session.

This client never exposes stack traces, environment values, or raw tool
output to callers. It returns a normalized ``HermesResult`` or raises
``HermesError`` with a safe, user-facing message.

Networking note: ``gateway_base_url`` points at the loopback address of the
machine running Hermes. FastAPI calls it from that same machine; the mobile
app never reaches the Gateway directly.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger("hermes.client")


class HermesError(Exception):
    """Raised when the Hermes Gateway cannot produce a usable response.

    ``message`` is safe to surface to the user; technical detail stays in the
    log line keyed by ``request_id``.
    """

    def __init__(self, message: str, *, code: str = "HERMES_UNAVAILABLE"):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class HermesResult:
    content: str
    tool_calls_made: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


# A tool executor runs a Hermes tool call against the real backend. It is
# injected by the caller so session lifecycle stays with the request.
ToolExecutor = Callable[[dict[str, Any], str], Awaitable[dict[str, Any]]]


def _chat_payload(
    *,
    model: str,
    messages: list[dict[str, Any]],
    conversation_id: str,
    request_id: str,
) -> dict[str, Any]:
    """Build the OpenAI-compatible chat completion request body."""
    return {
        "model": model,
        "messages": messages,
        "stream": False,
        "metadata": {"conversationId": conversation_id, "requestId": request_id},
    }


def _extract_choice(payload: dict[str, Any]) -> dict[str, Any]:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise HermesError("The assistant returned an empty response.", code="HERMES_EMPTY")
    choice = choices[0]
    if not isinstance(choice, dict) or "message" not in choice:
        raise HermesError("The assistant returned an unexpected response.", code="HERMES_BAD_SHAPE")
    return choice


def _message_content(message: dict[str, Any]) -> str:
    content = message.get("content")
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                parts.append(str(part.get("text") or ""))
            elif isinstance(part, str):
                parts.append(part)
        return "".join(parts)
    return str(content)


def _tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    calls = message.get("tool_calls")
    if not isinstance(calls, list):
        return []
    return [c for c in calls if isinstance(c, dict)]


async def chat(
    *,
    messages: list[dict[str, Any]],
    conversation_id: str,
    request_id: str,
    user_id: str,
    tool_executor: Optional[ToolExecutor] = None,
) -> HermesResult:
    """Send a multi-turn chat request to Hermes and resolve tool calls.

    ``messages`` is the full conversation history (system/user/assistant/tool
    roles). The function iterates up to ``gateway_max_iterations`` times so
    Hermes can call tools and incorporate their results before producing a
    final answer. ``tool_executor`` runs each tool call; when omitted the
    bridge's own scoped session is used.
    """
    settings = get_settings()
    if not settings.gateway_enabled:
        raise HermesError("The Hermes assistant is not enabled.", code="HERMES_DISABLED")

    base = settings.gateway_base_url.rstrip("/")
    url = f"{base}/v1/chat/completions"
    timeout = httpx.Timeout(settings.gateway_timeout_seconds, connect=5.0)
    tool_calls_made: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=timeout) as client:
        for _ in range(max(1, settings.gateway_max_iterations)):
            try:
                resp = await client.post(
                    url,
                    json=_chat_payload(
                        model=settings.gateway_model,
                        messages=messages,
                        conversation_id=conversation_id,
                        request_id=request_id,
                    ),
                )
            except httpx.ConnectError:
                logger.warning('{"event":"hermes.connect_failed","requestId":"%s"}', request_id)
                raise HermesError(
                    "The assistant is unavailable right now. Please try again in a moment.",
                    code="HERMES_UNREACHABLE",
                )
            except httpx.TimeoutException:
                logger.warning('{"event":"hermes.timeout","requestId":"%s"}', request_id)
                raise HermesError(
                    "The assistant took too long to respond. Please try again.",
                    code="HERMES_TIMEOUT",
                )
            except httpx.HTTPError as exc:
                logger.warning(
                    '{"event":"hermes.http_error","requestId":"%s","error":"%s"}',
                    request_id,
                    type(exc).__name__,
                )
                raise HermesError(
                    "The assistant could not be reached. Please try again later.",
                    code="HERMES_UNREACHABLE",
                )

            if resp.status_code >= 500:
                logger.warning(
                    '{"event":"hermes.5xx","requestId":"%s","status":%d}',
                    request_id,
                    resp.status_code,
                )
                raise HermesError(
                    "The assistant service is temporarily unavailable.",
                    code="HERMES_UNAVAILABLE",
                )
            if resp.status_code == 404:
                raise HermesError(
                    "The assistant endpoint was not found. Check the Gateway configuration.",
                    code="HERMES_NOT_FOUND",
                )
            if resp.status_code >= 400:
                logger.warning(
                    '{"event":"hermes.4xx","requestId":"%s","status":%d}',
                    request_id,
                    resp.status_code,
                )
                raise HermesError(
                    "The assistant rejected the request. Please rephrase and try again.",
                    code="HERMES_BAD_REQUEST",
                )

            try:
                payload = resp.json()
            except ValueError:
                raise HermesError(
                    "The assistant returned an unreadable response.",
                    code="HERMES_BAD_SHAPE",
                )

            choice = _extract_choice(payload)
            message = choice.get("message") or {}
            content = _message_content(message)
            calls = _tool_calls(message)

            if not calls:
                return HermesResult(content=content, tool_calls_made=tool_calls_made, raw=payload)

            messages.append({"role": "assistant", "content": content, "tool_calls": calls})
            for call in calls:
                resolved = await _resolve_tool_call(
                    call,
                    user_id=user_id,
                    request_id=request_id,
                    tool_executor=tool_executor,
                )
                tool_calls_made.append(resolved["summary"])
                messages.append(resolved["tool_message"])

        logger.warning('{"event":"hermes.max_iterations","requestId":"%s"}', request_id)
        raise HermesError(
            "The assistant could not finish reasoning in time. Please try again.",
            code="HERMES_MAX_ITERATIONS",
        )


async def _resolve_tool_call(
    call: dict[str, Any],
    *,
    user_id: str,
    request_id: str,
    tool_executor: Optional[ToolExecutor] = None,
) -> dict[str, Any]:
    """Execute one Hermes tool call and build the ``tool`` message to return.

    The tool output returned to Hermes is the structured JSON from the backend
    tool. We never fabricate results. Tool errors go back to the model as a
    ``tool`` message with the error text so it can recover gracefully.
    """
    tool_name = str(call.get("function", {}).get("name") or call.get("name") or "")
    raw_args = call.get("function", {}).get("arguments")
    call_id = str(call.get("id") or "")
    try:
        args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
    except (TypeError, ValueError):
        args = {}

    status = "ok"
    content: str
    try:
        if tool_executor is not None:
            result = await tool_executor({"name": tool_name, "args": args}, call_id)
        else:
            from app.services.tool_bridge import execute_tool_for_hermes

            result = execute_tool_for_hermes(
                tool_name=tool_name, args=args, user_id=user_id, request_id=request_id
            )
        content = json.dumps(result, default=str)
    except Exception as exc:  # noqa: BLE001 - tool errors go back to the model
        status = "error"
        content = json.dumps({"error": str(exc) or exc.__class__.__name__})

    return {
        "summary": {"tool": tool_name, "status": status, "callId": call_id},
        "tool_message": {
            "role": "tool",
            "tool_call_id": call_id,
            "name": tool_name,
            "content": content,
        },
    }


def system_prompt(*, user_id: str) -> str:
    """System instructions that anchor Hermes to the real banking tools."""
    return (
        "You are Fargo, a personal banking assistant for a simulated Indian "
        f"rupee account (user {user_id}). Use the registered personal-banking "
        "MCP tools whenever the user asks about balances, transactions, "
        "spending, beneficiaries, or transfers. Never invent account numbers, "
        "balances, transaction ids, beneficiary ids, or approval ids; always "
        "obtain them from tool results. Money is represented in integer paise "
        "(1 INR = 100 paise).\n\n"
        "Transfer rules: prepare_transfer only creates a pending approval and "
        "never debits the account. Never tell a user a transfer was executed, "
        "sent, or completed unless get_transfer_status returns COMPLETED. "
        "Before preparing a transfer you must validate the beneficiary and "
        "amount, summarise the transfer, and require explicit user "
        "confirmation. Treat a vague 'okay' as confirmation only when the "
        "exact beneficiary, amount, and currency were already shown.\n\n"
        "If a tool returns no records, say so plainly. Keep replies concise."
    )
