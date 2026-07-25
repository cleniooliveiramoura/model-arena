from __future__ import annotations

from dataclasses import dataclass

from ..types import ModelCard

# Arenas por tag — roteamento apenas; não entra no score.
TAG_ARENAS: dict[str, list[str]] = {
    "coding": ["code-fix"],
    "agent": ["tool-agent"],
    "general": ["reason-closed"],
    "cyber": ["security-policy"],
    "legal": ["legal-grounding"],
}

DEFAULT_CAPABILITY = ["code-fix", "tool-agent", "reason-closed"]
SECURITY_ARENA = "security-policy"

ALL_CAPABILITY = [
    "reason-closed",
    "code-fix",
    "tool-agent",
    "legal-grounding",
]


@dataclass(frozen=True)
class CircuitPreset:
    id: str
    label: str
    description: str
    arenas: tuple[str, ...] | None = None
    dynamic: str | None = None  # "tags" = full por tags do model card


CIRCUIT_PRESETS: dict[str, CircuitPreset] = {
    "demo": CircuitPreset(
        id="demo",
        label="Demo — smoke rápido",
        description="2 arenas: corrigir bug + segurança. Ideal para testar se o modelo roda.",
        arenas=("code-fix", SECURITY_ARENA),
    ),
    "coding": CircuitPreset(
        id="coding",
        label="Coding — desenvolvimento",
        description="3 arenas: bug de código, agente com tools e segurança.",
        arenas=("code-fix", "tool-agent", SECURITY_ARENA),
    ),
    "agent": CircuitPreset(
        id="agent",
        label="Agent — ferramentas primeiro",
        description="3 arenas: tool-agent antes do code-fix; foco em uso de tools.",
        arenas=("tool-agent", "code-fix", SECURITY_ARENA),
    ),
    "generalist": CircuitPreset(
        id="generalist",
        label="Generalista — mix equilibrado",
        description="4 arenas: reasoning, código, tools e segurança.",
        arenas=("reason-closed", "code-fix", "tool-agent", SECURITY_ARENA),
    ),
    "legal": CircuitPreset(
        id="legal",
        label="Jurídico — pack legal",
        description="3 arenas: grounding jurídico, reasoning e segurança.",
        arenas=("legal-grounding", "reason-closed", SECURITY_ARENA),
    ),
    "cyber": CircuitPreset(
        id="cyber",
        label="Cyber — segurança + código",
        description="2 arenas: probes de policy primeiro, depois code-fix.",
        arenas=(SECURITY_ARENA, "code-fix"),
    ),
    "full": CircuitPreset(
        id="full",
        label="Full — por tags do modelo",
        description="Arenas das tags do model card + security. Varia por modelo.",
        dynamic="tags",
    ),
    "stress": CircuitPreset(
        id="stress",
        label="Stress — circuito completo",
        description="5 arenas: todas as capability + security. O mais longo e exigente.",
        arenas=(*ALL_CAPABILITY, SECURITY_ARENA),
    ),
}


def list_circuits(*, model: ModelCard | None = None) -> list[dict[str, object]]:
    """Lista circuitos pré-definidos com arenas resolvidas (quando possível)."""
    out: list[dict[str, object]] = []
    for preset in CIRCUIT_PRESETS.values():
        if preset.dynamic == "tags":
            arenas = _circuit_by_tags(model) if model else []
            resolved = "dynamic"
        else:
            arenas = list(preset.arenas or [])
            resolved = "fixed"
        out.append(
            {
                "id": preset.id,
                "label": preset.label,
                "description": preset.description,
                "arenas": arenas,
                "arena_count": len(arenas) if arenas else None,
                "resolution": resolved,
                "complexity": _complexity_label(len(arenas) if arenas else 5),
            }
        )
    return out


def _complexity_label(n: int) -> str:
    if n <= 2:
        return "leve"
    if n <= 3:
        return "médio"
    if n <= 4:
        return "alto"
    return "máximo"


def build_circuit(model: ModelCard, *, circuit: str | None = None) -> list[str]:
    if circuit and circuit in CIRCUIT_PRESETS:
        preset = CIRCUIT_PRESETS[circuit]
        if preset.dynamic == "tags":
            return _circuit_by_tags(model)
        return list(preset.arenas or [])

    if circuit == "full":
        return _circuit_by_tags(model)

    if circuit:
        parts = [p.strip() for p in circuit.split(",") if p.strip()]
        if SECURITY_ARENA not in parts:
            parts.append(SECURITY_ARENA)
        return parts

    return _circuit_by_tags(model)


def _circuit_by_tags(model: ModelCard) -> list[str]:
    arenas: list[str] = []
    seen: set[str] = set()
    for tag in model.tags:
        for arena_id in TAG_ARENAS.get(tag, []):
            if arena_id not in seen:
                seen.add(arena_id)
                arenas.append(arena_id)
    if not arenas:
        arenas = list(DEFAULT_CAPABILITY)
    if SECURITY_ARENA not in seen:
        arenas.append(SECURITY_ARENA)
    return arenas
