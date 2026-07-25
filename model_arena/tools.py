from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentSession:
    output: str | None = None
    transcript: list[dict[str, Any]] = field(default_factory=list)
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
