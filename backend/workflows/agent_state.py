from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    query: str
    intent: str | None
    result: dict[str, Any] | None
    error: str | None
    attempts: int
    route_trace: list[str]