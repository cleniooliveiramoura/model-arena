from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..arenas import list_arenas
from ..profiler.cards import load_model_card
from ..profiler.circuit import build_circuit, list_circuits
from ..report.scorecard import compare_models, run_circuit
from ..debate import run_debate

BASE = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).resolve().parent / "static"


class RunRequest(BaseModel):
    model_path: str
    circuit: str = "demo"


class CompareRequest(BaseModel):
    baseline: str
    candidate: str
    circuit: str = "demo"


class DebateRequest(BaseModel):
    model_a: str
    model_b: str
    arena_id: str = "code-fix"
    sandbox_mode: str = "separate"
    rounds: int = 2
    max_iterations_per_turn: int = 8
    topic: str | None = None
    judge: str = "heuristic"
    judge_model: str | None = None


def create_app() -> FastAPI:
    app = FastAPI(title="Model Arena", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/arenas")
    def api_arenas() -> dict[str, list[str]]:
        return {"arenas": list_arenas(base=BASE)}

    @app.get("/api/circuits")
    def api_circuits() -> dict[str, list[dict[str, object]]]:
        return {"circuits": list_circuits()}

    @app.get("/api/models")
    def api_models() -> dict[str, list[dict[str, str]]]:
        models_dir = BASE / "models" / "examples"
        items: list[dict[str, str]] = []
        if models_dir.is_dir():
            for path in sorted(models_dir.glob("*.yaml")):
                card = load_model_card(path)
                rel = f"models/examples/{path.name}"
                provider = card.provider
                label = str(card.metadata.get("label") or card.id)
                items.append({"path": rel, "label": label, "provider": provider})
        return {"models": items}

    @app.post("/api/run")
    def api_run(body: RunRequest) -> JSONResponse:
        model = load_model_card(body.model_path)
        arenas = build_circuit(model, circuit=body.circuit)
        score = run_circuit(model, arenas, base=BASE)
        return JSONResponse(score.to_dict())

    @app.post("/api/compare")
    def api_compare(body: CompareRequest) -> JSONResponse:
        result = compare_models(
            body.baseline, body.candidate, circuit=body.circuit, base=BASE
        )
        return JSONResponse(result)

    @app.post("/api/debate")
    def api_debate(body: DebateRequest) -> JSONResponse:
        if body.sandbox_mode not in ("separate", "shared"):
            return JSONResponse(
                {"detail": "sandbox_mode deve ser 'separate' ou 'shared'"},
                status_code=400,
            )
        if body.judge not in ("heuristic", "llm", "none"):
            return JSONResponse(
                {"detail": "judge deve ser 'heuristic', 'llm' ou 'none'"},
                status_code=400,
            )
        result = run_debate(
            body.model_a,
            body.model_b,
            arena_id=body.arena_id,
            sandbox_mode=body.sandbox_mode,  # type: ignore[arg-type]
            rounds=max(1, min(body.rounds, 6)),
            max_iterations_per_turn=max(1, min(body.max_iterations_per_turn, 20)),
            topic=body.topic,
            base=BASE,
            judge=body.judge,  # type: ignore[arg-type]
            judge_model=body.judge_model,
        )
        return JSONResponse(result.to_dict())

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    if STATIC.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

    return app


def main(host: str = "127.0.0.1", port: int = 8790) -> int:
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port, log_level="info")
    return 0
