from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentSession:
    output: str | None = None
    transcript: list[dict[str, Any]] = field(default_factory=list)
