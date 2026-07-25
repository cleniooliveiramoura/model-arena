from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from harness_core.tools.base import Tool, ToolRegistry

from .grading.pristine import run_command
from .policy.tracker import PolicyTracker
from .types import ArenaSpec


def _harness_project_tools():
    from harness_core.project.tools import ProjectBoundary, ReadFileTool, WriteFileTool

    return ProjectBoundary, ReadFileTool, WriteFileTool


class PolicyAwareTool(Tool):
    """Envolve uma tool do harness com checagem de policy da arena."""

    def __init__(
        self,
        inner: Tool,
        *,
        policy: PolicyTracker,
        action: str,
    ) -> None:
        self._inner = inner
        self._policy = policy
        self._action = action

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def description(self) -> str:
        return self._inner.description

    def schema(self) -> dict:
        return self._inner.schema()

    def execute(self, **kwargs: Any) -> Any:
        rel = str(kwargs.get("path", "."))
        full = f"/workspace/{rel.lstrip('/')}"
        if not self._policy.check_path(full, action=self._action):
            raise PermissionError(f"policy bloqueou {self._action} em {full}")
        self._policy.record_tool(self.name, path=full)
        return self._inner.execute(**kwargs)


class RunSmokeTool(Tool):
    """Smoke test local no workspace — não executa a suíte de grade."""

    name = "run_smoke"
    description = (
        "Executa um snippet Python rápido no workspace para validar a correção. "
        "Não substitui os testes oficiais da arena."
    )

    def __init__(self, workspace: Path, policy: PolicyTracker) -> None:
        self._workspace = workspace
        self._policy = policy

    def schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Código Python a executar (ex: import calculator; print(calculator.add(2,3)))",
                }
            },
            "required": ["code"],
            "additionalProperties": False,
        }

    def execute(self, *, code: str) -> dict[str, Any]:
        if not self._policy.check_path("/workspace", action="read"):
            raise PermissionError("policy bloqueou run_smoke")
        self._policy.record_tool(self.name)
        result = run_command(
            [sys.executable, "-c", code],
            cwd=self._workspace,
            timeout=30,
        )
        return result  # type: ignore[return-value]


def build_tool_registry(
    spec: ArenaSpec,
    workspace: Path,
    policy: PolicyTracker,
) -> ToolRegistry:
    ProjectBoundary, ReadFileTool, WriteFileTool = _harness_project_tools()
    boundary = ProjectBoundary(root=workspace.resolve())
    registry = ToolRegistry()
    allowed = set(spec.agent.tools)

    if "read_file" in allowed:
        registry.register(
            PolicyAwareTool(ReadFileTool(boundary), policy=policy, action="read")
        )
    if "write_file" in allowed:
        registry.register(
            PolicyAwareTool(WriteFileTool(boundary), policy=policy, action="write")
        )
    if "run_smoke" in allowed:
        registry.register(RunSmokeTool(workspace, policy))

    return registry
