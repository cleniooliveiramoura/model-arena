from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from model_arena.arenas import list_arenas, load_arena
from model_arena.doctor import run_doctor
from model_arena.profiler.cards import load_model_card
from model_arena.profiler.circuit import build_circuit
from model_arena.report.scorecard import compare_models, run_circuit
from model_arena.runner import run_arena

BASE = Path(__file__).resolve().parents[1]


def test_doctor_ok():
    report = run_doctor(base=BASE)
    assert report["ok"] is True
    assert len(list_arenas(base=BASE)) >= 5


def test_honest_passes_code_fix():
    spec = load_arena("code-fix", base=BASE)
    model = load_model_card(BASE / "models/examples/honest-mock.yaml")
    with tempfile.TemporaryDirectory() as tmp:
        result = run_arena(spec, model, temp_root=Path(tmp))
    assert result.kind == "capability"
    assert result.passed is True
    assert result.mean_score >= 0.99
    policy = next(g for g in result.grades if g.grader == "policy_violation")
    assert policy.passed is True


def test_malicious_fails_code_fix():
    spec = load_arena("code-fix", base=BASE)
    model = load_model_card(BASE / "models/examples/malicious-mock.yaml")
    with tempfile.TemporaryDirectory() as tmp:
        result = run_arena(spec, model, temp_root=Path(tmp))
    assert result.passed is False
    policy = next(g for g in result.grades if g.grader == "policy_violation")
    assert policy.passed is False
    # Grading isolado: pytest em /hidden/tests não usa conftest do agente; policy pega o hack.
    cmd = next(g for g in result.grades if g.grader == "command")
    assert cmd.passed is True


def test_compare_honest_vs_malicious():
    result = compare_models(
        BASE / "models/examples/honest-mock.yaml",
        BASE / "models/examples/malicious-mock.yaml",
        circuit="demo",
        base=BASE,
    )
    baseline = result["baseline"]
    candidate = result["candidate"]
    assert baseline["capability_score"] > candidate["capability_score"]
    assert baseline["security_score"] >= candidate["security_score"]
    assert baseline["capability_score"] != candidate["capability_score"]


def test_dual_scorecard_separate():
    model = load_model_card(BASE / "models/examples/honest-mock.yaml")
    arenas = build_circuit(model, circuit="demo")
    score = run_circuit(model, arenas, base=BASE)
    assert "capability_score" in score.to_dict()
    assert "security_score" in score.to_dict()
    cap = [a for a in score.arenas if a.kind == "capability"]
    sec = [a for a in score.arenas if a.kind == "security"]
    assert cap and sec


def test_profiler_tags_do_not_affect_score():
    model = load_model_card(BASE / "models/examples/honest-mock.yaml")
    model.benchmarks = {"coding": 0.0}
    arenas = build_circuit(model, circuit="demo")
    score = run_circuit(model, arenas, base=BASE)
    assert score.capability_score >= 0.99


def test_legal_grounding():
    spec = load_arena("legal-grounding", base=BASE)
    good = load_model_card(BASE / "models/examples/honest-legal-mock.yaml")
    bad = load_model_card(BASE / "models/examples/bad-legal-mock.yaml")
    with tempfile.TemporaryDirectory() as tmp:
        good_r = run_arena(spec, good, temp_root=Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        bad_r = run_arena(spec, bad, temp_root=Path(tmp))
    assert good_r.passed is True
    assert bad_r.passed is False


def test_tool_agent():
    spec = load_arena("tool-agent", base=BASE)
    model = load_model_card(BASE / "models/examples/honest-agent-mock.yaml")
    with tempfile.TemporaryDirectory() as tmp:
        result = run_arena(spec, model, temp_root=Path(tmp))
    assert result.passed is True
