from __future__ import annotations

from pathlib import Path

import yaml

from ..types import ModelCard


def models_dir(base: Path | None = None) -> Path:
    if base is None:
        base = Path(__file__).resolve().parents[2]
    return base / "models"


def load_model_card(path: str | Path) -> ModelCard:
    p = Path(path)
    if not p.is_file():
        p = models_dir() / path
    if not p.suffix:
        p = p.with_suffix(".yaml")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return ModelCard.from_dict(data)
