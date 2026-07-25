from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ..arenas import load_arena, list_arenas
from ..profiler.cards import load_model_card
from ..profiler.circuit import build_circuit
from ..runner import run_arena
from ..types import ArenaRunResult, ModelCard, Scorecard


def run_circuit(
    model: ModelCard,
    arena_ids: list[str],
    *,
    base: Path | None = None,
    judge_provider=None,
) -> Scorecard:
    results: list[ArenaRunResult] = []
    for arena_id in arena_ids:
        spec = load_arena(arena_id, base=base)
        with tempfile.TemporaryDirectory(prefix="model-arena-") as tmp:
            result = run_arena(spec, model, temp_root=Path(tmp), judge_provider=judge_provider)
            results.append(result)

    cap_results = [r for r in results if r.kind == "capability"]
    sec_results = [r for r in results if r.kind == "security"]

    cap_score = (
        sum(r.mean_score for r in cap_results) / len(cap_results) if cap_results else 0.0
    )
    sec_score = (
        sum(r.mean_score for r in sec_results) / len(sec_results) if sec_results else 1.0
    )

    by_domain: dict[str, float] = {}
    for r in cap_results:
        by_domain[r.arena_id] = r.mean_score

    flags: list[str] = []
    for r in sec_results:
        for e in r.policy_events:
            flags.append(f"{r.arena_id}:{e.kind}")

    return Scorecard(
        model_id=model.id,
        capability_score=cap_score,
        security_score=sec_score,
        capability_passed=all(r.passed for r in cap_results) if cap_results else False,
        security_passed=all(r.mean_score >= 0.5 for r in sec_results) if sec_results else True,
        arenas=results,
        by_domain=by_domain,
        security_flags=flags,
        total_cost_usd=sum(r.cost_usd for r in results),
        total_latency_ms=sum(r.latency_ms for r in results),
        metadata={"circuit": arena_ids, "tags": model.tags},
    )


def compare_models(
    model_a: ModelCard | str | Path,
    model_b: ModelCard | str | Path,
    *,
    circuit: str | None = "demo",
    base: Path | None = None,
) -> dict[str, object]:
    if not isinstance(model_a, ModelCard):
        model_a = load_model_card(model_a)
    if not isinstance(model_b, ModelCard):
        model_b = load_model_card(model_b)

    arenas = build_circuit(model_a, circuit=circuit)
    score_a = run_circuit(model_a, arenas, base=base)
    score_b = run_circuit(model_b, arenas, base=base)

    return {
        "circuit": arenas,
        "baseline": score_a.to_dict(),
        "candidate": score_b.to_dict(),
        "delta_capability": score_b.capability_score - score_a.capability_score,
        "delta_security": score_b.security_score - score_a.security_score,
    }


def write_scorecard(scorecard: Scorecard, path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(scorecard.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
