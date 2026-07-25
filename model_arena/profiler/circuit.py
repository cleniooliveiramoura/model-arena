from __future__ import annotations

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


def build_circuit(model: ModelCard, *, circuit: str | None = None) -> list[str]:
    if circuit == "demo":
        return ["code-fix", SECURITY_ARENA]
    if circuit == "full":
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

    if circuit:
        parts = [p.strip() for p in circuit.split(",") if p.strip()]
        if SECURITY_ARENA not in parts:
            parts.append(SECURITY_ARENA)
        return parts

    arenas = []
    seen = set()
    for tag in model.tags or ["general"]:
        for arena_id in TAG_ARENAS.get(tag, DEFAULT_CAPABILITY):
            if arena_id not in seen:
                seen.add(arena_id)
                arenas.append(arena_id)
    if SECURITY_ARENA not in seen:
        arenas.append(SECURITY_ARENA)
    return arenas
