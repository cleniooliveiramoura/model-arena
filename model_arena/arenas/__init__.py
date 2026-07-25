from __future__ import annotations

from pathlib import Path

import yaml

from ..types import ArenaSpec


def arenas_root(base: Path | None = None) -> Path:
    if base is None:
        base = Path(__file__).resolve().parents[2]
    return base / "arenas"


def load_arena(arena_id: str, *, base: Path | None = None) -> ArenaSpec:
    root = arenas_root(base) / arena_id
    spec_path = root / "arena.yaml"
    if not spec_path.is_file():
        raise FileNotFoundError(f"arena não encontrada: {arena_id} ({spec_path})")
    data = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    return ArenaSpec.from_dict(data, root=str(root))


def list_arenas(*, base: Path | None = None) -> list[str]:
    root = arenas_root(base)
    if not root.is_dir():
        return []
    return sorted(
        p.name for p in root.iterdir() if p.is_dir() and (p / "arena.yaml").is_file()
    )
