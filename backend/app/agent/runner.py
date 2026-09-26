from __future__ import annotations

import os

from agents import Agent, Runner
from agents.items import ToolCallItem
from sqlalchemy.orm import Session

from app.agent.context import ConciergeContext
from app.agent.tools import ALL_TOOLS
from app.config import get_settings
from app.errors import ValidationError

SYSTEM_PROMPT = """You are the AI Travel Concierge for a short-term rental demo app.

Rules:
- Never invent properties, prices, reservations, house rules, or nearby places.
- Always use tools for facts and for any booking changes.
- Prefer concise, helpful answers.
- When the user wants to cancel, extend, book, or report an issue, call the matching tool.
- If a reservation_id is available in context, use it when the user says "my stay" or "this reservation".
- Dates must be ISO format YYYY-MM-DD when calling tools.
"""


def build_agent() -> Agent[ConciergeContext]:
    settings = get_settings()
    return Agent[ConciergeContext](
        name="Travel Concierge",
        instructions=SYSTEM_PROMPT,
        tools=ALL_TOOLS,
        model=settings.openai_model,
    )


def _require_api_key() -> None:
    settings = get_settings()
    key = settings.openai_api_key.strip()
    if not key:
        raise ValidationError(
            "OPENAI_API_KEY is not set. Add it to .env and restart the API."
        )
    os.environ["OPENAI_API_KEY"] = key


def _collect_tool_traces(
    context: ConciergeContext,
    result,
) -> list[dict[str, str]]:
    traces = list(context.tool_traces)
    if traces:
        return traces

    for item in result.new_items:
        if isinstance(item, ToolCallItem):
            name = item._resolved_tool_name or getattr(item.raw_item, "name", "tool")
            traces.append({"tool": str(name), "detail": ""})
    return traces


async def run_concierge(
    db: Session,
    *,
    messages: list[dict[str, str]],
    reservation_id: int | None = None,
) -> dict:
    _require_api_key()
    if not messages:
        raise ValidationError("messages must not be empty")

    context = ConciergeContext(db=db, reservation_id=reservation_id)
    agent = build_agent()

    transcript_parts: list[str] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "").strip()
        if not content:
            continue
        label = "User" if role == "user" else "Assistant"
        transcript_parts.append(f"{label}: {content}")
    if reservation_id is not None:
        transcript_parts.insert(
            0,
            f"(Context: the guest is asking about reservation_id={reservation_id}.)",
        )
    prompt = "\n".join(transcript_parts)
    if not prompt.strip():
        raise ValidationError("messages must include content")

    try:
        result = await Runner.run(agent, prompt, context=context, max_turns=8)
    except Exception as exc:
        _raise_openai_error(exc)

    reply = result.final_output
    if not isinstance(reply, str):
        reply = str(reply)

    return {
        "message": reply,
        "tool_traces": _collect_tool_traces(context, result),
    }


def _raise_openai_error(exc: BaseException) -> None:
    """Map OpenAI/SDK failures to ValidationError so the UI gets a clear 422."""
    name = type(exc).__name__
    message = str(exc)
    lowered = message.lower()

    if "credit_balance_exhausted" in lowered or "insufficient_quota" in lowered:
        raise ValidationError(
            "OpenAI account has no credits remaining. Add billing credits at "
            "https://platform.openai.com/settings/organization/billing/"
        ) from exc
    if name in {"AuthenticationError", "PermissionDeniedError"} or "invalid_api_key" in lowered:
        raise ValidationError(
            "OpenAI rejected the API key. Check OPENAI_API_KEY in .env and recreate the API container."
        ) from exc
    if name == "RateLimitError" or "rate limit" in lowered:
        raise ValidationError(
            "OpenAI rate limit hit. Wait a moment and try again."
        ) from exc
    raise ValidationError(f"OpenAI request failed: {message}") from exc
