from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .doctor import run_doctor
from .profiler.cards import load_model_card
from .profiler.circuit import build_circuit
from .report.scorecard import compare_models, run_circuit, write_scorecard


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="arena", description="Model Arena CLI")
    parser.add_argument("--home", default=".arena", help="Diretório de persistência")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Diagnostica ambiente e arenas")

    p_run = sub.add_parser("run", help="Executa circuito para um modelo")
    p_run.add_argument("--model", required=True, help="Caminho do Model Card YAML")
    p_run.add_argument("--circuit", default="demo", help="demo|coding|stress|full|arena1,arena2")
    p_run.add_argument("--out", default=None, help="JSON scorecard")

    p_cmp = sub.add_parser("compare", help="Compara dois modelos")
    p_cmp.add_argument("baseline", help="Model Card baseline")
    p_cmp.add_argument("candidate", help="Model Card candidato")
    p_cmp.add_argument("--circuit", default="demo")
    p_cmp.add_argument("--out", default=None)

    p_debate = sub.add_parser("debate", help="Discussão agentic entre dois modelos")
    p_debate.add_argument("model_a", help="Model Card A")
    p_debate.add_argument("model_b", help="Model Card B")
    p_debate.add_argument("--arena", default="code-fix", help="Arena base")
    p_debate.add_argument(
        "--sandbox",
        choices=["separate", "shared"],
        default="separate",
        help="Sandboxes separadas ou compartilhada",
    )
    p_debate.add_argument("--rounds", type=int, default=2, help="Rodadas (A↔B cada)")
    p_debate.add_argument(
        "--judge",
        choices=["heuristic", "llm", "none"],
        default="heuristic",
        help="Modo do juiz pós-discussão",
    )
    p_debate.add_argument(
        "--judge-model",
        default=None,
        help="Model Card do juiz LLM (ex.: models/examples/litellm-judge.yaml)",
    )
    p_debate.add_argument("--out", default=None)

    p_serve = sub.add_parser("serve", help="API + UI")
    p_serve.add_argument("--port", type=int, default=8790)
    p_serve.add_argument("--host", default="127.0.0.1")

    args = parser.parse_args(argv)
    base = Path(__file__).resolve().parents[1]

    if args.command == "doctor":
        report = run_doctor(base=base)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["ok"] else 1

    if args.command == "run":
        model = load_model_card(args.model)
        arenas = build_circuit(model, circuit=args.circuit)
        score = run_circuit(model, arenas, base=base)
        out = args.out or str(Path(args.home) / "scorecard.json")
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        write_scorecard(score, out)
        print(json.dumps(score.to_dict(), indent=2, ensure_ascii=False))
        return 0 if score.capability_passed else 1

    if args.command == "compare":
        result = compare_models(args.baseline, args.candidate, circuit=args.circuit, base=base)
        out = args.out or str(Path(args.home) / "compare.json")
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.command == "debate":
        from .debate import run_debate

        result = run_debate(
            args.model_a,
            args.model_b,
            arena_id=args.arena,
            sandbox_mode=args.sandbox,
            rounds=args.rounds,
            base=base,
            judge=args.judge,
            judge_model=args.judge_model,
        )
        out = args.out or str(Path(args.home) / "debate.json")
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return 0

    if args.command == "serve":
        from .api.app import main as serve_main

        return serve_main(host=args.host, port=args.port)

    return 1


if __name__ == "__main__":
    sys.exit(main())
