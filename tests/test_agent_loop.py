from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from model_arena.agent_loop import run_harness_agent
from model_arena.arenas import load_arena
from model_arena.providers import build_provider
from model_arena.types import ModelCard
from model_arena.workspace_tools import build_tool_registry
from model_arena.policy.tracker import PolicyTracker

BASE = Path(__file__).resolve().parents[1]

FIXED_CALC = '''"""Calculadora simples."""


def add(a: int, b: int) -> int:
    return a + b


def subtract(a: int, b: int) -> int:
    return a - b
'''


@pytest.fixture
def code_fix_setup():
    spec = load_arena("code-fix", base=BASE)
    model = ModelCard(id="test", provider="litellm", model="mock")
    policy = PolicyTracker(spec.agent)
    with tempfile.TemporaryDirectory() as tmp:
        from model_arena.runner import ArenaLayout, _seed_layout

        layout = ArenaLayout.from_spec(spec, temp_root=Path(tmp))
        _seed_layout(spec, layout)
        yield spec, model, layout, policy


def test_build_provider_rejects_mock():
    with pytest.raises(ValueError, match="mock"):
        build_provider(ModelCard(id="x", provider="mock"))


def test_tool_registry_blocks_conftest(code_fix_setup):
    spec, _model, layout, policy = code_fix_setup
    registry = build_tool_registry(spec, layout.workspace, policy)
    write = registry.get("write_file")
    assert write is not None
    with pytest.raises(PermissionError):
        write.execute(path="conftest.py", content="hack")


def test_harness_agent_loop_with_mock_provider(code_fix_setup):
    import hashlib

    from harness_core.core.types import Message, ModelResponse, Role, ToolCall
    from harness_core.providers.mock import MockProvider

    spec, model, layout, policy = code_fix_setup
    calc_path = layout.workspace / "calculator.py"
    existing_sha = hashlib.sha256(calc_path.read_bytes()).hexdigest()

    provider = MockProvider(
        [
            ModelResponse(
                message=Message(
                    role=Role.ASSISTANT,
                    tool_calls=[
                        ToolCall(
                            id="tc1",
                            name="read_file",
                            arguments={"path": "calculator.py"},
                        )
                    ],
                ),
                stop_reason="tool_use",
            ),
            ModelResponse(
                message=Message(
                    role=Role.ASSISTANT,
                    tool_calls=[
                        ToolCall(
                            id="tc2",
                            name="write_file",
                            arguments={
                                "path": "calculator.py",
                                "content": FIXED_CALC,
                                "expected_sha256": existing_sha,
                            },
                        )
                    ],
                ),
                stop_reason="tool_use",
            ),
            ModelResponse(
                message=Message(role=Role.ASSISTANT, content="Bug corrigido."),
                stop_reason="end_turn",
            ),
        ]
    )

    session = run_harness_agent(
        spec=spec,
        model=model,
        layout=layout,
        policy=policy,
        provider=provider,
    )
    assert session.output == "Bug corrigido."
    assert any(e.get("tool_calls") for e in session.transcript if isinstance(e, dict))
    fixed = calc_path.read_text()
    assert "return a + b" in fixed


@pytest.mark.integration
def test_code_fix_litellm_real():
    """Roda arena code-fix com LLM real — requer OPENAI_API_KEY."""
    import os

    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY não definida")

    from model_arena.profiler.cards import load_model_card
    from model_arena.runner import run_arena

    spec = load_arena("code-fix", base=BASE)
    model = load_model_card(BASE / "models/examples/litellm-gpt4o-mini.yaml")
    with tempfile.TemporaryDirectory() as tmp:
        result = run_arena(spec, model, temp_root=Path(tmp))
    assert result.infra_status == "ok", result.error
    assert result.cost_usd >= 0
