from __future__ import annotations

import json
from typing import Any


def sse_event(event_type: str, data: dict[str, Any]) -> str:
    """Format a Server-Sent Event message with double-newline terminator."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def status_event(message: str) -> str:
    return sse_event("status", {"message": message})


def token_event(token: str) -> str:
    return sse_event("token", {"token": token})


def sources_event(sources: list[dict[str, Any]]) -> str:
    return sse_event("sources", {"sources": sources})


def done_event(session_id: str, message_id: str) -> str:
    return sse_event("done", {"session_id": session_id, "message_id": message_id})


def error_event(message: str) -> str:
    return sse_event("error", {"message": message})

