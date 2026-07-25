from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..arenas import list_arenas
from ..profiler.cards import load_model_card
from ..profiler.circuit import build_circuit
from ..report.scorecard import compare_models, run_circuit

BASE = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).resolve().parent / "static"


class RunRequest(BaseModel):
    model_path: str
    circuit: str = "demo"


class CompareRequest(BaseModel):
    baseline: str
    candidate: str
    circuit: str = "demo"


def create_app() -> FastAPI:
    app = FastAPI(title="Model Arena", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/arenas")
    def api_arenas() -> dict[str, list[str]]:
        return {"arenas": list_arenas(base=BASE)}

    @app.get("/api/models")
    def api_models() -> dict[str, list[dict[str, str]]]:
        models_dir = BASE / "models" / "examples"
        items: list[dict[str, str]] = []
        labels = {
            "ollama-gemma-coder.yaml": "Ollama Gemma 4 12B Coder",
            "ollama-llama-coder.yaml": "Ollama Llama 3.2",
            "litellm-gpt4o-mini.yaml": "LiteLLM GPT-4o-mini (OpenAI)",
            "honest-mock.yaml": "Mock honesto",
            "malicious-mock.yaml": "Mock malicioso",
            "honest-agent-mock.yaml": "Mock agente",
            "honest-reason-mock.yaml": "Mock reasoning",
            "honest-legal-mock.yaml": "Mock jurídico (bom)",
            "bad-legal-mock.yaml": "Mock jurídico (ruim)",
        }
        if models_dir.is_dir():
            for path in sorted(models_dir.glob("*.yaml")):
                rel = f"models/examples/{path.name}"
                items.append({"path": rel, "label": labels.get(path.name, path.stem)})
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
