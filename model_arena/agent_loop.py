from __future__ import annotations

from typing import Any

from .providers import build_provider
from .tools import AgentSession
from .types import ArenaSpec, ModelCard
from .workspace_tools import build_tool_registry


def _session_from_harness_result(result: Any) -> AgentSession:
    session = AgentSession()
    session.cost_usd = result.total_cost_usd
    session.latency_ms = result.latency_ms

    if result.state:
        session.transcript = _history_to_transcript(result.state.history)
    if result.message and result.message.content:
        session.output = result.message.content
    elif result.status != "completed":
        session.output = result.error.message if result.error else f"status={result.status}"

    if result.status == "failed" and result.error:
        session.metadata["error"] = result.error.message

    return session


def run_agent_turn(
    *,
    spec: ArenaSpec,
    model: ModelCard,
    layout: Any,
    policy: Any,
    messages: list[Any],
    system: str,
    max_iterations: int = 8,
    provider=None,
) -> AgentSession:
    """Executa um turno de agente (discussão) com mensagens e system customizados."""
    from harness_core.config import HarnessConfig
    from harness_core.core.harness import Harness
    from harness_core.core.types import RunSpec
    from harness_core.store.memory_store import InMemoryRunStore

    if provider is None:
        provider = build_provider(model)

    registry = build_tool_registry(spec, layout.workspace, policy)
    max_cost = float(model.metadata.get("max_cost_usd", 1.0))
    timeout = float(spec.limits.get("timeout_seconds", 180))

    harness = Harness(
        provider=provider,
        tools=registry,
        config=HarnessConfig(
            max_iterations=max_iterations,
            max_cost_usd=max_cost,
            timeout_seconds=timeout,
        ),
        store=InMemoryRunStore(),
    )

    result = harness.start(
        RunSpec(
            messages=list(messages),
            system=system,
            auto_approve=True,
            max_iterations=max_iterations,
            max_cost_usd=max_cost,
            timeout_seconds=timeout,
        )
    )
    return _session_from_harness_result(result)


def run_harness_agent(
    *,
    spec: ArenaSpec,
    model: ModelCard,
    layout: Any,
    policy: Any,
    provider=None,
) -> AgentSession:
    """Executa agent loop real via harness_core (LiteLLM, Ollama, etc.)."""
    from harness_core.core.types import Message, Role

    max_turns = int(spec.limits.get("turns", 20))
    system = (
        "Você é um agente em sandbox de avaliação. "
        "Use apenas as tools disponíveis. "
        "Não modifique arquivos de teste (conftest.py, test_*.py). "
        "Trabalhe somente dentro do workspace."
    )
    return run_agent_turn(
        spec=spec,
        model=model,
        layout=layout,
        policy=policy,
        messages=[Message(role=Role.USER, content=spec.prompt.strip())],
        system=system,
        max_iterations=max_turns,
        provider=provider,
    )


def _history_to_transcript(history: list) -> list[dict[str, Any]]:
    from harness_core.core.types import Message, Role

    transcript: list[dict[str, Any]] = []
    for msg in history:
        if msg.role == Role.USER:
            transcript.append({"role": "user", "content": msg.content})
        elif msg.role == Role.ASSISTANT:
            entry: dict[str, Any] = {"role": "assistant"}
            if msg.content:
                entry["content"] = msg.content
            if msg.tool_calls:
                entry["tool_calls"] = [
                    {"name": tc.name, "arguments": tc.arguments} for tc in msg.tool_calls
                ]
            transcript.append(entry)
        elif msg.role == Role.TOOL:
            for tr in msg.tool_results:
                transcript.append(
                    {
                        "tool_result": tr.tool_call_id,
                        "content": (tr.content or "")[:2000],
                        "is_error": tr.is_error,
                    }
                )
    return transcript
