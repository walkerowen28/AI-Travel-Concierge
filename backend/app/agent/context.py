from dataclasses import dataclass, field

from sqlalchemy.orm import Session


@dataclass
class ConciergeContext:
    db: Session
    reservation_id: int | None = None
    tool_traces: list[dict[str, str]] = field(default_factory=list)

    def trace(self, tool: str, detail: str = "") -> None:
        self.tool_traces.append({"tool": tool, "detail": detail})
