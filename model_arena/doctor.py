from __future__ import annotations

import shutil
from pathlib import Path

from .arenas import list_arenas


def run_doctor(*, base: Path | None = None) -> dict[str, object]:
    if base is None:
        base = Path(__file__).resolve().parents[1]

    checks: list[dict[str, object]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    add("python", True, "ok")
    add("docker_cli", bool(shutil.which("docker")), "opcional para sandbox Docker")

    try:
        import harness_core  # noqa: F401

        add("harness_core", True, "instalado")
    except ImportError:
        add("harness_core", False, "pip install -e ../harness_core")

    arenas = list_arenas(base=base)
    add("arenas_catalog", len(arenas) > 0, f"{len(arenas)} arenas: {', '.join(arenas)}")

    for arena_id in arenas:
        root = base / "arenas" / arena_id
        for sub in ("workspace", "hidden", "arena.yaml"):
            p = root / sub if sub != "arena.yaml" else root / "arena.yaml"
            add(f"arena_{arena_id}_{sub}", p.exists(), str(p))

    models = base / "models" / "examples"
    add("model_examples", models.is_dir(), str(models))

    ok = all(
        c["ok"]
        for c in checks
        if c["name"] not in {"docker_cli", "harness_core"}
    )
    return {"ok": ok, "checks": checks}
