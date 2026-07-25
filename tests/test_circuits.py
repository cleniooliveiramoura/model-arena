from __future__ import annotations

from model_arena.profiler.cards import load_model_card
from model_arena.profiler.circuit import build_circuit, list_circuits

BASE = __import__("pathlib").Path(__file__).resolve().parents[1]


def test_list_circuits_includes_stress():
    circuits = list_circuits()
    ids = {c["id"] for c in circuits}
    assert "demo" in ids
    assert "stress" in ids
    assert "coding" in ids
    stress = next(c for c in circuits if c["id"] == "stress")
    assert stress["arena_count"] == 5
    assert stress["complexity"] == "máximo"


def test_build_circuit_stress_fixed_order():
    model = load_model_card(BASE / "models/examples/honest-mock.yaml")
    arenas = build_circuit(model, circuit="stress")
    assert arenas == [
        "reason-closed",
        "code-fix",
        "tool-agent",
        "legal-grounding",
        "security-policy",
    ]


def test_build_circuit_demo():
    model = load_model_card(BASE / "models/examples/honest-mock.yaml")
    assert build_circuit(model, circuit="demo") == ["code-fix", "security-policy"]


def test_build_circuit_custom_comma_list():
    model = load_model_card(BASE / "models/examples/honest-mock.yaml")
    arenas = build_circuit(model, circuit="tool-agent,reason-closed")
    assert "tool-agent" in arenas
    assert "reason-closed" in arenas
    assert "security-policy" in arenas
