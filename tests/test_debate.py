from __future__ import annotations

from pathlib import Path

from model_arena.debate import run_debate
from model_arena.profiler.cards import load_model_card

BASE = Path(__file__).resolve().parents[1]


def test_debate_separate_honest_vs_malicious():
    result = run_debate(
        BASE / "models/examples/honest-mock.yaml",
        BASE / "models/examples/malicious-mock.yaml",
        sandbox_mode="separate",
        rounds=2,
        base=BASE,
    )
    assert result.sandbox_mode == "separate"
    assert len(result.timeline) >= 4
    assert len(result.participants) == 2
    assert result.shared_grade is None

    by_id = {p.model_id: p for p in result.participants}
    honest = by_id["honest-mock"]
    malicious = by_id["malicious-mock"]
    assert honest.passed is True
    assert honest.mean_score >= 0.99
    assert malicious.passed is False

    model_ids = {e.get("model_id") for e in result.timeline if e.get("model_id")}
    assert "honest-mock" in model_ids
    assert "malicious-mock" in model_ids


def test_debate_shared_honest_vs_malicious():
    result = run_debate(
        BASE / "models/examples/honest-mock.yaml",
        BASE / "models/examples/malicious-mock.yaml",
        sandbox_mode="shared",
        rounds=1,
        base=BASE,
    )
    assert result.sandbox_mode == "shared"
    assert result.shared_grade is not None
    assert not result.participants
    assert any(e.get("kind") == "turn_start" for e in result.timeline)


def test_debate_judge_picks_honest():
    result = run_debate(
        BASE / "models/examples/honest-mock.yaml",
        BASE / "models/examples/malicious-mock.yaml",
        sandbox_mode="separate",
        rounds=2,
        base=BASE,
        judge="heuristic",
    )
    assert result.judge is not None
    assert result.judge.winner == "honest-mock"
    assert len(result.judge.scores) == 2
    honest = next(s for s in result.judge.scores if s.model_id == "honest-mock")
    malicious = next(s for s in result.judge.scores if s.model_id == "malicious-mock")
    assert honest.overall > malicious.overall
    assert honest.integrity > malicious.integrity


def test_debate_judge_none():
    result = run_debate(
        BASE / "models/examples/honest-mock.yaml",
        BASE / "models/examples/malicious-mock.yaml",
        judge="none",
        base=BASE,
    )
    assert result.judge is None


def test_debate_timeline_has_turn_markers():
    result = run_debate(
        load_model_card(BASE / "models/examples/honest-mock.yaml"),
        load_model_card(BASE / "models/examples/honest-mock.yaml"),
        sandbox_mode="separate",
        rounds=1,
        base=BASE,
    )
    turns = [e for e in result.timeline if e.get("kind") == "turn_start"]
    assert len(turns) == 2
