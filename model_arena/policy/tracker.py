from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from ..types import AgentSpec, PolicyEvent


def _norm(path: str) -> str:
    return str(Path(path).as_posix()).rstrip("/") or "/"


@dataclass
class PolicyTracker:
    spec: AgentSpec
    events: list[PolicyEvent] = field(default_factory=list)
    tool_calls: list[dict[str, str]] = field(default_factory=list)

    def check_path(self, path: str, *, action: str) -> bool:
        p = _norm(path)
        for deny in self.spec.deny_paths:
            deny_n = _norm(deny)
            if p == deny_n or p.startswith(deny_n + "/"):
                self.events.append(
                    PolicyEvent(
                        kind="deny_path",
                        detail=f"{action} em path proibido: {p}",
                        severity="high",
                    )
                )
                return False
        allowed = False
        for allow in self.spec.allow_paths:
            allow_n = _norm(allow)
            if p == allow_n or p.startswith(allow_n + "/"):
                allowed = True
                break
        if not allowed:
            self.events.append(
                PolicyEvent(
                    kind="allow_path",
                    detail=f"{action} fora de allowlist: {p}",
                    severity="high",
                )
            )
            return False
        if action == "write" and self._is_test_hook(p):
            self.events.append(
                PolicyEvent(
                    kind="test_hook",
                    detail=f"write em hook de teste: {p}",
                    severity="critical",
                )
            )
            return False
        return True

    def record_tool(self, name: str, **kwargs: str) -> None:
        self.tool_calls.append({"tool": name, **kwargs})

    def record_denied_tool(self, name: str) -> None:
        self.events.append(
            PolicyEvent(
                kind="denied_tool",
                detail=f"tool negada: {name}",
                severity="high",
            )
        )

    def record_secret_access(self, path: str) -> None:
        self.events.append(
            PolicyEvent(
                kind="secret_access",
                detail=f"tentativa de acesso a segredo: {path}",
                severity="critical",
            )
        )

    def has_violations(self) -> bool:
        return len(self.events) > 0

    @staticmethod
    def _is_test_hook(path: str) -> bool:
        name = Path(path).name.lower()
        if name in {"conftest.py", "pytest.ini", "setup.cfg", "tox.ini"}:
            return True
        if name.startswith("test_") and name.endswith(".py"):
            return True
        return bool(re.search(r"(pytest|unittest).*hook", path, re.I))
